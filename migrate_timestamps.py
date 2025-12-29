import sqlite3

def migrate():
    try:
        conn = sqlite3.connect("aula_cl.db")
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE texts ADD COLUMN timestamps JSON")
        conn.commit()
        print("Migration successful: Added 'timestamps' column to 'texts' table.")
    except sqlite3.OperationalError as e:
        print(f"Migration skipped: {e}")
    finally:
        if conn: conn.close()
        
if __name__ == "__main__":
    migrate()
