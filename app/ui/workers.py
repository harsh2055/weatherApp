"""
QThread workers for non-blocking API calls.
"""
from __future__ import annotations
import logging
from typing import Optional

from PyQt5.QtCore import QThread, pyqtSignal

from app.api.owm_client import WeatherAPIError
from app.models.weather import CurrentWeather, ForecastData, CitySearchResult
from app.services.weather_service import WeatherService

logger = logging.getLogger(__name__)


class WeatherWorker(QThread):
    """Worker thread that fetches current weather + forecast."""

    result_ready = pyqtSignal(object, object)   # (CurrentWeather, ForecastData)
    error_occurred = pyqtSignal(str)
    loading = pyqtSignal(bool)

    def __init__(
        self,
        service: WeatherService,
        city: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        unit: str = "metric",
    ) -> None:
        super().__init__()
        self._service = service
        self._city = city
        self._lat = lat
        self._lon = lon
        self._unit = unit

    def run(self) -> None:
        self.loading.emit(True)
        try:
            if self._city:
                current, forecast = self._service.get_full_weather(
                    self._city, self._unit
                )
            elif self._lat is not None and self._lon is not None:
                current, forecast = self._service.get_full_weather_by_coords(
                    self._lat, self._lon, self._unit
                )
            else:
                self.error_occurred.emit("No city or coordinates provided.")
                return

            self.result_ready.emit(current, forecast)
        except WeatherAPIError as exc:
            logger.warning("WeatherAPIError: %s", exc)
            self.error_occurred.emit(str(exc))
        except Exception as exc:
            logger.exception("Unexpected error in WeatherWorker")
            self.error_occurred.emit("An unexpected error occurred.")
        finally:
            self.loading.emit(False)


class CitySearchWorker(QThread):
    """Worker thread for city auto-complete search."""

    results_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, service: WeatherService, query: str) -> None:
        super().__init__()
        self._service = service
        self._query = query

    def run(self) -> None:
        try:
            results = self._service.search_cities(self._query)
            self.results_ready.emit(results)
        except WeatherAPIError as exc:
            self.error_occurred.emit(str(exc))
        except Exception:
            logger.exception("Unexpected error in CitySearchWorker")
            self.error_occurred.emit("Search failed.")
