import requests
import streamlit as st

st.title("AI Student Risk Analyzer")

name = st.text_input("Student Name")
marks = st.number_input("Marks")
attendance = st.number_input("Attendance")

if st.button("Analyze"):
    response = requests.post(
        "http://127.0.0.1:5000/api/analyze",
        json={
            "Name": name,
            "Sem6_Total": marks,
            "Attendance": attendance,
        },
        timeout=20,
    )
    st.json(response.json())
