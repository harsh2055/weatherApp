"""
Main application window.
"""
from __future__ import annotations
import logging
from typing import Optional, List

from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont, QIcon, QKeySequence
from PyQt5.QtWidgets import (
    QAction, QCompleter, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QPushButton,
    QScrollArea, QShortcut, QSizePolicy, QSplitter, QStackedWidget,
    QStatusBar, QTabBar, QTabWidget, QVBoxLayout, QWidget, QMessageBox,
)

from app.config.settings import config
from app.models.weather import (
    CitySearchResult, CurrentWeather, FavoriteCity, ForecastData,
)
from app.services.weather_service import WeatherService
from app.ui.themes import THEMES, get_stylesheet
from app.ui.widgets import (
    CurrentWeatherWidget, ForecastWidget, HourlyForecastWidget, LoadingSpinner,
)
from app.ui.workers import CitySearchWorker, WeatherWorker

logger = logging.getLogger(__name__)


class CityTab(QWidget):
    """A single city tab showing weather and forecast."""

    def __init__(self, service: WeatherService, city: str, unit: str, parent=None):
        super().__init__(parent)
        self._service = service
        self._city = city
        self._unit = unit
        self._current_weather: Optional[CurrentWeather] = None
        self._worker: Optional[WeatherWorker] = None
        self._build_ui()
        self._fetch_weather()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Spinner overlay
        self.spinner = LoadingSpinner(self, 50)
        self.spinner.move(20, 20)
        self.spinner.hide()

        # Current weather
        self.current_widget = CurrentWeatherWidget()
        layout.addWidget(self.current_widget)

        # Hourly forecast
        self.hourly_widget = HourlyForecastWidget()
        layout.addWidget(self.hourly_widget)

        # Daily forecast
        self.daily_widget = ForecastWidget()
        layout.addWidget(self.daily_widget)

        # Refresh time label
        self.refresh_label = QLabel()
        self.refresh_label.setObjectName("stat_label")
        self.refresh_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.refresh_label)
        layout.addStretch()

    def _fetch_weather(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        self._worker = WeatherWorker(self._service, city=self._city, unit=self._unit)
        self._worker.result_ready.connect(self._on_result)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.loading.connect(self._on_loading)
        self._worker.start()

    @pyqtSlot(bool)
    def _on_loading(self, loading: bool) -> None:
        if loading:
            self.spinner.start()
        else:
            self.spinner.stop()

    @pyqtSlot(object, object)
    def _on_result(self, weather: CurrentWeather, forecast: ForecastData) -> None:
        self._current_weather = weather
        self.current_widget.update_weather(weather)
        self.hourly_widget.update_forecast(forecast)
        self.daily_widget.update_forecast(forecast)
        from datetime import datetime
        self.refresh_label.setText(f"Updated: {datetime.now().strftime('%H:%M:%S')}")

    @pyqtSlot(str)
    def _on_error(self, message: str) -> None:
        self.refresh_label.setText(f"Error: {message}")
        logger.warning("City tab error for %s: %s", self._city, message)

    def refresh(self, unit: Optional[str] = None) -> None:
        if unit:
            self._unit = unit
        self._fetch_weather()

    @property
    def current_weather(self) -> Optional[CurrentWeather]:
        return self._current_weather


class MainWindow(QMainWindow):
    """
    Production-quality main application window.

    Features:
    - Multi-city tabs
    - Dark/light theme toggle
    - Celsius/Fahrenheit toggle
    - Auto-complete city search
    - Favorites management
    - Search history
    - Status bar with live feedback
    """

    def __init__(self, service: WeatherService) -> None:
        super().__init__()
        self._service = service
        self._theme_name = config.ui.default_theme
        self._unit = config.ui.default_unit
        self._search_worker: Optional[CitySearchWorker] = None
        self._search_results: List[CitySearchResult] = []
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._trigger_city_search)

        self.setWindowTitle(f"{config.ui.app_name} v{config.ui.version}")
        self.resize(config.ui.window_width, config.ui.window_height)
        self.setMinimumSize(800, 580)

        self._apply_theme()
        self._build_ui()
        self._setup_menu()
        self._setup_shortcuts()

    def _apply_theme(self) -> None:
        theme = THEMES[self._theme_name]
        self.setStyleSheet(get_stylesheet(theme))

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("central_widget")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # --- Sidebar ---
        sidebar = self._build_sidebar()
        root.addWidget(sidebar)

        # --- Main content ---
        content = self._build_content()
        root.addWidget(content, 1)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setObjectName("info_card")
        sidebar.setStyleSheet("border-radius: 0; border-right: 1px solid;")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(12)

        # App name
        app_lbl = QLabel(config.ui.app_name)
        app_lbl.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(app_lbl)

        # Search input with auto-complete
        search_lbl = QLabel("Search City")
        search_lbl.setObjectName("section_title")
        layout.addWidget(search_lbl)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter city name...")
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.search_input.returnPressed.connect(self._on_search_submit)
        layout.addWidget(self.search_input)

        # Search suggestions list
        self.suggestions_list = QListWidget()
        self.suggestions_list.setMaximumHeight(160)
        self.suggestions_list.hide()
        self.suggestions_list.itemClicked.connect(self._on_suggestion_clicked)
        layout.addWidget(self.suggestions_list)

        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._on_search_submit)
        layout.addWidget(search_btn)

        # Unit toggle
        unit_frame = QFrame()
        unit_layout = QHBoxLayout(unit_frame)
        unit_layout.setContentsMargins(0, 0, 0, 0)
        self.celsius_btn = QPushButton("°C")
        self.fahrenheit_btn = QPushButton("°F")
        self.celsius_btn.setObjectName("secondary_btn" if self._unit == "imperial" else "")
        self.fahrenheit_btn.setObjectName("secondary_btn" if self._unit == "metric" else "")
        self.celsius_btn.clicked.connect(lambda: self._set_unit("metric"))
        self.fahrenheit_btn.clicked.connect(lambda: self._set_unit("imperial"))
        unit_layout.addWidget(self.celsius_btn)
        unit_layout.addWidget(self.fahrenheit_btn)
        layout.addWidget(unit_frame)

        # Theme toggle
        theme_btn = QPushButton("🌙 Dark / ☀️ Light")
        theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(theme_btn)

        # Favorites
        fav_lbl = QLabel("⭐ Favorites")
        fav_lbl.setObjectName("section_title")
        layout.addWidget(fav_lbl)

        self.favorites_list = QListWidget()
        self.favorites_list.setMaximumHeight(180)
        self.favorites_list.itemDoubleClicked.connect(self._on_favorite_clicked)
        layout.addWidget(self.favorites_list)

        fav_btn_row = QHBoxLayout()
        self.add_fav_btn = QPushButton("+ Add")
        self.add_fav_btn.clicked.connect(self._add_favorite)
        remove_fav_btn = QPushButton("Remove")
        remove_fav_btn.setObjectName("secondary_btn")
        remove_fav_btn.clicked.connect(self._remove_favorite)
        fav_btn_row.addWidget(self.add_fav_btn)
        fav_btn_row.addWidget(remove_fav_btn)
        layout.addLayout(fav_btn_row)

        # History
        hist_lbl = QLabel("🕐 Recent")
        hist_lbl.setObjectName("section_title")
        layout.addWidget(hist_lbl)

        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(150)
        self.history_list.itemDoubleClicked.connect(self._on_history_clicked)
        layout.addWidget(self.history_list)

        layout.addStretch()
        self._refresh_favorites()
        self._refresh_history()
        return sidebar

    def _build_content(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tab widget for multiple cities
        self.city_tabs = QTabWidget()
        self.city_tabs.setTabsClosable(True)
        self.city_tabs.tabCloseRequested.connect(self._close_tab)
        layout.addWidget(self.city_tabs)

        # Placeholder when no tabs
        self.placeholder = QLabel("🔍 Search for a city to get started")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setFont(QFont("Segoe UI", 16))
        self.placeholder.setObjectName("condition_label")
        layout.addWidget(self.placeholder)

        return content

    def _setup_menu(self) -> None:
        menu = self.menuBar()

        # File
        file_menu = menu.addMenu("File")
        refresh_action = QAction("Refresh All", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._refresh_all_tabs)
        file_menu.addAction(refresh_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View
        view_menu = menu.addMenu("View")
        theme_action = QAction("Toggle Theme", self)
        theme_action.setShortcut("Ctrl+T")
        theme_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(theme_action)

        unit_action = QAction("Toggle °C/°F", self)
        unit_action.setShortcut("Ctrl+U")
        unit_action.triggered.connect(self._toggle_unit)
        view_menu.addAction(unit_action)

        # Help
        help_menu = menu.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(
            lambda: self.search_input.setFocus()
        )
        QShortcut(QKeySequence("F5"), self).activated.connect(self._refresh_all_tabs)

    # --- Search ---

    @pyqtSlot(str)
    def _on_search_text_changed(self, text: str) -> None:
        if len(text) >= 2:
            self._debounce_timer.start(400)
        else:
            self.suggestions_list.hide()

    def _trigger_city_search(self) -> None:
        query = self.search_input.text().strip()
        if len(query) < 2:
            return
        if self._search_worker and self._search_worker.isRunning():
            self._search_worker.quit()

        self._search_worker = CitySearchWorker(self._service, query)
        self._search_worker.results_ready.connect(self._on_search_results)
        self._search_worker.start()

    @pyqtSlot(list)
    def _on_search_results(self, results: List[CitySearchResult]) -> None:
        self._search_results = results
        self.suggestions_list.clear()
        if results:
            for r in results:
                self.suggestions_list.addItem(r.display_name)
            self.suggestions_list.show()
        else:
            self.suggestions_list.hide()

    @pyqtSlot(QListWidgetItem)
    def _on_suggestion_clicked(self, item: QListWidgetItem) -> None:
        idx = self.suggestions_list.currentRow()
        if 0 <= idx < len(self._search_results):
            city = self._search_results[idx]
            self.search_input.setText(city.name)
            self.suggestions_list.hide()
            self._open_city_tab(city.name)

    def _on_search_submit(self) -> None:
        city = self.search_input.text().strip()
        if city:
            self.suggestions_list.hide()
            self._open_city_tab(city)

    # --- Tabs ---

    def _open_city_tab(self, city: str) -> None:
        # Check if tab already open
        for i in range(self.city_tabs.count()):
            if self.city_tabs.tabText(i).lower() == city.lower():
                self.city_tabs.setCurrentIndex(i)
                return

        tab = CityTab(self._service, city, self._unit)
        self.city_tabs.addTab(tab, city.title())
        self.city_tabs.setCurrentWidget(tab)
        self.placeholder.hide()
        self.city_tabs.show()
        self.status_bar.showMessage(f"Loading weather for {city}...", 3000)

    def _close_tab(self, index: int) -> None:
        self.city_tabs.removeTab(index)
        if self.city_tabs.count() == 0:
            self.placeholder.show()

    def _refresh_all_tabs(self) -> None:
        for i in range(self.city_tabs.count()):
            tab = self.city_tabs.widget(i)
            if isinstance(tab, CityTab):
                tab.refresh()
        self.status_bar.showMessage("Refreshing all cities...", 2000)

    # --- Theme / Unit ---

    def _toggle_theme(self) -> None:
        self._theme_name = "light" if self._theme_name == "dark" else "dark"
        self._apply_theme()

    def _toggle_unit(self) -> None:
        self._set_unit("imperial" if self._unit == "metric" else "metric")

    def _set_unit(self, unit: str) -> None:
        if self._unit == unit:
            return
        self._unit = unit
        for i in range(self.city_tabs.count()):
            tab = self.city_tabs.widget(i)
            if isinstance(tab, CityTab):
                tab.refresh(unit)
        self.status_bar.showMessage(f"Unit changed to {'Celsius' if unit == 'metric' else 'Fahrenheit'}", 2000)

    # --- Favorites ---

    def _refresh_favorites(self) -> None:
        self.favorites_list.clear()
        for fav in self._service.get_favorites():
            item = QListWidgetItem(f"{fav.name}, {fav.country}")
            item.setData(Qt.UserRole, fav)
            self.favorites_list.addItem(item)

    def _add_favorite(self) -> None:
        current_tab = self.city_tabs.currentWidget()
        if not isinstance(current_tab, CityTab) or not current_tab.current_weather:
            self.status_bar.showMessage("No weather data to save as favorite.", 3000)
            return
        added = self._service.add_favorite(current_tab.current_weather)
        if added:
            self._refresh_favorites()
            self.status_bar.showMessage(f"Added {current_tab.current_weather.city} to favorites.", 3000)
        else:
            self.status_bar.showMessage("City already in favorites.", 2000)

    def _remove_favorite(self) -> None:
        item = self.favorites_list.currentItem()
        if not item:
            return
        fav: FavoriteCity = item.data(Qt.UserRole)
        self._service.remove_favorite(fav.id)
        self._refresh_favorites()

    @pyqtSlot(QListWidgetItem)
    def _on_favorite_clicked(self, item: QListWidgetItem) -> None:
        fav: FavoriteCity = item.data(Qt.UserRole)
        self._open_city_tab(fav.name)

    # --- History ---

    def _refresh_history(self) -> None:
        self.history_list.clear()
        for entry in self._service.get_search_history(limit=10):
            item = QListWidgetItem(f"{entry['city']}, {entry['country']}")
            item.setData(Qt.UserRole, entry["city"])
            self.history_list.addItem(item)

    @pyqtSlot(QListWidgetItem)
    def _on_history_clicked(self, item: QListWidgetItem) -> None:
        city = item.data(Qt.UserRole)
        self._open_city_tab(city)

    # --- About ---

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About WeatherApp Pro",
            f"<b>{config.ui.app_name}</b><br>"
            f"Version {config.ui.version}<br><br>"
            "A production-ready desktop weather application built with PyQt5 and OpenWeatherMap.<br><br>"
            "© 2024 WeatherApp Pro. MIT License.",
        )

    def closeEvent(self, event) -> None:
        logger.info("Application closing, shutting down service.")
        self._service.shutdown()
        event.accept()
