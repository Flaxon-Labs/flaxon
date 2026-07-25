from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Any


class ReportGenerator:
    def __init__(self) -> None:
        self._reports: list[dict[str, Any]] = []

    def generate_error_report(self, error_data: dict[str, Any]) -> dict[str, Any]:
        return {
            "report_id": error_data.get("error_id"),
            "generated_at": datetime.now().isoformat(),
            "error": {
                "type": error_data.get("type"),
                "message": error_data.get("message"),
                "timestamp": error_data.get("timestamp"),
            },
            "request": {
                "method": error_data.get("method"),
                "path": error_data.get("path"),
                "request_id": error_data.get("request_id"),
            },
            "system": self._get_system_info(),
        }

    def generate_summary_report(self, errors: list[dict[str, Any]]) -> dict[str, Any]:
        types = {}
        paths = {}

        for error in errors:
            error_type = error.get("type", "Unknown")
            types[error_type] = types.get(error_type, 0) + 1

            path = error.get("path", "/")
            paths[path] = paths.get(path, 0) + 1

        return {
            "generated_at": datetime.now().isoformat(),
            "total_errors": len(errors),
            "by_type": types,
            "by_path": paths,
            "errors": errors[-10:],
        }

    def generate_performance_report(self, metrics: dict[str, Any]) -> dict[str, Any]:
        return {
            "generated_at": datetime.now().isoformat(),
            "performance": metrics,
            "timestamp": time.time(),
        }

    def _get_system_info(self) -> dict[str, Any]:
        import platform
        import sys

        return {
            "python_version": sys.version,
            "platform": platform.platform(),
            "hostname": platform.node(),
        }

    def to_json(self, report: dict[str, Any], pretty: bool = True) -> str:
        if pretty:
            return json.dumps(report, indent=2, default=str)
        return json.dumps(report, default=str)

    def save_report(self, report: dict[str, Any], filename: str) -> None:
        import os
        os.makedirs("reports", exist_ok=True)
        path = os.path.join("reports", filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
