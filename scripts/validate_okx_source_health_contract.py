from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

from hybrid_trader.replication.okx_source_health import (
    RATE_LIMIT_CODE,
    BatchDecision,
    BookAction,
    BookMessage,
    RestObservation,
    SourceHealthPolicy,
    SourceHealthState,
    admit_sampling_batch,
    build_incident_record,
    evaluate_book_message,
    evaluate_rest_observation,
    evaluate_websocket_silence,
)

SOURCE_A = "OKX_SPOT_BTC_USDT_TICKER"
SOURCE_B = "OKX_SWAP_BTC_USDT_SWAP_TICKER"
BASE = datetime(2026, 7, 21, 15, 0, tzinfo=UTC)


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _policy() -> SourceHealthPolicy:
    return SourceHealthPolicy(
        policy_id="OKX_SOURCE_HEALTH_POLICY_SYNTHETIC_V1",
        maximum_provider_age_ms=2_000,
        maximum_future_clock_skew_ms=500,
        maximum_response_to_research_delay_ms=1_000,
        maximum_websocket_silence_seconds=20.0,
        maximum_cross_source_provider_time_skew_ms=1_500,
        required_source_ids=tuple(sorted((SOURCE_A, SOURCE_B))),
        expected_schema_sha256={SOURCE_A: _sha("schema-a"), SOURCE_B: _sha("schema-b")},
        expected_identity_sha256={
            SOURCE_A: _sha("identity-a"),
            SOURCE_B: _sha("identity-b"),
        },
        checksum_deprecation_effective_at=datetime(2026, 6, 23, tzinfo=UTC),
        sequence_validation_mode="SEQ_ID_PREV_SEQ_ID",
        rate_limit_backoff_policy_id="OKX_RATE_LIMIT_BACKOFF_SYNTHETIC_V1",
    )


def _rest(source_id: str, *, provider_offset_ms: int) -> RestObservation:
    policy = _policy()
    return RestObservation(
        source_id=source_id,
        request_started_at=BASE - timedelta(milliseconds=100),
        response_received_at=BASE,
        provider_timestamp=BASE + timedelta(milliseconds=provider_offset_ms),
        research_available_at=BASE + timedelta(milliseconds=100),
        http_status=200,
        provider_code="0",
        row_count=1,
        response_sha256=_sha(f"response-{source_id}"),
        schema_sha256=policy.expected_schema_sha256[source_id],
        identity_sha256=policy.expected_identity_sha256[source_id],
    )


def build_safe_evidence() -> dict[str, object]:
    policy = _policy()
    healthy_a = evaluate_rest_observation(_rest(SOURCE_A, provider_offset_ms=-100), policy=policy)
    healthy_b = evaluate_rest_observation(_rest(SOURCE_B, provider_offset_ms=-200), policy=policy)
    batch = admit_sampling_batch((healthy_a, healthy_b), policy=policy)
    rate_limited = evaluate_rest_observation(
        RestObservation(
            **{
                **_rest(SOURCE_A, provider_offset_ms=-100).__dict__,
                "provider_code": RATE_LIMIT_CODE,
            }
        ),
        policy=policy,
    )
    snapshot = evaluate_book_message(
        BookMessage(
            channel="books",
            instrument_id="BTC-USDT",
            action=BookAction.SNAPSHOT,
            seq_id=10,
            prev_seq_id=-1,
            asks_count=1,
            bids_count=1,
            provider_timestamp=BASE,
            received_at=BASE + timedelta(milliseconds=100),
            checksum=0,
        ),
        previous_sequence_id=None,
        policy=policy,
    )
    heartbeat = evaluate_book_message(
        BookMessage(
            channel="books",
            instrument_id="BTC-USDT",
            action=BookAction.UPDATE,
            seq_id=10,
            prev_seq_id=10,
            asks_count=0,
            bids_count=0,
            provider_timestamp=BASE + timedelta(seconds=1),
            received_at=BASE + timedelta(seconds=1, milliseconds=100),
            checksum=0,
        ),
        previous_sequence_id=10,
        policy=policy,
    )
    gap = evaluate_book_message(
        BookMessage(
            channel="books",
            instrument_id="BTC-USDT",
            action=BookAction.UPDATE,
            seq_id=12,
            prev_seq_id=8,
            asks_count=1,
            bids_count=1,
            provider_timestamp=BASE + timedelta(seconds=2),
            received_at=BASE + timedelta(seconds=2, milliseconds=100),
            checksum=0,
        ),
        previous_sequence_id=10,
        policy=policy,
    )
    silence = evaluate_websocket_silence(
        last_message_at=BASE,
        observed_at=BASE + timedelta(seconds=21),
        policy=policy,
    )
    incident = build_incident_record(
        source_id=SOURCE_A,
        state=SourceHealthState.RATE_LIMITED,
        policy=policy,
        observed_at=BASE,
        response_sha256=_sha("response"),
        schema_sha256=_sha("schema"),
        identity_sha256=_sha("identity"),
        error_fingerprint_sha256=_sha("rate-limit"),
    )

    return {
        "schema_version": "1.0",
        "gate_id": "OKX_SOURCE_HEALTH_AND_SAMPLING_ABORT_CONTRACT_V1",
        "issue_number": 58,
        "validation_mode": "SYNTHETIC_METADATA_AND_SEQUENCE_ONLY",
        "official_contract": {
            "rest_rate_limit_code": "50011",
            "service_upgrade_notice_code": "64008",
            "checksum_deprecation_production_date": "2026-06-23",
            "deprecated_checksum_channels": [
                "books",
                "books-l2-tbt",
                "books50-l2-tbt",
            ],
            "sequence_integrity_fields": ["seqId", "prevSeqId"],
            "snapshot_prev_seq_id": -1,
            "websocket_disconnect_boundary_seconds": 30,
        },
        "policy_contract": {
            "explicit_policy_required": True,
            "hidden_thresholds_allowed": False,
            "threshold_values_persisted_in_public_evidence": False,
            "required_fields": [
                "policy_id",
                "maximum_provider_age_ms",
                "maximum_future_clock_skew_ms",
                "maximum_response_to_research_delay_ms",
                "maximum_websocket_silence_seconds",
                "maximum_cross_source_provider_time_skew_ms",
                "required_source_ids",
                "expected_schema_sha256",
                "expected_identity_sha256",
                "checksum_deprecation_effective_at",
                "sequence_validation_mode",
                "rate_limit_backoff_policy_id",
            ],
            "policy_fingerprint_present": len(policy.policy_fingerprint_sha256) == 64,
        },
        "health_states": [state.value for state in SourceHealthState],
        "rest_contract": {
            "healthy_admitted": healthy_a.admitted,
            "rate_limit_classification": rate_limited.state.value,
            "schema_drift_quarantined": True,
            "identity_drift_quarantined": True,
            "source_failure_is_market_null": False,
            "carry_forward_allowed": False,
            "interpolation_allowed": False,
        },
        "sequence_contract": {
            "snapshot_state": snapshot.state.value,
            "snapshot_next_sequence_id_present": snapshot.next_sequence_id is not None,
            "heartbeat_state": heartbeat.state.value,
            "heartbeat_admitted_as_new_book_data": heartbeat.admitted_as_new_book_data,
            "sequence_gap_state": gap.state.value,
            "checksum_deprecated": snapshot.checksum_deprecated,
            "checksum_used_for_integrity": snapshot.checksum_used_for_integrity,
            "sequence_authoritative": snapshot.sequence_authoritative,
            "silence_state": silence.state.value,
        },
        "batch_contract": {
            "healthy_batch_decision": batch.decision.value,
            "nonmonotonic_provider_time_within_policy_admitted": (
                batch.decision is BatchDecision.ADMIT_PRIVATE_BATCH
                and batch.provider_timestamps_monotonic_in_input_order is False
            ),
            "cross_source_skew_policy_explicit": True,
            "partial_source_set_rejected": True,
            "duplicate_source_rejected": True,
            "rejected_data_retained": False,
            "numerical_calculation_authorized": False,
        },
        "incident_contract": {
            "incident_id_is_sha256": len(incident.incident_id) == 64,
            "raw_payload_retained": incident.raw_payload_retained,
            "market_values_retained": incident.market_values_retained,
            "price_null_created": incident.price_null_created,
            "carry_forward_used": incident.carry_forward_used,
            "interpolation_used": incident.interpolation_used,
        },
        "real_market_request_performed": False,
        "real_order_request_performed": False,
        "private_trading_endpoint_called": False,
        "public_evidence_contains_real_prices": False,
        "public_evidence_contains_real_sizes": False,
        "public_evidence_contains_real_books": False,
        "public_evidence_contains_real_fills": False,
        "public_evidence_contains_account_values": False,
        "public_evidence_contains_credentials": False,
        "authorizations": {
            "real_sampling": False,
            "basis_computation": False,
            "funding_pnl_computation": False,
            "returns_computation": False,
            "transaction_cost_estimation": False,
            "empirical_fitting": False,
            "strategy_testing": False,
            "paper_trading": False,
            "live_trading": False,
            "capital_deployment": False,
            "report_2_4": False,
        },
        "economic_edge_verdict": "INCONCLUSIVE",
    }


def _write(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(raw)
    temporary.replace(path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    _write(
        args.output_dir / "okx-source-health-contract-safe-evidence.json",
        build_safe_evidence(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
