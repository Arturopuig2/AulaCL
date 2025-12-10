from app.database import SessionLocal
from app import models

db = SessionLocal()

def migrate_courses():
    texts = db.query(models.Text).all()
    count = 0
    for t in texts:
        # Default all existing texts to 'ALL' (Sin Curso) as agreed.
        # Unless we want to try to map "PRIMARIA" to something generic? 
        # User said: "mark current texts as 'Sin Curso' (Para todos) por defecto"
        old_level = t.course_level
        t.course_level = "ALL"
        if old_level != "ALL":
            print(f"Updated '{t.title}' from '{old_level}' to 'ALL'")
            count += 1
            
    db.commit()
    print(f"Migration completed. Updated {count} texts.")
    db.close()

if __name__ == "__main__":
    migrate_courses()
