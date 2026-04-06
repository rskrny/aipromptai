#!/usr/bin/env python3
"""
HelloTalk Web Engagement Bot

Automates engagement actions on web.hellotalk.com to boost your account's
visibility signals. Works through the browser (DOM manipulation) — no
encryption issues.

SETUP:
1. Open Chrome with remote debugging:
   "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
2. Log into web.hellotalk.com manually (QR code scan from phone)
3. Run this script:
   python scripts/web-bot.py

MODES:
  python scripts/web-bot.py like-moments     — Auto-like moments in feed
  python scripts/web-bot.py view-profiles    — View profiles in discovery (triggers "viewed you")
  python scripts/web-bot.py correct          — Open moments that need corrections
  python scripts/web-bot.py full-cycle       — Run all engagement actions
  python scripts/web-bot.py intercept        — Capture API calls (encryption keys, endpoints)
"""

import asyncio
import json
import sys
import time
import random
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Install playwright: pip install playwright && python -m playwright install chromium")
    sys.exit(1)


# Config
CHROME_CDP = "http://localhost:9222"
BASE_URL = "https://web.hellotalk.com"
MIN_DELAY = 2.0   # Minimum seconds between actions
MAX_DELAY = 5.0   # Maximum seconds between actions
MAX_ACTIONS = 50   # Max actions per session (safety limit)

# Selectors (from hellotalk-automation research + common patterns)
SELECTORS = {
    # Chat/user list
    "user_item": ".userItem, div.userItem, [class*='userItem']",
    "user_name": ".userName, [class*='userName']",
    "unread_badge": ".newMsgCount, [class*='newMsg'], [class*='badge']",

    # Moments
    "moment_item": "[class*='moment'], [class*='feed-item'], [class*='post-item'], article",
    "like_button": "[class*='like'], [class*='heart'], button[aria-label*='like']",
    "liked_indicator": "[class*='liked'], [class*='active'][class*='like']",
    "correction_button": "[class*='correct'], [class*='edit'], [class*='pencil']",
    "moment_image": "[class*='moment'] img, [class*='feed'] img",
    "moment_text": "[class*='moment'] [class*='text'], [class*='content'] pre",

    # Discovery / Find Partners
    "discovery_tab": "[class*='discover'], [class*='find'], [class*='partner'], [class*='search']",
    "profile_card": "[class*='profile'], [class*='card'], [class*='user-card']",
    "next_button": "[class*='next'], [class*='arrow-right'], [class*='swipe']",

    # Navigation
    "moments_tab": "[class*='moment'], a[href*='moment'], [class*='timeline']",
    "chat_tab": "[class*='chat'], a[href*='chat'], [class*='message']",
    "profile_tab": "[class*='profile'], a[href*='profile'], [class*='me']",
}


async def human_delay(min_s=None, max_s=None):
    """Random human-like delay."""
    mn = min_s or MIN_DELAY
    mx = max_s or MAX_DELAY
    await asyncio.sleep(random.uniform(mn, mx))


async def connect_browser():
    """Connect to existing Chrome with remote debugging."""
    pw = await async_playwright().start()
    try:
        browser = await pw.chromium.connect_over_cdp(CHROME_CDP)
        contexts = browser.contexts
        if not contexts:
            print("No browser contexts found. Make sure Chrome is open and logged in.")
            return None, None, pw

        page = contexts[0].pages[0] if contexts[0].pages else await contexts[0].new_page()
        print(f"Connected to Chrome. Current URL: {page.url}")
        return browser, page, pw
    except Exception as e:
        print(f"Failed to connect to Chrome at {CHROME_CDP}")
        print(f"Error: {e}")
        print()
        print("Start Chrome with:")
        print('  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222')
        print()
        print("Then log into web.hellotalk.com")
        return None, None, pw


async def intercept_mode(page):
    """Capture all API calls to find encryption keys and endpoints.
    This is the most important mode — it captures the x-ht-pub key
    and all endpoint data from the real browser session."""

    captured = []
    encryption_keys = []

    async def on_request(request):
        url = request.url
        if "hellotalk" in url or "hellotalk8" in url:
            headers = request.headers
            entry = {
                "method": request.method,
                "url": url,
                "headers": dict(headers),
            }

            # Capture encryption key!
            if "x-ht-pub" in headers:
                key = headers["x-ht-pub"]
                print(f"\n  *** ENCRYPTION KEY CAPTURED ***")
                print(f"  x-ht-pub: {key}")
                print(f"  Key length: {len(key)} chars = {len(key)//2} bytes")
                encryption_keys.append({"url": url, "key": key})
                entry["encryption_key"] = key

            # Capture auth
            if "authorization" in headers:
                entry["auth"] = headers["authorization"][:50] + "..."

            captured.append(entry)
            print(f"  {request.method} {url.split('?')[0]}")

    async def on_response(response):
        url = response.url
        if "hellotalk" in url or "hellotalk8" in url:
            ct = response.headers.get("content-type", "")
            # Try to capture response body for non-encrypted endpoints
            if "json" in ct:
                try:
                    body = await response.json()
                    # Look for interesting fields
                    body_str = json.dumps(body).lower()
                    interesting = any(kw in body_str for kw in [
                        "trust", "score", "weight", "rank", "visible",
                        "flag", "restrict", "ban", "boost", "exposure",
                        "recommend", "level", "remain"
                    ])
                    if interesting:
                        print(f"\n  *** INTERESTING RESPONSE ***")
                        print(f"  URL: {url}")
                        print(f"  {json.dumps(body, indent=2, ensure_ascii=False)[:500]}")
                except:
                    pass

    page.on("request", on_request)
    page.on("response", on_response)

    print("=" * 60)
    print("  INTERCEPT MODE — Capturing all HelloTalk API traffic")
    print("=" * 60)
    print()
    print("  Now browse HelloTalk in the Chrome window.")
    print("  Try these actions to capture the most data:")
    print("    1. Open the Moments tab")
    print("    2. Open the Find Partners / Discovery tab")
    print("    3. View someone's profile")
    print("    4. Like a moment")
    print("    5. Open your own profile/settings")
    print()
    print("  Press Ctrl+C to stop and save captures.")
    print()

    try:
        # Navigate to HelloTalk if not already there
        if "hellotalk" not in page.url:
            await page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
            await human_delay(3, 5)

        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass

    # Save captures
    output_dir = Path("captures")
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "web_intercept.json", "w") as f:
        json.dump(captured, f, indent=2, default=str, ensure_ascii=False)
    print(f"\nSaved {len(captured)} captured requests to captures/web_intercept.json")

    if encryption_keys:
        with open(output_dir / "encryption_keys.json", "w") as f:
            json.dump(encryption_keys, f, indent=2)
        print(f"Saved {len(encryption_keys)} encryption keys to captures/encryption_keys.json")
        print("\n*** ENCRYPTION KEYS FOUND! ***")
        for k in encryption_keys:
            print(f"  {k['key']}")
    else:
        print("\nNo encryption keys captured (web client may use different encryption)")

    return captured, encryption_keys


async def like_moments(page, max_likes=20):
    """Auto-like moments in the feed."""
    print(f"\n=== LIKE MOMENTS MODE (max {max_likes}) ===\n")

    # Navigate to moments
    if "hellotalk" not in page.url:
        await page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        await human_delay(3, 5)

    # Try to find and click Moments tab
    for sel in ["[class*='moment']", "a[href*='moment']", "[class*='timeline']"]:
        tab = page.locator(sel).first
        if await tab.count() > 0:
            await tab.click()
            await human_delay(2, 4)
            break

    liked = 0
    scroll_count = 0

    while liked < max_likes and scroll_count < 30:
        # Find all like buttons
        buttons = page.locator(SELECTORS["like_button"])
        count = await buttons.count()

        for i in range(count):
            if liked >= max_likes:
                break

            btn = buttons.nth(i)
            # Skip already-liked
            classes = await btn.get_attribute("class") or ""
            if "liked" in classes or "active" in classes:
                continue

            try:
                await btn.scroll_into_view_if_needed()
                await human_delay(1, 2)
                await btn.click()
                liked += 1
                print(f"  Liked #{liked}")
                await human_delay()
            except:
                continue

        # Scroll down for more
        await page.evaluate("window.scrollBy(0, 800)")
        await human_delay(1, 3)
        scroll_count += 1

    print(f"\n  Total liked: {liked}")
    return liked


async def view_profiles(page, max_views=15):
    """View profiles in discovery to trigger "who viewed me" notifications."""
    print(f"\n=== VIEW PROFILES MODE (max {max_views}) ===\n")

    if "hellotalk" not in page.url:
        await page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        await human_delay(3, 5)

    # Try to find discovery/find partners tab
    for sel in ["[class*='discover']", "[class*='find']", "[class*='partner']", "a[href*='search']"]:
        tab = page.locator(sel).first
        if await tab.count() > 0:
            await tab.click()
            await human_delay(2, 4)
            break

    viewed = 0
    while viewed < max_views:
        # Find profile cards
        cards = page.locator(SELECTORS["profile_card"])
        count = await cards.count()

        if count == 0:
            # Try scrolling
            await page.evaluate("window.scrollBy(0, 500)")
            await human_delay(2, 3)
            continue

        for i in range(min(count, 5)):
            if viewed >= max_views:
                break

            try:
                card = cards.nth(i)
                await card.click()
                viewed += 1
                print(f"  Viewed profile #{viewed}")
                await human_delay(3, 6)  # Spend time on profile (more realistic)

                # Go back
                await page.go_back()
                await human_delay(2, 3)
            except:
                continue

        # Scroll/next page
        await page.evaluate("window.scrollBy(0, 600)")
        await human_delay(2, 4)

    print(f"\n  Total profiles viewed: {viewed}")
    return viewed


async def full_cycle(page):
    """Run a complete engagement cycle."""
    print("\n=== FULL ENGAGEMENT CYCLE ===\n")

    print("Step 1: Like moments...")
    likes = await like_moments(page, max_likes=15)

    print("\nStep 2: View profiles...")
    views = await view_profiles(page, max_views=10)

    print(f"\n=== CYCLE COMPLETE ===")
    print(f"  Likes: {likes}")
    print(f"  Profile views: {views}")


async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1].lower().replace("-", "_")

    browser, page, pw = await connect_browser()
    if not browser:
        await pw.stop()
        sys.exit(1)

    try:
        if cmd == "intercept":
            await intercept_mode(page)
        elif cmd == "like_moments":
            await like_moments(page)
        elif cmd == "view_profiles":
            await view_profiles(page)
        elif cmd == "full_cycle":
            await full_cycle(page)
        else:
            print(f"Unknown command: {cmd}")
            print("Available: intercept, like-moments, view-profiles, full-cycle")
    finally:
        # Don't close the browser — user's session
        await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
