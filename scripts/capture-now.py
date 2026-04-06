#!/usr/bin/env python3
"""Inject hooks into already-loaded page and click to generate XTEA traffic."""
import asyncio
import json
from playwright.async_api import async_playwright

HOOK = """() => {
    if (window.__hooks_installed) return 'already installed';
    window.__hooks_installed = true;
    window.__captures = [];
    window.__xhr_log = [];

    // Hook TextDecoder
    const origDecode = TextDecoder.prototype.decode;
    TextDecoder.prototype.decode = function(input) {
        const result = origDecode.call(this, input);
        if (result && result.length > 20) {
            window.__captures.push({
                len: result.length,
                text: result.substring(0, 5000),
                time: Date.now()
            });
        }
        return result;
    };

    // Hook XHR to see all hellotalk requests
    const origOpen = XMLHttpRequest.prototype.open;
    const origSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function(method, url) {
        this._url = url;
        this._method = method;
        return origOpen.apply(this, arguments);
    };
    XMLHttpRequest.prototype.send = function(body) {
        const self = this;
        const url = this._url || '';
        if (url.includes('hellotalk')) {
            this.addEventListener('load', function() {
                window.__xhr_log.push({
                    method: self._method,
                    url: url.substring(0, 300),
                    status: self.status,
                    ct: self.getResponseHeader('content-type') || '',
                    size: self.response ? (self.response.byteLength || self.responseText.length || 0) : 0,
                    time: Date.now()
                });
            });
        }
        return origSend.apply(this, arguments);
    };

    // Hook fetch too
    const origFetch = window.fetch;
    window.fetch = function(input, init) {
        const url = typeof input === 'string' ? input : (input.url || '');
        if (url.includes('hellotalk')) {
            return origFetch.apply(this, arguments).then(resp => {
                window.__xhr_log.push({
                    method: (init && init.method) || 'GET',
                    url: url.substring(0, 300),
                    status: resp.status,
                    ct: resp.headers.get('content-type') || '',
                    time: Date.now()
                });
                return resp;
            });
        }
        return origFetch.apply(this, arguments);
    };

    return 'installed';
}"""


async def main():
    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
    page = browser.contexts[0].pages[0]
    print(f"URL: {page.url}")

    # Install hooks
    r = await page.evaluate(HOOK)
    print(f"Hooks: {r}")

    # Wait a moment for any pending long-poll to complete
    await asyncio.sleep(3)
    caps = await page.evaluate("() => window.__captures || []")
    xhr = await page.evaluate("() => window.__xhr_log || []")
    print(f"Initial: {len(caps)} decoded, {len(xhr)} XHR")

    # Now click on chat items to trigger XTEA decryption
    print("\nLooking for clickable elements...")

    # Try various selectors for chat list items
    selectors = [
        ".userItem",
        "[class*='userItem']",
        "[class*='chat-item']",
        "[class*='conversation']",
        "[class*='contact']",
        ".el-menu-item",
        "[class*='sidebar'] li",
        "[class*='sidebar'] div",
        "[class*='list'] > div",
    ]

    for sel in selectors:
        loc = page.locator(sel)
        count = await loc.count()
        if count > 0:
            print(f"  Found {count} elements matching '{sel}'")
            # Click first one
            try:
                await loc.first.click()
                print(f"  Clicked first '{sel}'")
                await asyncio.sleep(3)
                break
            except Exception as e:
                print(f"  Click failed: {e}")

    # Check what we got
    caps = await page.evaluate("() => window.__captures || []")
    xhr = await page.evaluate("() => window.__xhr_log || []")
    print(f"\nAfter click: {len(caps)} decoded, {len(xhr)} XHR")

    for x in xhr:
        print(f"  XHR: {x.get('method')} {x.get('url','')[:80]} -> {x.get('status')} ({x.get('ct','')})")

    for c in caps:
        text = c.get("text", "")
        if len(text) < 30:
            continue
        try:
            parsed = json.loads(text)
            print(f"\n*** DECRYPTED JSON ({c.get('len')} chars) ***")
            preview = json.dumps(parsed, indent=2, ensure_ascii=False)
            print(preview[:1000])
        except json.JSONDecodeError:
            if len(text) > 50:
                print(f"\nDECODED TEXT ({c.get('len')} chars): {text[:500]}")

    # If nothing yet, let's take a screenshot to see what the page looks like
    if not caps and not xhr:
        print("\nNo traffic captured. Taking screenshot...")
        await page.screenshot(path="captures/page_state.png")
        print("Saved captures/page_state.png")

        # Also dump the page HTML structure
        html = await page.evaluate("() => document.body.innerHTML.substring(0, 5000)")
        print(f"\nPage HTML preview:\n{html[:2000]}")

    # Save
    with open("captures/capture_now.json", "w") as f:
        json.dump({"captures": caps, "xhr": xhr}, f, indent=2, default=str, ensure_ascii=False)
    print(f"\nSaved to captures/capture_now.json")

    await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
