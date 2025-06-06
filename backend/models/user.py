from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum


# --- Rôles ---
class Role(Enum):
    ATHLETE = "Athlète"
    COACH = "Coach"
    ADMIN = "Administrative"
    
class Sexe(Enum):
    M = "M"
    F = "F"
    NP = "Autre"

# --- User ---
class UserBase(SQLModel):
    name: str
    role: Role
    sport: str
    age: int
    sexe: Sexe

class UserCreate(UserBase):
    pass

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    training_sessions: List["UserTrainingLinks"] = Relationship(back_populates="user")
    coaches_supervising: List["CoachTrainingLinks"] = Relationship(back_populates="coach")