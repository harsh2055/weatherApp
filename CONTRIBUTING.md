# Contributing to WeatherApp Pro

Thank you for your interest in contributing!

## Getting Started

1. Fork the repository
2. Create a branch: `git checkout -b feature/your-feature`
3. Install dev dependencies: `pip install -r requirements.txt`
4. Install pre-commit hooks: `pre-commit install`

## Development Workflow

1. Write your code following the existing architecture:
   - API layer changes go in `app/api/`
   - Business logic in `app/services/`
   - UI changes in `app/ui/`
   - Data models in `app/models/`

2. Add or update tests in `tests/`

3. Ensure all checks pass:
   ```bash
   black app/ main.py tests/
   isort app/ main.py tests/
   flake8 app/ main.py --max-line-length=100
   pytest tests/ -v --cov=app --cov-fail-under=70
   ```

4. Commit with a clear message: `git commit -m "feat: add wind speed chart"`

5. Open a Pull Request with:
   - What the change does
   - Why it's needed
   - How to test it

## Code Style

- **PEP 8** with 100-character line limit
- **black** for formatting
- **Type hints** on all public functions
- **Docstrings** on all classes and public methods
- No logic in `__init__.py` files

## Commit Message Format

```
type(scope): short description

Types: feat, fix, refactor, test, docs, chore, perf
```
