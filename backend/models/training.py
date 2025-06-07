# app/models/training.py
from typing import Optional, List
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
from datetime import date


class Sport(Enum):
    ATHLETISME = "Athletisme"
    VOLLEYBALL = "Volley-ball"

class TrainingSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sport: Sport
    type: str
    duration_minutes: Optional[int] = None
    date: date
    intensity: int
    notes: Optional[str] = None
    
    coach_id: Optional[int] = Field(default=None, foreign_key="user.id")
    
    users: List["UserTrainingLinks"] = Relationship(back_populates="training")
    coaches: List["CoachTrainingLinks"] = Relationship(back_populates="training")


class UserTrainingLinks(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    training_id: Optional[int] = Field(default=None, foreign_key="trainingsession.id", primary_key=True)

    user: "User" = Relationship(back_populates="training_sessions")
    training: "TrainingSession" = Relationship(back_populates="users")


class CoachTrainingLinks(SQLModel, table=True):
    coach_id: int = Field(default=None, foreign_key="user.id", primary_key=True)
    training_id: int = Field(default=None, foreign_key="trainingsession.id", primary_key=True)

    coach: "User" = Relationship(back_populates="coaches_supervising")
    training: "TrainingSession" = Relationship(back_populates="coaches")


from backend.models.user import User  # Do this at the bottom