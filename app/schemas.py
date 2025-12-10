from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    course_level: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    
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
