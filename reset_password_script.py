import sys
from app.database import SessionLocal
from app import models
from app.auth import get_password_hash

def reset_password(username, new_password):
    db = SessionLocal()
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        print(f"User '{username}' not found.")
        return

    user.hashed_password = get_password_hash(new_password)
    db.commit()
    print(f"Password for user '{username}' has been updated successfully.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 reset_password_script.py <username> <new_password>")
    else:
        reset_password(sys.argv[1], sys.argv[2])
