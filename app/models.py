from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, JSON
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    course_level = Column(String)  # e.g., "1ESO", "2ESO"
    
    attempts = relationship("ReadingAttempt", back_populates="user")
    predictions = relationship("Prediction", back_populates="user")

class Text(Base):
    __tablename__ = "texts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    filename = Column(String, unique=True)
    course_level = Column(String)
    content_path = Column(String) # Path to the .txt file
    audio_path = Column(String, nullable=True) # Path to the .mp3 file
    language = Column(String, default="es") # "es", "en", "val", "cat", "gal", "eus", "fr"
    
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
