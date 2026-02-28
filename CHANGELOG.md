# Changelog

All notable changes to WeatherApp Pro are documented here.
This project follows [Semantic Versioning](https://semver.org/).

---

## [1.0.0] — 2024-01-01

### Added
- Initial production release
- Current weather display (temperature, humidity, pressure, wind, visibility)
- 5-day daily forecast panel
- 24-hour hourly forecast panel
- Multi-city tab support
- Auto-complete city search (OpenWeatherMap Geocoding API)
- Favorites management with SQLite persistence
- Search history tracking
- Dark / Light theme toggle
- Celsius / Fahrenheit unit toggle
- TTL-based SQLite caching (default 10 minutes)
- Retry with exponential backoff (3 attempts)
- Token-bucket rate limiter (60 req/min)
- Rotating log files (app.log + error.log)
- Full pytest test suite (unit + integration + mocked)
- GitHub Actions CI pipeline (Linux, Windows, macOS)
- PyInstaller build configuration
- Pre-commit hooks (black, flake8, isort, mypy)
