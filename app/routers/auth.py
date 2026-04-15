from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
import os
from app import schemas, models, security_utils
from app.limiter import limiter
from app.database import get_db
from app.auth import authenticate_user, create_access_token, get_current_user, get_current_active_user, ACCESS_TOKEN_EXPIRE_MINUTES, get_password_hash, verify_password

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: schemas.User = Depends(get_current_user)):
    return current_user

@router.post("/login-code", response_model=schemas.Token)
@limiter.limit("5/minute")
def login_with_code(
    login_req: schemas.LoginCodeRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    # 1. Calculate identifiers
    code = login_req.code
    ip_address = request.client.host
    code_index = security_utils.get_code_index(code)
    
    # 2. Check Rate Limit
    if not security_utils.check_rate_limit(db, ip_address, code_index):
        # Log the blocked attempt? (Optional, check_rate_limit usually implies we stop here)
        # We record it as a failure just to keep the block alive? 
        # For now, just 429.
        security_utils.record_login_attempt(db, ip_address, code_index, success=False)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )

    # 3. Find User
    subuser = db.query(models.SubUser).filter(models.SubUser.login_code_index == code_index).first()
    
    if not subuser:
        # Invalid code (User not found)
        security_utils.record_login_attempt(db, ip_address, code_index, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login code",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 4. Verify Hash
    if not subuser.login_code_hash or not security_utils.verify_code(code, subuser.login_code_hash):
        security_utils.record_login_attempt(db, ip_address, code_index, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login code",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 5. Success
    security_utils.record_login_attempt(db, ip_address, code_index, success=True)
    
    # Check Expiry
    if subuser.access_expires_at and subuser.access_expires_at < datetime.utcnow():
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access expired. Please renew your license.",
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # We use subuser.name as the identity for now, or maybe a composite?
    # Existing `get_current_user` expects `username`. SubUsers don't have usernames.
    # We might need to encode a flag in the token, e.g. "subuser:123"
    
    access_token = create_access_token(
        data={"sub": f"subuser:{subuser.id}"}, # Special prefix for subusers
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

from authlib.integrations.starlette_client import OAuth

# OAUTH SETUP
oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@router.get("/google")
async def login_google(request: Request):
    # Determine redirect URI dynamically or from env
    # For local: http://127.0.0.1:8000/auth/google/callback
    redirect_uri = request.url_for('auth_google_callback')
    # Force https if we are not on localhost (Render requirement)
    if "127.0.0.1" not in str(request.url) and "localhost" not in str(request.url):
        redirect_uri = str(redirect_uri).replace("http://", "https://")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def auth_google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        try:
            token = await oauth.google.authorize_access_token(request)
        except Exception as e:
             import traceback
             error_trace = traceback.format_exc()
             print(f"OAuth Error: {e}")
             print(error_trace)
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Google Auth Failed: {str(e)}. Check server logs for details."
             )

        user_info = token.get('userinfo')
        if not user_info:
             # Sometimes userinfo is in the token 'id_token' claims
             user_info = token.get('id_token') 
        
        email = user_info.get('email')
        name = user_info.get('name')
        
        if not email:
             raise HTTPException(status_code=400, detail="Email not found in Google Account")

        # LOGIN / REGISTER LOGIC
        user = db.query(models.User).filter(models.User.email == email).first()
        
        if not user:
            # Create new user
            import secrets
            import string
            
            base_username = email.split("@")[0]
            base_username = "".join(c for c in base_username if c.isalnum())
            
            clean_username = base_username
            while db.query(models.User).filter(models.User.username == clean_username).first():
                suffix = ''.join(secrets.choice(string.digits) for _ in range(4))
                clean_username = f"{base_username}{suffix}"
                
            random_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
            hashed_pwd = get_password_hash(random_password)
            
            new_user = models.User(
                username=clean_username,
                email=email,
                name=name,
                hashed_password=hashed_pwd,
                course_level="ALL" # Default
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user = new_user
            
        # Create Access Token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )
        
        # Standardize redirect to /login so login.html handles token storage and redirection
        response = RedirectResponse(url=f"/login?google_token={access_token}&username={user.username}")
        return response

    except Exception as e:
        import traceback
        traceback.print_exc()
        return HTMLResponse(content=f"<h1>Error Logging In</h1><p>{str(e)}</p>", status_code=500)
    # we will redirect to a special frontend route `/google-success?token=...`
    # or `/login?token=...` that parses it and sets localStorage.
    
    response = RedirectResponse(url=f"/login?google_token={access_token}&username={user.username}")
    return response

@router.post("/register", response_model=schemas.User)
@limiter.limit("3/minute")
def register(request: Request, user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    # VALIDATION: Strict format
    import re
    # 1. Email Format (Username must be email)
    email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    if not re.match(email_regex, user.username):
         raise HTTPException(status_code=400, detail="El nombre de usuario debe ser un correo electrónico válido")
         
    # 2. Password Complexity
    # At least 8 chars, 1 letter, 1 number
    if len(user.password) < 8:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres")
        
    if not re.search(r'[A-Za-z]', user.password) or not re.search(r'\d', user.password):
        raise HTTPException(status_code=400, detail="La contraseña debe contener al menos una letra y un número")
    
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

    hashed_password = get_password_hash(user.password)
    
    # Freemium: No expiration by default (or expired in past), until code is used.
    # We can set it to None, which means "Free Tier".
    expires_at = None
    
    db_user = models.User(
        username=user.username, 
        hashed_password=hashed_password, 
        course_level=user.course_level,
        email=user.email,
        name=user.name,
        access_expires_at=expires_at,
        is_teacher=user.is_teacher
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Process License Key if provided (Anonymous -> Registered User with License)
    if user.license_key and user.license_key.strip():
        lic_key = user.license_key.strip().upper()
        license_entry = db.query(models.License).filter(models.License.key == lic_key).first()
        
        if license_entry and license_entry.status == "ACTIVE":
            license_entry.status = "USED"
            license_entry.activated_at = datetime.utcnow()
            license_entry.used_by_user_id = db_user.id
            
            # Set Expiry
            now = datetime.utcnow()
            db_user.access_expires_at = now + timedelta(days=license_entry.duration_days)
            db.commit()
            db.refresh(db_user)

    return db_user

@router.post("/token", response_model=schemas.Token)
@limiter.limit("5/minute")
def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password")
@limiter.limit("3/minute")
def forgot_password(request_data: schemas.PasswordResetRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == request_data.email).first()
    if not user:
        # Don't reveal that the user does not exist (security best practice), or do it for UX in this MVP?
        # User asked for "pon tu correo y te enviamos un enlace". 
        # Let's just return success message.
        return {"message": "Si el correo existe, se enviará un enlace."}
    
    # Generar Token
    access_token_expires = timedelta(minutes=15)
    reset_token = create_access_token(
        data={"sub": user.username, "type": "reset"}, expires_delta=access_token_expires
    )
    
    # Determinar URL dinámica (sirve para localhost o producción)
    base_url = str(request.base_url).rstrip("/")
    if "127.0.0.1" not in base_url and "localhost" not in base_url:
        base_url = base_url.replace("http://", "https://")
    reset_link = f"{base_url}/reset-password?token={reset_token}"
    
    # Intentar enviar por Email real si hay variables de entorno (SMTP)
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    
    if smtp_user and smtp_pass:
        import smtplib
        from email.mime.text import MIMEText
        from email.utils import formataddr
        try:
            msg = MIMEText(f"Hola {user.name or user.username},\n\nAquí tienes tu enlace para crear una nueva contraseña en Aula CL:\n\n{reset_link}\n\nEste enlace caducará en 15 minutos.")
            # Prevenir que el mail llegue como From: 'info' si el servidor requiere login corto
            smtp_from = os.getenv("SMTP_FROM", smtp_user)
            if "@" not in smtp_from:
                smtp_from = f"{smtp_from}@editorialaula.es"

            # Personalizar el nombre visible del remitente
            sender_name = os.getenv("SMTP_SENDER_NAME", "Aula CL")

            msg['Subject'] = 'Recuperar Contraseña - Aula CL'
            msg['From'] = formataddr((sender_name, smtp_from))
            msg['To'] = user.email
            
            # Usa el host y puerto especificado en variables, o asume Gmail por defecto
            smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", 587))
            
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            return {"message": "Enlace enviado con éxito a tu correo electrónico."}
        except Exception as e:
            print(f"SMTP Error: {e}")
            return {"message": "Error al enviar el correo, pero operamos en modo seguro. Contactar al admin."}
    else:
        # MODO SIMULACIÓN (Local o si no hay SMTP configurado)
        print("==================================================")
        print(f"PASSWORD RESET LINK FOR {user.username}:")
        print(reset_link)
        print("==================================================")
        
        return {"message": "Modo simulación: Revisa la terminal del servidor para ver el link de recuperación."}

@router.post("/reset-password")
def reset_password(request: schemas.PasswordResetConfirm, db: Session = Depends(get_db)):
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
        hashed_password = get_password_hash(request.new_password)
        user.hashed_password = hashed_password
        db.commit()
        
        return {"message": "Contraseña restablecida correctamente"}
        
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

@router.post("/change-password")
def change_password(request: schemas.ChangePasswordRequest, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 1. Verify Current Password
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not verify_password(request.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")
    
    # 2. Update Password
    user.hashed_password = get_password_hash(request.new_password)
    db.commit()
    
    return {"message": "Contraseña actualizada correctamente"}

@router.post("/unlock")
def unlock_content(request: schemas.UnlockRequest, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Validate Code (Force Uppercase)
    code_input = request.access_code.upper().strip()
    
    # 1. TRY LICENSE TABLE (Standard Format: LIC-XXXXXXXX)
    license_entry = db.query(models.License).filter(models.License.key == code_input).first()
    
    invitation = None
    used_license = False
    duration_days = 365
    
    if license_entry:
        if license_entry.status != "ACTIVE":
             raise HTTPException(status_code=403, detail="Esta licencia ya ha sido utilizada o no es válida")
        used_license = True
    else:
        # 2. TRY INVITATION CODE (Legacy)
        invitation = db.query(models.InvitationCode).filter(models.InvitationCode.code == code_input).first()
        if not invitation:
            raise HTTPException(status_code=403, detail="Código de acceso inválido")
        
        if invitation.is_used:
            raise HTTPException(status_code=403, detail="Este código de acceso ya ha sido utilizado")

    # Grant Access (Cumulative)
    now = datetime.utcnow()
    
    if current_user.access_expires_at and current_user.access_expires_at > now:
        # Extend existing time
        current_user.access_expires_at += timedelta(days=duration_days)
        message = "¡Suscripción extendida 1 año!"
    else:
        # Start new subscription
        current_user.access_expires_at = now + timedelta(days=duration_days)
        message = "¡Contenido desbloqueado por 1 año!"
    
    # Mark code as used
    if used_license:
        license_entry.status = "USED"
        license_entry.activated_at = now
        license_entry.used_by_user_id = current_user.id
    else:
        invitation.is_used = True
        invitation.used_at = now
        invitation.used_by_user_id = current_user.id
    
    db.commit()
    
    return {"message": message, "expires_at": current_user.access_expires_at}



# --- ADMIN: CODE GENERATION ---
@router.post("/admin/codes", response_model=List[str])
def generate_codes(count: int = 1, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
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
def get_codes(current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
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

@router.get("/debug-openai")
def debug_openai_config():
    import os
    import openai
    
    key = os.getenv("OPENAI_API_KEY")
    report = {
        "key_present": bool(key),
        "key_length": len(key) if key else 0,
        "key_preview": f"{key[:5]}..." if key else "None",
        "api_call": "Not attempted"
    }
    
    if key:
        try:
            client = openai.OpenAI(api_key=key)
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5
            )
            report["api_call"] = "Success"
        except Exception as e:
            report["api_call"] = f"Failed: {str(e)}"
            
    return report

# --- ADMIN: LICENSE GENERATION (For Students) ---
@router.post("/admin/licenses", response_model=List[str])
def generate_licenses(count: int = 1, duration_days: int = 365, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    import secrets
    import string
    
    new_keys = []
    for _ in range(count):
        # Generate random uppercase code
        rand_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        key = f"LIC-{rand_part}"
        
        # Check uniqueness in License table
        while db.query(models.License).filter(models.License.key == key).first():
             rand_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
             key = f"LIC-{rand_part}"
             
        # Create License (Student License)
        db_license = models.License(
            key=key,
            status="ACTIVE",
            duration_days=duration_days
        )
        db.add(db_license)
        new_keys.append(key)
    
    db.commit()
    return new_keys

@router.get("/admin/licenses")
def get_licenses(current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # 1. Fetch Subuser Licenses (Old Model)
    licenses = db.query(models.License).all()
    
    result = []
    
    # Process Subuser Licenses
    for lic in licenses:
        used_by_name = None
        parent_email = None
        if lic.used_by_subuser_id:
            sub = db.query(models.SubUser).filter(models.SubUser.id == lic.used_by_subuser_id).first()
            if sub:
                used_by_name = f"SubUser: {sub.name}"
                if sub.parent_user:
                    parent_email = sub.parent_user.email

        result.append({
            "key": lic.key,
            "status": lic.status,
            "duration_days": lic.duration_days,
            "created_at": lic.created_at,
            "activated_at": lic.activated_at,
            "used_by": used_by_name,
            "parent_email": parent_email,
            "type": "Student"
        })

    # 2. Fetch Main Invitation Codes (New Model)
    invitations = db.query(models.InvitationCode).all()
    for inv in invitations:
        used_by_name = None
        parent_email = None
        status = "USED" if inv.is_used else "ACTIVE"
        
        if inv.used_by_user_id:
            u = db.query(models.User).filter(models.User.id == inv.used_by_user_id).first()
            if u:
                used_by_name = f"User: {u.name or u.username}"
                parent_email = u.email
        
        result.append({
            "key": inv.code,
            "status": status,
            "duration_days": 365,
            "created_at": inv.created_at,
            "activated_at": inv.used_at,
            "used_by": used_by_name,
            "parent_email": parent_email,
            "type": "Premium"
        })
        
    return result
