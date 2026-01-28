from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    name = Column(String)
    goals = Column(Text) # JSON or text description
    preferences = Column(Text) # JSON or text description
    
    workouts = relationship("Workout", back_populates="user")
    meals = relationship("Meal", back_populates="user")
    body_metrics = relationship("BodyMetric", back_populates="user")
    daily_summaries = relationship("DailySummary", back_populates="user")

class Workout(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    exercise_name = Column(String)
    sets = Column(Integer, nullable=True)
    reps = Column(Integer, nullable=True)
    weight_kg = Column(Float, nullable=True)
    duration_minutes = Column(Float, nullable=True)
    calories_burned = Column(Float)
    image_path = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="workouts")

class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    food_name = Column(String)
    weight_grams = Column(Float, nullable=True)
    calories = Column(Float)
    protein = Column(Float)
    carbs = Column(Float)
    fats = Column(Float)
    image_path = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="meals")

class BodyMetric(Base):
    __tablename__ = "body_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    weight_kg = Column(Float)
    body_fat_percentage = Column(Float, nullable=True)
    muscle_mass = Column(Float, nullable=True)
    source = Column(String, default="manual") # manual, smart_scale

    user = relationship("User", back_populates="body_metrics")

class DailySummary(Base):
    __tablename__ = "daily_summary"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date, default=datetime.utcnow().date)
    total_calories_in = Column(Float, default=0.0)
    total_calories_out = Column(Float, default=0.0)
    total_protein = Column(Float, default=0.0)
    workout_count = Column(Integer, default=0)
    weight_kg = Column(Float, nullable=True)

    user = relationship("User", back_populates="daily_summaries")
