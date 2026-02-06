
import os
import sqlalchemy
from sqlalchemy import create_engine, text
from app.database import Base

def update_schema():
    database_url = os.getenv("DATABASE_URL", "sqlite:///./aula_cl.db")
    if not database_url:
        print("DATABASE_URL not set and no default found. Skipping.")
        return

    # Fix for SQLAlchemy 1.4+ deprecated postgres://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    engine = create_engine(database_url)
    connection = engine.connect()

    print("Checking database schema...")

    # USERS TABLE
    verify_column(connection, "users", "is_teacher", "BOOLEAN DEFAULT FALSE")
    
    # TEXTS TABLE
    verify_column(connection, "texts", "image_path", "VARCHAR")
    verify_column(connection, "texts", "timestamps", "JSON")
    
    # READING ATTEMPTS
    verify_column(connection, "reading_attempts", "subuser_id", "INTEGER")
    
    # LICENSES TABLE
    verify_column(connection, "licenses", "used_by_subuser_id", "INTEGER")
    verify_column(connection, "licenses", "used_by_user_id", "INTEGER")
    # Postgres needs explicit foreign key? Usually integer is enough for code-level logic, 
    # but database integrity relies on Constraints. verify_column only adds column.
    
    # (Add other missing columns here if any found later)

    # (Add other missing columns here if any found later)
    
    # 3. DATA FIXES
    fix_audio_paths(connection)
    
    connection.close()
    print("Schema check complete.")

def verify_column(connection, table_name, column_name, column_type):
    try:
        # Cross-platform check
        database_url = str(connection.engine.url)
        is_sqlite = "sqlite" in database_url

        exists = False
        if is_sqlite:
            # SQLite check
            check_query = text(f"PRAGMA table_info({table_name})")
            rows = connection.execute(check_query).fetchall()
            exists = any(row[1] == column_name for row in rows)
        else:
            # PostgreSQL check
            check_query = text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='{table_name}' AND column_name='{column_name}';
            """)
            result = connection.execute(check_query).fetchone()
            exists = bool(result)

        if not exists:
            print(f"Adding missing column '{column_name}' to table '{table_name}'...")
            alter_query = text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
            connection.execute(alter_query)
            try:
                connection.commit()
            except:
                pass 
            print(f"Column '{column_name}' added.")
        else:
            print(f"Column '{column_name}' already exists in '{table_name}'.")

    except Exception as e:
        print(f"Error checking/adding column {column_name}: {e}")

def fix_audio_paths(connection):
    """
    Ensures all audio paths start with '/' to work with mounts correctly.
    """
    try:
        print("Checking audio paths...")
        # Get all texts with audio
        query = text("SELECT id, audio_path FROM texts WHERE audio_path IS NOT NULL")
        texts = connection.execute(query).fetchall()
        
        count = 0
        for t in texts:
            t_id = t[0]
            path = t[1]
            if path and not path.startswith("/") and not path.startswith("http"):
                new_path = "/" + path
                print(f"Fixing ID {t_id}: {path} -> {new_path}")
                update_query = text("UPDATE texts SET audio_path = :path WHERE id = :id")
                connection.execute(update_query, {"path": new_path, "id": t_id})
                count += 1
                
        if count > 0:
            try:
                connection.commit()
                print(f"Fixed {count} audio paths.")
            except:
                pass
    except Exception as e:
        print(f"Error fixing audio paths: {e}")

if __name__ == "__main__":
    update_schema()
