import time

import pytest

from flaxon.security import JWT


def test_jwt_encode_decode():
    jwt = JWT(secret_key="test-secret")

    payload = {"user_id": 1, "username": "alice"}
    token = jwt.encode(payload)

    decoded = jwt.decode(token)
    assert decoded["user_id"] == 1
    assert decoded["username"] == "alice"
    assert "iat" in decoded
    assert "exp" in decoded


def test_jwt_expiration():
    jwt = JWT(secret_key="test-secret")

    payload = {"user_id": 1}
    token = jwt.encode(payload, expires_in=1)

    time.sleep(2)

    with pytest.raises(Exception):
        jwt.decode(token)


def test_jwt_invalid_token():
    jwt = JWT(secret_key="test-secret")

    with pytest.raises(Exception):
        jwt.decode("invalid.token.format")


def test_jwt_tampered_token():
    jwt = JWT(secret_key="test-secret")

    payload = {"user_id": 1}
    token = jwt.encode(payload)

    parts = token.split(".")
    tampered = f"{parts[0]}.{parts[1]}.tampered"

    with pytest.raises(Exception):
        jwt.decode(tampered)


def test_jwt_different_secret():
    jwt1 = JWT(secret_key="secret1")
    jwt2 = JWT(secret_key="secret2")

    token = jwt1.encode({"user_id": 1})

    with pytest.raises(Exception):
        jwt2.decode(token)


def test_jwt_custom_algorithm():
    jwt = JWT(secret_key="test-secret", algorithm="HS256")

    token = jwt.encode({"user_id": 1})
    decoded = jwt.decode(token)

    assert decoded["user_id"] == 1


def test_jwt_missing_payload():
    jwt = JWT(secret_key="test-secret")

    with pytest.raises(Exception):
        jwt.decode("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")


def test_jwt_extra_fields():
    jwt = JWT(secret_key="test-secret")

    payload = {
        "user_id": 1,
        "username": "alice",
        "role": "admin",
        "permissions": ["read", "write"],
    }

    token = jwt.encode(payload)
    decoded = jwt.decode(token)

    assert decoded["user_id"] == 1
    assert decoded["username"] == "alice"
    assert decoded["role"] == "admin"
    assert decoded["permissions"] == ["read", "write"]