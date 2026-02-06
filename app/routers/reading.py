from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Request
from fastapi.responses import StreamingResponse, HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
from app import schemas, auth, models, database, config

def robust_decode(raw_bytes: bytes) -> str:
    """
    Attempts to decode bytes using different encodings common in Spanish text files.
    Priority: UTF-8-SIG (handles BOM), CP1252 (Windows), Latin-1.
    """
    for encoding in ["utf-8-sig", "cp1252", "latin-1"]:
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    # Fallback to utf-8 with ignore if everything fails
    return raw_bytes.decode("utf-8", errors="ignore")

router = APIRouter(
    prefix="/reading",
    tags=["reading"]
)

from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")

@router.get("/admin/sync", response_class=HTMLResponse)
def get_sync_tool(request: Request, user: models.User = Depends(auth.get_current_user_html)):
    if not user or user.username != 'admin':
        return RedirectResponse(url="/login", status_code=302)
    # We allow access to the HTML shell; JS handles the token check/redirect
    return templates.TemplateResponse("admin_sync.html", {"request": request})

@router.get("/admin", response_class=HTMLResponse)
def get_admin_hub(request: Request, user: models.User = Depends(auth.get_current_user_html)):
    if not user or user.username != 'admin':
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("admin.html", {"request": request})

@router.get("/admin/upload", response_class=HTMLResponse)
def get_admin_upload(request: Request, user: models.User = Depends(auth.get_current_user_html)):
    if not user or user.username != 'admin':
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("admin_upload.html", {"request": request})

@router.get("/admin/codes", response_class=HTMLResponse)
def get_admin_codes(request: Request, user: models.User = Depends(auth.get_current_user_html)):
    if not user or user.username != 'admin':
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("admin_codes.html", {"request": request})

@router.get("/admin/readings", response_class=HTMLResponse)
def get_admin_readings(request: Request, user: models.User = Depends(auth.get_current_user_html)):
    if not user or user.username != 'admin':
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("admin_readings.html", {"request": request})

@router.get("/admin/edit/{text_id}", response_class=HTMLResponse)
def get_admin_edit_reading(request: Request, text_id: int, user: models.User = Depends(auth.get_current_user_html)):
    if not user or user.username != 'admin':
        return RedirectResponse(url="/login", status_code=302)
    # Just serve the template, JS handles data loading
    return templates.TemplateResponse("admin_edit_reading.html", {"request": request})

@router.get("/texts", response_model=List[schemas.TextResponse])
def get_texts(current_user=Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    # Return all texts so frontend can filter by course
    is_admin = False
    is_subuser = False
    
    # Determine user type
    username = getattr(current_user, "username", None)
    if username == "admin":
        is_admin = True
    
    if not hasattr(current_user, "username"): # SubUsers don't have username
        is_subuser = True
        
    texts = db.query(models.Text).filter(models.Text.is_active == True).all()

    # Query attempts based on user type
    if is_subuser:
        user_attempts = db.query(models.ReadingAttempt).filter(models.ReadingAttempt.subuser_id == current_user.id).all()
    else:
        user_attempts = db.query(models.ReadingAttempt).filter(models.ReadingAttempt.user_id == current_user.id).all()
        
    attempts_map = {a.text_id: a.score for a in user_attempts}
    
    # Check Premium Status (Students have their own access_expires_at)
    is_premium = False
    if (current_user.access_expires_at and current_user.access_expires_at > datetime.utcnow()) or is_admin:
        is_premium = True
        
    # First reading per course level is free
    course_min_ids = {}
    for t in texts:
        level = t.course_level or "ALL"
        if level not in course_min_ids or t.id < course_min_ids[level]:
            course_min_ids[level] = t.id
    
    free_ids = set(course_min_ids.values())
    
    response = []
    for t in texts:
        t_resp = schemas.TextResponse.model_validate(t)
        t_resp.is_completed = t.id in attempts_map
        t_resp.score = attempts_map.get(t.id)
        
        # Lock Logic
        if is_premium:
            t_resp.is_locked = False
        else:
            if t.id in free_ids: # First per course is free
                t_resp.is_locked = False
            else:
                t_resp.is_locked = True
                
        response.append(t_resp)
        
    return response

@router.get("/texts/{text_id}", response_model=schemas.TextResponse)
def get_text(text_id: int, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    text = db.query(models.Text).filter(models.Text.id == text_id).first()
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")
    
    # Enforcement Check
    is_premium = False
    is_admin = getattr(current_user, "username", None) == "admin"
    if (current_user.access_expires_at and current_user.access_expires_at > datetime.utcnow()) or is_admin:
        is_premium = True
        
    # First reading of its course level is free
    first_in_course = db.query(models.Text).filter(
        models.Text.course_level == text.course_level,
        models.Text.is_active == True
    ).order_by(models.Text.id.asc()).first()
    
    is_free = (first_in_course and text.id == first_in_course.id)
    
    if not is_premium and not is_free:
        raise HTTPException(status_code=403, detail="Contenido bloqueado. Introduce un código para desbloquear.")

    # Read content from file
    try:
        with open(text.content_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        import os
        cwd = os.getcwd()
        content = f"Error loading text content. Path: '{text.content_path}'. CWD: '{cwd}'. Error: {str(e)}"

    # Create a response object including the content
    # We need to manually construct the dict or object because we are enhancing the DB model
    response = schemas.TextResponse.model_validate(text)
    response.content = content
    return response

@router.get("/texts/{text_id}/questions", response_model=List[schemas.QuestionResponse])
def get_questions(text_id: int, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    questions = db.query(models.Question).filter(models.Question.text_id == text_id).all()
    if not questions:
        raise HTTPException(status_code=404, detail="Questions not found for this text")
    return questions

@router.post("/attempt", response_model=schemas.AttemptResponse)
def submit_attempt(attempt: schemas.AttemptCreate, current_user = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    is_subuser = not hasattr(current_user, "username")
    
    # UPSERT LOGIC: Check if attempt exists
    existing_attempt = db.query(models.ReadingAttempt).filter(
        models.ReadingAttempt.text_id == attempt.text_id,
        models.ReadingAttempt.user_id == (current_user.id if not is_subuser else None),
        models.ReadingAttempt.subuser_id == (current_user.id if is_subuser else None)
    ).first()

    if existing_attempt:
        # Update existing
        existing_attempt.score = attempt.score
        existing_attempt.time_spent_seconds = attempt.time_spent_seconds
        existing_attempt.details = attempt.details
        existing_attempt.timestamp = datetime.utcnow()
        db_attempt = existing_attempt
    else:
        # Create new
        db_attempt = models.ReadingAttempt(
            user_id=current_user.id if not is_subuser else None,
            subuser_id=current_user.id if is_subuser else None,
            text_id=attempt.text_id,
            time_spent_seconds=attempt.time_spent_seconds,
            score=attempt.score,
            details=attempt.details
        )
        db.add(db_attempt)
    
    db.commit()
    db.refresh(db_attempt)
    return db_attempt



@router.get("/admin/texts", response_model=List[schemas.TextResponse])
def get_all_texts_admin(current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(models.Text).all()

@router.put("/admin/texts/{text_id}", response_model=schemas.TextResponse)
def update_text(text_id: int, text_update: schemas.TextUpdate, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    text = db.query(models.Text).filter(models.Text.id == text_id).first()
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")
        
    if text_update.course_level is not None:
        text.course_level = text_update.course_level
    if text_update.language is not None:
        text.language = text_update.language
        
    db.commit()
    db.refresh(text)
    return text

@router.put("/admin/texts/{text_id}/full", response_model=schemas.TextResponse)
def update_text_full(text_id: int, request: schemas.MagicSaveRequest, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    text = db.query(models.Text).filter(models.Text.id == text_id).first()
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")
        
    # 1. Update Metadata
    text.title = request.title
    text.course_level = request.course_level
    text.language = request.language
    if request.audio_path:
        # If it doesn't have leading 'audio/' or '/static/audio/', normalize it safely if needed.
        # But usually coming from upload-audio it returns 'audio/filename.mp3'
        text.audio_path = request.audio_path
    if request.image_path:
        text.image_path = request.image_path
        
    # 2. Update File Content
    try:
        # Check if dir changed (e.g. course changed), move file?
        # For simplicity, we keep same path or just write to existing path if course logic isn't strict on folder structure
        # User might want organization though. Let's stick to simple overwrite for now unless we want to implement move.
        # IF we change course, we might want to move it, but complicates things. Let's just overwrite defined path.
        
        with open(text.content_path, "w", encoding="utf-8") as f:
            f.write(request.content)
            
    except Exception as e:
        print(f"Error updating file content: {e}")
        raise HTTPException(status_code=500, detail="Error updating text file on disk")

    # 3. Update Questions (Full Replace)
    # Delete old
    db.query(models.Question).filter(models.Question.text_id == text_id).delete()
    
    # Add new
    for q in request.questions:
        db_q = models.Question(
            text_id=text.id,
            question_content=q.question,
            options=q.options,
            correct_answer=q.correct_index,
            category=q.category or "LITERAL"
        )
        db.add(db_q)
        
    db.commit()
    db.refresh(text)
    return text

@router.post("/admin/upload-audio")
def upload_audio(
    file: UploadFile = File(...),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    import shutil
    import uuid

    # 1. Setup Directory
    save_dir = config.AUDIO_DIR
    os.makedirs(save_dir, exist_ok=True)
    
    # 2. Save File
    try:
        # Generate unique name to avoid conflicts
        ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_path = f"{save_dir}/{unique_filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        print(f"Error saving uploaded audio: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving audio: {str(e)}")
        
    return {"path": f"/audio/{unique_filename}"}

@router.post("/admin/upload", response_model=schemas.TextResponse)
def upload_text(
    title: str = Form(...),
    course_level: str = Form("ALL"),
    language: str = Form("es"),
    text_file: UploadFile = File(...),
    audio_file: Optional[UploadFile] = File(None),
    current_user: schemas.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    import shutil
    import os
    
    # 1. Save Text File
    # Ensure directory exists
    save_dir = os.path.join(config.TEXTS_DIR, course_level)
    os.makedirs(save_dir, exist_ok=True)
    
    filename = text_file.filename
    content_path = f"{save_dir}/{filename}"
    
    with open(content_path, "wb") as buffer:
        shutil.copyfileobj(text_file.file, buffer)
        
    # FORCE UTF-8 NORMALIZATION
    # Attempts to read with multiple encodings and save as pure UTF-8
    try:
        with open(content_path, "rb") as f:
            raw_bytes = f.read()
        
        content_str = robust_decode(raw_bytes)
            
        # Rewrite as pure UTF-8
        with open(content_path, "w", encoding="utf-8") as f:
            f.write(content_str)
            
    except Exception as e:
        print(f"Error normalizing text encoding: {e}")
        # Proceeding, might fail later but we tried.
        
    # 2. Save Audio File (if present)
    audio_path = None
    if audio_file:
        audio_filename = audio_file.filename
        audio_save_dir = config.AUDIO_DIR
        os.makedirs(audio_save_dir, exist_ok=True)
        audio_path_full = f"{audio_save_dir}/{audio_filename}"
        
        with open(audio_path_full, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        
        # Store relative path for DB with leading slash for mount point consistency
        audio_path = f"/audio/{audio_filename}"

    # 3. Create DB Entry
    new_text = models.Text(
        title=title,
        filename=filename,
        course_level=course_level,
        language=language,
        content_path=content_path,
        audio_path=audio_path
    )
    
    try:
        db.add(new_text)
        db.commit()
        db.refresh(new_text)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error saving to DB (Title/Filename might be duplicate): {str(e)}")
        
    # 4. Parse & Save Questions
    # Read content to parse questions
    try:
        with open(content_path, "r", encoding="utf-8") as f:
            full_content = f.read()
            
        # Split Content vs Questions
        # Look for typical separators
        import re
        separator_pattern = r"(--- Preguntas ---|Preguntas:|--- PREGUNTAS ---|PREGUNTAS:)"
        parts = re.split(separator_pattern, full_content)
        
        main_text = parts[0].strip()
        questions_text = ""
        if len(parts) > 1:
            # Reconstruct the rest (in case multiple separators, take all after first)
            questions_text = "".join(parts[2:]).strip()
            
            # Update the file to ONLY contain the text (hide questions from reading view)
            with open(content_path, "w", encoding="utf-8") as f:
                f.write(main_text)
                
            # Parse Questions Logic
            # Expected format:
            # 1. Question text?
            # a) Option 1
            # b) Option 2 ...
            # * Solution (optional logic, but for now let's assume first is correct or randomized? 
            # Actually, let's assume standard format and try to detect 'CORRECT' or just take index.
            # SIMPLE PARSER:
            lines = questions_text.split('\n')
            current_q = None
            current_options = []
            current_correct = 0 # Default to 0 (a)
            
            for line in lines:
                line = line.strip()
                if not line: continue
                
                # Detect Question (starts with digit + dot/paren)
                if re.match(r"^\d+[\.\)]", line):
                    # Save previous if exists
                    if current_q:
                        db_q = models.Question(
                            text_id=new_text.id,
                            question_content=current_q,
                            options=current_options,
                            correct_answer=current_correct
                        )
                        db.add(db_q)
                    
                    # Start new
                    current_q = re.sub(r"^\d+[\.\)]\s*", "", line)
                    current_options = []
                    current_correct = 0
                    
                # Detect Option (starts with a) b) or - )
                elif re.match(r"^[a-z][\.\)]", line) or line.startswith("-"):
                    opt_text = re.sub(r"^[a-z][\.\)]\s*|-\s*", "", line)
                    
                    # Check if marked as correct (e.g. ends with *)
                    if "*" in line:
                        current_correct = len(current_options)
                        opt_text = opt_text.replace("*", "").strip()
                        
                    current_options.append(opt_text)
            
            # Save last one
            if current_q:
                db_q = models.Question(
                    text_id=new_text.id,
                    question_content=current_q,
                    options=current_options,
                    correct_answer=current_correct
                )
                db.add(db_q)
                
            db.commit()

    except Exception as e:
        print(f"Error parsing questions: {e}")
        # Non-blocking, text is saved anyway
        pass
        
    
    # 5. IF NO MANUAL QUESTIONS -> AI GENERATION
    # Check if questions were added manually
    existing_questions = db.query(models.Question).filter(models.Question.text_id == new_text.id).count()
    
    if existing_questions == 0:
        print("No manual questions found. Triggering AI Generation...")
        try:
            import openai
            import os
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv("OPENAI_API_KEY")
            client = openai.OpenAI(api_key=api_key)
            
            # Load context if exists (shared logic)
            context_instruction = ""
            try:
                if os.path.exists("data/magic_context.txt"):
                    with open("data/magic_context.txt", "r", encoding="utf-8") as f:
                        c = f.read().strip()
                        if c: context_instruction = f"\n    CONTEXTO ADICIONAL: {c}\n"
            except: pass

            questions_data = generate_lomloe_questions_logic(main_text, client, context_instruction)
            
            for q in questions_data:
                db_q = models.Question(
                    text_id=new_text.id,
                    question_content=q["question"],
                    options=q["options"],
                    correct_answer=q["correct_index"],
                    category=q.get("category", "LITERAL")
                )
                db.add(db_q)
            db.commit()
            
            print("AI Generation Success (LOMLOE)")
        except Exception as e:
            print(f"AI Generation Failed: {e}")
            # Don't fail the upload, but log it
            pass
        
    return new_text



@router.patch("/admin/texts/{text_id}/toggle", response_model=schemas.TextResponse)
def toggle_text_active(text_id: int, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    text = db.query(models.Text).filter(models.Text.id == text_id).first()
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")
        
    text.is_active = not text.is_active
    db.commit()
    db.refresh(text)
    return text

@router.post("/admin/upload/analyze")
def analyze_upload_text(
    title: str = Form(...),
    course_level: str = Form("ALL"),
    language: str = Form("es"),
    text_file: UploadFile = File(...),
    audio_file: Optional[UploadFile] = File(None),
    image_file: Optional[UploadFile] = File(None),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    import shutil
    import os
    import openai
    from dotenv import load_dotenv
    import uuid
    
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    client = openai.OpenAI(api_key=api_key)

    # 1. Process Text File
    content = ""
    try:
        raw_bytes = text_file.file.read()
        content = robust_decode(raw_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

    # 2. Process Audio File (Save Temporarily/Permanently)
    audio_path = None
    if audio_file:
        audio_filename = audio_file.filename
        audio_save_dir = config.AUDIO_DIR
        os.makedirs(audio_save_dir, exist_ok=True)
        audio_path_full = f"{audio_save_dir}/{audio_filename}"
        
        with open(audio_path_full, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        
        audio_path = f"/audio/{audio_filename}"

    # 2b. Process Image File
    image_path = None
    if image_file:
        try:
            # Save to static/images/uploads (same logic as upload_image endpoint)
            save_dir = config.IMAGES_DIR
            os.makedirs(save_dir, exist_ok=True)
            
            ext = os.path.splitext(image_file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{ext}"
            image_path_full = f"{save_dir}/{unique_filename}"
            
            with open(image_path_full, "wb") as buffer:
                shutil.copyfileobj(image_file.file, buffer)
                
            image_path = f"/static/images/uploads/{unique_filename}" # Web path
        except Exception as e:
            print(f"ERROR SAVING IMAGE: {e}")
            raise HTTPException(status_code=500, detail=f"Error saving image: {str(e)}")

    # 3. Generate Questions using Helper
    try:
        # Context loading
        context_instruction = ""
        if os.path.exists("data/magic_context.txt"):
            with open("data/magic_context.txt", "r", encoding="utf-8") as f:
                c = f.read().strip()
                if c: context_instruction = f"\n    CONTEXTO ADICIONAL: {c}\n"

        prompt = f"""
        Analiza el siguiente texto y genera:
        1. 3 preguntas de tipo LITERAL con 4 opciones.
        2. 3 preguntas de tipo INFERENTIAL con 4 opciones.
        3. 3 preguntas de tipo VOCABULARY con 4 opciones.
        
        TEXTO:
        {content[:3000]}
        
        {context_instruction}
        
        FORMATO JSON:
        [
          {{
            "question": "...",
            "options": ["A", "B", "C", "D"],
            "correct_answer": 0,
            "category": "LITERAL"
          }}
        ]
        """
        
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un experto creador de cuestionarios educativos. Devuelve SOLO JSON válido."},
                {"role": "user", "content": prompt}
            ]
        )
        
        response_content = completion.choices[0].message.content.strip()
        # Clean markdown code blocks if present
        if response_content.startswith("```json"):
            response_content = response_content.split("```json")[1].split("```")[0].strip()
        elif response_content.startswith("```"):
            response_content = response_content.split("```")[1].split("```")[0].strip()

        import json
        questions = json.loads(response_content)

    except Exception as e:
        print(f"ERROR OPENAI/PARSING: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing text (OpenAI): {str(e)}")

    return {
        "title": title,
        "content": content,
        "course_level": course_level,
        "language": language,
        "audio_path": audio_path,
        "image_path": image_path,
        "questions": questions
    }

@router.get("/texts/{text_id}/pdf")
def generate_text_pdf(text_id: int, font_style: str = "imprenta", font_size: str = "L", current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    # 1. Fetch Data & Check Access
    text = db.query(models.Text).filter(models.Text.id == text_id).first()
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")
        
    # Check Premium/Free (Reuse logic or simplify)
    is_premium = False
    if (current_user.access_expires_at and current_user.access_expires_at > datetime.utcnow()) or current_user.username == "admin":
        is_premium = True
        
    # First reading in its course level is free
    first_in_course = db.query(models.Text).filter(
        models.Text.course_level == text.course_level,
        models.Text.is_active == True
    ).order_by(models.Text.id.asc()).first()
    
    is_free = (first_in_course and text.id == first_in_course.id)
    
    if not is_premium and not is_free:
        raise HTTPException(status_code=403, detail="Contenido bloqueado.")

    # Get Content
    content = ""
    try:
        with open(text.content_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        content = "Error loading content."

    # Get Questions
    questions = db.query(models.Question).filter(models.Question.text_id == text_id).all()

    # Uppercase Logic
    is_uppercase = (font_style == "mayuscula")
    if is_uppercase:
        content = content.upper()
        # Note: Questions and Options need to be uppercased during iteration
        font_style = "imprenta" # Reset to standard font for rendering

    # 2. Generate PDF
    from fpdf import FPDF
    import io
    from fastapi.responses import StreamingResponse

    class PDF(FPDF):
        def header(self):
            # Header always standard
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'Aula de Comprensión Lectora', 0, 1, 'C')
            self.ln(5)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    pdf = PDF()
    
    # Calculate Base Sizes & Offsets
    # Base (for "L" size - as requested "current")
    # Title: 24 (was 20)
    # Text (Imp): 18 (was 16), Text (Lig): 20 (was 18)
    # Questions: 18 (was 16)
    # Options: 17 (was 15)
    
    # Map input size to offset
    size_offsets = {
        "S": -4,
        "M": -2,
        "L": 0,
        "XL": 6 
    }
    offset = size_offsets.get(font_size, 0)
    
    # Font Setup
    main_font = "Arial"
    base_text_size = 18 # Increased from 16
    
    if font_style == "ligada":
        try:
            # Register Custom Font
            pdf.add_font("AulaCNova", style="", fname="static/fonts/AulaCNova.ttf")
            main_font = "AulaCNova"
            base_text_size = 20 # Increased from 18
        except Exception as e:
            print(f"Font loading error: {e}")
            main_font = "Arial"

    # Apply Offset
    s_title = 24 + offset # Increased base from 20
    s_text = base_text_size + offset
    s_quest = 18 + offset # Increased base from 16
    s_opt = 17 + offset # Increased base from 15
    s_sol = 20 + offset # Increased base from 18

    pdf.add_page()
    
    # helper for safe text
    def safe_text(txt):
        if is_uppercase:
            txt = txt.upper()
            
        if main_font == "Arial":
            # Replace common incompatible characters
            replacements = {
                "–": "-", "—": "-", "“": '"', "”": '"', "‘": "'", "’": "'", "…": "..."
            }
            for k, v in replacements.items():
                txt = txt.replace(k, v)
                
            return txt.encode('latin-1', 'replace').decode('latin-1')
        else:
            # Custom fonts in fpdf2 usually handle utf-8 better, but let's be safe
            # Actually fpdf2 handles utf-8 natively with TTF fonts
            return txt

    # Title
    pdf.set_font("Arial", "B", s_title) # Increased from 18
    pdf.multi_cell(0, 10, safe_text(text.title), align='C')
    pdf.ln(10)

    # Illustration
    if text.image_path:
        # Check relative or absolute
        import os
        img_path = text.image_path
        # If it starts with /, it might be relative to web root, but for file system it might be relative to cwd
        # Our app runs from root, so if path is "static/...", it works.
        # If path is "/static/...", we need to strip leading slash
        if img_path.startswith("/"):
            img_path = img_path[1:]
            
        if os.path.exists(img_path):
            try:
                # Center image. Page width ~210mm.
                # Let's target width 100mm.
                # x = (210 - 100) / 2 = 55
                pdf.image(img_path, x=55, w=100)
                pdf.ln(10)
            except Exception as e:
                print(f"Error adding PDF image: {e}")

    # Text Content
    pdf.set_font(main_font, "", s_text)
    # Adjust line height based on size (approx size * 0.5)
    lh_text = s_text * 0.5 
    if lh_text < 6: lh_text = 6
    
    pdf.multi_cell(0, lh_text, safe_text(content)) # Increased line height for text
    pdf.ln(10)

    # Questions
    if questions:
        pdf.add_page()
        pdf.set_font("Arial", "B", s_quest) # Increased from 14
        pdf.cell(0, 10, safe_text("Preguntas de Comprensión"), 0, 1)
        pdf.ln(5)

        pdf.set_font("Arial", "", s_quest) # Increased from 14
        
        # Helper to calculate height
        def get_text_height(txt, w_available, font_family, font_style, font_size, line_height):
            pdf.set_font(font_family, font_style, font_size)
            # fpdf2 multi_cell with split_only=True returns list of lines
            # If split_only not supported in some context, fallback to simpler estimation
            try:
                # split_only=True returns the lines that would be printed
                lines = pdf.multi_cell(w_available, line_height, txt, split_only=True)
                return len(lines) * line_height
            except:
                # Fallback: approximation
                string_w = pdf.get_string_width(txt)
                lines = int(string_w / w_available) + 1
                return lines * line_height

        for i, q in enumerate(questions):
            # 1. Calculate Block Height
            block_height = 0
            
            # Question
            q_str = q.question_content
            if is_uppercase: q_str = q_str.upper()
            
            q_text = f"{i+1}. {safe_text(q_str)}"
            q_w = pdf.w - pdf.l_margin - pdf.r_margin
            
            lh_q = s_quest * 0.5
            if lh_q < 7: lh_q = 7
            
            block_height += get_text_height(q_text, q_w, "Arial", "B", s_quest, lh_q) # Using new size 16, line height 8
            
            # Options
            options = q.options if isinstance(q.options, list) else []
            opt_w = pdf.w - pdf.l_margin - pdf.r_margin - 10
            lh_opt = s_opt * 0.5
            if lh_opt < 6: lh_opt = 6
            
            char_code = 97
            
            for opt in options:
                opt_str = opt if not is_uppercase else opt.upper()
                opt_text = f"{chr(char_code)}) {safe_text(opt_str)}"
                block_height += get_text_height(opt_text, opt_w, "Arial", "", s_opt, lh_opt) # Using new size 15, line height 8
                char_code += 1
            
            block_height += 5 # Bottom padding
            
            # 2. Check Space
            # page_break_trigger is the Y position where auto-break happens
            space_left = pdf.page_break_trigger - pdf.get_y()
            if block_height > space_left:
                pdf.add_page()

            # 3. Render
            pdf.set_font("Arial", "B", s_quest) # Increased from 14
            pdf.multi_cell(0, lh_q, q_text) 
            
            pdf.set_font("Arial", "", s_opt) # Increased from 13
            char_code = 97
            for opt in options:
                pdf.set_x(pdf.l_margin + 10) 
                available_w = pdf.w - pdf.l_margin - pdf.r_margin - 10
                
                opt_str = opt if not is_uppercase else opt.upper()
                pdf.multi_cell(available_w, lh_opt, f"{chr(char_code)}) {safe_text(opt_str)}") # Increased line height
                char_code += 1
            pdf.ln(5)

    # Solutions Section
    if questions:
        pdf.add_page() # Start solutions on new page for privacy/teacher use
        
        # AulaCNova only has regular style registered. Avoid "B" if custom font.
        sol_style = "B" if main_font == "Arial" else ""
        pdf.set_font(main_font, sol_style, s_sol)
        
        pdf.cell(0, 10, safe_text("SOLUCIONES:"), 0, 1)
        pdf.ln(5)
        
        pdf.set_font(main_font, "", s_text) # Use text size for solutions
        for i, q in enumerate(questions):
            # Resolve correct answer
            opts = q.options if isinstance(q.options, list) else []
            idx = q.correct_answer
            
            answer_text = "N/A"
            letter = "?"
            
            if isinstance(idx, int) and 0 <= idx < len(opts):
                letter = chr(97 + idx) # 0->a, 1->b...
                answer_text = opts[idx]
            
            if is_uppercase:
                answer_text = answer_text.upper()
            
            full_line_text = f"{i+1}. {letter}) {answer_text}"
            
            # Robust width and positioning
            pdf.set_x(pdf.l_margin)
            available_w = pdf.w - pdf.l_margin - pdf.r_margin
            
            pdf.multi_cell(available_w, lh_text, safe_text(full_line_text))

    # Output
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    
    filename = f"Ficha_{text.filename.replace('.txt', '')}.pdf"
    
    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )



# --- MAGIC WRITER ENDPOINTS ---

@router.post("/admin/magic/story", response_model=schemas.MagicStoryResponse)
def generate_magic_story(request: schemas.MagicRequest, current_user: schemas.User = Depends(auth.get_current_user)):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    import openai
    import os
    import json
    from dotenv import load_dotenv
    import traceback
    
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ CRITICAL: OPENAI_API_KEY is missing/None in generate_magic_story")
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY missing")

    client = openai.OpenAI(api_key=api_key)

    # Context Loading
    context_instruction = ""
    try:
        if os.path.exists("data/magic_context.txt"):
            with open("data/magic_context.txt", "r", encoding="utf-8") as f:
                context_content = f.read().strip()
                if context_content:
                    context_instruction = f"\n    - CONTEXTO/INSTRUCCIONES ADICIONALES: {context_content}"
    except Exception as e:
        print(f"Warning: Could not read magic_context.txt: {e}")

    prompt_type_map = {
        "story": "un cuento para niños",
        "news": "una noticia periodística adecuada para niños",
        "poem": "un poema o poesía infantil",
        "recipe": "una receta de cocina divertida y realizable"
    }
    
    text_type_desc = prompt_type_map.get(request.text_type, "un texto")

    # Level Constraints
    level_constraints = {
        "1P": "Usa frases muy cortas. Vocabulario de alta frecuencia. Mucha repetición y rimas. Evita subordinadas. Tono alegre y seguro.",
        "2P": "Frases sencillas. Vocabulario cotidiano. Estructura lineal (Inicio-Nudo-Desenlace claro). Diálogos simples.",
        "3P": "Oraciones coordinadas. Introducción de adjetivos descriptivos. Aventuras ligeras y humor.",
        "4P": "Párrafos más desarrollados. Vocabulario variado. Tramas con pequeños giros. Diálogos más naturales.",
        "5P": "Oraciones subordinadas simples. Temas de amistad y superación. Uso de ironía sencilla.",
        "6P": "Estructuras gramaticales completas. Vocabulario rico. Conflictos éticos o emocionales moderados.",
        "1ESO": "Narrativa más compleja. Temas de identidad y pertenencia. Finales abiertos o reflexivos.",
        "2ESO": "Estilo ágil pero sofisticado. Suspenso, misterio o realista. Personajes con profundidad psicológica.",
        "3ESO": "Literatura juvenil. Temas sociales o distópicos. Metáforas y simbolismo.",
        "4ESO": "Preparación para bachillerato. Análisis crítico implícito. Ambigüedad moral.",
        "1BAT": "Literatura casi adulta. Estilo depurado. Temas filosóficos o existenciales.",
        "2BAT": "Alta complejidad sintáctica y semántica. Referencias culturales. Reto intelectual."
    }
    
    selected_constraint = level_constraints.get(request.course_level, "Adapta el lenguaje al nivel escolar indicado.")

    prompt = f"""
    Escribe {text_type_desc} siguiendo ESTRICTAMENTE estas pautas:
    
    1. PARÁMETROS:
    - TEMA: {request.topic}
    - NIVEL: {request.course_level} -> {selected_constraint}
    - LONGITUD: Aprox {request.word_count} palabras.
    - IDIOMA: {request.language}
    
    2. ESTILO Y PEDAGOGÍA:
    - Aplica "Show, Don't Tell" (Muestra, no cuentes).
    - Evita clichés y frases hechas (a menos que sea 1P/2P donde la repetición ayuda).
    - Crea una voz narrativa coherente.
    {context_instruction}

    FORMATO JSON OBLIGATORIO:
    {{
        "title": "Un título creativo y atractivo",
        "content": "El contenido del texto formateado con saltos de línea \\n..."
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un premiado autor de literatura infantil y juvenil, además de pedagogo experto. Tu misión es crear textos fascinantes, literariamente ricos y perfectamente ajustados a las capacidades cognitivas del nivel solicitado. No escribas como un robot, escribe con alma."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.85, # Slightly higher for creativity
            response_format={"type": "json_object"}
        )
        
        json_content = response.choices[0].message.content
        json_content = json_content.replace("```json", "").replace("```", "").strip()
        
        try:
            data = json.loads(json_content)
        except json.JSONDecodeError as je:
            print(f"❌ JSON Decode Error: {je} - Content: {json_content}")
            raise HTTPException(status_code=500, detail="Error de IA: Respuesta no es un JSON válido")

        # Robust Type Handling
        if isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                data = data[0]
            else:
                raise HTTPException(status_code=500, detail="Error de IA: Formato inesperado")

        data["title"] = str(data.get("title") or "Cuento Generado")
        data["content"] = str(data.get("content") or "Error generando contenido")
        
        return schemas.MagicStoryResponse(title=data["title"], content=data["content"])

    except Exception as e:
        print("❌ CRITICAL EXCEPTION IN GENERATE_MAGIC_STORY")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generando cuento: {str(e)}")



# --- HELPERS ---

def generate_lomloe_questions_logic(content: str, client, context_instruction: str = ""):
    import json
    import traceback
    
    prompt = f"""
    Genera 14 preguntas/actividades de comprensión lectora basándote EXCLUSIVAMENTE en el siguiente texto:
    
    TEXTO:
    {content}

    {context_instruction}
    
    DEFINICIONES DE TIPOS DE PREGUNTAS (LOMLOE):

    A) LITERAL (Comprensión):
       - La respuesta está ESCRITA en el texto. Se puede señalar con el dedo.
       - Fórmula: Texto = Respuesta.
       - Si la respuesta usa las mismas palabras, ES LITERAL.

    B) INFERENCIAL (Comprensión):
       - La respuesta NO está escrita explícitamente. Requiere "leer entre líneas".
       - Fórmula: Pistas del texto + Conocimiento previo = Inferencia.
       - Indaga en el "por qué", "conclusiones" o "sentimientos" no explicados.
    
    C) VOCABULARIO (Léxico):
       - Identificación de significados, contrarios o sentido figurado.
    
    D) EXPRESIÓN ORAL (Comunicación):
       - Propuestas para hablar, debatir o explicar algo verbalmente.
    
    E) EXPRESIÓN ESCRITA (Creación):
       - Propuestas para escribir frases, finales alternativos o descripciones.
    
    F) ACTIVIDAD LÚDICA (Juego):
       - Dramatización, dibujo, ritmos o retos divertidos basados en el texto.
    
    G) ACTIVIDAD REFLEXIVA (Valores/Crítico):
       - Relación con valores, emociones o pensamiento crítico (ODS).

    REQUISITOS (Total 14 preguntas/actividades):

    1. 2 PREGUNTAS LITERALES (Tipo Test, 3 opciones).
       - Respuesta explícita en el texto.
       - REASONING: Cita la frase exacta.

    2. 2 PREGUNTAS INFERENCIALES (Tipo Test, 3 opciones).
       - Respuesta deducida.
       - IMPERATIVO: Si la respuesta está en el texto, CÁMBIALA a Literal o haz otra pregunta.
       - REASONING: Explica la deducción.

    3. 2 PREGUNTAS DE VERDADERO O FALSO.
       - Opciones: ["Verdadero", "Falso"].
       - Indica si es [LITERAL] o [INFERENCIAL].

    4. 2 PREGUNTAS DE "RELLENAR HUECO".
       - Enunciado: "Completa la frase: ... ______ ...".
       - REGLA DE ORO: Si es cita exacta -> LITERAL. Si es conclusión -> INFERENCIAL.

    5. 2 PREGUNTAS DE VOCABULARIO.
       - Ej: Buscar antónimo, sinónimo o significado. (Tipo Test u Abierta).
       
    6. 1 ACTIVIDAD DE EXPRESIÓN ORAL.
       - Ej: "Explica a tus compañeros...", "Debate sobre...".
       - Options: [] (Array vacío).
       
    7. 1 ACTIVIDAD DE EXPRESIÓN ESCRITA.
       - Ej: "Escribe un final alternativo...", "Inventa una frase...".
       - Options: [] (Array vacío).

    8. 1 ACTIVIDAD LÚDICA.
       - Ej: "Dibuja...", "Dramatiza...", "Canta...".
       - Options: [] (Array vacío).

    9. 1 ACTIVIDAD REFLEXIVA.
       - Ej: "¿Qué harías tú...?", "¿Por qué es importante...?".
       - Options: [] (Array vacío).

    IMPORTANTE: El campo 'options' debe ser una lista de textos. Si es una actividad abierta, usa [].

    FORMATO JSON OBLIGATORIO:
    {{
        "questions": [
            {{
                "question": "Texto de la pregunta/actividad...",
                "options": ["Opción A", "Opción B"] o [],
                "correct_index": 0,
                "type": "LITERAL" | "INFERENCIAL" | "VOCABULARIO" | "ORAL" | "ESCRITA" | "LUDICA" | "REFLEXIVA",
                "reasoning": "Explicación de la clasificación"
            }}
        ]
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente experto que SOLO responde en JSON válido."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        json_content = response.choices[0].message.content
        json_content = json_content.replace("```json", "").replace("```", "").strip()

        data = json.loads(json_content)

        if isinstance(data, list):
             if len(data) > 0 and isinstance(data[0], dict):
                data = data[0]
        
        if "questions" not in data or not isinstance(data["questions"], list):
            data["questions"] = []

        valid_questions = []
        for i, q in enumerate(data["questions"]):
            if not isinstance(q, dict): continue
            
            # Format Question Text with Type Tag
            q_text = str(q.get("question") or f"Pregunta {i+1}")
            q_type = str(q.get("type", "")).upper().strip()
            
            # CLEAN QUESTION TEXT (No visual tags)
            q["question"] = q_text
            
            if "options" not in q or not isinstance(q["options"], list):
                q["options"] = []
            
            q["options"] = [str(opt) for opt in q["options"] if opt is not None]
            
            # Use strict option count only for Test types
            is_open_activity = any(x in q_type for x in ["ORAL", "ESCRITA", "LUDICA", "LÚDICA", "REFLEXIVA"])
            
            # For standard test types, ensure at least 2 options
            if not is_open_activity:
                 while len(q["options"]) < 2:
                    q["options"].append(f"Opción {len(q['options'])+1}")

            try:
                idx = int(q.get("correct_index", 0))
                if idx < 0 or idx >= len(q["options"]): idx = 0
                q["correct_index"] = idx
            except:
                q["correct_index"] = 0
                
            q["category"] = q_type # ADDED: Valid category for DB
            valid_questions.append(q)

        return valid_questions

    except Exception as e:
        print("❌ CRITICAL EXCEPTION IN generate_lomloe_questions_logic")
        traceback.print_exc()
        raise e

@router.post("/admin/magic/questions", response_model=schemas.MagicQuestionsResponse)
def generate_questions_from_text(request: schemas.MagicQuestionsRequest, current_user: schemas.User = Depends(auth.get_current_user)):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    import openai
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    client = openai.OpenAI(api_key=api_key)

    # Context Loading
    context_instruction = ""
    try:
        if os.path.exists("data/magic_context.txt"):
            with open("data/magic_context.txt", "r", encoding="utf-8") as f:
                context_content = f.read().strip()
                if context_content:
                    context_instruction = f"\n    CONTEXTO ADICIONAL PARA GENERACIÓN: {context_content}\n"
    except Exception as e:
        print(f"Warning: Could not read magic_context.txt: {e}")

    questions_data = generate_lomloe_questions_logic(request.content, client, context_instruction)
    return schemas.MagicQuestionsResponse(questions=questions_data)


@router.post("/admin/magic/save", response_model=schemas.TextResponse)
def save_magic_story(request: schemas.MagicSaveRequest, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    import os
    import re

    # 1. Generate Safe Filename
    safe_title = re.sub(r'[^\w\s-]', '', request.title).strip().lower()
    safe_title = re.sub(r'[-\s]+', '_', safe_title)
    filename = f"{safe_title}.txt"
    
    # 2. Save File
    save_dir = os.path.join(config.TEXTS_DIR, request.course_level)
    os.makedirs(save_dir, exist_ok=True)
    content_path = f"{save_dir}/{filename}"
    
    # Check if exists (append random valid if needed? for now just overwrite or error)
    if os.path.exists(content_path):
        import uuid
        filename = f"{safe_title}_{str(uuid.uuid4())[:4]}.txt"
        content_path = f"{save_dir}/{filename}"

    with open(content_path, "w", encoding="utf-8") as f:
        f.write(request.content)

    # 3. Create DB Entry
    new_text = models.Text(
        title=request.title,
        filename=filename,
        course_level=request.course_level,
        language=request.language,
        content_path=content_path,
        audio_path=request.audio_path,
        image_path=request.image_path
    )
    
    db.add(new_text)
    db.commit()
    db.refresh(new_text)

    # 4. Save Questions
    for q in request.questions:
        db_q = models.Question(
            text_id=new_text.id,
            question_content=q.question,
            options=q.options,
            correct_answer=q.correct_index,
            category=q.category or "LITERAL" # ADDED: Save category
        )
        db.add(db_q)
    
    db.commit()
    
    return new_text

@router.delete("/admin/texts/{text_id}")
def delete_text(text_id: int, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    text = db.query(models.Text).filter(models.Text.id == text_id).first()
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")
        
    db.delete(text)
    db.commit()
    return {"message": "Text deleted successfully"}

@router.get("/admin/texts", response_model=List[schemas.TextResponse])
def get_admin_texts(current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(models.Text).all()

@router.put("/admin/texts/{text_id}/timestamps")
def update_timestamps(text_id: int, request: dict, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    text = db.query(models.Text).filter(models.Text.id == text_id).first()
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")
        
    text.timestamps = request.get('timestamps')
    db.commit()
    return {"status": "success"}

@router.post("/admin/upload-image")
def upload_image(
    file: UploadFile = File(...),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    import shutil
    import os
    import uuid

    # 1. Setup Directory
    save_dir = config.IMAGES_DIR
    os.makedirs(save_dir, exist_ok=True)
    
    # 2. Save File
    try:
        # Generate unique name to avoid conflicts
        ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_path = f"{save_dir}/{unique_filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        print(f"Error saving uploaded image: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving image: {str(e)}")
        
    return {"path": f"/static/images/uploads/{unique_filename}"}
