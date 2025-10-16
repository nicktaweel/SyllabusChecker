# app_gui V1
# Streamlit interface for syllabus checker project
# Ishaq Halimi
# October 15, 2025

import streamlit as st
import tempfile
import os

# set up streamlit app's configuration: page title and layout size
st.set_page_config(page_title="Syllbus Checker", layout="wide")

# create the main title of the page and give instructions
st.title("Penn State abington - Syllabus Checker")
st.write("Upload a syllabus PDF to analyze its content, completeness, clarity.")

# upload section
uploaded_file = st.file_uploader("Upload a Syllabus (PDF only):", type=["pdf"])

if uploaded_file is not None:
    # save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(uploaded_file.getbuffer())
        temp_path = temp_file.name

st.success("File successfully uploaded!")

# placeholder for analysis(we'll connnect to syllabus_checker Later)
if st.button("Run Analyze"):
    st.info("Analyzing feature will be connected soon.")
    st.write("File saved temporarily at:", temp_path)

# Delete temp file when done
if os.path.exists(temp_path):
    os.remove(temp_path)

# Fuction to call on to check if pdf
from Syllabus_checker import analyze_pdf

if st.button("Run Analysis"):
    report = analyze_pdf(temp_path)
    st.text_area("📄 Analysis Results", report, height=400)

