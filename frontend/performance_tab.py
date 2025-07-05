import streamlit as st
from sqlmodel import Session, select
import requests
from datetime import date, datetime
from backend.models.enumeration import Role
from backend.models.user import User
from backend.models.performance import Performance
from backend.database import engine
from helpers import *


API_URL = "http://localhost:8000"

# --- Mapping ---
sport_disciplines = {
    "Volley-ball": ["Attaque", "Digs", "Recep", "Service - Ace", "Service - réussis", "Contre"],
    "Athlétisme": ["Muscu - Force", "Muscu - Puissance", "Muscu - Explosivité", "Décathlon", "100m", "Longueur", "Poids", "Hauteur", "400m", "110mH", "Disque", "Perche", "Javelot", "1500m", "Heptathlon", "60m", "60mH", "1000m", "200m", "400mH", "800m", "3000m", "3000m Steeple", "5000m", "10k", "Semi-marathon", "Marathon", "Marteau", "Triple-Saut"],
    "Mobilité": ["GE Facial", "GE Frontal Gauche", "GE Frontal Droit", "Hand-to-toes"]
}
unites = ["centimètres", "secondes", "points"]
meteo_mapping = ["Canicule", "Soleil", "Nuageux", "Venteux", "Pluvieux", "Orageux", "Intérieur"]

def performance_tab():
    st.title("Performances Lab")
    display_performances()
    st.divider()
    compute_performance_scoring()
    st.divider()
    add_performance()
    
def display_performances():    

    with Session(engine) as session:
        # --- Athlete selector --- 
        athletes = session.exec(select(User).where(User.role == Role.Athlete)).all()
        athlete_options = {f"{a.name}": a.id for a in athletes}
        selected_athlete_label = st.selectbox("Sélectionnez un·e athlète", [""] + list(athlete_options.keys()))
        selected_athlete_id = athlete_options.get(selected_athlete_label)

        if not selected_athlete_id:
            st.info("Veuillez sélectionner un·e athlète pour afficher les performances.")
            return

        # --- Get performances of the selected athlete ---
        query = select(Performance).where(Performance.user_id == selected_athlete_id)
        performances_ids = [r.id for r in session.exec(query).all()]
        
        if not performances_ids:
            st.info("No performances found for this athlete.")
        
        base_query = select(Performance).where(Performance.id.in_(performances_ids))
        all_perfs = session.exec(base_query).all()

        
        with st.expander("Filters", expanded=True):
            col1, col2 = st.columns(2)
            
            # Save old filter values from session state
            previous_sport = st.session_state.get("previous_sport_filter", "Tous")
            previous_discipline = st.session_state.get("previous_discipline_filter", "Toutes")
            
            # --- Sport Filter ---
            with col1:
                sport_filter = st.selectbox("Sport", ["Tous"] + sorted({p.sport.value for p in all_perfs}))

            # Discipline Filter
            with col2:
                if sport_filter == "Tous":
                    discipline_options = sorted({p.discipline for p in all_perfs})
                else:
                    discipline_options = sorted({p.discipline for p in all_perfs if p.sport.value == sport_filter})
                discipline_filter = st.selectbox("Discipline", ["Toutes"] + discipline_options)
            
            # Detect change and reset page if needed
            if (sport_filter != previous_sport or discipline_filter != previous_discipline):
                st.session_state["current_page"] = 1

            # Store new filter values for next run
            st.session_state["previous_sport_filter"] = sport_filter
            st.session_state["previous_discipline_filter"] = discipline_filter
            
        # --- Apply filters ---
        query = select(Performance).where(Performance.user_id == selected_athlete_id)
        if sport_filter != "Tous":
            query = query.where(Performance.sport == sport_filter)
        if discipline_filter != "Toutes":
            query = query.where(Performance.discipline == discipline_filter)

        filtered_perfs = session.exec(query).all()

        # --- Pagination ---
        performances_per_page = 6
        total_pages = (len(filtered_perfs) - 1) // performances_per_page + 1 if filtered_perfs else 1
        current_page = st.session_state.get("current_page", 1)
        
        if total_pages > 1:
            st.markdown("---")
        
        start_idx = (current_page -1) * performances_per_page
        end_idx = start_idx + performances_per_page
        performances_to_show = filtered_perfs[start_idx:end_idx]
        
        # Headers row
        cols = st.columns([1, 1, 1, 1, 2, 2, 2])
        headers = ['Date', 'Discipline', 'Performance', 'Météo', 'Remarques Techniques', 'Remarques Physiques', 'Remarques Mentales']
        for col, header in zip(cols, headers):
            col.markdown(f"**{header}**")
        st.markdown("---")
        
        # Performances rows
        for perf_ in performances_to_show:
            cols = st.columns([1, 1, 1, 1, 2, 2, 2])
            cols[0].write(perf_.date)
            cols[1].write(perf_.discipline)
            cols[2].write(f"{perf_.performance} {perf_.unit}")
            cols[3].write(f"{perf_.meteo.value} ({perf_.temperature}°C)")
            cols[4].write(f"{clip_text(perf_.technical_cues, 100)}")
            cols[5].write(f"{clip_text(perf_.physical_cues, 100)}")
            cols[6].write(f"{clip_text(perf_.mental_cues, 100)}")
        
        # --- Pagination control ---
        if total_pages > 1:
            st.write(f"Page {current_page} of {total_pages}")
            
            _, center_col, _ = st.columns([1, 1, 1])
            with center_col:
                cols = st.columns(total_pages)
                for i in range(total_pages):
                    page_num = i + 1
                    
                    button_label = f"**{page_num}**" if page_num == current_page else str(page_num)
                    if cols[i].button(button_label, key=f"page_button_{page_num}"):
                        st.session_state["current_page"] = page_num
                        
def compute_performance_scoring():
    st.subheader("Hungarian Scoring Table")
    

def add_performance():
    # Enregistrer nouvelles performances
    st.subheader("Ajouter une performance")
    
    with Session(engine) as session:
        athletes = session.exec(select(User).where(User.role == Role.Athlete)).all()

    selected_sport = st.selectbox("Sport", list(sport_disciplines.keys()), key="sport_selector")
    selected_discipline = st.selectbox("Discipline", sport_disciplines.get(selected_sport, []), key="discipline_selector")
    with st.form("add_performance"):
        selected_athlete = st.selectbox("Athlète", athletes, format_func=lambda a: a.name)
        
        perf_date = st.date_input("Date", value=date.today())
        perf_mark = st.text_input("Performance")
        perf_unit = st.selectbox("Unité", unites)
        temperature = st.number_input("Température", min_value=-40, max_value=60, value=25)
        meteo = st.selectbox("Conditions météo", meteo_mapping)
        technique = st.text_area("Points techniques", placeholder="ex: bon départ, bras désynchronisés...")
        physique = st.text_area("Points physiques", placeholder="ex: jambes lourdes, manque de puissance...")
        mental = st.text_area("Points mentaux", placeholder="ex: trop réfléchi, douleur fantôme déconcentrante...")

        submitted = st.form_submit_button("Enregistrer")
        if submitted:
            payload = {
                "user_id": selected_athlete.id,
                "date": str(perf_date),
                "sport": selected_sport,
                "discipline": selected_discipline,
                "performance": perf_mark,
                "unit": perf_unit,
                "temperature": temperature,
                "meteo": meteo,
                "technical_cues": technique,
                "physical_cues": physique,
                "mental_cues": mental,
            }
            resp = requests.post(f"{API_URL}/performances/", json=payload)
            if resp.status_code == 200:
                st.success("Performance enregistrée !")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("Échec de l'enregistrement.")