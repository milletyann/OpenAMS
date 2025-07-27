import streamlit as st
from sqlmodel import Session, select

from backend.database import engine
import requests
from datetime import date
from backend.models.user import User
from backend.models.enumeration import Role, Sport
from backend.models.decathlon import Decathlon, DecathlonPerformance, DecathlonAthleteLink

import pandas as pd
from datetime import datetime
import plotly.express as px

API_URL = "http://localhost:8000"

# --- Events --- #
decaH = ["100m", "Longueur", "Poids", "Hauteur", "400m", "110mH", "Disque", "Perche", "Javelot", "1500m"]
decaF = ["100m", "Longueur", "Poids", "Hauteur", "400m", "100mH", "Disque", "Perche", "Javelot", "1500m"]
decaHM = ["100m", "Longueur", "Poids", "Hauteur", "400m", "100mH", "Disque", "Perche", "Javelot", "1500m"]
all_events_deca = ["100m", "Longueur", "Poids", "Hauteur", "400m", "110mH/100mH", "Disque", "Perche", "Javelot", "1500m"]

event_aliases = {
    "110mH": "110mH/100mH",
    "100mH": "110mH/100mH"
}

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

def fetch_user_best_total_score(user_id: int, discipline: str):
    resp = requests.get(f"{API_URL}/get_pb", params={"user_id": user_id, "discipline": discipline})
    if resp.status_code == 200:
        return resp.json()
    return 0

def fetch_athletes_in_deca(decathlon_id: int):
    resp = requests.get(f"{API_URL}/athletes_in_decathlon?decathlon_id={decathlon_id}")
    if resp.status_code == 200:
        return resp.json()
    return []

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
    if df_rank.empty:
        st.info("Aucun.e athlète concerné.e.")
        return

    completed_events = df_rank[~df_rank["Missing"]]["Event"].unique().tolist()
    if not completed_events:
        st.info("Aucune performance enregistrée.")
        return
    
    last_event = max(completed_events, key=lambda e: all_events_deca.index(e))
    last_event_index = all_events_deca.index(last_event)
    not_allowed_events = all_events_deca[last_event_index + 1:]
    
    df_rank.loc[df_rank[df_rank["Event"].isin(not_allowed_events)].index, 'Rank'] = None
    
    fig = px.line(
        df_rank,
        x="Event",
        y="Rank",
        color="Athlete",
        markers=True,
        hover_data={
            "Event": False,
            "Athlete": True,
            "Rank": False,
            "Intermédiaire": True,
            "Score": True,
            "Performance": True,
            "Sexe": False,
            "Missing": False
        },
        title="Évolution du classement général",
    )


    fig.update_yaxes(autorange="reversed", title="Rang")
    fig.update_layout(
        height=600, 
        xaxis=dict(categoryarray=all_events_deca))
    st.plotly_chart(fig, use_container_width=True)

def display_competition():
    competitions = fetch_all_decathlons_cached()
    if not competitions:
        st.warning("Aucune compétition trouvée.")
        return
        
    comp_options = {comp["name"]: comp for comp in competitions}
    comp_names = list(comp_options.keys())
    
    if "selected_competition_name" not in st.session_state:
        st.session_state.selected_competition_name = comp_names[0]
    
    selected_name = st.selectbox(
        "Choisir une compétition",
        comp_names,
        index=comp_names.index(st.session_state.selected_competition_name) if st.session_state.selected_competition_name in comp_names else 0,
        key="selected_competition_name"
    )
    
    selected_comp = comp_options[selected_name]
    st.session_state["selected_competition"] = selected_comp

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


    best_scores_by_event = {}
    athlete_rows = []
    for athlete_id, data in athlete_map.items():
        user = data["user"]
        if user["sexe"] not in selected_sexes:
            continue
        perf_dict = data["performances"]
        total_score = 0

        if user["sexe"] == "M":
            events_athle = decaHM if user["age"] < 16 else decaH
        else:
            events_athle = decaF

        for event in events_athle:
            if event in perf_dict:
                _, score = perf_dict[event]
                total_score += score
                norm_event = event_aliases.get(event, event)
                best_scores_by_event[norm_event] = max(best_scores_by_event.get(norm_event, 0), score)

        athlete_rows.append((athlete_id, user, perf_dict, total_score))

    athlete_rows.sort(key=lambda x: x[3], reverse=True)

    rank = 0
    for athlete_id, user, perf_dict, total_score in athlete_rows:
        if user["sexe"] not in selected_sexes:
            continue
        
        rank += 1
        if rank == 1:
            bg_color = "#FFD90088"
        elif rank == 2:
            bg_color = "#C0C0C088"
        elif rank == 3:
            bg_color = "#CD7F3288"
        else:
            bg_color = ""
            
        best_perf = fetch_user_best_total_score(user["id"], discipline="Décathlon")
        best_score = best_perf['score']
        pb_tag = " <span style='color:white;'>(PB)</span>" if total_score > best_score else ""
        
        if user["sexe"] == "M":
            events_athle = decaHM if user["age"] < 16 else decaH
        else:
            events_athle = decaF

        html += f"<tr><td style='border: 1px solid black; font-weight: bold; background-color:{bg_color};'>{user['name']}</td>"
        cumulative = 0

        for event in events_athle:
            unit = unit_mapping.get(event, "")
            if event in perf_dict:
                perf, score = perf_dict[event]
                cumulative += score

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
                    
                norm_event = event_aliases.get(event, event)
                if score == best_scores_by_event.get(norm_event):
                    event_color = "#56D956"
                else:
                    event_color = "white"

                cell = f"{perf_str} ({score})<br><i>{cumulative} pts</i>"
            else:
                event_color = "white"
                cell = "-"

            html += f"<td style='border: 1px solid black; color: {event_color}; background-color:{bg_color};'>{cell}</td>"

        html += f"<td style='border: 1px solid black; background-color:{bg_color};'><b>{total_score}</b><i>{pb_tag}</i></td></tr>"

    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)
        
    st.markdown("---")

    if st.button("Retour"):
        st.session_state.decathlon_view = None
        st.rerun()

# ----------------- Resume/Modify section -----------------
def resume_competition():
    st.subheader("Reprendre une compétition en cours")
    competitions = fetch_all_decathlons_cached()
    if not competitions:
        st.warning("Aucune compétition trouvée.")
        return

    comp_options = {comp["name"]: comp for comp in competitions}
    selected_name = st.selectbox("Choisir une compétition", list(comp_options.keys()))
    selected_comp = comp_options[selected_name]
    
    st.session_state["decathlon_object"] = selected_comp
    
    performances = fetch_performances_cached(selected_comp["id"])
    competition_data = {}
    if not performances:
        ids = fetch_athletes_in_deca(selected_comp["id"])
        active_athletes = []
        with Session(engine) as session:
            for id in ids:
                athlete = session.exec(select(User).where(User.id == id['user_id'])).all()
                active_athletes.append(athlete[0])
        for athlete in ids:
            competition_data[athlete['user_id']] = {}
            
    else:
        ids = []
        for perf in performances:
            id = perf['user_id']
            if not id in ids:
                ids.append(id)
                competition_data[id] = {}
            event = perf['event']
            p = perf['performance']
            competition_data[id][event] = p
        
        active_athletes = []
        with Session(engine) as session:
            for id in ids:
                athlete = session.exec(select(User).where(User.id == id)).all()
                
                active_athletes.append(athlete[0])

    st.session_state["competition_data"] = competition_data
    st.session_state["active_athletes"] = active_athletes

    render_decathlon_table(edit_mode=True)
    
    if st.button("Retour"):
        st.session_state.decathlon_view = None
        st.rerun()

def update_decathlon_in_db():
    with Session(engine) as session:
        comp = st.session_state.get("decathlon_object")
        if not comp:
            st.error("Aucune compétition sélectionnée.")
            return

        decathlon_id = comp["id"]
        comp_date = datetime.strptime(comp["date"], "%Y-%m-%d").date()
        updated, created = 0, 0

        for athlete in st.session_state["active_athletes"]:
            user_id = athlete.id
            sexe = athlete.sexe.value
            age = athlete.age

            if sexe == "M":
                events = decaHM if age < 16 else decaH
            elif sexe == "F":
                events = decaF
            else:
                continue

            perf_data = st.session_state["competition_data"].get(user_id, {})

            for event in events:
                perf_str = perf_data.get(event)
                if not perf_str:
                    continue

                try:
                    perf_val = float(perf_str)
                    score = compute_score_remote(event, sexe, perf_val)
                    print(score)

                    existing = session.exec(
                        select(DecathlonPerformance)
                        .where(DecathlonPerformance.decathlon_id == decathlon_id)
                        .where(DecathlonPerformance.user_id == user_id)
                        .where(DecathlonPerformance.event == event)
                    ).first()

                    if existing:
                        existing.performance = perf_val
                        existing.score = score
                        existing.date = comp_date
                        updated += 1
                    else:
                        new_perf = DecathlonPerformance(
                            decathlon_id=decathlon_id,
                            user_id=user_id,
                            event=event,
                            performance=perf_val,
                            score=score,
                            date=comp_date
                        )
                        session.add(new_perf)
                        created += 1

                except ValueError:
                    st.warning(f"Performance invalide: {perf_str} pour {athlete.name} ({event})")
                except Exception as e:
                    session.rollback()
                    st.warning(f"Erreur pour {athlete.name} - {event}: {e}")

        session.commit()
        st.success(f"Performances mises à jour: {updated} – Ajouts: {created}")

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
        render_decathlon_table(edit_mode=False)
    
    if st.button("Retour"):
        st.session_state.decathlon_view = None
        st.session_state.active_athletes = []
        st.session_state.competition_data = {}
        st.rerun()

# ------------------ Editable Table with Scoring ------------------
def render_decathlon_table(edit_mode):
    if not edit_mode:
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

    st.divider()
    if not edit_mode:
        # not in edit mode = creation mode
        if st.button("Sauvegarder"):
            # save the competition object and already given performances into decathlon tables
            create_competition_in_db()
            st.session_state.decathlon_view = None
            st.session_state.active_athletes = []
            st.session_state.competition_data = {}
            st.rerun()
    else:
        # edit mode so not the same way of saving into database
        col1, _, col2 = st.columns([2, 5, 2])
        with col1:            
            if st.button("Enregistrer"):
                # save all perfs into decathlon_performance table
                update_decathlon_in_db()
                #st.session_state.decathlon_view = None
                st.rerun()
                
        with col2:
            if st.button("Sauvegarder les perfs"):
                # save all perfs of athletes into performance table + sum up scores and create a decathlon performance in the performance table
                # some function to save all perfs into performance table
                st.session_state.decathlon_view = None
                st.session_state.active_athletes = []
                st.session_state.competition_data = {}
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
def create_competition_in_db():
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
    cumulative_by_athlete = {}
    event_scores_map = {event: [] for event in all_events_deca}

    for athlete_id, data in athlete_map.items():
        user = data["user"]
        perf_dict = data["performances"]
        name = user["name"]
        sexe = user["sexe"]
        age = user["age"]

        if sexe not in selected_sexes:
            continue

        if sexe == "M":
            events = decaHM if age < 16 else decaH
        elif sexe == "F":
            events = decaF
        else:
            continue

        cumulative_score = 0
        for event in events:
            event_score = 0
            raw_perf = None
            formatted_perf = ""

            if event in perf_dict:
                raw_perf = perf_dict[event][0]
                event_score = perf_dict[event][1]

                unit = unit_mapping.get(event, "")
                if unit == "m":
                    raw_perf /= 100
                    formatted_perf = f"{raw_perf:.2f}m"
                elif unit == "s":
                    formatted_perf = f"{raw_perf:.2f}s"
                elif unit == "min":
                    minutes = int(raw_perf // 60)
                    seconds = raw_perf % 60
                    formatted_perf = f"{minutes}min{seconds:.2f}s"
                else:
                    formatted_perf = str(raw_perf)
            else:
                event_score = 0

            cumulative_score += event_score
            cumulative_by_athlete[name] = cumulative_score

            if event == "110mH" or event == "100mH":
                event = "110mH/100mH"
            event_scores_map[event].append(
                (name, cumulative_score, event_score, formatted_perf, sexe)
            )

    for event in all_events_deca:
        scores_this_event = event_scores_map.get(event, [])
        if not scores_this_event:
            continue

        scores_this_event.sort(key=lambda x: -x[1])
        
        display_event = "110mH/100mH" if event == "110mH" else event

        for rank, (name, cumulative_score, event_score, formatted_perf, sexe) in enumerate(scores_this_event, start=1):
            ranking_data.append({
                "Event": display_event,
                "Athlete": name,
                "Rank": rank,
                "Intermédiaire": cumulative_score,
                "Score": event_score,
                "Performance": formatted_perf,
                "Sexe": sexe,
                "Missing": event_score == 0,
            })

    return pd.DataFrame(ranking_data)
