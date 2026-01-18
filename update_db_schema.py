
import os
import sqlalchemy
from sqlalchemy import create_engine, text
from app.database import Base

def update_schema():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Fallback to local sqlite for testing if needed, though this is meant for Render
        print("DATABASE_URL not set. Skipping schema update.")
        return

    # Fix for SQLAlchemy 1.4+ deprecated postgres://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    engine = create_engine(database_url)
    connection = engine.connect()

    print("Checking database schema...")

    # TEXTS TABLE
    verify_column(connection, "texts", "image_path", "VARCHAR")
    verify_column(connection, "texts", "timestamps", "JSON")

    # (Add other missing columns here if any found later)
    
    connection.close()
    print("Schema check complete.")

def verify_column(connection, table_name, column_name, column_type):
    try:
        # Check if column exists
        # PostgreSQL specific query
        query = text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='{table_name}' AND column_name='{column_name}';
        """)
        result = connection.execute(query).fetchone()

        if not result:
            print(f"Adding missing column '{column_name}' to table '{table_name}'...")
            alter_query = text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
            connection.execute(alter_query)
            # Commit is implicit in some drivers/versions for DDL, but explicit commit is safer if transaction began
            # SQLAlchemy connection.execute usually autocommits DDL? 
            # In 1.4+, we might need explicit commit if autocommit is off.
            try:
                connection.commit()
            except:
                pass # If driver doesn't support commit on DDL or auto-committed
            print(f"Column '{column_name}' added.")
        else:
            print(f"Column '{column_name}' already exists in '{table_name}'.")

    except Exception as e:
        print(f"Error checking/adding column {column_name}: {e}")

if __name__ == "__main__":
    update_schema()
