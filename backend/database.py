# backend/database.py
from sqlmodel import create_engine, SQLModel, Session
from backend.models.user import User, UserCreate
from backend.models.performance import Performance
from backend.models.training import TrainingSession, UserTrainingLinks, CoachTrainingLinks
from backend.models.health_check import HealthCheck
from backend.models.injury_ticket import PhysicalIssueTicket, PhysicalIssueFollowUp
from backend.models.decathlon import Decathlon, DecathlonPerformance, DecathlonAthleteLink

#engine = create_engine(DATABASE_URL, echo=True, echo_pool=True)

# DB Permanent
PERMANENT_DB_URL = "sqlite:///backend/data/database.db"
engine_permanent = create_engine(PERMANENT_DB_URL, echo=False)

# DB Annuelle de saison
SEASON_DB_URL = "sqlite:///backend/data/season2526.db"
engine_season = create_engine(SEASON_DB_URL, echo=False)


def create_permanent_tables():
    SQLModel.metadata.create_all(engine_permanent, tables=[
        User.__table__,
        Performance.__table__,
        Decathlon.__table__,
        DecathlonPerformance.__table__,
        DecathlonAthleteLink.__table__,
    ])

def create_season_tables():
    SQLModel.metadata.create_all(engine_season, tables=[
        TrainingSession.__table__,
        UserTrainingLinks.__table__,
        CoachTrainingLinks.__table__,
        HealthCheck.__table__,
        PhysicalIssueTicket.__table__,
        PhysicalIssueFollowUp.__table__,
    ])
    
def get_session_permanent():
    return Session(engine_permanent)

def get_session_season():
    return Session(engine_season)