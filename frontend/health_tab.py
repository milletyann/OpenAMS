import streamlit as st
from sqlmodel import Session, select
import requests
import pandas as pd
from datetime import date, datetime, timedelta, time
from backend.models.enumeration import Role
from backend.models.user import User
from backend.models.injury_ticket import InjuryType, BodyArea
#from backend.database import engine
from backend.database import engine_permanent, engine_season

import locale
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

API_URL = "http://localhost:8000"

def health_tab():
    st.title("Santé")

    display_health_check()
    st.divider()
    display_issues()
    st.divider()
    
    col1, _, col2, _, col3 = st.columns([9, 1, 9, 1, 9])
    with col1:    
        add_daily_health_check()
    with col2:
        create_physical_issue()
    with col3:
        add_followup()
    
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

# Health check
def display_health_check():
    st.subheader("Check Santé Matinal - 7 derniers jours")

    athletes = fetch_athletes()

    if not athletes:
        st.warning("Aucun athlète trouvé. Veuillez d'abord créer un athlète.")
        return

    athlete_options = {a["name"]: a["id"] for a in athletes}

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
                "sleep_duration",
                "wakeup_time",
                "energy_level",
                "stress_level",
                "mood",
                "longest_expiration_test",
                "single_leg_proprio_test",
                "resting_heart_rate",
                "hand_grip_test",
                "notes",
            ]
            
            # Filter out missing columns (in case backend changes)
            df = df[[col for col in desired_columns if col in df.columns]]
            df = df.rename(columns={
                'date': 'date', 
                'muscle_soreness': 'Fatigue Msc', 
                "sleep_quality": "Qualité Som", 
                "sleep_duration": "Durée Som", 
                "wakeup_time": "Lever", 
                "energy_level": "Énergie",
                "stress_level": "Stress",
                "mood": "Humeur",
                "longest_expiration_test": "LET",
                "single_leg_proprio_test": "SLPT",
                "resting_heart_rate": "RHR",
                "hand_grip_test": "HGT",
                "notes": "Remarques",
            })
            
            if df.empty:
                st.info("Aucun bilan quotidien enregistré pour cet.te athlète.")
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
        
        athlete_name = st.selectbox("Select athlete", list(athlete_options.keys()))
        athlete_id = athlete_options[athlete_name]
        
        date_value = st.date_input("Date", value=date.today(), max_value=date.today())

        
        # sleep
        st.divider()
        st.subheader('Sommeil')
        sleep_quality = st.slider("Qualité du sommeil (1-10)", 0, 10, 5)
        sleep_duration = st.number_input(
            "Durée de sommeil",
            min_value=0.0,
            step=0.5,
            format="%.1f",
            placeholder="Optional",
        )
        wakeup_time = st.time_input("heure de réveil", time(7, 0))
        
        st.divider()
        st.subheader('Psychologie/Mental')
        stress_level = st.slider("Niveau de stress (1-10)", 0, 10, 0)

        mood = st.selectbox(
            "Mood",
            ["Joyeux", "Enthousiasme", "Motivé", "Neutre", "Las", "Stressé", "Triste"]
        )

        st.divider()
        st.subheader('Énergie/Fatigue')
        muscle_soreness = st.slider("Fatigue Musculaire (1-10)", 0, 10, 5)
        energy_level = st.slider("Niveau d'énergie (1-10)", 0, 10, 5)

        # tests
        st.divider()
        st.subheader('Tests qualitatifs')
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

        single_leg_proprio_test = st.number_input(
            "Test de proprioception sur une jambe (s)",
            min_value=0,
            format="%d",
            placeholder="Optional",
        )

        st.divider()
        st.subheader('Infos additionnelles')
        notes = st.text_area("Notes", placeholder="Optional")

        submitted = st.form_submit_button("Soumettre")

        if submitted:
            if date_value > date.today():
                st.error("Impossible de choisir une date future. Choisissez une date antérieure ou aujourd'hui.")
            else:
                payload = {
                    "date": date_value.isoformat(),
                    "athlete_id": athlete_id,
                    "muscle_soreness": muscle_soreness,
                    "sleep_quality": sleep_quality,
                    "sleep_duration": sleep_duration,
                    "wakeup_time": wakeup_time.strftime("%H:%M"),
                    "energy_level": energy_level,
                    "stress_level": stress_level,
                    "mood": mood,
                    "resting_heart_rate": resting_heart_rate if resting_heart_rate > 0 else None,
                    "hand_grip_test": hand_grip_test if hand_grip_test > 0 else None,
                    "longest_expiration_test": longest_expiration_test if longest_expiration_test > 0 else None,
                    "single_leg_proprio_test": single_leg_proprio_test if single_leg_proprio_test > 0 else None,
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
                        try:
                            st.error(f"Erreur: {response.json().get('detail')}")
                        except ValueError:
                            st.error(f"Erreur {response.status_code}: {response.text}")
                except Exception as e:
                    st.error(f"Requête échouée: {e}")

# Physical issue + Followup
def create_physical_issue():
    st.subheader("Créer un ticket de blessure")
    with Session(engine_permanent) as session:
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
                "notes": notes or None,
                "is_closed": False
            }
            resp = requests.post(f"{API_URL}/issues/", json=payload)
            if resp.status_code == 200:
                st.success("Ticket créé avec succès!")
            else:
                st.error(f"Erreur: {resp.json().get('detail')}")

def add_followup():
    st.subheader("Ajouter un suivi de blessure")
    with Session(engine_permanent) as session:
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
    
    athletes = fetch_athletes()
    if not athletes:
        st.warning("Aucun athlète trouvé. Veuillez d'abord créer un athlète.")
    athlete_map = {a["name"]: a["id"] for a in athletes}
    
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
    
    followups_sorted = sorted(followups, key=lambda x: x["date"], reverse=True)
    
    # Header row
    cols = st.columns([1, 1, 1, 3, 3])
    for c, h in zip(cols, ["Date", "Douleur", "Capacité", "Notes", "Traitements"]):
        c.markdown(f"**{h}**")
    st.markdown("---")
    
    for f in followups_sorted:
        cols = st.columns([1, 1, 1, 3, 3])
        cols[0].write(f["date"])
        cols[1].write(f["pain_intensity"])
        cols[2].write(f["capacity_restriction"])
        cols[3].write(f.get("status_notes", "—"))
        cols[4].write(f.get("treatments_applied", "—"))
