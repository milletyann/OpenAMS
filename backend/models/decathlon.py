from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON
from typing import List, Optional, TYPE_CHECKING
from datetime import date
import uuid

if TYPE_CHECKING:
    from .user import User

class DecathlonPerformance(SQLModel, table=True):
    #id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    id: Optional[int] = Field(default=None, primary_key=True)
    #decathlon_id: uuid.UUID = Field(foreign_key="decathlon.id")
    decathlon_id: Optional[int] = Field(default=None, foreign_key="decathlon.id")
    #user_id: uuid.UUID = Field(foreign_key="user.id")
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    event: str
    performance: Optional[str] = None
    score: Optional[int] = None
    date: date


class Decathlon(SQLModel, table=True):
    #id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    id: Optional[int] = Field(default=None, primary_key=True)#, sa_column_kwargs={"autoincrement": True})
    name: str
    date: date

    athlete_links: List["DecathlonAthleteLink"] = Relationship(back_populates="decathlon")


class DecathlonAthleteLink(SQLModel, table=True):
    decathlon_id: Optional[int] = Field(default=None, foreign_key="decathlon.id", primary_key=True)
    #decathlon_id: uuid.UUID = Field(foreign_key="decathlon.id", primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    #user_id: uuid.UUID = Field(foreign_key="user.id", primary_key=True)

    decathlon: "Decathlon" = Relationship(back_populates="athlete_links")
    user: "User" = Relationship(back_populates="competition_links")