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
    This version does NOT ask Playwright to manage system dependencies.
    """
    if 'playwright_installed' not in st.session_state:
        st.info("📦 First-time setup: Installing browser binaries for PDF export...")
        st.warning("This may take a minute. The app will automatically rerun when complete.")
        
        if not os.path.exists(PLAYWRIGHT_BROWSERS_PATH):
            os.makedirs(PLAYWRIGHT_BROWSERS_PATH)

        try:
            # --- THE FIX: Removed the "--with-deps" flag ---
            # We trust packages.txt to handle the system dependencies.
            # This command will ONLY download the browser binaries.
            subprocess.run(
                [sys.executable, "-m", "playwright", "install"],
                check=True,
                capture_output=True,
                text=True
            )
            st.session_state.playwright_installed = True
            st.success("✅ Browser binaries installed successfully!")
            st.rerun()

        except subprocess.CalledProcessError as e:
            st.error("❌ Failed to install Playwright browser binaries.")
            st.code(f"Exit Code: {e.returncode}\nSTDOUT: {e.stdout}\nSTDERR: {e.stderr}")
            st.stop()
        except Exception as e:
            st.error(f"An unexpected error occurred during setup: {e}")
            st.stop()
    
    return True