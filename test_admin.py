from app.database import SessionLocal
from app.routers.auth import get_licenses
from app.schemas import User
from app.models import User as DBUser

db = SessionLocal()
admin = DBUser(username="admin")

try:
    licenses = get_licenses(current_user=admin, db=db)
    print("Success! Number of licenses:", len(licenses))
    # print(licenses[0] if licenses else "No licenses")
except Exception as e:
    import traceback
    traceback.print_exc()
import json
print(json.dumps([l for l in licenses[:1]], default=str))
