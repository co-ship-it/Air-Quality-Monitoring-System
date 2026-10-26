"""
aqi_calculator.py
=================
Calculates the Air Quality Index (AQI) using ONE clearly identified standard:

    India's National Air Quality Index (NAQI), published by the
    Central Pollution Control Board (CPCB), 2014.

How the NAQI works (simple version):
    1. Each pollutant is averaged over the period the standard asks for
       (24 hours for PM2.5, PM10, NO2, SO2 and 8 hours for CO and O3).
    2. Each average is turned into a "sub-index" (0-500) using a breakpoint
       table and straight-line (linear) interpolation.
    3. The overall AQI is the HIGHEST sub-index. The pollutant with the
       highest sub-index is called the "dominant" (or prominent) pollutant.
    4. The AQI is only reported if at least 3 pollutants have valid
       sub-indices and at least one of them is PM2.5 or PM10.

This module does NOT use any API provider's own index. Providers such as
OpenWeatherMap have their own 1-5 scale, which is a different system.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import pandas as pd

AQI_STANDARD = "India NAQI (CPCB)"

# ---------------------------------------------------------------------------
# Pollutant information
# ---------------------------------------------------------------------------
# Keys are the short codes used everywhere in the project (API, DB, charts).
# All concentrations inside this project are stored in micrograms per cubic
# metre (µg/m³). The NAQI table for CO uses milligrams (mg/m³), so CO is
# divided by 1000 just before its sub-index is calculated.
POLLUTANTS = {
    "pm2_5": {
        "name": "PM2.5",
        "full_name": "Fine particulate matter (≤ 2.5 µm)",
        "unit": "µg/m³",
        "averaging_hours": 24,
        "description": "Tiny particles that reach deep into the lungs and blood. "
                       "Sources: vehicles, burning of crops/waste, industry.",
    },
    "pm10": {
        "name": "PM10",
        "full_name": "Coarse particulate matter (≤ 10 µm)",
        "unit": "µg/m³",
        "averaging_hours": 24,
        "description": "Dust and particles from roads, construction and industry.",
    },
    "no2": {
        "name": "NO₂",
        "full_name": "Nitrogen dioxide",
        "unit": "µg/m³",
        "averaging_hours": 24,
        "description": "Gas produced mainly by vehicle engines and power plants.",
    },
    "so2": {
        "name": "SO₂",
        "full_name": "Sulphur dioxide",
        "unit": "µg/m³",
        "averaging_hours": 24,
        "description": "Gas released when coal and oil containing sulphur are burned.",
    },
    "co": {
        "name": "CO",
        "full_name": "Carbon monoxide",
        "unit": "µg/m³",
        "averaging_hours": 8,
        "description": "Colourless gas from incomplete burning of fuel. "
                       "NAQI uses mg/m³ (1 mg/m³ = 1000 µg/m³).",
    },
    "o3": {
        "name": "O₃",
        "full_name": "Ozone (ground level)",
        "unit": "µg/m³",
        "averaging_hours": 8,
        "description": "Formed by sunlight reacting with other pollutants; "
                       "irritates airways.",
    },
}

POLLUTANT_CODES = list(POLLUTANTS.keys())

# Minimum number of hourly values needed to accept an average.
# CPCB requires at least 16 hourly values for a 24-hour average.
# For 8-hour averages this project uses the same 2/3 rule (6 of 8 hours).
MIN_HOURS_REQUIRED = {24: 16, 8: 6}

# ---------------------------------------------------------------------------
# NAQI breakpoint table
# ---------------------------------------------------------------------------
# Each row: (concentration_low, concentration_high, index_low, index_high)
# The official table uses integer ranges (0-30, 31-60, ...). Real data has
# decimals (e.g. 30.4), so we join the ranges end-to-end (0-30, 30-60, ...)
# to leave no gaps.
#
# The official "Severe" band has only a lower limit (e.g. PM2.5 > 250).
# To draw a straight line up to 500 we ASSUME an upper limit (marked "*").
# Anything above that assumed limit is capped at 500.
BREAKPOINTS = {
    "pm10": [(0, 50, 0, 50), (50, 100, 50, 100), (100, 250, 100, 200),
             (250, 350, 200, 300), (350, 430, 300, 400), (430, 510, 400, 500)],  # *510
    "pm2_5": [(0, 30, 0, 50), (30, 60, 50, 100), (60, 90, 100, 200),
              (90, 120, 200, 300), (120, 250, 300, 400), (250, 380, 400, 500)],  # *380
    "no2": [(0, 40, 0, 50), (40, 80, 50, 100), (80, 180, 100, 200),
            (180, 280, 200, 300), (280, 400, 300, 400), (400, 520, 400, 500)],  # *520
    "so2": [(0, 40, 0, 50), (40, 80, 50, 100), (80, 380, 100, 200),
            (380, 800, 200, 300), (800, 1600, 300, 400), (1600, 2400, 400, 500)],  # *2400
    # CO in mg/m³ (8-hour average)
    "co": [(0, 1.0, 0, 50), (1.0, 2.0, 50, 100), (2.0, 10, 100, 200),
           (10, 17, 200, 300), (17, 34, 300, 400), (34, 51, 400, 500)],  # *51
    "o3": [(0, 50, 0, 50), (50, 100, 50, 100), (100, 168, 100, 200),
           (168, 208, 200, 300), (208, 748, 300, 400), (748, 1000, 400, 500)],  # *1000
}

# ---------------------------------------------------------------------------
# AQI categories (official CPCB names, colours and health impacts)
# ---------------------------------------------------------------------------
CATEGORIES = [
    {
        "name": "Good", "low": 0, "high": 50,
        "color": "#00B050", "text_color": "#FFFFFF",
        "meaning": "Air quality is clean and poses little or no risk.",
        "health_impact": "Minimal impact.",
        "advice": [
            "Enjoy outdoor activities as usual.",
            "A good time to open windows and ventilate your home.",
        ],
    },
    {
        "name": "Satisfactory", "low": 51, "high": 100,
        "color": "#92D050", "text_color": "#1B1B1B",
        "meaning": "Air quality is acceptable for most people.",
        "health_impact": "Minor breathing discomfort to sensitive people.",
        "advice": [
            "Most people can continue normal outdoor activities.",
            "People who are unusually sensitive should reduce long, heavy exercise outdoors.",
        ],
    },
    {
        "name": "Moderate", "low": 101, "high": 200,
        "color": "#FFFF00", "text_color": "#1B1B1B",
        "meaning": "Air quality may affect sensitive groups.",
        "health_impact": "Breathing discomfort to people with lung disease such as asthma, "
                         "and discomfort to people with heart disease, children and older adults.",
        "advice": [
            "Children, older adults and people with asthma or heart disease should limit "
            "prolonged outdoor exertion.",
            "Keep any prescribed inhalers or medicines handy.",
        ],
    },
    {
        "name": "Poor", "low": 201, "high": 300,
        "color": "#FF9900", "text_color": "#1B1B1B",
        "meaning": "Air quality is unhealthy with prolonged exposure.",
        "health_impact": "Breathing discomfort to most people on prolonged exposure.",
        "advice": [
            "Reduce prolonged or heavy outdoor activity.",
            "Sensitive groups should stay indoors as much as possible.",
            "Consider wearing a well-fitted N95/FFP2 mask outdoors.",
        ],
    },
    {
        "name": "Very Poor", "low": 301, "high": 400,
        "color": "#FF0000", "text_color": "#FFFFFF",
        "meaning": "Air quality is very unhealthy.",
        "health_impact": "Respiratory illness on prolonged exposure. Effects may be more "
                         "pronounced in people with lung and heart diseases.",
        "advice": [
            "Avoid outdoor exercise; everyone should limit time outside.",
            "Keep windows closed; use an air purifier if available.",
            "Wear an N95/FFP2 mask if you must go out.",
        ],
    },
    {
        "name": "Severe", "low": 401, "high": 500,
        "color": "#C00000", "text_color": "#FFFFFF",
        "meaning": "Air quality is hazardous - a health emergency level.",
        "health_impact": "Affects healthy people and seriously impacts those with existing "
                         "diseases, even during light physical activity.",
        "advice": [
            "Stay indoors and avoid all outdoor physical activity.",
            "Follow advisories issued by local health authorities.",
            "Seek medical help if you have breathing difficulty or chest pain.",
        ],
    },
]

HEALTH_DISCLAIMER = (
    "These recommendations are general information based on the CPCB category "
    "descriptions. They are not medical advice. Please consult a doctor for "
    "personal health concerns."
)


@dataclass
class AQIResult:
    """Everything the app needs to know about one AQI calculation."""

    aqi: int | None                       # None when the standard cannot be applied
    category: dict | None                 # one entry from CATEGORIES
    dominant_pollutant: str | None        # pollutant code, e.g. "pm2_5"
    averages: dict = field(default_factory=dict)      # code -> average (µg/m³) or None
    sub_indices: dict = field(default_factory=dict)   # code -> sub-index or None
    message: str = ""                     # explanation shown to the user
    standard: str = AQI_STANDARD

    @property
    def is_valid(self) -> bool:
        return self.aqi is not None


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def is_valid_measurement(value) -> bool:
    """True if value is a real, finite, non-negative number."""
    if value is None or isinstance(value, bool):
        return False
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and number >= 0


def get_category(aqi: float | None) -> dict | None:
    """Return the CPCB category dictionary for an AQI value (0-500)."""
    if aqi is None or not is_valid_measurement(aqi):
        return None
    aqi = round(aqi)
    for category in CATEGORIES:
        if aqi <= category["high"]:
            return category
    return CATEGORIES[-1]          # anything above 500 is still "Severe"


def calculate_sub_index(pollutant: str, concentration) -> float | None:
    """
    Convert one pollutant's average concentration into a sub-index (0-500).

    Formula (linear interpolation inside the matching breakpoint row):

        I = I_low + (C - C_low) * (I_high - I_low) / (C_high - C_low)

    `concentration` must be in µg/m³ (CO is converted to mg/m³ here).
    Returns None for unknown pollutants or invalid values.
    """
    if pollutant not in BREAKPOINTS or not is_valid_measurement(concentration):
        return None

    c = float(concentration)
    if pollutant == "co":
        c = c / 1000.0             # µg/m³ -> mg/m³

    for c_low, c_high, i_low, i_high in BREAKPOINTS[pollutant]:
        if c <= c_high:
            return i_low + (c - c_low) * (i_high - i_low) / (c_high - c_low)

    return 500.0                   # above the top of the scale -> capped


def calculate_aqi(averages: dict) -> AQIResult:
    """
    Calculate the overall NAQI from averaged concentrations.

    `averages` maps pollutant code -> average concentration (µg/m³) that has
    already been averaged over the correct period (see compute_averages).
    """
    sub_indices = {code: calculate_sub_index(code, averages.get(code))
                   for code in POLLUTANT_CODES}
    valid = {code: value for code, value in sub_indices.items() if value is not None}

    result = AQIResult(aqi=None, category=None, dominant_pollutant=None,
                       averages=dict(averages), sub_indices=sub_indices)

    if len(valid) < 3:
        result.message = (f"AQI not calculated: the CPCB standard needs at least 3 pollutants, "
                          f"but only {len(valid)} had enough valid data.")
        return result
    if "pm2_5" not in valid and "pm10" not in valid:
        result.message = "AQI not calculated: the CPCB standard needs PM2.5 or PM10 data."
        return result

    dominant = max(valid, key=valid.get)
    result.aqi = int(round(valid[dominant]))
    result.category = get_category(result.aqi)
    result.dominant_pollutant = dominant
    result.message = (f"AQI calculated from {len(valid)} pollutants. "
                      f"Dominant pollutant: {POLLUTANTS[dominant]['name']}.")
    return result


def compute_averages(hourly: pd.DataFrame, end_time: datetime | None = None) -> dict:
    """
    Average each pollutant over the period required by the NAQI standard.

    `hourly` must have a "time" column (timezone-aware UTC datetimes) and one
    column per pollutant code with hourly concentrations in µg/m³.
    The window is (end_time - N hours, end_time]. Invalid values (missing,
    negative) are ignored. If too few valid hours remain, the average is None.
    """
    if hourly is None or hourly.empty or "time" not in hourly.columns:
        return {code: None for code in POLLUTANT_CODES}

    if end_time is None:
        end_time = hourly["time"].max()

    averages = {}
    for code in POLLUTANT_CODES:
        if code not in hourly.columns:
            averages[code] = None
            continue
        hours = POLLUTANTS[code]["averaging_hours"]
        start_time = end_time - timedelta(hours=hours)
        window = hourly[(hourly["time"] > start_time) & (hourly["time"] <= end_time)]
        values = pd.to_numeric(window[code], errors="coerce")
        values = values[values >= 0].dropna()
        if len(values) >= MIN_HOURS_REQUIRED[hours]:
            averages[code] = round(float(values.mean()), 2)
        else:
            averages[code] = None
    return averages


def evaluate_air_quality(hourly: pd.DataFrame, end_time: datetime | None = None) -> AQIResult:
    """One-step helper: average the hourly data, then calculate the AQI."""
    return calculate_aqi(compute_averages(hourly, end_time))


def aqi_timeline(hourly: pd.DataFrame, forecast: pd.DataFrame | None = None,
                 hours_back: int = 24) -> pd.DataFrame:
    """
    Calculate the AQI for EVERY hour: the last `hours_back` hours and all
    forecast hours. Each hour uses the same NAQI rules (24 h / 8 h averages
    ending at that hour), so it is a "rolling" AQI.

    Forecast hours mix measured past data with the provider's model forecast,
    so they are an estimate and are marked with is_forecast = True.
    """
    columns = ["time", "aqi", "category", "dominant", "is_forecast"]
    if hourly is None or hourly.empty:
        return pd.DataFrame(columns=columns)

    data = hourly
    if forecast is not None and not forecast.empty:
        data = pd.concat([hourly, forecast], ignore_index=True)

    now = hourly["time"].max()
    rows = []
    for moment in data.loc[data["time"] > now - timedelta(hours=hours_back), "time"]:
        result = evaluate_air_quality(data, moment)
        rows.append({
            "time": moment,
            "aqi": result.aqi,
            "category": result.category["name"] if result.category else None,
            "dominant": result.dominant_pollutant,
            "is_forecast": moment > now,
        })
    return pd.DataFrame(rows, columns=columns)
