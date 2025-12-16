import os
from openai import OpenAI
from app.database import SessionLocal
from app import models

db = SessionLocal()

# Requires OPENAI_API_KEY env var
client = OpenAI()

def generate_audio_for_ada():
    title = "Ada Yey"
    text = db.query(models.Text).filter(models.Text.title == title).first()
    
    if not text:
        print(f"Text '{title}' not found in database.")
        return

    print(f"Generating audio for '{title}' using OpenAI TTS (nova)...")
    
    # Read content
    if not os.path.exists(text.content_path):
        print(f"Content file not found at {text.content_path}")
        return
        
    with open(text.content_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Generate MP3 using OpenAI
    audio_filename = "Ada_Yey.mp3"
    audio_dir = "static/audio"
    os.makedirs(audio_dir, exist_ok=True)
    full_audio_path = os.path.join(audio_dir, audio_filename)
    
    # Inject pauses for paragraph breaks
    processed_content = content.replace(".\n", ".\n\n... ... ... ...\n\n")
    processed_content = processed_content.replace(". ", ". ... ")

    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=processed_content
    )
    
    response.stream_to_file(full_audio_path)
    print(f"Audio saved to {full_audio_path}")
    
    # Update DB path (ensure it's just filename as per fix)
    text.audio_path = audio_filename
    db.commit()
    print("Database updated with audio path.")
    
    db.close()

if __name__ == "__main__":
    generate_audio_for_ada()
