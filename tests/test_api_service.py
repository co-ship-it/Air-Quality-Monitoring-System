"""
Tests for api_service.py. Network calls are replaced with fake responses
(monkeypatch), so these tests run offline and never use a real API key.
"""

from datetime import datetime, timedelta, timezone

import pytest
import requests

import api_service
from aqi_calculator import evaluate_air_quality


class FakeResponse:
    def __init__(self, data, status=200):
        self._data, self.status_code = data, status

    def json(self):
        return self._data


# ---------- city name validation -------------------------------------------
@pytest.mark.parametrize("name, cleaned", [
    ("  Delhi ", "Delhi"), ("new   york", "new york"), ("Pune, India", "Pune, India"),
    ("São Paulo", "São Paulo"), ("Saint-Étienne", "Saint-Étienne")])
def test_valid_city_names(name, cleaned):
    assert api_service.validate_city_name(name) == cleaned


@pytest.mark.parametrize("bad", ["", "   ", "a", "12345", "Delhi<script>", "x" * 81, "Delhi; DROP"])
def test_invalid_city_names(bad):
    with pytest.raises(api_service.AirQualityError):
        api_service.validate_city_name(bad)


# ---------- sample data ----------------------------------------------------
def test_sample_city_works_and_is_labelled():
    reading = api_service.get_air_quality("delhi", "sample")
    assert reading.city == "Delhi"
    assert reading.is_sample is True
    assert "Sample" in reading.source
    assert len(reading.hourly) == 48              # 48 past hours
    assert len(reading.forecast) == 24            # 24 forecast hours
    assert reading.forecast["time"].min() > reading.observed_at
    assert evaluate_air_quality(reading.hourly, reading.observed_at).is_valid


def test_sample_data_is_repeatable():
    end = datetime(2026, 10, 1, 6, tzinfo=timezone.utc)
    first = api_service.fetch_sample("Mumbai", end)
    second = api_service.fetch_sample("Mumbai", end)
    assert first.hourly.equals(second.hourly)


def test_unknown_sample_city():
    with pytest.raises(api_service.CityNotFoundError):
        api_service.get_air_quality("Atlantis", "sample")


# ---------- Open-Meteo (mocked) ---------------------------------------------
def _fake_open_meteo(url, params=None, timeout=None):
    if "geocoding" in url:
        if params["name"].lower() == "nowhere":
            return FakeResponse({})                       # no "results" key = not found
        return FakeResponse({"results": [{"name": "Delhi", "country": "India",
                                          "country_code": "IN",
                                          "latitude": 28.65, "longitude": 77.23}]})
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    times = [int((now - timedelta(hours=h)).timestamp()) for h in range(30, -6, -1)]
    n = len(times)                                        # includes 5 future (forecast) hours
    return FakeResponse({"hourly": {
        "time": times, "pm2_5": [45.0] * n, "pm10": [60.0] * n,
        "nitrogen_dioxide": [30.0] * n, "sulphur_dioxide": [10.0] * n,
        "carbon_monoxide": [700.0] * n, "ozone": [40.0] * n}})


def test_open_meteo_success(monkeypatch):
    monkeypatch.setattr(api_service.requests, "get", _fake_open_meteo)
    reading = api_service.get_air_quality("Delhi", "open-meteo")
    assert reading.city == "Delhi" and reading.country == "India"
    assert reading.is_sample is False
    assert reading.observed_at <= datetime.now(timezone.utc)   # forecast hours split off
    assert len(reading.forecast) == 5                           # the 5 future hours
    assert reading.forecast["time"].min() > datetime.now(timezone.utc)
    result = evaluate_air_quality(reading.hourly, reading.observed_at)
    assert result.aqi == 75                                     # PM2.5 45 -> 75
    assert result.dominant_pollutant == "pm2_5"


def test_open_meteo_city_not_found(monkeypatch):
    monkeypatch.setattr(api_service.requests, "get", _fake_open_meteo)
    with pytest.raises(api_service.CityNotFoundError):
        api_service.get_air_quality("Nowhere", "open-meteo")


def test_connection_error_gives_friendly_message(monkeypatch):
    def broken(*args, **kwargs):
        raise requests.exceptions.ConnectionError("network down")
    monkeypatch.setattr(api_service.requests, "get", broken)
    with pytest.raises(api_service.AirQualityError, match="internet"):
        api_service.get_air_quality("Delhi", "open-meteo")


def test_timeout_gives_friendly_message(monkeypatch):
    def slow(*args, **kwargs):
        raise requests.exceptions.Timeout()
    monkeypatch.setattr(api_service.requests, "get", slow)
    with pytest.raises(api_service.AirQualityError, match="did not respond"):
        api_service.get_air_quality("Delhi", "open-meteo")


# ---------- OpenWeatherMap (mocked) and key safety ---------------------------
def test_openweathermap_without_key(monkeypatch):
    monkeypatch.delenv("OPENWEATHER_API_KEY", raising=False)
    assert "openweathermap" not in api_service.available_providers()
    with pytest.raises(api_service.AirQualityError, match="not configured"):
        api_service.get_air_quality("Delhi", "openweathermap")


def test_placeholder_key_is_ignored(monkeypatch):
    monkeypatch.setenv("OPENWEATHER_API_KEY", "your_api_key_here")
    assert api_service.get_api_key() is None


def test_invalid_key_message_does_not_leak_key(monkeypatch):
    secret = "SECRET123456"
    monkeypatch.setenv("OPENWEATHER_API_KEY", secret)
    monkeypatch.setattr(api_service.requests, "get", lambda *a, **k: FakeResponse({}, 401))
    with pytest.raises(api_service.AirQualityError) as info:
        api_service.get_air_quality("Delhi", "openweathermap")
    assert secret not in str(info.value)
    assert "API key" in str(info.value)


def test_openweathermap_success_keeps_provider_index_separate(monkeypatch):
    monkeypatch.setenv("OPENWEATHER_API_KEY", "testkey")
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

    def fake(url, params=None, timeout=None):
        if "geo" in url:
            return FakeResponse([{"name": "Delhi", "country": "IN", "lat": 28.6, "lon": 77.2}])
        items = [{"dt": int((now - timedelta(hours=h)).timestamp()), "main": {"aqi": 4},
                  "components": {"pm2_5": 75.0, "pm10": 120.0, "no2": 40.0,
                                 "so2": 10.0, "co": 900.0, "o3": 30.0}}
                 for h in range(25, -1, -1)]
        return FakeResponse({"list": items})

    monkeypatch.setattr(api_service.requests, "get", fake)
    reading = api_service.get_air_quality("Delhi", "openweathermap")
    result = evaluate_air_quality(reading.hourly, reading.observed_at)
    assert result.aqi == 150                      # our NAQI, from PM2.5 = 75
    assert "OpenWeatherMap's own 1-5 scale" in reading.provider_index
