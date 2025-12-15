from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, JSON, Boolean
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    email = Column(String, nullable=True)
    course_level = Column(String, default="ALL")
    name = Column(String, nullable=True)
    access_expires_at = Column(DateTime, nullable=True)
    
    attempts = relationship("ReadingAttempt", back_populates="user")
    predictions = relationship("Prediction", back_populates="user")
    subusers = relationship("SubUser", back_populates="parent_user")

class InvitationCode(Base):
    __tablename__ = "invitation_codes"

    code = Column(String, primary_key=True, index=True)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime, nullable=True)
    used_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    user = relationship("User")

class Text(Base):
    __tablename__ = "texts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    filename = Column(String, unique=True)
    course_level = Column(String)
    content_path = Column(String) # Path to the .txt file
    audio_path = Column(String, nullable=True) # Path to the .mp3 file
    language = Column(String, default="es") # "es", "en", "val", "cat", "gal", "eus", "fr"
    is_active = Column(Boolean, default=True)
    
    questions = relationship("Question", back_populates="text")
    attempts = relationship("ReadingAttempt", back_populates="text")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    text_id = Column(Integer, ForeignKey("texts.id"))
    question_content = Column(String)
    options = Column(JSON) # Store as JSON list ["Option A", "Option B", ...]
    correct_answer = Column(Integer) # Index of correct option (0-3)

    text = relationship("Text", back_populates="questions")

class ReadingAttempt(Base):
    __tablename__ = "reading_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    text_id = Column(Integer, ForeignKey("texts.id"))
    time_spent_seconds = Column(Float)
    score = Column(Float) # Percentage or raw score
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="attempts")
    text = relationship("Text", back_populates="attempts")

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    predicted_score = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="predictions")

class SubUser(Base):
    __tablename__ = "subusers"

    id = Column(Integer, primary_key=True, index=True)
    parent_user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    
    # Security fields for code-based login
    login_code_hash = Column(String, nullable=True) # Bcrypt hash
    login_code_index = Column(String, index=True, nullable=True) # HMAC for lookup
    login_code_display = Column(String, nullable=True) # RAW CODE FOR DISPLAY (User Request)
    
    is_active = Column(Boolean, default=True)
    access_expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    parent_user = relationship("User", back_populates="subusers")
    licenses = relationship("License", back_populates="subuser")

class License(Base):
    __tablename__ = "licenses"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True) # The 9-char code
    status = Column(String, default="ACTIVE") # ACTIVE, USED, REVOKED
    duration_days = Column(Integer, default=365)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    activated_at = Column(DateTime, nullable=True)
    
    used_by_subuser_id = Column(Integer, ForeignKey("subusers.id"), nullable=True)
    subuser = relationship("SubUser", back_populates="licenses")

class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String, index=True)
    login_code_index = Column(String, index=True, nullable=True) # Targeted account (if known)
    timestamp = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=False)
