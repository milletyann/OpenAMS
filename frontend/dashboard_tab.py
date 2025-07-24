import streamlit as st
import requests

from datetime import date, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

API_URL = "http://localhost:8000"

training_type_to_event_mapping = {
    "Sprint - Technique": "Sprint", 
    "Sprint - Lactique": "Lactique", 
    "Course - Aérobie": "Aérobie", 
    "Sprint - Départ": "Sprint", 
    "Sprint - Haies": "Haies", 
    "Longueur - Technique": "Longueur",
    "Longueur - Élan réduit": "Longueur", 
    "Longueur - Élan complet": "Longueur", 
    "Longueur - Prise de marques": "Longueur", 
    "Longueur - Courses d'élan": "Longueur", 
    "Hauteur - Technique": "Hauteur",
    "Hauteur - Élan réduit": "Hauteur", 
    "Hauteur - Élan complet": "Hauteur", 
    "Hauteur - Prise de marques": "Hauteur", 
    "Hauteur - Courses d'élan": "Hauteur", 
    "Perche - Technique": "Perche",
    "Perche - Élan réduit": "Perche", 
    "Perche - Élan complet": "Perche", 
    "Perche - Prise de marques": "Perche", 
    "Perche - Courses d'élan": "Perche", 
    "Poids - Technique": "Poids", 
    "Poids - Élan réduit": "Poids", 
    "Poids - Élan complet": "Poids", 
    "Disque - Technique": "Disque", 
    "Disque - Élan réduit": "Disque", 
    "Disque - Élan complet": "Disque", 
    "Javelot - Technique": "Javelot", 
    "Javelot - Élan réduit": "Javelot", 
    "Javelot - Élan complet": "Javelot", 
    "Lancer - PPG": "Muscu", 
    "Muscu - Force": "Muscu", 
    "Muscu - Puissance": "Muscu", 
    "Muscu - Explosivité": "Muscu", 
    "PPG": "Muscu", 
    "Bondissements": "Muscu", 
    "Compétition - Décathlon": "Compétition", 
    "Compétition - 100m": "Compétition", 
    "Compétition - Longueur": "Compétition", 
    "Compétition - Poids": "Compétition", 
    "Compétition - Hauteur": "Compétition", 
    "Compétition - 400m": "Compétition", 
    "Compétition - 110mH": "Compétition", 
    "Compétition - Disque": "Compétition", 
    "Compétition - Perche": "Compétition", 
    "Compétition - Javelot": "Compétition", 
    "Compétition - 1500m": "Compétition",
    
    "Général": "Mobilité", 
    "Spécifique - Épaules": "Mobilité", 
    "Spécifique - Hanches": "Mobilité", 
    "Spécifique - Dos": "Mobilité", 
    "Spécifique - Jambes": "Mobilité", 
    "Spécifique - Bas du corps": "Mobilité", 
    "Spécifique - Haut du corps": "Mobilité",
}

def dashboard_tab():
    st.title("Tableau de bord")
    st.divider()
    athlete = main_header()
    st.divider()
    # ----- Différents composants à organiser ----- #
    bandeau(athlete)
    
    col1, _, col2, _, col3 = st.columns([20, 1, 15, 1, 20])
    with col1:
        health_temporal_graph(athlete)
    with col2:
        training_load(athlete)
    with col3:
        radar_graph(athlete)
    
    col1, _, col2 = st.columns([20, 1, 20])
    with col1:
        human_body(athlete)
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
    
    default_start = date.today() - timedelta(days=7)
    default_end = date.today()
    with col2:
        start, end = st.date_input(
            "Période",
            value=(default_start, default_end),
            min_value= date.today() - timedelta(days=60),
            max_value= date.today()
        )

        if (end - start).days < 7:
            st.warning("La période doit être d’au moins 7 jours.")
            st.stop()

        st.session_state.period = (start, end)
    
    st.session_state.period = (start, end)
    
    return athletes_options[selected_athlete]

# ----- Bandeau ----- #
def bandeau(athlete):
    st.info("Bandeau des 4 métriques (intensité moyenne des entraînements sur la durée,\
        durée d'entraînement moyenne sur la durée, santé globale calculée sur base des \
            infos du check quotidien et pénalisé/régularisé par les infos blessures, \
                distinguer santé physique et santé physio comme sommeil, blessure, \
                    mental, stress)")

# ----- Charge d'entraînement ----- #
def training_load(athlete):
    period = st.session_state.period
    end_date = period[1]
    start_date = period[0]
    user_id = athlete["id"]

    response = requests.get(f"{API_URL}/training_data", params={
        "user_id": user_id,
        "start_date": start_date,
        "end_date": end_date
    })
    
    try:
        response.raise_for_status()
    except Exception as e:
        st.error(f"Erreur: {e}")
        st.stop()

    if response.status_code != 200:
        st.error("Erreur lors de la récupération des données.")
        return

    training_data = response.json()
    load = compute_training_load(training_data=training_data, period=period)

    fig = plot_training_load_gauge(load)
    st.plotly_chart(fig, use_container_width=True)

def compute_training_load(training_data, period, I_max=8, D_max=180):
    df = pd.DataFrame(training_data)

    if df.empty:
        return 0.0

    df["date"] = pd.to_datetime(df["date"])
    df["intensity"] = df["intensity"].astype(float)
    df["duration"] = df["duration"].astype(float)
    df["training_product"] = df["duration"] * df["intensity"]

    # double check de la période sur laquelle on filtre
    start, end = pd.Timestamp(period[0]), pd.Timestamp(period[1])
    df = df[(df["date"] >= start)]
    df = df[(df["date"] <= end)]
    delta = (end - start).days

    if df.empty:
        return 0.0

    grouped = df.groupby("date").agg({"intensity": "sum", "duration": "sum", "training_product": "sum"})
    grouped["load_per_day"] = grouped["training_product"] / (I_max*D_max)

    load = (10 / delta) * grouped["load_per_day"].sum()
    return load

def plot_training_load_gauge(load):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=load,
        number={'suffix': "", 'font': {'size': 32}},
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Training Load", 'font': {'size': 14}},
        gauge={
            'axis': {'range': [0, 10], 'tickwidth': 1, 'tickcolor': "darkgray"},
            'bar': {'color': "black", 'thickness': 0.25},
            'bgcolor': None,
            'borderwidth': 2,
            'bordercolor': None,
            'steps': [
                {'range': [0, 3], 'color': "#60AF62"}, #4CAF4F
                {'range': [3, 5], 'color': "#FFC926"}, #FFC107
                {'range': [5, 7], 'color': "#FFA51F"}, #FF9800
                {'range': [7, 9], 'color': "#FF4A3D"}, #F44336
                {'range': [9, 9.7], 'color': "#5C453E"}, #5D4037
                {'range': [9.7, 10], 'color': "#272727"}, #1B1B1B
            ],
            'threshold': None
            # {
            #     'line': {'color': "white", 'width': 2},
            #     'thickness': 0.75,
            #     'value': 7.5
            # }
        }
    ))

    fig.update_layout(
        margin=dict(l=20, r=20, t=30, b=10),
        height=250,
    )

    return fig

# ----- Graphe CS ----- #
def radar_graph(athlete):
    period = st.session_state.period
    end_date = period[1]
    start_date = period[0]
    user_id = athlete["id"]

    response = requests.get(f"{API_URL}/training_data", params={
        "user_id": user_id,
        "start_date": start_date,
        "end_date": end_date
    })
    
    try:
        response.raise_for_status()
    except Exception as e:
        st.error(f"Erreur: {e}")
        st.stop()

    if response.status_code != 200:
        st.error("Erreur lors de la récupération des données.")
        return

    training_data = response.json()
    df = pd.DataFrame(training_data)
    
    if df.empty:
        return []

    df['event'] = df['type'].map(training_type_to_event_mapping)
    df = df.dropna(subset=['event'])
    counts = df['event'].value_counts().reset_index()
    counts.columns = ['name', 'value']
    
    
    fig = plot_radar(counts)
    st.plotly_chart(fig, use_container_width=True)
    
def plot_radar(df):
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=df['value'],
        theta=df['name'],
        fill='toself',
        name='Training Types',
        line=dict(color='royalblue')
    ))

    fig.update_layout(
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(
                visible=True,
                range=[0, df['value'].max() * 1.2],
                showline=False,
                ticks='',
                showticklabels=True
            ),
            angularaxis=dict(
                showline=False,
                ticks='',
                showticklabels=True,
                tickcolor= 'rgba(0,0,0,0)',
                tickfont=dict(size=14),
                ticklen=15,
                rotation=90,
                direction='clockwise',
            )
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        title="",
        font=dict(color='white'),
        margin=dict(t=20, l=60, r=50, b=30),
    )
    
    return fig
# ----- Corps Humain 3D ----- #
def human_body(athlete):
    st.info("Corps 3D des blessures (le corps en 3D tourne lentement sur lui-même. \
            points rouges semi transparents qui brillent pour localiser les blessures \
                et douleurs encore en cours. Possibilité de cliquer sur un point pour avoir \
                    un tooltip récapitulatif du nom, durée, intensité actuelle)")

# ----- Graphe temporel de santé ----- #
def health_temporal_graph(athlete):
    st.info("Graphe des métriques temporelles de santé (humeur, qualité de sommeil, durée\
        de sommeil, fatigue musculaire, ...)")

# ----- Graphe suivi de blessure ----- #
def injury_graph(athlete):
    st.info("Graphe des suivis de blessure (représenter toutes les blessures d'un coup,\
        une courbe pour chaque qui représente l'intensité de la douleur, avec un design \
            spécial pour un début et une fin de blessure avec un emoji sur le point du \
                graphe)")

