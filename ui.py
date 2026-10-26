"""
ui.py
=====
Helper functions shared by all pages (each page lives in app_pages/).

    init_state()      - default values kept between page changes
    city_search()     - search box + quick-pick and recent-city buttons
    fetch_city()      - get data, calculate AQI, save to history, show alerts
    data_banner()     - clear "SAMPLE" or "LIVE" label
    aqi_card()        - big colour-coded AQI card
    report_text()     - text report the user can download
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st

import api_service
import database
import health_advice
import sample_data
from aqi_calculator import (AQI_STANDARD, HEALTH_DISCLAIMER, POLLUTANTS, AQIResult,
                            aqi_timeline, evaluate_air_quality)

POPULAR_CITIES = ["Delhi", "Mumbai", "Bengaluru", "Kolkata",
                  "Chennai", "Hyderabad", "Pune", "Lucknow"]
MAX_RECENT = 6


# ---------------------------------------------------------------------------
# Session state (values remembered while the browser tab is open)
# ---------------------------------------------------------------------------
def init_state() -> None:
    defaults = {
        "report": None,            # dict with reading, result, timeline
        "recent": {},              # data source -> list of recently searched cities
        "provider": "sample",      # data source chosen in the sidebar
        "profile": "general",      # health profile chosen in the sidebar
        "alert_level": 201,        # AQI that triggers an alert (201 = start of "Poor")
        "auto_save": True,         # save every search to history
        "pending_city": None,      # city clicked in a quick-pick button
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------
@st.cache_data(ttl=600, show_spinner=False)
def load_reading(city: str, provider: str) -> api_service.AirQualityReading:
    """Fetch data (cached for 10 minutes so repeated clicks do not call the API again)."""
    return api_service.get_air_quality(city, provider)


def analyse(reading: api_service.AirQualityReading) -> AQIResult:
    return evaluate_air_quality(reading.hourly, reading.observed_at)


def build_record(reading: api_service.AirQualityReading, result: AQIResult) -> dict:
    """Prepare one database row from a reading and its AQI result."""
    return {
        "city": reading.city, "country": reading.country,
        "latitude": reading.latitude, "longitude": reading.longitude,
        "observed_at": reading.observed_at,
        **{code: result.averages.get(code) for code in POLLUTANTS},
        "aqi": result.aqi,
        "category": result.category["name"] if result.category else None,
        "dominant_pollutant": result.dominant_pollutant,
        "aqi_standard": result.standard,
        "data_source": reading.provider,
        "is_sample": reading.is_sample,
    }


def fmt_time(moment: datetime) -> str:
    """'23 Oct 2026, 14:00 UTC (19:30 local)'"""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    utc = moment.astimezone(timezone.utc)
    return f"{utc:%d %b %Y, %H:%M} UTC ({moment.astimezone():%H:%M} local)"


def fmt_local(moment) -> str:
    """'Fri 14:00' in the computer's local time."""
    return pd.Timestamp(moment).to_pydatetime().astimezone().strftime("%a %H:%M")


def fmt_value(value, decimals: int = 1) -> str:
    return "Not available" if value is None or pd.isna(value) else f"{value:,.{decimals}f}"


def remember_city(city: str) -> None:
    provider = st.session_state.provider
    recent = [c for c in st.session_state.recent.get(provider, []) if c != city]
    st.session_state.recent[provider] = ([city] + recent)[:MAX_RECENT]


def fetch_city(city: str) -> bool:
    """Fetch a city, calculate AQI, save it and keep it for all pages. Returns True on success."""
    provider = st.session_state.provider
    st.session_state.report = None            # never show an old city after a failed search
    try:
        with st.spinner(f"Getting air-quality data for {city}..."):
            reading = load_reading(city, provider)
    except api_service.CityNotFoundError as err:
        st.error(str(err), icon=":material/travel_explore:", title="City not found")
        return False
    except api_service.AirQualityError as err:
        st.error(str(err), icon=":material/cloud_off:", title="Could not get data")
        return False
    except Exception:                          # unexpected problem - do not crash the app
        st.error("Something unexpected went wrong while getting data. Please try again "
                 "or switch to Sample data in the sidebar.", icon=":material/error:")
        return False

    result = analyse(reading)
    st.session_state.report = {
        "reading": reading,
        "result": result,
        "timeline": aqi_timeline(reading.hourly, reading.forecast),
    }
    remember_city(reading.city)

    if st.session_state.auto_save:
        if database.save_observation(build_record(reading, result)):
            st.toast("Saved to history", icon=":material/save:")
    if result.is_valid and result.aqi >= st.session_state.alert_level:
        st.toast(f"Alert: AQI {result.aqi} in {reading.city} is at or above your alert "
                 f"level ({st.session_state.alert_level}).",
                 icon=":material/notifications_active:", duration="long")
    return True


# ---------------------------------------------------------------------------
# Search box
# ---------------------------------------------------------------------------
def _queue_city(widget_key: str) -> None:
    """Called when a quick-pick button is clicked: remember it and reset the button."""
    choice = st.session_state.get(widget_key)
    if choice:
        st.session_state.pending_city = choice
    st.session_state[widget_key] = None


def city_search(key: str) -> None:
    """Search form + quick-pick buttons + recent searches."""
    provider = st.session_state.provider
    with st.form(f"search_{key}", border=False):
        with st.container(horizontal=True, vertical_alignment="bottom"):
            if provider == "sample":
                city = st.selectbox("Choose a sample city", sample_data.list_sample_cities(),
                                    index=None, placeholder="Select a city")
            else:
                city = st.text_input("Search any city in the world",
                                     placeholder="e.g. Delhi  or  Pune, India",
                                     icon=":material/search:")
            submitted = st.form_submit_button("Check air quality", type="primary",
                                              icon=":material/air:")

    quick = sample_data.list_sample_cities() if provider == "sample" else POPULAR_CITIES
    st.pills("Quick pick", quick, key=f"quick_{key}",
             on_change=_queue_city, args=(f"quick_{key}",))
    recent = st.session_state.recent.get(provider, [])
    if recent:
        st.pills("Recent searches", recent, key=f"recent_{key}",
                 on_change=_queue_city, args=(f"recent_{key}",))

    city_to_fetch = None
    if submitted:
        if city:
            city_to_fetch = city
        else:
            st.warning("Please choose or type a city first.", icon=":material/edit:")
    if st.session_state.pending_city:
        city_to_fetch = st.session_state.pending_city
        st.session_state.pending_city = None
    if city_to_fetch:
        fetch_city(city_to_fetch)


def require_report():
    """Return the current report, or show a link to the Home page and stop."""
    report = st.session_state.report
    if report is None:
        st.info("Search for a city first - then come back to this page.",
                icon=":material/search:", title="No city selected")
        st.page_link("app_pages/home.py", label="Go to Home", icon=":material/home:")
        st.stop()
    return report


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------
def data_banner(reading: api_service.AirQualityReading) -> None:
    if reading.is_sample:
        st.warning("Demonstration values, not real measurements.",
                   icon=":material/science:", title="Sample data")
    else:
        st.success(api_service.SOURCE_DESCRIPTIONS[reading.provider],
                   icon=":material/satellite_alt:",
                   title=f"Live data - {api_service.PROVIDER_LABELS[reading.provider]}")


def aqi_card(result: AQIResult) -> None:
    """Large card in the official CPCB category colour (no native element does this)."""
    cat = result.category
    st.html(f"""
    <div style="background:{cat['color']};color:{cat['text_color']};border-radius:14px;
                padding:18px 22px;min-height:200px;box-sizing:border-box">
      <div style="font-size:.8rem;opacity:.85;letter-spacing:.05em;text-transform:uppercase">
        Air quality index</div>
      <div style="font-size:3.4rem;font-weight:800;line-height:1.05">{result.aqi}</div>
      <div style="font-size:1.3rem;font-weight:700">{cat['name']}</div>
      <div style="font-size:.8rem;opacity:.85;margin-top:4px">{AQI_STANDARD} ·
        range {cat['low']}-{cat['high']}</div>
    </div>""")


def report_text(report: dict, profile: str) -> str:
    """Plain-text report for the download button."""
    reading, result = report["reading"], report["result"]
    lines = [
        "AIR QUALITY REPORT",
        "==================",
        f"City:        {reading.display_name}",
        f"Data time:   {fmt_time(reading.observed_at)}",
        f"Data source: {reading.source}",
        f"Data type:   {'SAMPLE DATA (not real measurements)' if reading.is_sample else 'Live'}",
        f"Standard:    {result.standard}",
        "",
    ]
    if result.is_valid:
        cat = result.category
        lines += [
            f"AQI:                {result.aqi} ({cat['name']})",
            f"Dominant pollutant: {POLLUTANTS[result.dominant_pollutant]['name']}",
            f"Meaning:            {cat['meaning']}",
            f"Health impact:      {cat['health_impact']}",
            "",
            f"Advice for: {health_advice.PROFILES[profile]}",
        ]
        lines += [f"  - {tip}" for tip in health_advice.all_tips(cat, profile)]
    else:
        lines.append(f"AQI: not available - {result.message}")
    lines += ["", "Pollutant averages used for the AQI:"]
    for code, info in POLLUTANTS.items():
        sub = result.sub_indices.get(code)
        lines.append(f"  {info['name']:<6} {fmt_value(result.averages.get(code)):>14} {info['unit']}"
                     f"  ({info['averaging_hours']} h avg)  sub-index: "
                     f"{'-' if sub is None else round(sub)}")
    lines += ["", HEALTH_DISCLAIMER,
              f"Generated: {datetime.now(timezone.utc):%d %b %Y %H:%M} UTC by "
              "Air Quality Monitoring System"]
    return "\n".join(lines)


def seed_demo_history(days: int = 7) -> int:
    """Insert `days` days of SAMPLE observations for a few cities (for demo charts)."""
    saved = 0
    today = datetime.now(timezone.utc).replace(hour=6, minute=0, second=0, microsecond=0)
    for city in ["Delhi", "Mumbai", "Bengaluru", "Kolkata", "Shimla"]:
        for day in range(days, 0, -1):
            reading = api_service.fetch_sample(city, today - timedelta(days=day))
            saved += database.save_observation(build_record(reading, analyse(reading)))
    return saved
