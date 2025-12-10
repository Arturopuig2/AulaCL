from app.database import SessionLocal
from app import models

db = SessionLocal()

def list_and_update():
    texts = db.query(models.Text).all()
    print("\n--- TEXTOS DISPONIBLES ---")
    for t in texts:
        print(f"ID: {t.id} | Título: {t.title} | Curso Actual: {t.course_level} | Idioma: {t.language}")
    
    print("\n--- CÓDIGOS DE CURSO VÁLIDOS ---")
    print("Primaria: 1P, 2P, 3P, 4P, 5P, 6P")
    print("ESO: 1ESO, 2ESO, 3ESO, 4ESO")
    print("Bachillerato: 1BAT, 2BAT")
    print("Otros: ALL (Sin curso)")

    text_id = input("\nIntroduce el ID del texto a actualizar (o 'q' para salir): ")
    if text_id.lower() == 'q': return

    new_level = input(f"Introduce el nuevo código de curso para ID {text_id}: ")
    
    text = db.query(models.Text).filter(models.Text.id == text_id).first()
    if text:
        text.course_level = new_level
        db.commit()
        print(f"✅ ¡Actualizado! '{text.title}' ahora es de nivel '{new_level}'")
    else:
        print("❌ ID no encontrado.")

if __name__ == "__main__":
    while True:
        list_and_update()
        cont = input("\n¿Editar otro? (s/n): ")
        if cont.lower() != 's': break
