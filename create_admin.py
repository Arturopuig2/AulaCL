from app.database import SessionLocal
from app import models, auth

db = SessionLocal()

def create_admin():
    username = "admin"
    password = "1234"
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        print(f"Creating user {username}...")
        hashed_pw = auth.get_password_hash(password)
        user = models.User(
            username=username,
            hashed_password=hashed_pw,
            course_level="ALL",
            email="admin@aulacl.com"
        )
        db.add(user)
    else:
        print(f"Updating user {username} password...")
        user.hashed_password = auth.get_password_hash(password)
        if not user.email:
             user.email = "admin@aulacl.com"
    
    db.commit()
    print(f"✅ Usuario: {username}")
    print(f"✅ Contraseña: {password}")
    db.close()

if __name__ == "__main__":
    create_admin()
