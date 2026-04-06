#!/usr/bin/env python3
"""Use Chrome DevTools Protocol to intercept XHR and capture decrypted responses."""
import asyncio
import json
from playwright.async_api import async_playwright


async def main():
    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
    page = browser.contexts[0].pages[0]
    print(f"URL: {page.url}")

    # Use CDP to override the response decryption
    # Instead, let's use a smarter approach:
    # Override XMLHttpRequest to capture the DECRYPTED response
    # after the app processes it

    js_code = open("scripts/cdp-hook.js").read()
    await page.evaluate(js_code)
    print("Hooks installed. Waiting for app to make XTEA-encrypted requests...")

    # Click on a chat to trigger data load
    try:
        items = page.locator(".userItem")
        count = await items.count()
        if count > 1:
            await items.nth(1).click()  # click second chat
            print(f"Clicked chat item (2nd of {count})")
    except Exception as e:
        print(f"Click failed: {e}")

    # Wait and check
    for i in range(15):
        await asyncio.sleep(2)
        data = await page.evaluate("() => window.__decrypted_data || []")
        if data:
            print(f"\n*** GOT {len(data)} DECRYPTED RESPONSES ***")
            for d in data[:5]:
                print(f"\n  URL: {d.get('url', '?')[:100]}")
                print(f"  Size: {d.get('size', '?')}")
                text = d.get('text', '')
                if text:
                    print(f"  Preview: {text[:500]}")
            with open("captures/decrypted_responses.json", "w") as f:
                json.dump(data, f, indent=2, default=str, ensure_ascii=False)
            print("\nSaved to captures/decrypted_responses.json")
            break

    await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
