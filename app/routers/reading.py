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

@router.get("/prediction", response_model=schemas.PredictionResponse)
def get_prediction(current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    from .. import ml
    attempts = db.query(models.ReadingAttempt).filter(models.ReadingAttempt.user_id == current_user.id).all()
    predicted_score = ml.get_latest_prediction(attempts)
    
    # Save prediction?
    if isinstance(predicted_score, float) or isinstance(predicted_score, int):
        # It's a number
        return {"predicted_score": float(predicted_score), "message": "Basado en tu rendimiento reciente."}
    else:
        # It's a string message
        return {"predicted_score": 0.0, "message": str(predicted_score)}

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

@router.delete("/admin/texts/{text_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_text(text_id: int, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    text = db.query(models.Text).filter(models.Text.id == text_id).first()
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")
    
    # Delete associated files
    import os
    if os.path.exists(text.content_path):
        os.remove(text.content_path)
    if text.audio_path:
        full_audio_path = f"static/{text.audio_path}"
        if os.path.exists(full_audio_path):
            os.remove(full_audio_path)
            
    db.delete(text)
    db.commit()
    return None
