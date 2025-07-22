import streamlit as st
import requests

API_URL = "http://localhost:8000"

def dashboard_tab():
    st.title("Tableau de bord")
    st.divider()
    athlete = main_header()
    st.divider()
    # ----- Différents composants à organiser ----- #
    bandeau(athlete)
    
    col1, _, col2, _, col3 = st.columns([20, 1, 15, 1, 20])
    with col1:
        human_body(athlete)
    with col2:
        small_table_display(athlete)
    with col3:
        cs_graph(athlete)
    
    col1, _, col2 = st.columns([20, 1, 20])
    with col1:
        health_temporal_graph(athlete)
    with col2:
        injury_graph(athlete)
    
def get_athletes():
    resp = requests.get(f"{API_URL}/athletes")
    if resp.status_code == 200:
        return resp.json()
    return None

def main_header():
    athletes = get_athletes()
    if not athletes:
        st.info('Aucun athlète trouvé.')
        return
    
    col1, _, col2 = st.columns([10, 1, 10])
    
    athletes_options = {athlete['name']: athlete for athlete in athletes}
    with col1:
        selected_athlete = st.selectbox("Athlète à monitorer", list(athletes_options.keys()))
    with col2:
        horizon = st.slider("Horizon d'analyse (jours)", 7, 35, 7)
        st.session_state.horizon = horizon
    
    return athletes_options[selected_athlete]

# ----- Bandeau ----- #
def bandeau(athlete):
    st.info("Bandeau des 5 métriques")

# ----- Small table display ----- #
def small_table_display(athlete):
    st.info("Petit tableau basique")

# ----- Graphe CS ----- #
def cs_graph(athlete):
    st.info("Plot des répartitions d'entraînements")

# ----- Corps Humain 3D ----- #
def human_body(athlete):
    st.info("Corps 3D des blessures")

# ----- Graphe temporel de santé ----- #
def health_temporal_graph(athlete):
    st.info("Graphe des métriques temporelles")

# ----- Graphe suivi de blessure ----- #
def injury_graph(athlete):
    st.info("Graphe des suivis de blessure")

