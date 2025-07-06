from sqlalchemy import text
from sqlmodel import Session, create_engine, select

from backend.models import Performance
from backend.database import get_session
from backend.assets import compute_hungarian_score

engine = create_engine("sqlite:///data/database.db")

with Session(engine) as session:
    session.execute(text("ALTER TABLE performance ADD COLUMN score FLOAT NOT NULL DEFAULT 0;"))
    session.commit()