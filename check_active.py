from app.database import SessionLocal
from app.models import Text

db = SessionLocal()
texts = db.query(Text).all()
print(f"Total rows: {len(texts)}")
for t in texts:
    print(f"ID: {t.id}, Title: {t.title}, Active: {t.is_active}, Audio: {t.audio_path}")
