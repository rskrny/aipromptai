#!/usr/bin/env python3
"""
Extract HelloTalk's encryption implementation from the web client.

Connects to Chrome via CDP and:
1. Navigates to web.hellotalk.com
2. Dumps all loaded JavaScript source files
3. Searches for encryption-related code (ECDH, AES, x-ht-pub, encbin)
4. Intercepts XMLHttpRequest/fetch to capture actual encryption keys
5. Hooks crypto APIs (SubtleCrypto, CryptoJS) to capture key material

SETUP:
  Start Chrome with: chrome --remote-debugging-port=9222
  Log in to web.hellotalk.com
  Run: python scripts/extract-crypto.py
"""

import asyncio
import json
import re
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Install playwright: pip install playwright && python -m playwright install chromium")
    sys.exit(1)


# JavaScript injection to hook crypto operations and XHR/fetch
HOOK_SCRIPT = """
(() => {
    window.__ht_captures = {
        keys: [],
        requests: [],
        crypto_ops: [],
        errors: [],
    };

    // === HOOK XMLHttpRequest ===
    const origOpen = XMLHttpRequest.prototype.open;
    const origSetHeader = XMLHttpRequest.prototype.setRequestHeader;
    const origSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function(method, url, ...args) {
        this.__ht_method = method;
        this.__ht_url = url;
        this.__ht_headers = {};
        return origOpen.call(this, method, url, ...args);
    };

    XMLHttpRequest.prototype.setRequestHeader = function(name, value) {
        this.__ht_headers[name.toLowerCase()] = value;
        if (name.toLowerCase() === 'x-ht-pub') {
            window.__ht_captures.keys.push({
                source: 'xhr',
                url: this.__ht_url,
                key: value,
                key_length: value.length,
                timestamp: Date.now(),
            });
            console.log('[HT-HOOK] XHR x-ht-pub captured:', value.substring(0, 40) + '...');
        }
        return origSetHeader.call(this, name, value);
    };

    XMLHttpRequest.prototype.send = function(body) {
        const entry = {
            method: this.__ht_method,
            url: this.__ht_url,
            headers: {...this.__ht_headers},
            timestamp: Date.now(),
        };
        if (body && typeof body === 'string') {
            entry.body_preview = body.substring(0, 200);
        } else if (body instanceof ArrayBuffer || body instanceof Uint8Array) {
            const arr = new Uint8Array(body instanceof ArrayBuffer ? body : body.buffer);
            entry.body_hex_preview = Array.from(arr.slice(0, 64)).map(b => b.toString(16).padStart(2, '0')).join('');
            entry.body_size = arr.length;
        }
        window.__ht_captures.requests.push(entry);
        return origSend.call(this, body);
    };

    // === HOOK fetch() ===
    const origFetch = window.fetch;
    window.fetch = async function(input, init) {
        const url = typeof input === 'string' ? input : input.url;
        const headers = init?.headers || {};

        // Check for x-ht-pub in fetch headers
        const checkHeaders = (h) => {
            if (h instanceof Headers) {
                if (h.has('x-ht-pub')) {
                    const key = h.get('x-ht-pub');
                    window.__ht_captures.keys.push({
                        source: 'fetch',
                        url: url,
                        key: key,
                        key_length: key.length,
                        timestamp: Date.now(),
                    });
                    console.log('[HT-HOOK] fetch x-ht-pub captured:', key.substring(0, 40) + '...');
                }
            } else if (typeof h === 'object') {
                for (const [k, v] of Object.entries(h)) {
                    if (k.toLowerCase() === 'x-ht-pub') {
                        window.__ht_captures.keys.push({
                            source: 'fetch',
                            url: url,
                            key: v,
                            key_length: v.length,
                            timestamp: Date.now(),
                        });
                        console.log('[HT-HOOK] fetch x-ht-pub captured:', v.substring(0, 40) + '...');
                    }
                }
            }
        };

        if (headers) checkHeaders(headers);

        window.__ht_captures.requests.push({
            method: init?.method || 'GET',
            url: url,
            timestamp: Date.now(),
        });

        return origFetch.call(this, input, init);
    };

    // === HOOK SubtleCrypto ===
    if (window.crypto && window.crypto.subtle) {
        const subtle = window.crypto.subtle;

        // Hook generateKey
        const origGenKey = subtle.generateKey.bind(subtle);
        subtle.generateKey = async function(algorithm, extractable, keyUsages) {
            const result = await origGenKey(algorithm, extractable, keyUsages);
            window.__ht_captures.crypto_ops.push({
                op: 'generateKey',
                algorithm: JSON.parse(JSON.stringify(algorithm)),
                extractable: extractable,
                keyUsages: [...keyUsages],
                timestamp: Date.now(),
            });
            console.log('[HT-HOOK] generateKey:', JSON.stringify(algorithm));
            return result;
        };

        // Hook deriveBits
        const origDeriveBits = subtle.deriveBits.bind(subtle);
        subtle.deriveBits = async function(algorithm, baseKey, length) {
            const result = await origDeriveBits(algorithm, baseKey, length);
            window.__ht_captures.crypto_ops.push({
                op: 'deriveBits',
                algorithm_name: algorithm?.name,
                length: length,
                timestamp: Date.now(),
            });
            console.log('[HT-HOOK] deriveBits:', algorithm?.name, length);
            return result;
        };

        // Hook deriveKey
        const origDeriveKey = subtle.deriveKey.bind(subtle);
        subtle.deriveKey = async function(algorithm, baseKey, derivedKeyAlgorithm, extractable, keyUsages) {
            const result = await origDeriveKey(algorithm, baseKey, derivedKeyAlgorithm, extractable, keyUsages);
            window.__ht_captures.crypto_ops.push({
                op: 'deriveKey',
                algorithm_name: algorithm?.name,
                derived_algorithm: JSON.parse(JSON.stringify(derivedKeyAlgorithm)),
                extractable: extractable,
                keyUsages: [...keyUsages],
                timestamp: Date.now(),
            });
            console.log('[HT-HOOK] deriveKey:', algorithm?.name, '->', derivedKeyAlgorithm?.name);
            return result;
        };

        // Hook encrypt
        const origEncrypt = subtle.encrypt.bind(subtle);
        subtle.encrypt = async function(algorithm, key, data) {
            window.__ht_captures.crypto_ops.push({
                op: 'encrypt',
                algorithm: JSON.parse(JSON.stringify(algorithm)),
                data_size: data?.byteLength,
                timestamp: Date.now(),
            });
            console.log('[HT-HOOK] encrypt:', JSON.stringify(algorithm), 'data size:', data?.byteLength);
            return origEncrypt(algorithm, key, data);
        };

        // Hook decrypt
        const origDecrypt = subtle.decrypt.bind(subtle);
        subtle.decrypt = async function(algorithm, key, data) {
            const result = await origDecrypt(algorithm, key, data);
            window.__ht_captures.crypto_ops.push({
                op: 'decrypt',
                algorithm: JSON.parse(JSON.stringify(algorithm)),
                data_size: data?.byteLength,
                result_size: result?.byteLength,
                timestamp: Date.now(),
            });
            console.log('[HT-HOOK] decrypt:', JSON.stringify(algorithm));
            return result;
        };

        // Hook importKey
        const origImportKey = subtle.importKey.bind(subtle);
        subtle.importKey = async function(format, keyData, algorithm, extractable, keyUsages) {
            let keyDataInfo = {};
            if (keyData instanceof ArrayBuffer) {
                const arr = new Uint8Array(keyData);
                keyDataInfo = {
                    format: format,
                    size: arr.length,
                    hex_preview: Array.from(arr.slice(0, 32)).map(b => b.toString(16).padStart(2, '0')).join(''),
                };
            } else if (typeof keyData === 'object') {
                keyDataInfo = {format: format, jwk_preview: JSON.stringify(keyData).substring(0, 200)};
            }

            window.__ht_captures.crypto_ops.push({
                op: 'importKey',
                format: format,
                algorithm: JSON.parse(JSON.stringify(algorithm)),
                extractable: extractable,
                keyUsages: [...keyUsages],
                keyData: keyDataInfo,
                timestamp: Date.now(),
            });
            console.log('[HT-HOOK] importKey:', format, JSON.stringify(algorithm));
            return origImportKey(format, keyData, algorithm, extractable, keyUsages);
        };

        // Hook exportKey
        const origExportKey = subtle.exportKey.bind(subtle);
        subtle.exportKey = async function(format, key) {
            const result = await origExportKey(format, key);
            let exported = {};
            if (result instanceof ArrayBuffer) {
                const arr = new Uint8Array(result);
                exported = {
                    format: format,
                    size: arr.length,
                    hex: Array.from(arr).map(b => b.toString(16).padStart(2, '0')).join(''),
                };
            }
            window.__ht_captures.crypto_ops.push({
                op: 'exportKey',
                format: format,
                exported: exported,
                timestamp: Date.now(),
            });
            console.log('[HT-HOOK] exportKey:', format, 'size:', exported.size);
            return result;
        };
    }

    console.log('[HT-HOOK] All hooks installed. Browse HelloTalk to capture crypto operations.');
})();
"""


async def main():
    pw = await async_playwright().start()

    try:
        browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
    except Exception as e:
        print(f"Can't connect to Chrome: {e}")
        print()
        print('Start Chrome with:')
        print('  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222')
        print()
        print("Then log into web.hellotalk.com")
        await pw.stop()
        sys.exit(1)

    contexts = browser.contexts
    if not contexts or not contexts[0].pages:
        print("No pages found. Open web.hellotalk.com in Chrome first.")
        await pw.stop()
        sys.exit(1)

    page = contexts[0].pages[0]
    print(f"Connected. Current URL: {page.url}")

    # Inject hooks
    print("\nInjecting crypto hooks...")
    await page.evaluate(HOOK_SCRIPT)
    print("Hooks installed.")

    # Also search loaded scripts for crypto-related code
    print("\nSearching loaded scripts for encryption code...")

    scripts_content = await page.evaluate("""
    () => {
        const scripts = document.querySelectorAll('script[src]');
        return Array.from(scripts).map(s => s.src);
    }
    """)

    print(f"Found {len(scripts_content)} script tags")
    for src in scripts_content:
        print(f"  {src}")

    # Search all scripts in the page's scope for crypto keywords
    print("\nSearching JavaScript scope for crypto patterns...")

    crypto_search = await page.evaluate("""
    () => {
        const results = {};

        // Search for global objects that might contain crypto
        const cryptoKeywords = [
            'encbin', 'ht_pub', 'htPub', 'x-ht-pub', 'encrypt', 'decrypt',
            'ECDH', 'ecdh', 'AES', 'aes', 'SM2', 'sm2', 'SM4', 'sm4',
            'publicKey', 'privateKey', 'sharedSecret', 'deriveKey',
            'CryptoJS', 'forge', 'elliptic', 'tweetnacl', 'nacl',
            'secp256', 'P256', 'curve25519', 'x25519',
        ];

        // Check window properties
        for (const key of Object.getOwnPropertyNames(window)) {
            try {
                const val = window[key];
                if (typeof val === 'function' || typeof val === 'object') {
                    const str = String(val).substring(0, 500);
                    for (const kw of cryptoKeywords) {
                        if (str.toLowerCase().includes(kw.toLowerCase())) {
                            if (!results[kw]) results[kw] = [];
                            results[kw].push({global: key, preview: str.substring(0, 100)});
                        }
                    }
                }
            } catch(e) {}
        }

        return results;
    }
    """)

    if crypto_search:
        print("\n*** CRYPTO-RELATED GLOBALS FOUND ***")
        for keyword, matches in crypto_search.items():
            print(f"\n  Keyword: {keyword}")
            for m in matches[:3]:
                print(f"    Global: {m['global']}")
                print(f"    Preview: {m['preview']}")
    else:
        print("  No crypto globals found in window scope")

    print("\n" + "=" * 60)
    print("  MONITORING — Browse HelloTalk to trigger API calls")
    print("  Press Ctrl+C to stop and dump captures")
    print("=" * 60)

    try:
        while True:
            await asyncio.sleep(5)

            # Periodically check for new captures
            captures = await page.evaluate("() => window.__ht_captures")
            if captures:
                keys = captures.get("keys", [])
                ops = captures.get("crypto_ops", [])
                reqs = captures.get("requests", [])

                if keys:
                    print(f"\n  *** {len(keys)} ENCRYPTION KEYS CAPTURED! ***")
                    for k in keys:
                        print(f"    Source: {k['source']}, Key: {k['key'][:60]}...")

                if ops:
                    new_ops = [o for o in ops if not o.get("_printed")]
                    if new_ops:
                        print(f"\n  {len(new_ops)} new crypto operations:")
                        for o in new_ops:
                            print(f"    {o['op']}: {json.dumps({k:v for k,v in o.items() if k not in ('timestamp','_printed')})[:200]}")
                            o["_printed"] = True

    except KeyboardInterrupt:
        pass

    # Final dump
    print("\n\nFinal capture dump...")
    captures = await page.evaluate("() => window.__ht_captures")

    output_dir = Path("captures")
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "crypto_captures.json", "w") as f:
        json.dump(captures, f, indent=2, default=str, ensure_ascii=False)

    print(f"\nSaved to captures/crypto_captures.json")
    print(f"  Keys: {len(captures.get('keys', []))}")
    print(f"  Crypto ops: {len(captures.get('crypto_ops', []))}")
    print(f"  Requests: {len(captures.get('requests', []))}")

    if captures.get("keys"):
        print("\n*** ENCRYPTION KEYS ***")
        for k in captures["keys"]:
            print(f"  {k['key']}")

    if captures.get("crypto_ops"):
        print("\n*** CRYPTO OPERATIONS ***")
        for o in captures["crypto_ops"]:
            print(f"  {o['op']}: {json.dumps(o, default=str)[:300]}")

    await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
