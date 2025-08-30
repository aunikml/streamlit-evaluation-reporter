# app.py

import streamlit as st
from db_utils import init_db, verify_user

# Initialize the database (creates the DB file and admin user on first run)
init_db()

st.set_page_config(page_title="Evaluation Report Builder", page_icon="🔐", layout="centered")

# --- Login Logic ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("Login to Report Builder")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            role = verify_user(username, password)
            if role:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.role = role
                st.rerun()
            else:
                st.error("Invalid username or password")
else:
    # --- Main App for Logged-in Users ---
    st.set_page_config(page_title="Evaluation Report Builder", page_icon="🏠", layout="wide")
    st.title("Welcome to the Evaluation Report Builder")
    
    st.markdown(
        f"""
        You are logged in as **{st.session_state.username}** (Role: {st.session_state.role}).
        
        This tool helps you automatically generate insightful reports from evaluation data.

        ### How to use this tool:
        1.  Select the type of evaluation you want to perform from the sidebar navigation.
        2.  Fill in the report details in the sidebar form.
        3.  Upload the corresponding CSV file and click "Generate Report".

        **👈 Select an evaluation from the sidebar to get started!**
        """
    )
    
    with st.sidebar:
        if st.button("Logout"):
            del st.session_state.authenticated
            del st.session_state.username
            del st.session_state.role
            if 'processed_data' in st.session_state:
                del st.session_state.processed_data
            st.rerun()