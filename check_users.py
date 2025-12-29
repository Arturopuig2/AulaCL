from app.database import SessionLocal
from app import models

db = SessionLocal()
users = db.query(models.User).all()

print(f"Total Users: {len(users)}")
for u in users:
    print(f"ID: {u.id} | Username: {u.username} | Email: {u.email} | HashedPwd: {u.hashed_password[:10]}...")
