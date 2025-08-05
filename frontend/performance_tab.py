import streamlit as st
from sqlmodel import Session, select
import requests
from datetime import date, datetime
from backend.models.enumeration import Role
from backend.models.user import User
from backend.models.performance import Performance
# from backend.database import engine
from backend.database import engine_permanent, engine_season
from helpers import *


API_URL = "http://localhost:8000"

# --- Mapping ---
sport_disciplines = {
    "Athlétisme": ["Muscu - Force", "Muscu - Puissance", "Muscu - Explosivité", "Décathlon", "100m", "Longueur", "Poids", "Hauteur", "400m", "110mH", "100mH", "Disque", "Perche", "Javelot", "1500m", "Heptathlon", "60m", "60mH", "1000m", "200m", "400mH", "800m", "3000m", "3000m Steeple", "5000m", "10k", "Semi-marathon", "Marathon", "Marteau", "Triple-Saut"],
    "Volley-ball": ["Attaque", "Digs", "Recep", "Service - Ace", "Service - réussis", "Contre"],
    "Mobilité": ["GE Facial", "GE Frontal Gauche", "GE Frontal Droit", "Hand-to-toes"]
}

# --- Athlétisme --- #
muscu = ['Muscu - Force', 'Muscu - Puissance', 'Muscu - Explosivité']
throws = ['Disque', 'Javelot', 'Poids']
jumps = ['Longueur', 'Hauteur', 'Perche']
races = ['60m', '60mH', '100m', '100mH', '110mH', '200m', '400m', '800m', '1000m', '1500m']
events_athle = throws + jumps + races

# --- Lists for performance sorting --- #
disciplines_to_min = races + sport_disciplines['Volley-ball']
disciplines_to_max = jumps + throws + ["Décathlon", "Heptathlon"] + sport_disciplines['Mobilité'] + muscu

# --- Units --- #
unites = ["centimètres", "secondes", "points", "kg"]

# --- Weather --- #
meteo_mapping = ["Canicule", "Soleil", "Nuageux", "Venteux", "Pluvieux", "Orageux", "Intérieur"]

def performance_tab():
    st.title("Performance")
    display_performances()
    st.divider()
    col1, _, col2 = st.columns([15, 1, 11])
    with col1:
        add_performance()
    with col2:
        hungarian_table()
    
def display_performances():    
    st.subheader("Historique des performances")
    with Session(engine_permanent) as session:
        # --- Athlete selector --- 
        athletes = session.exec(select(User).where(User.role == Role.Athlete)).all()
        
        if not athletes:
            st.warning("Aucun athlète trouvé. Veuillez d'abord créer un athlète.")
            return
    
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
            sort_by = "Plus Récent"
            sort_by = st.selectbox(
                "Trier",
                ["Plus Récent", "Plus Ancien", "Meilleur Score", "Pire Score"],
                key="sort_selectbox"
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

        all_perfs = session.exec(query).all()
        
        # --- Calculate PBs ---
        pbs_per_discipline = {}
        discipline_groups = {}
        for perf in all_perfs:
            discipline_groups.setdefault(perf.discipline, []).append(perf)
        
        for discipline, perfs in discipline_groups.items():
            valid_perfs = [p for p in perfs if p.performance is not None]
            if not valid_perfs:
                continue
            
            if discipline in disciplines_to_min:
                best_perf = min(valid_perfs, key=lambda p: p.performance)
            elif discipline in disciplines_to_max:
                best_perf = max(valid_perfs, key=lambda p: p.performance)
            
            pbs_per_discipline[discipline] = best_perf.performance
        
        # Trier les perfs
        if sort_by == "Plus Récent":
            all_perfs.sort(key=lambda p: p.date or datetime.min, reverse=True)
        elif sort_by == "Plus Ancien":
            all_perfs.sort(key=lambda p: p.date or datetime.min)
        elif sort_by == "Meilleur Score":
            all_perfs.sort(key=lambda p: p.score or 0, reverse=True)
        elif sort_by == "Pire Score":
            all_perfs.sort(key=lambda p: p.score or 0)
        
        # --- Pagination ---
        performances_per_page = 6
        total_pages = (len(all_perfs) - 1) // performances_per_page + 1 if all_perfs else 1
        current_page = st.session_state.get("current_page", 1)
        
        if total_pages > 1:
            st.markdown("---")
        
        start_idx = (current_page - 1) * performances_per_page
        end_idx = start_idx + performances_per_page
        performances_to_show = all_perfs[start_idx:end_idx]
            
        headers = f"""
            <div style="
                margin: 5px;
            ">
                <table style="width: 94%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 4px; width: 8%;"><center><b>Date</b></center></td>
                        <td style="padding: 4px; width: 8%;"><center><b>Discipline</b></center></td>
                        <td style="padding: 4px; width: 12%;"><center><b>Performance</b></center></td>
                        <td style="padding: 4px; width: 8%;"><center><b>Score</b></center></td>
                        <td style="padding: 4px; width: 12%;"><center><b>Météo</b></center></td>
                        <td style="padding: 4px; width: 16%;"><center><b>Remarques Techniques</b></center></td>
                        <td style="padding: 4px; width: 16%;"><center><b>Remarques Physiques</b></center></td>
                        <td style="padding: 4px; width: 16%;"><center><b>Remarques Mentales</b></center></td>
                    </tr>
                </table>
            </div>
        """
        st.markdown(headers, unsafe_allow_html=True)

        st.markdown("---")
        
        # Performances rows
        for perf_ in performances_to_show:
            # Check if PB
            is_pb = False
            pb_icon = ""
            pb_value = pbs_per_discipline.get(perf_.discipline)
            if pb_value is not None and perf_.performance == pb_value:
                is_pb = True
                pb_icon = "<br><span style='color:gold;'>🏅<b>PB</b></span>"

            if is_pb:
                # PB row design
                row_html = f"""
                            <div style="
                                background-color: #fff2cc;
                                border: 2px solid gold;
                                border-radius: 6px;
                                margin: 5px;
                                opacity: 0.9;
                                color: black;
                            ">"""
                        
            else:
                # Normal row rendering for non-PB
                row_html = f"""
                            <div style="
                                border: none;
                                border-radius: 6px;
                                margin: 5px;
                                opacity: 0.9;
                                color: white;
                            ">"""
            if perf_.discipline == "Décathlon":
                color_score = deca_score_color(perf_.score)
            elif perf_.discipline == "Heptathlon":
                color_score = hepta_score_color(perf_.score)
            else:
                color_score = score_color(perf_.score)
            row_html += f"""
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 4px; width: 8%;">{perf_.date}</td>
                                    <td style="padding: 4px; width: 8%;"><center>{perf_.discipline}</center></td>
                                    <td style="padding: 4px; width: 12%;"><center>{perf_.performance} {perf_.unit}{pb_icon}</center></td>
                                    <td style="padding: 4px; width: 8%; color:{color_score}; font-weight:bold; background: white; text-align:center; border-radius:8px; opacity: 0.8;">{perf_.score or 0}</td>
                                    <td style="padding: 4px; width: 12%;"><center>{perf_.meteo.value} ({perf_.temperature}°C)</center></td>
                                    <td style="padding: 4px; width: 16%;">{clip_text(perf_.technical_cues, 100)}</td>
                                    <td style="padding: 4px; width: 16%;">{clip_text(perf_.physical_cues, 100)}</td>
                                    <td style="padding: 4px; width: 16%;">{clip_text(perf_.mental_cues, 100)}</td>
                                </tr>
                            </table>
                        </div>
                    """

            row_cols = st.columns([19, 1])
            with row_cols[0]:
                st.markdown(row_html, unsafe_allow_html=True)
            
            with row_cols[1]:
                st.markdown(
                    """
                    <div style="display: flex; align-items: center; justify-content: center; height: 100%;">
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("🗑️", key=f"delete_{perf_.id}"):
                    response = requests.post(
                        f"{API_URL}/performances/delete",
                        data={"performance_id": perf_.id}
                    )
                    if response.status_code == 200:
                        st.success("Performance supprimée.")
                        st.rerun()
                    else:
                        st.error(f"Erreur lors de la suppression: {response.text}")
                st.markdown("</div>", unsafe_allow_html=True)

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
    
    with Session(engine_permanent) as session:
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
            if not selected_athlete:
                st.warning("Veuillez sélectionner au moins un atlhète.")
                return
            sex = selected_athlete.sexe.value
            
            if selected_discipline in ["Décathlon", "Heptathlon"]:
                score = perf_mark
            # COMPUTE THE SCORE HERE (WE HAVE THE DISCIPLINE, THE SEX AND THE PERFORMANCE)
            elif selected_discipline in events_athle:
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
                "score": score,
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
                #st.rerun()
            else:
                st.error("Échec de l'enregistrement.")
                

########################
### HELPER FUNCTIONS ###
######################## 

def score_color(intensity: int) -> str:
    if intensity > 700:
        return "#00cd00"
    elif 700 >= intensity > 600:
        return "#ffff00"
    elif 600 >= intensity > 500:
        return "#ffa500"
    elif 500 >= intensity > 400:
        return "#cd0000"
    elif 400 >= intensity > 300:
        return "#8b0000"
    else:
        return "#000000"

def deca_score_color(intensity: int) -> str:
    if intensity > 7000:
        return "#00cd00"
    elif 7000 >= intensity > 6000:
        return "#ffff00"
    elif 6000 >= intensity > 5000:
        return "#ffa500"
    elif 5000 >= intensity > 4000:
        return "#cd0000"
    elif 4000 >= intensity > 3000:
        return "#8b0000"
    else:
        return "#000000"

def hepta_score_color(intensity: int) -> str:
    if intensity > 4900:
        return "#00cd00"
    elif 4900 >= intensity > 4200:
        return "#ffff00"
    elif 4200 >= intensity > 3500:
        return "#ffa500"
    elif 3500 >= intensity > 2800:
        return "#cd0000"
    elif 2800 >= intensity > 2100:
        return "#8b0000"
    else:
        return "#000000"