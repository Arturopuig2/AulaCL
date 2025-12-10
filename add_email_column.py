from app.database import SessionLocal, engine
from app import models
from sqlalchemy import text as sql_text

db = SessionLocal()

def migrate_database():
    # 1. Add Column
    try:
        with engine.connect() as conn:
            conn.execute(sql_text("ALTER TABLE users ADD COLUMN email VARCHAR"))
            conn.commit()
        print("Added 'email' column to users table.")
    except Exception as e:
        print(f"Column might already exist or error: {e}")

    # 2. Update Existing Users with dummy email to avoid null issues if we enforce unique later
    users = db.query(models.User).all()
    for u in users:
        if not u.email:
            u.email = f"{u.username}@example.com"
            print(f"Updated {u.username} with email: {u.email}")
            
    db.commit()
    print("User email migration completed.")
    db.close()

if __name__ == "__main__":
    migrate_database()
