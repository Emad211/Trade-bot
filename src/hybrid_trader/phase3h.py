"""Phase 3H bounded source-diversity and relevance pilot assessment."""

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
from hybrid_trader.semantic_extraction import SemanticEventRecord


class Phase3HPilotPolicy(BaseModel):
    """Frozen quality and diversity requirements for the first live Phase 3H pilot."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    max_new_calls: int = Field(default=4, ge=1, le=20)
    max_total_tokens: int = Field(default=8_000, ge=1)
    max_failed_calls: int = Field(default=0, ge=0)
    max_attempts_per_call: int = Field(default=4, ge=1, le=10)
    minimum_successful_sources: int = Field(default=2, ge=1)
    minimum_new_semantic_sources: int = Field(default=2, ge=1)
    minimum_new_assets: int = Field(default=2, ge=1)
    required_new_sources: tuple[str, ...] = (
        "bitcoin-optech-newsletters",
        "federal-reserve-monetary-policy",
    )
    required_new_assets: tuple[str, ...] = ("BTC", "MARKET")
    minimum_relevance_rejections: int = Field(default=1, ge=0)

    @model_validator(mode="after")
    def validate_required_sets(self) -> Phase3HPilotPolicy:
        if len(set(self.required_new_sources)) != len(self.required_new_sources):
            raise ValueError("required_new_sources cannot contain duplicates")
        if len(set(self.required_new_assets)) != len(self.required_new_assets):
            raise ValueError("required_new_assets cannot contain duplicates")
        return self


class Phase3HPilotAssessment(BaseModel):
    """Machine-readable verdict for a bounded live source-diversity pilot."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    assessment_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: Literal["pass", "fail"]
    recommended_action: Literal[
        "continue_diversified_collection",
        "halt_and_review",
    ]
    provider_calls_or_model_fitting_allowed: bool = False
    paper_or_live_trading_allowed: bool = False
    policy: Phase3HPilotPolicy
    base_phase3e_assessment_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    latest_capture_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    latest_provider_run_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    new_call_count: int = Field(ge=0)
    successful_new_call_count: int = Field(ge=0)
    failed_new_call_count: int = Field(ge=0)
    latest_total_tokens: int = Field(ge=0)
    maximum_attempts: int = Field(ge=0)
    successful_capture_sources: tuple[str, ...]
    failed_capture_sources: tuple[str, ...]
    new_semantic_sources: tuple[str, ...]
    new_semantic_assets: tuple[str, ...]
    missing_required_sources: tuple[str, ...]
    missing_required_assets: tuple[str, ...]
    zero_accepted_sources_called: tuple[str, ...]
    relevance_accepted_document_count: int = Field(ge=0)
    relevance_rejected_document_count: int = Field(ge=0)
    new_document_count: int = Field(ge=0)
    new_semantic_record_count: int = Field(ge=0)
    prospective_decision_count: int = Field(ge=0)
    credential_pattern_detected: bool
    failure_reasons: tuple[str, ...]

    @model_validator(mode="after")
    def enforce_non_activation(self) -> Phase3HPilotAssessment:
        if self.provider_calls_or_model_fitting_allowed:
            raise ValueError("Phase 3H cannot authorize further provider calls or fitting")
        if self.paper_or_live_trading_allowed:
            raise ValueError("Phase 3H cannot authorize paper or live trading")
        return self


def _jsonl_records(path: Path, model: type[BaseModel]) -> tuple[BaseModel, ...]:
    if not path.is_file():
        return ()
    return tuple(model.model_validate_json(line) for line in path.read_bytes().splitlines() if line)


def _latest_provider_run(root: Path) -> tuple[EventCaptureManifest, AvalAIProviderRunManifest]:
    runs: list[tuple[EventCaptureManifest, AvalAIProviderRunManifest]] = []
    for run_root in sorted((root / "state" / "avalai_runs").iterdir()):
        if not run_root.is_dir():
            continue
        provider = AvalAIProviderRunManifest.model_validate_json(
            (run_root / "provider_manifest.json").read_text(encoding="utf-8")
        )
        capture = EventCaptureManifest.model_validate_json(
            (root / provider.capture_manifest_relative_path).read_text(encoding="utf-8")
        )
        runs.append((capture, provider))
    if not runs:
        raise RuntimeError("No Phase 3H provider run was found")
    runs.sort(key=lambda item: (item[0].capture_completed_at, item[0].capture_id))
    return runs[-1]


def assess_phase3h_pilot(
    root: str | Path,
    *,
    policy: Phase3HPilotPolicy | None = None,
) -> Phase3HPilotAssessment:
    """Verify the full state and assess the latest bounded diversity delta."""

    capture_root = Path(root)
    declared = policy or Phase3HPilotPolicy()
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
    call_records = tuple(
        record
        for record in _jsonl_records(
            capture_root / "state" / "avalai_calls.jsonl",
            AvalAICallRecord,
        )
        if isinstance(record, AvalAICallRecord)
    )
    semantic_records = tuple(
        record
        for record in _jsonl_records(
            capture_root / "state" / "semantic_events.jsonl",
            SemanticEventRecord,
        )
        if isinstance(record, SemanticEventRecord)
    )
    call_by_id = {record.call_id: record for record in call_records}
    new_calls = tuple(call_by_id[call_id] for call_id in provider.new_call_ids)
    new_keys = {record.extraction_key for record in new_calls}
    new_semantic = tuple(record for record in semantic_records if record.extraction_key in new_keys)
    if len(new_semantic) != provider.successful_call_count:
        raise RuntimeError("New successful calls do not map one-to-one to semantic records")
    if len({record.extraction_key for record in new_semantic}) != len(new_semantic):
        raise RuntimeError("Latest semantic delta contains duplicate extraction keys")

    semantic_sources = tuple(sorted({record.source_id for record in new_semantic}))
    semantic_assets = tuple(sorted({record.signal.asset for record in new_semantic}))
    missing_sources = tuple(sorted(set(declared.required_new_sources).difference(semantic_sources)))
    missing_assets = tuple(sorted(set(declared.required_new_assets).difference(semantic_assets)))
    zero_accepted = {
        attempt.source_id
        for attempt in capture.source_attempts
        if attempt.status == "success" and attempt.relevance_accepted_documents == 0
    }
    zero_accepted_called = tuple(sorted(zero_accepted.intersection(semantic_sources)))

    reasons = list(base.failure_reasons)
    if base.status != "pass":
        reasons.append("phase3e_base_gate_failed")
    if len(semantic_sources) < declared.minimum_new_semantic_sources:
        reasons.append("insufficient_new_semantic_source_diversity")
    if len(semantic_assets) < declared.minimum_new_assets:
        reasons.append("insufficient_new_asset_diversity")
    if missing_sources:
        reasons.append("required_new_sources_missing")
    if missing_assets:
        reasons.append("required_new_assets_missing")
    if zero_accepted_called:
        reasons.append("zero_accepted_source_received_provider_call")
    if capture.relevance_rejected_document_count < declared.minimum_relevance_rejections:
        reasons.append("insufficient_relevance_rejection_evidence")

    deduplicated_reasons = tuple(dict.fromkeys(reasons))
    status: Literal["pass", "fail"] = "pass" if not deduplicated_reasons else "fail"
    identity = {
        "policy": declared.model_dump(mode="json"),
        "base_phase3e_assessment_id": base.assessment_id,
        "latest_capture_id": capture.capture_id,
        "latest_provider_run_id": provider.provider_run_id,
        "new_call_ids": list(provider.new_call_ids),
        "new_semantic_signal_ids": [record.signal_id for record in new_semantic],
        "new_semantic_sources": list(semantic_sources),
        "new_semantic_assets": list(semantic_assets),
        "failure_reasons": list(deduplicated_reasons),
    }
    return Phase3HPilotAssessment(
        assessment_id=canonical_sha256(identity),
        status=status,
        recommended_action=(
            "continue_diversified_collection" if status == "pass" else "halt_and_review"
        ),
        policy=declared,
        base_phase3e_assessment_id=base.assessment_id,
        latest_capture_id=capture.capture_id,
        latest_provider_run_id=provider.provider_run_id,
        new_call_count=base.new_call_count,
        successful_new_call_count=base.successful_new_call_count,
        failed_new_call_count=base.failed_new_call_count,
        latest_total_tokens=base.latest_total_tokens,
        maximum_attempts=base.maximum_attempts,
        successful_capture_sources=capture.successful_sources,
        failed_capture_sources=capture.failed_sources,
        new_semantic_sources=semantic_sources,
        new_semantic_assets=semantic_assets,
        missing_required_sources=missing_sources,
        missing_required_assets=missing_assets,
        zero_accepted_sources_called=zero_accepted_called,
        relevance_accepted_document_count=capture.relevance_accepted_document_count,
        relevance_rejected_document_count=capture.relevance_rejected_document_count,
        new_document_count=capture.new_document_count,
        new_semantic_record_count=capture.new_semantic_record_count,
        prospective_decision_count=base.prospective_decision_count,
        credential_pattern_detected=base.credential_pattern_detected,
        failure_reasons=deduplicated_reasons,
    )


def write_phase3h_assessment(
    root: str | Path,
    *,
    policy: Phase3HPilotPolicy | None = None,
) -> Path:
    """Write the Phase 3H assessment and its deterministic checksum."""

    capture_root = Path(root)
    assessment = assess_phase3h_pilot(capture_root, policy=policy)
    path = capture_root / "phase3h_assessment.json"
    path.write_text(
        json.dumps(assessment.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    (capture_root / "PHASE3H_SHA256SUMS").write_text(
        f"{digest}  phase3h_assessment.json\n",
        encoding="utf-8",
    )
    return path
