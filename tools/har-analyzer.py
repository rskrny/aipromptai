#!/usr/bin/env python3
"""
Analyze HAR (HTTP Archive) files for HelloTalk API traffic.

HAR files can be exported from:
  - Chrome DevTools (if using web version)
  - Charles Proxy
  - mitmproxy (mitmdump --set hardump=file.har)

Usage:
    python tools/har-analyzer.py <file.har> [--domain hellotalk]
"""

import sys
import json
from pathlib import Path
from collections import Counter


def load_har(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze(har: dict, domain_filter: str = "hellotalk"):
    entries = har.get("log", {}).get("entries", [])

    if domain_filter:
        entries = [
            e for e in entries
            if domain_filter in e.get("request", {}).get("url", "")
        ]

    print(f"\nTotal entries matching '{domain_filter}': {len(entries)}\n")

    # Endpoint frequency
    endpoints = Counter()
    methods = Counter()
    status_codes = Counter()
    hosts = set()

    for entry in entries:
        req = entry["request"]
        resp = entry["response"]

        url = req["url"]
        method = req["method"]
        status = resp["status"]

        # Extract path without query params
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path = parsed.path
        host = parsed.netloc

        endpoints[f"{method} {path}"] += 1
        methods[method] += 1
        status_codes[status] += 1
        hosts.add(host)

    print("=== Hosts ===")
    for h in sorted(hosts):
        print(f"  {h}")

    print("\n=== Methods ===")
    for method, count in methods.most_common():
        print(f"  {method}: {count}")

    print("\n=== Status Codes ===")
    for code, count in status_codes.most_common():
        print(f"  {code}: {count}")

    print("\n=== Endpoints (by frequency) ===")
    for endpoint, count in endpoints.most_common(30):
        print(f"  {count:>4}x  {endpoint}")

    # Look for auth patterns
    print("\n=== Auth Headers (from first matching request) ===")
    if entries:
        headers = entries[0]["request"].get("headers", [])
        auth_keywords = ["auth", "token", "cookie", "session", "api-key", "x-"]
        for h in headers:
            name = h["name"].lower()
            if any(kw in name for kw in auth_keywords):
                value = h["value"]
                # Mask the token for safety
                if len(value) > 20:
                    value = value[:10] + "..." + value[-5:]
                print(f"  {h['name']}: {value}")

    return entries


def export_endpoints(entries: list, output_path: str):
    """Export unique endpoints as JSON for further analysis."""
    unique = {}
    for entry in entries:
        req = entry["request"]
        from urllib.parse import urlparse
        parsed = urlparse(req["url"])
        key = f"{req['method']} {parsed.path}"
        if key not in unique:
            unique[key] = {
                "method": req["method"],
                "path": parsed.path,
                "example_url": req["url"],
                "query_params": parsed.query,
                "status": entry["response"]["status"],
            }

    with open(output_path, "w") as f:
        json.dump(list(unique.values()), f, indent=2)
    print(f"\nExported {len(unique)} unique endpoints to {output_path}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    filepath = sys.argv[1]
    domain = "hellotalk"

    for i, arg in enumerate(sys.argv):
        if arg == "--domain" and i + 1 < len(sys.argv):
            domain = sys.argv[i + 1]

    if not Path(filepath).exists():
        print(f"File not found: {filepath}")
        sys.exit(1)

    har = load_har(filepath)
    entries = analyze(har, domain)

    if entries:
        output = filepath.replace(".har", "_endpoints.json")
        export_endpoints(entries, output)


if __name__ == "__main__":
    main()
