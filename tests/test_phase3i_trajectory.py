from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from hybrid_trader.event_capture_state import canonical_sha256
from hybrid_trader.phase3g_trajectory import (
    Phase3GTrajectoryEntry,
    trajectory_identity_payload,
)
from hybrid_trader.phase3i_health import (
    Phase3ISourceHealthAssessment,
    Phase3ISourceHealthPolicy,
    Phase3ISourceHealthRecord,
    health_identity_payload,
)
from hybrid_trader.phase3i_lineage import (
    make_semantic_state_candidate,
    select_semantic_state,
)
from hybrid_trader.phase3i_trajectory import (
    append_phase3i_health_trajectory,
    make_phase3i_health_trajectory_entry,
    verify_phase3i_health_trajectory,
)


def _phase3g_entry(as_of: datetime, suffix: str) -> Phase3GTrajectoryEntry:
    candidate = Phase3GTrajectoryEntry.model_construct(
        entry_id="0" * 64,
        schema_version="1.0",
        previous_entry_sha256=None,
        recorded_at=as_of,
        as_of=as_of,
        source_commit_sha=suffix * 40,
        market_run_id=suffix * 64,
        market_snapshot_sha256=("a" if suffix != "a" else "b") * 64,
        dataset_id=f"semantic-{suffix * 12}",
        dataset_content_sha256=("c" if suffix != "c" else "d") * 64,
        semantic_ledger_head_sha256="e" * 64,
        relevant_semantic_record_count=12,
        unique_availability_date_count=3,
        unique_source_count=4,
        active_decision_row_count=5,
        matured_labeled_row_count=700,
        maturity_status="insufficient_prospective_sample",
        research_model_fitting_allowed=False,
        paper_or_live_trading_allowed=False,
        prospective_decisions_created=False,
    )
    payload = candidate.model_dump(mode="json")
    payload["entry_id"] = canonical_sha256(trajectory_identity_payload(candidate))
    return Phase3GTrajectoryEntry.model_validate(payload)


def _health(assessed_at: datetime) -> Phase3ISourceHealthAssessment:
    record = Phase3ISourceHealthRecord(
        source_id="source-a",
        latest_status="success",
        latest_required=True,
        latest_parsed_documents=1,
        latest_relevance_accepted_documents=1,
        latest_relevance_rejected_documents=0,
        document_count=1,
        semantic_record_count=1,
        pending_semantic_document_count=0,
        successful_provider_call_count=1,
        failed_provider_call_count=0,
        semantic_assets=("BTC",),
        source_metadata_variant_count=1,
        source_quality_values=(0.9,),
        asset_tag_variants=(("BTC",),),
    )
    candidate = Phase3ISourceHealthAssessment.model_construct(
        assessment_id="0" * 64,
        schema_version="1.0",
        status="pass",
        recommended_action="continue_maturity_monitoring",
        model_fitting_allowed=False,
        paper_or_live_trading_allowed=False,
        assessed_at=assessed_at,
        policy=Phase3ISourceHealthPolicy(
            minimum_document_sources=1,
            minimum_semantic_sources=1,
            minimum_semantic_assets=1,
        ),
        latest_capture_id="f" * 64,
        latest_provider_run_id="1" * 64,
        document_ledger_head_sha256="2" * 64,
        semantic_ledger_head_sha256="e" * 64,
        call_ledger_head_sha256="3" * 64,
        total_document_count=1,
        total_semantic_record_count=1,
        total_pending_semantic_document_count=0,
        total_successful_provider_call_count=1,
        total_failed_provider_call_count=0,
        document_source_count=1,
        semantic_source_count=1,
        semantic_assets=("BTC",),
        failed_required_sources=(),
        failed_optional_sources=(),
        metadata_drift_sources=(),
        zero_accepted_sources_called=(),
        source_records=(record,),
        failure_reasons=(),
    )
    payload = candidate.model_dump(mode="json")
    payload["assessment_id"] = canonical_sha256(health_identity_payload(candidate))
    return Phase3ISourceHealthAssessment.model_validate(payload)


def _selection(observed: datetime, run_id: int):
    candidate = make_semantic_state_candidate(
        workflow_name="phase3h-avalai-pilot",
        workflow_run_id=str(run_id),
        run_created_at=observed - timedelta(minutes=10),
        run_completed_at=observed - timedelta(minutes=5),
        source_commit_sha="4" * 40,
        artifact_id=run_id + 1000,
        artifact_name=f"phase3h-state-{run_id}",
        artifact_digest="sha256:" + "5" * 64,
        artifact_created_at=observed - timedelta(minutes=4),
    )
    return select_semantic_state([candidate], selected_at=observed)


def test_phase3i_health_trajectory_appends_and_verifies(tmp_path: Path) -> None:
    first_time = datetime(2026, 7, 18, 12, tzinfo=UTC)
    first = make_phase3i_health_trajectory_entry(
        _phase3g_entry(first_time, "6"),
        _selection(first_time, 10),
        _health(first_time),
        recorded_at=first_time,
    )
    state = append_phase3i_health_trajectory(tmp_path / "health.jsonl", first)
    assert state.count == 1
    assert state.head_sha256 == first.entry_id

    second_time = first_time + timedelta(hours=4)
    second = make_phase3i_health_trajectory_entry(
        _phase3g_entry(second_time, "7"),
        _selection(second_time, 11),
        _health(second_time),
        recorded_at=second_time,
        previous_entry_sha256=state.head_sha256,
    )
    state = append_phase3i_health_trajectory(tmp_path / "health.jsonl", second)
    assert state.count == 2
    assert state.head_sha256 == second.entry_id
    assert verify_phase3i_health_trajectory(tmp_path / "health.jsonl") == state


def test_phase3i_trajectory_rejects_duplicate_selection_and_tampering(tmp_path: Path) -> None:
    observed = datetime(2026, 7, 18, 12, tzinfo=UTC)
    selection = _selection(observed, 20)
    first = make_phase3i_health_trajectory_entry(
        _phase3g_entry(observed, "8"),
        selection,
        _health(observed),
        recorded_at=observed,
    )
    path = tmp_path / "health.jsonl"
    state = append_phase3i_health_trajectory(path, first)

    duplicate = make_phase3i_health_trajectory_entry(
        _phase3g_entry(observed + timedelta(hours=4), "9"),
        selection,
        _health(observed + timedelta(hours=4)),
        recorded_at=observed + timedelta(hours=4),
        previous_entry_sha256=state.head_sha256,
    )
    with pytest.raises(ValueError, match="selection is already present"):
        append_phase3i_health_trajectory(path, duplicate)

    payload = path.read_bytes().replace(b'"semantic_source_count":1', b'"semantic_source_count":2')
    path.write_bytes(payload)
    with pytest.raises(ValueError):
        verify_phase3i_health_trajectory(path)
