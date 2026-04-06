#!/usr/bin/env python3
"""Find the XTEA encryption key from the browser's Vue store."""
import asyncio
import json
from playwright.async_api import async_playwright

JS_DUMP_STATE = """() => {
    const result = {};

    // All localStorage
    const ls = {};
    for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i);
        ls[k] = localStorage.getItem(k);
    }
    result.localStorage = ls;

    // Cookies
    result.cookies = document.cookie;

    // URL info
    result.url = window.location.href;
    result.hash = window.location.hash;

    // Vue store - dump everything
    const app = document.querySelector("#app");
    if (app && app.__vue__) {
        const vue = app.__vue__;
        if (vue.$store) {
            const state = vue.$store.state;
            const snap = {};
            for (const k of Object.keys(state)) {
                try {
                    snap[k] = JSON.parse(JSON.stringify(state[k]));
                } catch(e) {
                    snap[k] = "[circular]";
                }
            }
            result.vuex = snap;
        }

        // Check vue data
        try {
            result.vue_data = JSON.parse(JSON.stringify(vue.$data));
        } catch(e) {
            result.vue_data = "[error]";
        }
    }

    return result;
}"""


async def main():
    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
    page = browser.contexts[0].pages[0]
    print(f"Connected: {page.url}")

    state = await page.evaluate(JS_DUMP_STATE)

    # Save full state
    with open("captures/full_browser_state.json", "w") as f:
        json.dump(state, f, indent=2, default=str, ensure_ascii=False)

    # Print interesting parts
    print("\n=== COOKIES ===")
    print(state.get("cookies", "none"))

    print("\n=== LOCALSTORAGE ===")
    for k, v in state.get("localStorage", {}).items():
        print(f"  {k}: {str(v)[:200]}")

    print("\n=== VUEX STATE KEYS ===")
    vuex = state.get("vuex", {})
    for k, v in vuex.items():
        v_str = json.dumps(v, ensure_ascii=False, default=str)
        if len(v_str) > 300:
            print(f"  {k}: ({len(v_str)} chars) {v_str[:300]}...")
        else:
            print(f"  {k}: {v_str}")

    print(f"\nFull state saved to captures/full_browser_state.json")

    await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
