from sqlalchemy import text
from sqlmodel import Session, create_engine

engine = create_engine("sqlite:///data/database.db")

with Session(engine) as session:
    session.execute(text("ALTER TABLE performance ADD COLUMN mental_cues TEXT"))
    session.commit()
