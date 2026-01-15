from app.database import SessionLocal
from app import models

db = SessionLocal()
text = db.query(models.Text).filter(models.Text.title.ilike("%LA LIEBRE Y LA TORTUGA%")).first()

if text:
    print(f"ID: {text.id}")
    print(f"Title: {text.title}")
    print(f"Audio Path: {text.audio_path}")
    print(f"Content Path: {text.content_path}")
else:
    print("Text not found")
