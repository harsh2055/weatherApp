"""
WeatherApp Pro — Production-ready desktop weather application.
Entry point.
"""
import sys
import logging

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QIcon

from app.config.logging_config import setup_logging, get_logger
from app.config.settings import config
from app.services.weather_service import WeatherService
from app.ui.main_window import MainWindow


def main() -> int:
    setup_logging()
    logger = get_logger("main")
    logger.info("Starting %s v%s", config.ui.app_name, config.ui.version)

    app = QApplication(sys.argv)
    app.setApplicationName(config.ui.app_name)
    app.setApplicationVersion(config.ui.version)
    app.setOrganizationName("WeatherAppPro")

    # Validate API key early
    try:
        _ = config.api.api_key
    except ValueError as exc:
        QMessageBox.critical(
            None,
            "Configuration Error",
            str(exc) + "\n\nPlease create a .env file with your OWM_API_KEY.",
        )
        return 1

    service = WeatherService()
    window = MainWindow(service)
    window.show()

    logger.info("Application started successfully.")
    exit_code = app.exec_()
    logger.info("Application exited with code %d", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
