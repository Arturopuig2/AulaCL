
import pytest
import time
import subprocess
import os
import signal
from playwright.sync_api import sync_playwright
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app import models, auth

# Config
TEST_PORT = 8001
BASE_URL = f"http://localhost:{TEST_PORT}"
DB_PATH = "test_e2e.db"
os.environ["DATABASE_URL"] = f"sqlite:///./{DB_PATH}"

@pytest.fixture(scope="module", autouse=True)
def test_server():
    # Clean up old DB
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    # Create DB and Admin
    engine = create_engine(f"sqlite:///./{DB_PATH}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    admin_pass = auth.get_password_hash("admin123")
    admin = models.User(username="admin", hashed_password=admin_pass, is_teacher=True)
    db.add(admin)
    
    # Add a reading
    txt = models.Text(title="Lectura E2E", filename="e2e.txt", course_level="1P", order=5, content_path="/tmp/e2e.txt")
    db.add(txt)
    db.commit()
    db.close()
    
    # Start server
    import sys
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(TEST_PORT), "--host", "127.0.0.1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    
    # Wait for server
    time.sleep(3)
    yield
    
    # Shutdown
    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

def test_admin_order_save_e2e():
    """Prueba E2E: Simula un profesor real cambiando el orden de una lectura."""
    with sync_playwright() as p:
        print("🚀 Launching browser...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            # 1. Login
            print("🔑 Attempting Login...")
            page.goto(f"{BASE_URL}/login")
            page.fill("#username", "admin")
            page.fill("#password", "admin123")
            page.click("button[type='submit']")
            
            # 2. Go to Admin Readings
            print("🏠 Navigating to Admin Home...")
            # Increased timeout to 15s for slow startups
            page.wait_for_url(f"{BASE_URL}/reading/admin", timeout=15000)
            
            print("📚 Navigating to Admin Readings...")
            page.goto(f"{BASE_URL}/reading/admin/readings")
            page.wait_for_selector("table", timeout=15000)
            
            # 3. Modify Order
            print("✏️ Modifying order to 12...")
            # We use locator with data-id if possible, but let's just find the first input
            order_input = page.locator('input[id^="order-"]').first
            order_input.fill("12")
            
            # Click "Guardar"
            save_btn = page.locator("tr", has_text="Lectura E2E").get_by_role("button", name="Guardar")
            save_btn.click()
            
            # Wait for text 
            print("💾 Saving...")
            page.wait_for_function('document.body.innerText.includes("¡Guardado!") || document.body.innerText.includes("Guardando...")', timeout=10000)
            time.sleep(1) 
            
            # 4. Reload and Verify
            print("🔄 Reloading page...")
            page.reload()
            page.wait_for_selector('input[id^="order-"]', timeout=15000)
            final_val = page.locator('input[id^="order-"]').first.input_value()
            
            print(f"✅ Final E2E result: Order is {final_val}")
            assert final_val == "12"
            
        except Exception as e:
            print(f"❌ TEST FAILED: {str(e)}")
            page.screenshot(path="/tmp/e2e_error.png")
            print("📸 Error screenshot saved to /tmp/e2e_error.png")
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    # This allows running directly if needed
    pytest.main([__file__, "-s", "-v"])
