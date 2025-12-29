import sqlite3
from app.database import SessionLocal
from app.models import Text

print("--- RAW SQL CHECK ---")
try:
    conn = sqlite3.connect("aula_cl.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, timestamps FROM texts")
    rows = cursor.fetchall()
    print(f"Total rows in 'texts' (raw SQL): {len(rows)}")
    for r in rows:
        print(f"ID: {r[0]}, Title: {r[1]}, Timestamps: {r[2]}")
    conn.close()
except Exception as e:
    print(f"Raw SQL Error: {e}")

print("\n--- SQLALCHEMY CHECK ---")
try:
    db = SessionLocal()
    texts = db.query(Text).all()
    print(f"Total rows via SQLAlchemy: {len(texts)}")
    for t in texts:
        print(f"ID: {t.id}, Title: {t.title}")
except Exception as e:
    print(f"SQLAlchemy Error: {e}")
