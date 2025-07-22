import streamlit as st
from sqlmodel import Session, select

from backend.database import engine
import requests
from datetime import date
from backend.models.user import User
from backend.models.enumeration import Role, Sport
from backend.models.decathlon import Decathlon, DecathlonPerformance, DecathlonAthleteLink

import pandas as pd
import plotly.express as px

API_URL = "http://localhost:8000"

# --- Events --- #
decaH = ["100m", "Longueur", "Poids", "Hauteur", "400m", "110mH", "Disque", "Perche", "Javelot", "1500m"]
decaF = ["100m", "Longueur", "Poids", "Hauteur", "400m", "100mH", "Disque", "Perche", "Javelot", "1500m"]
decaHM = ["100m", "Longueur", "Poids", "Hauteur", "400m", "100mH", "Disque", "Perche", "Javelot", "1500m"]

unit_mapping = {
    "100m": "s",
    "Longueur": "m",
    "Poids": "m",
    "Hauteur": "m",
    "400m": "s",
    "110mH": "s",
    "100mH": "s",
    "Disque": "m",
    "Perche": "m",
    "Javelot": "m",
    "1500m": "min",
}


def decathlon_tab():
    st.header("Ma Compétition")
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

# ----------- Fetching database -----------
def fetch_all_decathlons():
    resp = requests.get(f"{API_URL}/decathlons")
    if resp.status_code == 200:
        return resp.json()
    return []

def fetch_performances(decathlon_id: int):
    resp = requests.get(f"{API_URL}/decathlon_performances?decathlon_id={decathlon_id}")
    if resp.status_code == 200:
        return resp.json()
    return []

def fetch_user(user_id: int):
    resp = requests.get(f"{API_URL}/users/{user_id}")
    if resp.status_code == 200:
        return resp.json()
    return None

@st.cache_data
def fetch_all_decathlons_cached():
    return fetch_all_decathlons()

@st.cache_data
def fetch_performances_cached(comp_id):
    return fetch_performances(comp_id)

@st.cache_data
def fetch_user_cached(uid):
    return fetch_user(uid)


# ----------------- Displaying section -------------------
def display_live_ranking(df_rank):
    fig = px.line(
        df_rank,
        x="Event",
        y="Rank",
        color="Athlete",
        markers=True,
        hover_data={
            "Athlete": True,
            "Sexe": False,
            "Intermédiaire": True,
            "Score": True,
            "Rank": False,
            "Event": False,
            "Missing": False
        },
        title="Évolution du classement général",
    )

    fig.update_yaxes(autorange="reversed", title="Rang")
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)


    # df_missing = df_rank[df_rank["Missing"]==True]
    
    # fig.add_scatter(
    # x=df_missing["Event"],
    # y=df_missing["Rank"],
    # mode="markers",
    # marker=dict(color="lightgrey", symbol="circle-open"),
    # name="Manquant",
    # text=df_missing["Athlete"],
    # hovertemplate=(
    #         "<b>%{text}</b><br>" +
    #         "Sexe: %{customdata[1]}<br>" +
    #         "Épreuve: %{x}<br>" +
    #         "Points sur l'épreuve: 0<br>" +
    #         "Points cumulés: %{customdata[0]}<br>" +
    #         "<extra></extra>"
    #     ),
    #     customdata=df_missing[["Score", "Sexe"]],
    #     showlegend=True,
    # )




def display_competition():
    competitions = fetch_all_decathlons_cached()
    if not competitions:
        st.warning("Aucune compétition trouvée.")
        return

    comp_options = {comp["name"]: comp for comp in competitions}
    selected_name = st.selectbox("Choisir une compétition", list(comp_options.keys()))
    selected_comp = comp_options[selected_name]

    performances = fetch_performances_cached(selected_comp["id"])
    if not performances:
        st.info("Aucune performance enregistrée pour cette compétition.")
        return

    # Group by athlete
    athlete_map = {}
    for perf in performances:
        uid = perf["user_id"]
        if uid not in athlete_map:
            user_data = fetch_user_cached(uid)
            athlete_map[uid] = {
                "user": user_data,
                "performances": {}
            }
        athlete_map[uid]["performances"][perf["event"]] = (perf["performance"], perf["score"])
        
    # Filter by sexe
    col1, col2, _ = st.columns([1, 1, 4])

    with col1:
        show_f = st.checkbox("Femmes", value=True)
    with col2:
        show_m = st.checkbox("Hommes", value=True)

    if not (show_f or show_m):
        st.warning("Veuillez sélectionner au moins un sexe.")
        st.stop()

    # Map to selected sexes
    selected_sexes = []
    if show_f:
        selected_sexes.append("F")
    if show_m:
        selected_sexes.append("M")


    # Compute cumulative ranking
    df_rank = compute_ranking(athlete_map, selected_sexes)
    display_live_ranking(df_rank)
    
    html = """
        <style>
            .sticky-table th {
                position: sticky;
                top: 0;
                z-index: 1;
            }
        </style>
        <table class="sticky-table" style='border-collapse: collapse; width: 100%; text-align: center;'>
        """

    # --- Header row ---
    html += "<tr><th style='border: 1px solid black;'>Athlètes</th>"
    for event in decaH:
        if event == "110mH":
            html += f"<th style='border: 1px solid black;'>{event}/100mH</th>"
        else:
            html += f"<th style='border: 1px solid black;'>{event}</th>"
    html += "<th style='border: 1px solid black;'>Total</th></tr>"

    for athlete_id, data in athlete_map.items():
        user = data["user"]
        perf_dict = data["performances"]
        total_score = 0
        cumulative = 0
        if user["sexe"] == "M":
            if user["age"] < 16:
                events_athle = decaHM
            else:
                events_athle = decaH
        elif user["sexe"] == "F":
            events_athle = decaF
            
        html += f"<tr><td style='border: 1px solid black; font-weight: bold;'>{user['name']}</td>"

        for event in events_athle:
            unit = unit_mapping.get(event, "")
            if event in perf_dict:
                perf, score = perf_dict[event]
                cumulative += score
                total_score += score

                if unit == "m":
                    perf /= 100
                    perf_str = f"{perf:.2f}m"
                elif unit == "s":
                    perf_str = f"{perf:.2f}s"
                elif unit == "min":
                    minutes = int(perf // 60)
                    seconds = perf % 60
                    perf_str = f"{minutes}min{seconds:.2f}s"
                else:
                    perf_str = str(perf)

                cell = f"{perf_str} ({score})<br><i>{cumulative} pts</i>"
            else:
                cell = "-"

            html += f"<td style='border: 1px solid black;'>{cell}</td>"

        html += f"<td style='border: 1px solid black; font-weight: bold;'>{total_score}</td></tr>"
    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)
        
    st.markdown("---")

    if st.button("Retour"):
        st.session_state.decathlon_view = None
        st.rerun()
    

def resume_competition():
    st.subheader("Reprendre une compétition en cours")
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

    col_left, _ = st.columns([3, 6])
    with col_left:
        name = st.text_input("Nom de la compétition")

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
        st.session_state['competition_name'] = name
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
            cols = st.columns(11)
            row_data = competition_data.get(athlete.id, {})
            total_score = 0
            if athlete.sexe.value == "M":
                if athlete.age < 16:
                    events_athle = decaHM
                else:
                    events_athle = decaH
            elif athlete.sexe.value == "F":
                events_athle = decaF
            
            for idx, event in enumerate(events_athle):
                with cols[idx % 11]:
                    key = f"perf_{athlete.id}_{event}"
                    perf = st.text_input(event, key=key, value=row_data.get(event, ""))

                    if perf:
                        try:
                            perf_val = float(perf)
                            score = compute_score_remote(event, athlete.sexe.value, perf_val)
                            st.markdown(f"**Score**: {score}")
                            total_score += score
                            row_data[event] = perf
                        except ValueError:
                            st.warning("Entrée invalide")
            with cols[10]:
                st.markdown(f"**Total** {total_score}")
            competition_data[athlete.id] = row_data

    st.session_state["competition_data"] = competition_data

    if st.button("Sauvegarder"):
        save_competition()
        st.session_state.decathlon_view = None
        st.session_state.active_athletes = []
        st.rerun()

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
            name=st.session_state['competition_name'],
            date=date.today(),
        )
        session.add(comp)
        session.commit()
        session.refresh(comp)

        # 2. Link athletes to this competition
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
        
        
# ---------- HELPERS ----------- #
def compute_ranking(athlete_map, selected_sexes):
    ranking_data = []


    # Track previous cumulative scores for missing events
    cumulative_by_athlete = {}

    for event_idx, event in enumerate(decaH):
        scores_this_event = []

        for athlete_id, data in athlete_map.items():
            user = data["user"]
            perf_dict = data["performances"]
            name = user["name"]
            sexe = user["sexe"]
            age= user["age"]

            if sexe not in selected_sexes:
                continue

            prev_score = cumulative_by_athlete.get(name, 0)

            event_score = 0
            if event in perf_dict:
                event_score += perf_dict[event][1]
            else:
                event_score = 0

            cumulative_score = prev_score + event_score
            cumulative_by_athlete[name] = cumulative_score
            
            scores_this_event.append((name, cumulative_score, event_score, sexe))

        if not scores_this_event:
            continue
        
        display_event = "110mH/100mH" if event == "110mH" else event
        scores_this_event.sort(key=lambda x: -x[1])
        for rank, (name, cumulative_score, event_score, sexe) in enumerate(scores_this_event, start=1):
            ranking_data.append({
                "Event": display_event,
                "Athlete": name,
                "Rank": rank,
                "Intermédiaire": cumulative_score,
                "Score": event_score,
                "Sexe": sexe,
                "Missing": event_score == 0,
            })

    return pd.DataFrame(ranking_data)

