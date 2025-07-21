import streamlit as st
from sqlmodel import Session, select

from backend.database import engine
import requests
from datetime import date
from backend.models.user import User
from backend.models.enumeration import Role, Sport
from backend.models.decathlon import Decathlon, DecathlonPerformance, DecathlonAthleteLink

API_URL = "http://localhost:8000"

# --- Events --- #
decaH = ["100m", "Longueur", "Poids", "Hauteur", "400m", "110mH", "Disque", "Perche", "Javelot", "1500m"]
decaF = ["100m", "Longueur", "Poids", "Hauteur", "400m", "100mH", "Disque", "Perche", "Javelot", "1500m"]
decaHM = ["100m", "Longueur", "Poids", "Hauteur", "400m", "100mH", "Disque", "Perche", "Javelot", "1500m"]

throws = ['Disque', 'Javelot', 'Poids']
jumps = ['Longueur', 'Hauteur', 'Perche']
races = ['60m', '60mH', '100m', '100mH', '110mH', '200m', '400m', '800m', '1000m', '1500m']
events_athle = throws + jumps + races


def decathlon_tab():
    st.header("Suivi de Décathlon")
    st.markdown("---")
    
    if "decathlon_view" not in st.session_state:
        st.session_state.decathlon_view = None

    if st.session_state.decathlon_view is None:
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Afficher une compétition"):
                st.session_state.decathlon_view = "display"
        with col2:
            if st.button("Reprendre une compétition"):
                st.session_state.decathlon_view = "resume"
        with col3:
            if st.button("Nouvelle compétition"):
                st.session_state.decathlon_view = "create"

    elif st.session_state.decathlon_view == "display":
        display_competition()
    elif st.session_state.decathlon_view == "resume":
        resume_competition()
    elif st.session_state.decathlon_view == "create":
        create_competition()

def display_competition():
    st.subheader("Voir une compétition")
    st.info("Fonctionnalité à venir...")
    
    if st.button("Retour"):
        st.session_state.decathlon_view = None
        st.rerun()


def resume_competition():
    st.subheader("Continuer une compétition existante")
    st.info("Fonctionnalité à venir...")
    
    if st.button("Retour"):
        st.session_state.decathlon_view = None
        st.rerun()

# ------------------ Competition Creation ------------------
def create_competition():
    st.subheader("Créer une nouvelle compétition")
    with Session(engine) as session:
        athletes = session.exec(select(User).where(User.role == Role.Athlete)).all()

    athlete_options = {f"{a.name}": a for a in athletes}

    col_left, col_right = st.columns([7, 3])
    with col_left:
        selected_labels = st.multiselect("Sélectionnez les athlètes", list(athlete_options.keys()))
        selected_athletes = [athlete_options[label] for label in selected_labels]

    with col_right:
        if st.button("Démarrer la compétition") and selected_athletes:
            st.session_state["active_athletes"] = selected_athletes
            st.session_state["competition_data"] = {}  # structure: {user_id: {event: perf}}
            st.session_state["start_competition"] = True

    if st.session_state.get("start_competition"):
        render_decathlon_table()
    
    if st.button("Retour"):
        st.session_state.decathlon_view = None
        st.rerun()
        
    
# ------------------ Editable Table with Scoring ------------------
def render_decathlon_table():
    st.markdown("### Entrer les performances")
    competition_data = st.session_state.get("competition_data", {})
    active_athletes = st.session_state.get("active_athletes", [])

    for athlete in active_athletes:
        with st.expander(f"{athlete.name} ({athlete.sexe.value})"):
            cols = st.columns(5)
            row_data = competition_data.get(athlete.id, {})
            for idx, event in enumerate(events_athle):
                with cols[idx % 5]:
                    key = f"perf_{athlete.id}_{event}"
                    perf = st.text_input(event, key=key, value=row_data.get(event, ""))

                    if perf:
                        try:
                            perf_val = float(perf)
                            score = compute_score_remote(event, athlete.sexe.value, perf_val)
                            st.markdown(f"**Score**: {score}")
                            row_data[event] = perf
                        except ValueError:
                            st.warning("Entrée invalide")
            competition_data[athlete.id] = row_data

    st.session_state["competition_data"] = competition_data

    if st.button("Sauvegarder"):
        save_competition()

# ------------------ Compute Score ------------------
def compute_score_remote(event: str, sex: str, perf: float) -> int:
    score_payload = {
        "event": event,
        "sex": sex,
        "perf": perf
    }
    try:
        score_response = requests.post(
            f"{API_URL}/compute_hungarian_score/",
            json=score_payload
        )
        if score_response.status_code == 200:
            return score_response.json().get("score", 0)
        else:
            st.error(f"Erreur calcul du score : {score_response.status_code} - {score_response.text}")
            return 0
    except Exception as e:
        st.error(f"Erreur lors de l'appel au calcul du score : {e}")
        return 0

# ------------------ Save to Database ------------------
def save_competition():
    with Session(engine) as session:
        
        # 1. Create the competition
        comp = Decathlon(
            name=f"Compétition du {date.today()}",
            date=date.today(),
        )
        session.add(comp)
        session.commit()
        session.refresh(comp)
        
        
        # 2. Link athletes to this competition
        print()
        print(st.session_state["active_athletes"])
        print()
        for athlete in st.session_state["active_athletes"]:
            if not getattr(athlete, "id", None):
                st.error(f"L'athlète {athlete} n'a pas d'ID – skipping.")
                continue
            try:
                link = DecathlonAthleteLink(
                    decathlon_id=comp.id,
                    user_id=athlete.id
                )
                session.add(link)
            except Exception as e:
                st.error(f"Erreur lors du lien: {e}")
                continue
            # if not athlete.id:
            #     st.error(f"Pas d'ID pour l'athlète {athlete} — Skipping.")
            #     continue

            # # Add entry to link table
            # link = DecathlonAthleteLink(
            #     decathlon_id=comp.id,
            #     user_id=athlete.id
            # )
            # session.add(link)
        session.commit()

        # 3. Add performances for each athlete
        for athlete in st.session_state["active_athletes"]:
            user_id = athlete.id
            perf_data = st.session_state["competition_data"].get(user_id, {})

            for event, perf_str in perf_data.items():
                try:
                    perf_val = float(perf_str)
                    score = compute_score_remote(event, athlete.sexe.value, perf_val)

                    performance = DecathlonPerformance(
                        decathlon_id=comp.id,
                        user_id=user_id,
                        event=event,
                        performance=perf_val,
                        score=score,
                        date=date.today()
                    )
                    session.add(performance)

                except Exception as e:
                    st.warning(f"Erreur: {e} sur athlète {athlete.id} - Skipping")
                    continue
                
        # 4. Final commit
        session.commit()
        st.success("Compétition sauvegardée")