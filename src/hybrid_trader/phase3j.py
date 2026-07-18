"""Diversified longitudinal semantic collection and backlog assessment."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from hybrid_trader.avalai import AvalAICallRecord
from hybrid_trader.avalai_capture import AvalAIProviderRunManifest
from hybrid_trader.event_capture_models import EventCaptureManifest
from hybrid_trader.event_capture_state import canonical_sha256
from hybrid_trader.phase3e import Phase3EPolicy, assess_phase3e_run
from hybrid_trader.phase3i_health import Phase3ISourceHealthAssessment
from hybrid_trader.semantic_extraction import SemanticEventRecord

PreviousSemanticWorkflow = Literal[
    "phase3h-avalai-pilot",
    "phase3j-diversified-longitudinal",
]


class Phase3JRunContext(BaseModel):
    """Verified restoration identity for one Phase 3J collection run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    workflow_run_id: str = Field(pattern=r"^[0-9]+$")
    source_commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    previous_workflow_name: PreviousSemanticWorkflow
    previous_workflow_run_id: str = Field(pattern=r"^[0-9]+$")
    previous_artifact_id: int = Field(ge=1)
    previous_artifact_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    state_restored: bool = True

    @model_validator(mode="after")
    def require_restored_state(self) -> Phase3JRunContext:
        if not self.state_restored:
            raise ValueError("Phase 3J requires a verified restored semantic state")
        return self


class Phase3JPolicy(BaseModel):
    """Predeclared longitudinal cost, diversity, and backlog limits."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    max_new_calls: int = Field(default=4, ge=1, le=20)
    max_total_tokens: int = Field(default=8_000, ge=1)
    max_failed_calls: int = Field(default=0, ge=0)
    max_attempts_per_call: int = Field(default=4, ge=1, le=10)
    minimum_successful_sources: int = Field(default=2, ge=1)
    minimum_new_semantic_sources_when_active: int = Field(default=2, ge=1)
    minimum_new_assets_when_active: int = Field(default=2, ge=1)
    maximum_pending_semantic_documents: int = Field(default=100, ge=0)
    allow_zero_call_run: bool = True


class Phase3JAssessment(BaseModel):
    """Machine-readable verdict for one diversified longitudinal delta."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    assessment_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: Literal["pass", "fail"]
    recommended_action: Literal[
        "continue_diversified_longitudinal_collection",
        "halt_and_review",
    ]
    model_fitting_allowed: bool = False
    paper_or_live_trading_allowed: bool = False
    policy: Phase3JPolicy
    context: Phase3JRunContext
    base_phase3e_assessment_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    before_source_health_assessment_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    after_source_health_assessment_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    latest_capture_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    latest_provider_run_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    new_call_count: int = Field(ge=0)
    successful_new_call_count: int = Field(ge=0)
    failed_new_call_count: int = Field(ge=0)
    latest_total_tokens: int = Field(ge=0)
    maximum_attempts: int = Field(ge=0)
    new_document_count: int = Field(ge=0)
    new_semantic_record_count: int = Field(ge=0)
    recovered_semantic_record_count: int = Field(ge=0)
    before_document_count: int = Field(ge=0)
    after_document_count: int = Field(ge=0)
    before_semantic_record_count: int = Field(ge=0)
    after_semantic_record_count: int = Field(ge=0)
    before_pending_semantic_document_count: int = Field(ge=0)
    after_pending_semantic_document_count: int = Field(ge=0)
    pending_semantic_delta: int
    new_semantic_sources: tuple[str, ...]
    new_semantic_assets: tuple[str, ...]
    document_source_count: int = Field(ge=0)
    semantic_source_count: int = Field(ge=0)
    semantic_assets: tuple[str, ...]
    metadata_drift_sources: tuple[str, ...]
    zero_accepted_sources_called: tuple[str, ...]
    prospective_decision_count: int = Field(ge=0)
    credential_pattern_detected: bool
    failure_reasons: tuple[str, ...]

    @model_validator(mode="after")
    def validate_totals_and_safety(self) -> Phase3JAssessment:
        if self.model_fitting_allowed or self.paper_or_live_trading_allowed:
            raise ValueError("Phase 3J cannot authorize model fitting or trading")
        if self.after_document_count - self.before_document_count != self.new_document_count:
            raise ValueError("Phase 3J document delta does not reconcile")
        if (
            self.after_semantic_record_count - self.before_semantic_record_count
            != self.new_semantic_record_count
        ):
            raise ValueError("Phase 3J semantic delta does not reconcile")
        if (
            self.after_pending_semantic_document_count
            - self.before_pending_semantic_document_count
            != self.pending_semantic_delta
        ):
            raise ValueError("Phase 3J pending backlog delta does not reconcile")
        if self.pending_semantic_delta != self.new_document_count - self.new_semantic_record_count:
            raise ValueError("Phase 3J backlog movement disagrees with document/semantic deltas")
        if self.assessment_id != canonical_sha256(phase3j_identity_payload(self)):
            raise ValueError("Phase 3J assessment ID is not self-consistent")
        return self


def phase3j_identity_payload(assessment: Phase3JAssessment) -> dict[str, object]:
    payload = assessment.model_dump(mode="json", exclude={"assessment_id"})
    return {str(key): value for key, value in payload.items()}


def _load_jsonl(path: Path, model: type[BaseModel]) -> tuple[BaseModel, ...]:
    if not path.exists() or path.stat().st_size == 0:
        return ()
    return tuple(
        model.model_validate_json(line)
        for line in path.read_bytes().splitlines()
        if line
    )


def _latest_provider_run(root: Path) -> tuple[EventCaptureManifest, AvalAIProviderRunManifest]:
    runs: list[tuple[EventCaptureManifest, AvalAIProviderRunManifest]] = []
    runs_root = root / "state" / "avalai_runs"
    if not runs_root.is_dir():
        raise RuntimeError("Phase 3J state contains no provider-run directory")
    for run_root in sorted(path for path in runs_root.iterdir() if path.is_dir()):
        provider = AvalAIProviderRunManifest.model_validate_json(
            (run_root / "provider_manifest.json").read_text(encoding="utf-8")
        )
        capture = EventCaptureManifest.model_validate_json(
            (root / provider.capture_manifest_relative_path).read_text(encoding="utf-8")
        )
        runs.append((capture, provider))
    if not runs:
        raise RuntimeError("Phase 3J state contains no provider run")
    runs.sort(key=lambda item: (item[0].capture_completed_at, item[0].capture_id))
    return runs[-1]


def _run_context(root: Path) -> Phase3JRunContext:
    path = root / "phase3j_run_context.json"
    if not path.is_file():
        raise FileNotFoundError("Phase 3J run context is missing")
    return Phase3JRunContext.model_validate_json(path.read_text(encoding="utf-8"))


def assess_phase3j_run(
    root: str | Path,
    *,
    before_health: Phase3ISourceHealthAssessment,
    after_health: Phase3ISourceHealthAssessment,
    policy: Phase3JPolicy | None = None,
) -> Phase3JAssessment:
    """Assess the newest bounded delta over a verified restored semantic state."""

    capture_root = Path(root)
    declared = policy or Phase3JPolicy()
    context = _run_context(capture_root)
    base = assess_phase3e_run(
        capture_root,
        policy=Phase3EPolicy(
            max_new_calls_per_run=declared.max_new_calls,
            max_total_tokens_per_run=declared.max_total_tokens,
            max_failed_calls_per_run=declared.max_failed_calls,
            max_attempts_per_call=declared.max_attempts_per_call,
            minimum_successful_sources=declared.minimum_successful_sources,
        ),
    )
    capture, provider = _latest_provider_run(capture_root)
    calls = tuple(
        record
        for record in _load_jsonl(
            capture_root / "state" / "avalai_calls.jsonl",
            AvalAICallRecord,
        )
        if isinstance(record, AvalAICallRecord)
    )
    semantics = tuple(
        record
        for record in _load_jsonl(
            capture_root / "state" / "semantic_events.jsonl",
            SemanticEventRecord,
        )
        if isinstance(record, SemanticEventRecord)
    )
    call_by_id = {record.call_id: record for record in calls}
    new_calls = tuple(call_by_id[call_id] for call_id in provider.new_call_ids)
    new_keys = {record.extraction_key for record in new_calls}
    new_semantics = tuple(record for record in semantics if record.extraction_key in new_keys)
    if len(new_semantics) != provider.successful_call_count:
        raise RuntimeError("Phase 3J new calls do not map one-to-one to semantic records")
    new_sources = tuple(sorted({record.source_id for record in new_semantics}))
    new_assets = tuple(sorted({record.signal.asset for record in new_semantics}))

    reasons = list(base.failure_reasons)
    if base.status != "pass":
        reasons.append("phase3e_base_gate_failed")
    if before_health.status != "pass":
        reasons.append("restored_source_health_failed")
    if after_health.status != "pass":
        reasons.append("current_source_health_failed")
    if base.new_call_count == 0 and not declared.allow_zero_call_run:
        reasons.append("zero_call_run_not_allowed")
    if base.new_call_count > 0:
        if len(new_sources) < declared.minimum_new_semantic_sources_when_active:
            reasons.append("insufficient_new_semantic_source_diversity")
        if len(new_assets) < declared.minimum_new_assets_when_active:
            reasons.append("insufficient_new_asset_diversity")
    if after_health.total_pending_semantic_document_count > declared.maximum_pending_semantic_documents:
        reasons.append("pending_semantic_backlog_limit_exceeded")
    if after_health.metadata_drift_sources:
        reasons.append("source_metadata_drift_detected")
    if after_health.zero_accepted_sources_called:
        reasons.append("zero_accepted_source_received_provider_call")

    deduplicated = tuple(dict.fromkeys(reasons))
    status: Literal["pass", "fail"] = "pass" if not deduplicated else "fail"
    candidate = Phase3JAssessment.model_construct(
        assessment_id="0" * 64,
        schema_version="1.0",
        status=status,
        recommended_action=(
            "continue_diversified_longitudinal_collection"
            if status == "pass"
            else "halt_and_review"
        ),
        model_fitting_allowed=False,
        paper_or_live_trading_allowed=False,
        policy=declared,
        context=context,
        base_phase3e_assessment_id=base.assessment_id,
        before_source_health_assessment_id=before_health.assessment_id,
        after_source_health_assessment_id=after_health.assessment_id,
        latest_capture_id=capture.capture_id,
        latest_provider_run_id=provider.provider_run_id,
        new_call_count=base.new_call_count,
        successful_new_call_count=base.successful_new_call_count,
        failed_new_call_count=base.failed_new_call_count,
        latest_total_tokens=base.latest_total_tokens,
        maximum_attempts=base.maximum_attempts,
        new_document_count=base.new_document_count,
        new_semantic_record_count=base.new_semantic_record_count,
        recovered_semantic_record_count=capture.recovered_semantic_record_count,
        before_document_count=before_health.total_document_count,
        after_document_count=after_health.total_document_count,
        before_semantic_record_count=before_health.total_semantic_record_count,
        after_semantic_record_count=after_health.total_semantic_record_count,
        before_pending_semantic_document_count=before_health.total_pending_semantic_document_count,
        after_pending_semantic_document_count=after_health.total_pending_semantic_document_count,
        pending_semantic_delta=(
            after_health.total_pending_semantic_document_count
            - before_health.total_pending_semantic_document_count
        ),
        new_semantic_sources=new_sources,
        new_semantic_assets=new_assets,
        document_source_count=after_health.document_source_count,
        semantic_source_count=after_health.semantic_source_count,
        semantic_assets=after_health.semantic_assets,
        metadata_drift_sources=after_health.metadata_drift_sources,
        zero_accepted_sources_called=after_health.zero_accepted_sources_called,
        prospective_decision_count=base.prospective_decision_count,
        credential_pattern_detected=base.credential_pattern_detected,
        failure_reasons=deduplicated,
    )
    payload = candidate.model_dump(mode="json")
    payload["assessment_id"] = canonical_sha256(phase3j_identity_payload(candidate))
    return Phase3JAssessment.model_validate(payload)


def write_phase3j_assessment(assessment: Phase3JAssessment, path: str | Path) -> Path:
    """Write the Phase 3J verdict and deterministic checksum."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(assessment.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_name("PHASE3J_SHA256SUMS").write_text(
        f"{digest}  {output.name}\n",
        encoding="utf-8",
    )
    return output
