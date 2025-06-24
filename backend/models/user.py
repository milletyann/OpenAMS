from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from backend.models.enumeration import Role, Sexe, Sport
from .training import UserTrainingLinks, CoachTrainingLinks

if TYPE_CHECKING:
    from .performance import Performance

# --- User ---
class UserBase(SQLModel):
    name: str
    role: Role
    sport: Sport
    age: int
    sexe: Sexe

class UserCreate(UserBase):
    pass

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    training_sessions: List["UserTrainingLinks"] = Relationship(back_populates="user")
    coaches_supervising: List["CoachTrainingLinks"] = Relationship(back_populates="coach")
    performances: List["Performance"] = Relationship(back_populates="user")