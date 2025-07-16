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
    "Athlétisme": ["Muscu - Force", "Muscu - Puissance", "Muscu - Explosivité", "Décathlon", "100m", "Longueur", "Poids", "Hauteur", "400m", "110mH", "Disque", "Perche", "Javelot", "1500m", "Heptathlon", "60m", "60mH", "1000m", "200m", "400mH", "800m", "3000m", "3000m Steeple", "5000m", "10k", "Semi-marathon", "Marathon", "Marteau", "Triple-Saut"],
    "Volley-ball": ["Attaque", "Digs", "Recep", "Service - Ace", "Service - réussis", "Contre"],
    "Mobilité": ["GE Facial", "GE Frontal Gauche", "GE Frontal Droit", "Hand-to-toes"]
}

throws = ['Disque', 'Javelot', 'Poids']
jumps = ['Longueur', 'Hauteur', 'Perche']
races = ['60m', '60mH', '100m', '100mH', '110mH', '200m', '400m', '800m', '1000m', '1500m']
events_athle = throws + jumps + races

unites = ["centimètres", "secondes", "points", "kg"]
meteo_mapping = ["Canicule", "Soleil", "Nuageux", "Venteux", "Pluvieux", "Orageux", "Intérieur"]

def performance_tab():
    st.title("Performance")
    display_performances()
    st.divider()
    hungarian_table()
    st.divider()
    add_performance()
    
def display_performances():    
    st.subheader("Historique des performances")
    with Session(engine) as session:
        # --- Athlete selector --- 
        athletes = session.exec(select(User).where(User.role == Role.Athlete)).all()
        athlete_options = {f"{a.name}": a.id for a in athletes}
        selected_athlete_label = st.selectbox("Sélectionnez un·e athlète", [""] + list(athlete_options.keys()), key="athlete_selectbox")
        selected_athlete_id = athlete_options.get(selected_athlete_label)

        if not selected_athlete_id:
            st.info("Veuillez sélectionner un·e athlète pour afficher les performances.")
            return

        # --- Get performances of the selected athlete ---
        query = select(Performance).where(Performance.user_id == selected_athlete_id)
        performances_ids = [r.id for r in session.exec(query).all()]
        
        if not performances_ids:
            st.info("Aucune performance n'a été trouvée pour cet athlète.")
            return
        
        base_query = select(Performance).where(Performance.id.in_(performances_ids))
        all_perfs = session.exec(base_query).all()

        with st.expander("Filtres", expanded=True):
            col1, col2 = st.columns(2)
            
            # Save old filter values from session state
            previous_sport = st.session_state.get("previous_sport_filter", "Tous")
            previous_discipline = st.session_state.get("previous_discipline_filter", "Toutes")
            
            # --- Sport Filter ---
            with col1:
                sport_filter = st.selectbox("Sport", ["Tous"] + sorted({p.sport.value for p in all_perfs}), key="sport_filter_selectbox")

            # Discipline Filter
            with col2:
                if sport_filter == "Tous":
                    discipline_options = sorted({p.discipline for p in all_perfs})
                else:
                    discipline_options = sorted({p.discipline for p in all_perfs if p.sport.value == sport_filter})
                discipline_filter = st.selectbox("Discipline", ["Toutes"] + discipline_options, key="discipline_filter_selectbox")
            
            # Filtre de tri par score
            sort_by = "Date Décroissante"
            if sport_filter == "Athlétisme":
                sort_by = st.selectbox(
                    "Trier",
                    ["Date Décroissante", "Date Croissante", "Score Décroissant", "Score Croissant"],
                    key="sort_selectbox"
                )
            else:
                sort_by = st.selectbox(
                    "Trier",
                    ["Date Décroissante", "Date Croissante"],
                    key="sort_selectbox_other"
                )
            
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
        
        # Trier les perfs
        if sort_by == "Date Décroissante":
            filtered_perfs.sort(key=lambda p: p.date or datetime.min, reverse=True)
        elif sort_by == "Date Croissante":
            filtered_perfs.sort(key=lambda p: p.date or datetime.min)
        elif sort_by == "Score Décroissant":
            filtered_perfs.sort(key=lambda p: p.score or 0, reverse=True)
        elif sort_by == "Score Croissant":
            filtered_perfs.sort(key=lambda p: p.score or 0)
        
        # --- Pagination ---
        performances_per_page = 6
        total_pages = (len(filtered_perfs) - 1) // performances_per_page + 1 if filtered_perfs else 1
        current_page = st.session_state.get("current_page", 1)
        
        if total_pages > 1:
            st.markdown("---")
        
        start_idx = (current_page - 1) * performances_per_page
        end_idx = start_idx + performances_per_page
        performances_to_show = filtered_perfs[start_idx:end_idx]
        
        # Headers row
        if sport_filter == "Athlétisme":
            cols = st.columns([1, 1, 1, 1, 2, 2, 2, 2])
            headers = ['Date', 'Discipline', 'Performance', 'Score', 'Météo', 'Remarques Techniques', 'Remarques Physiques', 'Remarques Mentales']
        else:
            cols = st.columns([1, 1, 1, 1, 2, 2, 2])
            headers = ['Date', 'Discipline', 'Performance', 'Météo', 'Remarques Techniques', 'Remarques Physiques', 'Remarques Mentales']

        for col, header in zip(cols, headers):
            col.markdown(f"<center><b>{header}</b></center>", unsafe_allow_html=True)
            

        st.markdown("---")
        
        # Performances rows
        for perf_ in performances_to_show:
            if sport_filter == "Athlétisme":
                cols = st.columns([1, 1, 1, 1, 2, 2, 2, 2])
                cols[0].write(perf_.date)
                cols[1].write(perf_.discipline)
                cols[2].write(f"{perf_.performance} {perf_.unit}")
                cols[3].write(perf_.score or 0)
                cols[4].write(f"{perf_.meteo.value} ({perf_.temperature}°C)")
                cols[5].write(f"{clip_text(perf_.technical_cues, 100)}")
                cols[6].write(f"{clip_text(perf_.physical_cues, 100)}")
                cols[7].write(f"{clip_text(perf_.mental_cues, 100)}")
            else:
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
            st.write(f"Page {current_page} sur {total_pages}")
            
            _, center_col, _ = st.columns([1, 1, 1])
            with center_col:
                cols = st.columns(total_pages)
                for i in range(total_pages):
                    page_num = i + 1
                    
                    button_label = f"**{page_num}**" if page_num == current_page else str(page_num)
                    if cols[i].button(button_label, key=f"page_button_{page_num}"):
                        st.session_state["current_page"] = page_num
                        
def hungarian_table():
    st.subheader("Table des points Décathlon")

    # Discipline selection
    discipline = st.selectbox(
        "Choisir une épreuve",
        events_athle
    )

    # Sex selection
    sexe = st.selectbox(
        "Choisir le sexe de l'athlète",
        ["M", "F"]
    )

    # Dynamic fields
    performance = {}

    if discipline in jumps + throws:
        distance = st.number_input("Distance (cm)", min_value=0.0, step=1.0)
        performance = distance
    
    elif discipline in races:
        time = st.number_input("Temps (s)", min_value=0.0)
        performance = time

    # Compute button
    if st.button("Calculer le score"):
        payload = {
            "event": discipline,
            "sex": sexe,
            "perf": performance
        }
        response = requests.post("http://localhost:8000/compute_hungarian_score/", json=payload)

        if response.status_code == 200:
            st.success(f"Score: {response.json()['score']}")
        else:
            st.error(f"Erreur: {response.json()['detail']}")

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
            # GET THE SEX OF THE ATHLETE HERE (I GUESS?)
            sex = selected_athlete.sexe.value
            # COMPUTE THE SCORE HERE (WE HAVE THE DISCIPLINE, THE SEX AND THE PERFORMANCE)
            if selected_discipline in events_athle:
                score_payload = {
                    "event": selected_discipline,
                    "sex": sex,
                    "perf": perf_mark
                }

                try:
                    score_response = requests.post(
                        f"{API_URL}/compute_hungarian_score/",
                        json=score_payload
                    )
                    if score_response.status_code == 200:
                        score = score_response.json().get("score", 0)
                    else:
                        st.error(f"Erreur calcul du score : {score_response.status_code} - {score_response.text}")
                        score = 0
                except Exception as e:
                    st.error(f"Erreur lors de l'appel au calcul du score : {e}")
                    score = 0

            else:
                score = 0
            
            
            payload = {
                "user_id": selected_athlete.id,
                "date": str(perf_date),
                "sport": selected_sport,
                "discipline": selected_discipline,
                "performance": perf_mark,
                "unit": perf_unit,
                "score": score, # FILL THE SCORE VARIABLE HERE
                "temperature": temperature,
                "meteo": meteo,
                "technical_cues": technique,
                "physical_cues": physique,
                "mental_cues": mental,
            }
            resp = requests.post(f"{API_URL}/performances/", json=payload)
            if resp.status_code == 200:
                st.success("Performance enregistrée !")
                st.info(f"Score calculé : {score}")
                #st.cache_data.clear()
                #st.rerun()
            else:
                st.error("Échec de l'enregistrement.")