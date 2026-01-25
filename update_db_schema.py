
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
    # Make user_id nullable if it wasn't? Standard SQL for ALTER TABLE nullable is complex across DBs, 
    # but in SQLite/PG usually null is default. 
    # For now just ensuring subuser_id exists.

    # (Add other missing columns here if any found later)
    
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

if __name__ == "__main__":
    update_schema()
