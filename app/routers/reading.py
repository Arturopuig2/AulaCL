from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import database, models, schemas, auth

router = APIRouter(
    prefix="/reading",
    tags=["reading"]
)

@router.get("/texts", response_model=List[schemas.TextResponse])
def get_texts(current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    texts = db.query(models.Text).filter(models.Text.course_level == current_user.course_level).all()
    
    user_attempts = db.query(models.ReadingAttempt).filter(models.ReadingAttempt.user_id == current_user.id).all()
    # Map text_id to latest score (assuming ID order is chronological)
    attempts_map = {a.text_id: a.score for a in user_attempts}
    
    response = []
    for t in texts:
        t_resp = schemas.TextResponse.model_validate(t)
        t_resp.is_completed = t.id in attempts_map
        t_resp.score = attempts_map.get(t.id)
        response.append(t_resp)
        
    return response

@router.get("/texts/{text_id}", response_model=schemas.TextResponse)
def get_text(text_id: int, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    text = db.query(models.Text).filter(models.Text.id == text_id).first()
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")
    
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
