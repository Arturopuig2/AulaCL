from app.database import SessionLocal
from app import models

db = SessionLocal()

def add_fable():
    filename = "la_liebre_y_la_tortuga_esp.txt"
    # Check if exists
    if db.query(models.Text).filter(models.Text.filename == filename).first():
        print(f"Text {filename} already exists.")
        return

    # Create Text (Assigning to 1ESO for now)
    text = models.Text(
        title="La Liebre y la Tortuga",
        filename=filename,
        course_level="1ESO",
        content_path="data/texts/1ESO/la_liebre_y_la_tortuga_esp.txt",
        audio_path="la_liebre_y_la_tortuga_esp.mp3"
    )
    db.add(text)
    db.commit()
    db.refresh(text)

    # Create Questions
    questions = [
        {
            "question_content": "¿Por qué se burlaba la liebre de la tortuga?",
            "options": ["Por su caparazón", "Por su lentitud", "Por su tamaño", "Por su color"],
            "correct_answer": 1
        },
        {
            "question_content": "¿Qué hizo la liebre a mitad del camino?",
            "options": ["Comer zanahorias", "Becaer", "Quedarse dormida", "Perderse"],
            "correct_answer": 2
        },
        {
            "question_content": "¿Quién ganó finalmente la carrera?",
            "options": ["La liebre", "El búho", "La tortuga", "El zorro"],
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
    print("Fable added successfully!")
    db.close()

if __name__ == "__main__":
    add_fable()
