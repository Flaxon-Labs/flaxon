"""
Route mounting for Flaxon.

This module provides functionality for mounting sub-applications
and routers at specific paths.
"""

from __future__ import annotations

from typing import Any

from .router import Router


class Mount:
    """
    Mount a sub-application or router at a specific path.

    This allows you to mount entire applications or routers at a path prefix,
    useful for modularizing large applications.

    Example:
        ```python
        from flaxon import Flaxon
        from flaxon.routing import Mount

        admin_app = Flaxon("admin")

        @admin_app.get("/")
        async def admin_home():
            return {"admin": True}

        app = Flaxon("main")
        mount = Mount("/admin", admin_app)
        app.include_router(mount)
        ```
    """

    def __init__(
        self,
        path: str,
        app: Any,
        *,
        name: str | None = None,
        middleware: list[type] | None = None,
    ) -> None:
        """
        Initialize the mount.

        Args:
            path: The path prefix to mount at.
            app: The application or router to mount.
            name: Optional name for the mount.
            middleware: Middleware to apply to the mounted app.
        """
        self.path = path.rstrip("/") if path != "/" else "/"
        self.app = app
        self.name = name
        self.middleware = middleware or []
        self._router = Router(prefix=self.path)

    def as_router(self) -> Router:
        """
        Convert the mount to a router.

        Returns:
            A router with the mounted app's routes.
        """
        if hasattr(self.app, "router"):
            self._router.include_router(self.app.router)
        elif hasattr(self.app, "routes"):
            for route in self.app.routes:
                self._router.add_route(
                    route.path,
                    route.endpoint,
                    methods=route.methods,
                    name=route.name,
                )
        else:
            raise ValueError(f"Cannot mount object of type {type(self.app)}")

        return self._router


def mount(path: str, app: Any, *, name: str | None = None) -> Mount:
    """
    Convenience function for mounting an application.

    Args:
        path: The path prefix to mount at.
        app: The application or router to mount.
        name: Optional name for the mount.

    Returns:
        A Mount object.

    Example:
        ```python
        admin_app = Flaxon("admin")
        app = Flaxon("main")
        app.include_router(mount("/admin", admin_app))
        ```
    """
    return Mount(path, app, name=name)
