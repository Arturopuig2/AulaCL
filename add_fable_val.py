from app.database import SessionLocal
from app import models

db = SessionLocal()

def add_fable_val():
    filename = "la_llebre_i_la_tortuga_val.txt"
    # Check if exists
    if db.query(models.Text).filter(models.Text.filename == filename).first():
        print(f"Text {filename} already exists.")
        return

    # Create Text (Assigning to 1ESO)
    text = models.Text(
        title="La Llebre i la Tortuga (Val)",
        filename=filename,
        course_level="1ESO",
        content_path="data/texts/1ESO/la_llebre_i_la_tortuga_val.txt",
        audio_path="la_llebre_i_la_tortuga_val.mp3"
    )
    db.add(text)
    db.commit()
    db.refresh(text)

    # Create Questions (Translated to Valencian)
    questions = [
        # Multiple Choice
        {
            "question_content": "Per què es burlava la llebre de la tortuga?",
            "options": ["Per la seua closca", "Per la seua lentitud", "Per la seua grandària"],
            "correct_answer": 1
        },
        {
            "question_content": "Què van apostar a la carrera?",
            "options": ["Una medalla d'or", "Un sac de safanòries", "Una lletuga fresca"],
            "correct_answer": 1
        },
        {
            "question_content": "Qui va donar el senyal d'eixida?",
            "options": ["El Mussol", "La Guineu", "La Llebre"],
            "correct_answer": 1
        },
        {
            "question_content": "Què va fer la llebre a meitat del camí?",
            "options": ["Menjar", "Dormir", "Beure aigua"],
            "correct_answer": 1
        },
        {
            "question_content": "Qui va guanyar finalment la carrera?",
            "options": ["La Llebre", "La Tortuga", "La Guineu"],
            "correct_answer": 1
        },
        # True / False
        {
            "question_content": "La llebre era l'animal més lent del bosc.",
            "options": ["Veritat", "Fals"],
            "correct_answer": 1
        },
        {
            "question_content": "La tortuga va reptar a la llebre a una carrera.",
            "options": ["Veritat", "Fals"],
            "correct_answer": 0
        },
        {
            "question_content": "La llebre es va adormir sota una roca.",
            "options": ["Veritat", "Fals"],
            "correct_answer": 1
        },
        {
            "question_content": "Tots els animals van aplaudir a la tortuga en arribar.",
            "options": ["Veritat", "Fals"],
            "correct_answer": 0
        },
        {
            "question_content": "La llebre va compartir les safanòries amb la tortuga al final.",
            "options": ["Veritat", "Fals"],
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
    print("Valencian fable added successfully!")
    db.close()

if __name__ == "__main__":
    add_fable_val()
