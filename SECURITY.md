# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 1.x | ✅ |

## Reporting a Vulnerability

Please **do not** open public GitHub Issues for security vulnerabilities.

Instead, email: security@weatherapp-pro.example.com

Include:
- Description of the vulnerability
- Steps to reproduce
- Affected versions
- Any suggested fix

You will receive a response within **72 hours**. If confirmed, a fix will be
released within **14 days** and you will be credited in the changelog.

## Security Practices

- API keys are stored only in `.env` (excluded from version control)
- API keys are never written to log files
- All HTTP requests use HTTPS only
- SQLite queries use parameterized statements (no SQL injection)
- User input (city names) is sanitized with regex allowlist
- Dependencies are pinned in `requirements.txt`
