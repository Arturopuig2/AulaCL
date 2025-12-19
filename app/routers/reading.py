from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from .. import database, models, schemas, auth

router = APIRouter(
    prefix="/reading",
    tags=["reading"]
)

@router.get("/texts", response_model=List[schemas.TextResponse])
def get_texts(current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    # Return all texts so frontend can filter by course
    is_admin = False
    if hasattr(current_user, "username") and current_user.username == "admin":
        is_admin = True
        
    if is_admin:
        texts = db.query(models.Text).all()
    else:
        texts = db.query(models.Text).filter(models.Text.is_active == True).all()
    
    user_attempts = db.query(models.ReadingAttempt).filter(models.ReadingAttempt.user_id == current_user.id).all()
    attempts_map = {a.text_id: a.score for a in user_attempts}
    
    # Check Premium Status
    is_premium = False
    if (current_user.access_expires_at and current_user.access_expires_at > datetime.utcnow()) or current_user.username == "admin":
        is_premium = True
        
    # Free Text Logic: First text created (lowest ID) is free.
    # Assuming IDs are 1, 2, 3...
    min_id = min([t.id for t in texts]) if texts else 0
    
    response = []
    for t in texts:
        t_resp = schemas.TextResponse.model_validate(t)
        t_resp.is_completed = t.id in attempts_map
        t_resp.score = attempts_map.get(t.id)
        
        # Lock Logic
        if is_premium:
            t_resp.is_locked = False
        else:
            if t.id == min_id: # First one is free
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
    if (current_user.access_expires_at and current_user.access_expires_at > datetime.utcnow()) or current_user.username == "admin":
        is_premium = True
        
    # Recalculate if it's the free one (needs logic or DB query optimization, for MVP simple query)
    first_text = db.query(models.Text).order_by(models.Text.id.asc()).first()
    is_free = (first_text and text.id == first_text.id)
    
    if not is_premium and not is_free:
        raise HTTPException(status_code=403, detail="Contenido bloqueado. Introduce un código para desbloquear.")

    # Read content from file
    try:
        with open(text.content_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        content = "Error loading text content."

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
def submit_attempt(attempt: schemas.AttemptCreate, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    # Calculate score logic can be here if we receive answers, but for now we trust the frontend sends the score
    # Or we could receive selected answers and calculate score here for security. 
    # For MVP, believing the score from frontend is faster (as per user request "Le propone unas preguntas..."). 
    # Let's stick to the schema which accepts 'score'. 
    
    db_attempt = models.ReadingAttempt(
        user_id=current_user.id,
        text_id=attempt.text_id,
        time_spent_seconds=attempt.time_spent_seconds,
        score=attempt.score
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
    db.commit()
    db.refresh(text)
    return text

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
    save_dir = f"data/texts/{course_level}"
    os.makedirs(save_dir, exist_ok=True)
    
    filename = text_file.filename
    content_path = f"{save_dir}/{filename}"
    
    with open(content_path, "wb") as buffer:
        shutil.copyfileobj(text_file.file, buffer)
        
    # 2. Save Audio File (if present)
    audio_path = None
    if audio_file:
        audio_filename = audio_file.filename
        audio_save_dir = "static/audio"
        os.makedirs(audio_save_dir, exist_ok=True)
        audio_path_full = f"{audio_save_dir}/{audio_filename}"
        
        with open(audio_path_full, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        
        # Store relative path for DB
        audio_path = f"audio/{audio_filename}"

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
        
    first_text = db.query(models.Text).order_by(models.Text.id.asc()).first()
    is_free = (first_text and text.id == first_text.id)
    
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
