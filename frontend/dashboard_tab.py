import streamlit as st
import requests
from datetime import date, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np

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
        health_temporal_graph(athlete)
    with col2:
        training_load(athlete)
    with col3:
        cs_graph(athlete)
    
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
    with col2:
        horizon = st.slider("Horizon d'analyse (jours)", 7, 35, 7)
        st.session_state.horizon = horizon
    
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
    d = st.session_state.horizon
    end_date = date.today()
    start_date = end_date - timedelta(days=d)
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
    load = compute_training_load(training_data=training_data, horizon=d)

    fig = plot_training_load_gauge(load)
    st.plotly_chart(fig, use_container_width=True)

def compute_training_load(training_data, horizon, I_max=8, D_max=180):
    df = pd.DataFrame(training_data)

    if df.empty:
        return 0.0

    df["date"] = pd.to_datetime(df["date"])
    df["intensity"] = df["intensity"].astype(float)
    df["duration"] = df["duration"].astype(float)
    df["training_product"] = df["duration"] * df["intensity"]

    # double check de la période sur laquelle on filtre
    df = df[df["date"] >= pd.Timestamp.today().normalize() - pd.Timedelta(days=horizon)]

    if df.empty:
        return 0.0

    grouped = df.groupby("date").agg({"intensity": "sum", "duration": "sum", "training_product": "sum"})
    grouped["load_per_day"] = grouped["training_product"] / (I_max*D_max)

    load = (10 / horizon) * grouped["load_per_day"].sum()
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
                {'range': [0, 3], 'color': "#4CAF50"},
                {'range': [3, 5], 'color': "#FFC107"},
                {'range': [5, 7], 'color': "#FF9800"},
                {'range': [7, 9], 'color': "#F44336"},
                {'range': [9, 9.7], 'color': "#5D4037"},
                {'range': [9.7, 10], 'color': "#1B1B1B"},
            ],
            'threshold': {
                'line': {'color': "white", 'width': 2},
                'thickness': 0.75,
                'value': 7.5
            }
        }
    ))

    fig.update_layout(
        margin=dict(l=20, r=20, t=30, b=10),
        height=250,
    )

    return fig


# ----- Graphe CS ----- #
def cs_graph(athlete):
    st.info("Plot des répartitions d'entraînements (radar chart (faisable avec matplotlib \
        par exemple) des derniers types d'entraînement effectués pour situer les épreuves \
            sur lesquelles on met l'accent)")

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

