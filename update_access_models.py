from app.database import engine
from app import models
import sqlite3

def migrate():
    print("Migrating Access Control models...")
    conn = sqlite3.connect("aula_cl.db")
    cursor = conn.cursor()
    
    # 1. Create invitation_codes table if not exists
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invitation_codes (
                code VARCHAR PRIMARY KEY,
                is_used BOOLEAN,
                created_at DATETIME,
                used_at DATETIME,
                used_by_user_id INTEGER,
                FOREIGN KEY(used_by_user_id) REFERENCES users(id)
            )
        """)
        print("✅ Created/Verified invitation_codes table.")
    except Exception as e:
        print(f"❌ Error creating invitation_codes: {e}")

    # 2. Add access_expires_at column to users if not exists
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'access_expires_at' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN access_expires_at DATETIME")
            print("✅ Added access_expires_at column to users.")
        else:
            print("ℹ️ access_expires_at column already exists.")
    except Exception as e:
        print(f"❌ Error checking/adding column: {e}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
