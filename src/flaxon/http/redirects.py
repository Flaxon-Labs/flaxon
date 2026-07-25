"""
HTTP redirect handling for Flaxon.

This module provides utilities for handling HTTP redirects.
"""

from __future__ import annotations

from typing import Any

from .response import RedirectResponse


class Redirect:
    """
    Redirect utility class.

    This class provides static methods for creating redirect responses.
    """

    @staticmethod
    def to(
        url: str,
        status_code: int = 307,
        headers: dict[str, str] | None = None,
    ) -> RedirectResponse:
        """
        Redirect to a URL.

        Args:
            url: The URL to redirect to.
            status_code: The redirect status code.
            headers: Additional headers.

        Returns:
            A redirect response.
        """
        return RedirectResponse(url, status_code=status_code, headers=headers)

    @staticmethod
    def permanent(url: str, headers: dict[str, str] | None = None) -> RedirectResponse:
        """
        Redirect permanently (301).

        Args:
            url: The URL to redirect to.
            headers: Additional headers.

        Returns:
            A redirect response.
        """
        return RedirectResponse(url, status_code=301, headers=headers)

    @staticmethod
    def temporary(url: str, headers: dict[str, str] | None = None) -> RedirectResponse:
        """
        Redirect temporarily (307).

        Args:
            url: The URL to redirect to.
            headers: Additional headers.

        Returns:
            A redirect response.
        """
        return RedirectResponse(url, status_code=307, headers=headers)

    @staticmethod
    def found(url: str, headers: dict[str, str] | None = None) -> RedirectResponse:
        """
        Redirect with 302 Found.

        Args:
            url: The URL to redirect to.
            headers: Additional headers.

        Returns:
            A redirect response.
        """
        return RedirectResponse(url, status_code=302, headers=headers)

    @staticmethod
    def see_other(url: str, headers: dict[str, str] | None = None) -> RedirectResponse:
        """
        Redirect with 303 See Other.

        Args:
            url: The URL to redirect to.
            headers: Additional headers.

        Returns:
            A redirect response.
        """
        return RedirectResponse(url, status_code=303, headers=headers)

    @staticmethod
    def https(
        domain: str,
        path: str = "/",
        status_code: int = 307,
        headers: dict[str, str] | None = None,
    ) -> RedirectResponse:
        """
        Redirect to HTTPS.

        Args:
            domain: The domain to redirect to.
            path: The path to redirect to.
            status_code: The redirect status code.
            headers: Additional headers.

        Returns:
            A redirect response.
        """
        url = f"https://{domain}{path}"
        return RedirectResponse(url, status_code=status_code, headers=headers)

    @staticmethod
    def www(
        domain: str,
        path: str = "/",
        status_code: int = 307,
        headers: dict[str, str] | None = None,
    ) -> RedirectResponse:
        """
        Redirect to www subdomain.

        Args:
            domain: The domain to redirect to.
            path: The path to redirect to.
            status_code: The redirect status code.
            headers: Additional headers.

        Returns:
            A redirect response.
        """
        if not domain.startswith("www."):
            domain = f"www.{domain}"
        url = f"https://{domain}{path}"
        return RedirectResponse(url, status_code=status_code, headers=headers)

    @staticmethod
    def non_www(
        domain: str,
        path: str = "/",
        status_code: int = 307,
        headers: dict[str, str] | None = None,
    ) -> RedirectResponse:
        """
        Redirect to non-www subdomain.

        Args:
            domain: The domain to redirect to.
            path: The path to redirect to.
            status_code: The redirect status code.
            headers: Additional headers.

        Returns:
            A redirect response.
        """
        if domain.startswith("www."):
            domain = domain[4:]
        url = f"https://{domain}{path}"
        return RedirectResponse(url, status_code=status_code, headers=headers)


class RedirectMiddleware:
    """
    Middleware for handling redirects.

    This middleware can automatically handle redirects based on request
    conditions (e.g., HTTPS enforcement, www/non-www redirection).
    """

    def __init__(
        self,
        app: Any,
        enforce_https: bool = False,
        enforce_www: bool | None = None,
        redirect_status: int = 301,
    ) -> None:
        """
        Initialize the middleware.

        Args:
            app: The ASGI application.
            enforce_https: Whether to enforce HTTPS.
            enforce_www: Whether to enforce www (True=www, False=non-www, None=no change).
            redirect_status: The redirect status code.
        """
        self.app = app
        self.enforce_https = enforce_https
        self.enforce_www = enforce_www
        self.redirect_status = redirect_status

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        """
        Process the request with redirect handling.

        Args:
            scope: The ASGI scope.
            receive: The ASGI receive callable.
            send: The ASGI send callable.
        """
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        headers = scope.get("headers", [])
        host = None
        for key, value in headers:
            if key.lower() == b"host":
                host = value.decode("latin-1")
                break

        if host is None:
            host = "localhost"

        if self.enforce_https and scope.get("scheme") == "http":
            path = scope.get("path", "/")
            url = f"https://{host}{path}"
            response = RedirectResponse(url, status_code=self.redirect_status)
            await response(scope, receive, send)
            return

        if self.enforce_www is not None:
            path = scope.get("path", "/")
            scheme = scope.get("scheme", "https")

            if self.enforce_www and not host.startswith("www."):
                url = f"{scheme}://www.{host}{path}"
                response = RedirectResponse(url, status_code=self.redirect_status)
                await response(scope, receive, send)
                return

            if not self.enforce_www and host.startswith("www."):
                url = f"{scheme}://{host[4:]}{path}"
                response = RedirectResponse(url, status_code=self.redirect_status)
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)
