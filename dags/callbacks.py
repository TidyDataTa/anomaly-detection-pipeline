"""Airflow failure callback: report broken runs to the same Telegram chat.

An alerting pipeline that fails silently is worse than no pipeline at all.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def notify_failure(context: dict) -> None:
    """Send a short failure notice for the task that just failed."""
    from anomaly_detection.config import Settings
    from anomaly_detection.notifications import send_alert

    task_instance = context.get("task_instance")
    message = (
        "🔥 Airflow task failed\n"
        f"DAG: {context.get('dag').dag_id if context.get('dag') else 'unknown'}\n"
        f"Task: {task_instance.task_id if task_instance else 'unknown'}\n"
        f"Run: {context.get('run_id', 'unknown')}\n"
        f"Log: {task_instance.log_url if task_instance else 'n/a'}"
    )

    settings = Settings.load()
    if not (settings.telegram_bot_token and settings.telegram_chat_id):
        logger.error("Telegram is not configured; failure notice dropped:\n%s", message)
        return

    send_alert(settings.telegram_bot_token, settings.telegram_chat_id, message)
