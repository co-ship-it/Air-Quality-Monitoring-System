"""
app.py
======
Air Quality Monitoring System - main entry point.

Run with:   streamlit run app.py      (or just:  python app.py)

This file only does three things:
    1. Page setup (title, icon, wide layout) and the database table.
    2. The sidebar with settings shared by all pages
       (data source, health profile, alert level, auto-save).
    3. The navigation menu at the top. Each page is a separate file in app_pages/.
"""

import os
import sys

import streamlit as st
from streamlit import runtime

# If started with "python app.py" (or VS Code's Run button), restart it
# properly as "streamlit run app.py" so the browser page opens.
if __name__ == "__main__" and not runtime.exists():
    from streamlit.web import cli as stcli
    sys.argv = ["streamlit", "run", os.path.abspath(__file__)]
    sys.exit(stcli.main())

import api_service
import database
import health_advice
import ui
from aqi_calculator import AQI_STANDARD

st.set_page_config(page_title="Air Quality Monitoring System", page_icon=":material/air:",
                   layout="wide")
database.init_db()
ui.init_state()


@st.dialog("How to use this app", icon=":material/help:")
def how_to_use() -> None:
    st.markdown("""
1. **Pick a data source** in the sidebar. *Sample data* works without internet;
   *Open-Meteo* gives live data for any city.
2. On **Home**, type a city (or click a quick-pick button) and press **Check air quality**.
3. Read the **AQI card**, the health advice for your profile and the activity guide.
4. Open **Pollutants** for details, **Outlook** for the next 24 hours, **Compare** for
   several cities and **History** for saved records and CSV export.
5. Set your **health profile** and **alert level** in the sidebar for personal advice
   and pop-up alerts.
""")
    st.caption("Recommendations are general information, not medical advice.")


# ---------------------------------------------------------------------------
# Sidebar - settings shared by every page
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### :material/air: Air quality monitor")
    st.caption(f"AQI standard: **{AQI_STANDARD}**")

    providers = api_service.available_providers()
    if st.session_state.provider not in providers:
        st.session_state.provider = "sample"
    st.radio("Data source", providers, key="provider",
             format_func=lambda p: api_service.PROVIDER_LABELS[p])
    if st.session_state.provider == "sample":
        st.caption(":material/science: Works offline. Values are **not** real measurements.")
    else:
        st.caption(":material/wifi: Needs an internet connection.")
    if not api_service.get_api_key():
        st.caption(":material/key: OpenWeatherMap key not set (optional, see README).")

    # Changing the data source clears the old result so sample and live never mix.
    if st.session_state.get("last_provider") != st.session_state.provider:
        st.session_state.report = None
        st.session_state.last_provider = st.session_state.provider

    st.selectbox("My health profile", list(health_advice.PROFILES), key="profile",
                 format_func=health_advice.PROFILES.get,
                 help="Used to personalise the health advice and activity guide.")
    st.slider("Alert me when AQI reaches", 51, 401, step=10, key="alert_level",
              help="A pop-up alert appears when a searched city reaches this AQI.")
    st.toggle("Save searches to history", key="auto_save")
    if st.button("How to use this app", icon=":material/help:", width="stretch"):
        how_to_use()


# ---------------------------------------------------------------------------
# Navigation (each page is a file in app_pages/)
# ---------------------------------------------------------------------------
page = st.navigation(
    [
        st.Page("app_pages/home.py", title="Home", icon=":material/home:", default=True),
        st.Page("app_pages/pollutants.py", title="Pollutants", icon=":material/science:"),
        st.Page("app_pages/outlook.py", title="Outlook", icon=":material/trending_up:"),
        st.Page("app_pages/compare.py", title="Compare", icon=":material/compare_arrows:"),
        st.Page("app_pages/history.py", title="History", icon=":material/history:"),
        st.Page("app_pages/guide.py", title="AQI guide", icon=":material/menu_book:"),
        st.Page("app_pages/about.py", title="About", icon=":material/info:"),
    ],
    position="top",
)
page.run()
