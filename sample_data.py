"""
sample_data.py
==============
Built-in SAMPLE data so the project can be demonstrated without internet
or an API key.

IMPORTANT: These numbers are made up for demonstration. They are loosely
based on typical pollution levels in each city but are NOT real
measurements. The app labels them clearly as "Sample data".

How it works:
    Each city has a "base" concentration for every pollutant. We create
    24+ hourly values by adding a daily pattern (higher in the morning and
    evening rush hours) and a little random noise. The random generator is
    seeded with the city name and date, so the same city on the same day
    always gives the same numbers - useful for a repeatable demo.
"""

from __future__ import annotations

import zlib
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

SAMPLE_SOURCE = "Sample data (demo values, not real measurements)"

# Base concentrations in µg/m³ (CO also in µg/m³).
SAMPLE_CITIES = {
    "Delhi":      {"country": "India", "lat": 28.61, "lon": 77.21,
                   "base": {"pm2_5": 115, "pm10": 230, "no2": 62, "so2": 16, "co": 1900, "o3": 48}},
    "Mumbai":     {"country": "India", "lat": 19.08, "lon": 72.88,
                   "base": {"pm2_5": 48, "pm10": 105, "no2": 38, "so2": 12, "co": 1100, "o3": 42}},
    "Kolkata":    {"country": "India", "lat": 22.57, "lon": 88.36,
                   "base": {"pm2_5": 72, "pm10": 140, "no2": 45, "so2": 14, "co": 1400, "o3": 40}},
    "Chennai":    {"country": "India", "lat": 13.08, "lon": 80.27,
                   "base": {"pm2_5": 32, "pm10": 68, "no2": 26, "so2": 10, "co": 800, "o3": 38}},
    "Bengaluru":  {"country": "India", "lat": 12.97, "lon": 77.59,
                   "base": {"pm2_5": 28, "pm10": 62, "no2": 30, "so2": 8, "co": 900, "o3": 35}},
    "Hyderabad":  {"country": "India", "lat": 17.39, "lon": 78.49,
                   "base": {"pm2_5": 40, "pm10": 88, "no2": 32, "so2": 9, "co": 950, "o3": 44}},
    "Lucknow":    {"country": "India", "lat": 26.85, "lon": 80.95,
                   "base": {"pm2_5": 95, "pm10": 180, "no2": 40, "so2": 13, "co": 1600, "o3": 46}},
    "Chandigarh": {"country": "India", "lat": 30.73, "lon": 76.78,
                   "base": {"pm2_5": 55, "pm10": 110, "no2": 28, "so2": 9, "co": 1000, "o3": 50}},
    "Shimla":     {"country": "India", "lat": 31.10, "lon": 77.17,
                   "base": {"pm2_5": 14, "pm10": 30, "no2": 10, "so2": 5, "co": 400, "o3": 55}},
    "London":     {"country": "United Kingdom", "lat": 51.51, "lon": -0.13,
                   "base": {"pm2_5": 10, "pm10": 18, "no2": 35, "so2": 4, "co": 300, "o3": 52}},
}


def list_sample_cities() -> list[str]:
    return sorted(SAMPLE_CITIES.keys())


def find_sample_city(name: str) -> str | None:
    """Case-insensitive lookup. Returns the proper city name or None."""
    cleaned = name.split(",")[0].strip().lower()
    for city in SAMPLE_CITIES:
        if city.lower() == cleaned:
            return city
    return None


def _seed_for(city: str, day: datetime) -> int:
    # zlib.crc32 gives the same number every run (Python's hash() does not).
    return zlib.crc32(f"{city}-{day:%Y-%m-%d}".encode("utf-8"))


def generate_hourly_data(city: str, end_time: datetime | None = None,
                         hours: int = 24) -> pd.DataFrame:
    """
    Create `hours` hourly rows ending at `end_time` (UTC) for a sample city.
    Returns a DataFrame with a "time" column and one column per pollutant.
    """
    info = SAMPLE_CITIES[city]
    if end_time is None:
        end_time = datetime.now(timezone.utc)
    end_time = end_time.replace(minute=0, second=0, microsecond=0)

    rng = np.random.default_rng(_seed_for(city, end_time))
    times = [end_time - timedelta(hours=h) for h in range(hours - 1, -1, -1)]

    # A day-level factor so different days look different (0.75x - 1.25x)
    day_factor = rng.uniform(0.75, 1.25)

    data = {"time": times}
    for code, base in info["base"].items():
        values = []
        for t in times:
            local_hour = (t.hour + 5.5) % 24          # rough Indian local time
            # Two rush-hour peaks (around 9 am and 8 pm local time)
            rush = 0.25 * np.exp(-((local_hour - 9) ** 2) / 6) + \
                   0.30 * np.exp(-((local_hour - 20) ** 2) / 8)
            if code == "o3":                           # ozone peaks in the afternoon sun
                rush = 0.45 * np.exp(-((local_hour - 14) ** 2) / 10)
            noise = rng.normal(0, 0.08)
            values.append(max(0.0, base * day_factor * (0.85 + rush + noise)))
        data[code] = np.round(values, 2)

    frame = pd.DataFrame(data)
    frame["time"] = pd.to_datetime(frame["time"], utc=True)
    return frame
