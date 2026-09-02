"""Configuration loading.

Nothing secret lives in this repository. Credentials are read from the
environment (or from Airflow Variables when the pipeline runs inside
Airflow); everything else comes from ``config/metrics.yaml``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "metrics.yaml"
SQL_DIR = PROJECT_ROOT / "sql" / "metrics"


def _from_env_or_airflow(name: str, default: str | None = None) -> str | None:
    """Read a secret from the environment, falling back to Airflow Variables.

    Running the pipeline locally only needs a ``.env`` file; running it on
    Airflow only needs the Variables to be set. Neither path hardcodes a value.
    """
    value = os.environ.get(name)
    if value:
        return value

    try:  # pragma: no cover - only exercised inside Airflow
        from airflow.models import Variable

        return Variable.get(name, default_var=default)
    except Exception:
        return default


@dataclass(frozen=True)
class MetricConfig:
    """One monitored metric."""

    name: str
    query: str
    grain: str = "daily"
    title: str | None = None
    bounds: dict[str, Any] = field(default_factory=dict)

    @property
    def sql_path(self) -> Path:
        return SQL_DIR / self.query

    @property
    def display_name(self) -> str:
        return self.title or self.name

    def read_sql(self) -> str:
        return self.sql_path.read_text(encoding="utf-8")


@dataclass(frozen=True)
class DetectionConfig:
    """Model hyper-parameters and guard rails."""

    seasonality_mode: str = "multiplicative"
    changepoint_prior_scale: float = 20.0
    interval_width: float = 0.95
    min_history_points: int = 30
    segment_baseline_days: int = 30


@dataclass(frozen=True)
class OutputConfig:
    """Where results are written back to."""

    schema: str = "analytics"
    total_table: str = "total_anomaly"
    segment_table: str = "segment_anomaly"


@dataclass(frozen=True)
class Settings:
    """Everything the pipeline needs to run."""

    detection: DetectionConfig
    output: OutputConfig
    metrics: list[MetricConfig]

    # Secrets — never committed, always injected.
    postgres_conn_id: str | None = None
    database_url: str | None = None
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    @classmethod
    def load(cls, config_path: str | Path = DEFAULT_CONFIG_PATH) -> Settings:
        raw = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))

        return cls(
            detection=DetectionConfig(**(raw.get("detection") or {})),
            output=OutputConfig(**(raw.get("output") or {})),
            metrics=[MetricConfig(**item) for item in raw.get("metrics", [])],
            postgres_conn_id=_from_env_or_airflow("ANOMALY_POSTGRES_CONN_ID"),
            database_url=_from_env_or_airflow("ANOMALY_DATABASE_URL"),
            telegram_bot_token=_from_env_or_airflow("ANOMALY_TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=_from_env_or_airflow("ANOMALY_TELEGRAM_CHAT_ID"),
        )

    def metrics_for(self, grain: str) -> list[MetricConfig]:
        return [metric for metric in self.metrics if metric.grain == grain]
