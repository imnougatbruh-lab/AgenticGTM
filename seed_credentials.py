import os
import sys
from database import SessionLocal
from models import User, SocialCredential

def main():
    print("=== AGENTICGTM SOCIAL CREDENTIALS SEEDER ===")
    db = SessionLocal()
    try:
        # Check if user with ID 1 exists, create if not
        user = db.query(User).filter(User.id == 1).first()
        if not user:
            user = User(id=1, email="test@example.com", clerk_id="mock_clerk_1")
            db.add(user)
            db.commit()
            print("Created default User 1 in database.")
        
        platform = input("Select platform (Twitter / Reddit / HackerNews): ").strip()
        if platform not in ["Twitter", "Reddit", "HackerNews"]:
            print("Invalid platform choice. Please select Twitter, Reddit, or HackerNews.")
            return
            
        username = input(f"Enter your {platform} username or email: ").strip()
        password = input(f"Enter your {platform} password: ").strip()
        
        if not username or not password:
            print("Username and password cannot be empty.")
            return

        # Check if credentials exist
        cred = db.query(SocialCredential).filter(SocialCredential.user_id == 1, SocialCredential.platform == platform).first()
        if cred:
            cred.username = username
            cred.password = password
            print(f"Successfully updated credentials for {platform} (User 1)!")
        else:
            cred = SocialCredential(user_id=1, platform=platform, username=username, password=password)
            db.add(cred)
            print(f"Successfully added credentials for {platform} (User 1)!")
            
        db.commit()
    except Exception as e:
        print(f"Error seeding credentials: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
