import streamlit as st
from sqlmodel import Session, select
import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent.parent))

from backend.database import engine
from backend.models.user import User
from backend.models.training import TrainingSession, UserTrainingLinks, CoachTrainingLinks
from datetime import date

def training_tab():
    st.title("Assign Training Session")

    with Session(engine) as session:
        # Fetch all athletes
        athletes = session.exec(select(User).where(User.role == "ATHLETE")).all()
        athlete_options = {f"{a.name} ({a.sport})": a.id for a in athletes}
        selected_names = st.multiselect("Select Athletes", options=list(athlete_options.keys()))
        
        # Fetch all coaches
        coaches = session.exec(select(User).where(User.role == "COACH")).all()
        coach_mapping = {f"{c.name} ({c.sport})": c.id for c in coaches}
        coach_display_options = ["None"] + list(coach_mapping.keys())
        selected_coach = st.selectbox("Assign Coach", options=coach_display_options)

        training_date = st.date_input("Training Date", value=date.today())
        duration = st.number_input("Duration (minutes)", min_value=0)
        session_type = st.text_input("Training Type")
        notes = st.text_area("Notes (optional)")

        if st.button("Create Training Session"):
            if not selected_names:
                st.warning("Please select at least one athlete.")
            # pas besoin de faire pareil avec les coach pcq coach n'est pas obligatoire
            else:
                new_session = TrainingSession(
                    date=training_date,
                    duration_minutes=duration,
                    type=session_type,
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
