"""
Reusable weather display widgets.
"""
from __future__ import annotations
from typing import List

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QColor
from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QSizePolicy,
    QVBoxLayout, QWidget, QScrollArea,
)

from app.models.weather import CurrentWeather, DailyForecast, ForecastData, HourlyForecast


def _stat_widget(label: str, value: str) -> QWidget:
    """Create a small stat label-value pair."""
    w = QFrame()
    w.setObjectName("info_card")
    layout = QVBoxLayout(w)
    layout.setContentsMargins(10, 8, 10, 8)
    layout.setSpacing(2)

    lbl = QLabel(label)
    lbl.setObjectName("stat_label")
    lbl.setAlignment(Qt.AlignCenter)

    val = QLabel(value)
    val.setObjectName("stat_value")
    val.setAlignment(Qt.AlignCenter)
    val.setFont(QFont("Segoe UI", 14, QFont.Bold))

    layout.addWidget(lbl)
    layout.addWidget(val)
    return w


class LoadingSpinner(QWidget):
    """Animated loading indicator."""

    def __init__(self, parent=None, size: int = 40):
        super().__init__(parent)
        self._angle = 0
        self._size = size
        self.setFixedSize(size, size)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)

    def start(self) -> None:
        self._timer.start(50)
        self.show()

    def stop(self) -> None:
        self._timer.stop()
        self.hide()

    def _rotate(self) -> None:
        self._angle = (self._angle + 10) % 360
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self._size / 2, self._size / 2)
        for i in range(12):
            alpha = int(255 * (i + 1) / 12)
            color = QColor(79, 142, 247, alpha)
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.rotate(self._angle + 30 * i)
            painter.drawRoundedRect(-3, -self._size // 2 + 4, 6, 12, 3, 3)


class CurrentWeatherWidget(QWidget):
    """Displays current weather data."""

    favorite_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(12)

        # Header: city + favorite button
        header = QHBoxLayout()
        self.city_label = QLabel("—")
        self.city_label.setObjectName("city_label")
        self.country_label = QLabel()
        self.country_label.setObjectName("condition_label")

        city_col = QVBoxLayout()
        city_col.setSpacing(2)
        city_col.addWidget(self.city_label)
        city_col.addWidget(self.country_label)
        header.addLayout(city_col)
        header.addStretch()
        main.addLayout(header)

        # Temperature + condition
        temp_row = QHBoxLayout()
        self.temp_label = QLabel("—")
        self.temp_label.setObjectName("temp_label")
        self.temp_label.setFont(QFont("Segoe UI", 64, QFont.Bold))

        cond_col = QVBoxLayout()
        cond_col.setSpacing(4)
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.condition_label = QLabel()
        self.condition_label.setObjectName("condition_label")
        self.feels_like_label = QLabel()
        self.feels_like_label.setObjectName("stat_label")
        cond_col.addWidget(self.icon_label)
        cond_col.addWidget(self.condition_label)
        cond_col.addWidget(self.feels_like_label)

        temp_row.addWidget(self.temp_label)
        temp_row.addSpacing(16)
        temp_row.addLayout(cond_col)
        temp_row.addStretch()
        main.addLayout(temp_row)

        # Stats row
        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(8)
        self._stat_widgets: dict = {}
        for stat in ["Humidity", "Pressure", "Wind", "Visibility", "High", "Low"]:
            w = _stat_widget(stat, "—")
            self._stat_widgets[stat] = w
            self.stats_row.addWidget(w)
        main.addLayout(self.stats_row)

        # Sunrise / sunset
        sun_row = QHBoxLayout()
        self.sunrise_label = QLabel()
        self.sunset_label = QLabel()
        sun_row.addWidget(QLabel("🌅"))
        sun_row.addWidget(self.sunrise_label)
        sun_row.addStretch()
        sun_row.addWidget(QLabel("🌇"))
        sun_row.addWidget(self.sunset_label)
        main.addLayout(sun_row)
        main.addStretch()

    def update_weather(self, weather: CurrentWeather) -> None:
        self.city_label.setText(weather.city)
        self.country_label.setText(weather.country)
        self.temp_label.setText(weather.temp_display())
        self.condition_label.setText(weather.condition.description)
        self.feels_like_label.setText(f"Feels like {weather.feels_like_display()}")

        unit_label = "m/s" if weather.unit == "metric" else "mph"
        vis = f"{weather.visibility // 1000} km" if weather.visibility else "N/A"

        stats = {
            "Humidity": f"{weather.humidity}%",
            "Pressure": f"{weather.pressure} hPa",
            "Wind": f"{weather.wind.speed:.1f} {unit_label} {weather.wind.direction}",
            "Visibility": vis,
            "High": f"{weather.temp_max:.1f}°",
            "Low": f"{weather.temp_min:.1f}°",
        }
        for name, val in stats.items():
            w = self._stat_widgets[name]
            w.findChild(QLabel, "") if False else None
            labels = w.findChildren(QLabel)
            if labels:
                labels[-1].setText(val)  # value is second label

        if weather.sunrise:
            self.sunrise_label.setText(weather.sunrise.strftime("%H:%M"))
        if weather.sunset:
            self.sunset_label.setText(weather.sunset.strftime("%H:%M"))


class DailyForecastCard(QFrame):
    """Single-day forecast card."""

    def __init__(self, forecast: DailyForecast, unit: str = "metric", parent=None):
        super().__init__(parent)
        self.setObjectName("forecast_card")
        self._build(forecast, unit)

    def _build(self, f: DailyForecast, unit: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)

        sym = "°C" if unit == "metric" else "°F"
        day_lbl = QLabel(f.date.strftime("%a %d"))
        day_lbl.setObjectName("section_title")
        day_lbl.setAlignment(Qt.AlignCenter)

        cond_lbl = QLabel(f.condition.description)
        cond_lbl.setObjectName("stat_label")
        cond_lbl.setAlignment(Qt.AlignCenter)
        cond_lbl.setWordWrap(True)

        temp_lbl = QLabel(f"{f.temp_max:.0f}{sym} / {f.temp_min:.0f}{sym}")
        temp_lbl.setObjectName("stat_value")
        temp_lbl.setAlignment(Qt.AlignCenter)

        pop_lbl = QLabel(f"💧 {f.pop * 100:.0f}%")
        pop_lbl.setObjectName("stat_label")
        pop_lbl.setAlignment(Qt.AlignCenter)

        layout.addWidget(day_lbl)
        layout.addWidget(cond_lbl)
        layout.addWidget(temp_lbl)
        layout.addWidget(pop_lbl)
        self.setMinimumWidth(110)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)


class ForecastWidget(QWidget):
    """5-day forecast panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("5-Day Forecast")
        title.setObjectName("section_title")
        self._layout.addWidget(title)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setFixedHeight(160)
        self._layout.addWidget(self._scroll)

        self._container = QWidget()
        self._cards_layout = QHBoxLayout(self._container)
        self._cards_layout.setSpacing(8)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._scroll.setWidget(self._container)

    def update_forecast(self, forecast: ForecastData) -> None:
        # Clear existing cards
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for daily in forecast.daily[:7]:
            card = DailyForecastCard(daily, forecast.unit)
            self._cards_layout.addWidget(card)
        self._cards_layout.addStretch()


class HourlyForecastWidget(QWidget):
    """Hourly forecast panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Hourly Forecast")
        title.setObjectName("section_title")
        self._layout.addWidget(title)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setFixedHeight(120)
        self._layout.addWidget(self._scroll)

        self._container = QWidget()
        self._cards_layout = QHBoxLayout(self._container)
        self._cards_layout.setSpacing(8)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._scroll.setWidget(self._container)

    def update_forecast(self, forecast: ForecastData) -> None:
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        sym = "°C" if forecast.unit == "metric" else "°F"
        for h in forecast.hourly[:24]:
            card = QFrame()
            card.setObjectName("forecast_card")
            card.setMinimumWidth(80)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(8, 8, 8, 8)
            cl.setSpacing(4)
            cl.setAlignment(Qt.AlignCenter)

            time_lbl = QLabel(h.timestamp.strftime("%H:%M"))
            time_lbl.setObjectName("stat_label")
            time_lbl.setAlignment(Qt.AlignCenter)

            temp_lbl = QLabel(f"{h.temp:.0f}{sym}")
            temp_lbl.setObjectName("stat_value")
            temp_lbl.setAlignment(Qt.AlignCenter)

            pop_lbl = QLabel(f"💧{h.pop*100:.0f}%")
            pop_lbl.setObjectName("stat_label")
            pop_lbl.setAlignment(Qt.AlignCenter)

            cl.addWidget(time_lbl)
            cl.addWidget(temp_lbl)
            cl.addWidget(pop_lbl)
            self._cards_layout.addWidget(card)
        self._cards_layout.addStretch()
