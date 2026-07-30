from __future__ import annotations

from flaxon.exceptions import FlaxonError


class SecurityError(FlaxonError):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)
        self.message = message


class AuthenticationError(SecurityError):
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message)


class AuthorizationError(SecurityError):
    def __init__(self, message: str = "Authorization failed") -> None:
        super().__init__(message)


class TokenError(SecurityError):
    def __init__(self, message: str = "Invalid token") -> None:
        super().__init__(message)


class TokenExpiredError(TokenError):
    def __init__(self, message: str = "Token has expired") -> None:
        super().__init__(message)


class TokenInvalidError(TokenError):
    def __init__(self, message: str = "Invalid token") -> None:
        super().__init__(message)


class PermissionDenied(AuthorizationError):
    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(message)


class RateLimitExceeded(SecurityError):
    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(message)


class EncryptionError(SecurityError):
    def __init__(self, message: str = "Encryption error") -> None:
        super().__init__(message)


class DecryptionError(SecurityError):
    def __init__(self, message: str = "Decryption error") -> None:
        super().__init__(message)
