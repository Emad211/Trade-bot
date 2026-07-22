from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from hybrid_trader.replication.okx_source_health import (
    RATE_LIMIT_CODE,
    BatchDecision,
    BookAction,
    BookMessage,
    RestObservation,
    SourceHealthError,
    SourceHealthPolicy,
    SourceHealthState,
    admit_sampling_batch,
    build_incident_record,
    evaluate_book_message,
    evaluate_rest_observation,
    evaluate_websocket_silence,
    safe_incident_json,
)

BASE = datetime(2026, 7, 21, 15, 0, tzinfo=UTC)
SOURCE_A = "OKX_SPOT_BTC_USDT_TICKER"
SOURCE_B = "OKX_SWAP_BTC_USDT_SWAP_TICKER"
SHA_A = hashlib.sha256(b"a").hexdigest()
SHA_B = hashlib.sha256(b"b").hexdigest()
SHA_C = hashlib.sha256(b"c").hexdigest()
SHA_D = hashlib.sha256(b"d").hexdigest()


def _policy(**changes: object) -> SourceHealthPolicy:
    values: dict[str, object] = {
        "policy_id": "OKX_SOURCE_HEALTH_POLICY_V1",
        "maximum_provider_age_ms": 2_000,
        "maximum_future_clock_skew_ms": 500,
        "maximum_response_to_research_delay_ms": 1_000,
        "maximum_websocket_silence_seconds": 20.0,
        "maximum_cross_source_provider_time_skew_ms": 1_500,
        "required_source_ids": tuple(sorted((SOURCE_A, SOURCE_B))),
        "expected_schema_sha256": {SOURCE_A: SHA_A, SOURCE_B: SHA_B},
        "expected_identity_sha256": {SOURCE_A: SHA_C, SOURCE_B: SHA_D},
        "checksum_deprecation_effective_at": datetime(2026, 6, 23, tzinfo=UTC),
        "sequence_validation_mode": "SEQ_ID_PREV_SEQ_ID",
        "rate_limit_backoff_policy_id": "OKX_RATE_LIMIT_BACKOFF_V1",
    }
    values.update(changes)
    return SourceHealthPolicy(**values)  # type: ignore[arg-type]


def _observation(
    source_id: str = SOURCE_A,
    *,
    provider_offset_ms: int = -200,
    response_offset_ms: int = 0,
    research_offset_ms: int = 100,
    request_offset_ms: int = -100,
    http_status: int = 200,
    provider_code: str = "0",
    row_count: int = 1,
    schema_sha: str | None = None,
    identity_sha: str | None = None,
    transport_error: str | None = None,
) -> RestObservation:
    policy = _policy()
    return RestObservation(
        source_id=source_id,
        request_started_at=BASE + timedelta(milliseconds=request_offset_ms),
        response_received_at=BASE + timedelta(milliseconds=response_offset_ms),
        provider_timestamp=BASE + timedelta(milliseconds=provider_offset_ms),
        research_available_at=BASE + timedelta(milliseconds=research_offset_ms),
        http_status=http_status,
        provider_code=provider_code,
        row_count=row_count,
        response_sha256=hashlib.sha256(f"response-{source_id}".encode()).hexdigest(),
        schema_sha256=schema_sha or policy.expected_schema_sha256[source_id],
        identity_sha256=identity_sha or policy.expected_identity_sha256[source_id],
        transport_error_fingerprint_sha256=transport_error,
    )


def _book(
    *,
    action: BookAction = BookAction.UPDATE,
    seq_id: int = 11,
    prev_seq_id: int = 10,
    asks_count: int = 1,
    bids_count: int = 1,
    checksum: int | None = 0,
    provider_time: datetime = BASE,
    notice_code: str | None = None,
) -> BookMessage:
    return BookMessage(
        channel="books",
        instrument_id="BTC-USDT",
        action=action,
        seq_id=seq_id,
        prev_seq_id=prev_seq_id,
        asks_count=asks_count,
        bids_count=bids_count,
        provider_timestamp=provider_time,
        received_at=provider_time + timedelta(milliseconds=100),
        checksum=checksum,
        notice_code=notice_code,
    )


def test_policy_requires_explicit_valid_thresholds_and_fingerprints() -> None:
    policy = _policy()
    policy.validate()
    assert len(policy.policy_fingerprint_sha256) == 64

    with pytest.raises(SourceHealthError, match="below 30"):
        _policy(maximum_websocket_silence_seconds=30.0).validate()
    with pytest.raises(SourceHealthError, match="sorted"):
        _policy(required_source_ids=(SOURCE_B, SOURCE_A)).validate()
    with pytest.raises(SourceHealthError, match="schema fingerprints"):
        _policy(expected_schema_sha256={SOURCE_A: SHA_A}).validate()


def test_healthy_rest_observation_is_admitted_without_raw_values() -> None:
    result = evaluate_rest_observation(_observation(), policy=_policy())
    assert result.state is SourceHealthState.HEALTHY
    assert result.admitted is True
    assert result.raw_response_retained is False
    assert result.market_values_retained is False
    assert result.carry_forward_used is False
    assert result.interpolation_used is False


def test_rest_clock_stale_future_and_research_delay_states_are_explicit() -> None:
    policy = _policy()
    assert (
        evaluate_rest_observation(_observation(provider_offset_ms=-2_001), policy=policy).state
        is SourceHealthState.STALE_PROVIDER_TIME
    )
    assert (
        evaluate_rest_observation(_observation(provider_offset_ms=501), policy=policy).state
        is SourceHealthState.FUTURE_PROVIDER_TIME
    )
    assert (
        evaluate_rest_observation(_observation(research_offset_ms=1_001), policy=policy).state
        is SourceHealthState.RESEARCH_DELAY_EXCEEDED
    )
    assert (
        evaluate_rest_observation(_observation(request_offset_ms=100), policy=policy).state
        is SourceHealthState.CLOCK_INVALID
    )


def test_rate_limit_http_transport_provider_and_empty_fail_closed() -> None:
    policy = _policy()
    assert (
        evaluate_rest_observation(_observation(provider_code=RATE_LIMIT_CODE), policy=policy).state
        is SourceHealthState.RATE_LIMITED
    )
    assert (
        evaluate_rest_observation(_observation(http_status=503), policy=policy).state
        is SourceHealthState.HTTP_ERROR
    )
    assert (
        evaluate_rest_observation(_observation(transport_error=SHA_A), policy=policy).state
        is SourceHealthState.TRANSPORT_ERROR
    )
    assert (
        evaluate_rest_observation(_observation(provider_code="51000"), policy=policy).state
        is SourceHealthState.PROVIDER_ERROR
    )
    assert (
        evaluate_rest_observation(_observation(row_count=0), policy=policy).state
        is SourceHealthState.EMPTY_RESPONSE
    )


def test_schema_and_identity_drift_require_quarantine() -> None:
    policy = _policy()
    schema = evaluate_rest_observation(_observation(schema_sha=SHA_D), policy=policy)
    identity = evaluate_rest_observation(_observation(identity_sha=SHA_A), policy=policy)
    assert schema.state is SourceHealthState.SCHEMA_CHANGED
    assert identity.state is SourceHealthState.IDENTITY_CHANGED
    assert schema.quarantine_required and identity.quarantine_required


def test_snapshot_and_incremental_sequence_continuity() -> None:
    policy = _policy()
    snapshot = evaluate_book_message(
        _book(action=BookAction.SNAPSHOT, seq_id=10, prev_seq_id=-1),
        previous_sequence_id=None,
        policy=policy,
    )
    update = evaluate_book_message(_book(), previous_sequence_id=10, policy=policy)
    assert snapshot.state is SourceHealthState.HEALTHY
    assert snapshot.next_sequence_id == 10
    assert update.state is SourceHealthState.HEALTHY
    assert update.next_sequence_id == 11
    assert update.sequence_authoritative is True


def test_empty_unchanged_sequence_is_heartbeat_not_book_update() -> None:
    result = evaluate_book_message(
        _book(seq_id=10, prev_seq_id=10, asks_count=0, bids_count=0),
        previous_sequence_id=10,
        policy=_policy(),
    )
    assert result.state is SourceHealthState.HEARTBEAT_NO_BOOK_CHANGE
    assert result.stream_live is True
    assert result.admitted_as_new_book_data is False
    assert result.next_sequence_id == 10


def test_sequence_gap_and_regression_require_reconnect() -> None:
    gap = evaluate_book_message(
        _book(seq_id=12, prev_seq_id=9), previous_sequence_id=10, policy=_policy()
    )
    regression = evaluate_book_message(
        _book(seq_id=9, prev_seq_id=10), previous_sequence_id=10, policy=_policy()
    )
    assert gap.state is SourceHealthState.SEQUENCE_GAP
    assert regression.state is SourceHealthState.SEQUENCE_REGRESSION
    assert gap.reconnect_required and regression.reconnect_required


def test_checksum_zero_is_ignored_after_deprecation_and_sequence_wins() -> None:
    valid = evaluate_book_message(_book(checksum=0), previous_sequence_id=10, policy=_policy())
    invalid_sequence = evaluate_book_message(
        _book(prev_seq_id=8, checksum=12345),
        previous_sequence_id=10,
        policy=_policy(),
    )
    assert valid.checksum_deprecated is True
    assert valid.checksum_used_for_integrity is False
    assert invalid_sequence.state is SourceHealthState.SEQUENCE_GAP


def test_pre_deprecation_message_fails_policy_version_closed() -> None:
    result = evaluate_book_message(
        _book(provider_time=datetime(2026, 6, 22, tzinfo=UTC)),
        previous_sequence_id=10,
        policy=_policy(),
    )
    assert result.state is SourceHealthState.POLICY_VERSION_MISMATCH
    assert result.reconnect_required is True


def test_upgrade_notice_and_silence_require_reconnect() -> None:
    notice = evaluate_book_message(
        _book(action=BookAction.NOTICE, notice_code="64008"),
        previous_sequence_id=10,
        policy=_policy(),
    )
    silent = evaluate_websocket_silence(
        last_message_at=BASE,
        observed_at=BASE + timedelta(seconds=21),
        policy=_policy(),
    )
    healthy = evaluate_websocket_silence(
        last_message_at=BASE,
        observed_at=BASE + timedelta(seconds=10),
        policy=_policy(),
    )
    assert notice.state is SourceHealthState.SERVICE_UPGRADE_DRAIN
    assert silent.state is SourceHealthState.CONNECTION_SILENT
    assert healthy.state is SourceHealthState.HEALTHY
    assert notice.reconnect_required and silent.reconnect_required


def test_batch_admission_requires_exact_healthy_sources() -> None:
    policy = _policy()
    results = (
        evaluate_rest_observation(_observation(SOURCE_A), policy=policy),
        evaluate_rest_observation(_observation(SOURCE_B), policy=policy),
    )
    admitted = admit_sampling_batch(results, policy=policy)
    partial = admit_sampling_batch(results[:1], policy=policy)
    duplicate = admit_sampling_batch((results[0], results[0]), policy=policy)
    assert admitted.decision is BatchDecision.ADMIT_PRIVATE_BATCH
    assert partial.state is SourceHealthState.PARTIAL_SOURCE_SET
    assert duplicate.state is SourceHealthState.DUPLICATE_SOURCE


def test_batch_quarantines_drift_and_rejects_unhealthy_source() -> None:
    policy = _policy()
    healthy_b = evaluate_rest_observation(_observation(SOURCE_B), policy=policy)
    drift = evaluate_rest_observation(_observation(SOURCE_A, schema_sha=SHA_D), policy=policy)
    stale = evaluate_rest_observation(
        _observation(SOURCE_A, provider_offset_ms=-2_001), policy=policy
    )
    assert (
        admit_sampling_batch((drift, healthy_b), policy=policy).decision
        is BatchDecision.QUARANTINE_INCIDENT
    )
    rejected = admit_sampling_batch((stale, healthy_b), policy=policy)
    assert rejected.decision is BatchDecision.REJECT_BATCH
    assert rejected.state is SourceHealthState.STALE_PROVIDER_TIME


def test_cross_source_skew_rejects_but_nonmonotonic_within_policy_is_diagnostic() -> None:
    policy = _policy()
    too_wide = (
        evaluate_rest_observation(_observation(SOURCE_A, provider_offset_ms=-1_900), policy=policy),
        evaluate_rest_observation(_observation(SOURCE_B, provider_offset_ms=-100), policy=policy),
    )
    rejected = admit_sampling_batch(too_wide, policy=policy)
    assert rejected.state is SourceHealthState.CROSS_SOURCE_SKEW_EXCEEDED

    nonmonotonic = (
        evaluate_rest_observation(_observation(SOURCE_A, provider_offset_ms=-100), policy=policy),
        evaluate_rest_observation(_observation(SOURCE_B, provider_offset_ms=-200), policy=policy),
    )
    admitted = admit_sampling_batch(nonmonotonic, policy=policy)
    assert admitted.decision is BatchDecision.ADMIT_PRIVATE_BATCH
    assert admitted.provider_timestamps_monotonic_in_input_order is False


def test_incident_record_is_content_addressed_and_contains_no_market_payload() -> None:
    record = build_incident_record(
        source_id=SOURCE_A,
        state=SourceHealthState.RATE_LIMITED,
        policy=_policy(),
        observed_at=BASE,
        response_sha256=SHA_A,
        schema_sha256=SHA_B,
        identity_sha256=SHA_C,
        error_fingerprint_sha256=SHA_D,
    )
    payload = json.loads(safe_incident_json(record))
    assert len(record.incident_id) == 64
    assert payload["raw_payload_retained"] is False
    assert payload["market_values_retained"] is False
    assert payload["price_null_created"] is False
    assert payload["carry_forward_used"] is False
    assert payload["interpolation_used"] is False
    forbidden = {"price", "size", "bid", "ask", "markPx", "idxPx"}
    assert forbidden.isdisjoint(payload)


def test_result_flags_never_enable_carry_forward_interpolation_or_calculation() -> None:
    policy = _policy()
    healthy = evaluate_rest_observation(_observation(SOURCE_A), policy=policy)
    unhealthy = replace(healthy, admitted=False, state=SourceHealthState.RATE_LIMITED)
    result = admit_sampling_batch(
        (
            unhealthy,
            evaluate_rest_observation(_observation(SOURCE_B), policy=policy),
        ),
        policy=policy,
    )
    assert result.carry_forward_used is False
    assert result.interpolation_used is False
    assert result.rejected_data_retained is False
    assert result.numerical_calculation_authorized is False
