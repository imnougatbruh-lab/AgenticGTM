import os
import sys
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

def main():
    user_id = 1
    print("=== TWITTER/X AUTO-LOGIN HELPER ===")
    print(f"Opening browser using profile for User {user_id}...")
    print("-----------------------------------------------------------------")
    print("INSTRUCTIONS:")
    print("1. A browser window will open shortly.")
    print("2. Log into your Twitter/X account inside that browser window.")
    print("   (You can use Google login, Apple login, or standard username/password).")
    print("3. Once you see your home feed (fully logged in), come back to this")
    print("   terminal window and press ENTER to save your session.")
    print("-----------------------------------------------------------------")
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=f"./playwright_profiles/user_{user_id}",
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = browser.pages[0] if browser.pages else browser.new_page()
            
            stealth = Stealth()
            stealth.apply_stealth_sync(page)
            
            page.goto("https://twitter.com/login", wait_until="load", timeout=60000)
            
            input("\n>>> PRESS ENTER HERE AFTER YOU HAVE LOGGED IN SUCCESSFULLY TO SAVE...")
            
            print("Saving session and closing browser...")
            browser.close()
            print("Session saved successfully! You can now run the crawler in background.")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
