# frontend/health_page.py

import streamlit as st
from sqlmodel import Session, select
import requests
import pandas as pd
from datetime import date
from backend.models.enumeration import Role
from backend.models.user import User
from backend.database import engine

API_URL = "http://localhost:8000"  # adjust to your backend

def health_tab():
    st.title("Health")

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
    st.subheader("Morning Health Check - 7 derniers jours")

    athletes = fetch_athletes()

    if not athletes:
        st.info("No athletes found.")
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
                    st.info("No health checks in the last 7 days for this athlete.")
                else:
                    st.dataframe(
                        last_week.sort_values("date", ascending=False),
                        use_container_width=True
                    )
        else:
            st.error("Failed to fetch health checks.")
    except Exception as e:
        st.error(f"Request failed: {e}")



def add_daily_health_check():
    st.subheader("Add Daily Health Check")

    athletes = fetch_athletes()

    if not athletes:
        st.warning("No athletes found. Please create athletes first.")
        return

    athlete_options = {athlete["name"]: athlete["id"] for athlete in athletes}

    with st.form("health_check_form", clear_on_submit=True):
        date_value = st.date_input("Date", value=date.today(), max_value=date.today())
        
        athlete_name = st.selectbox("Select athlete", list(athlete_options.keys()))
        athlete_id = athlete_options[athlete_name]

        muscle_soreness = st.slider("Muscle Soreness (1-10)", 1, 10, 5)
        sleep_quality = st.slider("Sleep Quality (1-10)", 1, 10, 5)
        energy_level = st.slider("Energy Level (1-10)", 1, 10, 5)

        mood = st.selectbox(
            "Mood",
            ["Neutral", "Happy", "Sad", "Stressed", "Excited"]
        )

        resting_heart_rate = st.number_input(
            "Resting Heart Rate (bpm)",
            min_value=0,
            step=1,
            format="%d",
            placeholder="Optional",
        )

        hand_grip_test = st.number_input(
            "Hand Grip Test (kg)",
            min_value=0.0,
            format="%.1f",
            placeholder="Optional",
        )

        longest_expiration_test = st.number_input(
            "Longest Expiration Test (s)",
            min_value=0.0,
            format="%.1f",
            placeholder="Optional",
        )

        notes = st.text_area("Notes", placeholder="Optional")

        submitted = st.form_submit_button("Submit")

        if submitted:
            if date_value > date.today():
                st.error("The date cannot be in the future. Please select today or an earlier date.")
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
                        st.success("Health check submitted successfully.")
                    else:
                        st.error(f"Error: {response.json().get('detail')}")
                except Exception as e:
                    st.error(f"Request failed: {e}")


