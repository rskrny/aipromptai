#!/usr/bin/env python3
"""
HelloTalk Traffic Capture Guide + Auto-Analyzer

This script analyzes HAR files exported from browser DevTools.

HOW TO GET THE HAR FILE (do this on your computer):
1. Open Chrome/Edge/Firefox on your computer
2. Go to web.hellotalk.com and log in with your HelloTalk account
3. Press F12 to open Developer Tools
4. Click the "Network" tab
5. Check "Preserve log" checkbox
6. Now USE the app: browse discovery, open your profile, check moments, etc.
7. Right-click in the Network panel → "Save all as HAR with content"
8. Save the file and upload it to this repo's captures/ folder

That's it — the script handles the rest.
"""

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict
from urllib.parse import urlparse, parse_qs


def load_har(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze_har(har, output_dir="captures"):
    entries = har.get("log", {}).get("entries", [])

    # Separate HelloTalk traffic from everything else
    ht_entries = []
    other_hosts = Counter()

    for entry in entries:
        url = entry["request"]["url"]
        parsed = urlparse(url)
        host = parsed.netloc

        if "hellotalk" in host.lower():
            ht_entries.append(entry)
        else:
            other_hosts[host] += 1

    print(f"\n{'='*70}")
    print(f"  HelloTalk Traffic Analysis")
    print(f"{'='*70}")
    print(f"\n  Total requests captured: {len(entries)}")
    print(f"  HelloTalk requests: {len(ht_entries)}")
    print(f"  Other hosts: {len(other_hosts)}")

    if not ht_entries:
        print("\n  ⚠ No HelloTalk traffic found!")
        print("  Make sure you captured while using web.hellotalk.com")
        return

    # === HOSTS ===
    ht_hosts = Counter()
    for e in ht_entries:
        host = urlparse(e["request"]["url"]).netloc
        ht_hosts[host] += 1

    print(f"\n{'─'*70}")
    print("  HELLOTALK HOSTS (subdomains found)")
    print(f"{'─'*70}")
    for host, count in ht_hosts.most_common():
        print(f"    {count:>5}x  {host}")

    # === ENDPOINTS ===
    endpoints = defaultdict(list)
    for e in ht_entries:
        req = e["request"]
        resp = e["response"]
        parsed = urlparse(req["url"])
        path = parsed.path
        method = req["method"]
        status = resp["status"]
        key = f"{method} {path}"

        endpoints[key].append({
            "url": req["url"],
            "status": status,
            "query": parsed.query,
            "request_headers": {h["name"]: h["value"] for h in req.get("headers", [])},
            "response_headers": {h["name"]: h["value"] for h in resp.get("headers", [])},
            "request_body": _get_body(req),
            "response_body": _get_body(resp),
            "response_size": resp.get("content", {}).get("size", 0),
            "time": e.get("time", 0),
        })

    print(f"\n{'─'*70}")
    print("  API ENDPOINTS (by frequency)")
    print(f"{'─'*70}")
    for key, calls in sorted(endpoints.items(), key=lambda x: -len(x[1])):
        statuses = set(c["status"] for c in calls)
        print(f"    {len(calls):>5}x  {key}  → {statuses}")

    # === AUTH HEADERS ===
    print(f"\n{'─'*70}")
    print("  AUTHENTICATION (from first request)")
    print(f"{'─'*70}")
    if ht_entries:
        headers = {h["name"]: h["value"] for h in ht_entries[0]["request"].get("headers", [])}
        auth_keywords = ["auth", "token", "cookie", "session", "api-key", "x-ht", "x-hello"]
        found_auth = False
        for name, value in sorted(headers.items()):
            if any(kw in name.lower() for kw in auth_keywords):
                # Mask sensitive values
                masked = _mask(value)
                print(f"    {name}: {masked}")
                found_auth = True
        if not found_auth:
            print("    No obvious auth headers found. Check cookies:")
            cookie = headers.get("Cookie", headers.get("cookie", ""))
            if cookie:
                # Show cookie names but mask values
                for part in cookie.split(";"):
                    part = part.strip()
                    if "=" in part:
                        cname, cval = part.split("=", 1)
                        print(f"    Cookie: {cname.strip()} = {_mask(cval.strip())}")

    # === DISCOVERY / MATCHING ENDPOINTS ===
    print(f"\n{'─'*70}")
    print("  DISCOVERY / MATCHING RELATED")
    print(f"{'─'*70}")
    discovery_keywords = ["discover", "match", "search", "find", "partner", "recommend", "nearby", "explore"]
    found_discovery = False
    for key, calls in endpoints.items():
        if any(kw in key.lower() for kw in discovery_keywords):
            print(f"    {key}")
            # Show query params from first call
            if calls[0]["query"]:
                params = parse_qs(calls[0]["query"])
                for pname, pvals in params.items():
                    print(f"      param: {pname} = {pvals[0][:100]}")
            found_discovery = True
    if not found_discovery:
        print("    No obvious discovery endpoints found yet.")
        print("    Try browsing the 'Find Partners' tab while capturing.")

    # === MOMENTS ENDPOINTS ===
    print(f"\n{'─'*70}")
    print("  MOMENTS / SOCIAL FEED")
    print(f"{'─'*70}")
    moment_keywords = ["moment", "feed", "post", "timeline", "like", "comment", "correct"]
    found_moments = False
    for key, calls in endpoints.items():
        if any(kw in key.lower() for kw in moment_keywords):
            print(f"    {key}")
            found_moments = True
    if not found_moments:
        print("    No moments endpoints found. Try browsing Moments while capturing.")

    # === USER / PROFILE ===
    print(f"\n{'─'*70}")
    print("  USER / PROFILE")
    print(f"{'─'*70}")
    user_keywords = ["user", "profile", "account", "me", "setting"]
    for key, calls in endpoints.items():
        if any(kw in key.lower() for kw in user_keywords):
            print(f"    {key}")

    # === EXPORT FULL DATA ===
    output_path = Path(output_dir) / "analyzed_endpoints.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    export = {}
    for key, calls in endpoints.items():
        export[key] = {
            "count": len(calls),
            "statuses": list(set(c["status"] for c in calls)),
            "example_url": calls[0]["url"],
            "query_params": parse_qs(calls[0]["query"]) if calls[0]["query"] else {},
            "request_headers": calls[0]["request_headers"],
            "response_sample": calls[0]["response_body"][:2000] if calls[0]["response_body"] else None,
        }

    with open(output_path, "w") as f:
        json.dump(export, f, indent=2, default=str)
    print(f"\n{'─'*70}")
    print(f"  Full analysis exported to: {output_path}")
    print(f"{'='*70}\n")

    # === EXPORT AUTH TOKEN (for API client) ===
    auth_path = Path(output_dir) / "auth_token.json"
    if ht_entries:
        headers = {h["name"]: h["value"] for h in ht_entries[0]["request"].get("headers", [])}
        auth_data = {}
        for name, value in headers.items():
            if any(kw in name.lower() for kw in ["auth", "token", "cookie", "x-ht", "x-hello"]):
                auth_data[name] = value
        if auth_data:
            with open(auth_path, "w") as f:
                json.dump(auth_data, f, indent=2)
            print(f"  Auth token(s) saved to: {auth_path}")
            print(f"  ⚠ KEEP THIS FILE PRIVATE — do not commit to git!\n")


def _get_body(req_or_resp):
    """Extract body text from a HAR request or response."""
    # For requests
    if "postData" in req_or_resp:
        return req_or_resp["postData"].get("text", "")
    # For responses
    if "content" in req_or_resp:
        return req_or_resp["content"].get("text", "")
    return ""


def _mask(value):
    """Mask a sensitive string, showing first 8 and last 4 chars."""
    if len(value) <= 16:
        return value[:4] + "..." + value[-2:]
    return value[:8] + "..." + value[-4:]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("Usage: python scripts/analyze-traffic.py <file.har>")
        print("\nThe HAR file should be captured from web.hellotalk.com")
        sys.exit(1)

    filepath = sys.argv[1]
    if not Path(filepath).exists():
        print(f"File not found: {filepath}")
        sys.exit(1)

    har = load_har(filepath)
    analyze_har(har)
