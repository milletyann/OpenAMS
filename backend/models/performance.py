from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import date
#from .user import User
from .enumeration import Sport
from enum import Enum

if TYPE_CHECKING:
    from .user import User

class ConditionMeteo(str, Enum):
    soleil = "Soleil"
    nuageux = "Nuageux"
    interieur = "Intérieur"
    canicule = "Canicule"
    venteux = "Venteux"
    pluvieux = "Pluvieux"
    orageux = "Orageux"

class Performance(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    date: str
    sport: Sport
    discipline: str
    performance: str
    unit: str
    score: float = Field(default=0)
    temperature: int
    meteo: ConditionMeteo
    technical_cues: Optional[str]
    physical_cues: Optional[str]
    mental_cues: Optional[str]
    
    user: Optional["User"] = Relationship(back_populates="performances")
