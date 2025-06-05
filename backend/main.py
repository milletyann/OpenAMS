# backend/main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import select, Session
from backend.models import Athlete, AthleteCreate
from backend.database import init_db, get_session
from typing import List

app = FastAPI()

# Initialize the database when app starts
@app.on_event("startup")
def on_startup():
    init_db()

# --- Récup tous les athlètes ---
@app.get("/athletes/", response_model=List[Athlete])
def read_athletes(session: Session = Depends(get_session)):
    statement = select(Athlete)
    return session.exec(statement).all()

# --- Créer un.e athlète
@app.post("/athletes/", response_model=Athlete)
def create_athlete(athlete: AthleteCreate, session: Session = Depends(get_session)):
    new_athlete = Athlete.from_orm(athlete)
    session.add(new_athlete)
    session.commit()
    session.refresh(new_athlete)
    return new_athlete

# --- Mettre à jour un.e athlète ---
@app.put("/athletes/{athlete_id}", response_model=Athlete)
def update_athlete(athlete_id: int, athlete: AthleteCreate, session: Session = Depends(get_session)):
    db_athlete = session.get(Athlete, athlete_id)
    if not db_athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")

    db_athlete.name = athlete.name
    db_athlete.age = athlete.age
    db_athlete.sport = athlete.sport
    session.add(db_athlete)
    session.commit()
    session.refresh(db_athlete)
    return db_athlete


# --- Supprimer un.e athlète ---
# --- Delete Athlete ---
@app.delete("/athletes/{athlete_id}")
def delete_athlete(athlete_id: int, session: Session = Depends(get_session)):
    db_athlete = session.get(Athlete, athlete_id)
    if not db_athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")

    session.delete(db_athlete)
    session.commit()
    return {"message": "Athlete deleted"}