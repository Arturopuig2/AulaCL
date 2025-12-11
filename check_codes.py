from app.database import SessionLocal
from app import models

def list_codes():
    db = SessionLocal()
    try:
        codes = db.query(models.InvitationCode).all()
        print(f"Found {len(codes)} codes in DB:")
        print("-" * 40)
        print(f"{'CODE':<15} | {'USED?':<10} | {'USER ID':<10}")
        print("-" * 40)
        for c in codes:
            status = "USED" if c.is_used else "OPEN"
            user = c.used_by_user_id if c.used_by_user_id else "-"
            print(f"{c.code:<15} | {status:<10} | {user:<10}")
        print("-" * 40)
    finally:
        db.close()

if __name__ == "__main__":
    list_codes()
