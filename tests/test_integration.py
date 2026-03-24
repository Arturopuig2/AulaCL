
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app import models, auth

# 1. SETUP TEST DATABASE (In-Memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite://" # In-memory
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency override
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Create Admin User
    admin_pass = auth.get_password_hash("admin123")
    admin = models.User(username="admin", hashed_password=admin_pass, is_teacher=True)
    db.add(admin)
    
    # Create Student User
    student_pass = auth.get_password_hash("student123")
    student = models.User(username="estudiante", hashed_password=student_pass, is_teacher=False)
    db.add(student)
    
    # Create some texts with specific order
    t1 = models.Text(title="Lectura B (Orden 2)", filename="b.txt", course_level="1P", order=2, content_path="/tmp/b.txt")
    t2 = models.Text(title="Lectura A (Orden 1)", filename="a.txt", course_level="1P", order=1, content_path="/tmp/a.txt")
    t3 = models.Text(title="Lectura C (Sin orden/0)", filename="c.txt", course_level="1P", order=0, content_path="/tmp/c.txt")
    
    db.add_all([t1, t2, t3])
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)

_tokens = {}

def get_token(username, password):
    if username in _tokens:
        return _tokens[username]
    response = client.post("/auth/token", data={"username": username, "password": password})
    if response.status_code != 200:
        raise Exception(f"Login failed for {username}: {response.text}")
    token = response.json()["access_token"]
    _tokens[username] = token
    return token

# --- TESTS ---

def test_login_success():
    """Confirma que el login funciona y devuelve un token."""
    response = client.post("/auth/token", data={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_admin_sorting():
    """Confirma que la lista de administración respeta el orden (0, 1, 2)."""
    token = get_token("admin", "admin123")
    # Endpoint /reading/admin/texts (default order_asc)
    response = client.get("/reading/admin/texts?sort_by=order_asc", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    
    # Should be: C (0), A (1), B (2)
    titles = [t["title"] for t in data]
    assert titles[0] == "Lectura C (Sin orden/0)"
    assert titles[1] == "Lectura A (Orden 1)"
    assert titles[2] == "Lectura B (Orden 2)"

def test_student_unauthorized_admin():
    """Seguridad: Un estudiante NO debe poder entrar al panel de administración."""
    token = get_token("estudiante", "student123")
    response = client.get("/reading/admin/texts", headers={"Authorization": f"Bearer {token}"})
    # Should be 403 (Not authorized in router)
    assert response.status_code == 403

def test_update_order_persists():
    """Lógica: Guardar un nuevo número de orden debe persistir en la DB."""
    token = get_token("admin", "admin123")
    
    # 1. Update text ID 3 (was order 0) to order 50
    update_response = client.put("/reading/admin/texts/3", 
                               json={"order": 50}, 
                               headers={"Authorization": f"Bearer {token}"})
    assert update_response.status_code == 200
    assert update_response.json()["order"] == 50
    
    # 2. Check list again - ID 3 should now be LAST
    list_response = client.get("/reading/admin/texts?sort_by=order_asc", headers={"Authorization": f"Bearer {token}"})
    data = list_response.json()
    assert data[-1]["id"] == 3
    assert data[-1]["order"] == 50

def test_student_view_is_sorted():
    """UI Estudiante: La lista principal para el alumno debe estar ya ordenada."""
    token = get_token("estudiante", "student123")
    response = client.get("/reading/texts", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    
    # We had A(1), B(2) and we moved C to (50)
    # Order should be A(1), B(2), C(50)
    titles = [t["title"] for t in data]
    assert titles[0] == "Lectura A (Orden 1)"
    assert titles[1] == "Lectura B (Orden 2)"

def test_no_token_unauthorized():
    """Seguridad: Sin token no se puede acceder a nada privado."""
    # Intentar acceder al listado de lecturas sin cabecera Authorization
    response = client.get("/reading/texts")
    assert response.status_code == 401

def test_delete_reading_access():
    """Seguridad: Solo el admin puede borrar lecturas."""
    # 1. Alumno intenta borrar (ID 1)
    student_token = get_token("estudiante", "student123")
    del_response = client.delete("/reading/admin/texts/1", headers={"Authorization": f"Bearer {student_token}"})
    assert del_response.status_code == 403 # Forbidden
    
    # 2. Admin borra (ID 1)
    admin_token = get_token("admin", "admin123")
    del_response = client.delete("/reading/admin/texts/1", headers={"Authorization": f"Bearer {admin_token}"})
    assert del_response.status_code == 200
    
    # 3. Verificar que ya no existe
    check_response = client.get("/reading/texts", headers={"Authorization": f"Bearer {admin_token}"})
    ids = [t["id"] for t in check_response.json()]
    assert 1 not in ids

def test_teacher_status_check():
    """Seguridad: El campo is_teacher de 'estudiante' debe ser False."""
    token = get_token("estudiante", "student123")
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["is_teacher"] is False

