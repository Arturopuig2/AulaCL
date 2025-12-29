import sqlite3
import os

DB_PATH = "aula_cl.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Add 'category' to 'questions'
        try:
            cursor.execute("ALTER TABLE questions ADD COLUMN category TEXT DEFAULT 'LITERAL'")
            print("Added 'category' column to 'questions' table.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("'category' column already exists in 'questions'.")
            else:
                raise e

        # Add 'details' to 'reading_attempts'
        try:
            cursor.execute("ALTER TABLE reading_attempts ADD COLUMN details JSON")
            print("Added 'details' column to 'reading_attempts' table.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("'details' column already exists in 'reading_attempts'.")
            else:
                raise e

        conn.commit()
        print("Migration completed successfully.")

    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
