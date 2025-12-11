from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
from .. import database, models, schemas, auth

router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

@router.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email is already taken (if provided)
    if user.email:
         db_email = db.query(models.User).filter(models.User.email == user.email).first()
         if db_email:
             raise HTTPException(status_code=400, detail="Email already registered")

    # VALIDATE ACCESS CODE against DB - REMOVED for Freemium
    # if not user.access_code:
    #     raise HTTPException(status_code=400, detail="Código de acceso requerido")
        
    # invitation = db.query(models.InvitationCode).filter(models.InvitationCode.code == user.access_code).first()
    
    # if not invitation:
    #     raise HTTPException(status_code=403, detail="Código de acceso inválido")
    
    # if invitation.is_used:
    #     raise HTTPException(status_code=403, detail="Este código de acceso ya ha sido utilizado")

    hashed_password = auth.get_password_hash(user.password)
    
    # Freemium: No expiration by default (or expired in past), until code is used.
    # We can set it to None, which means "Free Tier".
    expires_at = None
    
    db_user = models.User(
        username=user.username, 
        hashed_password=hashed_password, 
        course_level=user.course_level,
        email=user.email,
        access_expires_at=expires_at
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Mark Invitation as Used - REMOVED here, moved to /unlock
    
    return db_user

@router.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password")
def forgot_password(request: schemas.PasswordResetRequest, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user:
        # Don't reveal that the user does not exist (security best practice), or do it for UX in this MVP?
        # User asked for "pon tu correo y te enviamos un enlace". 
        # Let's just return success message.
        return {"message": "Si el correo existe, se enviará un enlace."}
    
    # Generate Token
    access_token_expires = timedelta(minutes=15) # Short lived
    reset_token = auth.create_access_token(
        data={"sub": user.username, "type": "reset"}, expires_delta=access_token_expires
    )
    
    # SIMULATE EMAIL SENDING
    print("==================================================")
    print(f"PASSWORD RESET LINK FOR {user.username}:")
    print(f"http://127.0.0.1:8000/reset-password?token={reset_token}")
    print("==================================================")
    
    return {"message": "Enlace enviado (Revisar consola del servidor)."}

@router.post("/reset-password")
def reset_password(request: schemas.PasswordResetConfirm, db: Session = Depends(database.get_db)):
    try:
        # Verify Token
        from jose import jwt, JWTError
        from ..auth import SECRET_KEY, ALGORITHM
        
        payload = jwt.decode(request.token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if username is None or token_type != "reset":
            raise HTTPException(status_code=400, detail="Invalid token")
            
        user = db.query(models.User).filter(models.User.username == username).first()
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
        
        # Update Password
        hashed_password = auth.get_password_hash(request.new_password)
        user.hashed_password = hashed_password
        db.commit()
        
        return {"message": "Contraseña restablecida correctamente"}
        
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

@router.post("/unlock")
def unlock_content(request: schemas.UnlockRequest, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    # Validate Code (Force Uppercase)
    code_input = request.access_code.upper().strip()
    invitation = db.query(models.InvitationCode).filter(models.InvitationCode.code == code_input).first()
    
    if not invitation:
        raise HTTPException(status_code=403, detail="Código de acceso inválido")
    
    if invitation.is_used:
        raise HTTPException(status_code=403, detail="Este código de acceso ya ha sido utilizado")

    # Grant 1 Year Access (Cumulative)
    now = datetime.utcnow()
    one_year = timedelta(days=365)
    
    if current_user.access_expires_at and current_user.access_expires_at > now:
        # Extend existing time
        current_user.access_expires_at += one_year
        message = "¡Suscripción extendida 1 año!"
    else:
        # Start new subscription
        current_user.access_expires_at = now + one_year
        message = "¡Contenido desbloqueado por 1 año!"
    
    # Mark code as used
    invitation.is_used = True
    invitation.used_at = now
    invitation.used_by_user_id = current_user.id
    
    db.commit()
    
    return {"message": message, "expires_at": current_user.access_expires_at}

@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: schemas.User = Depends(auth.get_current_user)):
    return current_user

# --- ADMIN: CODE GENERATION ---
@router.post("/admin/codes", response_model=List[str])
def generate_codes(count: int = 1, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    import secrets
    import string
    
    new_codes = []
    for _ in range(count):
        # Generate random 8-char code (Uppercase + Digits)
        code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        
        # Check uniqueness (simplified, unlikely collision with 8 chars but safer to check)
        while db.query(models.InvitationCode).filter(models.InvitationCode.code == code).first():
             code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
             
        db_code = models.InvitationCode(code=code)
        db.add(db_code)
        new_codes.append(code)
    
    db.commit()
    return new_codes

@router.get("/admin/codes")
def get_codes(current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    codes = db.query(models.InvitationCode).all()
    return [{
        "code": c.code, 
        "is_used": c.is_used, 
        "used_at": c.used_at, 
        "created_at": c.created_at,
        "used_by": c.user.username if c.user else None,
        "user_email": c.user.email if c.user else None,
        "expires_at": c.user.access_expires_at if c.user else None
    } for c in codes]
