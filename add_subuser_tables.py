from app.database import SessionLocal, engine, Base
from app import models
from sqlalchemy import text as sql_text

import time
import sqlite3
from sqlalchemy import exc

def migrate_database():
    print("Creating new tables...")
    max_retries = 5
    for i in range(max_retries):
        try:
            # This will create tables if they don't exist
            Base.metadata.create_all(bind=engine)
            print("Tables created (SubUser, License, LoginAttempt).")
            return
        except exc.OperationalError as e:
            if "database is locked" in str(e):
                print(f"Database locked, retrying in {i+1} seconds...")
                time.sleep(i+1)
            else:
                raise e
    print("Failed to acquire lock after retries.")

if __name__ == "__main__":
    migrate_database()
