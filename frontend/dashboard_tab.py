import streamlit as st
import requests
import streamlit.components.v1 as components

from datetime import date, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
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

mode = 'session'
color_map_intensity = {
    'blue': 1,
    'green': 3,
    'yellow': 5,
    'orange': 7,
    'red': 9,
    'brown': 9.7
}
inverse_color_map_intensity = {
    'blue': 8.5,
    'green': 7,
    'yellow': 5,
    'orange': 4,
    'red': 3,
    'brown': 0.5,
}
color_map_duration = {
    'blue': 20,
    'green': 60,
    'yellow': 100,
    'orange': 140,
    'red': 180,
    'brown': 194
}

def dashboard_tab():
    st.title("Tableau de bord")
    st.divider()
    athlete = main_header()
    st.divider()
    
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
    
    bandeau(training_data, period, user_id)
    
    col1, _, col2, _, col3 = st.columns([20, 1, 15, 1, 20])
    with col1:
        health_temporal_graph(athlete)
    with col2:
        training_load(training_data, period)
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
        period = st.date_input(
            "Période",
            value=(default_start, default_end),
            min_value= date.today() - timedelta(days=60),
            max_value= date.today()
        )
        
        if isinstance(period, tuple) and len(period) == 2:
            start, end = period
            if (end - start).days < 7:
                st.warning("La période doit être d’au moins 7 jours.")
                st.stop()

            st.session_state.period = (start, end)
    
    return athletes_options[selected_athlete]

# ----- Bandeau ----- #
def bandeau(training_data, period, athlete_id):
    #st.info("Bandeau des 5 métriques (intensité moyenne des entraînements sur la durée,\
    #    durée d'entraînement moyenne sur la durée, score de récupération, santé globale calculée sur base des \
    #        infos du check quotidien et pénalisé/régularisé par les infos blessures, \
    #            distinguer santé physique et santé physio comme sommeil, blessure, \
    #                mental, stress)")
    
    col1, _, col2, _, col3, _, col4, _, col5 = st.columns([10, 1, 10, 1, 10, 1, 10, 1, 10])
        
    with col1:
        data = mean_intensity(training_data, period, mode)

        fig = donut_chart(data, "Intensité moyenne d'entraînement", color_map=color_map_intensity, maxi=10, suffix='/10', bb=True)
        st.pyplot(fig)
    with col2:
        data = mean_duration(training_data, period, mode)
        
        fig = donut_chart(data, "Durée moyenne d'entraînement", color_map=color_map_duration, maxi=200, suffix=' min', bb=True)
        st.pyplot(fig)
        
    with col3:
        data = recovery_score(athlete_id)
        
        fig = donut_chart(data, "Score de Récupération", color_map=inverse_color_map_intensity, maxi=10, suffix='/10', bb=False)
        st.pyplot(fig)

    with col4:
        data = physical_health_score()
        data = 3.2
        
        fig = donut_chart(data, "Score Physique de Santé", color_map=inverse_color_map_intensity, maxi=10, suffix='/10', bb=False)
        st.pyplot(fig)

    with col5:
        data = physiological_health_score()
        data = 8.9
        
        fig = donut_chart(data, "Score Physiologique de Santé", color_map=inverse_color_map_intensity, maxi=10, suffix='/10', bb=False)
        st.pyplot(fig)

def mean_intensity(training_data, period, mode='session'):
    # mode = 'day' fait la moyenne quotidienne de l'intensité, 'session' fait la moyenne de l'intensité par séance
    df = pd.DataFrame(training_data)
    horizon = (period[1]-period[0]).days
    
    if df.empty:
        return 0
    
    if mode == 'day':
        grouped = df.groupby("date").agg({"intensity": 'mean', "duration": 'sum'})
        res = grouped['intensity'].mean()
        return res
    elif mode == 'session':
        res = df['intensity'].mean()
        return res
        
    return 0.0

def mean_duration(training_data, period, mode='day'):
    df = pd.DataFrame(training_data)
    horizon = (period[1]-period[0]).days
    
    if df.empty:
        return 0
    
    if mode == 'day':
        grouped = df.groupby("date").agg({"intensity": 'mean', "duration": 'sum'})
        res = grouped['duration'].mean()
        return res
    elif mode == 'session':
        res = df['duration'].mean()
        return res
        
    return 0.0

def recovery_score(athlete_id):
    end_date = st.session_state.get("period")[1]
    daily_measurements = requests.get(f"{API_URL}/health-checks/by-athlete/{athlete_id}/{end_date}").json()
    if daily_measurements is None:
        return 0
    else:
        daily_measurements = {
            'sleep_quality': daily_measurements["sleep_quality"], 
            'sleep_duration': daily_measurements["sleep_duration"], 
            'resting_heart_rate': daily_measurements["resting_heart_rate"], 
            'hand_grip_test': daily_measurements["hand_grip_test"], 
            'longest_expiration_test': daily_measurements["longest_expiration_test"], 
            'single_leg_proprio_test': daily_measurements["single_leg_proprio_test"], 
        }

    response = requests.post(f"{API_URL}/compute_recovery_score/", json=daily_measurements)

    if response.status_code == 200:
        score = response.json().get("recovery_score")
        return score
    else:
        return 0

def physical_health_score():
    return

def physiological_health_score():
    return

def donut_chart(data, title, color_map, maxi, suffix, bb=True): # bb = bottom best, true if it's bad to have a too high score
    fig, ax = plt.subplots(figsize=(2, 2), facecolor='none')

    percentage = max(0, min(data / maxi, 1))

    values = [percentage, 1 - percentage]
    if bb:
        colors = [get_color(data, color_map), "none"]
    else:
        colors = [get_inverse_color(data, color_map), "none"]
        
    wedges, _ = ax.pie(
        values,
        startangle=90,
        colors=colors,
        radius=1,
        counterclock=False,
        wedgeprops={'width': 0.25, 'edgecolor': 'none'}
    )

    ax.text(0, 0, f"{data:.2f}\n{suffix}", ha='center', va='center', fontsize=10, weight='bold', color="white")
    #ax.set_title(title, fontsize=8, pad=6, color="white")
    fig.suptitle(title, fontsize=8, y=0.05, color="white")

    ax.set(aspect="equal")
    plt.box(False)
    plt.tight_layout()
    return fig

# ----- Charge d'entraînement ----- #
def training_load(training_data, period):
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
        number={'suffix': "", 'font': {'color': get_color(load, color_map=color_map_intensity), 'size': 32}},
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Charge d'entraînement", 'font': {'size': 14}},
        gauge={
            'axis': {'range': [0, 10], 'tickwidth': 1, 'tickcolor': "darkgray"},
            'bar': {'color': "black", 'thickness': 0.25},
            'bgcolor': None,
            'borderwidth': 2,
            'bordercolor': None,
            'steps': [
                {'range': [0, 1], 'color': "#24A8F9"},
                {'range': [1, 3], 'color': "#60AF62"},
                {'range': [3, 5], 'color': "#FFC926"},
                {'range': [5, 7], 'color': "#FFA51F"},
                {'range': [7, 9], 'color': "#FF4A3D"},
                {'range': [9, 9.7], 'color': "#5C453E"},
                {'range': [9.7, 10], 'color': "#272727"},
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
    st.info("Human body en 3D avec Three.js, problème de chargement et d'exécution du javascript\
        pour l'instant, on reviendra là dessus plus tard.")
    
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


# ----- HELPERS ----- #
def get_color(val, color_map):
    if val <= color_map['blue']:
        return "#24a8f9"
    elif val <= color_map['green']:
        return "#4CAF50"
    elif val <= color_map['yellow']:
        return "#FFC107"
    elif val <= color_map['orange']:
        return "#FF9800"
    elif val <= color_map['red']:
        return "#F44336"
    elif val <= color_map['brown']:
        return "#5D4037"
    else:
        return "#181818"

def get_inverse_color(val, color_map):
    if val >= color_map['blue']:
        return "#24a8f9"
    elif val >= color_map['green']:
        return "#4CAF50"
    elif val >= color_map['yellow']:
        return "#FFC107"
    elif val >= color_map['orange']:
        return "#FF9800"
    elif val >= color_map['red']:
        return "#F44336"
    elif val >= color_map['brown']:
        return "#5D4037"
    else:
        return "#181818"
    
inverse_color_map_intensity = {
    'blue': 8.5,
    'green': 7,
    'yellow': 5,
    'orange': 4,
    'red': 3,
    'brown': 0.5,
}