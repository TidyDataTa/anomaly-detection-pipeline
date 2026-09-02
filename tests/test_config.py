"""Tests for configuration loading and scheduling."""

from __future__ import annotations

import datetime as dt

from anomaly_detection.config import Settings
from anomaly_detection.pipeline import due_metrics


def test_shipped_config_loads():
    settings = Settings.load()
    names = [metric.name for metric in settings.metrics]
    assert "new_users" in names
    assert settings.output.schema == "analytics"
    assert settings.detection.min_history_points == 30


def test_every_metric_points_at_an_existing_query():
    for metric in Settings.load().metrics:
        assert metric.sql_path.exists(), metric.query
        sql = metric.read_sql()
        assert f"total_{metric.name}" in sql
        assert "date_trunc" in sql


def test_no_secret_defaults_are_baked_in(monkeypatch):
    for variable in (
        "ANOMALY_DATABASE_URL",
        "ANOMALY_POSTGRES_CONN_ID",
        "ANOMALY_TELEGRAM_BOT_TOKEN",
        "ANOMALY_TELEGRAM_CHAT_ID",
    ):
        monkeypatch.delenv(variable, raising=False)

    settings = Settings.load()
    assert settings.database_url is None
    assert settings.telegram_bot_token is None


def test_weekly_metrics_only_run_on_monday():
    settings = Settings.load()
    monday = due_metrics(settings, dt.date(2025, 2, 10))
    tuesday = due_metrics(settings, dt.date(2025, 2, 11))

    assert {m.name for m in monday} - {m.name for m in tuesday} == {
        "s2_retention_14d",
        "lifetime_30d",
    }
    assert all(metric.grain == "daily" for metric in tuesday)


def test_explicit_selection_ignores_the_schedule():
    settings = Settings.load()
    forced = due_metrics(settings, dt.date(2025, 2, 11), force_all=True)
    assert "lifetime_30d" in {metric.name for metric in forced}
