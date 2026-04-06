#!/usr/bin/env python3
"""Hook the XTEA decrypt function to capture the actual key being used."""
import asyncio
import json
from playwright.async_api import async_playwright

# This script hooks into the webpack module system to intercept
# the actual xTEADecryptWithKey calls and capture the key parameter.

HOOK_JS = """() => {
    // Strategy: Monkey-patch the TextDecoder to catch decrypted output
    // The XTEA decrypt function calls new TextDecoder().decode() at the end
    const origDecode = TextDecoder.prototype.decode;
    window.__ht_xtea_captures = [];

    TextDecoder.prototype.decode = function(input) {
        const result = origDecode.call(this, input);

        // Capture if it looks like JSON or a meaningful message
        if (result && result.length > 10) {
            const entry = {
                length: result.length,
                preview: result.substring(0, 500),
                timestamp: Date.now()
            };

            // Check if it's JSON
            try {
                const parsed = JSON.parse(result);
                entry.is_json = true;
                entry.json = parsed;
            } catch(e) {
                entry.is_json = false;
            }

            window.__ht_xtea_captures.push(entry);

            if (result.length > 50) {
                console.log('[XTEA-HOOK] Decrypted:', result.substring(0, 200));
            }
        }

        return result;
    };

    // Also try to find and hook the actual module
    // The webpack runtime might expose __webpack_require__
    if (window.webpackJsonp) {
        // Push a fake module that requires the XTEA module
        window.webpackJsonp.push([
            ["xtea-hook"],
            {
                "xtea-hook": function(module, exports, require) {
                    // Try to find the xtea module by iterating all modules
                    try {
                        const moduleIds = Object.keys(require.c || {});
                        for (const id of moduleIds) {
                            const mod = require.c[id];
                            if (mod && mod.exports && mod.exports.default) {
                                const exp = mod.exports.default;
                                if (typeof exp.xTEADecryptWithKey === 'function') {
                                    console.log('[XTEA-HOOK] Found XTEA module at id:', id);
                                    window.__xt_module = exp;

                                    // Hook the decrypt function
                                    const origDecrypt = exp.xTEADecryptWithKey;
                                    exp.xTEADecryptWithKey = function(data, key) {
                                        console.log('[XTEA-HOOK] DECRYPT CALLED! Key:', key);
                                        window.__ht_xtea_key = key;
                                        if (!window.__ht_xtea_keys) window.__ht_xtea_keys = [];
                                        window.__ht_xtea_keys.push({
                                            key: key,
                                            data_size: data ? (data.byteLength || data.length) : 0,
                                            timestamp: Date.now()
                                        });
                                        return origDecrypt.call(this, data, key);
                                    };

                                    // Also hook encrypt
                                    const origEncrypt = exp.xTEAEncryptWithKey;
                                    exp.xTEAEncryptWithKey = function(data, key) {
                                        console.log('[XTEA-HOOK] ENCRYPT CALLED! Key:', key);
                                        if (!window.__ht_xtea_keys) window.__ht_xtea_keys = [];
                                        window.__ht_xtea_keys.push({
                                            key: key,
                                            operation: 'encrypt',
                                            timestamp: Date.now()
                                        });
                                        return origEncrypt.call(this, data, key);
                                    };

                                    break;
                                }
                            }
                        }
                    } catch(e) {
                        console.error('[XTEA-HOOK] Error:', e);
                    }
                }
            },
            [["xtea-hook"]]
        ]);
    }

    return {
        webpackJsonp_exists: !!window.webpackJsonp,
        webpackJsonp_length: window.webpackJsonp ? window.webpackJsonp.length : 0,
    };
}"""


async def main():
    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
    page = browser.contexts[0].pages[0]
    print(f"Connected: {page.url}")

    # Install hooks
    print("Installing XTEA hooks...")
    result = await page.evaluate(HOOK_JS)
    print(f"Hook result: {result}")

    # Listen for console logs
    page.on("console", lambda msg: print(f"  CONSOLE: {msg.text}") if "XTEA" in msg.text or "xtea" in msg.text.lower() else None)

    print()
    print("=" * 60)
    print("  Hooks installed. Now click around in HelloTalk:")
    print("  - Open a chat conversation")
    print("  - Click on a user")
    print("  - The XTEA key will be captured when traffic is decrypted")
    print("=" * 60)
    print()

    # Wait for some activity then check
    for i in range(30):
        await asyncio.sleep(2)

        # Check for captured keys
        keys = await page.evaluate("() => window.__ht_xtea_keys || []")
        if keys:
            print(f"\n*** XTEA KEYS CAPTURED ({len(keys)}) ***")
            for k in keys:
                print(f"  Key: {k.get('key', '?')}")
                print(f"  Data size: {k.get('data_size', '?')}")
                print(f"  Operation: {k.get('operation', 'decrypt')}")

            with open("captures/xtea_keys.json", "w") as f:
                json.dump(keys, f, indent=2)
            print("Saved to captures/xtea_keys.json")
            break

        # Also check TextDecoder captures
        decoded = await page.evaluate("() => window.__ht_xtea_captures || []")
        if decoded:
            print(f"\n*** DECODED DATA ({len(decoded)} entries) ***")
            for d in decoded[:5]:
                print(f"  len={d['length']} json={d.get('is_json')} preview={d.get('preview', '')[:200]}")

            with open("captures/decoded_data.json", "w") as f:
                json.dump(decoded, f, indent=2, default=str, ensure_ascii=False)
            print("Saved to captures/decoded_data.json")
            break

        if (i + 1) % 5 == 0:
            print(f"  Waiting... ({(i+1)*2}s) Click on a chat in Chrome!")

    await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
