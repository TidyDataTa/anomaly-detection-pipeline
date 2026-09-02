"""Alert delivery: render the segment breakdown, send it to Telegram.

An alert is only useful if the on-call analyst can act on it, so every
message carries both the number that broke and the chart of which segments
moved.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: the pipeline runs on a scheduler, not a desktop

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from .detection import AnomalyResult  # noqa: E402

logger = logging.getLogger(__name__)

plt.style.use("ggplot")

DROP_COLOR = "#C44E52"  # the metric moved down
RISE_COLOR = "#4C78A8"  # the metric moved up


def render_segment_chart(
    segments: pd.DataFrame,
    result: AnomalyResult,
    output_path: str | Path,
) -> Path:
    """Draw the per-segment deviation chart and save it as a PNG.

    Bars are ordered by how far the segment moved and coloured by direction,
    so the segment that carries the anomaly is the first thing the reader
    sees. Each bar is labelled with its current value and its own baseline —
    a -60% swing on a tiny segment should not read like a -60% swing on a
    large one.
    """
    output_path = Path(output_path)
    segments = segments.dropna(subset=["diff_percentage"])
    segments = segments.sort_values(by="diff_percentage")

    height = max(3.5, 0.5 * len(segments) + 1.2)
    figure, axes = plt.subplots(figsize=(11, height))

    colors = [DROP_COLOR if value < 0 else RISE_COLOR for value in segments["diff_percentage"]]
    axes.barh(segments["segment"], segments["diff_percentage"], color=colors, alpha=0.85)

    span = max(segments["diff_percentage"].abs().max(), 1.0)
    offset = span * 0.03

    for index, row in enumerate(segments.itertuples(index=False)):
        negative = row.diff_percentage < 0
        axes.text(
            row.diff_percentage + (-offset if negative else offset),
            index,
            f"{row.diff_percentage:+.1f}%   ({row.segment_value:g} vs {row.mean_last_month:.1f})",
            va="center",
            ha="right" if negative else "left",
            fontsize=9,
            color="#333333",
        )

    lowest = min(0.0, float(segments["diff_percentage"].min()))
    highest = max(0.0, float(segments["diff_percentage"].max()))
    axes.set_xlim(
        lowest - (span * 0.95 if lowest < 0 else span * 0.05),
        highest + (span * 0.95 if highest > 0 else span * 0.05),
    )
    axes.invert_yaxis()  # largest drop on top, where the eye lands first
    axes.set_xlabel("Deviation from the 30-day baseline, %")
    axes.set_ylabel("")
    axes.set_title(
        f"{result.metric_name} — {result.metric_value:g} on "
        f"{result.calendar_date:%Y-%m-%d}, {result.direction} the expected "
        f"{result.lower_bound:g}…{result.upper_bound:g}",
        fontsize=12,
    )
    axes.axvline(0, color="#333333", linewidth=1)
    axes.grid(axis="x", linestyle="--", alpha=0.7)

    figure.tight_layout()
    figure.savefig(output_path, bbox_inches="tight", dpi=140)
    plt.close(figure)

    return output_path


def format_message(result: AnomalyResult, title: str | None = None) -> str:
    """Compose the alert text."""
    name = title or result.metric_name
    return (
        f"❗ {name} on {result.calendar_date:%Y-%m-%d}: "
        f"{result.metric_value:g} is {result.direction} the expected range "
        f"({result.lower_bound:g} … {result.upper_bound:g})."
    )


def send_alert(
    bot_token: str,
    chat_id: str,
    message: str,
    image_path: str | Path | None = None,
) -> None:
    """Send the alert to Telegram, with the chart attached when there is one."""
    from telegram.ext import Application

    async def _send() -> None:
        application = Application.builder().token(bot_token).build()
        async with application:
            if image_path is None:
                await application.bot.send_message(chat_id=chat_id, text=message)
                return
            with open(image_path, "rb") as photo:
                await application.bot.send_photo(chat_id=chat_id, photo=photo, caption=message)

    asyncio.run(_send())
    logger.info("alert delivered to chat %s", chat_id)
