"""
Unit tests for WeatherApp Pro.
Run with: pytest tests/ -v --cov=app --cov-report=term-missing
"""
from __future__ import annotations
import json
from datetime import datetime
from typing import Any, Dict
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from app.api.owm_client import (
    WeatherAPIClient, WeatherAPIError,
    parse_current_weather, parse_forecast, parse_city_search,
)
from app.models.weather import CurrentWeather, ForecastData


# ── Fixtures ────────────────────────────────────────────────────────────────

CURRENT_WEATHER_PAYLOAD: Dict[str, Any] = {
    "coord": {"lon": -0.1257, "lat": 51.5085},
    "weather": [{"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d"}],
    "main": {
        "temp": 18.5, "feels_like": 17.2, "temp_min": 16.0,
        "temp_max": 21.0, "humidity": 60, "pressure": 1015,
    },
    "visibility": 10000,
    "wind": {"speed": 4.1, "deg": 270, "gust": 6.2},
    "dt": 1700000000,
    "sys": {"country": "GB", "sunrise": 1699999000, "sunset": 1700020000},
    "name": "London",
}

FORECAST_PAYLOAD: Dict[str, Any] = {
    "city": {"name": "London", "country": "GB", "coord": {"lat": 51.5, "lon": -0.12}},
    "list": [
        {
            "dt": 1700000000 + i * 10800,
            "main": {"temp": 18.0 + i, "feels_like": 17.0, "humidity": 60, "pressure": 1015},
            "weather": [{"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d"}],
            "wind": {"speed": 3.5, "deg": 200},
            "pop": 0.1 * (i % 3),
        }
        for i in range(40)
    ],
}

CITY_SEARCH_PAYLOAD = [
    {"name": "London", "country": "GB", "state": "England", "lat": 51.5085, "lon": -0.1257},
    {"name": "London", "country": "CA", "state": "Ontario", "lat": 42.9834, "lon": -81.2333},
]


# ── Parser Tests ──────────────────────────────────────────────────────────────

class TestParseCurrentWeather:
    def test_parses_city_and_country(self):
        w = parse_current_weather(CURRENT_WEATHER_PAYLOAD, "metric")
        assert w.city == "London"
        assert w.country == "GB"

    def test_parses_temperatures(self):
        w = parse_current_weather(CURRENT_WEATHER_PAYLOAD, "metric")
        assert w.temp == pytest.approx(18.5)
        assert w.feels_like == pytest.approx(17.2)
        assert w.temp_min == pytest.approx(16.0)
        assert w.temp_max == pytest.approx(21.0)

    def test_parses_wind(self):
        w = parse_current_weather(CURRENT_WEATHER_PAYLOAD, "metric")
        assert w.wind.speed == pytest.approx(4.1)
        assert w.wind.deg == 270
        assert w.wind.direction == "W"

    def test_parses_condition(self):
        w = parse_current_weather(CURRENT_WEATHER_PAYLOAD, "metric")
        assert w.condition.main == "Clear"
        assert "sky" in w.condition.description.lower()

    def test_parses_sunrise_sunset(self):
        w = parse_current_weather(CURRENT_WEATHER_PAYLOAD, "metric")
        assert isinstance(w.sunrise, datetime)
        assert isinstance(w.sunset, datetime)

    def test_temp_display_celsius(self):
        w = parse_current_weather(CURRENT_WEATHER_PAYLOAD, "metric")
        assert "°C" in w.temp_display()

    def test_temp_display_fahrenheit(self):
        w = parse_current_weather(CURRENT_WEATHER_PAYLOAD, "imperial")
        assert "°F" in w.temp_display()

    def test_coordinates(self):
        w = parse_current_weather(CURRENT_WEATHER_PAYLOAD, "metric")
        assert w.lat == pytest.approx(51.5085)
        assert w.lon == pytest.approx(-0.1257)


class TestParseForecast:
    def test_creates_hourly_entries(self):
        f = parse_forecast(FORECAST_PAYLOAD, "metric")
        assert len(f.hourly) == 40

    def test_groups_into_daily(self):
        f = parse_forecast(FORECAST_PAYLOAD, "metric")
        assert len(f.daily) >= 1

    def test_daily_min_max(self):
        f = parse_forecast(FORECAST_PAYLOAD, "metric")
        for day in f.daily:
            assert day.temp_min <= day.temp_max

    def test_city_info(self):
        f = parse_forecast(FORECAST_PAYLOAD, "metric")
        assert f.city == "London"
        assert f.country == "GB"


class TestParseCitySearch:
    def test_parses_results(self):
        results = parse_city_search(CITY_SEARCH_PAYLOAD)
        assert len(results) == 2

    def test_display_name(self):
        results = parse_city_search(CITY_SEARCH_PAYLOAD)
        assert "London" in results[0].display_name
        assert "GB" in results[0].display_name

    def test_state_included(self):
        results = parse_city_search(CITY_SEARCH_PAYLOAD)
        assert "England" in results[0].display_name


# ── Input Sanitization Tests ──────────────────────────────────────────────────

class TestInputSanitization:
    def test_empty_city_raises(self):
        with pytest.raises(ValueError, match="empty"):
            WeatherAPIClient._sanitize_city("   ")

    def test_too_long_city_raises(self):
        with pytest.raises(ValueError, match="long"):
            WeatherAPIClient._sanitize_city("a" * 101)

    def test_invalid_chars_raise(self):
        with pytest.raises(ValueError):
            WeatherAPIClient._sanitize_city("City<script>")

    def test_valid_city(self):
        assert WeatherAPIClient._sanitize_city("  London  ") == "London"

    def test_city_with_apostrophe(self):
        assert WeatherAPIClient._sanitize_city("Coeur d'Alene") == "Coeur d'Alene"

    def test_unicode_city(self):
        assert WeatherAPIClient._sanitize_city("München") == "München"


# ── Wind Direction Tests ──────────────────────────────────────────────────────

class TestWindDirection:
    from app.models.weather import WindData

    def test_north(self):
        from app.models.weather import WindData
        w = WindData(speed=1, deg=0)
        assert w.direction == "N"

    def test_south(self):
        from app.models.weather import WindData
        w = WindData(speed=1, deg=180)
        assert w.direction == "S"

    def test_east(self):
        from app.models.weather import WindData
        w = WindData(speed=1, deg=90)
        assert w.direction == "E"

    def test_west(self):
        from app.models.weather import WindData
        w = WindData(speed=1, deg=270)
        assert w.direction == "W"

    def test_no_deg_returns_na(self):
        from app.models.weather import WindData
        w = WindData(speed=1, deg=None)
        assert w.direction == "N/A"


# ── API Client Mock Tests ─────────────────────────────────────────────────────

class TestWeatherAPIClient:
    @patch("app.api.owm_client.WeatherAPIClient._get")
    @patch.object(type(MagicMock()), "api_key", new_callable=PropertyMock)
    def test_get_current_weather_calls_endpoint(self, mock_key, mock_get):
        mock_get.return_value = CURRENT_WEATHER_PAYLOAD
        client = WeatherAPIClient.__new__(WeatherAPIClient)
        client._cfg = MagicMock()
        client._cfg.base_url = "https://api.openweathermap.org/data/2.5"
        client._cfg.api_key = "test_key"
        client._rate_limiter = MagicMock()
        client._session = MagicMock()
        client._get = mock_get

        result = client.get_current_weather("London", "metric")
        mock_get.assert_called_once()
        args = mock_get.call_args
        assert "weather" in args[0][0]
        assert args[0][1]["q"] == "London"


# ── Rate Limiter Tests ────────────────────────────────────────────────────────

class TestRateLimiter:
    def test_does_not_block_within_limit(self):
        from app.api.owm_client import RateLimiter
        rl = RateLimiter(max_calls=10, period=60)
        import time
        start = time.monotonic()
        for _ in range(5):
            rl.acquire()
        elapsed = time.monotonic() - start
        assert elapsed < 0.5  # Should be near instant


# ── Database Tests ────────────────────────────────────────────────────────────

class TestDatabase:
    @pytest.fixture
    def tmp_db(self, tmp_path):
        from app.utils.database import Database
        return Database(db_path=tmp_path / "test.db")

    def test_cache_set_and_get(self, tmp_db):
        tmp_db.cache_set("key1", {"data": "value"}, ttl=600)
        result = tmp_db.cache_get("key1")
        assert result == {"data": "value"}

    def test_cache_miss_returns_none(self, tmp_db):
        result = tmp_db.cache_get("nonexistent")
        assert result is None

    def test_cache_expired_returns_none(self, tmp_db):
        tmp_db.cache_set("expired_key", {"x": 1}, ttl=-1)
        result = tmp_db.cache_get("expired_key")
        assert result is None

    def test_history_add_and_get(self, tmp_db):
        tmp_db.history_add("London", "GB", 51.5, -0.1)
        history = tmp_db.history_get()
        assert len(history) == 1
        assert history[0]["city"] == "London"

    def test_favorites_add_and_get(self, tmp_db):
        from app.models.weather import FavoriteCity
        fav = FavoriteCity(id=None, name="Paris", country="FR", lat=48.85, lon=2.35)
        tmp_db.favorites_add(fav)
        favs = tmp_db.favorites_get()
        assert len(favs) == 1
        assert favs[0].name == "Paris"

    def test_favorites_exists(self, tmp_db):
        from app.models.weather import FavoriteCity
        fav = FavoriteCity(id=None, name="Tokyo", country="JP", lat=35.68, lon=139.69)
        tmp_db.favorites_add(fav)
        assert tmp_db.favorites_exists(35.68, 139.69) is True
        assert tmp_db.favorites_exists(0.0, 0.0) is False

    def test_favorites_remove(self, tmp_db):
        from app.models.weather import FavoriteCity
        fav = FavoriteCity(id=None, name="Berlin", country="DE", lat=52.52, lon=13.40)
        tmp_db.favorites_add(fav)
        favs = tmp_db.favorites_get()
        tmp_db.favorites_remove(favs[0].id)
        assert tmp_db.favorites_get() == []


# ── Service Tests (mocked) ────────────────────────────────────────────────────

class TestWeatherService:
    @pytest.fixture
    def service_with_mock(self, tmp_path):
        from app.utils.database import Database
        from app.services.weather_service import WeatherService
        import app.services.weather_service as svc_module

        mock_client = MagicMock()
        mock_client.get_current_weather.return_value = CURRENT_WEATHER_PAYLOAD
        mock_client.get_forecast.return_value = FORECAST_PAYLOAD

        # Patch the db singleton in the service module
        test_db = Database(db_path=tmp_path / "svc_test.db")
        original_db = svc_module.db
        svc_module.db = test_db

        svc = WeatherService(client=mock_client)
        yield svc, mock_client, test_db

        svc_module.db = original_db

    def test_get_current_weather(self, service_with_mock):
        svc, client, _ = service_with_mock
        weather = svc.get_current_weather("London", use_cache=False)
        assert isinstance(weather, CurrentWeather)
        assert weather.city == "London"
        client.get_current_weather.assert_called_once()

    def test_caching_prevents_second_api_call(self, service_with_mock):
        svc, client, _ = service_with_mock
        svc.get_current_weather("London", use_cache=True)
        svc.get_current_weather("London", use_cache=True)
        # Second call should use cache
        assert client.get_current_weather.call_count == 1

    def test_get_forecast(self, service_with_mock):
        svc, client, _ = service_with_mock
        forecast = svc.get_forecast("London", use_cache=False)
        assert isinstance(forecast, ForecastData)
        assert forecast.city == "London"

    def test_add_favorite(self, service_with_mock):
        svc, client, _ = service_with_mock
        weather = svc.get_current_weather("London", use_cache=False)
        added = svc.add_favorite(weather)
        assert added is True
        assert len(svc.get_favorites()) == 1

    def test_add_duplicate_favorite(self, service_with_mock):
        svc, client, _ = service_with_mock
        weather = svc.get_current_weather("London", use_cache=False)
        svc.add_favorite(weather)
        added_again = svc.add_favorite(weather)
        assert added_again is False

    def test_history_tracked(self, service_with_mock):
        svc, client, _ = service_with_mock
        svc.get_current_weather("London", use_cache=False)
        history = svc.get_search_history()
        assert len(history) == 1
        assert history[0]["city"] == "London"
