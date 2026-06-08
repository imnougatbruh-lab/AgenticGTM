import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
import models
from directories import TARGET_DIRECTORIES

def run():
    db = SessionLocal()
    
    # 1. Wipe all existing directory submissions
    db.query(models.Submission).delete()
    db.commit()
    print("Deleted all old directories from the database.")
    
    # 2. Seed the exact new ones
    products = db.query(models.Product).all()
    total_added = 0
    for product in products:
        added = 0
        for name, url in TARGET_DIRECTORIES:
            sub = models.Submission(
                product_id=product.id,
                directory_name=name,
                directory_url=url,
                status="pending"
            )
            db.add(sub)
            added += 1
        db.commit()
        print(f"Added {added} perfectly curated directories to product {product.id}")
        total_added += added
        
    print(f"Total directories seeded into database: {total_added}")

if __name__ == "__main__":
    run()
