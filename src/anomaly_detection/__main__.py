"""Command-line entry point: ``python -m anomaly_detection``."""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import sys

from .config import DEFAULT_CONFIG_PATH, Settings
from .pipeline import run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anomaly_detection",
        description="Check product metrics against their forecast and alert on deviations.",
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="path to metrics.yaml")
    parser.add_argument(
        "--metrics",
        nargs="*",
        help="only run these metrics, ignoring their schedule (default: everything due today)",
    )
    parser.add_argument(
        "--date", help="treat this ISO date as today, e.g. 2025-02-10 (default: today)"
    )
    parser.add_argument(
        "--chart-dir", help="where to write the segment charts (default: a temp directory)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="run the checks but write nothing and send no alerts",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )

    settings = Settings.load(args.config)
    if args.metrics:
        selected = [metric for metric in settings.metrics if metric.name in args.metrics]
        missing = set(args.metrics) - {metric.name for metric in selected}
        if missing:
            raise SystemExit(f"unknown metric(s): {', '.join(sorted(missing))}")
        settings = replace_metrics(settings, selected)

    today = dt.date.fromisoformat(args.date) if args.date else dt.date.today()

    totals, segments = run(
        settings=settings,
        today=today,
        dry_run=args.dry_run,
        chart_dir=args.chart_dir,
        force_all=bool(args.metrics),
    )
    if not totals.empty:
        print(totals.to_string(index=False))
    if not segments.empty:
        print(segments.to_string(index=False))
    return 0


def replace_metrics(settings: Settings, metrics: list) -> Settings:
    """Return a copy of ``settings`` restricted to ``metrics``."""
    import dataclasses

    return dataclasses.replace(settings, metrics=metrics)


if __name__ == "__main__":
    sys.exit(main())
