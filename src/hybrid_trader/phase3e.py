"""Longitudinal prospective AvalAI state and per-run budget assessment."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from statistics import fmean
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from hybrid_trader.avalai import AvalAICallRecord, verify_avalai_call_ledger
from hybrid_trader.avalai_capture import (
    AvalAIProviderRunManifest,
    verify_phase3c_avalai_root,
)
from hybrid_trader.event_capture_models import EventCaptureManifest
from hybrid_trader.event_capture_state import canonical_sha256
from hybrid_trader.semantic_extraction import verify_semantic_ledger

_SECRET_BYTES = re.compile(
    rb"(?i)(?:authorization\s*[:=]|bearer\s+|\b(?:aa|sk)-[A-Za-z0-9_-]{6,})"
)


class Phase3ERunContext(BaseModel):
    """Secret-free identity for restoration and the current Actions run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    workflow_run_id: str = Field(min_length=1, max_length=100)
    source_commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    previous_workflow_run_id: str | None = Field(default=None, max_length=100)
    previous_artifact_id: int | None = Field(default=None, ge=1)
    previous_artifact_digest: str | None = Field(
        default=None,
        pattern=r"^sha256:[0-9a-f]{64}$",
    )
    state_restored: bool = False


class Phase3EPolicy(BaseModel):
    """Predeclared latest-run quality, coverage and cost limits."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    max_new_calls_per_run: int = Field(default=4, ge=1, le=20)
    max_total_tokens_per_run: int = Field(default=8_000, ge=1)
    max_failed_calls_per_run: int = Field(default=0, ge=0)
    max_attempts_per_call: int = Field(default=4, ge=1, le=10)
    minimum_successful_sources: int = Field(default=1, ge=1)


class Phase3EAssessment(BaseModel):
    """Machine-readable verdict for one longitudinal capture delta."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    assessment_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: Literal["pass", "fail"]
    recommended_action: Literal["continue_longitudinal_collection", "halt_and_review"]
    policy: Phase3EPolicy
    context: Phase3ERunContext
    provider_run_count: int = Field(ge=1)
    latest_capture_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    latest_provider_run_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    latest_capture_status: Literal["success", "failed"]
    previous_call_count: int = Field(ge=0)
    total_call_count: int = Field(ge=0)
    new_call_count: int = Field(ge=0)
    successful_new_call_count: int = Field(ge=0)
    failed_new_call_count: int = Field(ge=0)
    maximum_attempts: int = Field(ge=0)
    latest_input_tokens: int = Field(ge=0)
    latest_output_tokens: int = Field(ge=0)
    latest_total_tokens: int = Field(ge=0)
    mean_latency_seconds: float = Field(ge=0)
    maximum_latency_seconds: float = Field(ge=0)
    successful_source_count: int = Field(ge=0)
    failed_source_count: int = Field(ge=0)
    new_document_count: int = Field(ge=0)
    total_document_count: int = Field(ge=0)
    new_semantic_record_count: int = Field(ge=0)
    total_semantic_record_count: int = Field(ge=0)
    pending_semantic_document_count: int = Field(ge=0)
    duplicate_extraction_key_count: int = Field(ge=0)
    prospective_decision_count: int = Field(ge=0)
    credential_pattern_detected: bool
    failure_reasons: tuple[str, ...]


def _records(path: Path) -> tuple[AvalAICallRecord, ...]:
    if not path.is_file():
        return ()
    return tuple(
        AvalAICallRecord.model_validate_json(line)
        for line in path.read_bytes().splitlines()
        if line
    )


def _provider_runs(
    root: Path,
) -> tuple[tuple[EventCaptureManifest, AvalAIProviderRunManifest], ...]:
    runs: list[tuple[EventCaptureManifest, AvalAIProviderRunManifest]] = []
    runs_root = root / "state" / "avalai_runs"
    if not runs_root.is_dir():
        return ()
    for run_root in sorted(path for path in runs_root.iterdir() if path.is_dir()):
        provider = AvalAIProviderRunManifest.model_validate_json(
            (run_root / "provider_manifest.json").read_text(encoding="utf-8")
        )
        capture = EventCaptureManifest.model_validate_json(
            (root / provider.capture_manifest_relative_path).read_text(encoding="utf-8")
        )
        runs.append((capture, provider))
    runs.sort(key=lambda item: (item[0].capture_completed_at, item[0].capture_id))
    return tuple(runs)


def _context(root: Path) -> Phase3ERunContext:
    path = root / "phase3e_run_context.json"
    if not path.is_file():
        raise FileNotFoundError("Phase 3E run context is missing")
    return Phase3ERunContext.model_validate_json(path.read_text(encoding="utf-8"))


def _secret_pattern(root: Path) -> bool:
    state = root / "state"
    if not state.is_dir():
        return False
    return any(
        _SECRET_BYTES.search(path.read_bytes()) is not None
        for path in state.rglob("*")
        if path.is_file()
    )


def _decision_count(verification: dict[str, object]) -> int:
    value = verification.get("prospective_decision_count")
    if not isinstance(value, int):
        raise TypeError("Phase 3C verifier returned a non-integer decision count")
    return value


def _mean(values: list[float]) -> float:
    return float(fmean(values)) if values else 0.0


def assess_phase3e_run(
    root: str | Path,
    *,
    policy: Phase3EPolicy | None = None,
) -> Phase3EAssessment:
    """Assess only the newest longitudinal delta while verifying the full state."""

    capture_root = Path(root)
    declared_policy = policy or Phase3EPolicy()
    verification = verify_phase3c_avalai_root(capture_root)
    context = _context(capture_root)
    call_state = verify_avalai_call_ledger(capture_root / "state" / "avalai_calls.jsonl")
    semantic_state = verify_semantic_ledger(capture_root / "state" / "semantic_events.jsonl")
    records = _records(capture_root / "state" / "avalai_calls.jsonl")
    runs = _provider_runs(capture_root)
    if not runs:
        raise RuntimeError("No longitudinal provider run was found")
    capture, provider = runs[-1]

    if provider.call_count_after != len(records) or provider.call_count_after != call_state.count:
        raise RuntimeError("Latest provider manifest disagrees with the call ledger")
    if provider.call_count_before > len(records):
        raise RuntimeError("Latest provider call_count_before exceeds the ledger")
    new_records = records[provider.call_count_before : provider.call_count_after]
    if tuple(record.call_id for record in new_records) != provider.new_call_ids:
        raise RuntimeError("Latest provider manifest call IDs are not the ledger delta")

    previous_keys = {record.extraction_key for record in records[: provider.call_count_before]}
    duplicate_keys = sum(record.extraction_key in previous_keys for record in new_records)
    attempts = [record.attempts for record in new_records]
    latencies = [
        (record.completed_at - record.started_at).total_seconds() for record in new_records
    ]
    input_tokens = sum(record.input_tokens or 0 for record in new_records)
    output_tokens = sum(record.output_tokens or 0 for record in new_records)
    total_tokens = sum(record.total_tokens or 0 for record in new_records)
    decision_count = _decision_count(verification)
    credential_pattern = _secret_pattern(capture_root)
    pending_semantic = capture.document_count - semantic_state.count
    if pending_semantic < 0:
        raise RuntimeError("Semantic record count exceeds document count")

    reasons: list[str] = []
    if context.previous_workflow_run_id is not None and not context.state_restored:
        reasons.append("previous_state_not_restored")
    if context.state_restored and context.previous_workflow_run_id is None:
        reasons.append("restoration_without_previous_run")
    if provider.new_call_count > declared_policy.max_new_calls_per_run:
        reasons.append("new_call_budget_exceeded")
    if provider.failed_call_count > declared_policy.max_failed_calls_per_run:
        reasons.append("provider_failure_budget_exceeded")
    if total_tokens > declared_policy.max_total_tokens_per_run:
        reasons.append("token_budget_exceeded")
    if attempts and max(attempts) > declared_policy.max_attempts_per_call:
        reasons.append("retry_budget_exceeded")
    if len(capture.successful_sources) < declared_policy.minimum_successful_sources:
        reasons.append("insufficient_successful_sources")
    if provider.successful_call_count != capture.new_semantic_record_count:
        reasons.append("successful_call_semantic_delta_mismatch")
    if duplicate_keys:
        reasons.append("duplicate_extraction_key_called")
    if decision_count:
        reasons.append("prospective_decision_created")
    if credential_pattern:
        reasons.append("credential_pattern_detected")
    if capture.status != "success":
        reasons.append("capture_failed")

    identity = {
        "context": context.model_dump(mode="json"),
        "policy": declared_policy.model_dump(mode="json"),
        "latest_capture_id": capture.capture_id,
        "latest_provider_run_id": provider.provider_run_id,
        "call_ledger_head": call_state.head_sha256,
        "semantic_ledger_head": semantic_state.head_sha256,
        "new_call_ids": list(provider.new_call_ids),
        "failure_reasons": reasons,
    }
    status: Literal["pass", "fail"] = "pass" if not reasons else "fail"
    return Phase3EAssessment(
        assessment_id=canonical_sha256(identity),
        status=status,
        recommended_action=(
            "continue_longitudinal_collection" if status == "pass" else "halt_and_review"
        ),
        policy=declared_policy,
        context=context,
        provider_run_count=len(runs),
        latest_capture_id=capture.capture_id,
        latest_provider_run_id=provider.provider_run_id,
        latest_capture_status=capture.status,
        previous_call_count=provider.call_count_before,
        total_call_count=provider.call_count_after,
        new_call_count=provider.new_call_count,
        successful_new_call_count=provider.successful_call_count,
        failed_new_call_count=provider.failed_call_count,
        maximum_attempts=max(attempts, default=0),
        latest_input_tokens=input_tokens,
        latest_output_tokens=output_tokens,
        latest_total_tokens=total_tokens,
        mean_latency_seconds=_mean(latencies),
        maximum_latency_seconds=max(latencies, default=0.0),
        successful_source_count=len(capture.successful_sources),
        failed_source_count=len(capture.failed_sources),
        new_document_count=capture.new_document_count,
        total_document_count=capture.document_count,
        new_semantic_record_count=capture.new_semantic_record_count,
        total_semantic_record_count=semantic_state.count,
        pending_semantic_document_count=pending_semantic,
        duplicate_extraction_key_count=duplicate_keys,
        prospective_decision_count=decision_count,
        credential_pattern_detected=credential_pattern,
        failure_reasons=tuple(reasons),
    )


def write_phase3e_assessment(
    root: str | Path,
    *,
    policy: Phase3EPolicy | None = None,
) -> Path:
    """Write the latest-run assessment and its deterministic checksum."""

    capture_root = Path(root)
    assessment = assess_phase3e_run(capture_root, policy=policy)
    path = capture_root / "phase3e_assessment.json"
    path.write_text(
        json.dumps(assessment.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    (capture_root / "PHASE3E_SHA256SUMS").write_text(
        f"{digest}  phase3e_assessment.json\n",
        encoding="utf-8",
    )
    return path
