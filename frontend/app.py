# frontend/app.py
import streamlit as st
import requests
from training_tab import training_tab
from user_tab import user_tab

st.sidebar.title("OpenAMS")
tab = st.sidebar.radio(
    "Menu", 
    ("Home", "Athlete", "Training", "Health", "Settings")
)


if tab == "Home":
    st.subheader("")
    user_tab()

elif tab == "Athlete":
    st.subheader("Athlete")

elif tab == "Training":
    st.subheader("Training Logs")
    training_tab()

elif tab == "Health":
    st.subheader("Health")
    
elif tab == "Settings":
    st.subheader("Settings")
