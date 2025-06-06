# backend/main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import select, Session
from backend.models import Athlete, AthleteCreate, TrainingSession, AthleteTrainingLink
from backend.database import init_db, get_session
from typing import List

app = FastAPI()

# Initialize the database when app starts
@app.on_event("startup")
def on_startup():
    init_db()


# === ATHLETES === #
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
@app.delete("/athletes/{athlete_id}")
def delete_athlete(athlete_id: int, session: Session = Depends(get_session)):
    db_athlete = session.get(Athlete, athlete_id)
    if not db_athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")

    session.delete(db_athlete)
    session.commit()
    return {"message": "Athlete deleted"}



# === TRAINING === #
# --- Créer une session d'entraînement ---
@app.post("/trainings/", response_model=TrainingSession)
def create_training(
    athlete_ids: List[int],  # IDs des athlètes à assigner
    training: TrainingSession,
    session: Session = Depends(get_session)
):
    # Vérifier que tous les athlètes existent
    athletes = session.exec(select(Athlete).where(Athlete.id.in_(athlete_ids))).all()
    if len(athletes) != len(athlete_ids):
        raise HTTPException(status_code=400, detail="Un ou plusieurs athlètes sont introuvables")

    # Ajouter la session
    session.add(training)
    session.commit()
    session.refresh(training)

    # Créer les liens
    for athlete in athletes:
        link = AthleteTrainingLink(athlete_id=athlete.id, training_session_id=training.id)
        session.add(link)

    session.commit()
    return training

# --- Lister toutes les sessions ---
@app.get("/trainings/", response_model=List[TrainingSession])
def read_trainings(session: Session = Depends(get_session)):
    return session.exec(select(TrainingSession)).all()


# --- Lister les sessions d’un.e athlète ---
@app.get("/athletes/{athlete_id}/trainings", response_model=List[TrainingSession])
def read_athlete_trainings(athlete_id: int, session: Session = Depends(get_session)):
    athlete = session.get(Athlete, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")
    return athlete.trainings
