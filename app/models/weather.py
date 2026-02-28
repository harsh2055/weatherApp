"""
Pydantic-style data models for weather data.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class WeatherCondition:
    id: int
    main: str
    description: str
    icon: str


@dataclass
class WindData:
    speed: float
    deg: Optional[float] = None
    gust: Optional[float] = None

    @property
    def direction(self) -> str:
        if self.deg is None:
            return "N/A"
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                      "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        idx = round(self.deg / 22.5) % 16
        return directions[idx]


@dataclass
class CurrentWeather:
    city: str
    country: str
    lat: float
    lon: float
    timestamp: datetime
    temp: float
    feels_like: float
    temp_min: float
    temp_max: float
    humidity: int
    pressure: int
    visibility: Optional[int]
    wind: WindData
    condition: WeatherCondition
    sunrise: Optional[datetime] = None
    sunset: Optional[datetime] = None
    unit: str = "metric"

    def temp_display(self) -> str:
        symbol = "°C" if self.unit == "metric" else "°F"
        return f"{self.temp:.1f}{symbol}"

    def feels_like_display(self) -> str:
        symbol = "°C" if self.unit == "metric" else "°F"
        return f"{self.feels_like:.1f}{symbol}"


@dataclass
class HourlyForecast:
    timestamp: datetime
    temp: float
    feels_like: float
    humidity: int
    wind: WindData
    condition: WeatherCondition
    pop: float = 0.0  # Probability of precipitation


@dataclass
class DailyForecast:
    date: datetime
    temp_min: float
    temp_max: float
    humidity: int
    wind: WindData
    condition: WeatherCondition
    pop: float = 0.0
    hourly: List[HourlyForecast] = field(default_factory=list)


@dataclass
class ForecastData:
    city: str
    country: str
    lat: float
    lon: float
    daily: List[DailyForecast] = field(default_factory=list)
    hourly: List[HourlyForecast] = field(default_factory=list)
    unit: str = "metric"


@dataclass
class CitySearchResult:
    name: str
    country: str
    state: Optional[str]
    lat: float
    lon: float

    @property
    def display_name(self) -> str:
        parts = [self.name]
        if self.state:
            parts.append(self.state)
        parts.append(self.country)
        return ", ".join(parts)


@dataclass
class FavoriteCity:
    id: Optional[int]
    name: str
    country: str
    lat: float
    lon: float
    added_at: datetime = field(default_factory=datetime.now)
