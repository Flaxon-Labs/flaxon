"""
Application module for Flaxon.

This module contains the core application classes and components.
"""

from __future__ import annotations

from .app import Flaxon
from .bootstrap import ApplicationFactory, Bootstrapper, bootstrap_app
from .configuration import Config
from .context import (
    ContextMiddleware,
    RequestContext,
    get_current_request,
    get_current_websocket,
    get_request_context,
    request_context,
    websocket_context,
)
from .environment import Environment, EnvironmentInfo, get_env, set_debug, set_env
from .lifecycle import Lifecycle, call_maybe_async
from .registry import Registry, ServiceRegistry
from .state import State

__all__ = [
    "ApplicationFactory",
    "Bootstrapper",
    "Config",
    "ContextMiddleware",
    "Environment",
    "EnvironmentInfo",
    "Flaxon",
    "Lifecycle",
    "Registry",
    "RequestContext",
    "ServiceRegistry",
    "State",
    "bootstrap_app",
    "call_maybe_async",
    "get_current_request",
    "get_current_websocket",
    "get_env",
    "get_request_context",
    "request_context",
    "set_debug",
    "set_env",
    "websocket_context",
]
