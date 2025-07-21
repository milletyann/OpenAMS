import streamlit as st
from sqlmodel import Session, select
import requests
import pandas as pd
from datetime import date, datetime, timedelta
from backend.models.enumeration import Role
from backend.models.user import User
from backend.models.injury_ticket import InjuryType, BodyArea
from backend.database import engine

import locale
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

API_URL = "http://localhost:8000"

def health_tab():
    st.title("Santé")

    display_health_check()
    st.divider()
    add_daily_health_check()
    st.divider()
    create_physical_issue()
    st.divider()
    add_followup()
    st.divider()
    display_issues()
    
    
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
                        use_container_width=True,
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

        muscle_soreness = st.slider("Fatigue Musculaire (1-10)", 0, 10, 5)
        sleep_quality = st.slider("Qualité du sommeil (1-10)", 0, 10, 5)
        energy_level = st.slider("Niveau d'énergie (1-10)", 0, 10, 5)

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

def create_physical_issue():
    st.subheader("Créer un ticket de blessure")
    with Session(engine) as session:
        athletes = session.exec(select(User).where(User.role == Role.Athlete)).all()
    athlete_map = {a.name: a.id for a in athletes}
    
    with st.form("new_issue_form", clear_on_submit=True):
        athlete_name = st.selectbox("Athlète", options=list(athlete_map.keys()))
        date_opened = st.date_input("Date d'apparition", value=date.today())
        title = st.text_input("Nom")
        area = st.selectbox("Zone concernée", options=[area.value for area in BodyArea])
        injury = st.selectbox("Type de blessure", options=[inj.value for inj in InjuryType])
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Créer ticket")
        
        if submitted:
            payload = {
                "athlete_id": athlete_map[athlete_name],
                "date_opened": str(date_opened),
                "title": title,
                "area_concerned": area,
                "injury_type": injury,
                "notes": notes or None
            }
            resp = requests.post(f"{API_URL}/issues/", json=payload)
            if resp.status_code == 200:
                st.success("Ticket créé avec succès!")
            else:
                st.error(f"Erreur: {resp.json().get('detail')}")

def add_followup():
    st.subheader("Ajouter un suivi de blessure")
    with Session(engine) as session:
        athletes = session.exec(select(User).where(User.role == Role.Athlete)).all()
    athlete_map = {a.name: a.id for a in athletes}
    
    athlete_name = st.selectbox("Athlète", options=[""] + list(athlete_map.keys()))
    if not athlete_name:
        return
    
    athlete_id = athlete_map[athlete_name]
    issues = requests.get(f"{API_URL}/athletes/{athlete_id}/issues/").json()
    
    if not issues:
        st.info("Aucune blessure enregistrée pour cet.te athlète.")
        return
    
    
    issue_map = {f"{i['title']} (Depuis le {datetime.strptime(i['date_opened'], '%Y-%m-%d').strftime('%d %B %Y')})": i['id'] for i in issues}
    issue_label = st.selectbox("Sélectionner une blessure", options=[""] + list(issue_map.keys()))
    if not issue_label:
        return
    
    ticket_id = issue_map[issue_label]
    followups = requests.get(f"{API_URL}/issues/{ticket_id}/followups/").json()
    used_dates = {f["date"] for f in followups}
    
    selected_issue = next(i for i in issues if i["id"] == ticket_id)
    min_followup_date = date.fromisoformat(selected_issue["date_opened"])
    
    # Compute available dates
    all_dates = [
        (min_followup_date + timedelta(days=i)).isoformat()
        for i in range((date.today() - min_followup_date).days + 1)
    ]
    available_dates = sorted(set(all_dates) - used_dates)
    if not available_dates:
        st.info("Tous les jours entre la blessure et aujourd'hui ont déjà un suivi.")
        return

    default_date = date.fromisoformat(available_dates[-1])
    max_followup_date = default_date
    
    with st.form("followup_form", clear_on_submit=True):
        followup_date = st.date_input(
            "Date",
            value=default_date,
            min_value=min_followup_date,
            max_value=max_followup_date
        )
        
        pain = st.slider("Intensité de la douleur", 0, 10, 5)
        capacity = st.slider("Restriction de capacité", 0, 10, 5)
        notes = st.text_area("Notes")
        treatments = st.text_area("Traitements")
        submitted = st.form_submit_button("Enregistrer le suivi")
        
        if submitted:
            if followup_date.isoformat() not in available_dates:
                st.warning("Le suivi est déjà renseigné ce jour.")
            else:
                payload = {
                    "ticket_id": ticket_id,
                    "date": str(followup_date),
                    "pain_intensity": pain,
                    "capacity_restriction": capacity,
                    "status_notes": notes or None,
                    "treatments_applied": treatments or None
                }
                resp = requests.post(f"{API_URL}/issues/{ticket_id}/followups/", json=payload)
                if resp.status_code == 200:
                    st.success("Suivi enregistré.")
                else:
                    st.error(f"Erreur: {resp.json().get('detail')}")

def display_issues():
    st.subheader("Suivi des blessures")
    with Session(engine) as session:
        athletes = session.exec(select(User).where(User.role == Role.Athlete)).all()
    athlete_map = {a.name: a.id for a in athletes}
    
    athlete_name = st.selectbox("Athlète", options=[""] + list(athlete_map.keys()), key="disp_ai")
    if not athlete_name:
        return
    
    athlete_id = athlete_map[athlete_name]
    tickets = requests.get(f"{API_URL}/athletes/{athlete_id}/issues/").json()
    if not tickets:
        st.info("Aucune blessure enregistrée pour cet.te athlète.")
        return

    ticket_map = {f"{t['title']} (Depuis le {datetime.strptime(t['date_opened'], '%Y-%m-%d').strftime('%d %B %Y')})": t["id"] for t in tickets}
    t_label = st.selectbox("Sélectionner une blessure", options=[""] + list(ticket_map.keys()), key="disp_ti")
    if not t_label:
        return
    
    ticket_id = ticket_map[t_label]
    ticket = next(t for t in tickets if t["id"] == ticket_id)
    
    
    st.markdown(f"""
    **Nom:** {ticket['title']}  
    **Date d'apparition:** {ticket['date_opened']}  
    **Zone:** {ticket['area_concerned']}  
    **Type:** {ticket['injury_type']}  
    **Informations générales:** {ticket.get('notes', '—')}
    """)
    
    followups = requests.get(f"{API_URL}/issues/{ticket_id}/followups/").json()
    if not followups:
        st.info("Aucun suivi enregistré.")
        return
    
    # Header row
    cols = st.columns([1, 1, 1, 3, 3])
    for c, h in zip(cols, ["Date", "Douleur", "Capacité", "Notes", "Traitements"]):
        c.markdown(f"**{h}**")
    st.markdown("---")
    
    for f in followups:
        cols = st.columns([1, 1, 1, 3, 3])
        cols[0].write(f["date"])
        cols[1].write(f["pain_intensity"])
        cols[2].write(f["capacity_restriction"])
        cols[3].write(f.get("status_notes", "—"))
        cols[4].write(f.get("treatments_applied", "—"))
