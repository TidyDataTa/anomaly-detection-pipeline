"""Orchestration: run every configured metric, store results, raise alerts.

One metric failing must never take the run down with it — each check is
isolated, and whatever succeeded is still written and reported.
"""

from __future__ import annotations

import datetime as dt
import logging
import tempfile
from pathlib import Path

import pandas as pd

from . import db
from .config import MetricConfig, Settings
from .detection import InsufficientHistory, detect_total, explain_segments
from .notifications import format_message, render_segment_chart, send_alert

logger = logging.getLogger(__name__)

TOTAL_TABLE_COLUMNS = [
    ("calendar_date", "date"),
    ("metric_name", "text"),
    ("metric_value", "float"),
    ("is_lower", "int"),
    ("is_upper", "int"),
    ("is_anomaly", "int"),
    ("lower_bound", "float"),
    ("upper_bound", "float"),
    ("load_date", "date"),
]

SEGMENT_TABLE_COLUMNS = [
    ("calendar_date", "date"),
    ("metric_name", "text"),
    ("segment", "text"),
    ("segment_value", "float"),
    ("mean_last_month", "float"),
    ("diff_percentage", "float"),
    ("load_date", "date"),
]


def due_metrics(
    settings: Settings,
    today: dt.date | None = None,
    force_all: bool = False,
) -> list[MetricConfig]:
    """Metrics that have a fresh data point today.

    Daily metrics run every day; weekly ones only on Monday, when the week
    that just closed is complete. ``force_all`` overrides that, which is what
    an explicit ``--metrics`` selection on the command line means.
    """
    today = today or dt.date.today()
    metrics = settings.metrics_for("daily")
    if force_all or today.weekday() == 0:
        metrics += settings.metrics_for("weekly")
    else:
        weekly = settings.metrics_for("weekly")
        logger.info("not Monday — skipping %d weekly metric(s)", len(weekly))
    return metrics


def run(
    settings: Settings | None = None,
    today: dt.date | None = None,
    dry_run: bool = False,
    chart_dir: str | Path | None = None,
    force_all: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run the pipeline end to end and return (totals, segments)."""
    settings = settings or Settings.load()
    today = today or dt.date.today()
    chart_dir = Path(chart_dir or tempfile.gettempdir())
    chart_dir.mkdir(parents=True, exist_ok=True)

    total_rows: list[dict[str, object]] = []
    segment_frames: list[pd.DataFrame] = []

    with db.connect(settings.postgres_conn_id, settings.database_url) as connection:
        cursor = connection.cursor()

        for metric in due_metrics(settings, today, force_all):
            try:
                frame = db.read_sql(cursor, metric.read_sql())
                result, cleaned = detect_total(
                    frame, metric.name, settings.detection, metric.bounds
                )
            except InsufficientHistory as error:
                logger.warning("%s", error)
                continue
            except Exception:
                logger.exception("%s: check failed", metric.name)
                continue

            total_rows.append(result.as_row())

            if not result.is_anomaly:
                continue

            try:
                segments = explain_segments(
                    cleaned, metric.name, result.calendar_date, settings.detection
                )
                segment_frames.append(segments)

                chart_path = render_segment_chart(
                    segments, result, chart_dir / f"{metric.name}.png"
                )
                if dry_run:
                    logger.info("dry run: alert for %s not sent (%s)", metric.name, chart_path)
                else:
                    send_alert(
                        settings.telegram_bot_token,
                        settings.telegram_chat_id,
                        format_message(result, metric.display_name),
                        chart_path,
                    )
            except Exception:
                logger.exception("%s: flagged, but the alert could not be delivered", metric.name)

        totals = pd.DataFrame(total_rows)
        segments = (
            pd.concat(segment_frames, ignore_index=True) if segment_frames else pd.DataFrame()
        )
        for frame in (totals, segments):
            if not frame.empty:
                frame["load_date"] = today

        if dry_run:
            logger.info("dry run: results not written to the warehouse")
            return totals, segments

        output = settings.output
        db.ensure_table(cursor, output.schema, output.total_table, TOTAL_TABLE_COLUMNS)
        db.ensure_table(cursor, output.schema, output.segment_table, SEGMENT_TABLE_COLUMNS)
        db.upsert_by_pointer(cursor, totals, output.schema, output.total_table, "calendar_date")
        db.upsert_by_pointer(cursor, segments, output.schema, output.segment_table, "calendar_date")

        cursor.close()

    logger.info("run finished: %d metric(s) checked, %d flagged", len(totals), len(segment_frames))
    return totals, segments
