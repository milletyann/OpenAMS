from sqlmodel import SQLModel, Field, UniqueConstraint
from typing import Optional
from datetime import date, time

class HealthCheck(SQLModel, table=True):
    __tablename__ = "health_check"
    __table_args__ = (UniqueConstraint("date", "athlete_id"),)

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False, sa_column_kwargs={"autoincrement": True})
    date: date
    athlete_id: int

    sleep_quality: int
    sleep_duration: float
    wakeup_time: time
    
    muscle_soreness: int
    energy_level: int
    
    stress_level: int
    mood: str

    resting_heart_rate: Optional[int] = None
    hand_grip_test: Optional[float] = None
    longest_expiration_test: Optional[float] = None
    single_leg_proprio_test: Optional[int] = None

    notes: Optional[str] = None


class HealthCheckCreate(SQLModel):
    date: date
    athlete_id: int
    
    sleep_quality: int
    sleep_duration: Optional[float] = None
    wakeup_time: Optional[time] = None
    
    muscle_soreness: int
    energy_level: int
    
    stress_level: Optional[int] = None
    mood: str
    
    resting_heart_rate: Optional[int] = None
    hand_grip_test: Optional[float] = None
    longest_expiration_test: Optional[float] = None
    single_leg_proprio_test: Optional[int] = None
    
    notes: Optional[str] = None
