#!/usr/bin/env python3
"""
Lightweight HelloTalk API client for testing discovered endpoints.

Usage:
    1. First capture traffic to discover your auth token
    2. Set HELLOTALK_TOKEN env var or pass it directly
    3. Use the client to test specific endpoints

This is a research tool — keep request rates reasonable.
"""

import os
import time
import random
import json
import httpx

# Defaults — update these as you discover the real values from traffic analysis
BASE_URL = os.getenv("HELLOTALK_BASE_URL", "https://api.hellotalk.com")
TOKEN = os.getenv("HELLOTALK_TOKEN", "")


class HelloTalkClient:
    def __init__(self, base_url: str = BASE_URL, token: str = TOKEN):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=30,
            headers=self._default_headers(token),
        )

    def _default_headers(self, token: str) -> dict:
        """Build default headers. Update after analyzing real traffic."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if token:
            # Update this with the real auth header format once discovered
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _delay(self, min_sec=1.0, max_sec=3.0):
        """Random delay to keep requests human-like."""
        time.sleep(random.uniform(min_sec, max_sec))

    def get(self, path: str, params: dict = None) -> httpx.Response:
        """GET request with built-in delay."""
        self._delay()
        resp = self.client.get(path, params=params)
        self._log(resp)
        return resp

    def post(self, path: str, data: dict = None) -> httpx.Response:
        """POST request with built-in delay."""
        self._delay()
        resp = self.client.post(path, json=data)
        self._log(resp)
        return resp

    def _log(self, resp: httpx.Response):
        """Log request/response for research."""
        req = resp.request
        print(f"\n{'—'*50}")
        print(f"{req.method} {req.url} → {resp.status_code}")

        # Check for rate limit headers
        for header in resp.headers:
            if "rate" in header.lower() or "limit" in header.lower():
                print(f"  ⚠ {header}: {resp.headers[header]}")

        try:
            body = resp.json()
            print(f"  Response: {json.dumps(body, indent=2)[:500]}")
        except Exception:
            print(f"  Response: <{len(resp.content)} bytes>")


# --- Endpoint methods (fill in as you discover them) ---

    def get_profile(self):
        """Fetch your own profile."""
        return self.get("/user/profile")  # update path after discovery

    def get_discovery(self, **filters):
        """Get discovery/matching feed."""
        return self.get("/discovery", params=filters)  # update path

    def get_moments(self, page: int = 1):
        """Get moments feed."""
        return self.get("/moments", params={"page": page})  # update path


if __name__ == "__main__":
    if not TOKEN:
        print("Set HELLOTALK_TOKEN env var first.")
        print("Capture it from traffic using: bash scripts/proxy-setup.sh")
        exit(1)

    client = HelloTalkClient()
    print("Testing profile endpoint...")
    client.get_profile()
