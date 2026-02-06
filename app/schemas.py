from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UserBase(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    course_level: Optional[str] = "NONE"

class UserCreate(UserBase):
    password: str
    access_code: Optional[str] = None
    license_key: Optional[str] = None
    is_teacher: Optional[bool] = False

class User(UserBase):
    id: int
    access_expires_at: Optional[datetime] = None
    is_teacher: Optional[bool] = False
    
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
    category: Optional[str] = "LITERAL"
    
    class Config:
        from_attributes = True

class TextBase(BaseModel):
    title: str
    course_level: str

class TextResponse(TextBase):
    id: int
    filename: str
    audio_path: Optional[str] = None
    image_path: Optional[str] = None
    content: Optional[str] = None
    is_completed: Optional[bool] = False
    score: Optional[float] = None
    language: Optional[str] = "es"
    is_active: Optional[bool] = True
    is_locked: Optional[bool] = False
    timestamps: Optional[List[Optional[dict]]] = None
    
    class Config:
        from_attributes = True

class TextUpdate(BaseModel):
    course_level: Optional[str] = None
    language: Optional[str] = None

class AttemptCreate(BaseModel):
    text_id: int
    time_spent_seconds: float
    score: float
    user_id: Optional[int] = None
    subuser_id: Optional[int] = None
    details: Optional[dict] = None

class AttemptResponse(AttemptCreate):
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True



class PasswordResetRequest(BaseModel):
    email: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class UnlockRequest(BaseModel):
    access_code: str

class SubUserCreate(BaseModel):
    name: str
    license_key: Optional[str] = None

class SubUserUpdate(BaseModel):
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

# Magic Writer Schemas
class QuestionDraft(BaseModel):
    question: str
    options: List[str]
    correct_index: int
    category: Optional[str] = "LITERAL"

class MagicRequest(BaseModel):
    topic: str
    course_level: str
    word_count: int
    language: str
    text_type: Optional[str] = "story"

class MagicDraftResponse(BaseModel):
    title: str
    content: str
    questions: List[QuestionDraft]

class MagicSaveRequest(BaseModel):
    title: str
    content: str
    questions: List[QuestionDraft]
    course_level: str
    language: str
    audio_path: Optional[str] = None
    image_path: Optional[str] = None

class MagicStoryResponse(BaseModel):
    title: str
    content: str

class MagicQuestionsRequest(BaseModel):
    content: str
    topic: Optional[str] = None

class MagicQuestionsResponse(BaseModel):
    questions: List[QuestionDraft]
