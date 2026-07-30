from __future__ import annotations

import time
from typing import Any

from flaxon.http import JSONResponse


class HealthResponse:
    def __init__(
        self,
        status: str = "healthy",
        details: dict[str, Any] | None = None,
        version: str | None = None,
        uptime: float | None = None,
    ) -> None:
        self.status = status
        self.details = details or {}
        self.version = version
        self.uptime = uptime
        self.timestamp = time.time()

    def to_dict(self) -> dict[str, Any]:
        result = {
            "status": self.status,
            "timestamp": self.timestamp,
        }

        if self.version:
            result["version"] = self.version

        if self.uptime:
            result["uptime"] = round(self.uptime, 2)

        if self.details:
            result["details"] = self.details

        return result

    def to_response(self) -> JSONResponse:
        status_code = 200 if self.status == "healthy" else 503
        return JSONResponse(self.to_dict(), status_code=status_code)


class HealthResponseBuilder:
    def __init__(self) -> None:
        self._status = "healthy"
        self._details: dict[str, Any] = {}
        self._version: str | None = None
        self._uptime: float | None = None

    def status(self, status: str) -> HealthResponseBuilder:
        self._status = status
        return self

    def healthy(self) -> HealthResponseBuilder:
        self._status = "healthy"
        return self

    def degraded(self) -> HealthResponseBuilder:
        self._status = "degraded"
        return self

    def unhealthy(self) -> HealthResponseBuilder:
        self._status = "unhealthy"
        return self

    def detail(self, key: str, value: Any) -> HealthResponseBuilder:
        self._details[key] = value
        return self

    def details(self, details: dict[str, Any]) -> HealthResponseBuilder:
        self._details.update(details)
        return self

    def version(self, version: str) -> HealthResponseBuilder:
        self._version = version
        return self

    def uptime(self, uptime: float) -> HealthResponseBuilder:
        self._uptime = uptime
        return self

    def build(self) -> HealthResponse:
        return HealthResponse(
            status=self._status,
            details=self._details,
            version=self._version,
            uptime=self._uptime,
        )

    def build_response(self) -> JSONResponse:
        return self.build().to_response()


def create_health_response(
    status: str = "healthy",
    details: dict[str, Any] | None = None,
    version: str | None = None,
) -> JSONResponse:
    response = HealthResponse(status, details, version)
    return response.to_response()
