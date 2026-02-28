# WeatherApp Pro 🌤️

[![CI](https://github.com/yourname/weather-app-pro/actions/workflows/ci.yml/badge.svg)](https://github.com/yourname/weather-app-pro/actions)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A production-ready desktop weather application built with **Python**, **PyQt5**, and the **OpenWeatherMap API**.

---

## ✨ Features

| Feature | Description |
|---|---|
| Current weather | Temperature, humidity, pressure, wind, visibility |
| 5-day forecast | Daily high/low, precipitation probability |
| Hourly forecast | 24-hour scrollable view |
| Multi-city tabs | Open and compare multiple cities |
| Auto-complete search | City suggestions as you type |
| Favorites | Save and quickly reload cities |
| Search history | Recent searches tracked in SQLite |
| Dark/Light theme | One-click toggle |
| °C/°F toggle | Unit change refreshes all open tabs |
| Local caching | TTL-based SQLite cache (10min default) |
| Retry + backoff | Robust handling of transient API failures |
| Rate limiting | Token-bucket protection (60 req/min) |
| Rotating logs | App log + error log, 5MB each |

---

## 🏗️ Architecture

```
weather_app/
├── app/
│   ├── api/            # HTTP client, parsing, error handling
│   ├── config/         # Settings, logging
│   ├── models/         # Pure data classes (no I/O)
│   ├── services/       # Business logic, orchestration
│   ├── ui/             # PyQt5 windows, widgets, workers, themes
│   └── utils/          # SQLite database layer
├── tests/              # pytest test suite
├── assets/             # Icons, stylesheets
├── main.py             # Entry point
├── requirements.txt
├── .env.example
└── weatherapp.spec     # PyInstaller build config
```

**Layer responsibilities:**

```
UI Layer → Service Layer → API Client → OpenWeatherMap
               ↕
          SQLite (cache / history / favorites)
```

---

## 🚀 Quick Start

### 1. Clone and set up environment

```bash
git clone https://github.com/yourname/weather-app-pro.git
cd weather-app-pro
python -m venv venv
source venv/bin/activate       # Linux/macOS
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 2. Configure API key

```bash
cp .env.example .env
# Edit .env and add your OpenWeatherMap API key:
# OWM_API_KEY=your_api_key_here
```

Get a free API key at [openweathermap.org/api](https://openweathermap.org/api).

### 3. Run

```bash
python main.py
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=app --cov-report=html

# Open coverage report
open htmlcov/index.html
```

---

## 📦 Building Executables

### Windows (.exe)

```bash
pip install pyinstaller
pyinstaller weatherapp.spec
# Output: dist/WeatherApp Pro.exe
```

### macOS (.app)

```bash
pyinstaller weatherapp.spec
# Output: dist/WeatherApp Pro.app
# Optional: create DMG
hdiutil create -volname "WeatherApp Pro" -srcfolder dist -ov -format UDZO WeatherApp.dmg
```

### Linux (binary)

```bash
pyinstaller --onefile --windowed --name weatherapp main.py
chmod +x dist/weatherapp
```

---

## 🔧 Development

### Linting and formatting

```bash
# Format code
black app/ main.py tests/

# Sort imports
isort app/ main.py tests/

# Lint
flake8 app/ main.py --max-line-length=100

# Type check
mypy app/ --ignore-missing-imports
```

### Pre-commit hooks

```bash
pip install pre-commit
pre-commit install
# Now runs on every git commit automatically
```

---

## ⚙️ Configuration

| Variable | Default | Description |
|---|---|---|
| `OWM_API_KEY` | — | **Required.** Your OpenWeatherMap API key |
| `DEBUG` | `false` | Enable verbose debug logging |

Advanced settings are in `app/config/settings.py`:

| Setting | Default | Description |
|---|---|---|
| Cache TTL | 600s | How long to cache weather responses |
| API timeout | 10s | Request timeout per attempt |
| Max retries | 3 | Retry attempts with exponential backoff |
| Rate limit | 60/min | Outgoing API call rate |
| Log rotation | 5MB | Max log file size before rotation |

---

## 🔒 Security

- API keys are **never logged** — masked before any log output
- `.env` is excluded from git via `.gitignore`
- **HTTPS enforced** — HTTP endpoints rejected
- Input sanitization on all city name inputs
- No eval, no exec, no shell injection vectors
- SQLite uses parameterized queries (no SQL injection)

See [SECURITY.md](SECURITY.md) for reporting vulnerabilities.

---

## 📋 Changelog

See [CHANGELOG.md](CHANGELOG.md).

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 📄 License

MIT License — see [LICENSE](LICENSE).
