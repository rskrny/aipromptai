#!/usr/bin/env python3
"""
Proxyman Traffic Analyzer for HelloTalk

Analyzes Proxyman exports (HAR format) to extract everything useful
from HelloTalk API traffic — even when payloads are encrypted.

What this extracts:
- Complete endpoint map with methods, frequencies, timing
- Unencrypted responses (plain JSON endpoints)
- Request metadata (headers, query params, cookies)
- Encryption analysis (which endpoints use ht/encbin vs plain JSON)
- Timing patterns (request frequency, session duration)
- CDN/infrastructure mapping

Usage:
    python scripts/proxyman-analyzer.py <file.har>
    python scripts/proxyman-analyzer.py <file.har> --json    # Machine-readable output
"""

import json
import sys
import base64
from pathlib import Path
from collections import Counter, defaultdict
from urllib.parse import urlparse, parse_qs
from datetime import datetime


def load_har(filepath):
    """Load a HAR file, handling common encoding issues."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        return json.load(f)


def is_hellotalk(url):
    """Check if a URL belongs to HelloTalk infrastructure."""
    return "hellotalk" in urlparse(url).netloc.lower()


def classify_content(content_type, body_text):
    """Classify response content as encrypted, JSON, protobuf, or other."""
    if not content_type:
        return "unknown"
    ct = content_type.lower()
    if "ht/encbin" in ct:
        return "encrypted"
    if "application/json" in ct:
        return "json"
    if "protobuf" in ct or "application/octet-stream" in ct:
        return "protobuf"
    if "image/" in ct:
        return "image"
    if "text/html" in ct:
        return "html"
    # Check if body looks like JSON even with wrong content type
    if body_text:
        stripped = body_text.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            return "json"
    return "other"


def try_decode_body(body_text, encoding=None):
    """Try to decode a response body, handling base64 and binary."""
    if not body_text:
        return None, "empty"

    # Try as plain JSON first
    try:
        return json.loads(body_text), "json"
    except (json.JSONDecodeError, ValueError):
        pass

    # Try base64 decode then JSON
    try:
        decoded = base64.b64decode(body_text)
        try:
            return json.loads(decoded), "base64+json"
        except (json.JSONDecodeError, ValueError):
            # It's base64 but not JSON (encrypted or protobuf)
            return {"_binary_size": len(decoded), "_hex_preview": decoded[:32].hex()}, "base64+binary"
    except Exception:
        pass

    # It's something else
    if len(body_text) > 100:
        return {"_raw_preview": body_text[:200], "_size": len(body_text)}, "raw"
    return {"_raw": body_text}, "raw"


def extract_auth(headers):
    """Extract authentication-related headers."""
    auth = {}
    auth_keys = ["authorization", "cookie", "x-ht-os", "x-ht-uid", "x-ht-did",
                 "x-ht-timezone", "x-ht-pub", "x-b3-spanid", "x-b3-traceid"]
    for name, value in headers.items():
        if name.lower() in auth_keys or "token" in name.lower() or "auth" in name.lower():
            auth[name] = value
    return auth


def analyze_har(har_data):
    """Full analysis of a HAR file."""
    entries = har_data.get("log", {}).get("entries", [])

    results = {
        "summary": {},
        "endpoints": {},
        "encryption_analysis": {"encrypted": [], "plaintext": [], "other": []},
        "decoded_responses": {},
        "auth": {},
        "infrastructure": {"hosts": Counter(), "servers": Counter()},
        "timing": [],
        "query_params": {},
    }

    ht_entries = []
    for entry in entries:
        url = entry.get("request", {}).get("url", "")
        if is_hellotalk(url):
            ht_entries.append(entry)
        else:
            host = urlparse(url).netloc
            if host:
                results["infrastructure"]["hosts"][host] += 1

    results["summary"] = {
        "total_requests": len(entries),
        "hellotalk_requests": len(ht_entries),
        "other_requests": len(entries) - len(ht_entries),
    }

    if not ht_entries:
        return results

    # Extract auth from first request
    if ht_entries:
        req_headers = {h["name"]: h["value"]
                       for h in ht_entries[0].get("request", {}).get("headers", [])}
        results["auth"] = extract_auth(req_headers)

    # Analyze each HelloTalk request
    for entry in ht_entries:
        req = entry.get("request", {})
        resp = entry.get("response", {})
        url = req.get("url", "")
        parsed = urlparse(url)
        method = req.get("method", "?")
        path = parsed.path
        status = resp.get("status", 0)
        host = parsed.netloc

        # Track infrastructure
        results["infrastructure"]["hosts"][host] += 1
        resp_headers = {h["name"]: h["value"]
                        for h in resp.get("headers", [])}
        server = resp_headers.get("server", resp_headers.get("Server", ""))
        if server:
            results["infrastructure"]["servers"][server] += 1

        # Request headers
        req_headers = {h["name"]: h["value"]
                       for h in req.get("headers", [])}

        # Content type analysis
        resp_content_type = resp_headers.get("content-type",
                                             resp_headers.get("Content-Type", ""))
        req_content_type = req_headers.get("content-type",
                                           req_headers.get("Content-Type", ""))

        # Get response body
        resp_body_text = resp.get("content", {}).get("text", "")
        resp_encoding = resp.get("content", {}).get("encoding", "")

        # Classify the response
        content_class = classify_content(resp_content_type, resp_body_text)

        # Try to decode the response
        decoded, decode_method = try_decode_body(resp_body_text, resp_encoding)

        endpoint_key = f"{method} {path}"

        # Store endpoint info
        if endpoint_key not in results["endpoints"]:
            results["endpoints"][endpoint_key] = {
                "method": method,
                "path": path,
                "host": host,
                "count": 0,
                "statuses": [],
                "content_types": [],
                "encrypted": False,
                "query_params": {},
                "has_x_ht_pub": False,
            }

        ep = results["endpoints"][endpoint_key]
        ep["count"] += 1
        ep["statuses"].append(status)
        ep["content_types"].append(resp_content_type)

        # Check encryption
        if "ht/encbin" in req_content_type or "ht/encbin" in resp_content_type:
            ep["encrypted"] = True
            results["encryption_analysis"]["encrypted"].append(endpoint_key)
        elif content_class == "json":
            results["encryption_analysis"]["plaintext"].append(endpoint_key)
        else:
            results["encryption_analysis"]["other"].append(endpoint_key)

        # Track x-ht-pub header
        if "x-ht-pub" in req_headers or "X-Ht-Pub" in req_headers:
            ep["has_x_ht_pub"] = True

        # Query params
        if parsed.query:
            params = parse_qs(parsed.query)
            ep["query_params"] = {k: v[0] if len(v) == 1 else v
                                  for k, v in params.items()}

        # Store decoded responses for plaintext endpoints
        if content_class == "json" and decoded and decode_method in ("json", "base64+json"):
            if endpoint_key not in results["decoded_responses"]:
                results["decoded_responses"][endpoint_key] = decoded

        # Timing
        started = entry.get("startedDateTime", "")
        time_ms = entry.get("time", 0)
        results["timing"].append({
            "endpoint": endpoint_key,
            "started": started,
            "duration_ms": time_ms,
            "status": status,
        })

    # Deduplicate encryption lists
    results["encryption_analysis"]["encrypted"] = list(set(results["encryption_analysis"]["encrypted"]))
    results["encryption_analysis"]["plaintext"] = list(set(results["encryption_analysis"]["plaintext"]))
    results["encryption_analysis"]["other"] = list(set(results["encryption_analysis"]["other"]))

    # Convert Counters to dicts for JSON serialization
    results["infrastructure"]["hosts"] = dict(results["infrastructure"]["hosts"])
    results["infrastructure"]["servers"] = dict(results["infrastructure"]["servers"])

    # Deduplicate statuses
    for ep in results["endpoints"].values():
        ep["statuses"] = list(set(ep["statuses"]))
        ep["content_types"] = list(set(ep["content_types"]))

    return results


def print_report(results):
    """Print a human-readable analysis report."""
    s = results["summary"]

    print(f"\n{'='*70}")
    print(f"  HELLOTALK TRAFFIC ANALYSIS")
    print(f"{'='*70}")
    print(f"\n  Total requests: {s['total_requests']}")
    print(f"  HelloTalk:      {s['hellotalk_requests']}")
    print(f"  Other:          {s['other_requests']}")

    # Encryption overview
    enc = results["encryption_analysis"]
    total_ht = s["hellotalk_requests"]
    n_enc = len(enc["encrypted"])
    n_plain = len(enc["plaintext"])
    n_other = len(enc["other"])

    print(f"\n{'─'*70}")
    print(f"  ENCRYPTION ANALYSIS")
    print(f"{'─'*70}")
    print(f"  Encrypted (ht/encbin):  {n_enc} unique endpoints")
    print(f"  Plain JSON:             {n_plain} unique endpoints")
    print(f"  Other (images, etc):    {n_other} unique endpoints")

    if n_enc > 0:
        print(f"\n  HelloTalk uses ECIES-like encryption (ECDH key exchange + AES).")
        print(f"  The x-ht-pub header carries the client's ephemeral public key.")
        print(f"  Without APK decompilation, encrypted payloads cannot be read.")

    # Plain JSON endpoints (the valuable ones!)
    if n_plain > 0:
        print(f"\n{'─'*70}")
        print(f"  READABLE ENDPOINTS (plain JSON — no encryption)")
        print(f"{'─'*70}")
        for ep_key in sorted(enc["plaintext"]):
            ep = results["endpoints"].get(ep_key, {})
            print(f"  {ep_key}")
            print(f"    Calls: {ep.get('count', '?')}  Status: {ep.get('statuses', '?')}")

    # Encrypted endpoints
    if n_enc > 0:
        print(f"\n{'─'*70}")
        print(f"  ENCRYPTED ENDPOINTS (ht/encbin — cannot read)")
        print(f"{'─'*70}")
        for ep_key in sorted(enc["encrypted"]):
            ep = results["endpoints"].get(ep_key, {})
            print(f"  {ep_key}")
            print(f"    Calls: {ep.get('count', '?')}  x-ht-pub: {ep.get('has_x_ht_pub', False)}")

    # All endpoints sorted by frequency
    print(f"\n{'─'*70}")
    print(f"  ALL ENDPOINTS (by frequency)")
    print(f"{'─'*70}")
    sorted_eps = sorted(results["endpoints"].items(),
                        key=lambda x: -x[1]["count"])
    for key, ep in sorted_eps:
        enc_flag = " [ENC]" if ep["encrypted"] else ""
        print(f"  {ep['count']:>4}x  {key}{enc_flag}  → {ep['statuses']}")
        if ep["query_params"]:
            for pk, pv in ep["query_params"].items():
                val = str(pv)[:60]
                print(f"         param: {pk} = {val}")

    # Decoded responses
    decoded = results.get("decoded_responses", {})
    if decoded:
        print(f"\n{'─'*70}")
        print(f"  DECODED RESPONSES (plain JSON data we can read)")
        print(f"{'─'*70}")
        for ep_key, data in decoded.items():
            print(f"\n  >>> {ep_key}")
            preview = json.dumps(data, indent=2, ensure_ascii=False)
            if len(preview) > 800:
                print(f"  {preview[:800]}")
                print(f"  ... (truncated, {len(preview)} chars total)")
            else:
                print(f"  {preview}")

    # Auth info
    auth = results.get("auth", {})
    if auth:
        print(f"\n{'─'*70}")
        print(f"  AUTHENTICATION HEADERS")
        print(f"{'─'*70}")
        for name, value in sorted(auth.items()):
            # Mask sensitive values
            if len(value) > 20:
                masked = value[:8] + "..." + value[-4:]
            else:
                masked = value
            print(f"  {name}: {masked}")

    # Infrastructure
    infra = results.get("infrastructure", {})
    hosts = infra.get("hosts", {})
    if hosts:
        print(f"\n{'─'*70}")
        print(f"  INFRASTRUCTURE (hosts)")
        print(f"{'─'*70}")
        for host, count in sorted(hosts.items(), key=lambda x: -x[1]):
            print(f"  {count:>5}x  {host}")

    # Key findings
    print(f"\n{'='*70}")
    print(f"  KEY FINDINGS")
    print(f"{'='*70}")

    # Check for visibility/boost endpoints
    visibility_endpoints = [k for k in results["endpoints"]
                            if any(w in k.lower() for w in
                                   ["recommend", "boost", "expose", "discover",
                                    "visibility", "rank", "score", "trust"])]
    if visibility_endpoints:
        print(f"\n  Visibility-related endpoints found:")
        for ep in visibility_endpoints:
            enc_status = "ENCRYPTED" if results["endpoints"][ep]["encrypted"] else "READABLE"
            print(f"    [{enc_status}] {ep}")

    # Check for user/profile endpoints
    profile_endpoints = [k for k in results["endpoints"]
                         if any(w in k.lower() for w in
                                ["user", "profile", "account", "me", "setting",
                                 "ban", "restrict", "flag"])]
    if profile_endpoints:
        print(f"\n  Profile/account endpoints found:")
        for ep in profile_endpoints:
            enc_status = "ENCRYPTED" if results["endpoints"][ep]["encrypted"] else "READABLE"
            print(f"    [{enc_status}] {ep}")

    print(f"\n{'='*70}\n")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    filepath = sys.argv[1]
    if not Path(filepath).exists():
        print(f"File not found: {filepath}")
        sys.exit(1)

    json_output = "--json" in sys.argv

    print(f"Loading {filepath}...")
    har_data = load_har(filepath)

    print("Analyzing traffic...")
    results = analyze_har(har_data)

    if json_output:
        output_path = Path(filepath).stem + "_analysis.json"
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=str, ensure_ascii=False)
        print(f"Analysis saved to: {output_path}")
    else:
        print_report(results)

    # Always save the full analysis
    output_dir = Path("captures")
    output_dir.mkdir(exist_ok=True)
    analysis_path = output_dir / "full_analysis.json"
    with open(analysis_path, "w") as f:
        json.dump(results, f, indent=2, default=str, ensure_ascii=False)
    print(f"Full analysis saved to: {analysis_path}")


if __name__ == "__main__":
    main()
