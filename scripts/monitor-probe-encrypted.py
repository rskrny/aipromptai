#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HelloTalk encrypted-endpoint probe.

Runs from a GitHub Actions runner because the Claude Code sandbox cannot
reach hellotalk8.com. Generates a fresh X25519 keypair each run, derives
the AES-256 shared secret with the known HelloTalk server public key, and
probes the encrypted endpoints.

The critical probe is /go_user_search/v2/filter — on 2026-04-06 it
returned error code 6000 "Get Search User Plan Failed". Re-running it
tells us whether the search index exclusion is still active after the
2026-04-11 profile unlock.

Requires: cryptography, httpx (installed in the workflow step).
Writes results under monitor/runs/<timestamp>/enc_*.{body,meta} and
copies them into monitor/latest/ alongside the plain-probe results.
"""

from __future__ import annotations

import gzip
import json
import random
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from cryptography.hazmat.primitives.asymmetric.x25519 import (
        X25519PrivateKey,
        X25519PublicKey,
    )
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.padding import PKCS7
    from cryptography.hazmat.primitives import serialization
except ImportError:
    print("need cryptography: pip install cryptography")
    sys.exit(1)

try:
    import httpx
except ImportError:
    print("need httpx: pip install httpx")
    sys.exit(1)


# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------
BASE = "https://api-global.hellotalk8.com"
HT_UID = "98755150"
DID = "29ea6362a590de52972d100cd01ab78dd7b7b6c9"
TOKEN = (
    "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJleHAiOjE3NzgwMzA1NzAsInNyYyI6MiwidWlkIjo5ODc1NTE1MH0."
    "Og3Hb2l95RB7SPuw5TRR5Q_rJsnSb1ClqMaCP-Abqh8"
)

# X25519 server public key, extracted from WnsConfigManager on 2026-04-06.
SERVER_PUB_HEX = (
    "f684f611b895a5d3abc124a20ca2dfd397662318cfd4fd74b80aba478c17ca68"
)
SERVER_PUB_BYTES = bytes.fromhex(SERVER_PUB_HEX)


# --------------------------------------------------------------------------
# Crypto
# --------------------------------------------------------------------------
def generate_handshake() -> tuple[bytes, bytes, str]:
    """Generate ephemeral X25519 keys and derive the AES key."""
    priv = X25519PrivateKey.generate()
    client_pub = priv.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    server_pub = X25519PublicKey.from_public_bytes(SERVER_PUB_BYTES)
    shared_secret = priv.exchange(server_pub)  # 32 bytes = AES-256 key
    x_ht_pub_header = SERVER_PUB_HEX + client_pub.hex()
    return client_pub, shared_secret, x_ht_pub_header


def aes_decrypt(ciphertext: bytes, key: bytes) -> bytes:
    """AES-256-ECB + PKCS7 + optional gzip."""
    if not ciphertext or len(ciphertext) % 16 != 0:
        return ciphertext
    cipher = Cipher(algorithms.AES(key), modes.ECB())
    dec = cipher.decryptor()
    padded = dec.update(ciphertext) + dec.finalize()
    try:
        unpadder = PKCS7(128).unpadder()
        raw = unpadder.update(padded) + unpadder.finalize()
    except Exception:
        raw = padded
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return raw


def aes_encrypt(plaintext: bytes, key: bytes) -> bytes:
    """AES-256-ECB + PKCS7."""
    padder = PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.ECB())
    enc = cipher.encryptor()
    return enc.update(padded) + enc.finalize()


# --------------------------------------------------------------------------
# Probe runner
# --------------------------------------------------------------------------
def try_parse(data: bytes, aes_key: bytes):
    """Attempt to decrypt + parse a response body."""
    if not data:
        return None, "empty"
    # Plain JSON shortcut
    if data[:1] in (b"{", b"["):
        try:
            return json.loads(data.decode("utf-8", errors="replace")), "plain"
        except Exception:
            return data.decode("utf-8", errors="replace"), "plain_text"
    # Otherwise treat as encrypted
    try:
        decrypted = aes_decrypt(data, aes_key)
        text = decrypted.decode("utf-8", errors="replace")
        try:
            return json.loads(text), "decrypted_json"
        except Exception:
            return text, "decrypted_text"
    except Exception as exc:
        return f"<decrypt failed: {exc}>", "decrypt_error"


def main() -> int:
    client_pub, aes_key, x_ht_pub = generate_handshake()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path("monitor/runs") / ts
    latest_dir = Path("monitor/latest")
    run_dir.mkdir(parents=True, exist_ok=True)
    latest_dir.mkdir(parents=True, exist_ok=True)

    headers = {
        "Authorization": TOKEN,
        "x-ht-uid": HT_UID,
        "x-ht-did": DID,
        "x-ht-os": "ios",
        "x-ht-timezone": "-10.00",
        "User-Agent": f"ios;6.3.0;iPhone14,3;26.4;{HT_UID}",
        "Accept": "*/*",
        "x-ht-pub": x_ht_pub,
    }

    client = httpx.Client(base_url=BASE, headers=headers, timeout=30)

    # (name, method, path, GET-params-or-None, POST-body-or-None)
    probes = [
        # The big one — search plan / filter / error 6000 diagnostic
        ("enc_search_filter", "GET", "/go_user_search/v2/filter",
         {"userid": HT_UID, "learnlang": "2"}, None),
        # Discovery feed — are we appearing in recommendations?
        ("enc_search_recommend", "GET", "/go_user_search/v2/recommend",
         {"userid": HT_UID, "learnlang": "2", "page": "1"}, None),
        # Nearby user count for our location
        ("enc_nearby_count", "GET", "/go_user_search/v2/nearby_count",
         {"latitude": "20.7564", "longitude": "-155.9900",
          "learnlang": "2", "page": "1", "sort": "distance",
          "userid": HT_UID}, None),
        # Exposure record — reveals whether our moments are being shown
        ("enc_expose_record", "POST", "/v2/moment/query_expose_record",
         None, {"user_id": int(HT_UID)}),
        # Moments latest (our own feed)
        ("enc_moments_latest", "POST", "/v2/moment/latest",
         None, {"user_id": int(HT_UID), "page": 1, "count": 5}),
        # Moment tab info (visibility / engagement metadata)
        ("enc_moment_tab_info", "POST", "/go_moment/v2/get_moment_tab_info",
         None, {"user_id": int(HT_UID)}),
    ]

    print(f"== Encrypted API probes ==")
    print(f"  timestamp:  {ts}")
    print(f"  client_pub: {client_pub.hex()[:32]}...")
    print(f"  aes_key:    {aes_key.hex()[:32]}...")
    print(f"  x-ht-pub:   {len(x_ht_pub)} hex chars")
    print()

    for (name, method, path, params, body) in probes:
        meta_path = run_dir / f"{name}.meta"
        body_path = run_dir / f"{name}.body"

        try:
            if method == "GET":
                resp = client.get(path, params=params)
            else:
                plaintext = json.dumps(body).encode("utf-8")
                enc_body = aes_encrypt(plaintext, aes_key)
                resp = client.post(
                    path,
                    content=enc_body,
                    headers={"Content-Type": "ht/encbin"},
                )

            code = resp.status_code
            content = resp.content
            parsed, kind = try_parse(content, aes_key)

            # Write meta
            with open(meta_path, "w", encoding="utf-8") as f:
                f.write(f"name={name}\n")
                f.write(f"method={method}\n")
                f.write(f"path={path}\n")
                f.write(f"http_code={code}\n")
                f.write(f"content_length={len(content)}\n")
                f.write(f"content_type={resp.headers.get('content-type', '')}\n")
                f.write(f"parse_kind={kind}\n")

            # Write body
            with open(body_path, "w", encoding="utf-8") as f:
                if isinstance(parsed, (dict, list)):
                    json.dump(parsed, f, indent=2, ensure_ascii=False)
                else:
                    f.write(str(parsed) if parsed is not None else "")

            # Log line
            summary = ""
            if isinstance(parsed, dict):
                cfield = parsed.get("code")
                if cfield is None:
                    cfield = parsed.get("status")
                mfield = parsed.get("msg") or parsed.get("message") or ""
                summary = f"code={cfield} msg={mfield[:60]}"
            elif isinstance(parsed, str):
                summary = parsed[:60].replace("\n", " ")
            print(f"  {name:25s}  http={code}  [{kind}]  {summary}")

        except Exception as exc:
            with open(meta_path, "w", encoding="utf-8") as f:
                f.write(f"name={name}\n")
                f.write(f"error={exc}\n")
            print(f"  {name:25s}  EXCEPTION: {exc}")

        # Human-paced
        time.sleep(random.uniform(1.0, 2.5))

    client.close()

    # Copy enc_* files to monitor/latest/ WITHOUT wiping what's there from
    # the bash probe. The bash script runs first and populates latest/,
    # we just add our encrypted results alongside.
    for f in run_dir.glob("enc_*"):
        shutil.copy(f, latest_dir / f.name)

    print()
    print("== Done ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
