# pages/1_Faculty_Evaluation.py

import streamlit as st
import pandas as pd
import os
import sys
import platform
import asyncio

# --- SECURITY GATE & FIXES: Ensures user is logged in and all modules can be imported ---
if not st.session_state.get('authenticated', False):
    st.error("Please log in to access this page.")
    st.stop()
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from utils import (
        display_metadata_form, create_pie_chart, calculate_scores,
        generate_report_html, convert_html_to_pdf
    )
except ImportError as e:
    st.error(f"A critical error occurred trying to import from 'utils.py': {e}")
    st.stop()

# --- Page-Specific Configurations ---
PAGE_TITLE = "Faculty Evaluation"
SCORE_MAPPING = {'Excellent': 5, 'Very Good': 4, 'Good': 3, 'Satisfactory': 2, 'Poor': 1}
CATEGORY_ORDER = ["Excellent", "Very Good", "Good", "Satisfactory", "Poor"]
COLOR_MAP = {"Excellent": "#2ca02c", "Very Good": "#1f77b4", "Good": "#ff7f0e", "Satisfactory": "#d62728", "Poor": "#9467bd"}
COMMENT_COLUMN = 'General comments'
QUESTION_COLUMNS_SLICE = slice(1, 9)
CONVERTED_SCORE_MAX = 60

def display_score_analysis(df):
    """Displays the score analysis UI for this page."""
    st.subheader("Score Summary")
    scores_df, total_avg_sum, converted_score, overall_average, max_possible_sum = calculate_scores(
        df, QUESTION_COLUMNS_SLICE, SCORE_MAPPING, CONVERTED_SCORE_MAX
    )
    st.write("The table below shows the average score for each attribute on a scale of 1 to 5.")
    st.dataframe(scores_df.style.format({"Average Score": "{:.2f}"}), use_container_width=True)
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label=f"Total Score (out of {max_possible_sum})", value=f"{total_avg_sum:.2f}")
    with col2:
        st.metric(label=f"Converted Score (out of {CONVERTED_SCORE_MAX})", value=f"{converted_score:.2f}")
    with col3:
        st.metric(label="Overall Average Rating (out of 5)", value=f"{overall_average:.2f}")

# --- Main Page UI ---
st.set_page_config(page_title=PAGE_TITLE, page_icon="🧑‍🏫", layout="wide")
st.title(f"🧑‍🏫 {PAGE_TITLE} Report Builder")

# --- Sidebar Logic ---
with st.sidebar:
    st.write(f"Logged in as **{st.session_state.username}**")
    if st.button("Logout", key="logout_faculty"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.markdown("---")

    # Show the form if no report has been generated yet
    if 'processed_data' not in st.session_state:
        display_metadata_form(PAGE_TITLE, requires_faculty_name=True)
    # Once a report is generated, show the export and clear options
    else:
        st.header("Export Report")
        data = st.session_state.processed_data
        metadata = data['metadata']
        
        if st.button("Generate PDF", key="generate_faculty_pdf"):
            with st.spinner("Generating PDF... This may take a moment."):
                html_string = generate_report_html(
                    data['df'], PAGE_TITLE, metadata, QUESTION_COLUMNS_SLICE, CATEGORY_ORDER, 
                    COLOR_MAP, COMMENT_COLUMN, SCORE_MAPPING, CONVERTED_SCORE_MAX
                )
                pdf_bytes = convert_html_to_pdf(html_string)
                
                # Sanitize each part of the metadata for a clean filename
                fn = metadata.get('Faculty Name', 'Faculty').replace(' ', '_')
                cc = metadata.get('Course Code', 'Course').replace(' ', '_')
                b = metadata.get('Batch', 'Batch').replace(' ', '_')
                s = metadata.get('Semester', 'Semester').replace(' ', '_')
                
                # Construct the new, more descriptive filename
                pdf_filename = f"{fn}_{cc}_{b}_{s}_Report.pdf"
                
                st.download_button(
                    "Download PDF", pdf_bytes, 
                    pdf_filename, # Use the new filename
                    "application/pdf"
                )
        
        if st.button("Clear Report and Start Over"):
            del st.session_state.processed_data
            st.rerun()

# --- Main Panel Logic ---
if 'processed_data' in st.session_state:
    data = st.session_state.processed_data
    df = data['df']
    metadata = data['metadata']
    question_columns = df.columns[QUESTION_COLUMNS_SLICE]

    tab1, tab2 = st.tabs(["📊 Evaluation Report", "📄 Raw Data"])
    with tab1:
        st.header("Evaluation Report")
        for key, value in metadata.items():
            st.markdown(f"**{key}:** {value}")
        st.metric(label="Total Responses Received", value=len(df))
        st.markdown("---")
        
        st.subheader("Quantitative Feedback Analysis")
        for i in range(0, len(question_columns), 2):
            col1, col2 = st.columns(2)
            with col1:
                fig1 = create_pie_chart(df, question_columns[i], CATEGORY_ORDER, COLOR_MAP)
                st.plotly_chart(fig1, use_container_width=True, key=f"faculty_{question_columns[i]}")
            if (i + 1) < len(question_columns):
                with col2:
                    fig2 = create_pie_chart(df, question_columns[i+1], CATEGORY_ORDER, COLOR_MAP)
                    st.plotly_chart(fig2, use_container_width=True, key=f"faculty_{question_columns[i+1]}")
        
        st.markdown("---")
        st.subheader("Qualitative Feedback (General Comments)")
        if COMMENT_COLUMN in df.columns:
            comments = df[COMMENT_COLUMN].dropna()
            # FIX: Ensure all comments are treated as strings before filtering to prevent errors
            non_placeholder_comments = comments[~comments.astype(str).str.strip().str.lower().isin(['n/a', 'na', 'no', ''])]
            if not non_placeholder_comments.empty:
                for i, comment in enumerate(non_placeholder_comments):
                    st.info(f"**Comment {i+1}:** {comment}")
            else:
                st.warning("No detailed comments were provided.")
        else:
            st.error(f"The '{COMMENT_COLUMN}' column was not found.")

        st.markdown("---")
        display_score_analysis(df)

    with tab2:
        st.header("Full Data Preview")
        st.dataframe(df, use_container_width=True)
else:
    st.info("Please fill in the details in the sidebar and click 'Generate Report' to begin.")