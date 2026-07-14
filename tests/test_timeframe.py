from datetime import timedelta

import pytest

from hybrid_trader.data.timeframe import timeframe_to_timedelta


def test_timeframe_parsing() -> None:
    assert timeframe_to_timedelta("4h") == timedelta(hours=4)
    assert timeframe_to_timedelta("15m") == timedelta(minutes=15)
    assert timeframe_to_timedelta("1w") == timedelta(weeks=1)


@pytest.mark.parametrize("value", ["0h", "4HOURS", "h4", "", "1M"])
def test_timeframe_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError):
        timeframe_to_timedelta(value)
