from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
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

    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username, 
        hashed_password=hashed_password, 
        course_level=user.course_level,
        email=user.email
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
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
