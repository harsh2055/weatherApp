"""
OpenWeatherMap API client with retry logic, rate limiting, and input sanitization.
"""
from __future__ import annotations
import re
import time
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from collections import deque

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config.settings import config
from app.models.weather import (
    CitySearchResult, CurrentWeather, DailyForecast, ForecastData,
    HourlyForecast, WeatherCondition, WindData,
)

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token-bucket style rate limiter."""

    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self._calls: deque[float] = deque()

    def acquire(self) -> None:
        now = time.monotonic()
        # Remove expired timestamps
        while self._calls and now - self._calls[0] > self.period:
            self._calls.popleft()

        if len(self._calls) >= self.max_calls:
            sleep_time = self.period - (now - self._calls[0])
            if sleep_time > 0:
                logger.warning("Rate limit reached, sleeping %.2fs", sleep_time)
                time.sleep(sleep_time)

        self._calls.append(time.monotonic())


class WeatherAPIClient:
    """
    Thread-safe OpenWeatherMap API client.

    Features:
    - HTTPS enforced
    - Retry with exponential backoff
    - Rate limiting
    - API key never logged
    - Input sanitization
    """

    def __init__(self) -> None:
        self._cfg = config.api
        self._rate_limiter = RateLimiter(
            self._cfg.rate_limit_calls,
            self._cfg.rate_limit_period,
        )
        self._session = self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=self._cfg.max_retries,
            backoff_factor=self._cfg.retry_backoff,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        return session

    @staticmethod
    def _sanitize_city(city: str) -> str:
        """Sanitize city name input."""
        city = city.strip()
        if not city:
            raise ValueError("City name cannot be empty.")
        if len(city) > 100:
            raise ValueError("City name too long.")
        # Allow letters, spaces, hyphens, apostrophes, commas
        if not re.match(r"^[\w\s\-',\.]+$", city, re.UNICODE):
            raise ValueError(f"Invalid characters in city name: {city!r}")
        return city

    def _get(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a rate-limited GET request. API key masked in logs."""
        self._rate_limiter.acquire()
        # Add API key after logging params
        log_params = {k: v for k, v in params.items()}
        params["appid"] = self._cfg.api_key  # Never in log_params

        logger.debug("GET %s params=%s", url, log_params)

        try:
            response = self._session.get(
                url, params=params, timeout=self._cfg.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response else "?"
            if status == 401:
                raise WeatherAPIError("Invalid API key.", status_code=401) from exc
            if status == 404:
                raise WeatherAPIError("City not found.", status_code=404) from exc
            if status == 429:
                raise WeatherAPIError("API rate limit exceeded.", status_code=429) from exc
            raise WeatherAPIError(f"HTTP error {status}.", status_code=status) from exc
        except requests.exceptions.ConnectionError as exc:
            raise WeatherAPIError("Network connection failed.") from exc
        except requests.exceptions.Timeout as exc:
            raise WeatherAPIError("Request timed out.") from exc
        except requests.exceptions.RequestException as exc:
            raise WeatherAPIError(f"Request failed: {exc}") from exc

    def get_current_weather(self, city: str, unit: str = "metric") -> Dict[str, Any]:
        city = self._sanitize_city(city)
        url = f"{self._cfg.base_url}/weather"
        return self._get(url, {"q": city, "units": unit})

    def get_current_weather_by_coords(
        self, lat: float, lon: float, unit: str = "metric"
    ) -> Dict[str, Any]:
        url = f"{self._cfg.base_url}/weather"
        return self._get(url, {"lat": lat, "lon": lon, "units": unit})

    def get_forecast(self, city: str, unit: str = "metric") -> Dict[str, Any]:
        city = self._sanitize_city(city)
        url = f"{self._cfg.base_url}/forecast"
        return self._get(url, {"q": city, "units": unit, "cnt": 40})

    def get_forecast_by_coords(
        self, lat: float, lon: float, unit: str = "metric"
    ) -> Dict[str, Any]:
        url = f"{self._cfg.base_url}/forecast"
        return self._get(url, {"lat": lat, "lon": lon, "units": unit, "cnt": 40})

    def search_cities(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        query = self._sanitize_city(query)
        url = f"{self._cfg.geo_url}/direct"
        return self._get(url, {"q": query, "limit": min(limit, 10)})

    def close(self) -> None:
        self._session.close()


class WeatherAPIError(Exception):
    """Raised when the weather API returns an error."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


def parse_current_weather(data: Dict[str, Any], unit: str = "metric") -> CurrentWeather:
    """Parse raw API response into CurrentWeather model."""
    wind_raw = data.get("wind", {})
    wind = WindData(
        speed=wind_raw.get("speed", 0.0),
        deg=wind_raw.get("deg"),
        gust=wind_raw.get("gust"),
    )
    cond_raw = data["weather"][0]
    condition = WeatherCondition(
        id=cond_raw["id"],
        main=cond_raw["main"],
        description=cond_raw["description"].capitalize(),
        icon=cond_raw["icon"],
    )
    main = data["main"]
    sys = data.get("sys", {})
    return CurrentWeather(
        city=data["name"],
        country=sys.get("country", ""),
        lat=data["coord"]["lat"],
        lon=data["coord"]["lon"],
        timestamp=datetime.fromtimestamp(data["dt"]),
        temp=main["temp"],
        feels_like=main["feels_like"],
        temp_min=main.get("temp_min", main["temp"]),
        temp_max=main.get("temp_max", main["temp"]),
        humidity=main["humidity"],
        pressure=main["pressure"],
        visibility=data.get("visibility"),
        wind=wind,
        condition=condition,
        sunrise=datetime.fromtimestamp(sys["sunrise"]) if "sunrise" in sys else None,
        sunset=datetime.fromtimestamp(sys["sunset"]) if "sunset" in sys else None,
        unit=unit,
    )


def parse_forecast(data: Dict[str, Any], unit: str = "metric") -> ForecastData:
    """Parse 5-day/3-hour forecast API response."""
    city_info = data.get("city", {})
    hourly: List[HourlyForecast] = []

    for item in data.get("list", []):
        wind_raw = item.get("wind", {})
        cond_raw = item["weather"][0]
        hourly.append(HourlyForecast(
            timestamp=datetime.fromtimestamp(item["dt"]),
            temp=item["main"]["temp"],
            feels_like=item["main"]["feels_like"],
            humidity=item["main"]["humidity"],
            wind=WindData(speed=wind_raw.get("speed", 0), deg=wind_raw.get("deg")),
            condition=WeatherCondition(
                id=cond_raw["id"],
                main=cond_raw["main"],
                description=cond_raw["description"].capitalize(),
                icon=cond_raw["icon"],
            ),
            pop=item.get("pop", 0.0),
        ))

    # Group hourly into daily
    daily_map: Dict[str, List[HourlyForecast]] = {}
    for h in hourly:
        key = h.timestamp.strftime("%Y-%m-%d")
        daily_map.setdefault(key, []).append(h)

    daily: List[DailyForecast] = []
    for date_str, hours in daily_map.items():
        temps = [h.temp for h in hours]
        daily.append(DailyForecast(
            date=datetime.strptime(date_str, "%Y-%m-%d"),
            temp_min=min(temps),
            temp_max=max(temps),
            humidity=round(sum(h.humidity for h in hours) / len(hours)),
            wind=hours[len(hours) // 2].wind,
            condition=hours[len(hours) // 2].condition,
            pop=max(h.pop for h in hours),
            hourly=hours,
        ))

    coord = city_info.get("coord", {})
    return ForecastData(
        city=city_info.get("name", ""),
        country=city_info.get("country", ""),
        lat=coord.get("lat", 0.0),
        lon=coord.get("lon", 0.0),
        daily=daily,
        hourly=hourly,
        unit=unit,
    )


def parse_city_search(data: List[Dict[str, Any]]) -> List[CitySearchResult]:
    results = []
    for item in data:
        results.append(CitySearchResult(
            name=item.get("name", ""),
            country=item.get("country", ""),
            state=item.get("state"),
            lat=item["lat"],
            lon=item["lon"],
        ))
    return results
