from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from hybrid_trader.semantic_dataset import (
    SemanticMaturityAssessment,
    SemanticMaturityPolicy,
)
from hybrid_trader.semantic_monitor import (
    append_maturity_observation,
    make_maturity_observation,
    maturity_deficits,
    verify_maturity_registry,
)


def _assessment(*, mature: bool) -> SemanticMaturityAssessment:
    policy = SemanticMaturityPolicy(
        minimum_semantic_records=100,
        minimum_unique_availability_dates=30,
        minimum_active_decision_rows=50,
        minimum_unique_sources=2,
        minimum_matured_labeled_rows=500,
    )
    if mature:
        values = {
            "relevant_semantic_record_count": 120,
            "unique_availability_date_count": 35,
            "unique_source_count": 2,
            "active_decision_row_count": 70,
            "matured_labeled_row_count": 600,
            "positive_target_count": 310,
            "negative_target_count": 290,
            "failure_reasons": (),
        }
        status = "mature_for_research"
    else:
        values = {
            "relevant_semantic_record_count": 8,
            "unique_availability_date_count": 1,
            "unique_source_count": 1,
            "active_decision_row_count": 0,
            "matured_labeled_row_count": 7632,
            "positive_target_count": 3915,
            "negative_target_count": 3717,
            "failure_reasons": (
                "insufficient_semantic_records",
                "insufficient_unique_availability_dates",
                "insufficient_active_decision_rows",
                "insufficient_source_diversity",
            ),
        }
        status = "insufficient_prospective_sample"
    return SemanticMaturityAssessment(
        assessment_id=("a" if mature else "b") * 64,
        status=status,
        research_model_fitting_allowed=mature,
        policy=policy,
        paper_or_live_trading_allowed=False,
        **values,
    )


def _observation(*, run_id: str, observed_at: datetime, mature: bool = False):
    return make_maturity_observation(
        observed_at=observed_at,
        workflow_run_id=run_id,
        source_commit_sha="c" * 40,
        market_snapshot_sha256="d" * 64,
        semantic_dataset_sha256=("e" if mature else "f") * 64,
        semantic_ledger_head_sha256="1" * 64,
        maturity=_assessment(mature=mature),
    )


def test_maturity_deficits_are_exact_and_never_negative() -> None:
    immature = maturity_deficits(_assessment(mature=False))
    assert immature.semantic_records == 92
    assert immature.availability_dates == 29
    assert immature.active_decision_rows == 50
    assert immature.unique_sources == 1
    assert immature.matured_labeled_rows == 0
    assert immature.missing_target_classes == 0

    mature = maturity_deficits(_assessment(mature=True))
    assert set(mature.model_dump().values()) == {0}


def test_registry_append_is_idempotent_hash_chained_and_time_ordered(
    tmp_path: Path,
) -> None:
    registry = tmp_path / "maturity.jsonl"
    first = _observation(
        run_id="run-1",
        observed_at=datetime(2026, 7, 17, 12, tzinfo=UTC),
    )
    appended, first_head = append_maturity_observation(registry, first)
    assert appended is True
    assert len(first_head) == 64

    appended_again, same_head = append_maturity_observation(registry, first)
    assert appended_again is False
    assert same_head == first_head

    second = _observation(
        run_id="run-2",
        observed_at=datetime(2026, 7, 18, 12, tzinfo=UTC),
        mature=True,
    )
    appended_second, second_head = append_maturity_observation(registry, second)
    assert appended_second is True
    assert second_head != first_head
    state = verify_maturity_registry(registry)
    assert state.count == 2
    assert state.head_sha256 == second_head
    assert state.previous_record is not None
    assert state.previous_record.next_action == "open_separate_predeclared_research_protocol"
    assert state.previous_record.model_fitting_executed is False
    assert state.previous_record.paper_or_live_trading_allowed is False

    stale = _observation(
        run_id="run-3",
        observed_at=datetime(2026, 7, 17, 18, tzinfo=UTC),
    )
    with pytest.raises(ValueError, match="does not advance time"):
        append_maturity_observation(registry, stale)


def test_duplicate_workflow_run_and_registry_tamper_fail_closed(tmp_path: Path) -> None:
    registry = tmp_path / "maturity.jsonl"
    observed = datetime(2026, 7, 17, 12, tzinfo=UTC)
    first = _observation(run_id="run-1", observed_at=observed)
    append_maturity_observation(registry, first)

    conflicting = make_maturity_observation(
        observed_at=observed + timedelta(hours=1),
        workflow_run_id="run-1",
        source_commit_sha="c" * 40,
        market_snapshot_sha256="9" * 64,
        semantic_dataset_sha256="8" * 64,
        semantic_ledger_head_sha256="1" * 64,
        maturity=_assessment(mature=False),
    )
    with pytest.raises(ValueError, match="Workflow run already exists"):
        append_maturity_observation(registry, conflicting)

    lines = registry.read_text(encoding="utf-8").splitlines()
    payload = json.loads(lines[0])
    payload["deficits"]["semantic_records"] = 0
    registry.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid maturity registry line"):
        verify_maturity_registry(registry)


def test_mature_observation_never_executes_or_authorizes_trading() -> None:
    observation = _observation(
        run_id="mature-run",
        observed_at=datetime(2026, 8, 20, 12, tzinfo=UTC),
        mature=True,
    )
    assert observation.next_action == "open_separate_predeclared_research_protocol"
    assert observation.model_fitting_executed is False
    assert observation.threshold_selection_executed is False
    assert observation.prospective_decisions_created is False
    assert observation.paper_or_live_trading_allowed is False
