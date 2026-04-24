from app.database import SessionLocal
from app.routers.auth import get_licenses
from app.models import User as DBUser

db = SessionLocal()
admin = db.query(DBUser).filter(DBUser.username == 'admin').first()
if not admin:
    admin = DBUser(username="admin")

try:
    print("Getting licenses...")
    licenses = get_licenses(current_user=admin, db=db)
    print("Success! Number of licenses:", len(licenses))
    for i, l in enumerate(licenses):
        # Trigger serialization
        import json
        json.dumps(l, default=str)
    print("All licenses serialized successfully.")
except Exception as e:
    import traceback
    print("FAILED!")
    traceback.print_exc()
