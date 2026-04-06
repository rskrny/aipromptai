#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HelloTalk Encrypted API Client — Full ECIES decryption support.

Encryption fully cracked: X25519 key exchange -> AES-256-ECB + PKCS7.
Responses are gzipped then encrypted. The x-ht-pub header concatenates
server_pub_hex + client_pub_hex (128 hex chars total).

Subcommands:
    python scripts/ht-encrypted-client.py discovery          -- scan all discovery pages
    python scripts/ht-encrypted-client.py profile <userid>   -- get a user's profile
    python scripts/ht-encrypted-client.py compare <u1> <u2>  -- diff two profiles
    python scripts/ht-encrypted-client.py probe              -- probe all endpoints
    python scripts/ht-encrypted-client.py monitor            -- watch for account in discovery

Requires: pip install httpx cryptography
"""

import argparse
import gzip
import json
import os
import sys
import time
import random
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Force UTF-8 everywhere (Windows console compat)
# ---------------------------------------------------------------------------
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    import httpx
except ImportError:
    print("Need httpx: pip install httpx")
    sys.exit(1)

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.padding import PKCS7
except ImportError:
    print("Need cryptography: pip install cryptography")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Paths — resolve relative to repo root so the script works from anywhere
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
CAPTURES = REPO_ROOT / "captures"
AUTH_PATH = CAPTURES / "probe_auth.json"
KEYS_PATH = CAPTURES / "our_keys.json"

BASE_URL = "https://api-global.hellotalk8.com"
OUR_UID = "98755150"


# ===== Crypto helpers ======================================================

def decrypt_response(data: bytes, aes_key: bytes) -> str:
    """Decrypt an AES-256-ECB + PKCS7 + gzip response."""
    cipher = Cipher(algorithms.AES(aes_key), modes.ECB())
    decryptor = cipher.decryptor()
    padded = decryptor.update(data) + decryptor.finalize()
    try:
        unpadder = PKCS7(128).unpadder()
        raw = unpadder.update(padded) + unpadder.finalize()
    except Exception:
        raw = padded
    # gzip magic bytes
    if raw[:2] == b"\x1f\x8b":
        return gzip.decompress(raw).decode("utf-8", errors="replace")
    return raw.decode("utf-8", errors="replace")


def encrypt_body(data: bytes, aes_key: bytes) -> bytes:
    """Encrypt a request body with AES-256-ECB + PKCS7."""
    padder = PKCS7(128).padder()
    padded = padder.update(data) + padder.finalize()
    cipher = Cipher(algorithms.AES(aes_key), modes.ECB())
    encryptor = cipher.encryptor()
    return encryptor.update(padded) + encryptor.finalize()


# ===== Config loading =====================================================

def load_json(path: Path) -> dict:
    if not path.exists():
        print(f"[!] File not found: {path}")
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_keys() -> dict:
    keys = load_json(KEYS_PATH)
    if not keys:
        print("[!] No keys found. Put your key material in captures/our_keys.json")
        sys.exit(1)
    return keys


def load_auth() -> dict:
    auth = load_json(AUTH_PATH)
    if not auth:
        print("[!] No auth found. Put your auth headers in captures/probe_auth.json")
        sys.exit(1)
    return auth


def derive_aes_key(keys: dict) -> bytes:
    """shared_secret hex string -> 32 raw bytes = AES-256 key."""
    return bytes.fromhex(keys["shared_secret"])


# ===== HTTP client ========================================================

class HTClient:
    """HelloTalk encrypted API client."""

    def __init__(self):
        self.auth = load_auth()
        self.keys = load_keys()
        self.aes_key = derive_aes_key(self.keys)
        self.uid = self.auth.get("x-ht-uid", OUR_UID)
        self.headers = {
            "x-ht-version": "6.3.0",
            "x-ht-os": "ios",
            "x-ht-uid": self.uid,
            "x-ht-did": self.auth["x-ht-did"],
            "x-ht-timezone": "-10.00",
            "Authorization": self.auth["Authorization"],
            "User-Agent": f"ios;6.3.0;iPhone14,3;26.4;{self.uid}",
            "Accept": "*/*",
            "x-ht-pub": self.keys["x_ht_pub"],
        }
        self.client = httpx.Client(
            base_url=BASE_URL,
            timeout=30,
            headers=self.headers,
            follow_redirects=True,
        )
        self._req_count = 0

    def close(self):
        self.client.close()

    # --- low-level ---------------------------------------------------------

    def _delay(self):
        """Random 0.5-1.5 s pause between requests to stay polite."""
        time.sleep(random.uniform(0.5, 1.5))

    def _process_response(self, resp: httpx.Response) -> dict | str | None:
        """Decrypt or parse a response, return Python object."""
        ct = resp.headers.get("content-type", "")
        raw = resp.content

        if not raw:
            return None

        # Encrypted payload
        if "ht/encbin" in ct or (len(raw) > 0 and raw[:1] != b"{" and raw[:1] != b"["):
            try:
                text = decrypt_response(raw, self.aes_key)
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return text
            except Exception as exc:
                # Maybe it was plain text after all
                try:
                    return resp.json()
                except Exception:
                    return f"<decrypt failed: {exc}, {len(raw)} bytes>"

        # Plain JSON
        try:
            return resp.json()
        except Exception:
            return resp.text

    def get(self, path: str, params: dict | None = None,
            encrypted: bool = True) -> tuple[int, any]:
        """GET with optional encrypted response handling.
        Returns (status_code, parsed_body).
        """
        if self._req_count > 0:
            self._delay()
        self._req_count += 1

        hdrs = {}
        if not encrypted:
            hdrs["Accept"] = "application/json"

        resp = self.client.get(path, params=params, headers=hdrs)
        body = self._process_response(resp)
        return resp.status_code, body

    def post(self, path: str, body: dict | bytes | None = None,
             encrypted: bool = True) -> tuple[int, any]:
        """POST with encrypted body + encrypted response.
        Returns (status_code, parsed_body).
        """
        if self._req_count > 0:
            self._delay()
        self._req_count += 1

        hdrs = {}
        content = None
        json_body = None

        if encrypted and isinstance(body, dict):
            raw = json.dumps(body).encode("utf-8")
            content = encrypt_body(raw, self.aes_key)
            hdrs["Content-Type"] = "ht/encbin"
        elif encrypted and isinstance(body, bytes):
            content = encrypt_body(body, self.aes_key)
            hdrs["Content-Type"] = "ht/encbin"
        elif isinstance(body, dict):
            json_body = body
            hdrs["Content-Type"] = "application/json"
        else:
            content = body

        resp = self.client.post(path, content=content, json=json_body, headers=hdrs)
        parsed = self._process_response(resp)
        return resp.status_code, parsed

    def post_plain(self, path: str, body: dict | None = None) -> tuple[int, any]:
        """POST without encryption (plain JSON in, JSON out)."""
        return self.post(path, body=body, encrypted=False)


# ===== Saving results =====================================================

def save_json(name: str, data) -> Path:
    """Write data to captures/<name>.json with a timestamp suffix."""
    CAPTURES.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = CAPTURES / f"{name}_{ts}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    print(f"  -> saved {out.name}")
    return out


def save_overwrite(name: str, data) -> Path:
    """Write data to captures/<name>.json (overwrite, no timestamp)."""
    CAPTURES.mkdir(parents=True, exist_ok=True)
    out = CAPTURES / f"{name}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    print(f"  -> saved {out.name}")
    return out


# ===== Endpoint catalog ===================================================
# Endpoints are grouped by whether they require encryption or not.

# Encrypted endpoints (need x-ht-pub + ht/encbin)
ENCRYPTED_ENDPOINTS = {
    "moments_latest": {
        "method": "POST", "path": "/v2/moment/latest",
        "body": {"user_id": None, "page": 1, "count": 20},
    },
    "exposure_record": {
        "method": "POST", "path": "/v2/moment/query_expose_record",
        "body": {"user_id": None},
    },
    "moment_tab_info": {
        "method": "POST", "path": "/go_moment/v2/get_moment_tab_info",
        "body": {"user_id": None},
    },
    "nearby_count": {
        "method": "GET", "path": "/go_user_search/v2/nearby_count",
        "params": {
            "latitude": "20.7564", "longitude": "-155.9900",
            "learnlang": "2", "page": "1", "sort": "distance",
            "userid": None,
        },
    },
    "discovery_recommend": {
        "method": "POST", "path": "/go_user_search/v2/discovery_recommend",
        "body": {
            "user_id": None, "learnlang": 2, "page": 1,
            "page_size": 30, "sort": "recommend",
        },
    },
    "moment_view": {
        "method": "POST", "path": "/v2/moment/view_content",
        "body": {"user_id": None, "moment_id": ""},
    },
    "moment_like": {
        "method": "POST", "path": "/v2/moment/like",
        "body": {"user_id": None, "moment_id": ""},
    },
}

# Plain JSON endpoints (no encryption needed)
PLAIN_ENDPOINTS = {
    "boost_status": {
        "method": "POST",
        "path": "/virtual_product/v1/virtual_product/free_recommend_status",
        "body": {
            "os_version": "26.4", "nationality": "US", "lang_id": 1,
            "native_lang": 1, "os_type": 0, "user_id": None,
            "app_version": "6.3.0", "virtual_type": 14,
        },
    },
    "boost_trigger": {
        "method": "POST",
        "path": "/virtual_product/v1/recommend/post_recommend_btn",
        "body": {
            "os_version": "26.4", "nationality": "US", "lang_id": 1,
            "native_lang": 1, "os_type": 0, "user_id": None,
            "app_version": "6.3.0",
        },
    },
    "user_langs": {
        "method": "GET",
        "path": "/go_user_search/v1/go_user_info/get_user_langs",
        "params": {"user_id": None},
    },
    "translate_config": {
        "method": "POST",
        "path": "/translate/v1/config",
        "body": {},
    },
}

# Speculative / probing endpoints (some encrypted, some unknown)
PROBE_ENDPOINTS = {
    "user_profile_encrypted": {
        "method": "POST", "path": "/v4/user/profile",
        "body": {"user_id": None},
    },
    "user_info_encrypted": {
        "method": "POST", "path": "/v4/user/info",
        "body": {"user_id": None},
    },
    "user_detail_search": {
        "method": "POST", "path": "/go_user_search/v2/get_user_detail",
        "body": {"user_id": None},
    },
    "user_card": {
        "method": "POST", "path": "/go_user_search/v2/user_card",
        "body": {"user_id": None},
    },
    "partner_search": {
        "method": "POST", "path": "/go_user_search/v2/partner_search",
        "body": {"user_id": None, "learnlang": 2, "page": 1},
    },
    "discovery_feed_v2": {
        "method": "POST", "path": "/go_user_search/v2/discovery",
        "body": {"user_id": None, "learnlang": 2, "page": 1},
    },
    "account_restrict_enc": {
        "method": "POST", "path": "/v2/account/restrict",
        "body": {"user_id": None},
    },
    "user_trust_enc": {
        "method": "POST", "path": "/v2/user/trust_score",
        "body": {"user_id": None},
    },
    "visibility_status_enc": {
        "method": "POST", "path": "/v2/user/visibility",
        "body": {"user_id": None},
    },
    "user_profile_v2": {
        "method": "GET", "path": "/v2/user/profile",
        "params": {"user_id": None},
    },
    "user_info_v2": {
        "method": "GET", "path": "/v2/user/info",
        "params": {"user_id": None},
    },
    "get_user_info_search": {
        "method": "GET",
        "path": "/go_user_search/v1/go_user_info/get_user_info",
        "params": {"user_id": None},
    },
    "get_user_detail_v1": {
        "method": "GET",
        "path": "/go_user_search/v1/go_user_info/get_user_detail",
        "params": {"user_id": None},
    },
}


def fill_uid(data: dict | None, uid: str) -> dict | None:
    """Replace None values in user_id / userid fields with actual UID."""
    if data is None:
        return None
    out = {}
    for k, v in data.items():
        if v is None and ("user" in k.lower() or "userid" in k.lower()):
            out[k] = uid
        elif isinstance(v, dict):
            out[k] = fill_uid(v, uid)
        else:
            out[k] = v
    return out


# ===== Subcommands ========================================================

def cmd_discovery(client: HTClient, args):
    """Scan all discovery pages and collect user profiles."""
    max_pages = args.pages if hasattr(args, "pages") and args.pages else 20
    all_users = []
    page = 1

    print(f"\n{'='*60}")
    print(f"  DISCOVERY SCAN  (up to {max_pages} pages)")
    print(f"{'='*60}\n")

    while page <= max_pages:
        print(f"  [page {page}] fetching...")
        body = {
            "user_id": int(client.uid),
            "learnlang": 2,
            "page": page,
            "page_size": 30,
            "sort": "recommend",
        }
        status, resp = client.post("/go_user_search/v2/discovery_recommend", body=body)
        print(f"    status={status}")

        if status != 200:
            # Try alternate endpoint
            print("    trying alternate /v4/discovery/recommend ...")
            status, resp = client.post("/v4/discovery/recommend", body=body)
            print(f"    status={status}")

        if status != 200:
            print("    trying /go_user_search/v2/nearby_count (GET) ...")
            params = fill_uid({
                "latitude": "20.7564", "longitude": "-155.9900",
                "learnlang": "2", "page": str(page), "sort": "recommend",
                "userid": None,
            }, client.uid)
            status, resp = client.get(
                "/go_user_search/v2/nearby_count", params=params
            )
            print(f"    status={status}")

        if not resp or not isinstance(resp, dict):
            print(f"    no parseable response, stopping. raw={str(resp)[:200]}")
            break

        data = resp.get("data", resp)
        results = []
        if isinstance(data, dict):
            results = data.get("results", data.get("list", data.get("users", [])))
        elif isinstance(data, list):
            results = data

        if not results:
            print(f"    0 results, end of discovery feed.")
            break

        print(f"    got {len(results)} users")
        for u in results:
            uid_field = u.get("user_id") or u.get("id") or u.get("uid", "?")
            name = u.get("nickname") or u.get("name") or u.get("from_nickname", "?")
            nat = u.get("nationality", "?")
            print(f"      {uid_field}  {name}  ({nat})")

        all_users.extend(results)
        page += 1

    print(f"\n  TOTAL: {len(all_users)} users across {page - 1} pages\n")

    # Check if our account appears
    our_ids = {OUR_UID, int(OUR_UID)}
    found = [u for u in all_users
             if u.get("user_id") in our_ids or u.get("id") in our_ids]
    if found:
        print("  ** YOUR ACCOUNT WAS FOUND IN DISCOVERY **")
    else:
        print("  -- your account was NOT found in these results --")

    save_json("discovery_scan", {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "pages": page - 1,
        "total_users": len(all_users),
        "own_account_found": bool(found),
        "users": all_users,
    })
    return all_users


def cmd_profile(client: HTClient, args):
    """Fetch a user's profile via encrypted endpoint."""
    target = args.userid if hasattr(args, "userid") and args.userid else client.uid
    print(f"\n{'='*60}")
    print(f"  PROFILE FETCH  user_id={target}")
    print(f"{'='*60}\n")

    results = {}

    # Try multiple endpoint patterns, encrypted first
    attempts = [
        ("POST /v4/user/profile",
         lambda: client.post("/v4/user/profile", body={"user_id": int(target)})),
        ("POST /v4/user/info",
         lambda: client.post("/v4/user/info", body={"user_id": int(target)})),
        ("POST /v2/user/profile",
         lambda: client.post("/v2/user/profile", body={"user_id": int(target)})),
        ("POST /v2/user/info",
         lambda: client.post("/v2/user/info", body={"user_id": int(target)})),
        ("POST /go_user_search/v2/get_user_detail",
         lambda: client.post("/go_user_search/v2/get_user_detail",
                             body={"user_id": int(target)})),
        ("POST /go_user_search/v2/user_card",
         lambda: client.post("/go_user_search/v2/user_card",
                             body={"user_id": int(target)})),
        ("GET /go_user_search/v1/go_user_info/get_user_detail",
         lambda: client.get("/go_user_search/v1/go_user_info/get_user_detail",
                            params={"user_id": target})),
        ("GET /go_user_search/v1/go_user_info/get_user_info",
         lambda: client.get("/go_user_search/v1/go_user_info/get_user_info",
                            params={"user_id": target})),
        ("GET /go_user_search/v1/go_user_info/get_user_langs",
         lambda: client.get("/go_user_search/v1/go_user_info/get_user_langs",
                            params={"user_id": target}, encrypted=False)),
    ]

    for label, call_fn in attempts:
        print(f"  trying {label} ...")
        try:
            status, resp = call_fn()
            results[label] = {"status": status, "body": resp}
            print(f"    status={status}")
            if resp and isinstance(resp, dict):
                code = resp.get("code", resp.get("status", ""))
                msg = resp.get("msg", resp.get("message", ""))
                print(f"    code={code}  msg={msg}")
                data = resp.get("data", {})
                if isinstance(data, dict) and data:
                    for k in list(data.keys())[:15]:
                        print(f"    {k}: {str(data[k])[:80]}")
                    # Found real data, save and return early
                    if any(k in data for k in ("nickname", "name", "user_id",
                                                "nationality", "gender")):
                        print(f"\n  ** Profile data found via {label} **\n")
                        save_json(f"profile_{target}", {"endpoint": label, "data": data})
                        return data
            elif resp and isinstance(resp, str):
                print(f"    body[:200]={resp[:200]}")
        except Exception as exc:
            print(f"    ERROR: {exc}")
            results[label] = {"error": str(exc)}

    # Save whatever we got
    save_json(f"profile_{target}", results)
    print("\n  No profile data found from any endpoint.")
    return results


def cmd_compare(client: HTClient, args):
    """Fetch two profiles and diff their fields."""
    uid1 = args.userid1
    uid2 = args.userid2
    print(f"\n{'='*60}")
    print(f"  COMPARE  {uid1}  vs  {uid2}")
    print(f"{'='*60}\n")

    # Reuse profile logic
    class FakeArgs:
        pass

    a1 = FakeArgs()
    a1.userid = uid1
    p1 = cmd_profile(client, a1)

    a2 = FakeArgs()
    a2.userid = uid2
    p2 = cmd_profile(client, a2)

    if not isinstance(p1, dict) or not isinstance(p2, dict):
        print("\n  Cannot compare: one or both profiles failed to load.")
        save_json(f"compare_{uid1}_vs_{uid2}", {
            "user1": {"uid": uid1, "data": p1},
            "user2": {"uid": uid2, "data": p2},
            "diff": "incomplete",
        })
        return

    # Build diff
    all_keys = sorted(set(list(p1.keys()) + list(p2.keys())))
    diff = {}
    same = {}
    only1 = {}
    only2 = {}

    for k in all_keys:
        in1 = k in p1
        in2 = k in p2
        if in1 and in2:
            if p1[k] == p2[k]:
                same[k] = p1[k]
            else:
                diff[k] = {"user1": p1[k], "user2": p2[k]}
        elif in1:
            only1[k] = p1[k]
        else:
            only2[k] = p2[k]

    print(f"\n{'='*60}")
    print(f"  COMPARISON RESULTS")
    print(f"{'='*60}")
    print(f"\n  Same fields ({len(same)}):")
    for k, v in same.items():
        print(f"    {k}: {str(v)[:60]}")
    print(f"\n  Different fields ({len(diff)}):")
    for k, vals in diff.items():
        print(f"    {k}:")
        print(f"      user1: {str(vals['user1'])[:60]}")
        print(f"      user2: {str(vals['user2'])[:60]}")
    if only1:
        print(f"\n  Only in user1 ({len(only1)}):")
        for k, v in only1.items():
            print(f"    {k}: {str(v)[:60]}")
    if only2:
        print(f"\n  Only in user2 ({len(only2)}):")
        for k, v in only2.items():
            print(f"    {k}: {str(v)[:60]}")

    result = {
        "user1": uid1, "user2": uid2,
        "same": same, "diff": diff,
        "only_user1": only1, "only_user2": only2,
    }
    save_json(f"compare_{uid1}_vs_{uid2}", result)
    return result


def cmd_probe(client: HTClient, args):
    """Probe all known endpoints (plain + encrypted + speculative)."""
    print(f"\n{'='*60}")
    print(f"  ENDPOINT PROBE  (encrypted client)")
    print(f"{'='*60}\n")

    all_results = {}

    def probe_one(name: str, spec: dict, encrypted: bool):
        method = spec["method"]
        path = spec["path"]
        print(f"\n  [{name}] {method} {path}")

        try:
            if method == "GET":
                params = fill_uid(spec.get("params"), client.uid)
                status, resp = client.get(path, params=params, encrypted=encrypted)
            else:
                body = fill_uid(spec.get("body"), client.uid)
                if encrypted:
                    status, resp = client.post(path, body=body, encrypted=True)
                else:
                    status, resp = client.post_plain(path, body=body)

            entry = {
                "status": status,
                "encrypted": encrypted,
                "response": resp,
            }

            print(f"    status={status}")
            if isinstance(resp, dict):
                code = resp.get("code", resp.get("status", ""))
                msg = resp.get("msg", resp.get("message", ""))
                print(f"    code={code}  msg={msg}")
                # Flag interesting fields
                body_str = json.dumps(resp).lower()
                flags = [kw for kw in (
                    "restrict", "ban", "trust", "score", "weight",
                    "visible", "shadow", "penalty", "suppress",
                    "rank", "boost", "recommend", "exposure", "level",
                ) if kw in body_str]
                if flags:
                    entry["interesting"] = flags
                    print(f"    ** flags: {', '.join(flags)} **")
            elif isinstance(resp, str):
                print(f"    body[:150]={resp[:150]}")

            all_results[name] = entry
        except Exception as exc:
            print(f"    ERROR: {exc}")
            all_results[name] = {"error": str(exc)}

    # Phase 1: plain endpoints
    print("  --- Phase 1: Plain JSON endpoints ---")
    for name, spec in PLAIN_ENDPOINTS.items():
        probe_one(name, spec, encrypted=False)

    # Phase 2: encrypted endpoints
    print("\n  --- Phase 2: Encrypted endpoints ---")
    for name, spec in ENCRYPTED_ENDPOINTS.items():
        probe_one(name, spec, encrypted=True)

    # Phase 3: speculative endpoints (try encrypted)
    print("\n  --- Phase 3: Speculative endpoints (encrypted) ---")
    for name, spec in PROBE_ENDPOINTS.items():
        probe_one(name, spec, encrypted=True)

    # Summary
    print(f"\n{'='*60}")
    print(f"  PROBE SUMMARY")
    print(f"{'='*60}")

    success = {k: v for k, v in all_results.items()
               if isinstance(v.get("status"), int) and v["status"] == 200}
    errored = {k: v for k, v in all_results.items()
               if v.get("error") or (isinstance(v.get("status"), int) and v["status"] >= 400)}
    interesting = {k: v for k, v in all_results.items() if v.get("interesting")}

    print(f"\n  Success (200): {len(success)}")
    for k in success:
        print(f"    {k}")
    print(f"\n  Error/4xx+: {len(errored)}")
    for k in errored:
        s = all_results[k].get("status", "?")
        e = all_results[k].get("error", "")[:60]
        print(f"    [{s}] {k} {e}")
    if interesting:
        print(f"\n  ** INTERESTING ({len(interesting)}) **")
        for k, v in interesting.items():
            print(f"    {k}: {v['interesting']}")

    save_json("probe_encrypted", all_results)
    return all_results


def cmd_monitor(client: HTClient, args):
    """Continuously check whether our account appears in discovery results.
    Runs until interrupted or --rounds is exhausted.
    """
    max_rounds = args.rounds if hasattr(args, "rounds") and args.rounds else 0
    interval = args.interval if hasattr(args, "interval") and args.interval else 300
    round_num = 0

    print(f"\n{'='*60}")
    print(f"  VISIBILITY MONITOR")
    print(f"  Checking every {interval}s  |  rounds={'inf' if max_rounds == 0 else max_rounds}")
    print(f"  Looking for UID {OUR_UID} in discovery results")
    print(f"{'='*60}\n")

    log = []

    try:
        while True:
            round_num += 1
            ts = datetime.now(timezone.utc).isoformat()
            print(f"\n  --- round {round_num}  {ts} ---")

            found = False
            pages_checked = 0
            users_seen = 0

            # Check a few discovery pages
            for page in range(1, 4):
                body = {
                    "user_id": int(client.uid),
                    "learnlang": 2,
                    "page": page,
                    "page_size": 30,
                    "sort": "recommend",
                }
                status, resp = client.post(
                    "/go_user_search/v2/discovery_recommend", body=body
                )
                pages_checked += 1

                if not resp or not isinstance(resp, dict):
                    break

                data = resp.get("data", resp)
                results = []
                if isinstance(data, dict):
                    results = data.get("results", data.get("list", []))
                elif isinstance(data, list):
                    results = data
                if not results:
                    break

                users_seen += len(results)
                our_ids = {OUR_UID, int(OUR_UID)}
                for u in results:
                    if u.get("user_id") in our_ids or u.get("id") in our_ids:
                        found = True
                        break
                if found:
                    break

            # Also check boost status (plain endpoint)
            boost_body = fill_uid(PLAIN_ENDPOINTS["boost_status"]["body"], client.uid)
            b_status, b_resp = client.post_plain(
                PLAIN_ENDPOINTS["boost_status"]["path"], body=boost_body
            )
            remain = "?"
            if isinstance(b_resp, dict):
                remain = (b_resp.get("data", {}) or {}).get("remain_times", "?")

            entry = {
                "round": round_num,
                "time": ts,
                "visible": found,
                "pages_checked": pages_checked,
                "users_seen": users_seen,
                "boost_remain": remain,
            }
            log.append(entry)
            print(f"    visible={found}  users_seen={users_seen}  "
                  f"boost_remain={remain}")

            if found:
                print("\n  ** ACCOUNT IS VISIBLE IN DISCOVERY! **\n")

            # Save log every round
            save_overwrite("monitor_log", log)

            if max_rounds > 0 and round_num >= max_rounds:
                print(f"\n  Completed {max_rounds} rounds. Stopping.")
                break

            print(f"    sleeping {interval}s until next check...")
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\n  Monitor stopped by user.")
        save_overwrite("monitor_log", log)

    return log


# ===== Generic GET/POST any endpoint =====================================

def cmd_request(client: HTClient, args):
    """Make a raw GET or POST request to any endpoint."""
    method = args.method.upper()
    path = args.path

    print(f"\n  {method} {path}")

    if method == "GET":
        status, resp = client.get(path, encrypted=True)
    else:
        body = None
        if args.body:
            try:
                body = json.loads(args.body)
            except json.JSONDecodeError:
                body = args.body.encode("utf-8")
        status, resp = client.post(path, body=body, encrypted=True)

    print(f"  status={status}")
    if isinstance(resp, dict):
        print(json.dumps(resp, indent=2, ensure_ascii=False))
    elif isinstance(resp, str):
        print(resp[:2000])
    else:
        print(repr(resp)[:500])

    return resp


# ===== CLI ================================================================

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ht-encrypted-client",
        description="HelloTalk encrypted API client (AES-256-ECB / X25519)",
    )
    sub = p.add_subparsers(dest="command")

    # discovery
    d = sub.add_parser("discovery", help="Scan discovery pages")
    d.add_argument("--pages", type=int, default=20,
                   help="Max pages to scan (default: 20)")

    # profile
    pr = sub.add_parser("profile", help="Fetch user profile")
    pr.add_argument("userid", nargs="?", default=None,
                    help="User ID (default: your own)")

    # compare
    c = sub.add_parser("compare", help="Compare two profiles")
    c.add_argument("userid1", help="First user ID")
    c.add_argument("userid2", help="Second user ID")

    # probe
    sub.add_parser("probe", help="Probe all endpoints")

    # monitor
    m = sub.add_parser("monitor", help="Monitor account visibility")
    m.add_argument("--rounds", type=int, default=0,
                   help="Number of rounds (0 = infinite)")
    m.add_argument("--interval", type=int, default=300,
                   help="Seconds between checks (default: 300)")

    # raw request
    r = sub.add_parser("request", help="Raw GET/POST to any endpoint")
    r.add_argument("method", choices=["GET", "POST", "get", "post"])
    r.add_argument("path", help="API path, e.g. /v2/moment/latest")
    r.add_argument("--body", default=None,
                   help="JSON body for POST (as string)")

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    client = HTClient()
    try:
        dispatch = {
            "discovery": cmd_discovery,
            "profile": cmd_profile,
            "compare": cmd_compare,
            "probe": cmd_probe,
            "monitor": cmd_monitor,
            "request": cmd_request,
        }
        fn = dispatch.get(args.command)
        if fn:
            fn(client, args)
        else:
            parser.print_help()
    finally:
        client.close()


if __name__ == "__main__":
    main()
