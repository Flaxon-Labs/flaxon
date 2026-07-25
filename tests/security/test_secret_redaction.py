import pytest

from flaxon.debugging import redact
from flaxon.debugging.redaction import Redactor


def test_redact_sensitive_keys():
    data = {
        "username": "alice",
        "password": "secret123",
        "email": "alice@example.com",
        "token": "abc123token",
        "api_key": "key123456",
        "authorization": "Bearer token123",
        "data": {"nested": {"secret": "hidden"}},
    }

    redacted = redact(data)

    assert redacted["username"] == "alice"
    assert redacted["password"] == "[REDACTED]"
    assert redacted["token"] == "[REDACTED]"
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["authorization"] == "[REDACTED]"
    assert redacted["data"]["nested"]["secret"] == "[REDACTED]"


def test_redact_email():
    redactor = Redactor()
    result = redactor._redact_string("alice@example.com")
    assert result == "[EMAIL]"


def test_redact_credit_card():
    redactor = Redactor()
    result = redactor._redact_string("4111-1111-1111-1111")
    assert result == "[CREDIT_CARD]"


def test_redact_ssn():
    redactor = Redactor()
    result = redactor._redact_string("123-45-6789")
    assert result == "[SSN]"


def test_redact_token():
    redactor = Redactor()
    result = redactor._redact_string("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")
    assert result == "[TOKEN]"


def test_redact_uuid():
    redactor = Redactor()
    result = redactor._redact_string("123e4567-e89b-12d3-a456-426614174000")
    assert result == "[UUID]"


def test_redact_long_string():
    redactor = Redactor()
    long_string = "a" * 2000
    result = redactor._redact_string(long_string)
    assert len(result) <= 1000 + len("...[TRUNCATED]")
    assert result.endswith("...[TRUNCATED]")


def test_redact_list():
    data = ["alice", "secret123", "bob", "token456"]

    redacted = redact(data)
    assert redacted[0] == "alice"
    assert redacted[1] == "[REDACTED]"
    assert redacted[2] == "bob"
    assert redacted[3] == "[REDACTED]"


def test_redact_nested_dict():
    data = {
        "user": {
            "name": "alice",
            "password": "secret123",
            "profile": {
                "bio": "Hello world",
                "api_key": "key123",
            },
        }
    }

    redacted = redact(data)
    assert redacted["user"]["name"] == "alice"
    assert redacted["user"]["password"] == "[REDACTED]"
    assert redacted["user"]["profile"]["bio"] == "Hello world"
    assert redacted["user"]["profile"]["api_key"] == "[REDACTED]"


def test_redact_headers():
    redactor = Redactor()

    headers = {
        "content-type": "application/json",
        "authorization": "Bearer token123",
        "x-api-key": "key456",
        "cookie": "session=abc123",
    }

    redacted = redactor.redact_headers(headers)
    assert redacted["content-type"] == "application/json"
    assert redacted["authorization"] == "[REDACTED]"
    assert redacted["x-api-key"] == "[REDACTED]"
    assert redacted["cookie"] == "[REDACTED]"


def test_redact_url():
    redactor = Redactor()

    url = "https://example.com/api?token=abc123&user=alice"
    redacted = redactor.redact_url(url)

    assert "token=[REDACTED]" in redacted
    assert "abc123" not in redacted