from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from hybrid_trader.forward import (
    ForwardDecision,
    append_forward_decision,
    make_forward_decision,
    verify_forward_ledger,
)


def _decision(
    when: datetime,
    *,
    previous: str | None = None,
    recorded_at: datetime | None = None,
) -> ForwardDecision:
    return make_forward_decision(
        decision_time=when,
        recorded_at=recorded_at or when,
        symbol="BTC/USD",
        dataset_sha256="a" * 64,
        experiment_id="b" * 64,
        probability=0.7,
        threshold=0.6,
        desired_exposure=0.2,
        reason_codes=("model",),
        previous_record_sha256=previous,
    )


def test_forward_ledger_round_trip(tmp_path: Path) -> None:
    ledger = tmp_path / "decisions.jsonl"
    first = _decision(datetime(2026, 1, 1, tzinfo=UTC))
    first_sha = append_forward_decision(ledger, first)
    second = _decision(
        datetime(2026, 1, 1, 4, tzinfo=UTC),
        previous=first_sha,
    )
    second_sha = append_forward_decision(ledger, second)
    head, last, count = verify_forward_ledger(ledger)
    assert head == second_sha
    assert last == second
    assert count == 2


def test_forward_ledger_rejects_wrong_previous_hash(tmp_path: Path) -> None:
    ledger = tmp_path / "decisions.jsonl"
    append_forward_decision(ledger, _decision(datetime(2026, 1, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="current ledger head"):
        append_forward_decision(
            ledger,
            _decision(datetime(2026, 1, 1, 4, tzinfo=UTC), previous="c" * 64),
        )


def test_forward_ledger_detects_tampering(tmp_path: Path) -> None:
    ledger = tmp_path / "decisions.jsonl"
    first_sha = append_forward_decision(ledger, _decision(datetime(2026, 1, 1, tzinfo=UTC)))
    append_forward_decision(
        ledger,
        _decision(datetime(2026, 1, 1, 4, tzinfo=UTC), previous=first_sha),
    )
    text = ledger.read_text()
    ledger.write_text(text.replace('"probability":0.7', '"probability":0.6', 1))
    with pytest.raises(ValueError, match="hash chain"):
        verify_forward_ledger(ledger)


def test_forward_decision_rejects_recording_before_decision() -> None:
    when = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(ValueError, match="recorded_at"):
        _decision(when, recorded_at=when - timedelta(seconds=1))
