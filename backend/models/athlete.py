from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

# --- Athlète ---
class AthleteBase(SQLModel):
    name: str
    age: int
    sport: str
    sexe: str

class AthleteCreate(AthleteBase):
    pass

class Athlete(AthleteBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # "" pour TrainingSession pcq pas encore défini (qlq lignes plus bas), c'est une string forward reference
    # trainings: List["TrainingSession"] = Relationship(
    #     back_populates="athletes",
    #     link_model=AthleteTrainingLink,
    # )
    trainings: List["AthleteTrainingLink"] = Relationship(back_populates="athlete")