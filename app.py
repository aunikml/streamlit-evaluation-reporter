# app.py

import streamlit as st
from db_utils import init_db, verify_user
from setup import check_and_install_playwright # Import the new function

# --- First-time setup for Streamlit Cloud ---
# This will check and install Playwright's browser if needed.
# It uses session_state to run only once.
is_ready = check_and_install_playwright()

# --- The rest of your app will only run if the setup is complete ---
if is_ready:
    # Initialize the database
    init_db()

    st.set_page_config(page_title="Evaluation Report Builder", page_icon="🔐", layout="centered")

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
        st.set_page_config(page_title="Evaluation Report Builder", page_icon="🏠", layout="wide")
        st.title("Welcome to the Evaluation Report Builder")
        
        st.markdown(
            f"""
            You are logged in as **{st.session_state.username}** (Role: {st.session_state.role}).
            
            This tool helps you automatically generate insightful reports from evaluation data.

            ### How to use this tool:
            1.  Select the type of evaluation from the sidebar.
            2.  Fill in the report details in the sidebar form.
            3.  Provide your data source and click "Generate Report".

            **👈 Select an evaluation from the sidebar to get started!**
            """
        )
        
        with st.sidebar:
            if st.button("Logout"):
                for key in list(st.session_state.keys()): del st.session_state[key]
                st.rerun()