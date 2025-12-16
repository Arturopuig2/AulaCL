import os
from app.database import SessionLocal
from app import models

db = SessionLocal()

def add_ada_yey():
    filename = "Ada_Yey.txt"
    title = "Ada Yey"
    
    # Check if text exists
    text = db.query(models.Text).filter(models.Text.filename == filename).first()
    
    if not text:
        print(f"Creating new text entry for {title}...")
        text = models.Text(
            title=title,
            filename=filename,
            course_level="PRIMARIA",
            content_path="data/texts/PRIMARIA/Ada_Yey.txt",
            # assuming no audio for now, or placeholder
            audio_path="" 
        )
        db.add(text)
        db.commit()
        db.refresh(text)
    else:
        print(f"Text {title} already exists. Updating questions...")
        
    # Delete old questions for this text to avoid duplicates
    db.query(models.Question).filter(models.Question.text_id == text.id).delete()
    
    questions = [
        # Opción Múltiple
        {
            "question_content": "¿Cómo es la personalidad de Ada?",
            "options": ["Triste y tímida", "Alegre y aventurera", "Aburrida y seria"],
            "correct_answer": 1
        },
        {
            "question_content": "¿Cómo se llama el abuelo de Ada?",
            "options": ["Antonio", "Eugenio", "Fortunio"],
            "correct_answer": 2
        },
        {
            "question_content": "¿Dónde vive Ada?",
            "options": ["En una casa de campo", "En un apartamento en la ciudad", "En una cabaña en la playa"],
            "correct_answer": 0
        },
        {
            "question_content": "¿Qué hay cerca de la casa de Ada?",
            "options": ["Un centro comercial", "Una granja de ovejas", "Un parque de atracciones"],
            "correct_answer": 1
        },
        {
            "question_content": "¿Qué es lo que más le gusta hacer a Ada?",
            "options": ["Cuidar el huerto", "Ayudar a inventar cosas", "Observar a los animales"],
            "correct_answer": 2
        },
        
        # Verdadero / Falso
        {
            "question_content": "La casa de Ada está muy cerca de la ciudad.",
            "options": ["Verdadero", "Falso"],
            "correct_answer": 1  # Falso, está lejos
        },
        {
            "question_content": "El abuelo Fortunio tiene un taller lleno de máquinas.",
            "options": ["Verdadero", "Falso"],
            "correct_answer": 0
        },
        {
            "question_content": "Ada siente un cosquilleo en la frente cuando observa a los animales.",
            "options": ["Verdadero", "Falso"],
            "correct_answer": 0
        },
        {
            "question_content": "Ada vive sola en la casa de campo.",
            "options": ["Verdadero", "Falso"],
            "correct_answer": 1
        },
        {
            "question_content": "A Ada no le gusta ayudar a su abuelo en el huerto.",
            "options": ["Verdadero", "Falso"],
            "correct_answer": 1
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
    print("Questions for Ada Yey inserted successfully.")
    db.close()

if __name__ == "__main__":
    add_ada_yey()
