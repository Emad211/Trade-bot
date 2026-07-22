"""CFTC Commitments of Traders timing and semantic guards."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

EASTERN = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


def standard_release_time(report_as_of: date) -> datetime:
    """Return the normal Friday 15:30 Eastern release after the report date."""

    days_until_friday = (4 - report_as_of.weekday()) % 7
    release_date = report_as_of + timedelta(days=days_until_friday)
    return datetime.combine(release_date, time(15, 30), tzinfo=EASTERN).astimezone(UTC)


def release_time(
    report_as_of: date,
    *,
    overrides: Mapping[date, datetime] | None = None,
) -> datetime:
    if overrides and report_as_of in overrides:
        result = overrides[report_as_of]
        if result.tzinfo is None:
            raise ValueError("Release override must be timezone-aware")
        return result.astimezone(UTC)
    return standard_release_time(report_as_of)


def normalize_cot_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    report_family: str,
    parser_delay: timedelta = timedelta(minutes=1),
    release_overrides: Mapping[date, datetime] | None = None,
) -> pd.DataFrame:
    if parser_delay < timedelta(0):
        raise ValueError("parser_delay cannot be negative")
    if not rows:
        raise ValueError("No CFTC rows supplied")

    frame = pd.DataFrame(rows)
    date_field = "report_date_as_yyyy_mm_dd"
    if date_field not in frame:
        raise ValueError(f"Missing {date_field}")
    frame["report_as_of_time"] = pd.to_datetime(frame[date_field], utc=True, errors="raise")
    frame["actual_release_time"] = [
        pd.Timestamp(release_time(timestamp.date(), overrides=release_overrides))
        for timestamp in frame["report_as_of_time"]
    ]
    frame["available_at"] = frame["actual_release_time"] + pd.Timedelta(parser_delay)
    frame["report_family"] = report_family
    if (frame["available_at"] <= frame["report_as_of_time"]).any():
        raise ValueError("CFTC data became available before its report date")
    return frame


def normalized_pressure(long: pd.Series, short: pd.Series) -> pd.Series:
    long_numeric = pd.to_numeric(long, errors="raise").astype(float)
    short_numeric = pd.to_numeric(short, errors="raise").astype(float)
    if (long_numeric < 0).any() or (short_numeric < 0).any():
        raise ValueError("CFTC positions cannot be negative")
    denominator = long_numeric + short_numeric
    values = (long_numeric - short_numeric) / denominator.replace(0.0, np.nan)
    return values
