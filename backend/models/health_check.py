from sqlmodel import SQLModel, Field, UniqueConstraint
from typing import Optional
import datetime

class HealthCheck(SQLModel, table=True):
    __tablename__ = "health_check"
    __table_args__ = (UniqueConstraint("date", "athlete_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    date: datetime.date
    athlete_id: int

    muscle_soreness: int
    sleep_quality: int
    energy_level: int
    mood: str

    resting_heart_rate: Optional[int] = None
    hand_grip_test: Optional[float] = None
    longest_expiration_test: Optional[float] = None
    notes: Optional[str] = None
