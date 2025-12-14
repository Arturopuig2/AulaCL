from app.database import SessionLocal, engine
from app import models
from sqlalchemy import text as sql_text

db = SessionLocal()

def migrate_database():
    # 1. Add Column
    try:
        with engine.connect() as conn:
            conn.execute(sql_text("ALTER TABLE users ADD COLUMN name VARCHAR"))
            conn.commit()
        print("Added 'name' column to users table.")
    except Exception as e:
        print(f"Column might already exist or error: {e}")

    # 2. No need to update existing users with dummy names, null is fine.
            
    db.close()

if __name__ == "__main__":
    migrate_database()
