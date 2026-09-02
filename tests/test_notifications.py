"""Tests for alert rendering. Delivery itself is not exercised here."""

from __future__ import annotations

import pandas as pd
import pytest

from anomaly_detection.detection import AnomalyResult
from anomaly_detection.notifications import format_message, render_segment_chart


@pytest.fixture
def result() -> AnomalyResult:
    return AnomalyResult(
        calendar_date=pd.Timestamp("2025-02-10"),
        metric_name="new_users",
        metric_value=617.0,
        lower_bound=938.0,
        upper_bound=1118.0,
        is_lower=1,
        is_upper=0,
    )


@pytest.fixture
def segments() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "calendar_date": [pd.Timestamp("2025-02-10")] * 3,
            "metric_name": ["new_users"] * 3,
            "segment": ["ios", "android", "web"],
            "segment_value": [131.0, 402.0, 84.0],
            "mean_last_month": [318.4, 421.7, 210.2],
            "diff_percentage": [-58.9, -4.7, -60.0],
        }
    )


def test_message_names_the_metric_the_value_and_the_band(result):
    message = format_message(result, title="New registrations")
    assert "New registrations" in message
    assert "2025-02-10" in message
    assert "617" in message
    assert "below" in message
    assert "938" in message and "1118" in message


def test_message_reports_the_other_direction(result):
    result.is_lower, result.is_upper = 0, 1
    assert "above" in format_message(result)


def test_chart_is_written(tmp_path, segments, result):
    path = render_segment_chart(segments, result, tmp_path / "chart.png")
    assert path.exists()
    assert path.stat().st_size > 5_000  # a real figure, not an empty canvas


def test_chart_survives_segments_without_a_baseline(tmp_path, segments, result):
    segments.loc[1, "diff_percentage"] = float("nan")
    path = render_segment_chart(segments, result, tmp_path / "chart.png")
    assert path.exists()
