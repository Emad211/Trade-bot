from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from hybrid_trader.replication.okx_prospective_registry import (
    AvailabilitySemantics,
    ObservationClock,
    OKXProspectiveRegistryError,
    ProspectiveFundingSourceContent,
    ProspectiveInstrumentContent,
    ProspectiveRegistryObservation,
    SourceHealthObservation,
    SourceHealthStatus,
    append_observation,
    diff_selected_fields,
)

BASE_TIME = datetime(2026, 7, 21, 10, 15, tzinfo=UTC)
SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64


def _clock(offset_seconds: int = 0) -> ObservationClock:
    request = BASE_TIME + timedelta(seconds=offset_seconds)
    response = request + timedelta(seconds=1)
    available = response + timedelta(seconds=1)
    committed = available + timedelta(seconds=1)
    return ObservationClock(
        request_started_at=request,
        response_received_at=response,
        provider_timestamp=None,
        research_available_at=available,
        registry_committed_at=committed,
    )


def _health(response_sha256: str = SHA_A) -> SourceHealthObservation:
    return SourceHealthObservation(
        status=SourceHealthStatus.SUCCESS,
        http_status=200,
        application_code="0",
        latency_milliseconds=125,
        response_sha256=response_sha256,
    )


def _instrument_content(
    *,
    response_sha256: str = SHA_A,
    tick_size: str = "0.1",
) -> ProspectiveInstrumentContent:
    return ProspectiveInstrumentContent(
        source_id="OKX_CURRENT_BTC_USDT_SWAP_INSTRUMENT_API",
        official_host="www.okx.com",
        endpoint_path="/api/v5/public/instruments",
        response_byte_count=1079,
        response_sha256=response_sha256,
        schema_fields=("ctType", "ctVal", "instId", "tickSz"),
        schema_sha256=SHA_B,
        selected_fields={
            "instId": "BTC-USDT-SWAP",
            "ctType": "linear",
            "ctVal": "0.01",
            "tickSz": tick_size,
        },
        provider_time_fields={
            "listTime": "1573557408000",
            "contTdSwTime": "1611916860000",
        },
    )


def _observation(
    content: ProspectiveInstrumentContent,
    *,
    offset_seconds: int = 0,
    previous_observation_id: str | None = None,
    changed_fields: tuple[str, ...] = (),
) -> ProspectiveRegistryObservation:
    return ProspectiveRegistryObservation(
        observation_clock=_clock(offset_seconds),
        content_kind="INSTRUMENT",
        content_version_id=content.content_version_id,
        previous_observation_id=previous_observation_id,
        changed_fields=changed_fields,
        source_health=_health(content.response_sha256),
    )


def test_observation_clock_keeps_all_clocks_separate_and_ordered() -> None:
    clock = _clock()

    assert clock.provider_timestamp is None
    assert clock.request_started_at < clock.response_received_at
    assert clock.response_received_at < clock.research_available_at
    assert clock.research_available_at < clock.registry_committed_at

    with pytest.raises(ValidationError, match="request <= response <= available <= commit"):
        ObservationClock(
            request_started_at=BASE_TIME,
            response_received_at=BASE_TIME + timedelta(seconds=3),
            research_available_at=BASE_TIME + timedelta(seconds=2),
            registry_committed_at=BASE_TIME + timedelta(seconds=4),
        )

    with pytest.raises(ValidationError, match="provider_timestamp cannot follow"):
        ObservationClock(
            request_started_at=BASE_TIME,
            response_received_at=BASE_TIME + timedelta(seconds=1),
            provider_timestamp=BASE_TIME + timedelta(seconds=2),
            research_available_at=BASE_TIME + timedelta(seconds=3),
            registry_committed_at=BASE_TIME + timedelta(seconds=4),
        )


def test_naive_clock_is_rejected() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        ObservationClock(
            request_started_at=datetime(2026, 7, 21, 10, 15),
            response_received_at=BASE_TIME,
            research_available_at=BASE_TIME,
            registry_committed_at=BASE_TIME,
        )


def test_source_health_is_safe_and_status_consistent() -> None:
    success = _health()
    assert success.raw_error_retained is False

    with pytest.raises(ValidationError, match="HTTP 200 and a response hash"):
        SourceHealthObservation(
            status=SourceHealthStatus.SUCCESS,
            http_status=500,
            latency_milliseconds=10,
        )

    with pytest.raises(ValidationError, match="require an error fingerprint"):
        SourceHealthObservation(
            status=SourceHealthStatus.TRANSPORT_ERROR,
            latency_milliseconds=10,
        )

    failure = SourceHealthObservation(
        status=SourceHealthStatus.HTTP_ERROR,
        http_status=503,
        latency_milliseconds=10,
        error_fingerprint_sha256=SHA_C,
    )
    assert failure.response_sha256 is None
    assert failure.raw_error_retained is False


def test_instrument_content_is_deterministic_and_never_historical() -> None:
    first = _instrument_content()
    second = ProspectiveInstrumentContent(
        source_id=first.source_id,
        official_host=first.official_host,
        endpoint_path=first.endpoint_path,
        response_byte_count=first.response_byte_count,
        response_sha256=first.response_sha256,
        schema_fields=first.schema_fields,
        schema_sha256=first.schema_sha256,
        selected_fields={
            "tickSz": "0.1",
            "ctVal": "0.01",
            "ctType": "linear",
            "instId": "BTC-USDT-SWAP",
        },
        provider_time_fields={
            "contTdSwTime": "1611916860000",
            "listTime": "1573557408000",
        },
    )

    assert first.content_version_id == second.content_version_id
    assert first.historical_effective_from is None
    assert (
        first.effective_from_semantics
        == AvailabilitySemantics.FIRST_OBSERVED_NOT_PROVIDER_EFFECTIVE
    )

    with pytest.raises(ValidationError, match="historical effective_from"):
        ProspectiveInstrumentContent(
            **{
                **first.model_dump(),
                "historical_effective_from": datetime(2022, 3, 1, tzinfo=UTC),
            }
        )


def test_instrument_content_rejects_unsorted_or_empty_schema_and_raw_retention() -> None:
    base = _instrument_content().model_dump()

    with pytest.raises(ValidationError, match="sorted unique"):
        ProspectiveInstrumentContent(**{**base, "schema_fields": ("tickSz", "instId")})

    with pytest.raises(ValidationError, match="raw instrument responses"):
        ProspectiveInstrumentContent(**{**base, "raw_response_retained": True})


def test_funding_source_profile_retains_no_values_or_ordered_series() -> None:
    profile = ProspectiveFundingSourceContent(
        source_id="OKX_PUBLIC_FUNDING_RATE_HISTORY",
        official_host="www.okx.com",
        endpoint_path="/api/v5/public/funding-rate-history",
        request_fingerprint_sha256=SHA_A,
        response_byte_count=10240,
        response_sha256=SHA_B,
        schema_fields=(
            "formulaType",
            "fundingRate",
            "fundingTime",
            "instId",
            "instType",
            "method",
            "realizedRate",
        ),
        schema_sha256=SHA_C,
        row_count=100,
        unique_provider_timestamps=100,
        minimum_provider_timestamp_ms=1750000000000,
        maximum_provider_timestamp_ms=1752851200000,
        interval_seconds_counts=((28800, 99),),
    )

    assert len(profile.content_version_id) == 64
    assert profile.raw_response_retained is False
    assert profile.funding_rate_values_retained is False
    assert profile.ordered_timestamp_series_retained is False

    with pytest.raises(ValidationError, match="must not retain raw funding data"):
        ProspectiveFundingSourceContent(
            **{**profile.model_dump(), "funding_rate_values_retained": True}
        )


def test_diff_selected_fields_detects_value_presence_and_removal() -> None:
    assert diff_selected_fields(
        {"a": "1", "b": "2"},
        {"a": "1", "b": "3", "c": "4"},
    ) == ("b", "c")
    assert diff_selected_fields({"a": "1", "b": "2"}, {"a": "1"}) == ("b",)
    assert diff_selected_fields({"a": "1"}, {"a": "1"}) == ()


def test_append_registry_is_immutable_monotonic_and_content_aware() -> None:
    first_content = _instrument_content()
    first = _observation(first_content)
    initial = append_observation([], first)

    assert initial.observations == (first,)
    assert initial.content_version_changed is True

    repeated = _observation(
        first_content,
        offset_seconds=10,
        previous_observation_id=first.observation_id,
    )
    second = append_observation(initial.observations, repeated)
    assert second.content_version_changed is False

    changed_content = _instrument_content(response_sha256=SHA_C, tick_size="0.01")
    changed = _observation(
        changed_content,
        offset_seconds=20,
        previous_observation_id=repeated.observation_id,
        changed_fields=("tickSz",),
    )
    third = append_observation(second.observations, changed)
    assert third.content_version_changed is True
    assert len(third.observations) == 3


def test_append_registry_rejects_duplicates_wrong_tail_and_false_diffs() -> None:
    content = _instrument_content()
    first = _observation(content)
    existing = append_observation([], first).observations

    with pytest.raises(OKXProspectiveRegistryError, match="already exists"):
        append_observation(existing, first)

    wrong_tail = _observation(
        content,
        offset_seconds=10,
        previous_observation_id=SHA_B,
    )
    with pytest.raises(OKXProspectiveRegistryError, match="registry tail"):
        append_observation(existing, wrong_tail)

    false_diff = _observation(
        content,
        offset_seconds=10,
        previous_observation_id=first.observation_id,
        changed_fields=("tickSz",),
    )
    with pytest.raises(OKXProspectiveRegistryError, match="unchanged content"):
        append_observation(existing, false_diff)

    changed_content = _instrument_content(response_sha256=SHA_C, tick_size="0.01")
    missing_diff = _observation(
        changed_content,
        offset_seconds=10,
        previous_observation_id=first.observation_id,
    )
    with pytest.raises(OKXProspectiveRegistryError, match="non-empty field diff"):
        append_observation(existing, missing_diff)


def test_append_registry_rejects_nonmonotonic_commit_time() -> None:
    content = _instrument_content()
    first = _observation(content, offset_seconds=10)
    existing = append_observation([], first).observations
    earlier = _observation(
        content,
        offset_seconds=0,
        previous_observation_id=first.observation_id,
    )

    with pytest.raises(OKXProspectiveRegistryError, match="increase monotonically"):
        append_observation(existing, earlier)


def test_observation_rejects_backfill_and_any_economic_authorization() -> None:
    content = _instrument_content()
    base = _observation(content).model_dump()

    with pytest.raises(ValidationError, match="cannot backfill"):
        ProspectiveRegistryObservation(**{**base, "historical_backfill": True})

    with pytest.raises(ValidationError, match="cannot authorize economic testing"):
        ProspectiveRegistryObservation(**{**base, "returns_computation_authorized": True})
