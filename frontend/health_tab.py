import streamlit as st
from sqlmodel import Session, select
import requests
import pandas as pd
from datetime import date
from backend.models.enumeration import Role
from backend.models.user import User
from backend.database import engine

API_URL = "http://localhost:8000"

def health_tab():
    st.title("Santé")

    display_health_check()
    st.divider()
    add_daily_health_check()
    
    
def fetch_athletes():
    """
    Fetch list of athletes from backend.
    """
    try:
        response = requests.get(f"{API_URL}/athletes")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to load athletes list.")
            return []
    except Exception as e:
        st.error(f"Error loading athletes: {e}")
        return []

def display_health_check():
    st.subheader("Check Santé Matinal - 7 derniers jours")

    athletes = fetch_athletes()

    if not athletes:
        st.info("Aucun athlète trouvé.")
        return

    athlete_options = {athlete["name"]: athlete["id"] for athlete in athletes}

    athlete_name = st.selectbox(
        "Sélectionnez un athlète",
        list(athlete_options.keys())
    )

    athlete_id = athlete_options[athlete_name]

    try:
        response = requests.get(f"{API_URL}/health-checks/by-athlete/{athlete_id}")
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            # Reorder and filter columns
            desired_columns = [
                "date",
                "muscle_soreness",
                "sleep_quality",
                "energy_level",
                "mood",
                "resting_heart_rate",
                "hand_grip_test",
                "longest_expiration_test",
                "notes",
            ]
            # Filter out missing columns (in case backend changes)
            df = df[[col for col in desired_columns if col in df.columns]]
            
            if df.empty:
                st.info("No health checks recorded yet for this athlete.")
            else:
                # Convert date to datetime
                df["date"] = pd.to_datetime(df["date"])
                df["date"] = df["date"].dt.strftime("%d %B %Y")
                
                last_week = df[pd.to_datetime(df["date"], format="%d %B %Y") > (pd.Timestamp.today() - pd.Timedelta(days=7))]
                
                if last_week.empty:
                    st.info("Aucun check santé dans les 7 derniers jours pour cet athlète.")
                else:
                    st.dataframe(
                        last_week.sort_values("date", ascending=False),
                        use_container_width=True
                    )
        else:
            st.error("Impossible de récupérer les checks santé.")
    except Exception as e:
        st.error(f"Requête échouée: {e}")



def add_daily_health_check():
    st.subheader("Ajouter un check santé quotidien")

    athletes = fetch_athletes()

    if not athletes:
        st.warning("Aucun athlète trouvé. Veuillez d'abord créer un athlète.")
        return

    athlete_options = {athlete["name"]: athlete["id"] for athlete in athletes}

    with st.form("health_check_form", clear_on_submit=True):
        date_value = st.date_input("Date", value=date.today(), max_value=date.today())
        
        athlete_name = st.selectbox("Select athlete", list(athlete_options.keys()))
        athlete_id = athlete_options[athlete_name]

        muscle_soreness = st.slider("Fatigue Musculaire (1-10)", 1, 10, 5)
        sleep_quality = st.slider("Qualité du sommeil (1-10)", 1, 10, 5)
        energy_level = st.slider("Niveau d'énergie (1-10)", 1, 10, 5)

        mood = st.selectbox(
            "Mood",
            ["Joyeux", "Enthousiasme", "Motivé", "Neutre", "Las", "Stressé", "Triste"]
        )

        resting_heart_rate = st.number_input(
            "Fréquence Cardiaque au repos (bpm)",
            min_value=0,
            step=1,
            format="%d",
            placeholder="Optional",
        )

        hand_grip_test = st.number_input(
            "Test du grip de main (kg)",
            min_value=0.0,
            format="%.1f",
            placeholder="Optional",
        )

        longest_expiration_test = st.number_input(
            "Test de la plus longue expiration (s)",
            min_value=0.0,
            format="%.1f",
            placeholder="Optional",
        )

        notes = st.text_area("Notes", placeholder="Optional")

        submitted = st.form_submit_button("Soumettre")

        if submitted:
            if date_value > date.today():
                st.error("Impossible de choisir une date future. Choisissez une date antérieure ou aujourd'hui.")
            else:
                payload = {
                    "date": str(date_value),
                    "athlete_id": athlete_id,
                    "muscle_soreness": muscle_soreness,
                    "sleep_quality": sleep_quality,
                    "energy_level": energy_level,
                    "mood": mood,
                    "resting_heart_rate": resting_heart_rate if resting_heart_rate > 0 else None,
                    "hand_grip_test": hand_grip_test if hand_grip_test > 0 else None,
                    "longest_expiration_test": longest_expiration_test if longest_expiration_test > 0 else None,
                    "notes": notes if notes else None,
                }

                # Remove optional fields if None
                payload = {k: v for k, v in payload.items() if v is not None}

                try:
                    response = requests.post(
                        f"{API_URL}/health-checks/",
                        json=payload
                    )
                    if response.status_code == 200:
                        st.success("Check santé enregistré avec succès.")
                    else:
                        st.error(f"Erreur: {response.json().get('detail')}")
                except Exception as e:
                    st.error(f"Requête échouée: {e}")


