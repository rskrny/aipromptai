#!/usr/bin/env python3
"""Simple hook — capture TextDecoder output and find XTEA key via console override."""
import asyncio
import json
from playwright.async_api import async_playwright

HOOK = """() => {
    window.__captures = [];
    window.__console_logs = [];

    // Hook console.log to catch "[XTEA" or key-related logs
    const origLog = console.log;
    const origError = console.error;
    console.log = function() {
        const msg = Array.from(arguments).map(String).join(' ');
        window.__console_logs.push(msg.substring(0, 500));
        origLog.apply(console, arguments);
    };
    console.error = function() {
        const msg = Array.from(arguments).map(String).join(' ');
        if (msg.includes('tplain')) {
            window.__console_logs.push('XTEA_ERROR: ' + msg);
        }
        origError.apply(console, arguments);
    };

    // Hook TextDecoder to catch decrypted XTEA output
    const origDecode = TextDecoder.prototype.decode;
    TextDecoder.prototype.decode = function(input) {
        const result = origDecode.call(this, input);
        if (result && result.length > 20) {
            window.__captures.push({
                len: result.length,
                text: result.substring(0, 2000),
                time: Date.now()
            });
        }
        return result;
    };

    // Hook XMLHttpRequest to see the sync requests and responses
    const origXHROpen = XMLHttpRequest.prototype.open;
    const origXHRSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function(method, url) {
        this.__url = url;
        this.__method = method;
        return origXHROpen.apply(this, arguments);
    };
    XMLHttpRequest.prototype.send = function(body) {
        const self = this;
        const url = this.__url || '';
        if (url.includes('hellotalk')) {
            this.addEventListener('load', function() {
                const ct = self.getResponseHeader('content-type') || '';
                window.__captures.push({
                    type: 'xhr',
                    url: url.substring(0, 200),
                    status: self.status,
                    ct: ct,
                    responseLen: self.response ? (self.response.byteLength || self.response.length || 0) : 0,
                    time: Date.now()
                });
            });
        }
        return origXHRSend.apply(this, arguments);
    };

    return 'hooks installed';
}"""


async def main():
    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
    page = browser.contexts[0].pages[0]
    print(f"Connected: {page.url}")

    # Install hooks
    r = await page.evaluate(HOOK)
    print(f"Hooks: {r}")

    # Capture console messages from the page
    messages = []
    page.on("console", lambda msg: messages.append(msg.text))

    print()
    print("Waiting 60s for traffic. Click on chats/moments in Chrome!")
    print()

    for i in range(30):
        await asyncio.sleep(2)

        caps = await page.evaluate("() => window.__captures || []")
        logs = await page.evaluate("() => window.__console_logs || []")

        if caps:
            new_caps = caps[len(getattr(main, '_last_count', 0)):]
            main._last_count = len(caps)
            for c in new_caps:
                if c.get('type') == 'xhr':
                    print(f"  XHR {c.get('url','?')[:80]} -> {c.get('status')} ({c.get('ct','?')})")
                else:
                    text = c.get('text', '')
                    # Check if it's decrypted XTEA data
                    if len(text) > 50:
                        print(f"  DECODED ({c.get('len')}): {text[:200]}")
                        try:
                            parsed = json.loads(text)
                            print(f"  *** JSON DECODED: {json.dumps(parsed, ensure_ascii=False)[:300]}")
                        except json.JSONDecodeError:
                            pass

        if logs:
            for log in logs:
                if 'XTEA' in log or 'tplain' in log or 'encrypt' in log.lower():
                    print(f"  LOG: {log}")

        if messages:
            new_msgs = messages[getattr(main, '_last_msgs', 0):]
            main._last_msgs = len(messages)
            for m in new_msgs:
                if any(kw in m.lower() for kw in ['xtea', 'decrypt', 'encrypt', 'key', 'token']):
                    print(f"  CONSOLE: {m[:200]}")

    # Final dump
    all_caps = await page.evaluate("() => window.__captures || []")
    all_logs = await page.evaluate("() => window.__console_logs || []")

    with open("captures/hook_output.json", "w") as f:
        json.dump({"captures": all_caps, "logs": all_logs}, f, indent=2, default=str, ensure_ascii=False)

    print(f"\nDone. {len(all_caps)} captures, {len(all_logs)} logs")
    print("Saved to captures/hook_output.json")

    await pw.stop()

main._last_count = 0
main._last_msgs = 0

if __name__ == "__main__":
    asyncio.run(main())
