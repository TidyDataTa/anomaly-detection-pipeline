"""Shared fixtures: a synthetic metric frame that behaves like the real one."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

SEGMENTS = ["female", "male", "ios", "android", "web"]


def make_frame(
    metric: str = "new_users",
    days: int = 120,
    end: str = "2025-02-10",
    spike: float = 1.0,
) -> pd.DataFrame:
    """Build a seasonal metric series ending on ``end``.

    ``spike`` multiplies the final day, which is how the tests simulate an
    anomaly without needing a real model fit.
    """
    rng = np.random.default_rng(42)
    dates = pd.date_range(end=end, periods=days, freq="D")
    weekly = 1 + 0.1 * np.sin(np.arange(days) * 2 * np.pi / 7)
    base = 1000 * weekly + rng.normal(0, 15, days)
    base[-1] *= spike

    frame = pd.DataFrame({"date_trunc": dates})
    share = 1.0 / len(SEGMENTS)
    for index, segment in enumerate(SEGMENTS):
        frame[f"{segment}_{metric}"] = np.round(base * share * (1 + 0.02 * index))
    frame[f"total_{metric}"] = np.round(base)
    return frame


@pytest.fixture
def metric_frame() -> pd.DataFrame:
    return make_frame()
