# pages/2_Course_Evaluation.py

import streamlit as st
import pandas as pd
import os
import sys
import platform
import asyncio

# --- SECURITY GATE: Must be at the top of every page ---
if not st.session_state.get('authenticated', False):
    st.error("Please log in to access this page.")
    st.stop()
# --- END OF SECURITY GATE ---

# --- ROBUST FIX for Windows asyncio and Module Imports ---
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)
# --- END OF FIX ---

try:
    from utils import (
        display_metadata_form, create_pie_chart, calculate_scores,
        generate_report_html, convert_html_to_pdf
    )
except ImportError as e:
    st.error(f"A critical error occurred trying to import from 'utils.py': {e}")
    st.stop()

# --- Page-Specific Configurations ---
PAGE_TITLE = "Course Evaluation"
SCORE_MAPPING = {'Strongly Agree': 5, 'Agree': 4, 'Neutral': 3, 'Disagree': 2, 'Strongly Disagree': 1}
CATEGORY_ORDER = ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]
COLOR_MAP = {"Strongly Agree": "#2ca02c", "Agree": "#1f7b14", "Neutral": "#ff7f0e", "Disagree": "#d62728", "Strongly Disagree": "#9467bd"}
# --- FIX 1: Add trailing space to match the CSV header exactly ---
COMMENT_COLUMN = 'General comment '
QUESTION_COLUMNS_SLICE = slice(1, 5)
CONVERTED_SCORE_MAX = 15

def display_score_analysis(df):
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
st.set_page_config(page_title=PAGE_TITLE, page_icon="📚", layout="wide")
st.title(f"📚 {PAGE_TITLE} Report Builder")

# --- Sidebar Logic ---
with st.sidebar:
    st.write(f"Logged in as **{st.session_state.username}**")
    if st.button("Logout", key="logout_course"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.markdown("---")

    if 'processed_data' not in st.session_state:
        # --- FIX 2: Call the form function without requiring faculty name ---
        display_metadata_form(PAGE_TITLE, requires_faculty_name=False)
    else:
        st.header("Export Report")
        data = st.session_state.processed_data
        metadata = data['metadata']
        
        if st.button("Generate PDF", key="generate_course_pdf"):
            with st.spinner("Generating PDF... This may take a moment."):
                html_string = generate_report_html(
                    data['df'], PAGE_TITLE, metadata, QUESTION_COLUMNS_SLICE, CATEGORY_ORDER,
                    COLOR_MAP, COMMENT_COLUMN, SCORE_MAPPING, CONVERTED_SCORE_MAX
                )
                pdf_bytes = convert_html_to_pdf(html_string)
                st.download_button(
                    "Download PDF", pdf_bytes,
                    f"{metadata['Course Code']}_{PAGE_TITLE}_Report.pdf", "application/pdf"
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
        # The loop will now correctly display metadata without Faculty Name
        for key, value in metadata.items():
            st.markdown(f"**{key}:** {value}")
        st.metric(label="Total Responses Received", value=len(df))
        st.markdown("---")
        
        st.subheader("Quantitative Feedback Analysis")
        for i in range(0, len(question_columns), 2):
            col1, col2 = st.columns(2)
            with col1:
                fig1 = create_pie_chart(df, question_columns[i], CATEGORY_ORDER, COLOR_MAP)
                st.plotly_chart(fig1, use_container_width=True, key=f"course_{question_columns[i]}")
            if (i + 1) < len(question_columns):
                with col2:
                    fig2 = create_pie_chart(df, question_columns[i+1], CATEGORY_ORDER, COLOR_MAP)
                    st.plotly_chart(fig2, use_container_width=True, key=f"course_{question_columns[i+1]}")
        
        st.markdown("---")
        st.subheader("Qualitative Feedback (General Comments)")
        if COMMENT_COLUMN in df.columns:
            comments = df[COMMENT_COLUMN].dropna()
            non_placeholder_comments = comments[~comments.str.strip().str.lower().isin(['n/a', 'na', 'no', ''])]
            if not non_placeholder_comments.empty:
                for i, comment in enumerate(non_placeholder_comments):
                    st.info(f"**Comment {i+1}:** {comment}")
            else:
                st.warning("No detailed comments were provided.")
        else:
            st.error(f"The column '{COMMENT_COLUMN}' was not found in the uploaded file.")
            st.info(f"Available columns are: {list(df.columns)}")

        st.markdown("---")
        display_score_analysis(df)

    with tab2:
        st.header("Full Data Preview")
        st.dataframe(df)
else:
    st.info("Please fill in the details in the sidebar and click 'Generate Report' to begin.")