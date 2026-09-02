"""Airflow DAG: run the anomaly detection pipeline once a day.

Scheduled at 03:15 UTC, after the nightly warehouse refresh has landed, so
every metric sees a complete previous day.
"""

from __future__ import annotations

import datetime as dt

from airflow import DAG
from airflow.operators.python import PythonOperator
from callbacks import notify_failure

DEFAULT_ARGS = {
    "owner": "analytics",
    "retries": 1,
    "retry_delay": dt.timedelta(minutes=10),
    "on_failure_callback": notify_failure,
}


def run_anomaly_detection(**_context) -> None:
    """Thin wrapper so the DAG stays free of business logic."""
    from anomaly_detection.pipeline import run

    run()


with DAG(
    dag_id="anomaly_detection",
    description="Forecast-based anomaly detection over core product metrics",
    default_args=DEFAULT_ARGS,
    start_date=dt.datetime(2025, 2, 6),
    schedule_interval="15 3 * * *",
    catchup=False,
    max_active_runs=1,
    tags=["analytics", "monitoring"],
) as dag:
    detect_anomalies = PythonOperator(
        task_id="detect_anomalies",
        python_callable=run_anomaly_detection,
    )
