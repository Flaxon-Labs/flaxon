from __future__ import annotations

from collections.abc import Callable
from typing import Any

from flaxon.exceptions import Forbidden, Unauthorized
from flaxon.http import Request

from .authentication import User


class AuthorizationMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        await self.app(scope, receive, send)


def has_permission(user: User | None, permission: str) -> bool:
    if user is None:
        return False
    return user.has_permission(permission)


def has_role(user: User | None, role: str) -> bool:
    if user is None:
        return False
    return user.has_role(role)


def authorize(permission: str | None = None, role: str | None = None) -> Callable:
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if request is None:
                for arg in kwargs.values():
                    if isinstance(arg, Request):
                        request = arg
                        break

            if request is None:
                raise Unauthorized("Authentication required")

            user = getattr(request, "user", None)
            if user is None:
                raise Unauthorized("Authentication required")

            if permission is not None and not has_permission(user, permission):
                raise Forbidden(f"Permission '{permission}' required")

            if role is not None and not has_role(user, role):
                raise Forbidden(f"Role '{role}' required")

            result = func(*args, **kwargs)
            if hasattr(result, "__await__"):
                return await result
            return result
        return wrapper
    return decorator


def permission_required(permission: str) -> Callable:
    return authorize(permission=permission)


def role_required(role: str) -> Callable:
    return authorize(role=role)


class AuthorizationChecker:
    def __init__(self, user: User | None) -> None:
        self.user = user

    def has_permission(self, permission: str) -> bool:
        return has_permission(self.user, permission)

    def has_role(self, role: str) -> bool:
        return has_role(self.user, role)

    def require_permission(self, permission: str) -> None:
        if not self.has_permission(permission):
            raise Forbidden(f"Permission '{permission}' required")

    def require_role(self, role: str) -> None:
        if not self.has_role(role):
            raise Forbidden(f"Role '{role}' required")

    def require_any_permission(self, *permissions: str) -> None:
        for permission in permissions:
            if self.has_permission(permission):
                return
        raise Forbidden(f"One of permissions required: {', '.join(permissions)}")

    def require_any_role(self, *roles: str) -> None:
        for role in roles:
            if self.has_role(role):
                return
        raise Forbidden(f"One of roles required: {', '.join(roles)}")
