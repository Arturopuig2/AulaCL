from app.database import SessionLocal
from app import models, security_utils

db = SessionLocal()

def generate_licenses(count=5):
    print(f"Generating {count} licenses...")
    for _ in range(count):
        key = security_utils.generate_license_key()
        license_obj = models.License(key=key, duration_days=365)
        db.add(license_obj)
        print(f"Key: {key}")
    db.commit()
    print("Done.")
    db.close()

if __name__ == "__main__":
    generate_licenses()
