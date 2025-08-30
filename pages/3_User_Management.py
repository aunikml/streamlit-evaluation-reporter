# pages/3_User_Management.py

import streamlit as st
import pandas as pd
from db_utils import add_user, get_all_users

st.set_page_config(page_title="User Management", page_icon="👤", layout="wide")
st.title("👤 User Management")

# --- Security Gate ---
# Ensure user is logged in and is an admin
if not st.session_state.get('authenticated', False) or st.session_state.get('role') != 'admin':
    st.error("Access Denied: You must be an admin to view this page.")
    st.stop()

# --- Create New User Form ---
st.subheader("Create a New User")
with st.form("create_user_form", clear_on_submit=True):
    new_username = st.text_input("New Username")
    new_password = st.text_input("New Password", type="password")
    new_role = st.selectbox("Role", ["user", "admin"])
    submitted = st.form_submit_button("Create User")

    if submitted:
        if not new_username or not new_password:
            st.warning("Please provide both username and password.")
        else:
            if add_user(new_username, new_password, new_role):
                st.success(f"User '{new_username}' created successfully!")
            else:
                st.error(f"Username '{new_username}' already exists.")

# --- Display Existing Users ---
st.markdown("---")
st.subheader("Existing Users")
users_data = get_all_users()
if users_data:
    users_df = pd.DataFrame(users_data, columns=["Username", "Role"])
    st.dataframe(users_df, use_container_width=True)
else:
    st.info("No users found in the database.")