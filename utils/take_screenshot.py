import sys
from playwright.sync_api import sync_playwright
import time

def take_screenshot(url, output_path):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Emulate a mobile device (iPhone 12 Pro)
        iphone = p.devices['iPhone 12 Pro']
        context = browser.new_context(**iphone)
        page = context.new_page()
        
        # Navigate
        page.goto(url, wait_until="networkidle", timeout=15000)
        
        # Wait for rendering
        time.sleep(2) 
        
        page.screenshot(path=output_path)
        browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python take_screenshot.py <url> <output_path>")
        sys.exit(1)
        
    url = sys.argv[1]
    output_path = sys.argv[2]
    
    try:
        take_screenshot(url, output_path)
        print("SUCCESS")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
