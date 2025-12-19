from app.database import SessionLocal
from app.models import User
import sys
import os

# Ensure we are connecting to the right DB
url = os.environ.get("DATABASE_URL")
if not url:
    print("❌ ERROR: No has configurado la variable DATABASE_URL.")
    print("Debes ejecutar el script así:")
    print('DATABASE_URL="tu_url_externa_de_render" python promote_admin.py')
    sys.exit(1)

if "sqlite" in url:
    print("⚠️  CUIDADO: Estás conectado a la base de datos LOCAL (SQLite).")
    print("Si quieres cambiar el usuario de Render, necesitas la URL externa de Render.")
    confirm = input("¿Continuar de todos modos? (y/n): ")
    if confirm.lower() != 'y':
        sys.exit()
else:
    print("✅ Conectado a base de datos REMOTA (PostgreSQL).")

db = SessionLocal()

def promote_first_user():
    print("Buscando usuarios...")
    # Get the email from the user via input to be sure
    target_email = input("Introduce el CORREO con el que te registraste en Render: ").strip()
    
    user = db.query(User).filter(User.email == target_email).first()
    
    if not user:
        print(f"❌ No se encontró ningún usuario con el correo: {target_email}")
        print("Asegúrate de haberte registrado primero en la web.")
        return

    print(f"Usuario encontrado: ID={user.id}, Username actual='{user.username}'")
    
    if user.username == "admin":
        print("¡Este usuario ya es admin!")
        return

    # Check if 'admin' username is already taken by someone else
    existing_admin = db.query(User).filter(User.username == "admin").first()
    if existing_admin:
        print(f"⚠️  Ya existe un usuario con nombre 'admin' (ID: {existing_admin.id}).")
        print("Cambiando el nombre del antiguo admin a 'admin_old'...")
        existing_admin.username = f"admin_old_{existing_admin.id}"
        db.add(existing_admin)
    
    confirm = input(f"¿Estás seguro de cambiar el username de {target_email} a 'admin'? (y/n): ")
    if confirm.lower() == 'y':
        user.username = "admin"
        db.commit()
        print("\n✅ ¡HECHO! Tu usuario ha sido actualizado.")
        print("Ahora puedes iniciar sesión en la web poniendo:")
        print("   Usuario: admin")
        print("   Contraseña: (tu contraseña de siempre)")
    else:
        print("Operación cancelada.")

if __name__ == "__main__":
    try:
        promote_first_user()
    except Exception as e:
        print(f"\n❌ Error de conexión: {e}")
        print("Verifica que la URL de la base de datos sea correcta.")
