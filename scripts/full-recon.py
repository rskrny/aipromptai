#!/usr/bin/env python3
"""
Full recon: navigate every section of HelloTalk web, capture all decrypted data,
and look for visibility/trust/boost/ranking fields we can exploit.
"""
import asyncio
import json
from playwright.async_api import async_playwright

HOOK = """(() => {
    if (window.__recon_hooks) return 'already';
    window.__recon_hooks = true;
    window.__decrypted_data = [];
    window.__xhr_requests = [];

    var origParse = JSON.parse;
    JSON.parse = function(text) {
        var result = origParse.apply(this, arguments);
        if (typeof text === 'string' && text.length > 50) {
            window.__decrypted_data.push({
                size: text.length,
                text: text.substring(0, 20000),
                time: Date.now(),
                label: window.__current_section || 'unknown'
            });
        }
        return result;
    };

    var origDecode = TextDecoder.prototype.decode;
    TextDecoder.prototype.decode = function(input) {
        var result = origDecode.apply(this, arguments);
        if (result && result.length > 50) {
            window.__decrypted_data.push({
                source: 'TextDecoder',
                size: result.length,
                text: result.substring(0, 20000),
                time: Date.now(),
                label: window.__current_section || 'unknown'
            });
        }
        return result;
    };

    // Hook XHR to see request URLs
    var origOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url) {
        this._url = url;
        if (url.indexOf('hellotalk') > -1) {
            window.__xhr_requests.push({
                method: method,
                url: url.substring(0, 300),
                time: Date.now(),
                label: window.__current_section || 'unknown'
            });
        }
        return origOpen.apply(this, arguments);
    };

    return 'installed';
})()"""


async def get_captures(page, label):
    """Get new captures and tag them."""
    data = await page.evaluate("() => window.__decrypted_data || []")
    xhr = await page.evaluate("() => window.__xhr_requests || []")
    return data, xhr


async def main():
    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
    page = browser.contexts[0].pages[0]
    print(f"URL: {page.url}")

    # Install hooks
    r = await page.evaluate(HOOK)
    print(f"Hooks: {r}")

    all_captures = []
    all_xhr = []

    # === SECTION 1: Chat list (already loaded) ===
    await page.evaluate("() => { window.__current_section = 'chat_list'; }")
    print("\n=== SECTION 1: Chat List ===")
    await asyncio.sleep(2)
    data, xhr = await get_captures(page, "chat_list")
    print(f"  Captures: {len(data)}, XHR: {len(xhr)}")
    all_captures.extend(data)
    all_xhr.extend(xhr)

    # Click on your own profile to see account data
    await page.evaluate("() => { window.__decrypted_data = []; window.__xhr_requests = []; window.__current_section = 'my_profile'; }")
    print("\n=== SECTION 2: My Profile ===")
    try:
        # Click on the profile/avatar area
        profile = page.locator(".selfProfile-box, .headPortrait-box, [class*='selfProfile']").first
        if await profile.count() > 0:
            await profile.click()
            await asyncio.sleep(3)
            data, xhr = await get_captures(page, "my_profile")
            print(f"  Captures: {len(data)}, XHR: {len(xhr)}")
            all_captures.extend(data)
            all_xhr.extend(xhr)
    except Exception as e:
        print(f"  Profile click failed: {e}")

    # Look for settings/menu
    await page.evaluate("() => { window.__decrypted_data = []; window.__xhr_requests = []; window.__current_section = 'menu'; }")
    print("\n=== SECTION 3: Menu/Settings ===")
    try:
        menu = page.locator(".chatListMoreMenu, [class*='MoreMenu'], .el-icon-more").first
        if await menu.count() > 0:
            await menu.click()
            await asyncio.sleep(2)
            data, xhr = await get_captures(page, "menu")
            print(f"  Captures: {len(data)}, XHR: {len(xhr)}")
            all_captures.extend(data)
            all_xhr.extend(xhr)
            # Click away to close menu
            await page.locator("body").click(position={"x": 400, "y": 400})
            await asyncio.sleep(1)
    except Exception as e:
        print(f"  Menu failed: {e}")

    # Navigate to different chats to trigger more data loading
    await page.evaluate("() => { window.__decrypted_data = []; window.__xhr_requests = []; window.__current_section = 'chat_click'; }")
    print("\n=== SECTION 4: Click through chats ===")
    items = page.locator(".userItem")
    count = await items.count()
    print(f"  {count} chats available")
    for i in range(min(5, count)):
        try:
            await items.nth(i).click()
            await asyncio.sleep(2)
        except:
            pass
    data, xhr = await get_captures(page, "chat_click")
    print(f"  Captures: {len(data)}, XHR: {len(xhr)}")
    all_captures.extend(data)
    all_xhr.extend(xhr)

    # Now let's look for any navigation to Moments or Discovery
    # Check what other elements exist on the page
    await page.evaluate("() => { window.__decrypted_data = []; window.__xhr_requests = []; window.__current_section = 'navigation'; }")
    print("\n=== SECTION 5: Looking for navigation elements ===")
    nav_html = await page.evaluate("""() => {
        var els = document.querySelectorAll('a, button, [class*="tab"], [class*="nav"], [class*="menu"]');
        var result = [];
        for (var i = 0; i < Math.min(els.length, 50); i++) {
            var el = els[i];
            result.push({
                tag: el.tagName,
                class: el.className ? el.className.substring(0, 100) : '',
                text: el.textContent ? el.textContent.trim().substring(0, 50) : '',
                href: el.href || ''
            });
        }
        return result;
    }""")
    for n in nav_html:
        if n.get('text') or n.get('href'):
            print(f"  {n['tag']} .{n['class'][:40]} text='{n['text']}' href={n['href'][:60]}")

    # === ANALYZE ALL CAPTURES ===
    print("\n" + "=" * 60)
    print("  ANALYZING ALL CAPTURED DATA")
    print("=" * 60)

    # Combine and save
    full_output = {
        "captures": all_captures,
        "xhr": all_xhr,
    }

    with open("captures/full_recon.json", "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=2, ensure_ascii=False)

    # Search all captured data for exploit-relevant fields
    exploit_keywords = [
        "trust", "score", "weight", "rank", "visible", "visibility",
        "flag", "restrict", "ban", "shadow", "penalty", "suppress",
        "boost", "exposure", "recommend", "level", "vip", "premium",
        "coin", "diamond", "balance", "purchase", "product",
        "active", "status", "privilege", "permission", "limit",
        "discover", "search", "match", "nearby", "partner",
        "profile_score", "quality", "spam", "abuse", "report",
    ]

    print(f"\nSearching {len(all_captures)} captures for exploit keywords...")
    findings = []

    for cap in all_captures:
        text = cap.get("text", "")
        text_lower = text.lower()
        for kw in exploit_keywords:
            if kw in text_lower:
                # Find the context
                idx = text_lower.find(kw)
                context = text[max(0, idx - 100):idx + len(kw) + 200]
                findings.append({
                    "keyword": kw,
                    "section": cap.get("label", "?"),
                    "context": context[:400],
                })

    if findings:
        print(f"\n*** {len(findings)} EXPLOIT-RELEVANT FIELDS FOUND ***")
        seen = set()
        for f in findings:
            key = f"{f['keyword']}:{f['context'][:50]}"
            if key not in seen:
                seen.add(key)
                print(f"\n  [{f['keyword']}] in {f['section']}:")
                print(f"    {f['context'][:300]}")
    else:
        print("No exploit keywords found in captures.")

    print(f"\nAll data saved to captures/full_recon.json")

    await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
