import streamlit as st
st.set_page_config(layout="wide")

from training_tab import training_tab
from user_tab import user_tab
from performance_tab import performance_tab
from health_tab import health_tab
from dashboard_tab import dashboard_tab
from settings import settings

def main():
    st.sidebar.title("OpenAMS")

    # Initialize session state for selected tab if not present
    if "selected_tab" not in st.session_state:
        st.session_state.selected_tab = "Athlète"

    # Sidebar radio with session state syncing
    selected_tab = st.sidebar.radio(
        "Menu",
        ("Athlète", "Tableau de bord", "Entraînement", "Performance", "Santé", "Paramètres"),
        index=["Athlète", "Tableau de bord", "Entraînement", "Performance", "Santé", "Paramètres"].index(st.session_state.selected_tab),
        key="sidebar_tabs",
    )
    
    # Update session state when user changes tab
    if selected_tab != st.session_state.selected_tab:
        st.session_state.selected_tab = selected_tab

    # Display corresponding tab content
    if selected_tab == "Athlète":
        user_tab()
        
    elif selected_tab == "Tableau de bord":
        dashboard_tab()

    elif selected_tab == "Entraînement":
        training_tab()
        
    elif selected_tab == "Performance":
        performance_tab()

    elif selected_tab == "Santé":
        health_tab()

    elif selected_tab == "Paramètres":
        settings()

if __name__ == "__main__":
    main()