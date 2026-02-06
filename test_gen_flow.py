
from app import models, schemas
from app.database import SessionLocal
from app.routers import auth
from fastapi import HTTPException

db = SessionLocal()

# 1. Fetch Admin User
admin = db.query(models.User).filter(models.User.username == "admin").first()
if not admin:
    print("Admin user not found. Creating mock admin.")
    admin = models.User(username="admin", is_teacher=True, hashed_password="pw")
    db.add(admin)
    db.commit()
    db.refresh(admin)

print(f"User: {admin.username} (Is Teacher: {admin.is_teacher})")

# 2. Call Generate Licenses directly
try:
    print("Calling generate_licenses...")
    # NOTE: generate_licenses returns List[str]
    result = auth.generate_licenses(
        count=1,
        duration_days=365,
        current_user=admin, # Pydantic model expected? No, SQLAlchemy model is what Dependency returns usually, but Type hint says schemas.User.
        # Wait, get_current_user returns models.User or schemas.User?
        # Let's check auth.py implementation.
        db=db
    )
    print(f"Result: {result}")
    print("SUCCESS")
except Exception as e:
    print(f"FAILURE: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
