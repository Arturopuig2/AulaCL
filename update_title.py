from app.database import SessionLocal
from app import models

db = SessionLocal()

def update_quijote_title():
    # Find the text by filename or partial title
    text = db.query(models.Text).filter(models.Text.filename == "el_quijote.txt").first()
    
    if text:
        text.title = "Don Quijote de la Mancha"
        db.commit()
        print(f"Updated text {text.id} title to: {text.title}")
    else:
        print("Text not found.")
    
    db.close()

if __name__ == "__main__":
    update_quijote_title()
