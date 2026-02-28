"""
Centralized logging setup with rotating file handlers.
"""
import logging
import logging.handlers
from pathlib import Path
from app.config.settings import config


def setup_logging() -> None:
    """Configure application-wide logging with rotating files."""
    log_dir: Path = config.log.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=date_fmt)

    root_logger = logging.getLogger()
    root_logger.setLevel(config.log.level if not config.debug else logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.WARNING)
    root_logger.addHandler(console_handler)

    # App log (all levels)
    app_handler = logging.handlers.RotatingFileHandler(
        log_dir / config.log.app_log,
        maxBytes=config.log.max_bytes,
        backupCount=config.log.backup_count,
        encoding="utf-8",
    )
    app_handler.setFormatter(formatter)
    app_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(app_handler)

    # Error log (ERROR+)
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / config.log.error_log,
        maxBytes=config.log.max_bytes,
        backupCount=config.log.backup_count,
        encoding="utf-8",
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)

    # Suppress verbose third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger instance."""
    return logging.getLogger(name)
