import sqlite3
import os

DB_PATH = "aula_cl.db"

def migrate_db():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(texts)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "image_path" not in columns:
            print("Adding 'image_path' column to 'texts' table...")
            cursor.execute("ALTER TABLE texts ADD COLUMN image_path TEXT")
            conn.commit()
            print("Migration successful.")
        else:
            print("'image_path' column already exists.")
            
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_db()
