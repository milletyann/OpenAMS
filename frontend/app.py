# frontend/app.py
import streamlit as st
import requests
from training_tab import training_tab
from athlete_tab import athlete_tab

tab = st.sidebar.selectbox("Choose Tab", ["Athlete", "Training"])

if tab == "Athlete":
    athlete_tab()
elif tab == "Training":
    training_tab()