# Streamlit Evaluation Report Builder

This is a multi-page Streamlit application designed to automatically generate insightful evaluation reports from data collected via CSV files or Google Sheets.

## Features

- **Multi-Page Interface:** Separate, dedicated pages for "Faculty Evaluation" and "Course Evaluation".
- **User Authentication:** A secure login system with 'admin' and 'user' roles.
- **Admin Panel:** Admins can create and manage user accounts.
- **Flexible Data Input:** Supports both CSV file uploads and direct import from public Google Sheet links.
- **Rich Data Visualization:** Generates interactive pie charts for quantitative feedback.
- **Quantitative Analysis:** Automatically calculates average scores and summary metrics.
- **PDF Export:** Generates a professional, print-ready PDF report with all metadata, charts, and summaries.
- **Modular and Scalable:** Built with a clean structure using a `utils.py` file for reusable functions.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
    ```

2.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install browser binaries for Playwright:**
    (This is a one-time setup step for PDF generation)
    ```bash
    playwright install
    ```

## How to Run the Application

1.  Ensure your virtual environment is activated.
2.  Run the main Streamlit application from the root directory:
    ```bash
    streamlit run app.py
    ```
3.  The application will open in your web browser. The first time you run it, a `users.db` file will be created with a default admin account:
    - **Username:** `admin`
    - **Password:** `admin`

4.  Log in with the admin credentials to start using the app and create new users.