# app/models/training.py
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import date


class TrainingSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: date
    duration_minutes: Optional[int] = None
    type: str

    notes: Optional[str] = None

    athletes: List["AthleteTrainingLink"] = Relationship(back_populates="training")


class AthleteTrainingLink(SQLModel, table=True):
    athlete_id: Optional[int] = Field(default=None, foreign_key="athlete.id", primary_key=True)
    training_id: Optional[int] = Field(default=None, foreign_key="trainingsession.id", primary_key=True)

    athlete: "Athlete" = Relationship(back_populates="trainings")
    training: "TrainingSession" = Relationship(back_populates="athletes")



from backend.models.athlete import Athlete  # Do this at the bottom