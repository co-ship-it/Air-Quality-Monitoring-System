"""Tests for aqi_calculator.py  -  run with:  python -m pytest -v"""

from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from aqi_calculator import (calculate_aqi, calculate_sub_index, compute_averages,
                            evaluate_air_quality, get_category, is_valid_measurement)


# ---------- sub-index -------------------------------------------------------
@pytest.mark.parametrize("pollutant, concentration, expected", [
    ("pm2_5", 0, 0),          # lowest value
    ("pm2_5", 30, 50),        # top of "Good"
    ("pm2_5", 45, 75),        # middle of 30-60 -> middle of 50-100
    ("pm2_5", 60, 100),
    ("pm2_5", 75, 150),       # 60-90 maps to 100-200
    ("pm10", 100, 100),
    ("pm10", 175, 150),       # 100-250 maps to 100-200
    ("no2", 80, 100),
    ("so2", 40, 50),
    ("o3", 100, 100),
    ("co", 1000, 50),         # 1000 µg/m³ = 1.0 mg/m³ -> 50
    ("co", 6000, 150),        # 6 mg/m³ is the middle of 2-10 -> 150
])
def test_sub_index_values(pollutant, concentration, expected):
    assert calculate_sub_index(pollutant, concentration) == pytest.approx(expected)


def test_sub_index_is_capped_at_500():
    assert calculate_sub_index("pm2_5", 9999) == 500


@pytest.mark.parametrize("bad_value", [None, -5, float("nan"), float("inf"), "abc", True])
def test_sub_index_rejects_invalid_values(bad_value):
    assert calculate_sub_index("pm2_5", bad_value) is None


def test_sub_index_unknown_pollutant():
    assert calculate_sub_index("lead", 10) is None


def test_is_valid_measurement():
    assert is_valid_measurement(12.5)
    assert is_valid_measurement("7")
    assert not is_valid_measurement(-1)
    assert not is_valid_measurement(None)


# ---------- categories ------------------------------------------------------
@pytest.mark.parametrize("aqi, name", [
    (0, "Good"), (50, "Good"), (51, "Satisfactory"), (100, "Satisfactory"),
    (101, "Moderate"), (200, "Moderate"), (201, "Poor"), (300, "Poor"),
    (301, "Very Poor"), (400, "Very Poor"), (401, "Severe"), (500, "Severe"),
    (50.4, "Good"),           # rounds to 50
])
def test_categories(aqi, name):
    assert get_category(aqi)["name"] == name


def test_category_of_invalid_value_is_none():
    assert get_category(None) is None
    assert get_category(-3) is None


# ---------- overall AQI -----------------------------------------------------
def test_aqi_is_the_highest_sub_index():
    result = calculate_aqi({"pm2_5": 45, "pm10": 175, "no2": 40, "so2": None,
                            "co": None, "o3": None})
    assert result.is_valid
    assert result.aqi == 150
    assert result.dominant_pollutant == "pm10"
    assert result.category["name"] == "Moderate"


def test_aqi_needs_at_least_three_pollutants():
    result = calculate_aqi({"pm2_5": 45, "pm10": 80})
    assert not result.is_valid
    assert "at least 3" in result.message


def test_aqi_needs_pm25_or_pm10():
    result = calculate_aqi({"no2": 40, "so2": 20, "o3": 30, "co": 500})
    assert not result.is_valid
    assert "PM2.5 or PM10" in result.message


# ---------- averaging -------------------------------------------------------
def _hourly_frame(hours, value=50.0):
    end = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
    times = [end - timedelta(hours=h) for h in range(hours - 1, -1, -1)]
    frame = pd.DataFrame({"time": pd.to_datetime(times, utc=True)})
    for code in ["pm2_5", "pm10", "no2", "so2", "co", "o3"]:
        frame[code] = value
    return frame, end


def test_averages_use_correct_periods():
    frame, end = _hourly_frame(30)
    frame.loc[frame.index[-8:], "o3"] = 100.0       # only the last 8 hours are 100
    frame.loc[frame.index[-24:], "pm2_5"] = 20.0    # only the last 24 hours are 20
    averages = compute_averages(frame, end)
    assert averages["o3"] == pytest.approx(100.0)   # 8-hour window
    assert averages["pm2_5"] == pytest.approx(20.0) # 24-hour window


def test_too_few_hours_gives_no_average():
    frame, end = _hourly_frame(10)                  # 10 h < 16 h needed for 24 h average
    averages = compute_averages(frame, end)
    assert averages["pm2_5"] is None
    assert averages["co"] is not None               # 8 h average still possible


def test_missing_and_negative_values_are_ignored():
    frame, end = _hourly_frame(24, value=40.0)
    frame.loc[0:4, "pm10"] = None
    frame.loc[5, "pm10"] = -10                      # invalid sensor value
    averages = compute_averages(frame, end)
    assert averages["pm10"] == pytest.approx(40.0)  # 18 valid hours remain


def test_evaluate_with_empty_data():
    result = evaluate_air_quality(pd.DataFrame())
    assert not result.is_valid
