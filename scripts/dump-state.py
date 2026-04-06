#!/usr/bin/env python3
"""Dump all browser state to find encryption keys."""
import asyncio
import json
from playwright.async_api import async_playwright

JS_CODE = r"""
() => {
    const out = {};

    // localStorage
    for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i);
        const v = localStorage.getItem(k);
        out["ls_" + k] = v ? v.substring(0, 1000) : null;
    }

    // sessionStorage
    for (let i = 0; i < sessionStorage.length; i++) {
        const k = sessionStorage.key(i);
        const v = sessionStorage.getItem(k);
        out["ss_" + k] = v ? v.substring(0, 1000) : null;
    }

    // Vue store
    const app = document.querySelector("#app");
    if (app && app.__vue__ && app.__vue__.$store) {
        const state = app.__vue__.$store.state;
        out["vuex_keys"] = Object.keys(state).join(", ");
        for (const key of Object.keys(state)) {
            try {
                out["vuex_" + key] = JSON.stringify(state[key]).substring(0, 1000);
            } catch (e) {
                out["vuex_" + key] = "[circular]";
            }
        }
    }

    // Check globals
    out["has_CryptoJS"] = typeof CryptoJS !== "undefined";
    out["has_JSEncrypt"] = typeof JSEncrypt !== "undefined";

    // Try to find the encryption config via the _ utility object
    // The generateEncryptyData function uses _ (underscore/util namespace)
    try {
        if (typeof ta !== "undefined" && ta.config) {
            out["ta_config"] = JSON.stringify(ta.config).substring(0, 1000);
        }
    } catch (e) {}

    // Check for any window property containing 'public' or 'key' or 'encrypt'
    for (const key of Object.getOwnPropertyNames(window)) {
        try {
            if (key.toLowerCase().includes("encrypt") ||
                key.toLowerCase().includes("pubkey") ||
                key.toLowerCase().includes("publickey") ||
                key.toLowerCase().includes("rsaconfig")) {
                out["window." + key] = String(window[key]).substring(0, 500);
            }
        } catch (e) {}
    }

    return out;
}
"""


async def main():
    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
    page = browser.contexts[0].pages[0]
    print(f"Connected: {page.url}")

    result = await page.evaluate(JS_CODE)

    print("\n=== ALL STATE ===\n")
    for k, v in sorted(result.items()):
        if v and str(v) != "null" and str(v) != "false":
            print(f"{k}:")
            print(f"  {v}\n")

    # Save
    with open("captures/browser_state.json", "w") as f:
        json.dump(result, f, indent=2, default=str, ensure_ascii=False)
    print("Saved to captures/browser_state.json")

    await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
