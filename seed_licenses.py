import os
import secrets
import string
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import InvitationCode, User
from app import database

# Setup DB Connection
database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("ERROR: DATABASE_URL not set.")
    exit(1)

if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(database_url)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def generate_licenses(count=5):
    print(f"Generating {count} new licenses...")
    
    # Check for admin user to assign as creator (optional, usually null is fine or admin id)
    admin = db.query(User).filter(User.username == "admin").first()
    creator_id = admin.id if admin else None

    new_codes = []
    for _ in range(count):
        # Format: LIC-XXXXXXXX
        random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        code_str = f"LIC-{random_part}"
        
        invitation = InvitationCode(
            code=code_str,
            is_used=False,
            created_by_user_id=creator_id
        )
        db.add(invitation)
        new_codes.append(code_str)
    
    db.commit()
    
    print("\n✅ GENERATED LICENSES:")
    for code in new_codes:
        print(f"  👉 {code}")
    print("\nCopy one of these and use it in the dashboard!")

if __name__ == "__main__":
    try:
        generate_licenses()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()
