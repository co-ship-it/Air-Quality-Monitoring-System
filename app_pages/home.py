"""Home page: search a city, see its AQI, health advice and activity guide."""

import streamlit as st

import health_advice
import ui
import visualizations as viz
from aqi_calculator import HEALTH_DISCLAIMER, POLLUTANTS

st.title("Air quality monitoring system", icon=":material/air:")
st.caption("Check the Air Quality Index (AQI) of any city, see what it means for your "
           "health, and plan your day. AQI follows India's National Air Quality Index (CPCB).")

ui.city_search("home")

report = st.session_state.report
if report is None:
    st.subheader("Get started in three steps")
    step1, step2, step3 = st.columns(3, border=True)
    step1.markdown("**:material/tune: 1. Choose a data source**  \n"
                   "Sample data works offline; Open-Meteo gives live data for any city.")
    step2.markdown("**:material/search: 2. Search a city**  \n"
                   "Type a name or click a quick-pick button above.")
    step3.markdown("**:material/health_and_safety: 3. Read the advice**  \n"
                   "Set your health profile in the sidebar for personal tips.")
    st.stop()

reading, result, timeline = report["reading"], report["result"], report["timeline"]
ui.data_banner(reading)
st.subheader(reading.display_name, icon=":material/location_on:")

if not result.is_valid:
    st.warning(result.message, icon=":material/warning:", title="AQI not available")
    st.page_link("app_pages/pollutants.py", label="See the pollutant values that are available",
                 icon=":material/science:")
    st.stop()

cat = result.category
profile = st.session_state.profile

# --- Headline row: colour card + key numbers --------------------------------
past = timeline[~timeline["is_forecast"]].dropna(subset=["aqi"])
card_col, m1, m2, m3 = st.columns([1.3, 1, 1, 1])
with card_col:
    ui.aqi_card(result)
with m1.container(border=True, height="stretch"):
    change = int(result.aqi - past["aqi"].iloc[0]) if len(past) > 1 else None
    st.metric("AQI over the last 24 h", result.aqi, delta=change, delta_color="inverse",
              delta_description="vs. 24 h ago", chart_data=past["aqi"].tolist() or None,
              chart_type="area",
              help="Hourly AQI for the last 24 hours. A green arrow means the air got cleaner.")
with m2.container(border=True, height="stretch"):
    dom = POLLUTANTS[result.dominant_pollutant]
    st.metric("Main pollutant", dom["name"], help=dom["description"])
    st.caption(f"{ui.fmt_value(result.averages[result.dominant_pollutant])} {dom['unit']} "
               f"({dom['averaging_hours']} h average). {dom['full_name']}.")
with m3.container(border=True, height="stretch"):
    st.metric("Last updated", f"{reading.observed_at:%H:%M} UTC",
              help="Time of the most recent hourly data.")
    st.caption(ui.fmt_time(reading.observed_at))

# --- Warning banner ------------------------------------------------------------
if result.aqi > 300:
    st.error("Everyone should avoid outdoor activity.", icon=":material/emergency:",
             title=f"Health alert: {cat['name']} air quality")
elif result.aqi > 200:
    st.error("Limit time outdoors, especially sensitive groups.", icon=":material/warning:",
             title=f"Health warning: {cat['name']} air quality")
elif result.aqi > 100:
    st.warning("Sensitive groups should take care outdoors.", icon=":material/info:",
               title=f"{cat['name']} air quality")

# --- Gauge + health advice ------------------------------------------------------
gauge_col, advice_col = st.columns([1, 1.3])
with gauge_col:
    with st.container(border=True):
        st.plotly_chart(viz.aqi_gauge(result), config={"displaylogo": False},
                        alt=f"Gauge showing AQI {result.aqi}, {cat['name']}")
        if not timeline[timeline["is_forecast"]].empty:
            peak = timeline[timeline["is_forecast"]].dropna(subset=["aqi"])
            if not peak.empty:
                top = peak.loc[peak["aqi"].idxmax()]
                st.caption(f":material/trending_up: Forecast peak in the next hours: "
                           f"**AQI {int(top['aqi'])}** ({top['category']}) around "
                           f"{ui.fmt_local(top['time'])} local time.")
                st.page_link("app_pages/outlook.py", label="Open the 24-hour outlook",
                             icon=":material/trending_up:")

with advice_col:
    with st.container(border=True):
        st.markdown(f"**:material/health_and_safety: What this means**  \n{cat['meaning']}  \n"
                    f"*Possible health impact:* {cat['health_impact']}")
        level = health_advice.risk_level(cat["name"], profile)
        st.markdown(f"**Advice for: {health_advice.PROFILES[profile]}** "
                    f"· risk level: {health_advice.RISK_LABELS[level]}")
        for tip in health_advice.all_tips(cat, profile):
            st.markdown(f"- {tip}")
        st.dataframe(health_advice.activity_guide(cat["name"], profile), hide_index=True,
                     alt="Activity guide")
        st.caption(HEALTH_DISCLAIMER)

# --- Graphs ----------------------------------------------------------------------
st.subheader("Graphs at a glance", icon=":material/bar_chart:")
trend_col, pollutant_col = st.columns([1.4, 1])
with trend_col.container(border=True):
    st.plotly_chart(viz.aqi_timeline_chart(timeline), config={"displaylogo": False},
                    alt="Hourly AQI for the past 24 hours and the forecast")
    st.caption("Hourly AQI. Dashed line = forecast estimate.")
with pollutant_col.container(border=True):
    st.plotly_chart(viz.subindex_bar_chart(result), config={"displaylogo": False},
                    alt="Sub-index of each pollutant")
    st.caption("The tallest bar is the pollutant that decides the AQI.")

# --- Extras --------------------------------------------------------------------
with st.container(horizontal=True):
    st.download_button("Download report", ui.report_text(report, profile),
                       file_name=f"air_quality_{reading.city}_{reading.observed_at:%Y%m%d_%H%M}.txt",
                       mime="text/plain", icon=":material/download:")
    st.page_link("app_pages/pollutants.py", label="Pollutant details", icon=":material/science:")
    st.page_link("app_pages/compare.py", label="Compare cities", icon=":material/compare_arrows:")

if reading.provider_index:
    st.caption(f"Provider's own index: {reading.provider_index}. Shown for reference only; "
               "it is NOT used in our AQI.")
