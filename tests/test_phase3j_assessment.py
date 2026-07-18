from __future__ import annotations

import pytest
from pydantic import ValidationError

from hybrid_trader.event_capture_state import canonical_sha256
from hybrid_trader.phase3j import (
    Phase3JAssessment,
    Phase3JPolicy,
    Phase3JRunContext,
    phase3j_identity_payload,
)


def _context() -> Phase3JRunContext:
    return Phase3JRunContext(
        workflow_run_id="101",
        source_commit_sha="a" * 40,
        previous_workflow_name="phase3h-avalai-pilot",
        previous_workflow_run_id="100",
        previous_artifact_id=200,
        previous_artifact_digest="sha256:" + "b" * 64,
        state_restored=True,
    )


def _assessment(*, active: bool) -> Phase3JAssessment:
    new_calls = 2 if active else 0
    new_semantics = 2 if active else 0
    before_semantics = 2 if active else 4
    before_pending = 2 if active else 0
    candidate = Phase3JAssessment.model_construct(
        assessment_id="0" * 64,
        schema_version="1.0",
        status="pass",
        recommended_action="continue_diversified_longitudinal_collection",
        model_fitting_allowed=False,
        paper_or_live_trading_allowed=False,
        policy=Phase3JPolicy(max_new_calls=2, max_total_tokens=500),
        context=_context(),
        base_phase3e_assessment_id="c" * 64,
        before_source_health_assessment_id="d" * 64,
        after_source_health_assessment_id="e" * 64,
        latest_capture_id="f" * 64,
        latest_provider_run_id="1" * 64,
        new_call_count=new_calls,
        successful_new_call_count=new_calls,
        failed_new_call_count=0,
        latest_total_tokens=260 if active else 0,
        maximum_attempts=1 if active else 0,
        new_document_count=0,
        new_semantic_record_count=new_semantics,
        recovered_semantic_record_count=new_semantics,
        before_document_count=4,
        after_document_count=4,
        before_semantic_record_count=before_semantics,
        after_semantic_record_count=before_semantics + new_semantics,
        before_pending_semantic_document_count=before_pending,
        after_pending_semantic_document_count=0,
        pending_semantic_delta=-before_pending,
        new_semantic_sources=("alpha", "beta") if active else (),
        new_semantic_assets=("BTC", "MARKET") if active else (),
        document_source_count=2,
        semantic_source_count=2,
        semantic_assets=("BTC", "MARKET"),
        metadata_drift_sources=(),
        zero_accepted_sources_called=(),
        prospective_decision_count=0,
        credential_pattern_detected=False,
        failure_reasons=(),
    )
    payload = candidate.model_dump(mode="json")
    payload["assessment_id"] = canonical_sha256(phase3j_identity_payload(candidate))
    return Phase3JAssessment.model_validate(payload)


def test_phase3j_assessment_reconciles_backlog_drainage() -> None:
    assessment = _assessment(active=True)
    assert assessment.status == "pass"
    assert assessment.pending_semantic_delta == -2
    assert assessment.after_pending_semantic_document_count == 0
    assert assessment.new_semantic_sources == ("alpha", "beta")
    assert assessment.new_semantic_assets == ("BTC", "MARKET")


def test_phase3j_assessment_allows_verified_zero_call_continuity() -> None:
    assessment = _assessment(active=False)
    assert assessment.status == "pass"
    assert assessment.new_call_count == 0
    assert assessment.pending_semantic_delta == 0
    assert assessment.new_semantic_sources == ()
    assert assessment.new_semantic_assets == ()


def test_phase3j_assessment_rejects_inconsistent_backlog_arithmetic() -> None:
    payload = _assessment(active=True).model_dump(mode="json")
    payload["after_pending_semantic_document_count"] = 1
    with pytest.raises(ValidationError, match="pending backlog delta"):
        Phase3JAssessment.model_validate(payload)


def test_phase3j_context_requires_verified_restoration() -> None:
    payload = _context().model_dump(mode="json")
    payload["state_restored"] = False
    with pytest.raises(ValidationError, match="verified restored semantic state"):
        Phase3JRunContext.model_validate(payload)
