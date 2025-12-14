from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .database import engine, Base
from .routers import auth, reading, subusers

# Create Database Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Aula CL")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/texts", StaticFiles(directory="data/texts"), name="texts_files") # Serve text files
app.mount("/audio", StaticFiles(directory="static/audio"), name="audio_files") # Serve audio

# Include Routers
app.include_router(auth.router)
app.include_router(reading.router)
app.include_router(subusers.router)
templates = Jinja2Templates(directory="templates")

from fastapi import Request
from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/login-code", response_class=HTMLResponse)
def login_code_page(request: Request):
    return templates.TemplateResponse("login_code.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/reading-room/{text_id}", response_class=HTMLResponse)
def reading_page(request: Request, text_id: int):
    return templates.TemplateResponse("reading.html", {"request": request, "text_id": text_id})

@app.get("/quiz/{text_id}", response_class=HTMLResponse)
def quiz_page(request: Request, text_id: int):
    return templates.TemplateResponse("quiz.html", {"request": request, "text_id": text_id})

@app.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@app.get("/reset-password", response_class=HTMLResponse)
def reset_password_page(request: Request):
    return templates.TemplateResponse("reset_password.html", {"request": request})

@app.get("/my-subusers", response_class=HTMLResponse)
def subusers_page(request: Request):
    return templates.TemplateResponse("subusers.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

