# frontend/app.py
import streamlit as st
import requests
from training_tab import training_tab
from user_tab import user_tab

tab = st.sidebar.selectbox("Choose Tab", ["User", "Training"])

if tab == "User":
    user_tab()
elif tab == "Training":
    training_tab()