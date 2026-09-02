"""Public-holiday calendar handed to Prophet.

Traffic collapses on public holidays and during the New Year break. Feeding
those dates to the model keeps them from being reported as anomalies every
January.

The dates below are the Russian public holidays; swap them for your own
market. Easter is movable, so it is listed per year.
"""

from __future__ import annotations

import pandas as pd

# Fixed-date public holidays, month/day.
FIXED_HOLIDAYS: dict[str, tuple[int, int]] = {
    "New Year": (1, 1),
    "Orthodox Christmas": (1, 7),
    "Defender of the Fatherland Day": (2, 23),
    "International Women's Day": (3, 8),
    "Spring and Labour Day": (5, 1),
    "Victory Day": (5, 9),
    "Russia Day": (6, 12),
    "Unity Day": (11, 4),
}

# Movable feast, one entry per covered year.
EASTER: dict[int, str] = {
    2023: "2023-04-16",
    2024: "2024-05-05",
    2025: "2025-04-20",
    2026: "2026-04-12",
    2027: "2027-05-02",
}

DEFAULT_YEARS = tuple(EASTER)


def new_year_break(year: int) -> list[pd.Timestamp]:
    """Dates of the extended New Year break leading into ``year``.

    December 30-31 of the previous year plus January 2-6, i.e. the low-traffic
    days around the two fixed holidays that are already listed above.
    """
    return [
        pd.Timestamp(year - 1, 12, 30),
        pd.Timestamp(year - 1, 12, 31),
        *[pd.Timestamp(year, 1, day) for day in range(2, 7)],
    ]


def build_holiday_frame(years: tuple[int, ...] = DEFAULT_YEARS) -> pd.DataFrame:
    """Return the Prophet ``holidays`` frame for the given years."""
    records: list[dict[str, object]] = []

    for year in years:
        for name, (month, day) in FIXED_HOLIDAYS.items():
            records.append({"holiday": name, "ds": pd.Timestamp(year, month, day)})

        if year in EASTER:
            records.append({"holiday": "Easter", "ds": pd.Timestamp(EASTER[year])})

        for date in new_year_break(year):
            records.append({"holiday": "New Year break", "ds": date})

    frame = pd.DataFrame(records)
    return frame.drop_duplicates(subset=["holiday", "ds"]).sort_values("ds").reset_index(drop=True)
