import streamlit as st
from sqlmodel import Session, select
import uuid
import sys
import pathlib
import requests
from helpers import *

sys.path.append(str(pathlib.Path(__file__).parent.parent))
st.set_page_config(layout="wide") # Pourquoi ici seulement et ça marche partout??
API_URL = "http://127.0.0.1:8000"

from backend.database import engine
from backend.models.user import User
from backend.models.enumeration import Role, Sport
from backend.models.training import TrainingSession, UserTrainingLinks, CoachTrainingLinks
from datetime import date, timedelta

def training_tab():
    st.title("Entraînements")
    display_trainings()
    st.divider()
    add_training_session()
    
def display_trainings():
    st.subheader("Historique des entraînements")

    with Session(engine) as session:
        # --- Select Athlete ---
        athletes = session.exec(select(User).where(User.role == Role.Athlete)).all()
        athlete_options = {f"{a.name}": a.id for a in athletes}
        selected_name = st.selectbox("Sélectionner un athlète", options= [""] + list(athlete_options.keys()))
        athlete_id = athlete_options.get(selected_name)
        
        if not athlete_id:
            st.info("Veuillez sélectionner un.e athlète pour afficher ses entraînements.")
            return

        # --- Get all training sessions linked to this athlete ---
        link_query = select(UserTrainingLinks.training_id).where(UserTrainingLinks.user_id == athlete_id)
        training_ids = [r for r in session.exec(link_query).all()]

        if not training_ids:
            st.info("Aucun entraînement trouvé pour cet athlète.")
            return

        # --- Base query ---
        base_query = select(TrainingSession).where(TrainingSession.id.in_(training_ids))
        all_sessions = session.exec(base_query).all()
        
        # --- Build Filters ---
        with st.expander("Filtres", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            # Save previous filter values
            previous_sport = st.session_state.get("selected_sport")
            previous_type = st.session_state.get("selected_type")
            previous_min_intensity = st.session_state.get("min_intensity")
            previous_max_intensity = st.session_state.get("max_intensity")
            previous_min_duration = st.session_state.get("min_duration")
            previous_max_duration = st.session_state.get("max_duration")
            previous_start_date = st.session_state.get("start_date")
            previous_end_date = st.session_state.get("end_date")
            previous_sort_by = st.session_state.get("selected_sort")
            
            # Sport filter
            with col1:
                selected_sport = st.selectbox(
                    "Sport",
                    options=[None] + list(Sport),
                    format_func=lambda x: x.value if x else "Tous sports"
                )

            # Filter training sessions by selected sport
            filtered_sessions = [s for s in all_sessions if (not selected_sport or s.sport == selected_sport)]

            # Training types available for this sport only
            available_types = sorted(set(s.type for s in filtered_sessions))
            with col2:
                selected_type = st.selectbox(
                    "Type d'entraînement",
                    options=["Tous"] + available_types
                )

            # Intensity range
            with col3:
                min_intensity, max_intensity = st.slider(
                    "Intensité", 1, 10, (1, 10)
                )

            col4, col5, col6 = st.columns(3)

            # Date range
            all_dates = [s.date for s in all_sessions]
            default_start = min(all_dates) if all_dates else date.today()
            default_end = max(all_dates) if all_dates else date.today()

            with col4:
                start_date = st.date_input("Date de début", value=default_start)

            with col5:
                end_date = st.date_input("Date de fin", value=default_end)
            
            # Duration range
            with col6:
                min_duration, max_duration = st.slider(
                    "Durée (min)", 5, 240, (5, 240), step=5
                )
            
            with st.container():
                sort_options = {
                    "Plus Récente": lambda s: s.date,
                    "Plus Intense": lambda s: s.intensity,
                    "Plus Longue": lambda s: s.duration_minutes,
                }
                selected_sort = st.selectbox("Trier les entraînements par", options=list(sort_options.keys()))
                reverse_sort = True  # All sorts are descending
            
                
            # Detect change and reset page if needed
            if (selected_sport != previous_sport
                or selected_type != previous_type
                or min_intensity != previous_min_intensity
                or max_intensity != previous_max_intensity
                or min_duration != previous_min_duration
                or max_duration != previous_max_duration
                or start_date != previous_start_date
                or end_date != previous_end_date
                or selected_sort != previous_sort_by
                ):
                st.session_state["current_page"] = 1
            
            # Store new filter values for next run
            st.session_state["selected_sport"] = selected_sport
            st.session_state["selected_type"] = selected_type
            st.session_state["min_intensity"] = min_intensity
            st.session_state["max_intensity"] = max_intensity
            st.session_state["min_duration"] = min_duration
            st.session_state["max_duration"] = max_duration
            st.session_state["start_date"] = start_date
            st.session_state["end_date"] = end_date
            st.session_state["selected_sort"] = selected_sort

        # --- Apply filters ---
        final_sessions = [
            s for s in filtered_sessions
            if (selected_type == "Tous" or s.type == selected_type)
            and (min_intensity <= s.intensity <= max_intensity)
            and (min_duration <= s.duration_minutes <= max_duration)
            and (start_date <= s.date <= end_date)
        ]
        
        # --- Sort Sessions ---
        sort_key = sort_options[selected_sort]
        final_sessions.sort(key=sort_key, reverse=reverse_sort)

        # --- Pagination ---
        sessions_per_page = 6
        total_pages = (len(final_sessions) - 1) // sessions_per_page + 1 if final_sessions else 1
        current_page = st.session_state.get("current_page", 1)

        if total_pages > 1:
            st.markdown("---")

        # Display trainings
        start_idx = (current_page - 1) * sessions_per_page
        end_idx = start_idx + sessions_per_page
        sessions_to_show = final_sessions[start_idx:end_idx]
        
        # Headers row
        cols = st.columns([1, 1, 1, 1, 1, 2])  # width ratios
        headers = ["Date", "Type", "Sport", "Durée", "Intensité", "Notes"]
        for col, header in zip(cols, headers):
            col.markdown(f"**{header}**")
        st.markdown("---")  # separator below header# Rows: each training session
        
        # Training session rows
        for session_ in sessions_to_show:
            cols = st.columns([1, 1, 1, 1, 1, 2])
            cols[0].write(session_.date)
            cols[1].write(session_.type)
            cols[2].write(session_.sport.value)
            color_d = duration_color(session_.duration_minutes)
            cols[3].markdown(
                f'<span style="color:{color_d}; font-weight:bold;">{session_.duration_minutes} minutes</span>',
                unsafe_allow_html=True,
            )
            color_i = intensity_color(session_.intensity)
            cols[4].markdown(
                f'<span style="color:{color_i}; font-weight:bold;">{session_.intensity}/10</span>',
                unsafe_allow_html=True,
            )
            cols[5].write(clip_text(session_.notes, 100))
        
        # --- Pagination control with numbered buttons (bottom only) ---
        if total_pages > 1:
            st.write(f"Page {current_page} sur {total_pages}")

            _, center_col, _ = st.columns([1, 1, 1])
            with center_col:
                cols = st.columns(total_pages)
                for i in range(total_pages):
                    page_num = i + 1
                    # Highlight the button of current page
                    button_label = f"**{page_num}**" if page_num == current_page else str(page_num)
                    if cols[i].button(button_label, key=f"page_button_{page_num}"):
                        st.session_state["current_page"] = page_num

def add_training_session():
    st.subheader("Créer un entraînement")

    # Types de séances selon le sport choisi
    session_types = {
        "Divers": ["Sport collectif", "Randonnée", "Sortie entre copains", "Sport de raquette"],
        "Volley-ball": ["Tactique", "Technique", "Match", "PPG", "Muscu", "Coordination"],
        "Athlétisme": ["Sprint - Technique", "Sprint - Lactique", "Course - Aérobie", "Sprint - Départ", "Sprint - Haies", "Saut - Technique", "Saut - Élan réduit", "Saut - Élan complet", "Saut - Prise de marques", "Saut - Courses d'élan", "Lancer - Technique", "Lancer - Élan complet", "Lancer - PPG", "Muscu - Force", "Muscu - Puissance", "Muscu - Explosivité", "PPG", "Compétition - Décathlon", "Compétition - 100m", "Compétition - Longueur", "Compétition - Poids", "Compétition - Hauteur", "Compétition - 400m", "Compétition - 110mH", "Compétition - Disque", "Compétition - Perche", "Compétition - Javelot", "Compétition - 1500m"],
        "Mobilité": ["Général", "Spécifique - Épaules", "Spécifique - Hanches", "Spécifique - Dos", "Spécifique - Jambes", "Spécifique - Bas du corps", "Spécifique - Haut du corps"],
    }
    
    with Session(engine) as session:
        # Sport entraîné
        sport = st.selectbox("Sport", options=list(Sport), format_func=lambda x: x.value, index=0)
        
        # Récup tous les athlètes
        athletes = session.exec(select(User).where(User.role == Role.Athlete)).all()
        athlete_options = {f"{a.name}": a.id for a in athletes}
        selected_names = st.multiselect("Sélectionner des athlètes", options=list(athlete_options.keys()))
        
        # Récup tous les coachs
        coaches = session.exec(select(User).where(User.role == Role.Coach)).all()
        coach_mapping = {f"{c.name} ({c.sport.value})": c.id for c in coaches}
        coach_display_options = ["Aucun"] + list(coach_mapping.keys())
        selected_coach = st.selectbox("Désigner un coach", options=coach_display_options)
    
        # Autres attributs
        session_type = st.selectbox("Type d'entraînement", options=session_types[sport])
        training_date = st.date_input("Date", value=date.today())
        
        duration = st.number_input("Durée (minutes)", min_value=5, max_value=240, step=10)
        intensity = st.slider("Intensité", 1, 10)
        notes = st.text_area("Notes")


        if st.button("Créer un entraînement"):
            if not selected_names:
                st.warning("Veuillez sélectionner au moins un atlhète.")
            if not sport:
                st.warning("Veuillez sélectionner un sport.")

            # pas besoin de faire pareil avec les coach pcq coach n'est pas obligatoire
            else:
                new_session = TrainingSession(
                    sport=sport,
                    type=session_type,
                    duration_minutes=duration,
                    date=training_date,
                    intensity=intensity,
                    notes=notes,
                    coach_id = None if selected_coach == "Aucun" else coach_mapping[selected_coach]
                )
                session.add(new_session)
                session.flush()

                # Link selected athletes
                for name in selected_names:
                    athlete_id = athlete_options[name]
                    link = UserTrainingLinks(
                        user_id=athlete_id,
                        training_id=new_session.id,
                    )
                    session.add(link)
                
                # Link selected coaches
                if selected_coach != "Aucun":
                    coach_id = coach_mapping[selected_coach]
                    link = CoachTrainingLinks(
                        coach_id=coach_id,
                        training_id=new_session.id,
                    )
                    session.add(link)

                session.commit()
                st.success(f"Entraînement créé et lié à {len(selected_names)} athlète(s).")

def edit_training_session():
    st.title("Modifier un entraînement")
                
########################
### HELPER FUNCTIONS ###
######################## 
                
def intensity_color(intensity: int) -> str:
    if 1 <= intensity <= 4:
        return "#00cd00"
    elif 5 <= intensity <= 6:
        return "#ffff00"
    elif 7 <= intensity <= 8:
        return "#ffa500"
    elif intensity == 9:
        return "#cd0000"
    elif intensity == 10:
        return "#8b0000"
    else:
        return "white"

def duration_color(duration: int) -> str:
    if 0 <= duration <= 45:
        return "#caf0f8"
    elif 45 < duration <= 90:
        return "#90e0ef"
    elif 90 < duration <= 120:
        return "#00b4d8"
    elif 120 < duration <= 150:
        return "#0077b6"
    elif 150 < duration:
        return "#03045e"
    else:
        return "white"