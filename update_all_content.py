from app.database import SessionLocal
from app import models

db = SessionLocal()

def update_content():
    # 1. Fix Paths for Existing Texts
    # Move from 1ESO to PRIMARIA in DB record
    texts = db.query(models.Text).all()
    for t in texts:
        if "1ESO" in t.content_path:
            t.content_path = t.content_path.replace("1ESO", "PRIMARIA")
            print(f"Updated path for {t.title}: {t.content_path}")
            # Ensure Level is PRIMARIA if desired, or keep 1ESO? 
            # User moved files to PRIMARIA folder, so maybe they want to change level too?
            # Let's assume we update level only if it was 1ESO
            if t.course_level == "1ESO":
                t.course_level = "PRIMARIA"
                print(f"Updated level for {t.title}: PRIMARIA")
    
    db.commit()

    # 2. Add New English Text
    filename = "the_tortoise_and_the_hare_eng.txt"
    if db.query(models.Text).filter(models.Text.filename == filename).first():
        print(f"Text {filename} already exists.")
    else:
        new_text = models.Text(
            title="The Tortoise and the Hare (Eng)",
            filename=filename,
            course_level="PRIMARIA",
            content_path="data/texts/PRIMARIA/the_tortoise_and_the_hare_eng.txt",
            audio_path="the_tortoise_and_the_hare_eng.mp3"
        )
        db.add(new_text)
        db.commit()
        db.refresh(new_text)
        print("Added new text: The Tortoise and the Hare (Eng)")

        # Questions for English Text
        questions = [
             # MC
            {
                "question_content": "Why did the Hare stop running?",
                "options": ["To eat carrots", "To sleep and mock the Tortoise", "To talk to the Fox"],
                "correct_answer": 1
            },
            {
                "question_content": "What did the Hare bet on the race?",
                "options": ["A gold medal", "A sack of carrots", "A fresh lettuce"],
                "correct_answer": 1
            },
            {
                "question_content": "Who started the race?",
                "options": ["The Owl", "The Fox", "The Wolf"],
                "correct_answer": 1
            },
            {
                "question_content": "How did the Tortoise win?",
                "options": ["She took a shortcut", "She ran faster than the Hare", "She kept going slowly but surely"],
                "correct_answer": 2
            },
            {
                "question_content": "What did the Tortoise do with the prize?",
                "options": ["She ate it all alone", "She shared it with other animals", "She saved it for winter"],
                "correct_answer": 1
            },
            # T/F
            {
                "question_content": "The Hare was very humble about his speed.",
                "options": ["True", "False"],
                "correct_answer": 1
            },
            {
                "question_content": "The Tortoise challenged the Hare to a race.",
                "options": ["True", "False"],
                "correct_answer": 0
            },
            {
                "question_content": "The Hare slept under a tree during the race.",
                "options": ["True", "False"],
                "correct_answer": 0
            },
            {
                "question_content": "The animals cheered for the Hare at the finish line.",
                "options": ["True", "False"],
                "correct_answer": 1
            },
            {
                "question_content": "Slow and steady wins the race.",
                "options": ["True", "False"],
                "correct_answer": 0
            }
        ]

        for q in questions:
            db_q = models.Question(
                text_id=new_text.id,
                question_content=q["question_content"],
                options=q["options"],
                correct_answer=q["correct_answer"]
            )
            db.add(db_q)
        
        db.commit()
        print("Added questions for English text.")

    db.close()

if __name__ == "__main__":
    update_content()
