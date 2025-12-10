from app.database import SessionLocal
from app import models

db = SessionLocal()

def update_users():
    users = db.query(models.User).all()
    count = 0
    for u in users:
        # Update everyone to PRIMARIA to match the new content location
        if u.course_level != "PRIMARIA":
            u.course_level = "PRIMARIA"
            count += 1
    
    db.commit()
    print(f"Updated {count} users to PRIMARIA level.")
    db.close()

if __name__ == "__main__":
    update_users()
