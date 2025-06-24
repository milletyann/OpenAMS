# frontend/app.py
import streamlit as st
from training_tab import training_tab
from user_tab import user_tab
from performance_tab import performance_tab

def main():
    st.sidebar.title("OpenAMS")

    # Initialize session state for selected tab if not present
    if "selected_tab" not in st.session_state:
        st.session_state.selected_tab = "Athlete"

    # Sidebar radio with session state syncing
    selected_tab = st.sidebar.radio(
        "Menu",
        ("Athlete", "Training", "Performance", "Health", "Settings"),
        index=["Athlete", "Training", "Performance", "Health", "Settings"].index(st.session_state.selected_tab),
        key="sidebar_tabs",  # internal key for radio widget
    )
    
    # Update session state when user changes tab
    if selected_tab != st.session_state.selected_tab:
        st.session_state.selected_tab = selected_tab

    # Display corresponding tab content
    if selected_tab == "Athlete":
        user_tab()

    elif selected_tab == "Training":
        training_tab()
        
    elif selected_tab == "Performance":
        performance_tab()

    elif selected_tab == "Health":
        st.write("Health tab is under construction.")

    elif selected_tab == "Settings":
        st.write("Settings tab is under construction.")

if __name__ == "__main__":
    main()