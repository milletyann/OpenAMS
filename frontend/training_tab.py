import streamlit as st
from sqlmodel import Session, select
import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent.parent))

from backend.database import engine
from backend.models.athlete import Athlete
from backend.models.training import TrainingSession, AthleteTrainingLink
from datetime import date

def training_tab():
    st.title("Assign Training Session")

    with Session(engine) as session:
        # Fetch all athletes
        athletes = session.exec(select(Athlete)).all()

        athlete_options = {f"{a.name} (ID {a.id})": a.id for a in athletes}
        selected_names = st.multiselect("Select Athletes", options=list(athlete_options.keys()))

        training_date = st.date_input("Training Date", value=date.today())
        duration = st.number_input("Duration (minutes)", min_value=0)
        session_type = st.text_input("Training Type")
        notes = st.text_area("Notes (optional)")

        if st.button("Create Training Session"):
            if not selected_names:
                st.warning("Please select at least one athlete.")
            else:
                new_session = TrainingSession(
                    date=training_date,
                    duration_minutes=duration,
                    type=session_type,
                    notes=notes,
                )
                session.add(new_session)
                session.flush()  # get session.id before committing

                # Link selected athletes
                for name in selected_names:
                    athlete_id = athlete_options[name]
                    link = AthleteTrainingLink(
                        athlete_id=athlete_id,
                        training_id=new_session.id,
                    )
                    session.add(link)

                session.commit()
                st.success(f"Training session created and linked to {len(selected_names)} athletes.")
