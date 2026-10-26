"""Tests for health_advice.py and the hourly AQI timeline in aqi_calculator.py."""

from datetime import datetime, timedelta, timezone

import pandas as pd

import health_advice
from aqi_calculator import aqi_timeline


# ---------- health advice ---------------------------------------------------
def test_sensitive_profiles_are_one_level_more_cautious():
    assert health_advice.risk_level("Moderate", "general") == 1
    assert health_advice.risk_level("Moderate", "lung") == 2
    assert health_advice.risk_level("Good", "lung") == 0          # Good stays low
    assert health_advice.risk_level("Severe", "heart") == 3       # capped at 3


def test_every_profile_has_tips_for_every_category():
    for profile in health_advice.PROFILES:
        for category in health_advice.CATEGORY_RISK:
            assert health_advice.personal_tips(category, profile)


def test_all_tips_has_no_duplicates():
    from aqi_calculator import CATEGORIES
    for cat in CATEGORIES:
        for profile in health_advice.PROFILES:
            tips = health_advice.all_tips(cat, profile)
            assert len(tips) == len(set(tips))
            assert tips[:len(cat["advice"])] == cat["advice"]   # CPCB advice comes first


def test_activity_guide():
    good = health_advice.activity_guide("Good", "general")
    severe = health_advice.activity_guide("Severe", "general")
    assert list(good.columns) == ["Activity", "Recommendation"]
    assert all("OK" in r for r in good["Recommendation"])
    assert all("Avoid" in r for r in severe["Recommendation"])


# ---------- AQI timeline ----------------------------------------------------
def _frame(start, hours, pm25):
    times = [start + timedelta(hours=h) for h in range(hours)]
    return pd.DataFrame({"time": pd.to_datetime(times, utc=True), "pm2_5": pm25,
                         "pm10": 50.0, "no2": 20.0, "so2": 5.0, "co": 500.0, "o3": 30.0})


def test_timeline_past_and_forecast():
    start = datetime(2026, 10, 1, tzinfo=timezone.utc)
    past = _frame(start, 48, 45.0)                         # 48 measured hours
    future = _frame(start + timedelta(hours=48), 24, 45.0)  # 24 forecast hours
    timeline = aqi_timeline(past, future)
    assert len(timeline) == 24 + 24
    assert timeline["is_forecast"].sum() == 24
    assert (timeline["aqi"] == 75).all()                   # PM2.5 45 -> 75 everywhere


def test_timeline_follows_a_rise_in_pollution():
    start = datetime(2026, 10, 1, tzinfo=timezone.utc)
    past = _frame(start, 48, 30.0)
    future = _frame(start + timedelta(hours=48), 24, 90.0)  # pollution rises
    timeline = aqi_timeline(past, future)
    assert timeline["aqi"].iloc[-1] > timeline["aqi"].iloc[0]


def test_timeline_without_forecast_and_empty():
    start = datetime(2026, 10, 1, tzinfo=timezone.utc)
    timeline = aqi_timeline(_frame(start, 48, 45.0), pd.DataFrame())
    assert len(timeline) == 24 and not timeline["is_forecast"].any()
    assert aqi_timeline(pd.DataFrame()).empty
