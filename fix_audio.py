from app.database import SessionLocal
from app import models

db = SessionLocal()

def fix_audio_path():
    filename = "la_llebre_i_la_tortuga_val.txt"
    text = db.query(models.Text).filter(models.Text.filename == filename).first()
    
    if text:
        text.audio_path = "la_llebre_i_la_tortuga_val.mp3"
        db.commit()
        print(f"Updated audio_path for {text.title} to: {text.audio_path}")
    else:
        print("Text key not found.")
    
    db.close()

if __name__ == "__main__":
    fix_audio_path()
