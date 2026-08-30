from flaxon.security import PasswordValidator
from flaxon.admin.services import AdminAuth


def test_password_validator_accepts_non_ascii_symbols():
    assert PasswordValidator().is_valid("SecurePass1§")


def test_password_validator_does_not_treat_spaces_as_special_symbols():
    assert not PasswordValidator().is_valid("SecurePass1 ")


def test_reset_token_survives_rejected_password():
    auth = AdminAuth([{"username": "owner", "email": "owner@example.com", "password": "OldPass1!"}])
    token = auth.request_password_reset("owner")
    assert token
    assert not auth.reset_password(token, "weak")
    assert auth.reset_password(token, "NewSecurePass1!")
