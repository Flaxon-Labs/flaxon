from __future__ import annotations

import base64
import asyncio
import hashlib
import hmac
import time

from flaxon.admin.services import AdminAuth


def _current_otp(secret: str) -> str:
    key = base64.b32decode(secret + "=" * (-len(secret) % 8), casefold=True)
    counter = int(time.time() // 30).to_bytes(8, "big")
    digest = hmac.new(key, counter, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    number = (int.from_bytes(digest[offset:offset + 4], "big") & 0x7FFFFFFF) % 1_000_000
    return f"{number:06d}"


def test_mfa_enrollment_requires_confirmation_and_uses_recovery_once():
    auth = AdminAuth([{"username": "admin", "password": "Admin123!", "email": "admin@example.com"}])
    uri, recovery_codes = auth.begin_mfa_setup("admin")
    record = auth.users["admin"]
    assert uri.startswith("otpauth://totp/")
    assert len(recovery_codes) == 10
    assert "mfa_secret" not in record
    assert auth.confirm_mfa_setup("admin", "000000") is False
    assert auth.confirm_mfa_setup("admin", _current_otp(record["mfa_pending_secret"])) is True
    assert record["mfa_secret"]
    assert auth.consume_recovery_code("admin", recovery_codes[0]) is True
    assert auth.consume_recovery_code("admin", recovery_codes[0]) is False


def test_mfa_login_requires_otp_and_accepts_recovery_code():
    auth = AdminAuth([{"username": "admin", "password": "Admin123!"}])
    uri, recovery_codes = auth.begin_mfa_setup("admin")
    secret = auth.users["admin"]["mfa_pending_secret"]
    assert auth.confirm_mfa_setup("admin", _current_otp(secret)) is True
    assert asyncio.run(auth.login("admin", "Admin123!", "000000")) is None
    assert asyncio.run(auth.login("admin", "Admin123!", recovery_codes[1]))
