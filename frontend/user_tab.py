# frontend/app.py
import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"


def user_tab():
    st.title("🏋️‍♂️ OpenAMS - Athlete Monitoring System")

    # --- Create a new User ---
    st.header("➕ Add New User")

    with st.form("user_form"):
        name = st.text_input("Name")
        sport = st.text_input("Sport")
        role = st.selectbox(
            "Rôle dans l'organisation",
            ("Athlète", "Coach", "Administrative"),
        )
        age = st.number_input("Age", min_value=1, max_value=100)
        sexe = st.selectbox(
            "Sexe",
            ("M", "F", "Autre")
        )
        submitted = st.form_submit_button("Enregistrer")

        if submitted:
            payload = {
                "name": name,
                "sport": sport,
                "role": role,
                "age": age,
                "sexe": sexe,
            }
            response = requests.post(f"{API_URL}/users/", json=payload)

            if response.status_code == 200:
                st.success("User added!")
            else:
                st.error(f"Failed to add user: {response.text}")

    # --- Display all users ---
    st.header("📋 Current Users")

    response = requests.get(f"{API_URL}/users/")
    if response.status_code == 200:
        users = response.json()
        for user in users:
            with st.expander(f"{user['name']} ({user['role']})"):
                st.markdown(f"**Sport:** {user['sport']}  \n**Age:** {user['age']}  \n**Sexe:** {user['sexe']}")

                # --- Update form ---
                with st.form(f"update_{user['id']}"):
                    new_name = st.text_input("Name", value=user["name"], key=f"name_{user['id']}")
                    new_sport = st.text_input("Sport", value=user["sport"], key=f"sport_{user['id']}")
                    new_role = st.selectbox(
                        "Rôle dans l'organisation",
                        ("Athlète", "Coach", "Administrative"),
                    )
                    new_age = st.number_input("Age", min_value=1, max_value=100, value=user["age"], key=f"age_{user['id']}")
                    new_sexe = st.selectbox(
                        "Sexe",
                        ("M", "F", "Autre")
                    )
                    update_btn = st.form_submit_button("Update")

                    if update_btn:
                        update_payload = {
                            "name": new_name,
                            "sport": new_sport,
                            "role": new_role,
                            "age": new_age,
                            "sexe": new_sexe,
                        }
                        update_response = requests.put(f"{API_URL}/users/{user['id']}", json=update_payload)
                        if update_response.status_code == 200:
                            st.success("Updated successfully. Refresh to see changes.")
                        else:
                            st.error("Update failed.")

                # --- Delete button ---
                if st.button("🗑️ Delete", key=f"delete_{user['id']}"):
                    delete_response = requests.delete(f"{API_URL}/users/{user['id']}")
                    if delete_response.status_code == 200:
                        st.success("Deleted successfully. Refresh to see changes.")
                    else:
                        st.error("Delete failed.")
    else:
        st.error("Could not load athletes.")

