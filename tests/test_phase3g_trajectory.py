from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from hybrid_trader.data.snapshot import canonical_json_sha256
from hybrid_trader.phase3g_market import Phase3GMarketManifest
from hybrid_trader.phase3g_trajectory import (
    append_phase3g_trajectory,
    make_phase3g_trajectory_entry,
    verify_phase3g_trajectory,
)
from hybrid_trader.semantic_dataset import (
    SemanticDatasetManifest,
    SemanticMaturityAssessment,
    SemanticMaturityPolicy,
)
from hybrid_trader.semantic_features import SemanticFeatureSpec


def _market(*, as_of: datetime, snapshot_sha: str = "a" * 64) -> Phase3GMarketManifest:
    return Phase3GMarketManifest(
        run_id="b" * 64,
        as_of=as_of,
        window_start=as_of - timedelta(days=120),
        window_end=as_of,
        source_commit_sha="c" * 40,
        spec_sha256="d" * 64,
        primary_source="venue-a",
        successful_spot_sources=("venue-a", "venue-b"),
        combined_snapshot_sha256=snapshot_sha,
        source_attempts=(),
        bar_quality=(),
        cross_venue_quality=(),
        created_at=as_of,
    )


def _dataset(
    *,
    as_of: datetime,
    content_sha: str,
    snapshot_sha: str = "a" * 64,
    active_rows: int = 2,
) -> SemanticDatasetManifest:
    feature_spec = SemanticFeatureSpec(windows_hours=(4,), allowed_assets=("BTC",))
    maturity = SemanticMaturityAssessment(
        assessment_id="e" * 64,
        status="insufficient_prospective_sample",
        research_model_fitting_allowed=False,
        policy=SemanticMaturityPolicy(),
        relevant_semantic_record_count=8,
        unique_availability_date_count=2,
        unique_source_count=1,
        active_decision_row_count=active_rows,
        matured_labeled_row_count=10,
        positive_target_count=6,
        negative_target_count=4,
        failure_reasons=("insufficient_semantic_records",),
    )
    return SemanticDatasetManifest(
        dataset_id=f"semantic-{content_sha[:12]}",
        content_sha256=content_sha,
        market_snapshot_sha256=snapshot_sha,
        document_ledger_head_sha256="f" * 64,
        semantic_ledger_head_sha256="1" * 64,
        semantic_record_count=8,
        relevant_semantic_record_count=8,
        as_of=as_of,
        feature_spec=feature_spec,
        feature_spec_sha256=canonical_json_sha256(feature_spec.model_dump(mode="json")),
        source_commit_sha="c" * 40,
        row_count=10,
        candidate_row_count=10,
        excluded_unmatured_label_count=0,
        market_feature_columns=("market_feature",),
        semantic_feature_columns=("semantic_4h_event_count",),
        index_start=as_of - timedelta(days=2),
        index_end=as_of - timedelta(hours=8),
        decision_start=as_of - timedelta(days=2),
        decision_end=as_of - timedelta(hours=8),
        label_availability_end=as_of - timedelta(hours=4),
        maturity=maturity,
        created_at=as_of,
    )


def test_phase3g_trajectory_appends_and_verifies_chain(tmp_path: Path) -> None:
    first_time = datetime(2026, 7, 18, 8, tzinfo=UTC)
    first = make_phase3g_trajectory_entry(
        _market(as_of=first_time),
        _dataset(as_of=first_time, content_sha="2" * 64),
        recorded_at=first_time,
    )
    ledger = tmp_path / "trajectory.jsonl"
    first_state = append_phase3g_trajectory(ledger, first)
    assert first_state.count == 1
    assert first_state.head_sha256 == first.entry_id

    second_time = first_time + timedelta(days=7)
    second = make_phase3g_trajectory_entry(
        _market(as_of=second_time, snapshot_sha="3" * 64),
        _dataset(
            as_of=second_time,
            content_sha="4" * 64,
            snapshot_sha="3" * 64,
            active_rows=8,
        ),
        recorded_at=second_time,
        previous_entry_sha256=first.entry_id,
    )
    second_state = append_phase3g_trajectory(ledger, second)
    assert second_state.count == 2
    assert second_state.head_sha256 == second.entry_id
    assert second_state.last_as_of == second_time
    assert second_state.dataset_ids == frozenset({first.dataset_id, second.dataset_id})


def test_phase3g_trajectory_rejects_mismatched_inputs() -> None:
    as_of = datetime(2026, 7, 18, 8, tzinfo=UTC)
    with pytest.raises(ValueError, match="snapshot hashes disagree"):
        make_phase3g_trajectory_entry(
            _market(as_of=as_of, snapshot_sha="a" * 64),
            _dataset(
                as_of=as_of,
                content_sha="2" * 64,
                snapshot_sha="b" * 64,
            ),
            recorded_at=as_of,
        )

    dataset = _dataset(as_of=as_of, content_sha="2" * 64)
    changed = dataset.model_copy(update={"source_commit_sha": "9" * 40})
    with pytest.raises(ValueError, match="source commits disagree"):
        make_phase3g_trajectory_entry(
            _market(as_of=as_of),
            changed,
            recorded_at=as_of,
        )


def test_phase3g_trajectory_rejects_duplicates_and_nonadvancing_time(
    tmp_path: Path,
) -> None:
    as_of = datetime(2026, 7, 18, 8, tzinfo=UTC)
    entry = make_phase3g_trajectory_entry(
        _market(as_of=as_of),
        _dataset(as_of=as_of, content_sha="2" * 64),
        recorded_at=as_of,
    )
    ledger = tmp_path / "trajectory.jsonl"
    append_phase3g_trajectory(ledger, entry)

    with pytest.raises(ValueError, match="current ledger head"):
        append_phase3g_trajectory(ledger, entry)

    duplicate = make_phase3g_trajectory_entry(
        _market(as_of=as_of + timedelta(days=1)),
        _dataset(as_of=as_of + timedelta(days=1), content_sha="2" * 64),
        recorded_at=as_of + timedelta(days=1),
        previous_entry_sha256=entry.entry_id,
    )
    with pytest.raises(ValueError, match="already present"):
        append_phase3g_trajectory(ledger, duplicate)

    nonadvancing = make_phase3g_trajectory_entry(
        _market(as_of=as_of, snapshot_sha="3" * 64),
        _dataset(
            as_of=as_of,
            content_sha="4" * 64,
            snapshot_sha="3" * 64,
        ),
        recorded_at=as_of + timedelta(hours=1),
        previous_entry_sha256=entry.entry_id,
    )
    with pytest.raises(ValueError, match="must advance"):
        append_phase3g_trajectory(ledger, nonadvancing)


def test_phase3g_trajectory_detects_tampering(tmp_path: Path) -> None:
    as_of = datetime(2026, 7, 18, 8, tzinfo=UTC)
    entry = make_phase3g_trajectory_entry(
        _market(as_of=as_of),
        _dataset(as_of=as_of, content_sha="2" * 64),
        recorded_at=as_of,
    )
    ledger = tmp_path / "trajectory.jsonl"
    append_phase3g_trajectory(ledger, entry)
    payload = json.loads(ledger.read_text())
    payload["active_decision_row_count"] = 999
    ledger.write_text(json.dumps(payload) + "\n")
    with pytest.raises(ValueError, match="entry ID is not self-consistent"):
        verify_phase3g_trajectory(ledger)
