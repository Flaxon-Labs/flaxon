from __future__ import annotations

from flaxon.http import Response, TextResponse

from .collector import MetricsCollector


class PrometheusExporter:
    def __init__(self, collector: MetricsCollector | None = None) -> None:
        self.collector = collector or MetricsCollector()

    def export(self) -> str:
        lines = []

        for name, counter in self.collector._counters.items():
            lines.append(f"# HELP {name} {counter.help_text}")
            lines.append(f"# TYPE {name} counter")
            for key, value in counter.get_all().items():
                if key:
                    lines.append(f'{name}{{{key}}} {value}')
                else:
                    lines.append(f"{name} {value}")
            lines.append("")

        for name, gauge in self.collector._gauges.items():
            lines.append(f"# HELP {name} {gauge.help_text}")
            lines.append(f"# TYPE {name} gauge")
            for key, value in gauge.get_all().items():
                if key:
                    lines.append(f'{name}{{{key}}} {value}')
                else:
                    lines.append(f"{name} {value}")
            lines.append("")

        for name, timer in self.collector._timers.items():
            lines.append(f"# HELP {name} {timer.help_text}")
            lines.append(f"# TYPE {name} summary")
            for key, stats in timer.get_all_stats().items():
                label_str = f"{{{key}}}" if key else ""
                lines.append(f'{name}_count{label_str} {stats["count"]}')
                lines.append(f'{name}_sum{label_str} {stats["sum"]}')
            lines.append("")

        for name, histogram in self.collector._histograms.items():
            lines.append(f"# HELP {name} {histogram.help_text}")
            lines.append(f"# TYPE {name} histogram")
            for key, values in histogram.get_all_stats().items():
                label_str = f"{{{key}}}" if key else ""
                for bucket in histogram.buckets:
                    le_key = f"le_{bucket}"
                    if le_key in values:
                        lines.append(f'{name}_bucket{label_str} {{le="{bucket}"}} {values[le_key]}')
                lines.append(f'{name}_bucket{label_str} {{le="+Inf"}} {values.get("count", 0)}')
                lines.append(f'{name}_count{label_str} {values.get("count", 0)}')
                lines.append(f'{name}_sum{label_str} {values.get("sum", 0.0)}')
            lines.append("")

        return "\n".join(lines)

    def response(self) -> Response:
        return TextResponse(
            self.export(),
            status_code=200,
            headers={"Content-Type": "text/plain; version=0.0.4"},
        )


def prometheus_metrics(collector: MetricsCollector | None = None) -> Response:
    exporter = PrometheusExporter(collector)
    return exporter.response()
