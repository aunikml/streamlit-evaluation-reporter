# setup.py

import streamlit as st
import subprocess
import sys
import os

# Path where playwright browsers will be stored in Streamlit Cloud
PLAYWRIGHT_BROWSERS_PATH = "/home/appuser/.cache/ms-playwright"

def check_and_install_playwright():
    """
    Checks if the Playwright browser is installed. If not, it installs it.
    This function is designed to run only once per container startup.
    """
    # Use a session state flag to ensure this runs only once.
    if 'playwright_installed' not in st.session_state:
        st.info("📦 First-time setup: Installing browser dependencies for PDF export...")
        st.warning("This may take a minute. The app will automatically rerun when complete.")
        
        # Check if the directory exists, if not, create it.
        if not os.path.exists(PLAYWRIGHT_BROWSERS_PATH):
            os.makedirs(PLAYWRIGHT_BROWSERS_PATH)

        try:
            # Run the playwright install command
            subprocess.run(
                [sys.executable, "-m", "playwright", "install", "--with-deps"],
                check=True,
                capture_output=True,
                text=True
            )
            st.session_state.playwright_installed = True
            st.success("✅ Browser dependencies installed successfully!")
            # Rerun the app to clear the setup messages and proceed
            st.rerun()

        except subprocess.CalledProcessError as e:
            st.error("❌ Failed to install Playwright browser.")
            st.code(f"Exit Code: {e.returncode}\nSTDOUT: {e.stdout}\nSTDERR: {e.stderr}")
            st.stop()
        except Exception as e:
            st.error(f"An unexpected error occurred during setup: {e}")
            st.stop()
    
    return True