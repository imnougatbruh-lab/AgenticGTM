import json
from playwright.sync_api import sync_playwright
from database import SessionLocal
from models import SocialCredential

def main():
    user_id = 1
    print("=== EXTRACTING TWITTER COOKIES TO DATABASE ===")
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=f"./playwright_profiles/user_{user_id}",
                headless=True
            )
            cookies = browser.cookies()
            browser.close()
            
            if not cookies:
                print("No cookies found. Did you log in?")
                return
                
            cookies_json = json.dumps(cookies)
            
            # Save to database
            db = SessionLocal()
            cred = db.query(SocialCredential).filter(
                SocialCredential.user_id == user_id, 
                SocialCredential.platform == 'Twitter'
            ).first()
            
            if cred:
                cred.session_cookies = cookies_json
                db.commit()
                print("Cookies successfully saved to database!")
            else:
                print("SocialCredential not found for user 1. Creating new...")
                new_cred = SocialCredential(
                    user_id=user_id,
                    platform='Twitter',
                    session_cookies=cookies_json
                )
                db.add(new_cred)
                db.commit()
                print("New SocialCredential created and cookies saved!")
                
            db.close()
        except Exception as e:
            print(f"Error extracting cookies: {e}")

if __name__ == "__main__":
    main()
