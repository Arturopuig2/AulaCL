from app.database import SessionLocal, engine, Base
from app import models
import json

Base.metadata.create_all(bind=engine)
db = SessionLocal()

def seed():
    # Check if text exists
    if db.query(models.Text).filter(models.Text.filename == "el_quijote.txt").first():
        print("Data already exists.")
        return

    # Create Text
    text = models.Text(
        title="Don Quijote de la Mancha (Intro)",
        filename="el_quijote.txt",
        course_level="1ESO",
        content_path="data/texts/1ESO/el_quijote.txt",
        audio_path=None # No audio for this sample
    )
    db.add(text)
    db.commit()
    db.refresh(text)

    # Create Questions
    questions = [
        {
            "question_content": "¿Qué comía el hidalgo los sábados?",
            "options": ["Lantejas", "Duelos y quebrantos", "Salpicón", "Palomino"],
            "correct_answer": 1
        },
        {
            "question_content": "¿Cuál era la edad aproximada del hidalgo?",
            "options": ["Cuarenta años", "Treinta años", "Cincuenta años", "Sesenta años"],
            "correct_answer": 2
        },
        {
            "question_content": "¿Cómo se llamaba probablemente el hidalgo?",
            "options": ["Quijada", "Quesada", "Quejana", "Quijote"],
            "correct_answer": 2
        }
    ]

    for q in questions:
        db_q = models.Question(
            text_id=text.id,
            question_content=q["question_content"],
            options=q["options"],
            correct_answer=q["correct_answer"]
        )
        db.add(db_q)
    
    db.commit()
    print("Database seeded!")

if __name__ == "__main__":
    seed()
