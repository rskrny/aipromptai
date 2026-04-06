#!/usr/bin/env python3
"""Parse mitmproxy capture files and extract HelloTalk API calls."""

import sys
import json
from pathlib import Path

try:
    from mitmproxy.io import FlowReader
    from mitmproxy.http import HTTPFlow
except ImportError:
    print("mitmproxy not installed. Run: pip install mitmproxy")
    sys.exit(1)


def parse_capture(filepath: str, domain_filter: str = "hellotalk"):
    """Read a .mitm capture file and extract matching requests."""
    results = []

    with open(filepath, "rb") as f:
        reader = FlowReader(f)
        for flow in reader.stream():
            if not isinstance(flow, HTTPFlow):
                continue

            req = flow.request
            host = req.pretty_host

            if domain_filter and domain_filter not in host:
                continue

            entry = {
                "method": req.method,
                "url": req.pretty_url,
                "host": host,
                "path": req.path,
                "headers": dict(req.headers),
                "request_body": None,
                "status_code": None,
                "response_headers": None,
                "response_body": None,
            }

            # Request body
            if req.content:
                try:
                    entry["request_body"] = json.loads(req.content)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    entry["request_body"] = f"<binary, {len(req.content)} bytes>"

            # Response
            if flow.response:
                resp = flow.response
                entry["status_code"] = resp.status_code
                entry["response_headers"] = dict(resp.headers)

                if resp.content:
                    try:
                        entry["response_body"] = json.loads(resp.content)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        entry["response_body"] = f"<binary, {len(resp.content)} bytes>"

            results.append(entry)

    return results


def summarize(results: list):
    """Print a summary of captured API calls."""
    print(f"\n{'='*60}")
    print(f"Found {len(results)} HelloTalk API calls")
    print(f"{'='*60}\n")

    # Group by endpoint
    endpoints = {}
    for r in results:
        key = f"{r['method']} {r['path'].split('?')[0]}"
        if key not in endpoints:
            endpoints[key] = []
        endpoints[key].append(r)

    for endpoint, calls in sorted(endpoints.items()):
        status_codes = [c["status_code"] for c in calls if c["status_code"]]
        print(f"  {endpoint}  ({len(calls)}x)  statuses: {set(status_codes)}")

    print(f"\n{'='*60}")
    print("Unique hosts seen:")
    hosts = set(r["host"] for r in results)
    for h in sorted(hosts):
        print(f"  - {h}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/parse-traffic.py <capture.mitm> [--full]")
        print("\nCapture files are in the captures/ directory.")
        sys.exit(1)

    filepath = sys.argv[1]
    full_output = "--full" in sys.argv

    if not Path(filepath).exists():
        print(f"File not found: {filepath}")
        sys.exit(1)

    results = parse_capture(filepath)
    summarize(results)

    if full_output:
        output_path = filepath.replace(".mitm", "_parsed.json")
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nFull output written to: {output_path}")


if __name__ == "__main__":
    main()
