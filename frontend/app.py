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
    user_tab()

elif tab == "Athlete":
    pass

elif tab == "Training":
    training_tab()

elif tab == "Health":
    pass
    
elif tab == "Settings":
    pass
