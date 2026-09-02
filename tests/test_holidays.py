"""Tests for the holiday calendar handed to the model."""

from __future__ import annotations

import pandas as pd

from anomaly_detection.holidays import build_holiday_frame, new_year_break


def test_frame_has_the_columns_prophet_expects():
    frame = build_holiday_frame()
    assert list(frame.columns) == ["holiday", "ds"]
    assert pd.api.types.is_datetime64_any_dtype(frame["ds"])


def test_no_duplicate_dates_per_holiday():
    frame = build_holiday_frame()
    assert not frame.duplicated(subset=["holiday", "ds"]).any()


def test_new_year_break_belongs_to_the_right_year():
    dates = new_year_break(2025)
    assert dates[0] == pd.Timestamp("2024-12-30")
    assert dates[-1] == pd.Timestamp("2025-01-06")
    assert len(dates) == 7


def test_every_requested_year_is_covered():
    frame = build_holiday_frame(years=(2024, 2025))
    years = set(frame["ds"].dt.year)
    assert {2024, 2025} <= years
