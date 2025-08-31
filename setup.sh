#!/bin/bash

# Create the directory for playwright's cache if it doesn't exist
mkdir -p /home/appuser/.cache/ms-playwright

# Set the correct permissions for the directory
chown -R appuser:appuser /home/appuser/.cache

# Install the browser and its system dependencies
playwright install --with-deps

# Run the Streamlit application
streamlit run app.py