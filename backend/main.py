from fastapi import FastAPI, Depends, HTTPException, Request, Form#, APIRouter, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse


#from typing import Optional

from sqlmodel import select, Session
from backend.models import User, UserCreate, TrainingSession, UserTrainingLinks, Performance, HealthCheck, CoachTrainingLinks
from backend.models.injury_ticket import PhysicalIssueTicket, PhysicalIssueFollowUp, InjuryType, BodyArea
from backend.models.decathlon import Decathlon, DecathlonPerformance, DecathlonAthleteLink
from backend.models.enumeration import Role
from backend.database import init_db, get_session
from typing import List

from datetime import date
from pydantic import BaseModel
from backend.assets.hungarian import compute_hungarian_score

app = FastAPI()

origins = [
    "http://localhost:8501",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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

# Récuperer un user précis
@app.get("/users/{user_id}")
def get_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# --- Récup tou.te.s les athlètes ---
@app.get("/athletes", response_model=List[User])
def read_athletes(session: Session = Depends(get_session)):
    return session.exec(
        select(User)
        .where(User.role == Role.Athlete)
    ).all()


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

# --- Lister les séances d'un.e athlète entre 2 dates spécifiques ---
@app.get("/training_data")
def get_training_data(user_id: int, start_date: date, end_date: date, session: Session = Depends(get_session)):
    training_links = session.exec(
        select(UserTrainingLinks).where(UserTrainingLinks.user_id == user_id)
    ).all()

    training_ids = [link.training_id for link in training_links]
    
    if not training_ids:
        return []
    
    trainings = session.exec(
        select(TrainingSession)
        .where(TrainingSession.id.in_(training_ids))
        .where(TrainingSession.date >= start_date)
        .where(TrainingSession.date <= end_date)
    ).all()

    return [
        {
            "date": t.date,
            "duration": t.duration_minutes,
            "intensity": t.intensity,
            "sport": t.sport,
            "type": t.type,
        }
        for t in trainings
    ]


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

@app.post("/performances/delete")
def delete_performance(
    performance_id: int = Form(...),
    session: Session = Depends(get_session)
):
    perf = session.get(Performance, performance_id)
    if not perf:
        return JSONResponse({"detail": "Performance not found."}, status_code=404)
    
    session.delete(perf)
    session.commit()
    return JSONResponse({"detail": "Performance deleted."}, status_code=200)

class ScoreRequest(BaseModel):
    event: str
    sex: str
    perf: float
class ScoreResponse(BaseModel):
    score: int

@app.post("/compute_hungarian_score", response_model=ScoreResponse)
def compute_score_api(data: ScoreRequest):
    try:
        # For simplicity, assume only one performance
        score = compute_hungarian_score(
            event=data.event,
            sex=data.sex,
            perf=data.perf
        )
        return ScoreResponse(score=score)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.get("/get_pb")
def get_pb(user_id: int, discipline: str, session: Session = Depends(get_session)):
    query = (
        select(Performance)
        .where(Performance.user_id == user_id)
        .where(Performance.discipline == discipline)
    )

    perfs = session.exec(query).all()

    if not perfs:
        return {
            "performance": 0,
            "score": 0,
            "unit": None,
            "date": None
        }

    best_perf = max(perfs, key=lambda p: p.score)

    return {
        "performance": best_perf.performance,
        "score": best_perf.score,
        "unit": getattr(best_perf, "unit", None),
        "date": best_perf.date if hasattr(best_perf, "date") else None,
    }

# === DECATHLON === #
# Récupérer les Compétitions
@app.get("/decathlons")
def get_all_decathlons(session: Session = Depends(get_session)):
    return session.query(Decathlon).all()

# Récupérer les performances d'une certaine compétition
@app.get("/decathlon_performances")
def get_decathlon_performances(decathlon_id: int, session: Session = Depends(get_session)):
    return session.query(DecathlonPerformance).filter(
        DecathlonPerformance.decathlon_id == decathlon_id
    ).all()
    
# Récupérer les id d'athlètes qui sont notés dans un certain décathlon
@app.get("/athletes_in_decathlon")
def get_decathlon_athletes(decathlon_id: int, session: Session = Depends(get_session)):
    return session.query(DecathlonAthleteLink).filter(
        DecathlonAthleteLink.decathlon_id == decathlon_id
    ).all()

# === HEALTH === #
# Créer un HealthCheck
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

# Récupérer les HealthCheck
@app.get("/health-checks/", response_model=list[HealthCheck])
def get_all_health_checks(session: Session = Depends(get_session)):
    statement = select(HealthCheck)
    results = session.exec(statement).all()
    return results

# Récupérer les HealthCheck d'un athlète précis
@app.get("/health-checks/by-athlete/{athlete_id}", response_model=list[HealthCheck])
def get_health_checks_by_athlete(athlete_id: int, session: Session = Depends(get_session)):
    statement = select(HealthCheck).where(HealthCheck.athlete_id == athlete_id)
    results = session.exec(statement).all()
    return results

# Créer un nouveau ticket
@app.post("/issues/", response_model=PhysicalIssueTicket)
def create_issue(ticket: PhysicalIssueTicket, session: Session = Depends(get_session)):
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket

# Ajouter un suivi de ticket
@app.post("/issues/{ticket_id}/followups/", response_model=PhysicalIssueFollowUp)
def add_followup(ticket_id: int, followup: PhysicalIssueFollowUp, session: Session = Depends(get_session)):
    ticket = session.get(PhysicalIssueTicket, ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    # Block duplicate date for same ticket
    existing = session.exec(select(PhysicalIssueFollowUp)
                            .where(PhysicalIssueFollowUp.ticket_id == ticket_id)
                            .where(PhysicalIssueFollowUp.date == followup.date)).first()
    if existing:
        raise HTTPException(400, "Follow-up already exists for this date")
    session.add(followup)
    session.commit()
    session.refresh(followup)
    return followup

# Récupérer les tickets d'un athlète
@app.get("/athletes/{athlete_id}/issues/", response_model=list[PhysicalIssueTicket])
def get_athlete_issues(athlete_id: int, session: Session = Depends(get_session)):
    return session.exec(select(PhysicalIssueTicket).where(PhysicalIssueTicket.athlete_id == athlete_id)).all()

# Récupérer tous les suivis pour un ticket
@app.get("/issues/{ticket_id}/followups/", response_model=list[PhysicalIssueFollowUp])
def get_issue_followups(ticket_id: int, session: Session = Depends(get_session)):
    return session.exec(select(PhysicalIssueFollowUp).where(PhysicalIssueFollowUp.ticket_id == ticket_id).order_by(PhysicalIssueFollowUp.date)).all()
