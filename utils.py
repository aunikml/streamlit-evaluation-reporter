# utils.py

import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from playwright.sync_api import sync_playwright
import re
from urllib.error import URLError

def load_df_from_gsheet_url(url):
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
    except Exception as e:
        st.error("Could not load data from the Google Sheet link.")
        st.warning("Please ensure the sheet's sharing is set to 'Anyone with the link'.")
        return None

def display_metadata_form(page_type, requires_faculty_name=True):
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
        source_option = st.radio("Choose one:", ("Upload CSV File", "Google Sheet Link"), horizontal=True)
        uploaded_file = st.file_uploader("1. Upload CSV File", type="csv")
        gsheet_url = st.text_input("2. Or, Paste Google Sheet Link")
        submitted = st.form_submit_button("Generate Report")
        if submitted:
            if requires_faculty_name and not faculty_name:
                st.warning("Please fill in the 'Faculty Name'."); st.stop()
            if not course_code: st.warning("Please fill in the 'Course Code'."); st.stop()
            if not batch: st.warning("Please fill in the 'Batch'."); st.stop()
            df = None
            if source_option == "Upload CSV File":
                if uploaded_file is None: st.warning("Please upload a CSV file."); st.stop()
                df = pd.read_csv(uploaded_file)
            else:
                if not gsheet_url: st.warning("Please paste a Google Sheet link."); st.stop()
                df = load_df_from_gsheet_url(gsheet_url)
                if df is None: st.stop()
            with st.spinner("Processing data..."):
                metadata = {"Program": program, "Course Code": course_code, "Batch": batch, "Semester": f"{semester} {year}"}
                if requires_faculty_name and faculty_name:
                    metadata["Faculty Name"] = faculty_name
                st.session_state.processed_data = {"df": df, "metadata": metadata}
                st.rerun()

def create_pie_chart(df, col_name, category_order, color_map, chart_title="Response Distribution"):
    st.markdown(f"#### {col_name}")
    if df[col_name].dtype == 'object' and ': ' in str(df[col_name].iloc[0]):
        ratings = df[col_name].str.split(': ').str[1].dropna()
    else:
        ratings = df[col_name].dropna()
    rating_counts = ratings.value_counts().reindex(category_order, fill_value=0).reset_index()
    rating_counts.columns = ['Rating', 'Count']
    fig = px.pie(rating_counts, names='Rating', values='Count', hole=0.4, color='Rating', color_discrete_map=color_map)
    fig.update_traces(textposition='inside', textinfo='percent+label', pull=[0.05, 0, 0, 0, 0])
    fig.update_layout(showlegend=False, uniformtext_minsize=12, uniformtext_mode='hide', title={'text': chart_title, 'x': 0.5, 'xanchor': 'center'})
    return fig

def calculate_scores(df, question_columns_slice, score_mapping, new_max_score=60):
    question_columns = df.columns[question_columns_slice]
    score_results = []
    for col in question_columns:
        if df[col].dtype == 'object' and ': ' in str(df[col].iloc[0]):
            ratings = df[col].str.split(': ').str[1].dropna()
        else:
            ratings = df[col].dropna()
        numerical_scores = ratings.map(score_mapping)
        average_score = numerical_scores.mean()
        score_results.append({"Attribute": col, "Average Score": average_score})
    scores_df = pd.DataFrame(score_results)
    total_avg_sum = scores_df['Average Score'].sum()
    max_rating_value = max(score_mapping.values()) if score_mapping else 5
    max_possible_sum = len(question_columns) * max_rating_value
    converted_score = (total_avg_sum / max_possible_sum) * new_max_score if max_possible_sum > 0 else 0
    overall_average = scores_df['Average Score'].mean()
    return scores_df, total_avg_sum, converted_score, overall_average, max_possible_sum

def generate_report_html(df, report_title, metadata, question_columns_slice, category_order, color_map, comment_column, score_mapping, new_max_score=60):
    question_columns = df.columns[question_columns_slice]
    metadata_html = "<table>"
    display_order = ['Faculty Name', 'Program', 'Course Code', 'Batch', 'Semester']
    sorted_metadata = {k: metadata[k] for k in display_order if k in metadata}
    for key, value in sorted_metadata.items():
        metadata_html += f"<tr><td style='font-weight: bold; padding-right: 15px;'>{key}:</td><td>{value}</td></tr>"
    metadata_html += "</table>"
    html = f"""
    <html><head>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{ font-family: sans-serif; }} h1, h2, h3, h4 {{ color: #333; }}
            .container {{ width: 90%; margin: auto; }}
            .header {{ border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 20px; }}
            .header h1 {{ margin: 0; }} .header table {{ width: 100%; font-size: 14px; border-collapse: collapse; }}
            .header table td {{ border: none; padding: 2px; }}
            .chart-item {{ page-break-inside: avoid; margin-bottom: 40px; text-align: center; }}
            .chart-item h4 {{ text-align: left; background-color: #f0f2f6; padding: 10px; border-radius: 5px; }}
            .chart-div {{ width: 100%; height: 450px; }}
            .comments-section, .score-section {{ margin-top: 30px; page-break-before: auto; }}
            .comment {{ background-color: #f0f2f6; border-left: 5px solid #1f77b4; padding: 10px; margin-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .metrics-container {{ display: flex; justify-content: space-around; text-align: center; margin-top: 30px; page-break-inside: avoid; }}
            .metric-card {{ border: 1px solid #ddd; padding: 15px; border-radius: 8px; width: 30%; }}
            .metric-card h4 {{ margin: 0 0 10px 0; color: #555; font-size: 14px; }}
            .metric-card p {{ font-size: 24px; font-weight: bold; margin: 0; color: #1f77b4; }}
        </style>
    </head><body><div class="container">
        <div class="header"><h1>{report_title}</h1>{metadata_html}</div>
        <p>Total Responses: {len(df)}</p><h3>Quantitative Feedback</h3>
    """
    charts_js = ""
    for i, col_name in enumerate(question_columns):
        html += f'<div class="chart-item"><h4>{col_name}</h4><div id="chart-{i}" class="chart-div"></div></div>'
        if df[col_name].dtype == 'object' and ': ' in str(df[col_name].iloc[0]):
            ratings = df[col_name].str.split(': ').str[1].dropna()
        else:
            ratings = df[col_name].dropna()
        rating_counts = ratings.value_counts().reindex(category_order, fill_value=0).reset_index()
        rating_counts.columns = ['Rating', 'Count']
        fig = px.pie(rating_counts, names='Rating', values='Count', hole=0.4, color='Rating', color_discrete_map=color_map)
        fig.update_traces(textposition='inside', textinfo='percent+label', pull=[0.05, 0, 0, 0, 0])
        fig.update_layout(showlegend=False, uniformtext_minsize=12, uniformtext_mode='hide', title={'text': 'Response Distribution', 'x': 0.5, 'xanchor': 'center'})
        fig_json = fig.to_json()
        charts_js += f"Plotly.newPlot('chart-{i}', {fig_json});\n"
    html += "<div class='comments-section'>"
    if comment_column in df.columns:
        comments = df[comment_column].dropna()
        non_placeholder_comments = comments[~comments.str.strip().str.lower().isin(['n/a', 'na', 'no', ''])]
        if not non_placeholder_comments.empty:
            html += '<h3>Qualitative Feedback</h3>'
            for comment in non_placeholder_comments: html += f'<div class="comment"><p>{comment}</p></div>'
    html += "</div>"
    scores_df, total_avg_sum, converted_score, overall_average, max_possible_sum = calculate_scores(df, question_columns_slice, score_mapping, new_max_score)
    html += '<div class="score-section"><h3>Score Summary</h3><table><thead><tr><th>Attribute</th><th>Average Score</th></tr></thead><tbody>'
    for index, row in scores_df.iterrows():
        html += f"<tr><td>{row['Attribute']}</td><td>{row['Average Score']:.2f}</td></tr>"
    html += '</tbody></table>'
    html += f"""
    <div class="metrics-container">
        <div class="metric-card"><h4>Total Score (out of {max_possible_sum})</h4><p>{total_avg_sum:.2f}</p></div>
        <div class="metric-card"><h4>Converted Score (out of {new_max_score})</h4><p>{converted_score:.2f}</p></div>
        <div class="metric-card"><h4>Overall Average Rating (out of 5)</h4><p>{overall_average:.2f}</p></div>
    </div></div>
    """
    html += f"<script>{charts_js}</script>"
    html += "</div></body></html>"
    return html

def convert_html_to_pdf(html_string):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_string)
        page.wait_for_timeout(2000) 
        pdf_bytes = page.pdf(format="A4", print_background=True, margin={"top": "50px", "bottom": "50px"})
        browser.close()
    return pdf_bytes