from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from hybrid_trader.events import EventSignal


def test_event_signal_is_constrained() -> None:
    event = EventSignal(
        asset="BTC",
        event_time_utc=datetime.now(UTC),
        event_type="regulation",
        direction="bearish",
        horizon="1d_3d",
        severity=0.8,
        novelty=0.9,
        source_quality=0.95,
        confidence=0.7,
        evidence_ids=("source-1",),
    )
    assert event.asset == "BTC"


def test_event_signal_rejects_unbounded_scores() -> None:
    with pytest.raises(ValidationError):
        EventSignal(
            asset="BTC",
            event_time_utc=datetime.now(UTC),
            event_type="regulation",
            direction="bearish",
            horizon="1d_3d",
            severity=1.5,
            novelty=0.9,
            source_quality=0.95,
            confidence=0.7,
        )
