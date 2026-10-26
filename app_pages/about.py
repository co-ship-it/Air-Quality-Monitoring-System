"""About page: project summary, modules, technologies and data sources."""

import streamlit as st

from aqi_calculator import AQI_STANDARD, HEALTH_DISCLAIMER

st.title("About this project", icon=":material/info:")
st.markdown(f"""
**Air Quality Monitoring System Using Python** is a college project that monitors air
pollution in cities, calculates the Air Quality Index using **{AQI_STANDARD}**, shows
interactive charts and a 24-hour outlook, and gives personalised general health advice.
""")

st.subheader("Modules", icon=":material/folder:")
st.table({
    "File": ["app.py", "app_pages/*.py", "ui.py", "api_service.py", "aqi_calculator.py",
             "health_advice.py", "database.py", "visualizations.py", "sample_data.py"],
    "Purpose": [
        "Entry point: page setup, sidebar settings, navigation",
        "One file per page (Home, Pollutants, Outlook, Compare, History, AQI guide, About)",
        "Shared helpers: city search, data loading, AQI card, downloadable report",
        "Gets data from Open-Meteo, OpenWeatherMap or sample data (past + forecast)",
        "Averages, sub-indices, AQI, categories and the hourly AQI timeline",
        "Personalised tips and activity guide for each health profile",
        "Saves and reads observations in SQLite, CSV export",
        "Plotly charts and map",
        "Offline demo data",
    ],
})

st.subheader("Technologies", icon=":material/build:")
with st.container(horizontal=True):
    for tech in ["Python", "Streamlit", "Pandas", "NumPy", "Plotly", "SQLite", "Requests",
                 "datetime", "python-dotenv"]:
        st.badge(tech, color="blue")

st.subheader("Data sources", icon=":material/cloud:")
st.markdown("""
- **Open-Meteo Air Quality API** - CAMS model data, no key needed (past and forecast hours).
- **OpenWeatherMap Air Pollution API** - optional, needs a free key in `.env`.
- **Built-in sample data** - offline demo values, always labelled.

Live values from these services are model estimates for a location, not readings from a
specific government monitoring station.
""")
st.caption(HEALTH_DISCLAIMER)
