from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from hybrid_trader.phase3i_lineage import (
    SemanticStateCandidate,
    make_semantic_state_candidate,
    select_semantic_state,
)


def _candidate(
    workflow_name: str,
    run_id: int,
    *,
    created_at: datetime,
    artifact_created_at: datetime | None = None,
    expired: bool = False,
) -> SemanticStateCandidate:
    return make_semantic_state_candidate(
        workflow_name=workflow_name,  # type: ignore[arg-type]
        workflow_run_id=str(run_id),
        run_created_at=created_at,
        run_completed_at=created_at + timedelta(minutes=5),
        source_commit_sha=f"{run_id % 16:x}" * 40,
        artifact_id=run_id + 100,
        artifact_name=f"{workflow_name}-{run_id}",
        artifact_digest=f"sha256:{run_id % 16:x}" * 0 + "sha256:" + f"{run_id % 16:x}" * 64,
        artifact_created_at=artifact_created_at or created_at + timedelta(minutes=6),
        artifact_expired=expired,
    )


def test_newest_semantic_state_artifact_is_selected() -> None:
    start = datetime(2026, 7, 18, 8, tzinfo=UTC)
    phase3e = _candidate("phase3e-longitudinal-events", 10, created_at=start)
    phase3h = _candidate(
        "phase3h-avalai-pilot",
        11,
        created_at=start + timedelta(hours=1),
    )
    selection = select_semantic_state(
        [phase3e, phase3h],
        selected_at=start + timedelta(hours=2),
    )
    assert selection.selected_candidate == phase3h
    assert selection.considered_candidate_ids == tuple(
        sorted((phase3e.candidate_id, phase3h.candidate_id))
    )
    assert selection.rejected_candidate_ids == (phase3e.candidate_id,)


def test_phase3h_wins_an_exact_time_tie_by_frozen_priority() -> None:
    observed = datetime(2026, 7, 18, 8, tzinfo=UTC)
    phase3e = _candidate("phase3e-longitudinal-events", 20, created_at=observed)
    phase3h = _candidate("phase3h-avalai-pilot", 19, created_at=observed)
    selection = select_semantic_state(
        [phase3e, phase3h],
        selected_at=observed + timedelta(hours=1),
    )
    assert selection.selected_candidate.workflow_name == "phase3h-avalai-pilot"


def test_expired_and_stale_artifacts_are_not_eligible() -> None:
    observed = datetime(2026, 7, 18, 8, tzinfo=UTC)
    expired = _candidate(
        "phase3h-avalai-pilot",
        30,
        created_at=observed + timedelta(hours=2),
        expired=True,
    )
    old = _candidate("phase3e-longitudinal-events", 29, created_at=observed)
    selection = select_semantic_state(
        [old, expired],
        selected_at=observed + timedelta(hours=3),
    )
    assert selection.selected_candidate == old

    with pytest.raises(ValueError, match="No eligible semantic state"):
        select_semantic_state(
            [old, expired],
            selected_at=observed + timedelta(hours=3),
            minimum_artifact_created_at=observed + timedelta(hours=1),
        )


def test_candidate_identity_tampering_is_rejected() -> None:
    observed = datetime(2026, 7, 18, 8, tzinfo=UTC)
    candidate = _candidate("phase3h-avalai-pilot", 40, created_at=observed)
    payload = candidate.model_dump(mode="json")
    payload["artifact_id"] = 999
    with pytest.raises(ValueError, match="candidate ID"):
        SemanticStateCandidate.model_validate(payload)
