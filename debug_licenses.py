
import sqlite3
from app.database import SessionLocal, engine
from app import models
from sqlalchemy import text

# 1. Check SQLite Schema directly
print("--- SQLITE SCHEMA CHECK ---")
conn = sqlite3.connect('aula_cl.db')
cursor = conn.cursor()
try:
    cursor.execute("PRAGMA table_info(licenses)")
    columns = cursor.fetchall()
    found = False
    for col in columns:
        print(f"Column: {col[1]} ({col[2]})")
        if col[1] == 'used_by_user_id':
            found = True
    
    if found:
        print("SUCCESS: 'used_by_user_id' column exists in DB.")
    else:
        print("FAILURE: 'used_by_user_id' column MISSING in DB.")
except Exception as e:
    print(f"Schema check error: {e}")
finally:
    conn.close()

# 2. Check SQLAlchemy ORM Mapping
print("\n--- ORM MAPPING CHECK ---")
db = SessionLocal()
try:
    # Try to query licenses
    # This triggers the mapper
    count = db.query(models.License).count()
    print(f"License count: {count}")
    
    # Try to insert a dummy license linked to a user
    import secrets
    key = "TEST-" + secrets.token_hex(4)
    
    # Ensure there is a user
    user = db.query(models.User).first()
    if not user:
        print("No users found to test linking. Creating admin...")
        user = models.User(username="admin_test", hashed_password="pw")
        db.add(user)
        db.commit()
        db.refresh(user)
        
    print(f"Linking to user: {user.username} (ID: {user.id})")
    
    lic = models.License(
        key=key,
        used_by_user_id=user.id
    )
    db.add(lic)
    db.commit()
    db.refresh(lic)
    print(f"Successfully created license {lic.key} linked to user {lic.user.username if lic.user else 'None'}")
    
    # Cleanup
    db.delete(lic)
    db.commit()
    print("Cleanup successful.")
    
except Exception as e:
    print(f"ORM Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
