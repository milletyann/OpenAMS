# backend/database.py
from sqlmodel import create_engine, SQLModel, Session

DATABASE_URL = "sqlite:///backend/data/athletes.db"
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    return Session(engine)
