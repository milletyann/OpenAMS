import streamlit as st
from sqlmodel import Session, select
import uuid
import sys
import pathlib
import requests

sys.path.append(str(pathlib.Path(__file__).parent.parent))
API_URL = "http://127.0.0.1:8000"

from backend.database import engine
from backend.models.user import User
from backend.models.training import TrainingSession, UserTrainingLinks, CoachTrainingLinks
from datetime import date


def training_tab():
    display_trainings()
    st.divider()
    add_training_session()

def display_trainings():
    st.title("Training History")
    
    athletes_response = requests.get(f"{API_URL}/athletes")
    if athletes_response.status_code == 200:
        athletes = athletes_response.json()
        athlete_options = {f"{a['name']}": a["id"] for a in athletes}

        selected_name = st.selectbox("Select an athlete", [""] + list(athlete_options.keys()))
        if selected_name:
            user_id = athlete_options[selected_name]
            
            # 2. Fetch and show past trainings
            trainings_response = requests.get(f"{API_URL}/users/{user_id}/trainings")
            if trainings_response.status_code == 200:
                trainings = trainings_response.json()

                if trainings:
                    st.subheader(f"📋 Past Trainings for {selected_name}")
                    st.dataframe(
                        [
                            {
                                "Date": t["date"],
                                "Sport": t["sport"],
                                "Type de Séance": t["type"],
                                "Durée (min)": t["duration_minutes"],
                                "Intensité": t["intensity"],
                                "Notes": t.get("notes", "")
                            }
                            for t in trainings
                        ]
                    )
                else:
                    st.info("No training sessions found for this athlete.")
            else:
                st.error("Failed to fetch trainings.")
    else:
        st.error("Failed to fetch athletes.")
    
    

def add_training_session():
    st.title("Create Training Session")

    # Types de séances selon le sport choisi
    session_types = {
        "Athletisme": ["Technique", "Lactique", "Aérobie", "Sprint", "Haies", "Élan Complet", "Muscu", "PPG", "Simulation Compétition"],
        "Volley-ball": ["Tactique", "Technique", "Simulation Match", "PPG", "Muscu", "Coordination"],
    }
    
    with Session(engine) as session:
        # Sport entraîné
        sport = st.selectbox("Sport", ["Athletisme", "Volley-ball"])
        
        # Récup tous les athlètes
        athletes = session.exec(select(User).where(User.role == "ATHLETE")).all()
        athlete_options = {f"{a.name} ({a.sport})": a.id for a in athletes}
        selected_names = st.multiselect("Select Athletes", options=list(athlete_options.keys()))
        
        # Récup tous les coachs
        coaches = session.exec(select(User).where(User.role == "COACH")).all()
        coach_mapping = {f"{c.name} ({c.sport})": c.id for c in coaches}
        coach_display_options = ["None"] + list(coach_mapping.keys())
        selected_coach = st.selectbox("Assign Coach", options=coach_display_options)
    
        # Autres attributs
        session_type = st.selectbox("Training Type", options=session_types[sport])
        training_date = st.date_input("Date", value=date.today())
        duration = st.number_input("Duration (minutes)", min_value=5, max_value=240, step=10)
        intensity = st.slider("Intensity", 1, 10)
        notes = st.text_area("Notes")


        if st.button("Create Training Session"):
            if not selected_names:
                st.warning("Please select at least one athlete.")
            # pas besoin de faire pareil avec les coach pcq coach n'est pas obligatoire
            else:
                new_session = TrainingSession(
                    sport=sport,
                    type=session_type,
                    duration_minutes=duration,
                    date=training_date,
                    intensity=intensity,
                    notes=notes,
                    coach_id = None if selected_coach == "None" else coach_mapping[selected_coach]
                )
                session.add(new_session)
                session.flush()  # get session.id before committing

                # Link selected athletes
                for name in selected_names:
                    athlete_id = athlete_options[name]
                    link = UserTrainingLinks(
                        user_id=athlete_id,
                        training_id=new_session.id,
                    )
                    session.add(link)
                
                # Link selected coaches
                if selected_coach != "None":
                    coach_id = coach_mapping[selected_coach]
                    link = CoachTrainingLinks(
                        coach_id=coach_id,
                        training_id=new_session.id,
                    )
                    session.add(link)

                session.commit()
                st.success(f"Training session created and linked to {len(selected_names)} athletes.")