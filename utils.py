# utils.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
import base64
from playwright.sync_api import sync_playwright
import re
from urllib.error import URLError


# -------------------------------
# Data Loading
# -------------------------------
def load_df_from_gsheet_url(url):
    """
    Takes a Google Sheet URL, converts it to a CSV export URL, and loads it into a DataFrame.
    Includes improved, specific error handling for cloud environments.
    """
    try:
        match_id = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
        match_gid = re.search(r"gid=([0-9]+)", url)
        if not match_id:
            st.error("Invalid Google Sheet URL. Could not find the sheet ID.")
            return None
        sheet_id = match_id.group(1)
        gid = match_gid.group(1) if match_gid else "0"
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        df = pd.read_csv(export_url)
        return df
    except URLError:
        st.error("Network Connection Error: Failed to connect.")
        st.warning("This may be due to a firewall. Try the 'Upload CSV' option.")
        return None
    except Exception:
        st.error("Could not load data from the Google Sheet link.")
        st.warning("Please ensure the sheet's sharing setting is set to 'Anyone with the link'.")
        return None


# -------------------------------
# Sidebar Form
# -------------------------------
def display_metadata_form(page_type, requires_faculty_name=True):
    """
    Creates a reusable form in the sidebar with specific and helpful validation.
    """
    with st.form("metadata_form"):
        st.info("Fill in the details below and provide your data source.")
        
        faculty_name = st.text_input("Faculty Name") if requires_faculty_name else None
        program = st.selectbox("Program", ["M.Ed.", "ECD"])
        course_code = st.text_input("Course Code")
        batch = st.text_input("Batch")
        semester = st.selectbox("Semester", ["SUMMER", "FALL", "SPRING"])
        year = st.selectbox("Year", list(range(2025, 2031)))
        
        st.markdown("---")
        
        st.write("**Select Data Source**")
        source_option = st.radio(
            "Choose one:",
            ("Upload CSV File", "Google Sheet Link"),
            horizontal=True
        )
        uploaded_file = st.file_uploader("1. Upload CSV File", type="csv")
        gsheet_url = st.text_input("2. Or, Paste Google Sheet Link")

        submitted = st.form_submit_button("Generate Report")

        if submitted:
            if requires_faculty_name and not faculty_name:
                st.warning("Please fill in the 'Faculty Name'."); st.stop()
            if not course_code:
                st.warning("Please fill in the 'Course Code'."); st.stop()
            if not batch:
                st.warning("Please fill in the 'Batch'."); st.stop()
            
            df = None
            if source_option == "Upload CSV File":
                if uploaded_file is None:
                    st.warning("Please upload a CSV file."); st.stop()
                df = pd.read_csv(uploaded_file)
            else:
                if not gsheet_url:
                    st.warning("Please paste a Google Sheet link."); st.stop()
                df = load_df_from_gsheet_url(gsheet_url)
                if df is None:
                    st.stop()
            
            with st.spinner("Processing data..."):
                metadata = {
                    "Program": program, "Course Code": course_code, "Batch": batch,
                    "Semester": f"{semester} {year}"
                }
                if requires_faculty_name and faculty_name:
                    metadata["Faculty Name"] = faculty_name
                
                st.session_state.processed_data = {"df": df, "metadata": metadata}
                st.rerun()


# -------------------------------
# Chart Generation
# -------------------------------
def _generate_figure(ratings_series, category_order, color_map):
    """
    Single source of truth for creating a chart figure.
    Both the UI and the PDF will call this function.
    """
    rating_counts = ratings_series.value_counts().reindex(category_order, fill_value=0).reset_index()
    rating_counts.columns = ['Rating', 'Count']
    
    fig = px.pie(
        rating_counts, names='Rating', values='Count', hole=0.4,
        color='Rating',
        color_discrete_map=color_map.copy()
    )
    fig.update_traces(textposition='inside', textinfo='percent+label', pull=[0.05, 0, 0, 0, 0])
    fig.update_layout(
        showlegend=False, uniformtext_minsize=12, uniformtext_mode='hide',
        title={'text': 'Response Distribution', 'x': 0.5, 'xanchor': 'center'}
    )
    return fig, rating_counts


def create_pie_chart(df, col_name, category_order, color_map):
    """
    Creates a Pie Chart and supplements it with a data table for the UI.
    """
    st.markdown(f"#### {col_name}")
    
    if df[col_name].dtype == 'object' and ': ' in str(df[col_name].iloc[0]):
        ratings_for_viz = df[col_name].str.split(': ').str[1].dropna()
    else:
        ratings_for_viz = df[col_name].dropna()
    
    fig, rating_counts = _generate_figure(ratings_for_viz, category_order, color_map)
    
    with st.expander("View Raw Counts (includes categories with 0 responses)"):
        st.dataframe(rating_counts, hide_index=True, use_container_width=True)
    
    return fig


# -------------------------------
# Score Calculation
# -------------------------------
def calculate_scores(df, question_columns_slice, score_mapping, new_max_score=60):
    """Performs score calculations by mapping the raw string values directly."""
    question_columns = df.columns[question_columns_slice]
    score_results = []
    
    for col in question_columns:
        ratings = df[col].dropna()
        numerical_scores = ratings.map(score_mapping)
        unmapped_values = ratings[numerical_scores.isna()]
        if not unmapped_values.empty:
            st.warning(f"In question **'{col}'**, the following unknown ratings were found and ignored: `{list(unmapped_values.unique())}`")
        average_score = numerical_scores.mean()
        score_results.append({"Attribute": col, "Average Score": average_score})

    scores_df = pd.DataFrame(score_results)
    total_avg_sum = scores_df['Average Score'].sum()
    max_rating_value = 5
    max_possible_sum = len(question_columns) * max_rating_value
    converted_score = (total_avg_sum / max_possible_sum) * new_max_score if max_possible_sum > 0 else 0
    overall_average = scores_df['Average Score'].mean()
    
    return scores_df, total_avg_sum, converted_score, overall_average, max_possible_sum


# -------------------------------
# Report Generation (PDF Ready)
# -------------------------------
def fig_to_base64_img(fig, width=700, height=500, scale=2):
    """Convert a Plotly figure to a base64 PNG string for embedding in HTML."""
    img_bytes = pio.to_image(fig, format="png", width=width, height=height, scale=scale)
    base64_str = base64.b64encode(img_bytes).decode("utf-8")
    return f"<img src='data:image/png;base64,{base64_str}' style='max-width:100%; height:auto; border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,0.1);'/>"


def generate_report_html(df, report_title, metadata, question_columns_slice, category_order, color_map, comment_column, score_mapping, new_max_score=60):
    """Generates a self-contained HTML string for the PDF report (charts embedded as base64 images)."""
    question_columns = df.columns[question_columns_slice]

    # Metadata section
    metadata_html = "<table class='meta-table'>"
    display_order = ['Faculty Name', 'Program', 'Course Code', 'Batch', 'Semester']
    sorted_metadata = {k: metadata[k] for k in display_order if k in metadata}
    for key, value in sorted_metadata.items():
        metadata_html += f"<tr><td class='meta-key'>{key}:</td><td>{value}</td></tr>"
    metadata_html += "</table>"

    html = f"""
    <html><head><style>
        body {{ font-family: Arial, sans-serif; background-color:#fafafa; color:#333; }}
        h1, h2, h3, h4 {{ color: #222; }}
        .container {{ width: 90%; margin: auto; }}
        .header {{ text-align:center; padding:30px; background:#f0f2f6; border-radius:10px; margin-bottom:30px; }}
        .header h1 {{ margin: 0; font-size: 28px; }}
        .meta-table {{ margin:auto; font-size:14px; margin-top:15px; }}
        .meta-key {{ font-weight:bold; padding-right:10px; text-align:right; }}
        .section-title {{ font-size:20px; margin:30px 0 15px; padding-bottom:8px; border-bottom:2px solid #1f77b4; }}
        .question-card {{ background:#fff; border:1px solid #ddd; border-radius:10px; padding:20px; margin-bottom:25px; }}
        .question-header {{ font-weight:bold; margin-bottom:10px; }}
        .chart-table-container {{ display:flex; gap:20px; align-items:center; }}
        .chart-table-container table {{ border-collapse:collapse; width:40%; font-size:13px; }}
        th, td {{ border:1px solid #ddd; padding:6px; text-align:left; }}
        th {{ background:#f2f2f2; }}
        .comment {{ background:#f9f9f9; border-left:4px solid #1f77b4; padding:12px; margin:10px 0; border-radius:5px; font-size:14px; }}
        .score-section table {{ width:100%; border-collapse:collapse; margin-top:10px; font-size:14px; }}
        .score-section th {{ background:#1f77b4; color:white; }}
        .metrics-container {{ display:flex; justify-content:space-around; margin-top:25px; }}
        .metric-card {{ background:#fff; border:1px solid #ddd; border-radius:10px; width:30%; padding:15px; text-align:center; box-shadow:0 2px 5px rgba(0,0,0,0.05); }}
        .metric-card h4 {{ font-size:14px; margin-bottom:10px; color:#555; }}
        .metric-card p {{ font-size:22px; font-weight:bold; color:#1f77b4; margin:0; }}
    </style></head><body><div class="container">
        <div class="header"><h1>{report_title}</h1>{metadata_html}</div>
        <p><b>Total Responses:</b> {len(df)}</p>
        <div class="section-title">Quantitative Feedback</div>
    """

    # Charts + tables
    for idx, col_name in enumerate(question_columns, 1):
        if df[col_name].dtype == 'object' and ': ' in str(df[col_name].iloc[0]):
            ratings_for_viz = df[col_name].str.split(': ').str[1].dropna()
        else:
            ratings_for_viz = df[col_name].dropna()

        fig, rating_counts = _generate_figure(ratings_for_viz, category_order, color_map)
        chart_img = fig_to_base64_img(fig)

        table_html = "<table><thead><tr><th>Rating</th><th>Count</th></tr></thead><tbody>"
        for _, row in rating_counts.iterrows():
            table_html += f"<tr><td>{row['Rating']}</td><td>{row['Count']}</td></tr>"
        table_html += "</tbody></table>"

        html += f"""
        <div class="question-card">
            <div class="question-header">Q{idx}. {col_name}</div>
            <div class="chart-table-container">
                <div style="width:60%;">{chart_img}</div>
                <div>{table_html}</div>
            </div>
        </div>
        """

    # Comments
    html += "<div class='section-title'>Qualitative Feedback</div>"
    if comment_column in df.columns:
        comments = df[comment_column].dropna()
        non_placeholder_comments = comments[~comments.astype(str).str.strip().str.lower().isin(['n/a', 'na', 'no', ''])]
        if not non_placeholder_comments.empty:
            for comment in non_placeholder_comments:
                html += f'<div class="comment">{comment}</div>'
    else:
        html += "<p>No qualitative feedback available.</p>"

    # Score summary
    scores_df, total_avg_sum, converted_score, overall_average, max_possible_sum = calculate_scores(
        df, question_columns_slice, score_mapping, new_max_score
    )
    html += '<div class="section-title">Score Summary</div><div class="score-section"><table><thead><tr><th>Attribute</th><th>Average Score</th></tr></thead><tbody>'
    for _, row in scores_df.iterrows():
        html += f"<tr><td>{row['Attribute']}</td><td>{row['Average Score']:.2f}</td></tr>"
    html += '</tbody></table>'

    html += f"""
    <div class="metrics-container">
        <div class="metric-card"><h4>Total Score (out of {max_possible_sum})</h4><p>{total_avg_sum:.2f}</p></div>
        <div class="metric-card"><h4>Converted Score (out of {new_max_score})</h4><p>{converted_score:.2f}</p></div>
        <div class="metric-card"><h4>Overall Average Rating (out of 5)</h4><p>{overall_average:.2f}</p></div>
    </div></div>
    """

    html += "</div></body></html>"
    return html


# -------------------------------
# PDF Export (FIXED)
# -------------------------------
def convert_html_to_pdf(html_string):
    """Uses Playwright to convert an HTML string to a PDF, ensuring images load first."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_string, wait_until="load")

        # Ensure all images are fully loaded before exporting
        page.evaluate("""
            () => new Promise((resolve) => {
                const imgs = Array.from(document.images);
                if (imgs.length === 0) { resolve(); return; }
                let loaded = 0;
                imgs.forEach(img => {
                    if (img.complete) {
                        loaded++;
                        if (loaded === imgs.length) resolve();
                    } else {
                        img.addEventListener('load', () => {
                            loaded++;
                            if (loaded === imgs.length) resolve();
                        });
                        img.addEventListener('error', () => {
                            loaded++;
                            if (loaded === imgs.length) resolve();
                        });
                    }
                });
            })
        """)

        pdf_bytes = page.pdf(
            format="A4",
            print_background=True,
            margin={"top": "40px", "bottom": "40px", "left": "30px", "right": "30px"}
        )
        browser.close()
    return pdf_bytes
