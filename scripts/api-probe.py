#!/usr/bin/env python3
"""
HelloTalk API Probe — Direct API access testing

Tests whether HelloTalk's API accepts unencrypted requests by:
1. Calling known endpoints WITHOUT the x-ht-pub encryption header
2. Using application/json content-type instead of ht/encbin
3. Probing for profile, trust score, and visibility data

This script needs your auth token. Get it from Proxyman:
  - Open any HelloTalk request in Proxyman
  - Copy the Authorization header value (the long Bearer eyJ... token)
  - Save it to captures/probe_auth.json

Usage:
    python scripts/api-probe.py              # Run all probes
    python scripts/api-probe.py --endpoint X # Probe specific endpoint
"""

import json
import sys
import time
import random
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Need httpx: pip install httpx")
    sys.exit(1)


BASE_URL = "https://api-global.hellotalk8.com"

# Known endpoints from traffic capture
PROBE_ENDPOINTS = {
    # === CONFIRMED WORKING (plain JSON) ===
    "boost_status": {
        "method": "POST",
        "path": "/virtual_product/v1/virtual_product/free_recommend_status",
        "body": {
            "os_version": "26.4",
            "nationality": "US",
            "lang_id": 1,
            "native_lang": 1,
            "os_type": 0,
            "user_id": None,  # filled from auth
            "app_version": "6.3.0",
            "virtual_type": 14,
        },
        "note": "Check remaining visibility boosts",
    },
    "boost_trigger": {
        "method": "POST",
        "path": "/virtual_product/v1/recommend/post_recommend_btn",
        "body": {
            "os_version": "26.4",
            "nationality": "US",
            "lang_id": 1,
            "native_lang": 1,
            "os_type": 0,
            "user_id": None,
            "app_version": "6.3.0",
        },
        "note": "Attempt to trigger a visibility boost",
    },
    "user_langs": {
        "method": "GET",
        "path": "/go_user_search/v1/go_user_info/get_user_langs",
        "params": {"user_id": None},
        "note": "Get language settings",
    },
    "translate_config": {
        "method": "POST",
        "path": "/translate/v1/config",
        "body": {},
        "note": "Translation configuration",
    },

    # === PROBING (may be encrypted, testing plain access) ===
    "moments_latest": {
        "method": "POST",
        "path": "/v2/moment/latest",
        "body": {
            "user_id": None,
            "page": 1,
            "count": 10,
        },
        "note": "Get latest moments — normally encrypted",
    },
    "exposure_record": {
        "method": "POST",
        "path": "/v2/moment/query_expose_record",
        "body": {
            "user_id": None,
        },
        "note": "Visibility/exposure metrics — the holy grail",
    },
    "moment_tab_info": {
        "method": "POST",
        "path": "/go_moment/v2/get_moment_tab_info",
        "body": {
            "user_id": None,
        },
        "note": "Moment tab configuration",
    },

    # === DISCOVERY PROBES ===
    "nearby_count": {
        "method": "GET",
        "path": "/go_user_search/v2/nearby_count",
        "params": {
            "latitude": "20.7564",   # Hana, Hawaii
            "longitude": "-155.9900",
            "learnlang": "2",        # Chinese
            "page": "1",
            "sort": "distance",
            "userid": None,
        },
        "note": "Nearby user count for discovery",
    },

    # === SPECULATIVE PROFILE ENDPOINTS ===
    # These are guesses based on common API patterns
    "user_profile_v1": {
        "method": "GET",
        "path": "/v1/user/profile",
        "params": {"user_id": None},
        "note": "Speculative: user profile v1",
    },
    "user_info": {
        "method": "GET",
        "path": "/v1/user/info",
        "params": {"user_id": None},
        "note": "Speculative: user info",
    },
    "account_status": {
        "method": "GET",
        "path": "/v1/account/status",
        "params": {"user_id": None},
        "note": "Speculative: account status / flags",
    },
    "user_setting": {
        "method": "GET",
        "path": "/v1/user/setting",
        "params": {"user_id": None},
        "note": "Speculative: user settings",
    },
    "go_user_info": {
        "method": "GET",
        "path": "/go_user_search/v1/go_user_info/get_user_info",
        "params": {"user_id": None},
        "note": "Speculative: full user info from search service",
    },
    "user_detail": {
        "method": "GET",
        "path": "/go_user_search/v1/go_user_info/get_user_detail",
        "params": {"user_id": None},
        "note": "Speculative: detailed user profile from search service",
    },
    "discovery_feed": {
        "method": "POST",
        "path": "/go_user_search/v2/discovery",
        "body": {
            "user_id": None,
            "learnlang": 2,
            "page": 1,
        },
        "note": "Speculative: discovery feed",
    },
    "partner_search": {
        "method": "POST",
        "path": "/go_user_search/v2/partner_search",
        "body": {
            "user_id": None,
            "learnlang": 2,
            "page": 1,
        },
        "note": "Speculative: partner search",
    },

    # === TRUST/BAN PROBES ===
    "account_restrict": {
        "method": "GET",
        "path": "/v1/account/restrict",
        "params": {"user_id": None},
        "note": "Speculative: restriction status",
    },
    "user_trust": {
        "method": "GET",
        "path": "/v1/user/trust_score",
        "params": {"user_id": None},
        "note": "Speculative: trust score",
    },
    "visibility_status": {
        "method": "GET",
        "path": "/v1/user/visibility",
        "params": {"user_id": None},
        "note": "Speculative: visibility status",
    },
}


def load_auth():
    """Load auth from file or prompt user."""
    auth_path = Path("captures/probe_auth.json")
    if auth_path.exists():
        with open(auth_path) as f:
            return json.load(f)

    print("=" * 60)
    print("  AUTH TOKEN NEEDED")
    print("=" * 60)
    print()
    print("  Open Proxyman on your iPhone:")
    print("  1. Tap any HelloTalk request")
    print("  2. Look at the request headers")
    print("  3. Find 'Authorization: Bearer eyJ...'")
    print("  4. Copy that ENTIRE value (including 'Bearer ')")
    print()
    print("  Also find these headers:")
    print("  - x-ht-uid (your user ID)")
    print("  - x-ht-did (device ID)")
    print()

    auth = {}
    token = input("Paste Authorization header value: ").strip()
    if token:
        auth["Authorization"] = token

    uid = input("Paste x-ht-uid value: ").strip()
    if uid:
        auth["x-ht-uid"] = uid

    did = input("Paste x-ht-did value: ").strip()
    if did:
        auth["x-ht-did"] = did

    if auth:
        auth_path.parent.mkdir(parents=True, exist_ok=True)
        with open(auth_path, "w") as f:
            json.dump(auth, f, indent=2)
        print(f"\nSaved to {auth_path}")

    return auth


def build_headers(auth, include_encryption=False):
    """Build request headers — deliberately omitting encryption by default."""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "x-ht-os": "ios",
        "x-ht-timezone": "-10.00",
        "User-Agent": "ios;6.3.0;iPhone14,3;26.4;98755150",
        "Accept-Language": "en-US;q=1.0, zh-Hans-US;q=0.9",
    }

    # Add auth headers
    for key, value in auth.items():
        headers[key] = value

    # Update user-agent with actual UID
    uid = auth.get("x-ht-uid", "98755150")
    headers["User-Agent"] = f"ios;6.3.0;iPhone14,3;26.4;{uid}"

    # Deliberately NOT including x-ht-pub — testing if server falls back to JSON
    if include_encryption:
        # Only if explicitly requested
        headers["Content-Type"] = "ht/encbin"
        # Would need actual ECDH key pair here

    return headers


def fill_user_id(data, uid):
    """Replace None user_id placeholders with actual UID."""
    if isinstance(data, dict):
        result = {}
        for k, v in data.items():
            if v is None and ("user" in k.lower() or "userid" in k.lower()):
                result[k] = uid
            elif isinstance(v, dict):
                result[k] = fill_user_id(v, uid)
            else:
                result[k] = v
        return result
    return data


def probe_endpoint(client, name, config, uid, results):
    """Probe a single endpoint and record the result."""
    method = config["method"]
    path = config["path"]
    note = config.get("note", "")

    print(f"\n{'─'*60}")
    print(f"  PROBE: {name}")
    print(f"  {method} {path}")
    print(f"  Note: {note}")

    # Human-like delay
    time.sleep(random.uniform(1.0, 2.5))

    try:
        kwargs = {}
        if "body" in config:
            kwargs["json"] = fill_user_id(config["body"], uid)
        if "params" in config:
            kwargs["params"] = fill_user_id(config["params"], uid)

        resp = client.request(method, path, **kwargs)

        result = {
            "endpoint": name,
            "method": method,
            "path": path,
            "status": resp.status_code,
            "content_type": resp.headers.get("content-type", ""),
            "response_size": len(resp.content),
            "headers": dict(resp.headers),
        }

        # Check for rate limiting
        for h, v in resp.headers.items():
            if any(w in h.lower() for w in ["rate", "limit", "retry", "throttle"]):
                print(f"  !! Rate limit header: {h}: {v}")
                result["rate_limited"] = True

        # Try to parse response
        try:
            body = resp.json()
            result["response"] = body
            result["readable"] = True

            preview = json.dumps(body, indent=2, ensure_ascii=False)
            if len(preview) > 500:
                print(f"  Status: {resp.status_code}")
                print(f"  Response (truncated):")
                print(f"  {preview[:500]}...")
            else:
                print(f"  Status: {resp.status_code}")
                print(f"  Response:")
                print(f"  {preview}")

            # Flag interesting fields
            body_str = json.dumps(body).lower()
            flags = []
            for keyword in ["restrict", "ban", "flag", "trust", "score",
                            "weight", "visible", "shadow", "penalty",
                            "suppress", "limit", "block", "rank",
                            "boost", "recommend", "exposure", "level"]:
                if keyword in body_str:
                    flags.append(keyword)
            if flags:
                print(f"\n  ** INTERESTING FIELDS DETECTED: {', '.join(flags)} **")
                result["interesting_flags"] = flags

        except (json.JSONDecodeError, ValueError):
            result["readable"] = False
            ct = resp.headers.get("content-type", "")
            if "ht/encbin" in ct:
                print(f"  Status: {resp.status_code}")
                print(f"  ENCRYPTED (ht/encbin) — {len(resp.content)} bytes")
                result["encrypted"] = True
            else:
                print(f"  Status: {resp.status_code}")
                print(f"  Not JSON — Content-Type: {ct}, {len(resp.content)} bytes")
                # Try to show raw content for small responses
                if len(resp.content) < 200:
                    print(f"  Raw: {resp.content}")

        results[name] = result
        return result

    except httpx.ConnectError as e:
        print(f"  CONNECTION FAILED: {e}")
        results[name] = {"error": str(e), "endpoint": name}
        return None
    except Exception as e:
        print(f"  ERROR: {e}")
        results[name] = {"error": str(e), "endpoint": name}
        return None


def run_all_probes(auth, specific_endpoint=None):
    """Run all probe endpoints and generate a report."""
    uid = auth.get("x-ht-uid", "98755150")
    headers = build_headers(auth, include_encryption=False)

    print(f"\n{'='*60}")
    print(f"  HELLOTALK API PROBE")
    print(f"  Testing {len(PROBE_ENDPOINTS)} endpoints")
    print(f"  User ID: {uid}")
    print(f"  Encryption: DISABLED (testing plaintext fallback)")
    print(f"{'='*60}")

    client = httpx.Client(
        base_url=BASE_URL,
        timeout=15,
        headers=headers,
        follow_redirects=True,
    )

    results = {}

    if specific_endpoint:
        if specific_endpoint in PROBE_ENDPOINTS:
            probe_endpoint(client, specific_endpoint,
                           PROBE_ENDPOINTS[specific_endpoint], uid, results)
        else:
            print(f"Unknown endpoint: {specific_endpoint}")
            print(f"Available: {', '.join(PROBE_ENDPOINTS.keys())}")
            return
    else:
        # Run confirmed endpoints first, then speculative
        confirmed = [k for k in PROBE_ENDPOINTS if "Speculative" not in PROBE_ENDPOINTS[k].get("note", "")]
        speculative = [k for k in PROBE_ENDPOINTS if "Speculative" in PROBE_ENDPOINTS[k].get("note", "")]

        print(f"\n  --- Phase 1: Confirmed endpoints ({len(confirmed)}) ---")
        for name in confirmed:
            probe_endpoint(client, name, PROBE_ENDPOINTS[name], uid, results)

        print(f"\n  --- Phase 2: Speculative endpoints ({len(speculative)}) ---")
        for name in speculative:
            probe_endpoint(client, name, PROBE_ENDPOINTS[name], uid, results)

    client.close()

    # === REPORT ===
    print(f"\n\n{'='*60}")
    print(f"  PROBE RESULTS SUMMARY")
    print(f"{'='*60}")

    readable = {k: v for k, v in results.items() if v.get("readable")}
    encrypted = {k: v for k, v in results.items() if v.get("encrypted")}
    errors = {k: v for k, v in results.items() if v.get("error")}
    other = {k: v for k, v in results.items()
             if k not in readable and k not in encrypted and k not in errors}

    print(f"\n  READABLE (plain JSON): {len(readable)}")
    for k in readable:
        status = results[k].get("status", "?")
        flags = results[k].get("interesting_flags", [])
        flag_str = f" ** {', '.join(flags)} **" if flags else ""
        print(f"    [{status}] {k}{flag_str}")

    print(f"\n  ENCRYPTED (ht/encbin): {len(encrypted)}")
    for k in encrypted:
        print(f"    [{results[k].get('status', '?')}] {k}")

    print(f"\n  ERRORS/FAILED: {len(errors)}")
    for k in errors:
        print(f"    {k}: {errors[k].get('error', '?')[:80]}")

    print(f"\n  OTHER: {len(other)}")
    for k in other:
        status = results[k].get("status", "?")
        ct = results[k].get("content_type", "?")[:40]
        print(f"    [{status}] {k} ({ct})")

    # Save full results
    output_path = Path("captures") / "probe_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str, ensure_ascii=False)
    print(f"\n  Full results saved to: {output_path}")

    # Highlight the most important finding
    if readable:
        print(f"\n{'='*60}")
        print(f"  KEY FINDING: {len(readable)} endpoints returned plain JSON!")
        print(f"  The encryption fallback hypothesis may be CONFIRMED.")
        print(f"{'='*60}")

    return results


if __name__ == "__main__":
    auth = load_auth()
    if not auth:
        print("No auth data. Cannot proceed.")
        sys.exit(1)

    specific = None
    for arg in sys.argv[1:]:
        if arg.startswith("--endpoint"):
            specific = sys.argv[sys.argv.index(arg) + 1]
        elif not arg.startswith("--"):
            specific = arg

    run_all_probes(auth, specific)
