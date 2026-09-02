"""Unit tests for the detection logic.

The Prophet fit itself is stubbed: what these tests protect is the decision
logic around it — data hygiene, bound comparison, rounding and the segment
breakdown — which is where the bugs that would page an on-call analyst live.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from anomaly_detection import detection
from anomaly_detection.config import DetectionConfig
from tests.conftest import make_frame

CONFIG = DetectionConfig()


@pytest.fixture(autouse=True)
def stub_prophet(monkeypatch):
    """Replace the model fit with a flat band around the training mean."""

    def fake_bounds(train, config, bounds):
        if bounds and bounds.get("type") == "const":
            return float(train["y"].mean()), float(bounds["lower"]), float(bounds["upper"])
        mean = float(train["y"].mean())
        spread = float(train["y"].std()) * 2
        return mean, mean - spread, mean + spread

    monkeypatch.setattr(detection, "_forecast_bounds", fake_bounds)


def test_normal_day_is_not_flagged(metric_frame):
    result, _ = detection.detect_total(metric_frame, "new_users", CONFIG)
    assert result.is_anomaly == 0
    assert result.lower_bound < result.metric_value < result.upper_bound


def test_spike_is_flagged_as_upper():
    result, _ = detection.detect_total(make_frame(spike=3.0), "new_users", CONFIG)
    assert (result.is_upper, result.is_lower, result.is_anomaly) == (1, 0, 1)
    assert result.direction == "above"


def test_drop_is_flagged_as_lower():
    result, _ = detection.detect_total(make_frame(spike=0.2), "new_users", CONFIG)
    assert (result.is_upper, result.is_lower, result.is_anomaly) == (0, 1, 1)
    assert result.direction == "below"


def test_short_history_is_refused():
    with pytest.raises(detection.InsufficientHistory):
        detection.detect_total(make_frame(days=10), "new_users", CONFIG)


def test_rows_with_gaps_are_dropped():
    frame = make_frame()
    frame.loc[5, "male_new_users"] = np.nan
    cleaned = detection.prepare_series(frame, "new_users", CONFIG)
    assert len(cleaned) == len(frame) - 1
    assert not cleaned.isnull().any().any()


@pytest.mark.parametrize(
    ("value", "expected"),
    [(1234.56, 1235.0), (5.4321, 5.43), (0.41234, 0.412), (-42.7, -43.0)],
)
def test_rounding_follows_magnitude(value, expected):
    assert detection._round_by_magnitude(value) == expected


def test_constant_bounds_override_the_model():
    frame = make_frame(metric="cv_7d")
    result, _ = detection.detect_total(
        frame, "cv_7d", CONFIG, bounds={"type": "const", "lower": 0.0, "upper": 10.0}
    )
    assert (result.lower_bound, result.upper_bound) == (0.0, 10.0)
    assert result.is_upper == 1


def test_segment_columns_exclude_the_total(metric_frame):
    columns = detection.segment_columns(metric_frame, "new_users")
    assert "total_new_users" not in columns
    assert set(columns) == {f"{s}_new_users" for s in ["female", "male", "ios", "android", "web"]}


def test_segment_breakdown_measures_against_own_baseline():
    frame = make_frame(spike=2.0)
    result, cleaned = detection.detect_total(frame, "new_users", CONFIG)
    segments = detection.explain_segments(cleaned, "new_users", result.calendar_date, CONFIG)

    assert len(segments) == 5
    assert set(segments["segment"]) == {"female", "male", "ios", "android", "web"}
    assert (segments["diff_percentage"] > 50).all()
    assert (segments["calendar_date"] == result.calendar_date).all()


def test_segment_breakdown_is_stable_when_nothing_moves(metric_frame):
    result, cleaned = detection.detect_total(metric_frame, "new_users", CONFIG)
    segments = detection.explain_segments(cleaned, "new_users", result.calendar_date, CONFIG)
    assert segments["diff_percentage"].abs().max() < 20


def test_result_row_matches_the_output_table(metric_frame):
    result, _ = detection.detect_total(metric_frame, "new_users", CONFIG)
    row = result.as_row()
    assert set(row) == {
        "calendar_date",
        "metric_name",
        "metric_value",
        "is_lower",
        "is_upper",
        "is_anomaly",
        "lower_bound",
        "upper_bound",
    }
    assert isinstance(row["calendar_date"], pd.Timestamp)
