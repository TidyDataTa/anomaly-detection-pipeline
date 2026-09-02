"""The detection logic itself.

Two steps, deliberately separated:

1. :func:`detect_total` asks whether the metric's *total* value for the day
   under test falls outside the interval a Prophet forecast expected.
2. :func:`explain_segments` runs only when step 1 flagged something, and
   compares each user segment against its own 30-day baseline so the alert
   arrives with a hypothesis attached rather than just a red number.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import DetectionConfig
from .holidays import build_holiday_frame

logger = logging.getLogger(__name__)

TOTAL_PREFIX = "total_"
DATE_COLUMN = "date_trunc"


class InsufficientHistory(ValueError):
    """Raised when a series is too short to fit a model on."""


@dataclass
class AnomalyResult:
    """Outcome of a single metric check."""

    calendar_date: pd.Timestamp
    metric_name: str
    metric_value: float
    lower_bound: float
    upper_bound: float
    is_lower: int
    is_upper: int

    @property
    def is_anomaly(self) -> int:
        return max(self.is_lower, self.is_upper)

    @property
    def direction(self) -> str:
        return "below" if self.is_lower else "above"

    def as_row(self) -> dict[str, object]:
        return {
            "calendar_date": self.calendar_date,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "is_lower": self.is_lower,
            "is_upper": self.is_upper,
            "is_anomaly": self.is_anomaly,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
        }


def _round_by_magnitude(value: float) -> float:
    """Round to a number of decimals that suits the metric's scale.

    Counts read better as integers, conversion rates need three decimals.
    """
    value = float(value)
    if abs(value) > 10:
        return round(value, 0)
    if abs(value) > 1:
        return round(value, 2)
    return round(value, 3)


def prepare_series(frame: pd.DataFrame, metric_name: str, config: DetectionConfig) -> pd.DataFrame:
    """Return a clean, chronologically sorted frame for ``metric_name``."""
    frame = frame.copy()
    frame[DATE_COLUMN] = pd.to_datetime(frame[DATE_COLUMN])
    frame = frame.sort_values(by=DATE_COLUMN)

    if frame.isnull().any().any():
        logger.info("%s: dropping rows with missing values", metric_name)
        frame = frame.dropna()

    if len(frame) < config.min_history_points:
        raise InsufficientHistory(
            f"{metric_name}: {len(frame)} usable point(s), "
            f"{config.min_history_points} required to fit a model."
        )

    total_column = f"{TOTAL_PREFIX}{metric_name}"
    frame[total_column] = pd.to_numeric(frame[total_column])
    return frame


def _forecast_bounds(
    train: pd.DataFrame,
    config: DetectionConfig,
    bounds: dict | None,
) -> tuple[float, float, float]:
    """Fit Prophet on ``train`` and return (forecast, lower, upper) for the next point.

    A metric may pin a constant band via config instead of using the model
    interval — useful for ratios with a known acceptable range.
    """
    from prophet import Prophet

    bounds = bounds or {}
    use_const = bounds.get("type") == "const"

    model = Prophet(
        seasonality_mode=config.seasonality_mode,
        changepoint_prior_scale=config.changepoint_prior_scale,
        holidays=build_holiday_frame(),
        interval_width=config.interval_width,
    )
    model.fit(train)

    future = model.make_future_dataframe(periods=1)
    forecast = model.predict(future)

    forecast_value = float(forecast["yhat"].iloc[-1])
    if use_const:
        return forecast_value, float(bounds["lower"]), float(bounds["upper"])
    return (
        forecast_value,
        float(forecast["yhat_lower"].iloc[-1]),
        float(forecast["yhat_upper"].iloc[-1]),
    )


def detect_total(
    frame: pd.DataFrame,
    metric_name: str,
    config: DetectionConfig,
    bounds: dict | None = None,
    periods_back: int = 1,
) -> tuple[AnomalyResult, pd.DataFrame]:
    """Check the most recent point of ``metric_name`` against its forecast.

    Returns the result plus the cleaned frame, so the segment step can reuse
    exactly the rows the model saw.
    """
    frame = prepare_series(frame, metric_name, config)
    test_day = frame[DATE_COLUMN].tail(periods_back).values[0]
    frame = frame[frame[DATE_COLUMN] <= test_day]

    total_column = f"{TOTAL_PREFIX}{metric_name}"
    series = frame[[DATE_COLUMN, total_column]].rename(
        columns={DATE_COLUMN: "ds", total_column: "y"}
    )

    train = series[series["ds"] < test_day]
    test = series[series["ds"] == test_day]

    _, lower_bound, upper_bound = _forecast_bounds(train, config, bounds)

    actual_value = _round_by_magnitude(test["y"].iloc[-1])
    lower_bound = _round_by_magnitude(lower_bound)
    upper_bound = _round_by_magnitude(upper_bound)

    result = AnomalyResult(
        calendar_date=test["ds"].iloc[-1],
        metric_name=metric_name,
        metric_value=actual_value,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        is_lower=int(actual_value < lower_bound),
        is_upper=int(actual_value > upper_bound),
    )

    logger.info(
        "%s = %s, expected %s..%s -> %s",
        metric_name,
        actual_value,
        lower_bound,
        upper_bound,
        "ANOMALY" if result.is_anomaly else "ok",
    )
    return result, frame


def segment_columns(frame: pd.DataFrame, metric_name: str) -> list[str]:
    """Names of the per-segment columns of ``metric_name``."""
    suffix = f"_{metric_name}"
    return [
        column
        for column in frame.columns
        if column.endswith(suffix) and not column.startswith(TOTAL_PREFIX)
    ]


def explain_segments(
    frame: pd.DataFrame,
    metric_name: str,
    calendar_date: pd.Timestamp,
    config: DetectionConfig,
) -> pd.DataFrame:
    """Compare every segment's latest value against its own recent baseline.

    The baseline is the mean of the previous ``segment_baseline_days`` points,
    excluding the point under test, so a segment is measured against its own
    normal rather than against the other segments.
    """
    window = config.segment_baseline_days
    rows: list[dict[str, object]] = []

    for column in segment_columns(frame, metric_name):
        values = pd.to_numeric(frame[column], errors="coerce")

        baseline = values.iloc[-(window + 2) : -1].mean()
        current = float(values.iloc[-1])
        diff_percentage = np.round((current / baseline) * 100 - 100, 2) if baseline else np.nan

        rows.append(
            {
                "calendar_date": calendar_date,
                "metric_name": metric_name,
                "segment": column.replace(f"_{metric_name}", ""),
                "segment_value": current,
                "mean_last_month": baseline,
                "diff_percentage": diff_percentage,
            }
        )

    return pd.DataFrame(rows)
