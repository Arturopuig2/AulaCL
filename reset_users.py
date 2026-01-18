
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models import User
from app.auth import get_password_hash

# USAGE: 
# 1. Ensure this file is in the root directory.
# 2. Run with specific environment variables if mostly local, or on Render Shell.
#    python reset_users.py

def reset_users():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set.")
        return

    # Fix for SQLAlchemy 1.4+
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    print("WARNING: This will delete ALL users.")
    confirm = input("Type 'yes' to confirm: ")
    if confirm != "yes":
        print("Aborted.")
        return

    try:
        # Delete dependencies first to satisfy Foreign Keys
        print("Deleting dependent records...")
        db.execute(text("DELETE FROM reading_attempts"))
        db.execute(text("DELETE FROM licenses"))
        db.execute(text("DELETE FROM subusers"))
        db.execute(text("DELETE FROM invitation_codes"))
        db.commit()

        # Delete all users
        num_deleted = db.query(User).delete()
        db.commit()
        print(f"Deleted {num_deleted} users.")
        
        # Create default Admin
        admin_user = User(
            username="admin",
            email="admin@aulacl.com", # Dummy email
            hashed_password=get_password_hash("Arturo12345@"),
            course_level="ALL",
            name="Super Admin"
        )
        db.add(admin_user)
        db.commit()
        
        print("------------------------------------------------")
        print("SUCCESS! Users reset.")
        print("New Admin Credentials:")
        print("Username: admin")
        print("Password: Arturo12345@")
        print("------------------------------------------------")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_users()
