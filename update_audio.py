from app.database import SessionLocal
from app import models

db = SessionLocal()

def enable_audio():
    text = db.query(models.Text).filter(models.Text.filename == "el_quijote.txt").first()
    if text:
        text.audio_path = "el_quijote.mp3"
        db.commit()
        print("Audio path updated for Don Quijote.")
    else:
        print("Text not found.")
    db.close()

if __name__ == "__main__":
    enable_audio()
