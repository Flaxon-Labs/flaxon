from __future__ import annotations

from typing import Any


class Redactor:
    SENSITIVE_KEYS = {
        "password", "passwd", "pwd", "secret", "token", "authorization",
        "auth", "api_key", "apikey", "private_key", "private", "credit_card",
        "card_number", "cvv", "ssn", "social_security", "phone", "email",
        "address", "cookie", "set_cookie", "x_api_key", "x_apikey",
        "bearer", "jwt", "access_token", "refresh_token",
    }

    SENSITIVE_PATTERNS = [
        (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL]"),
        (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),
        (r"\b\d{4}-\d{4}-\d{4}-\d{4}\b", "[CREDIT_CARD]"),
        (r"\b[A-Za-z0-9+/]{40,}={0,2}\b", "[TOKEN]"),
        (r"\beyJ[A-Za-z0-9_-]+\b", "[TOKEN]"),
        (r"\b(?:secret|token)[A-Za-z0-9_-]+\b", "[REDACTED]"),
        (r"\b[0-9a-f]{32,}\b", "[HASH]"),
        (r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", "[UUID]"),
    ]

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled

    def redact(self, value: Any, depth: int = 0) -> Any:
        if not self.enabled:
            return value

        if depth > 5:
            return "[TRUNCATED]"

        if isinstance(value, dict):
            return {
                str(key): "[REDACTED]" if self._is_sensitive(key) else self.redact(item, depth + 1)
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple)):
            return [self.redact(item, depth + 1) for item in value[:50]]

        if isinstance(value, str):
            return self._redact_string(value)

        return value

    def _is_sensitive(self, key: str) -> bool:
        normalized = key.lower().replace("-", "_").replace(" ", "_")
        return any(part in normalized for part in self.SENSITIVE_KEYS)

    def _redact_string(self, value: str) -> str:
        truncated = len(value) > 1000
        result = value[:1000] if truncated else value

        for pattern, replacement in self.SENSITIVE_PATTERNS:
            import re
            result = re.sub(pattern, replacement, result)

        if truncated:
            result += "...[TRUNCATED]"

        return result

    def redact_headers(self, headers: dict[str, str]) -> dict[str, str]:
        result = {}
        for key, value in headers.items():
            if self._is_sensitive(key):
                result[key] = "[REDACTED]"
            else:
                result[key] = value
        return result

    def redact_url(self, url: str) -> str:
        import re
        return re.sub(r"([?&][^=]+=)[^&]+", r"\1[REDACTED]", url)


_default_redactor = Redactor()


def redact(value: Any, enabled: bool = True) -> Any:
    if enabled:
        return _default_redactor.redact(value)
    return value


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    return _default_redactor.redact_headers(headers)


def redact_url(url: str) -> str:
    return _default_redactor.redact_url(url)
