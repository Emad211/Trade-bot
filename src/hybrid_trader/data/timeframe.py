"""Utilities for parsing exchange timeframes without silent assumptions."""

from __future__ import annotations

import re
from datetime import timedelta

_TIMEFRAME_RE = re.compile(r"^(?P<count>[1-9][0-9]*)(?P<unit>[smhdw])$")


def timeframe_to_timedelta(value: str) -> timedelta:
    """Convert a compact exchange timeframe, for example ``4h``, to timedelta."""

    match = _TIMEFRAME_RE.fullmatch(value.strip())
    if match is None:
        raise ValueError("timeframe must match <positive integer><s|m|h|d|w>")
    count = int(match.group("count"))
    unit = match.group("unit")
    multipliers = {
        "s": timedelta(seconds=1),
        "m": timedelta(minutes=1),
        "h": timedelta(hours=1),
        "d": timedelta(days=1),
        "w": timedelta(weeks=1),
    }
    return count * multipliers[unit]
