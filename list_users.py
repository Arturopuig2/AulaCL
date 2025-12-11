from app.database import SessionLocal
from app import models

def list_users():
    db = SessionLocal()
    try:
        users = db.query(models.User).all()
        print(f"Found {len(users)} users:")
        for u in users:
            print(f"ID: {u.id} | Username: '{u.username}' | Course: {u.course_level} | Expires: {u.access_expires_at}")
    finally:
        db.close()

if __name__ == "__main__":
    list_users()
