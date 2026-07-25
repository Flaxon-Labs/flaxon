from __future__ import annotations

from flaxon.exceptions import FlaxonError


class WebSocketError(FlaxonError):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)
        self.message = message


class WebSocketConnectionError(WebSocketError):
    def __init__(self, message: str = "WebSocket connection failed") -> None:
        super().__init__(message)


class WebSocketHandshakeError(WebSocketError):
    def __init__(self, message: str = "WebSocket handshake failed") -> None:
        super().__init__(message)


class WebSocketProtocolError(WebSocketError):
    def __init__(self, message: str = "WebSocket protocol error") -> None:
        super().__init__(message)


class WebSocketMessageError(WebSocketError):
    def __init__(self, message: str = "WebSocket message error") -> None:
        super().__init__(message)


class WebSocketTimeoutError(WebSocketError):
    def __init__(self, message: str = "WebSocket timeout") -> None:
        super().__init__(message)


class WebSocketRoomError(WebSocketError):
    def __init__(self, message: str = "WebSocket room error") -> None:
        super().__init__(message)


class WebSocketBroadcastError(WebSocketError):
    def __init__(self, message: str = "WebSocket broadcast error") -> None:
        super().__init__(message)


class WebSocketAuthenticationError(WebSocketError):
    def __init__(self, message: str = "WebSocket authentication failed") -> None:
        super().__init__(message)
