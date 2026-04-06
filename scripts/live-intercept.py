#!/usr/bin/env python3
"""Live intercept all HelloTalk traffic from Chrome and dump encryption data."""
import asyncio
import json
from playwright.async_api import async_playwright

captured_requests = []
captured_responses = []


async def main():
    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = ctx.pages[0]
    print(f"Connected: {page.url}")

    async def on_request(request):
        url = request.url
        if "hellotalk" not in url:
            return
        headers = request.headers
        entry = {
            "method": request.method,
            "url": url,
            "headers": {k: v for k, v in headers.items() if k.startswith("x-") or k in ("authorization", "content-type", "accept")},
        }
        try:
            body = request.post_data
            if body:
                entry["post_data"] = body[:500]
        except Exception:
            pass

        captured_requests.append(entry)

        # Print key info
        short_url = url.split("?")[0].replace("https://", "")
        print(f"\n  REQ {request.method} {short_url}")
        for k, v in headers.items():
            if k.startswith("x-ht") or k == "authorization":
                val_preview = v[:80] + "..." if len(v) > 80 else v
                print(f"      {k}: {val_preview}")

    async def on_response(response):
        url = response.url
        if "hellotalk" not in url:
            return
        ct = response.headers.get("content-type", "")
        status = response.status
        short_url = url.split("?")[0].replace("https://", "")

        entry = {
            "url": url,
            "status": status,
            "content_type": ct,
            "headers": dict(response.headers),
        }

        try:
            body = await response.body()
            entry["body_size"] = len(body)

            if "json" in ct:
                data = json.loads(body)
                entry["json"] = data
                preview = json.dumps(data, ensure_ascii=False)
                print(f"  RSP {status} {short_url} ({ct})")
                print(f"      {preview[:300]}")

                # Flag anything with encryption config
                data_str = json.dumps(data).lower()
                if any(kw in data_str for kw in ["publickey", "pub_key", "pubkey", "rsa",
                                                   "encrypt", "pkv", "version", "mig", "mii"]):
                    print(f"      *** ENCRYPTION CONFIG DETECTED ***")
                    print(f"      {json.dumps(data, indent=2, ensure_ascii=False)[:1000]}")
            else:
                print(f"  RSP {status} {short_url} ({ct}, {len(body)}b)")
                if len(body) < 200:
                    print(f"      raw: {body[:200]}")
        except Exception as e:
            print(f"  RSP {status} {short_url} (error reading body: {e})")

        captured_responses.append(entry)

    page.on("request", on_request)
    page.on("response", on_response)

    print()
    print("=" * 60)
    print("  LIVE INTERCEPT — watching all HelloTalk traffic")
    print("  Browse around in Chrome: click chats, moments, discovery")
    print("  Press Ctrl+C to stop and save")
    print("=" * 60)
    print()

    try:
        # Also reload to catch initial traffic
        print("Reloading page to capture login/init traffic...")
        await page.reload(wait_until="networkidle", timeout=30000)
        print("Page loaded. Now browse around.\n")

        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass

    # Save
    output = {
        "requests": captured_requests,
        "responses": captured_responses,
    }
    with open("captures/live_intercept.json", "w") as f:
        json.dump(output, f, indent=2, default=str, ensure_ascii=False)

    print(f"\nSaved {len(captured_requests)} requests, {len(captured_responses)} responses")
    print("=> captures/live_intercept.json")

    # Print summary
    print("\n=== ENCRYPTION HEADERS FOUND ===")
    for r in captured_requests:
        for k, v in r.get("headers", {}).items():
            if "pub" in k.lower() or "encrypt" in k.lower() or "key" in k.lower():
                print(f"  {k}: {v}")

    await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
