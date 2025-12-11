from app.database import SessionLocal
from app import models
from datetime import datetime

def check_user():
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.username == "arturo").first()
        if user:
            print(f"User: {user.username}")
            print(f"Expires At: {user.access_expires_at}")
            print(f"Current UTC: {datetime.utcnow()}")
            
            if user.access_expires_at and user.access_expires_at > datetime.utcnow():
                print("✅ STATUS: PREMIUM ACTIVE")
            else:
                print("❌ STATUS: EXPIRED or NULL")
        else:
            print("User 'arturo' not found.")
    finally:
        db.close()

if __name__ == "__main__":
    check_user()
