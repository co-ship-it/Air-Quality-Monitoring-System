"""
api_service.py
==============
Gets air-quality data for a city from one of three sources:

    1. "sample"          - built-in demo data (no internet needed)
    2. "open-meteo"      - Open-Meteo Air Quality API (free, NO key needed)
    3. "openweathermap"  - OpenWeatherMap Air Pollution API (needs a free key)

Every source returns the same AirQualityReading object, so the rest of the
app does not care where the data came from.

Steps for live data:
    city name --(geocoding API)--> latitude/longitude
    latitude/longitude --(air quality API)--> last ~24 hours of hourly data

Security: the OpenWeatherMap key is read from an environment variable
(OPENWEATHER_API_KEY, usually set in a .env file). It is never written in
the code, and error messages never include the request URL (which would
contain the key).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests
import truststore
from dotenv import load_dotenv

import sample_data
from aqi_calculator import POLLUTANT_CODES

load_dotenv()          # reads the .env file (if present) into environment variables

# Use the Windows certificate store for HTTPS. Without this, antivirus
# "HTTPS scanning" or college/office networks can cause
# "CERTIFICATE_VERIFY_FAILED" errors even though the browser works.
truststore.inject_into_ssl()

REQUEST_TIMEOUT = 10   # seconds

OPEN_METEO_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
OWM_GEOCODE_URL = "https://api.openweathermap.org/geo/1.0/direct"
OWM_HISTORY_URL = "https://api.openweathermap.org/data/2.5/air_pollution/history"
OWM_FORECAST_URL = "https://api.openweathermap.org/data/2.5/air_pollution/forecast"

# Open-Meteo variable name -> our pollutant code
OPEN_METEO_FIELDS = {
    "pm2_5": "pm2_5",
    "pm10": "pm10",
    "nitrogen_dioxide": "no2",
    "sulphur_dioxide": "so2",
    "carbon_monoxide": "co",
    "ozone": "o3",
}

# OpenWeatherMap's OWN index (1-5). This is NOT the Indian NAQI.
OWM_INDEX_LABELS = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}

PROVIDER_LABELS = {
    "sample": "Sample data (demo)",
    "open-meteo": "Open-Meteo (live, no key needed)",
    "openweathermap": "OpenWeatherMap (live, API key needed)",
}

SOURCE_DESCRIPTIONS = {
    "open-meteo": "Open-Meteo Air Quality API - modelled data from the Copernicus "
                  "Atmosphere Monitoring Service (CAMS), about 11-40 km resolution.",
    "openweathermap": "OpenWeatherMap Air Pollution API - modelled/estimated data "
                      "for the city's coordinates.",
    "sample": sample_data.SAMPLE_SOURCE,
}


class AirQualityError(Exception):
    """An error with a message that is safe and friendly to show to the user."""


class CityNotFoundError(AirQualityError):
    """The city name could not be found."""


@dataclass
class AirQualityReading:
    city: str
    country: str
    latitude: float
    longitude: float
    hourly: pd.DataFrame              # PAST hours: "time" (UTC) + one column per pollutant (µg/m³)
    latest: dict                      # most recent hourly value for each pollutant
    observed_at: datetime             # time of the most recent hourly record (UTC)
    provider: str                     # "sample", "open-meteo" or "openweathermap"
    source: str                       # human-readable source description
    is_sample: bool = False
    provider_index: str | None = None # provider's own index text (NOT NAQI)
    forecast: pd.DataFrame = field(default_factory=pd.DataFrame)  # FUTURE hours (may be empty)
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def has_forecast(self) -> bool:
        return not self.forecast.empty

    @property
    def display_name(self) -> str:
        return f"{self.city}, {self.country}" if self.country else self.city


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def get_api_key() -> str | None:
    """Return the OpenWeatherMap key from the environment, or None if not set."""
    key = os.getenv("OPENWEATHER_API_KEY", "").strip()
    if not key or key.lower().startswith("your_"):
        return None                       # empty or still the placeholder text
    return key


def available_providers() -> list[str]:
    providers = ["sample", "open-meteo"]
    if get_api_key():
        providers.append("openweathermap")
    return providers


def validate_city_name(name: str) -> str:
    """
    Clean and check a city name typed by the user.
    Allowed: letters (any language), spaces and . , ' - ( )
    Raises AirQualityError with a helpful message if it is not valid.
    """
    cleaned = " ".join((name or "").split())      # trim + collapse spaces
    if not cleaned:
        raise AirQualityError("Please enter a city name.")
    if len(cleaned) < 2 or len(cleaned) > 80:
        raise AirQualityError("City name must be between 2 and 80 characters.")
    allowed_symbols = set(" .,'-()")
    if not all(ch.isalpha() or ch in allowed_symbols for ch in cleaned):
        raise AirQualityError("City name can contain only letters, spaces and . , ' - ( )")
    if not any(ch.isalpha() for ch in cleaned):
        raise AirQualityError("City name must contain letters.")
    return cleaned


def _get_json(url: str, params: dict, service: str):
    """GET a URL and return the JSON body, turning failures into friendly errors."""
    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.Timeout:
        raise AirQualityError(f"{service} did not respond in time. Please try again.") from None
    except requests.exceptions.ConnectionError:
        raise AirQualityError(f"Could not connect to {service}. Check your internet "
                              f"connection, or switch to Sample data mode.") from None
    except requests.exceptions.RequestException:
        raise AirQualityError(f"Request to {service} failed.") from None

    if response.status_code == 401:
        raise AirQualityError(f"{service} rejected the API key. Check OPENWEATHER_API_KEY in "
                              f"your .env file (new keys can take up to 2 hours to activate).")
    if response.status_code == 429:
        raise AirQualityError(f"Too many requests to {service}. Wait a minute and try again.")
    if response.status_code != 200:
        raise AirQualityError(f"{service} returned an error (HTTP {response.status_code}).")
    try:
        return response.json()
    except ValueError:
        raise AirQualityError(f"{service} sent a response that could not be read.") from None


def _split_hourly(frame: pd.DataFrame, now: datetime) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Clean the values and split the rows into PAST hours (time <= now) and
    FORECAST hours (time > now). Raises an error if there is no past data.
    """
    if not pd.api.types.is_datetime64_any_dtype(frame["time"]):
        frame["time"] = pd.to_datetime(frame["time"], unit="s", utc=True)
    frame = frame.sort_values("time").reset_index(drop=True)
    for code in POLLUTANT_CODES:
        if code not in frame.columns:
            frame[code] = float("nan")
        values = pd.to_numeric(frame[code], errors="coerce")
        frame[code] = values.where(values >= 0)       # negative values -> missing
    frame = frame.dropna(subset=POLLUTANT_CODES, how="all")[["time"] + POLLUTANT_CODES]

    past = frame[frame["time"] <= now].reset_index(drop=True)
    future = frame[frame["time"] > now].reset_index(drop=True)
    if past.empty:
        raise AirQualityError("The data source returned no recent measurements for this city.")
    return past, future


def _latest_values(frame: pd.DataFrame) -> tuple[dict, datetime]:
    last = frame.iloc[-1]
    latest = {code: (None if pd.isna(last[code]) else float(last[code]))
              for code in POLLUTANT_CODES}
    return latest, last["time"].to_pydatetime()


# ---------------------------------------------------------------------------
# Source 1: sample data
# ---------------------------------------------------------------------------
def fetch_sample(city: str, end_time: datetime | None = None) -> AirQualityReading:
    name = sample_data.find_sample_city(city)
    if name is None:
        raise CityNotFoundError(
            f"'{city}' is not in the sample data set. Sample cities: "
            + ", ".join(sample_data.list_sample_cities()) + ". "
            "Switch to Live data to search any city.")
    info = sample_data.SAMPLE_CITIES[name]
    now = (end_time or datetime.now(timezone.utc)).replace(minute=0, second=0, microsecond=0)
    # 48 past hours (for the 24-hour AQI trend) + 24 "forecast" hours
    frame = sample_data.generate_hourly_data(name, now + timedelta(hours=24), hours=72)
    hourly, forecast = _split_hourly(frame, now)
    latest, observed_at = _latest_values(hourly)
    return AirQualityReading(
        city=name, country=info["country"], latitude=info["lat"], longitude=info["lon"],
        hourly=hourly, latest=latest, observed_at=observed_at,
        provider="sample", source=SOURCE_DESCRIPTIONS["sample"], is_sample=True,
        forecast=forecast)


# ---------------------------------------------------------------------------
# Source 2: Open-Meteo (no key)
# ---------------------------------------------------------------------------
def geocode_open_meteo(city: str) -> dict:
    """Find a city's coordinates. Accepts "City" or "City, Country"."""
    parts = [p.strip() for p in city.split(",")]
    name, country = parts[0], (parts[1] if len(parts) > 1 else "")
    data = _get_json(OPEN_METEO_GEOCODE_URL,
                     {"name": name, "count": 10, "language": "en", "format": "json"},
                     "Open-Meteo geocoding")
    results = data.get("results") or []
    if country:
        wanted = country.lower()
        results = [r for r in results
                   if wanted in (r.get("country", "").lower(), r.get("country_code", "").lower())]
    if not results:
        raise CityNotFoundError(f"City '{city}' was not found. Check the spelling, or try "
                                f"adding the country, e.g. 'Pune, India'.")
    best = results[0]
    return {"city": best["name"], "country": best.get("country", ""),
            "lat": best["latitude"], "lon": best["longitude"]}


def fetch_open_meteo(city: str) -> AirQualityReading:
    place = geocode_open_meteo(city)
    params = {
        "latitude": place["lat"], "longitude": place["lon"],
        "hourly": ",".join(OPEN_METEO_FIELDS.keys()),
        "past_days": 2, "forecast_days": 2,
        "timeformat": "unixtime", "timezone": "GMT",
    }
    data = _get_json(OPEN_METEO_AQ_URL, params, "Open-Meteo air quality")
    hourly_json = data.get("hourly")
    if not hourly_json or "time" not in hourly_json:
        raise AirQualityError("Open-Meteo returned no hourly air-quality data for this location.")

    frame = pd.DataFrame({"time": hourly_json["time"]})
    for api_name, code in OPEN_METEO_FIELDS.items():
        frame[code] = hourly_json.get(api_name, [None] * len(frame))

    hourly, forecast = _split_hourly(frame, datetime.now(timezone.utc))
    latest, observed_at = _latest_values(hourly)
    return AirQualityReading(
        city=place["city"], country=place["country"],
        latitude=place["lat"], longitude=place["lon"],
        hourly=hourly, latest=latest, observed_at=observed_at,
        provider="open-meteo", source=SOURCE_DESCRIPTIONS["open-meteo"],
        forecast=forecast)


# ---------------------------------------------------------------------------
# Source 3: OpenWeatherMap (needs key)
# ---------------------------------------------------------------------------
def fetch_openweathermap(city: str) -> AirQualityReading:
    key = get_api_key()
    if key is None:
        raise AirQualityError("OpenWeatherMap API key is not configured. Add "
                              "OPENWEATHER_API_KEY to your .env file, or use Open-Meteo.")

    places = _get_json(OWM_GEOCODE_URL, {"q": city, "limit": 1, "appid": key},
                       "OpenWeatherMap geocoding")
    if not places:
        raise CityNotFoundError(f"City '{city}' was not found. Check the spelling, or try "
                                f"'City,CountryCode', e.g. 'Pune,IN'.")
    place = places[0]

    now = datetime.now(timezone.utc)
    params = {"lat": place["lat"], "lon": place["lon"],
              "start": int((now - timedelta(hours=50)).timestamp()),
              "end": int(now.timestamp()), "appid": key}
    data = _get_json(OWM_HISTORY_URL, params, "OpenWeatherMap air pollution")
    items = data.get("list") or []
    if not items:
        raise AirQualityError("OpenWeatherMap returned no air-quality data for this location.")

    # The forecast is a bonus: if it fails, the app still works without it.
    try:
        forecast_data = _get_json(OWM_FORECAST_URL, {"lat": place["lat"], "lon": place["lon"],
                                                     "appid": key}, "OpenWeatherMap forecast")
        forecast_items = forecast_data.get("list") or []
    except AirQualityError:
        forecast_items = []

    rows = []
    for item in items + forecast_items:
        comp = item.get("components", {})
        rows.append({"time": item.get("dt"), "pm2_5": comp.get("pm2_5"),
                     "pm10": comp.get("pm10"), "no2": comp.get("no2"),
                     "so2": comp.get("so2"), "co": comp.get("co"), "o3": comp.get("o3")})
    frame = pd.DataFrame(rows).drop_duplicates(subset="time")
    hourly, forecast = _split_hourly(frame, now)
    forecast = forecast[forecast["time"] <= now + timedelta(hours=48)].reset_index(drop=True)
    latest, observed_at = _latest_values(hourly)

    owm_index = items[-1].get("main", {}).get("aqi")
    provider_index = None
    if owm_index in OWM_INDEX_LABELS:
        provider_index = (f"{owm_index} ({OWM_INDEX_LABELS[owm_index]}) on OpenWeatherMap's "
                          f"own 1-5 scale - not the same as the Indian NAQI")

    return AirQualityReading(
        city=place.get("name", city), country=place.get("country", ""),
        latitude=place["lat"], longitude=place["lon"],
        hourly=hourly, latest=latest, observed_at=observed_at,
        provider="openweathermap", source=SOURCE_DESCRIPTIONS["openweathermap"],
        provider_index=provider_index, forecast=forecast)


# ---------------------------------------------------------------------------
# Main entry point used by the app
# ---------------------------------------------------------------------------
def get_air_quality(city: str, provider: str = "sample") -> AirQualityReading:
    """Validate the city name and fetch data from the chosen provider."""
    city = validate_city_name(city)
    if provider == "sample":
        return fetch_sample(city)
    if provider == "open-meteo":
        return fetch_open_meteo(city)
    if provider == "openweathermap":
        return fetch_openweathermap(city)
    raise AirQualityError(f"Unknown data provider: {provider}")
