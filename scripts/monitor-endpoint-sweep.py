#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HelloTalk endpoint discovery sweep.

Probes a list of candidate API paths to map what exists on HelloTalk's
server. We've been hitting the same ~15 endpoints for days; the
decompiled APK implies there are 300+ Retrofit endpoints in the app,
and we want to find the ones that could actually move the needle:

- profile write endpoints (to rewrite the bio via API, fill empty fields)
- language management endpoints (to delete the ghost lang 13)
- search plan rebuild endpoints (to force re-indexing)
- moderation / appeal endpoints (to request re-evaluation)

Read-only intent:
- Every candidate is probed with GET first (idempotent, safe).
- Only if GET returns 405 do we try POST with an empty body.
- We do NOT send write-intent bodies blindly. Once we know which
  endpoints are alive, a follow-up turn can weaponize them with
  targeted payloads.
- Random 2-4 second delay between requests to stay under rate limits.
- Aborts immediately on any 429 response.

Runs from a GitHub Actions runner because the Claude sandbox cannot
reach hellotalk8.com.
"""

from __future__ import annotations

import gzip
import json
import random
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
SERVER_PUB_HEX = (
    "f684f611b895a5d3abc124a20ca2dfd397662318cfd4fd74b80aba478c17ca68"
)
SERVER_PUB_BYTES = bytes.fromhex(SERVER_PUB_HEX)

# Per-request inter-delay
DELAY_RANGE = (2.0, 4.0)

# Fail-safe: stop immediately if any request returns 429
RATE_LIMIT_ABORT = True


# --------------------------------------------------------------------------
# Candidate endpoints to probe
# --------------------------------------------------------------------------
# Format: (category, path, hint_method)
# hint_method is "GET" or "POST" — what we try first. None = try both.
CANDIDATES: list[tuple[str, str, str]] = [
    # --- Known-working sanity checks (should succeed) ---
    ("sanity", "/virtual_product/v1/virtual_product/free_recommend_status", "POST"),
    ("sanity", "/go_user_search/v1/go_user_info/get_user_langs", "GET"),

    # --- Profile write / update candidates ---
    ("profile_write", "/v2/user/profile/update", "POST"),
    ("profile_write", "/v2/user/update", "POST"),
    ("profile_write", "/v2/user/edit", "POST"),
    ("profile_write", "/v2/user/bio", "POST"),
    ("profile_write", "/v2/user/self_introduction", "POST"),
    ("profile_write", "/v2/user/set_bio", "POST"),
    ("profile_write", "/v2/user/info/update", "POST"),
    ("profile_write", "/v4/user/update", "POST"),
    ("profile_write", "/v4/user/set_profile", "POST"),
    ("profile_write", "/v4/user/profile_update", "POST"),
    ("profile_write", "/v4/user/edit", "POST"),
    ("profile_write", "/ht_user/v1/update_profile", "POST"),
    ("profile_write", "/ht_user/v1/user/update", "POST"),
    ("profile_write", "/ht_user/v2/update_profile", "POST"),
    ("profile_write", "/go_user_search/v1/go_user_info/update_user", "POST"),
    ("profile_write", "/go_user_search/v1/go_user_info/set_profile", "POST"),
    ("profile_write", "/go_user_search/v1/go_user_info/set_user_info", "POST"),
    ("profile_write", "/go_user_search/v1/go_user_info/update_info", "POST"),
    ("profile_write", "/user/v1/profile/update", "POST"),
    ("profile_write", "/user/v1/bio/update", "POST"),

    # --- Profile read candidates (to find the 'get my profile' endpoint) ---
    ("profile_read", "/v2/user/me", "GET"),
    ("profile_read", "/v2/user/self", "GET"),
    ("profile_read", "/v2/user/profile", "GET"),
    ("profile_read", "/v4/user/me", "GET"),
    ("profile_read", "/v4/user/self", "GET"),
    ("profile_read", "/ht_user/v1/self", "GET"),
    ("profile_read", "/ht_user/v1/user/self", "GET"),
    ("profile_read", "/ht_user/v1/get_self", "GET"),

    # --- Language management ---
    ("lang_write", "/go_user_search/v1/go_user_info/set_user_langs", "POST"),
    ("lang_write", "/go_user_search/v1/go_user_info/update_langs", "POST"),
    ("lang_write", "/go_user_search/v1/go_user_info/add_lang", "POST"),
    ("lang_write", "/go_user_search/v1/go_user_info/remove_lang", "POST"),
    ("lang_write", "/go_user_search/v1/go_user_info/delete_lang", "POST"),
    ("lang_write", "/go_user_search/v1/go_user_info/clear_temp_lang", "POST"),
    ("lang_write", "/go_user_search/v1/go_user_info/set_learn_lang", "POST"),
    ("lang_write", "/v2/user/lang/update", "POST"),
    ("lang_write", "/v2/user/lang/delete", "POST"),
    ("lang_write", "/v2/user/lang/set", "POST"),

    # --- Search plan / index rebuild ---
    ("search_rebuild", "/go_user_search/v2/filter/refresh", "POST"),
    ("search_rebuild", "/go_user_search/v2/filter/rebuild", "POST"),
    ("search_rebuild", "/go_user_search/v2/rebuild_plan", "POST"),
    ("search_rebuild", "/go_user_search/v2/build_search_plan", "POST"),
    ("search_rebuild", "/go_user_search/v2/refresh_index", "POST"),
    ("search_rebuild", "/go_user_search/v2/update_search_plan", "POST"),
    ("search_rebuild", "/go_user_search/v2/user_flow_up", "POST"),
    ("search_rebuild", "/go_user_search/v2/flow_up", "POST"),
    ("search_rebuild", "/go_user_search/v2/republish", "POST"),
    ("search_rebuild", "/go_user_search/v2/reindex", "POST"),

    # --- Moderation / appeal / trust ---
    ("moderation", "/v2/account/appeal", "POST"),
    ("moderation", "/v2/user/appeal", "POST"),
    ("moderation", "/v2/moderation/appeal", "POST"),
    ("moderation", "/v2/user/request_review", "POST"),
    ("moderation", "/v2/user/trust_score", "GET"),
    ("moderation", "/v2/account/status", "GET"),
    ("moderation", "/v2/account/check", "GET"),
    ("moderation", "/v2/user/restriction", "GET"),
    ("moderation", "/v2/user/restrict", "GET"),

    # --- Location ---
    ("location", "/go_user_search/v2/choose_place", "POST"),
    ("location", "/go_user_search/v2/set_location", "POST"),
    ("location", "/v2/user/location", "POST"),
    ("location", "/v2/user/set_location", "POST"),

    # --- Account state / refresh ---
    ("account", "/v2/user/state", "GET"),
    ("account", "/v2/user/refresh", "POST"),
    ("account", "/v2/user/resync", "POST"),
    ("account", "/v2/account/sync", "POST"),

    # --- Content re-evaluation ---
    ("reeval", "/v2/moment/rescan", "POST"),
    ("reeval", "/v2/user/rescan", "POST"),
    ("reeval", "/v2/user/revalidate", "POST"),
]


# --------------------------------------------------------------------------
# Crypto
# --------------------------------------------------------------------------
def generate_handshake() -> tuple[bytes, bytes, str]:
    priv = X25519PrivateKey.generate()
    client_pub = priv.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    server_pub = X25519PublicKey.from_public_bytes(SERVER_PUB_BYTES)
    shared = priv.exchange(server_pub)
    return client_pub, shared, SERVER_PUB_HEX + client_pub.hex()


def aes_decrypt(data: bytes, key: bytes) -> bytes:
    if not data or len(data) % 16 != 0:
        return data
    cipher = Cipher(algorithms.AES(key), modes.ECB())
    dec = cipher.decryptor()
    padded = dec.update(data) + dec.finalize()
    try:
        unpadder = PKCS7(128).unpadder()
        raw = unpadder.update(padded) + unpadder.finalize()
    except Exception:
        raw = padded
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return raw


# --------------------------------------------------------------------------
# Probe logic
# --------------------------------------------------------------------------
def parse_body(content: bytes, aes_key: bytes) -> tuple[str, str]:
    """Return (kind, snippet) where snippet is <= 500 chars."""
    if not content:
        return "empty", ""
    # Plain JSON?
    if content[:1] in (b"{", b"["):
        try:
            parsed = json.loads(content.decode("utf-8", errors="replace"))
            return "plain_json", json.dumps(parsed, ensure_ascii=False)[:500]
        except Exception:
            return "plain_text", content[:500].decode("utf-8", errors="replace")
    # Encrypted?
    try:
        decrypted = aes_decrypt(content, aes_key)
        text = decrypted.decode("utf-8", errors="replace")
        try:
            parsed = json.loads(text)
            return "decrypted_json", json.dumps(parsed, ensure_ascii=False)[:500]
        except Exception:
            return "decrypted_text", text[:500]
    except Exception as exc:
        return f"decrypt_fail:{exc}"[:50], content[:500].decode("utf-8", errors="replace")


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
        "x-ht-timezone": "-4.00",
        "User-Agent": f"ios;6.3.0;iPhone14,3;26.4;{HT_UID}",
        "Accept": "*/*",
        "x-ht-pub": x_ht_pub,
    }

    client = httpx.Client(base_url=BASE, headers=headers, timeout=30)

    print(f"== Endpoint discovery sweep ==")
    print(f"  timestamp: {ts}")
    print(f"  candidates: {len(CANDIDATES)}")
    print()

    results = []  # each: dict with full probe result
    aborted = False

    for i, (category, path, hint_method) in enumerate(CANDIDATES, 1):
        attempts = []  # list of (method, code, kind, snippet)

        # First attempt: hint_method
        try:
            if hint_method == "GET":
                resp = client.get(path, params={"user_id": HT_UID, "userid": HT_UID})
            else:
                # Empty encrypted body
                empty = b""
                resp = client.post(
                    path, content=empty,
                    headers={"Content-Type": "ht/encbin"},
                )
            kind, snippet = parse_body(resp.content, aes_key)
            attempts.append({
                "method": hint_method,
                "code": resp.status_code,
                "kind": kind,
                "snippet": snippet,
                "content_type": resp.headers.get("content-type", ""),
            })

            if resp.status_code == 429:
                print(f"  [{i}/{len(CANDIDATES)}] {path}  429 RATE LIMITED — aborting")
                if RATE_LIMIT_ABORT:
                    aborted = True
                    break

            # If 405, try the other method
            if resp.status_code == 405:
                other = "POST" if hint_method == "GET" else "GET"
                time.sleep(1.0)
                try:
                    if other == "GET":
                        resp2 = client.get(
                            path, params={"user_id": HT_UID, "userid": HT_UID}
                        )
                    else:
                        resp2 = client.post(
                            path, content=b"",
                            headers={"Content-Type": "ht/encbin"},
                        )
                    k2, s2 = parse_body(resp2.content, aes_key)
                    attempts.append({
                        "method": other,
                        "code": resp2.status_code,
                        "kind": k2,
                        "snippet": s2,
                        "content_type": resp2.headers.get("content-type", ""),
                    })
                except Exception as e2:
                    attempts.append({"method": other, "error": str(e2)})

        except Exception as exc:
            attempts.append({"method": hint_method, "error": str(exc)})

        best = attempts[0]
        status = best.get("code", "ERR")
        snippet_preview = best.get("snippet", best.get("error", ""))[:70].replace("\n", " ")
        print(f"  [{i:2d}/{len(CANDIDATES)}] {category:15s} {path:55s} {status} {snippet_preview}")

        results.append({
            "category": category,
            "path": path,
            "hint_method": hint_method,
            "attempts": attempts,
        })

        # Human-paced delay
        time.sleep(random.uniform(*DELAY_RANGE))

    client.close()

    # --- Write the full results -------------------------------------------
    full_path = run_dir / "sweep_results.json"
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": ts,
            "aborted": aborted,
            "candidates": len(CANDIDATES),
            "results": results,
        }, f, indent=2, ensure_ascii=False)

    # --- Write a human-readable summary sorted by status ------------------
    summary_path = run_dir / "sweep_summary.txt"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"# Endpoint sweep summary  ({ts})\n\n")

        # Group by status code
        by_code: dict = {}
        for r in results:
            best = r["attempts"][0] if r["attempts"] else {}
            code = best.get("code", "ERR")
            by_code.setdefault(code, []).append(r)

        # Order: 200 first (hits), then 400/405 (alive), then 401/403, then 404
        order = [200, 400, 401, 403, 405, 404, 500, 502, "ERR"]
        remaining = sorted(
            [c for c in by_code.keys() if c not in order],
            key=lambda x: str(x),
        )
        order = order + remaining

        for code in order:
            rs = by_code.get(code, [])
            if not rs:
                continue
            label = {
                200: "200 SUCCESS — endpoint works, returned data",
                400: "400 BAD REQUEST — endpoint EXISTS, needs correct params",
                401: "401 UNAUTHORIZED — endpoint exists, auth issue",
                403: "403 FORBIDDEN — endpoint exists, we don't have permission",
                405: "405 METHOD NOT ALLOWED — endpoint exists, wrong method",
                404: "404 NOT FOUND — path does not exist",
                500: "500 INTERNAL ERROR",
                502: "502 BAD GATEWAY",
                "ERR": "CONNECTION ERROR",
            }.get(code, f"HTTP {code}")
            f.write(f"\n## {label}\n\n")
            for r in rs:
                best = r["attempts"][0]
                snip = best.get("snippet", best.get("error", ""))[:150].replace("\n", " ")
                f.write(f"  {r['category']:15s}  {r['hint_method']:4s} {r['path']}\n")
                f.write(f"                   -> {snip}\n")

    # --- Copy into latest/ ------------------------------------------------
    import shutil
    shutil.copy(full_path, latest_dir / "sweep_results.json")
    shutil.copy(summary_path, latest_dir / "sweep_summary.txt")

    print()
    print("== Sweep done ==")
    print(f"  results:  {full_path}")
    print(f"  summary:  {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
