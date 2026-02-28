"""
Application configuration management with environment variable support.
"""
import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Load environment variables
load_dotenv(dotenv_path=BASE_DIR / ".env")




@dataclass
class APIConfig:
    """OpenWeatherMap API configuration."""
    base_url: str = "https://api.openweathermap.org/data/2.5"
    geo_url: str = "https://api.openweathermap.org/geo/1.0"
    icon_url: str = "https://openweathermap.org/img/wn"
    timeout: int = 10
    max_retries: int = 3
    retry_backoff: float = 1.5
    rate_limit_calls: int = 60
    rate_limit_period: int = 60  # seconds

    @property
    def api_key(self) -> str:
        key = os.environ.get("OWM_API_KEY", "")
        if not key:
            raise ValueError("OWM_API_KEY environment variable not set.")
        return key


@dataclass
class CacheConfig:
    """Cache configuration."""
    ttl_seconds: int = 600  # 10 minutes
    max_entries: int = 100
    db_path: Path = BASE_DIR / "data" / "weather_cache.db"


@dataclass
class LogConfig:
    """Logging configuration."""
    level: int = logging.INFO
    log_dir: Path = BASE_DIR / "logs"
    app_log: str = "app.log"
    error_log: str = "error.log"
    max_bytes: int = 5 * 1024 * 1024  # 5MB
    backup_count: int = 5


@dataclass
class UIConfig:
    """UI configuration."""
    app_name: str = "WeatherApp Pro"
    version: str = "1.0.0"
    window_width: int = 1000
    window_height: int = 700
    default_theme: str = "dark"
    default_unit: str = "metric"  # metric or imperial


@dataclass
class AppConfig:
    """Master application configuration."""
    api: APIConfig = field(default_factory=APIConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    log: LogConfig = field(default_factory=LogConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    debug: bool = os.environ.get("DEBUG", "false").lower() == "true"

    def __post_init__(self):
        # Ensure directories exist
        self.cache.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.log.log_dir.mkdir(parents=True, exist_ok=True)


# Singleton config instance
config = AppConfig()
