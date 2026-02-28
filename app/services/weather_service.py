"""
Weather service layer. Orchestrates API calls, caching, and data transformation.
"""
from __future__ import annotations
import logging
from typing import List, Optional, Tuple

from app.api.owm_client import (
    WeatherAPIClient, WeatherAPIError,
    parse_current_weather, parse_forecast, parse_city_search,
)
from app.models.weather import (
    CitySearchResult, CurrentWeather, FavoriteCity, ForecastData,
)
from app.utils.database import db

logger = logging.getLogger(__name__)


class WeatherService:
    """
    Service layer for weather operations.
    Handles caching, history tracking, and business logic.
    """

    def __init__(self, client: Optional[WeatherAPIClient] = None) -> None:
        self._client = client or WeatherAPIClient()

    def get_current_weather(
        self, city: str, unit: str = "metric", use_cache: bool = True
    ) -> CurrentWeather:
        """Fetch current weather for a city with caching."""
        cache_key = f"current:{city.lower()}:{unit}"

        if use_cache:
            cached = db.cache_get(cache_key)
            if cached:
                logger.debug("Cache hit for %s", cache_key)
                return parse_current_weather(cached, unit)

        logger.info("Fetching current weather for city=%s unit=%s", city, unit)
        data = self._client.get_current_weather(city, unit)
        db.cache_set(cache_key, data)

        weather = parse_current_weather(data, unit)
        db.history_add(weather.city, weather.country, weather.lat, weather.lon)
        return weather

    def get_current_weather_by_coords(
        self, lat: float, lon: float, unit: str = "metric", use_cache: bool = True
    ) -> CurrentWeather:
        """Fetch current weather by coordinates with caching."""
        cache_key = f"current_coords:{lat:.4f}:{lon:.4f}:{unit}"

        if use_cache:
            cached = db.cache_get(cache_key)
            if cached:
                return parse_current_weather(cached, unit)

        data = self._client.get_current_weather_by_coords(lat, lon, unit)
        db.cache_set(cache_key, data)
        weather = parse_current_weather(data, unit)
        db.history_add(weather.city, weather.country, weather.lat, weather.lon)
        return weather

    def get_forecast(
        self, city: str, unit: str = "metric", use_cache: bool = True
    ) -> ForecastData:
        """Fetch 5-day forecast for a city."""
        cache_key = f"forecast:{city.lower()}:{unit}"

        if use_cache:
            cached = db.cache_get(cache_key)
            if cached:
                return parse_forecast(cached, unit)

        logger.info("Fetching forecast for city=%s", city)
        data = self._client.get_forecast(city, unit)
        db.cache_set(cache_key, data)
        return parse_forecast(data, unit)

    def get_forecast_by_coords(
        self, lat: float, lon: float, unit: str = "metric", use_cache: bool = True
    ) -> ForecastData:
        """Fetch 5-day forecast by coordinates."""
        cache_key = f"forecast_coords:{lat:.4f}:{lon:.4f}:{unit}"

        if use_cache:
            cached = db.cache_get(cache_key)
            if cached:
                return parse_forecast(cached, unit)

        data = self._client.get_forecast_by_coords(lat, lon, unit)
        db.cache_set(cache_key, data)
        return parse_forecast(data, unit)

    def search_cities(self, query: str) -> List[CitySearchResult]:
        """Search for cities by name."""
        if len(query.strip()) < 2:
            return []
        return parse_city_search(self._client.search_cities(query))

    def get_full_weather(
        self, city: str, unit: str = "metric"
    ) -> Tuple[CurrentWeather, ForecastData]:
        """Fetch both current weather and forecast simultaneously."""
        current = self.get_current_weather(city, unit)
        forecast = self.get_forecast(city, unit)
        return current, forecast

    def get_full_weather_by_coords(
        self, lat: float, lon: float, unit: str = "metric"
    ) -> Tuple[CurrentWeather, ForecastData]:
        current = self.get_current_weather_by_coords(lat, lon, unit)
        forecast = self.get_forecast_by_coords(lat, lon, unit)
        return current, forecast

    # --- Favorites ---

    def add_favorite(self, weather: CurrentWeather) -> bool:
        """Add a city to favorites. Returns True if added, False if already exists."""
        if db.favorites_exists(weather.lat, weather.lon):
            return False
        fav = FavoriteCity(
            id=None,
            name=weather.city,
            country=weather.country,
            lat=weather.lat,
            lon=weather.lon,
        )
        db.favorites_add(fav)
        logger.info("Added favorite: %s, %s", weather.city, weather.country)
        return True

    def remove_favorite(self, fav_id: int) -> None:
        db.favorites_remove(fav_id)

    def get_favorites(self) -> List[FavoriteCity]:
        return db.favorites_get()

    def is_favorite(self, lat: float, lon: float) -> bool:
        return db.favorites_exists(lat, lon)

    # --- History ---

    def get_search_history(self, limit: int = 20) -> List[dict]:
        return db.history_get(limit)

    def clear_history(self) -> None:
        db.history_clear()

    def shutdown(self) -> None:
        self._client.close()
        db.close()
        logger.info("WeatherService shutdown complete.")
