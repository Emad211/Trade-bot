from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from hybrid_trader.replication.okx_prospective_registry import (
    ObservationClock,
    OKXProspectiveRegistryError,
    ProspectiveRegistryObservation,
    SourceHealthObservation,
    SourceHealthStatus,
    append_observation,
    diff_safe_values,
    tail_by_content_kind,
)

SHA_A = "a" * 64
BASE = datetime(2026, 7, 21, 10, 30, tzinfo=UTC)


def _observation(*, kind: str, offset: int = 0) -> ProspectiveRegistryObservation:
    request = BASE + timedelta(seconds=offset)
    return ProspectiveRegistryObservation(
        observation_clock=ObservationClock(
            request_started_at=request,
            response_received_at=request + timedelta(seconds=1),
            research_available_at=request + timedelta(seconds=2),
            registry_committed_at=request + timedelta(seconds=3),
        ),
        content_kind=kind,
        content_version_id=SHA_A,
        source_health=SourceHealthObservation(
            status=SourceHealthStatus.SUCCESS,
            http_status=200,
            latency_milliseconds=10,
            response_sha256=SHA_A,
        ),
    )


def test_diff_safe_values_returns_stable_dotted_paths() -> None:
    previous = {
        "selected_fields": {"tickSz": "0.1", "state": "live"},
        "schema_fields": ["a", "b"],
        "row_count": 100,
    }
    current = {
        "selected_fields": {"tickSz": "0.01", "state": "live", "minSz": "0.01"},
        "schema_fields": ["a", "b", "c"],
        "row_count": 100,
    }

    assert diff_safe_values(previous, current) == (
        "schema_fields",
        "selected_fields.minSz",
        "selected_fields.tickSz",
    )
    assert diff_safe_values(previous, previous) == ()


def test_tail_by_content_kind_returns_stream_tail_and_rejects_missing_stream() -> None:
    first = _observation(kind="INSTRUMENT")
    second = ProspectiveRegistryObservation(
        **{
            **_observation(kind="INSTRUMENT", offset=10).model_dump(),
            "previous_observation_id": first.observation_id,
        }
    )

    assert tail_by_content_kind([first, second], content_kind="INSTRUMENT") == second
    with pytest.raises(OKXProspectiveRegistryError, match="no observations"):
        tail_by_content_kind([first], content_kind="FUNDING_SOURCE")


def test_append_observation_rejects_mixed_content_streams() -> None:
    instrument = _observation(kind="INSTRUMENT")
    funding = ProspectiveRegistryObservation(
        **{
            **_observation(kind="FUNDING_SOURCE", offset=10).model_dump(),
            "previous_observation_id": instrument.observation_id,
        }
    )

    with pytest.raises(OKXProspectiveRegistryError, match="one content-kind stream"):
        append_observation([instrument], funding)
