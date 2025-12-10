from app.database import SessionLocal, engine
from app import models
from sqlalchemy import text as sql_text

db = SessionLocal()

def migrate_database():
    # 1. Add Column
    try:
        with engine.connect() as conn:
            conn.execute(sql_text("ALTER TABLE texts ADD COLUMN language VARCHAR DEFAULT 'es'"))
            conn.commit()
        print("Added 'language' column to texts table.")
    except Exception as e:
        print(f"Column might already exist: {e}")

    # 2. Update Existing Data
    texts = db.query(models.Text).all()
    for t in texts:
        original_lang = t.language
        if "eng" in t.filename.lower() or "english" in t.title.lower():
            t.language = "en"
        elif "val" in t.filename.lower() or "valenci" in t.title.lower():
            t.language = "val"
        else:
            t.language = "es"
        
        if original_lang != t.language:
            print(f"Updated {t.title} language to {t.language}")
            
    db.commit()
    print("Data migration completed.")
    db.close()

if __name__ == "__main__":
    migrate_database()
