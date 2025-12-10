from app.database import SessionLocal
from app import models

db = SessionLocal()

def check_paths():
    texts = db.query(models.Text).all()
    for t in texts:
        print(f"ID: {t.id} | Title: {t.title} | Path: {t.content_path}")

    db.close()

if __name__ == "__main__":
    check_paths()
