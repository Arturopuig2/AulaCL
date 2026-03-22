from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from .. import database, models, auth

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)

@router.get("/student/{subuser_id}")
def get_student_analytics(
    subuser_id: int, 
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    # Verify subuser belongs to teacher
    subuser = db.query(models.SubUser).filter(
        models.SubUser.id == subuser_id,
        models.SubUser.parent_user_id == current_user.id
    ).first()
    
    if not subuser:
        raise HTTPException(status_code=404, detail="Student not found")
        
    attempts = db.query(models.ReadingAttempt).filter(models.ReadingAttempt.subuser_id == subuser.id).all()
    
    stats = {
        "LITERAL": {"correct": 0, "total": 0},
        "INFERENTIAL": {"correct": 0, "total": 0},
        "VOCABULARY": {"correct": 0, "total": 0},
        "ORDERING": {"correct": 0, "total": 0}
    }
    
    # Cache questions to avoid repeated DB hits
    # In a larger app, we'd join tables, but for MVP loop is fine
    q_cache = {}
    
    for attempt in attempts:
        if not attempt.details:
            continue
            
        # details is expected to be Dict[str, bool] where key is question_id
        for q_id_str, is_correct in attempt.details.items():
            try:
                q_id = int(q_id_str)
            except:
                continue
                
            if q_id not in q_cache:
                q = db.query(models.Question).filter(models.Question.id == q_id).first()
                if q:
                    q_cache[q_id] = q.category or "LITERAL"
                else:
                    q_cache[q_id] = "UNKNOWN"
            
            cat = q_cache[q_id]
            
            # NORMALIZE KEYS (DB might have Spanish "INFERENCIAL")
            cat_upper = cat.upper().strip()
            if "INFERENCIA" in cat_upper:
                cat = "INFERENTIAL"
            elif "VOCABULARIO" in cat_upper:
                cat = "VOCABULARY"
            elif "ORDERING" in cat_upper:
                cat = "ORDERING"
            elif "LITERAL" in cat_upper:
                cat = "LITERAL"
                
            # Normalize category if needed, assuming uppercase from DB default
            if cat not in stats:
                stats[cat] = {"correct": 0, "total": 0}
                
            stats[cat]["total"] += 1
            if is_correct:
                stats[cat]["correct"] += 1

    # Calculate percentages
    results = {}
    for cat, data in stats.items():
        if data["total"] > 0:
            results[cat] = round((data["correct"] / data["total"]) * 100, 1)
        else:
            results[cat] = 0
            
    return {
        "categories": results,
        "total_readings": len(attempts),
        "reading_history": [
            {
                "title": attempt.text.title if attempt.text else "Lectura Eliminada",
                "score": attempt.score,
                "correct_count": sum(1 for v in attempt.details.values() if v) if attempt.details else 0,
                "total_count": len(attempt.details) if attempt.details else 0,
                "date": attempt.timestamp.isoformat()
            }
            for attempt in attempts
        ]
    }

@router.get("/class")
def get_class_analytics(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    subusers = current_user.subusers
    
    global_stats = {
        "LITERAL": {"correct": 0, "total": 0},
        "INFERENTIAL": {"correct": 0, "total": 0},
        "VOCABULARY": {"correct": 0, "total": 0},
        "ORDERING": {"correct": 0, "total": 0}
    }
    
    q_cache = {}
    
    for sub in subusers:
        attempts = db.query(models.ReadingAttempt).filter(models.ReadingAttempt.subuser_id == sub.id).all()
        for attempt in attempts:
            if not attempt.details:
                continue
                
            for q_id_str, is_correct in attempt.details.items():
                try:
                    q_id = int(q_id_str)
                except:
                    continue
                    
                if q_id not in q_cache:
                    q = db.query(models.Question).filter(models.Question.id == q_id).first()
                    if q:
                        q_cache[q_id] = q.category or "LITERAL"
                    else:
                        q_cache[q_id] = "UNKNOWN"
                
                cat = q_cache[q_id]
                
                # NORMALIZE KEYS
                cat_upper = cat.upper().strip()
                if "INFERENCIA" in cat_upper:
                    cat = "INFERENTIAL"
                elif "VOCABULARIO" in cat_upper:
                    cat = "VOCABULARY"
                elif "ORDERING" in cat_upper:
                    cat = "ORDERING"
                elif "LITERAL" in cat_upper:
                    cat = "LITERAL"

                if cat not in global_stats:
                    global_stats[cat] = {"correct": 0, "total": 0}
                    
                global_stats[cat]["total"] += 1
                if is_correct:
                    global_stats[cat]["correct"] += 1
                    
    results = {}
    for cat, data in global_stats.items():
        if data["total"] > 0:
            results[cat] = round((data["correct"] / data["total"]) * 100, 1)
        else:
            results[cat] = 0
            
    return results

@router.get("/me")
def get_my_analytics(
    current_user = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    # Determine if user or subuser
    is_subuser = isinstance(current_user, models.SubUser)
    
    # Filter attempts
    if is_subuser:
        # Check attempts where subuser_id matches current subuser ID
        attempts = db.query(models.ReadingAttempt).filter(models.ReadingAttempt.subuser_id == current_user.id).all()
        
        # Fallback: Check user_id as well in case of legacy data mixed up (just to be safe), 
        # but STRICTLY avoid mixing with main User IDs if possible.
        # Since SubUser ID 1 and User ID 1 are different entities, we must rely on the column structure.
        # models.ReadingAttempt has separate columns: user_id (ForeignKey users.id) and subuser_id (ForeignKey subusers.id).
        # We should only query subuser_id.
    else:
        # Regular user
        attempts = db.query(models.ReadingAttempt).filter(models.ReadingAttempt.user_id == current_user.id).all() 


    # Reuse logic (Copy-paste for now to avoid refactor risk, or extract)
    # Extracting logic is cleaner.
    
    return calculate_analytics(attempts, db)

def calculate_analytics(attempts: List[models.ReadingAttempt], db: Session):
    stats = {
        "LITERAL": {"correct": 0, "total": 0},
        "INFERENTIAL": {"correct": 0, "total": 0},
        "VOCABULARY": {"correct": 0, "total": 0},
        "DECODING": {"correct": 0, "total": 0},
        "ORDERING": {"correct": 0, "total": 0}
    }
    
    q_cache = {}
    
    for attempt in attempts:
        if not attempt.details:
            continue
            
        for q_id_str, is_correct in attempt.details.items():
            try:
                q_id = int(q_id_str)
            except:
                continue
                
            if q_id not in q_cache:
                q = db.query(models.Question).filter(models.Question.id == q_id).first()
                if q:
                    q_cache[q_id] = q.category or "LITERAL"
                else:
                    q_cache[q_id] = "UNKNOWN"
            
            cat = q_cache[q_id]
            cat_upper = cat.upper().strip()
            if "INFERENCIA" in cat_upper:
                cat = "INFERENTIAL"
            elif "VOCABULARIO" in cat_upper:
                cat = "VOCABULARY"
            elif "ORDERING" in cat_upper:
                cat = "ORDERING"
            elif "LITERAL" in cat_upper:
                cat = "LITERAL"
            elif "DECODIF" in cat_upper:
                cat = "DECODING"
                
            if cat not in stats:
                stats[cat] = {"correct": 0, "total": 0}
                
            stats[cat]["total"] += 1
            if is_correct:
                stats[cat]["correct"] += 1

    results = {}
    for cat, data in stats.items():
        if data["total"] > 0:
            results[cat] = round((data["correct"] / data["total"]) * 100, 1)
        else:
            results[cat] = 0
            
    return {
        "categories": results,
        "total_readings": len(attempts),
        "reading_history": [
            {
                "title": attempt.text.title if attempt.text else "Lectura Eliminada",
                "score": attempt.score,
                "correct_count": sum(1 for v in attempt.details.values() if v) if attempt.details else 0,
                "total_count": len(attempt.details) if attempt.details else 0,
                "date": attempt.timestamp.isoformat()
            }
            for attempt in attempts
        ]
    }
