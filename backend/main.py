# backend/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select, Session
from backend.models import User, UserCreate, TrainingSession, UserTrainingLinks, Performance, HealthCheck, CoachTrainingLinks
from backend.models.enumeration import Role
from backend.database import init_db, get_session
from typing import List

app = FastAPI()

# Allow frontend calls (adjust your frontend URL if different)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the database when app starts
@app.on_event("startup")
def on_startup():
    init_db()



# === USERS === #
# --- Créer un.e user ---
# Le "/users/" qu'on met entre parenthèses est défini dans CES fonctions, on pourrait mettre ce qu'on veut mais c'est pour effectuer des requêtes autre part dans le code, pour pouvoir différencier des fonctions qui renvoient des résultats différents
# ex: récup tous les users et récup tous les athlètes
@app.post("/users/", response_model=User)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    new_user = User.from_orm(user)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

# --- Récup tous les users ---
@app.get("/users/", response_model=List[User])
def read_users(session: Session = Depends(get_session)):
    statement = select(User)
    return session.exec(statement).all()

# --- Récup tou.te.s les athlètes ---
@app.get("/athletes", response_model=List[User])
def read_athletes(session: Session = Depends(get_session)):
    return session.exec(select(User).where(User.role == Role.Athlete)).all()


# --- Mettre à jour un.e user ---
@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, user: UserCreate, session: Session = Depends(get_session)):
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.name = user.name
    db_user.age = user.age
    db_user.sport = user.sport
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


# --- Supprimer un.e User ---
@app.delete("/users/{user_id}")
def delete_user(user_id: int, session: Session = Depends(get_session)):
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # First delete CoachTrainingLinks where the user is a coach
    session.query(CoachTrainingLinks).filter(
        CoachTrainingLinks.coach_id == user_id
    ).delete()
    
    # Optionally, delete UserTrainingLinks if needed:
    session.query(UserTrainingLinks).filter(
        UserTrainingLinks.user_id == user_id
    ).delete()

    session.delete(db_user)
    session.commit()
    return {"message": "User deleted"}




# === TRAINING === #
# --- Créer une session d'entraînement ---
@app.post("/trainings/", response_model=TrainingSession)
def create_training(
    athlete_ids: List[int],  # IDs des athlètes à assigner
    training: TrainingSession,
    session: Session = Depends(get_session)
):
    # Vérifier que tous les athlètes existent
    athletes = session.exec(select(User).where(User.id.in_(athlete_ids))).all()
    if len(athletes) != len(athlete_ids):
        raise HTTPException(status_code=400, detail="Un ou plusieurs athlètes sont introuvables")

    # Ajouter la session
    session.add(training)
    session.commit()
    session.refresh(training)

    # Créer les liens
    for athlete in athletes:
        link = UserTrainingLinks(user_id=athlete.id, training_session_id=training.id)
        session.add(link)

    session.commit()
    return training

# --- Lister les sessions d’un.e athlète ---
@app.get("/users/{user_id}/trainings", response_model=List[TrainingSession])
def get_user_trainings(user_id: int, session: Session = Depends(get_session)):
    training_links = session.exec(
        select(UserTrainingLinks).where(UserTrainingLinks.user_id == user_id)
    ).all()
    
    training_ids = [link.training_id for link in training_links]
    
    if not training_ids:
        return []
    
    trainings = session.exec(
        select(TrainingSession).where(TrainingSession.id.in_(training_ids))
    ).all()
    
    return trainings


# === PERFORMANCE === #
@app.post("/performances/")
def create_performance(perf: Performance, session: Session = Depends(get_session)):
    session.add(perf)
    session.commit()
    session.refresh(perf)
    return perf

@app.get("/performances/")
def get_performances(session: Session = Depends(get_session)):
    return session.exec(select(Performance)).all()


# === HEALTH === #

# CREATE HealthCheck
@app.post("/health-checks/", response_model=HealthCheck)
def create_health_check(health_check: HealthCheck, session: Session = Depends(get_session)):
    # Check for duplicate record
    statement = select(HealthCheck).where(
        (HealthCheck.date == health_check.date) &
        (HealthCheck.athlete_id == health_check.athlete_id)
    )
    existing = session.exec(statement).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="A health check already exists for this athlete on this date."
        )
    session.add(health_check)
    session.commit()
    session.refresh(health_check)
    return health_check

# GET all HealthChecks
@app.get("/health-checks/", response_model=list[HealthCheck])
def get_all_health_checks(session: Session = Depends(get_session)):
    statement = select(HealthCheck)
    results = session.exec(statement).all()
    return results

# GET HealthChecks for one athlete
@app.get("/health-checks/by-athlete/{athlete_id}", response_model=list[HealthCheck])
def get_health_checks_by_athlete(athlete_id: int, session: Session = Depends(get_session)):
    statement = select(HealthCheck).where(HealthCheck.athlete_id == athlete_id)
    results = session.exec(statement).all()
    return results
