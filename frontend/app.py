# frontend/app.py
import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.title("🏋️‍♂️ OpenAMS - Athlete Monitoring System")

# --- Create a new athlete ---
st.header("➕ Add New Athlete")

with st.form("athlete_form"):
    name = st.text_input("Name")
    sport = st.text_input("Sport")
    age = st.number_input("Age", min_value=1, max_value=100)
    sexe = st.text_input("Sexe")
    submitted = st.form_submit_button("Enregistrer")

    if submitted:
        payload = {
            "name": name,
            "sport": sport,
            "age": age,
            "sexe": sexe,
        }
        response = requests.post(f"{API_URL}/athletes/", json=payload)

        if response.status_code == 200:
            st.success("Athlete added!")
        else:
            st.error(f"Failed to add athlete: {response.text}")

# --- Display all athletes ---
st.header("📋 Current Athletes")

response = requests.get(f"{API_URL}/athletes/")
if response.status_code == 200:
    athletes = response.json()
    for athlete in athletes:
        with st.expander(f"{athlete['name']}"):
            st.markdown(f"**Sport:** {athlete['sport']}  \n**Age:** {athlete['age']}  \n**Sexe:** {athlete['sexe']}")

            # --- Update form ---
            with st.form(f"update_{athlete['id']}"):
                new_name = st.text_input("Name", value=athlete["name"], key=f"name_{athlete['id']}")
                new_sport = st.text_input("Sport", value=athlete["sport"], key=f"sport_{athlete['id']}")
                new_age = st.number_input("Age", min_value=1, max_value=100, value=athlete["age"], key=f"age_{athlete['id']}")
                new_sexe = st.text_input("Sexe", value=athlete["sexe"], key=f"sexe_{athlete['id']}")
                update_btn = st.form_submit_button("Update")

                if update_btn:
                    update_payload = {
                        "name": new_name,
                        "sport": new_sport,
                        "age": new_age,
                        "sexe": new_age,
                    }
                    update_response = requests.put(f"{API_URL}/athletes/{athlete['id']}", json=update_payload)
                    if update_response.status_code == 200:
                        st.success("Updated successfully. Refresh to see changes.")
                    else:
                        st.error("Update failed.")

            # --- Delete button ---
            if st.button("🗑️ Delete", key=f"delete_{athlete['id']}"):
                delete_response = requests.delete(f"{API_URL}/athletes/{athlete['id']}")
                if delete_response.status_code == 200:
                    st.success("Deleted successfully. Refresh to see changes.")
                else:
                    st.error("Delete failed.")
else:
    st.error("Could not load athletes.")

