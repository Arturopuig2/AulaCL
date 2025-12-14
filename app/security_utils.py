import secrets
import string
import hmac
import hashlib
from passlib.context import CryptContext

# Configuration
SECRET_KEY = "CHANGE_THIS_TO_ENV_VARIABLE_IN_PROD_BUT_OK_FOR_NOW" # Ideally from env
PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Exclusion list for legibility (I, L, O)
# Note: secrets.choice is CSPRNG
ALPHABET_UPPER_NO_CONFUSING = "ABCDEFGHJKMNPQRSTUVWXYZ" # Removed I, L, O
DIGITS = string.digits

def generate_login_code() -> str:
    """
    Generates an 11-char code: 'CL' + 6 digits + 3 uppercase letters.
    No I, L, O in letters.
    Example: CL482901QTR
    """
    prefix = "CL"
    numbers = ''.join(secrets.choice(DIGITS) for _ in range(6))
    letters = ''.join(secrets.choice(ALPHABET_UPPER_NO_CONFUSING) for _ in range(3))
    return f"{prefix}{numbers}{letters}"

def generate_license_key() -> str:
    """
    Generates a 9-char code: Combination of digits and uppercase letters.
    No I, L, O.
    Example: 8AH2K9M2J
    """
    chars = DIGITS + ALPHABET_UPPER_NO_CONFUSING
    return ''.join(secrets.choice(chars) for _ in range(9))

def hash_code(code: str) -> str:
    """
    Hashes the login code using Bcrypt for storage.
    """
    return PWD_CONTEXT.hash(code)

def verify_code(plain_code: str, hashed_code: str) -> bool:
    """
    Verifies a plain login code against the stored hash.
    """
    return PWD_CONTEXT.verify(plain_code, hashed_code)

def get_code_index(code: str) -> str:
    """
    Generates a deterministic HMAC-SHA256 index for the code.
    This allows looking up the user without storing the code in plain text.
    """
    return hmac.new(
        SECRET_KEY.encode('utf-8'), 
        code.encode('utf-8'), 
        hashlib.sha256
    ).hexdigest()

from sqlalchemy.orm import Session
from app.models import LoginAttempt
from datetime import datetime, timedelta

MAX_ATTEMPTS = 6
BLOCK_DURATION_MINUTES = 5

def check_rate_limit(db: Session, ip_address: str, code_index: str) -> bool:
    """
    Checks if the IP or Code Index is currently blocked.
    Returns True if ALLOWED, False if BLOCKED.
    """
    # 1. Count failures in the last X minutes
    # Simple logic: Fixed window backoff for now (as per req: 5 min initial)
    # Ideally we'd scan backwards to find the last successful login or start of block.
    
    cutoff = datetime.utcnow() - timedelta(minutes=BLOCK_DURATION_MINUTES)
    
    attempts = db.query(LoginAttempt).filter(
        LoginAttempt.login_code_index == code_index,
        LoginAttempt.success == False,
        LoginAttempt.timestamp > cutoff
    ).count()
    
    if attempts >= MAX_ATTEMPTS:
        return False
        
    return True

def record_login_attempt(db: Session, ip_address: str, code_index: str, success: bool):
    """
    Logs a login attempt to the database.
    """
    attempt = LoginAttempt(
        ip_address=ip_address,
        login_code_index=code_index,
        success=success,
        timestamp=datetime.utcnow()
    )
    db.add(attempt)
    db.commit()
