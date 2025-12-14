from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    name: Optional[str] = None
    course_level: Optional[str] = "NONE"

class UserCreate(UserBase):
    password: str
    access_code: Optional[str] = None

class User(UserBase):
    id: int
    access_expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class QuestionBase(BaseModel):
    question_content: str
    options: List[str]
    
class QuestionResponse(QuestionBase):
    id: int
    correct_answer: int
    
    class Config:
        from_attributes = True

class TextBase(BaseModel):
    title: str
    course_level: str

class TextResponse(TextBase):
    id: int
    filename: str
    audio_path: Optional[str] = None
    content: Optional[str] = None
    is_completed: Optional[bool] = False
    score: Optional[float] = None
    language: Optional[str] = "es"
    is_locked: Optional[bool] = False
    
    class Config:
        from_attributes = True

class TextUpdate(BaseModel):
    course_level: Optional[str] = None
    language: Optional[str] = None

class AttemptCreate(BaseModel):
    text_id: int
    time_spent_seconds: float
    score: float

class AttemptResponse(AttemptCreate):
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class PredictionResponse(BaseModel):
    predicted_score: float
    message: Optional[str] = None

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class UnlockRequest(BaseModel):
    access_code: str

class SubUserCreate(BaseModel):
    name: str

class SubUserResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    access_expires_at: Optional[datetime] = None
    login_code_display: Optional[str] = None
    
    class Config:
        from_attributes = True

class LicenseActivate(BaseModel):
    license_key: str

class LoginCodeRequest(BaseModel):
    code: str
