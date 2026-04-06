"""Lightweight proxy to capture HelloTalk traffic and extract user ID."""
from mitmproxy import http
import json

class HelloTalkCapture:
    def __init__(self):
        self.uid = None
        self.auth = None
        self.captured = []

    def request(self, flow: http.HTTPFlow):
        if "hellotalk" not in flow.request.pretty_host:
            return

        headers = dict(flow.request.headers)
        url = flow.request.pretty_url

        # Extract user ID
        uid = headers.get("x-ht-uid", "")
        auth = headers.get("authorization", "")
        did = headers.get("x-ht-did", "")
        pub = headers.get("x-ht-pub", "")

        if uid and uid != self.uid:
            self.uid = uid
            self.auth = auth
            print(f"\n{'='*60}")
            print(f"  NEW ACCOUNT DETECTED!")
            print(f"  x-ht-uid: {uid}")
            print(f"  x-ht-did: {did}")
            print(f"  Authorization: {auth[:80]}...")
            if pub:
                print(f"  x-ht-pub: {pub}")
            print(f"{'='*60}\n")

            # Save to file
            data = {
                "Authorization": auth,
                "x-ht-uid": uid,
                "x-ht-did": did,
            }
            with open(f"captures/new_account_auth.json", "w") as f:
                json.dump(data, f, indent=2)
            print(f"  Saved to captures/new_account_auth.json")

        short_url = url.split("?")[0].replace("https://", "")
        print(f"  {flow.request.method} {short_url}")

addons = [HelloTalkCapture()]
