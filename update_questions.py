from app.database import SessionLocal
from app import models

db = SessionLocal()

def update_questions():
    filename = "la_liebre_y_la_tortuga_esp.txt"
    text = db.query(models.Text).filter(models.Text.filename == filename).first()
    
    if not text:
        print(f"Text {filename} not found.")
        return

    # Delete existing questions for this text
    db.query(models.Question).filter(models.Question.text_id == text.id).delete()
    
    # New Questions
    new_questions = [
        # Multiple Choice
        {
            "question_content": "¿Por qué se burlaba la liebre de la tortuga?",
            "options": ["Por su caparazón", "Por su lentitud", "Por su tamaño"],
            "correct_answer": 1
        },
        {
            "question_content": "¿Qué apostaron en la carrera?",
            "options": ["Una medalla de oro", "Un saco de zanahorias", "Una lechuga fresca"],
            "correct_answer": 1
        },
        {
            "question_content": "¿Quién dio la señal de salida?",
            "options": ["El Búho", "El Zorro", "La Liebre"],
            "correct_answer": 1
        },
        {
            "question_content": "¿Qué hizo la liebre a mitad del camino?",
            "options": ["Comer", "Dormir", "Beber agua"],
            "correct_answer": 1
        },
        {
            "question_content": "¿Quién ganó finalmente la carrera?",
            "options": ["La Liebre", "La Tortuga", "El Zorro"],
            "correct_answer": 1
        },
        # True / False
        {
            "question_content": "La liebre era el animal más lento del bosque.",
            "options": ["Verdadero", "Falso"],
            "correct_answer": 1
        },
        {
            "question_content": "La tortuga retó a la liebre a una carrera.",
            "options": ["Verdadero", "Falso"],
            "correct_answer": 0
        },
        {
            "question_content": "La liebre se durmió debajo de una roca.",
            "options": ["Verdadero", "Falso"],
            "correct_answer": 1
        },
        {
            "question_content": "Todos los animales aplaudieron a la tortuga al llegar.",
            "options": ["Verdadero", "Falso"],
            "correct_answer": 0
        },
        {
            "question_content": "La liebre compartió las zanahorias con la tortuga al final.",
            "options": ["Verdadero", "Falso"],
            "correct_answer": 1
        }
    ]

    for q in new_questions:
        db_q = models.Question(
            text_id=text.id,
            question_content=q["question_content"],
            options=q["options"],
            correct_answer=q["correct_answer"]
        )
        db.add(db_q)
    
    db.commit()
    print("Questions updated successfully!")
    db.close()

if __name__ == "__main__":
    update_questions()
