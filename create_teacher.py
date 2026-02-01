from app.database import SessionLocal
from app import models
from app.auth import get_password_hash

def create_teacher():
    db = SessionLocal()
    # Check if user already exists
    if db.query(models.User).filter(models.User.username == "profesor").first():
        print("User 'profesor' already exists.")
        db.close()
        return

    teacher = models.User(
        username="profesor",
        email="profesor@example.com",
        hashed_password=get_password_hash("Profesor1234!"),
        course_level="ALL",
        name="Profesor de Prueba",
        is_teacher=True
    )
    db.add(teacher)
    db.commit()
    print("User 'profesor' created successfully!")
    db.close()

if __name__ == "__main__":
    create_teacher()
