#!/usr/bin/env python
"""
Benchmark runner for Flaxon.

This script runs all benchmarks and generates a report.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_benchmark(script: str) -> dict:
    """Run a benchmark script and return results."""
    print(f"Running {script}...")

    result = subprocess.run(
        [sys.executable, script],
        capture_output=True,
        text=True,
        cwd="benchmarks",
    )

    if result.returncode != 0:
        print(f"Error running {script}:")
        print(result.stderr)

    return {
        "script": script,
        "output": result.stdout,
        "error": result.stderr,
        "returncode": result.returncode,
    }


def run_all_benchmarks() -> dict:
    """Run all benchmark scripts."""
    benchmark_scripts = [
        "routing_benchmark.py",
        "json_benchmark.py",
        "middleware_benchmark.py",
        "websocket_benchmark.py",
        "template_benchmark.py",
    ]

    results = {}
    for script in benchmark_scripts:
        results[script] = run_benchmark(script)

    return results


def generate_report(results: dict) -> str:
    """Generate a benchmark report."""
    lines = []
    lines.append("=" * 60)
    lines.append("Flaxon Benchmark Report")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("=" * 60)

    for script, result in results.items():
        lines.append(f"\n{script}:")
        if result["returncode"] == 0:
            lines.append("  Status: SUCCESS")
            lines.append(result["output"])
        else:
            lines.append("  Status: FAILED")
            lines.append(result["error"])

    return "\n".join(lines)


def save_report(report: str) -> None:
    """Save the benchmark report to a file."""
    report_dir = Path("benchmarks/results")
    report_dir.mkdir(parents=True, exist_ok=True)

    report_path = report_dir / "benchmark_report.txt"
    report_path.write_text(report)

    print(f"Report saved to {report_path}")


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run Flaxon benchmarks")
    parser.add_argument(
        "--script",
        help="Run a specific benchmark script",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available benchmark scripts",
    )

    args = parser.parse_args()

    if args.list:
        print("Available benchmark scripts:")
        print("  - routing_benchmark.py")
        print("  - json_benchmark.py")
        print("  - middleware_benchmark.py")
        print("  - websocket_benchmark.py")
        print("  - template_benchmark.py")
        return

    if args.script:
        result = run_benchmark(args.script)
        print(result["output"])
        if result["returncode"] != 0:
            sys.exit(1)
        return

    results = run_all_benchmarks()
    report = generate_report(results)
    print(report)
    save_report(report)


if __name__ == "__main__":
    main()