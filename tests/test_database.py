"""Tests for database.py (uses a temporary database file, never the real one)."""

from datetime import date, datetime, timezone

import pytest

import database


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "test.db"
    database.init_db(path)
    return path


def _record(city="Delhi", day=1, aqi=150, is_sample=False, source="open-meteo"):
    return {"city": city, "country": "India", "latitude": 28.6, "longitude": 77.2,
            "observed_at": datetime(2026, 10, day, 6, tzinfo=timezone.utc),
            "pm2_5": 75.0, "pm10": 120.0, "no2": 40.0, "so2": 10.0, "co": 900.0, "o3": 30.0,
            "aqi": aqi, "category": "Moderate", "dominant_pollutant": "pm2_5",
            "aqi_standard": "India NAQI (CPCB)", "data_source": source,
            "is_sample": is_sample}


def test_save_and_read_back(db):
    assert database.save_observation(_record(), db) is True
    rows = database.get_observations(db_path=db)
    assert len(rows) == 1
    assert rows.iloc[0]["city"] == "Delhi"
    assert rows.iloc[0]["aqi"] == 150


def test_duplicate_is_skipped(db):
    assert database.save_observation(_record(), db) is True
    assert database.save_observation(_record(), db) is False
    assert database.count_observations(db) == 1


def test_filter_by_city_and_date(db):
    database.save_observation(_record("Delhi", 1), db)
    database.save_observation(_record("Delhi", 5), db)
    database.save_observation(_record("Mumbai", 5), db)
    assert len(database.get_observations("Delhi", db_path=db)) == 2
    assert len(database.get_observations(start_date=date(2026, 10, 3), db_path=db)) == 2
    assert len(database.get_observations("Delhi", date(2026, 10, 3), date(2026, 10, 5),
                                         db_path=db)) == 1
    assert database.get_cities(db) == ["Delhi", "Mumbai"]


def test_live_and_sample_filter_and_delete(db):
    database.save_observation(_record(day=1), db)
    database.save_observation(_record(day=2, is_sample=True, source="sample"), db)
    assert len(database.get_observations(data_type="live", db_path=db)) == 1
    assert len(database.get_observations(data_type="sample", db_path=db)) == 1
    assert database.delete_sample_observations(db) == 1
    assert database.count_observations(db) == 1


def test_null_aqi_is_allowed(db):
    database.save_observation(_record(aqi=None), db)
    rows = database.get_observations(db_path=db)
    assert rows.iloc[0]["aqi"] is None or rows["aqi"].isna().iloc[0]


def test_missing_required_fields(db):
    with pytest.raises(ValueError):
        database.save_observation({"city": "Delhi"}, db)


def test_sql_injection_text_is_treated_as_data(db):
    database.save_observation(_record(), db)
    rows = database.get_observations("Delhi' OR '1'='1", db_path=db)
    assert rows.empty
    assert database.count_observations(db) == 1


def test_csv_export(db):
    database.save_observation(_record(), db)
    csv_text = database.to_csv_bytes(database.get_observations(db_path=db)).decode("utf-8-sig")
    assert csv_text.splitlines()[0].startswith("id,city,country")
    assert "Delhi" in csv_text
