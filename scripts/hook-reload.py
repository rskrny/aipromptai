#!/usr/bin/env python3
"""Install hooks BEFORE page loads, then reload to capture everything."""
import asyncio
import json
from playwright.async_api import async_playwright

INIT_SCRIPT = """
window.__captures = [];
window.__xtea_keys = [];

// Hook TextDecoder before any code runs
const origDecode = TextDecoder.prototype.decode;
TextDecoder.prototype.decode = function(input) {
    const result = origDecode.call(this, input);
    if (result && result.length > 20) {
        window.__captures.push({
            len: result.length,
            text: result.substring(0, 3000),
            time: Date.now()
        });
    }
    return result;
};

// Hook console.error to catch XTEA "bad tplain" errors
const origError = console.error;
console.error = function() {
    const msg = Array.from(arguments).map(String).join(' ');
    if (msg.includes('tplain') || msg.includes('XTEA')) {
        window.__captures.push({type: 'error', msg: msg, time: Date.now()});
    }
    origError.apply(console, arguments);
};
"""


async def main():
    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = ctx.pages[0]
    print(f"Connected: {page.url}")

    # Add init script that runs BEFORE any page JavaScript
    await ctx.add_init_script(INIT_SCRIPT)
    print("Init script added (will run on next page load)")

    # Reload the page — hooks will be active from the start
    print("Reloading page with hooks...")
    await page.reload(wait_until="networkidle", timeout=30000)
    print("Page reloaded.")

    # Wait for the app to load and make API calls
    await asyncio.sleep(5)

    # Check captures
    caps = await page.evaluate("() => window.__captures || []")
    keys = await page.evaluate("() => window.__xtea_keys || []")

    print(f"\nCaptures: {len(caps)}")
    print(f"XTEA keys: {len(keys)}")

    for c in caps:
        text = c.get("text", "")
        ctype = c.get("type", "decoded")

        if ctype == "error":
            print(f"\n  ERROR: {c.get('msg', '')[:200]}")
            continue

        if len(text) < 30:
            continue

        # Try to parse as JSON
        try:
            parsed = json.loads(text)
            print(f"\n  *** DECRYPTED JSON ({c.get('len')} chars) ***")
            print(f"  {json.dumps(parsed, indent=2, ensure_ascii=False)[:500]}")
        except json.JSONDecodeError:
            # Show raw text
            if len(text) > 50:
                print(f"\n  DECODED TEXT ({c.get('len')} chars): {text[:300]}")

    # Now click on a chat to trigger more XTEA traffic
    print("\n--- Clicking first chat to trigger XTEA ---")
    try:
        chat_items = page.locator(".userItem, [class*='userItem'], [class*='chat-item'], [class*='conversation']")
        count = await chat_items.count()
        print(f"Found {count} chat items")
        if count > 0:
            await chat_items.first.click()
            await asyncio.sleep(5)

            # Check for new captures
            new_caps = await page.evaluate("() => window.__captures || []")
            print(f"Captures after click: {len(new_caps)}")

            for c in new_caps[len(caps):]:
                text = c.get("text", "")
                if len(text) > 30:
                    try:
                        parsed = json.loads(text)
                        print(f"\n  *** NEW DECRYPTED JSON ***")
                        print(f"  {json.dumps(parsed, indent=2, ensure_ascii=False)[:500]}")
                    except json.JSONDecodeError:
                        if len(text) > 50:
                            print(f"\n  NEW DECODED ({c.get('len')} chars): {text[:300]}")
    except Exception as e:
        print(f"Click failed: {e}")

    # Save everything
    all_caps = await page.evaluate("() => window.__captures || []")
    with open("captures/decoded_output.json", "w") as f:
        json.dump(all_caps, f, indent=2, default=str, ensure_ascii=False)
    print(f"\nSaved {len(all_caps)} captures to captures/decoded_output.json")

    await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
