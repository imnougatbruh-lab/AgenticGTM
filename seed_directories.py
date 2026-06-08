import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
import models
from directories import TARGET_DIRECTORIES

def run():
    db = SessionLocal()
    products = db.query(models.Product).all()
    total_added = 0
    for product in products:
        existing = {s.directory_name for s in db.query(models.Submission).filter_by(product_id=product.id).all()}
        
        added = 0
        for name, url in TARGET_DIRECTORIES:
            if name not in existing:
                sub = models.Submission(
                    product_id=product.id,
                    directory_name=name,
                    directory_url=url,
                    status="pending"
                )
                db.add(sub)
                added += 1
        db.commit()
        print(f"Added {added} new directories to product {product.id}")
        total_added += added
        
    print(f"Total directories seeded into database: {total_added}")

if __name__ == "__main__":
    run()
