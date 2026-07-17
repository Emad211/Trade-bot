"""Bounded prospective AvalAI pilot assessment and non-activation gate."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from statistics import fmean
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from hybrid_trader.avalai import AvalAICallRecord
from hybrid_trader.avalai_capture import (
    AvalAIProviderRunManifest,
    verify_phase3c_avalai_root,
)
from hybrid_trader.event_capture_models import EventCaptureManifest
from hybrid_trader.event_capture_state import canonical_sha256
from hybrid_trader.semantic_extraction import SemanticEventRecord

_SECRET_BYTES = re.compile(
    rb"(?i)(?:authorization\s*[:=]|bearer\s+|\b(?:aa|sk)-[A-Za-z0-9_-]{6,})"
)


class Phase3DPolicy(BaseModel):
    """Predeclared limits for the low-cost prospective pilot."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    max_new_calls: int = Field(default=2, ge=1, le=20)
    max_total_tokens: int = Field(default=4_000, ge=1)
    max_failed_calls: int = Field(default=0, ge=0)
    max_attempts_per_call: int = Field(default=4, ge=1, le=10)
    minimum_provider_runs: int = Field(default=2, ge=2)
    minimum_successful_sources: int = Field(default=2, ge=1)


class Phase3DAssessment(BaseModel):
    """Machine-readable verdict for one bounded prospective pilot."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    assessment_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: Literal["pass", "fail"]
    recommended_action: Literal["continue_data_collection", "retain_research_only"]
    policy: Phase3DPolicy
    provider_run_count: int = Field(ge=0)
    capture_count: int = Field(ge=0)
    call_count: int = Field(ge=0)
    successful_call_count: int = Field(ge=0)
    failed_call_count: int = Field(ge=0)
    first_run_new_call_count: int = Field(ge=0)
    latest_run_new_call_count: int = Field(ge=0)
    repeat_capture_zero_new_calls: bool
    semantic_record_count: int = Field(ge=0)
    successful_source_count: int = Field(ge=0)
    source_document_counts: dict[str, int]
    direction_counts: dict[str, int]
    total_input_tokens: int = Field(ge=0)
    total_output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    maximum_attempts: int = Field(ge=0)
    mean_latency_seconds: float = Field(ge=0)
    maximum_latency_seconds: float = Field(ge=0)
    mean_confidence: float = Field(ge=0, le=1)
    mean_novelty: float = Field(ge=0, le=1)
    mean_severity: float = Field(ge=0, le=1)
    prospective_decision_count: int = Field(ge=0)
    credential_pattern_detected: bool
    failure_reasons: tuple[str, ...]


def _call_records(path: Path) -> tuple[AvalAICallRecord, ...]:
    if not path.is_file():
        return ()
    return tuple(
        AvalAICallRecord.model_validate_json(line)
        for line in path.read_bytes().splitlines()
        if line
    )


def _semantic_records(path: Path) -> tuple[SemanticEventRecord, ...]:
    if not path.is_file():
        return ()
    return tuple(
        SemanticEventRecord.model_validate_json(line)
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


def _contains_secret_pattern(root: Path) -> bool:
    state = root / "state"
    if not state.is_dir():
        return False
    return any(
        _SECRET_BYTES.search(path.read_bytes()) is not None
        for path in state.rglob("*")
        if path.is_file()
    )


def _mean(values: list[float]) -> float:
    return float(fmean(values)) if values else 0.0


def assess_phase3d_pilot(
    root: str | Path,
    *,
    policy: Phase3DPolicy | None = None,
) -> Phase3DAssessment:
    """Assess a two-pass prospective capture without permitting trading activation."""

    capture_root = Path(root)
    declared_policy = policy or Phase3DPolicy()
    verification = verify_phase3c_avalai_root(capture_root)
    calls = _call_records(capture_root / "state" / "avalai_calls.jsonl")
    semantic = _semantic_records(capture_root / "state" / "semantic_events.jsonl")
    runs = _provider_runs(capture_root)

    input_tokens = sum(record.input_tokens or 0 for record in calls)
    output_tokens = sum(record.output_tokens or 0 for record in calls)
    total_tokens = sum(record.total_tokens or 0 for record in calls)
    attempts = [record.attempts for record in calls]
    latencies = [
        (record.completed_at - record.started_at).total_seconds() for record in calls
    ]
    directions = Counter(record.signal.direction for record in semantic)
    source_documents = Counter(record.source_id for record in semantic)
    confidence = [record.signal.confidence for record in semantic]
    novelty = [record.signal.novelty for record in semantic]
    severity = [record.signal.severity for record in semantic]

    first_new_calls = runs[0][1].new_call_count if runs else 0
    latest_new_calls = runs[-1][1].new_call_count if runs else 0
    successful_sources = len(runs[-1][0].successful_sources) if runs else 0
    credential_pattern = _contains_secret_pattern(capture_root)
    decision_count = int(verification["prospective_decision_count"])

    reasons: list[str] = []
    if len(runs) < declared_policy.minimum_provider_runs:
        reasons.append("insufficient_provider_runs")
    if first_new_calls < 1 or first_new_calls > declared_policy.max_new_calls:
        reasons.append("first_run_call_budget_failed")
    if latest_new_calls != 0:
        reasons.append("repeat_capture_created_provider_calls")
    if len(calls) > declared_policy.max_new_calls:
        reasons.append("total_call_budget_exceeded")
    failed_calls = sum(record.status == "failed" for record in calls)
    if failed_calls > declared_policy.max_failed_calls:
        reasons.append("provider_failures_exceeded")
    if total_tokens > declared_policy.max_total_tokens:
        reasons.append("token_budget_exceeded")
    if attempts and max(attempts) > declared_policy.max_attempts_per_call:
        reasons.append("retry_budget_exceeded")
    if successful_sources < declared_policy.minimum_successful_sources:
        reasons.append("insufficient_successful_sources")
    if len(semantic) != sum(record.status == "success" for record in calls):
        reasons.append("semantic_call_count_mismatch")
    if decision_count != 0:
        reasons.append("prospective_decision_created")
    if credential_pattern:
        reasons.append("credential_pattern_detected")

    payload = {
        "policy": declared_policy.model_dump(mode="json"),
        "provider_run_count": len(runs),
        "capture_ids": [capture.capture_id for capture, _ in runs],
        "call_count": len(calls),
        "semantic_ids": [record.signal_id for record in semantic],
        "total_tokens": total_tokens,
        "failure_reasons": reasons,
    }
    status: Literal["pass", "fail"] = "pass" if not reasons else "fail"
    assessment = Phase3DAssessment(
        assessment_id=canonical_sha256(payload),
        status=status,
        recommended_action=(
            "continue_data_collection" if status == "pass" else "retain_research_only"
        ),
        policy=declared_policy,
        provider_run_count=len(runs),
        capture_count=len(runs),
        call_count=len(calls),
        successful_call_count=sum(record.status == "success" for record in calls),
        failed_call_count=failed_calls,
        first_run_new_call_count=first_new_calls,
        latest_run_new_call_count=latest_new_calls,
        repeat_capture_zero_new_calls=bool(runs) and latest_new_calls == 0,
        semantic_record_count=len(semantic),
        successful_source_count=successful_sources,
        source_document_counts=dict(sorted(source_documents.items())),
        direction_counts=dict(sorted(directions.items())),
        total_input_tokens=input_tokens,
        total_output_tokens=output_tokens,
        total_tokens=total_tokens,
        maximum_attempts=max(attempts, default=0),
        mean_latency_seconds=_mean(latencies),
        maximum_latency_seconds=max(latencies, default=0.0),
        mean_confidence=_mean(confidence),
        mean_novelty=_mean(novelty),
        mean_severity=_mean(severity),
        prospective_decision_count=decision_count,
        credential_pattern_detected=credential_pattern,
        failure_reasons=tuple(reasons),
    )
    return assessment


def write_phase3d_assessment(
    root: str | Path,
    *,
    policy: Phase3DPolicy | None = None,
) -> Path:
    """Write a deterministic assessment and checksum beside the pilot artifact."""

    capture_root = Path(root)
    assessment = assess_phase3d_pilot(capture_root, policy=policy)
    path = capture_root / "phase3d_assessment.json"
    path.write_text(
        json.dumps(assessment.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    (capture_root / "PHASE3D_SHA256SUMS").write_text(
        f"{digest}  phase3d_assessment.json\n",
        encoding="utf-8",
    )
    return path
