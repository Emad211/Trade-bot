"""Tamper-evident monitoring of prospective semantic dataset maturity."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hybrid_trader.data.snapshot import canonical_json_sha256
from hybrid_trader.semantic_dataset import SemanticMaturityAssessment


class SemanticMaturityDeficits(BaseModel):
    """Remaining observations required by each frozen Phase 3F threshold."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    semantic_records: int = Field(ge=0)
    availability_dates: int = Field(ge=0)
    active_decision_rows: int = Field(ge=0)
    unique_sources: int = Field(ge=0)
    matured_labeled_rows: int = Field(ge=0)
    missing_target_classes: int = Field(ge=0, le=2)


class SemanticMaturityObservation(BaseModel):
    """One immutable, non-activating maturity observation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    observation_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    observed_at: datetime
    workflow_run_id: str = Field(min_length=1, max_length=100)
    source_commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    market_snapshot_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    semantic_dataset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    semantic_ledger_head_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    maturity: SemanticMaturityAssessment
    deficits: SemanticMaturityDeficits
    next_action: Literal[
        "continue_prospective_collection",
        "open_separate_predeclared_research_protocol",
    ]
    model_fitting_executed: bool = False
    threshold_selection_executed: bool = False
    prospective_decisions_created: bool = False
    paper_or_live_trading_allowed: bool = False
    previous_record_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )

    @field_validator("observed_at")
    @classmethod
    def normalize_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Maturity observation time must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_non_activation(self) -> SemanticMaturityObservation:
        if self.model_fitting_executed:
            raise ValueError("Phase 3G cannot execute model fitting")
        if self.threshold_selection_executed:
            raise ValueError("Phase 3G cannot select a trading threshold")
        if self.prospective_decisions_created:
            raise ValueError("Phase 3G cannot create prospective decisions")
        if self.paper_or_live_trading_allowed:
            raise ValueError("Phase 3G cannot authorize paper or live trading")
        expected_action = (
            "open_separate_predeclared_research_protocol"
            if self.maturity.status == "mature_for_research"
            else "continue_prospective_collection"
        )
        if self.next_action != expected_action:
            raise ValueError("Phase 3G next action disagrees with maturity status")
        if self.maturity.research_model_fitting_allowed != (
            self.maturity.status == "mature_for_research"
        ):
            raise ValueError("Embedded maturity permission is inconsistent")
        if self.maturity.paper_or_live_trading_allowed:
            raise ValueError("Embedded maturity assessment permits trading")
        expected_deficits = maturity_deficits(self.maturity)
        if self.deficits != expected_deficits:
            raise ValueError("Maturity deficits do not match the frozen policy")
        expected_id = maturity_observation_id(
            observed_at=self.observed_at,
            workflow_run_id=self.workflow_run_id,
            source_commit_sha=self.source_commit_sha,
            market_snapshot_sha256=self.market_snapshot_sha256,
            semantic_dataset_sha256=self.semantic_dataset_sha256,
            semantic_ledger_head_sha256=self.semantic_ledger_head_sha256,
            maturity=self.maturity,
        )
        if self.observation_id != expected_id:
            raise ValueError("Maturity observation ID does not match its provenance")
        return self


@dataclass(frozen=True)
class SemanticMaturityRegistryState:
    head_sha256: str | None
    previous_record: SemanticMaturityObservation | None
    count: int
    observation_ids: frozenset[str]
    workflow_run_ids: frozenset[str]


def maturity_deficits(
    assessment: SemanticMaturityAssessment,
) -> SemanticMaturityDeficits:
    """Calculate exact remaining counts under the assessment's frozen policy."""

    policy = assessment.policy
    missing_classes = int(assessment.positive_target_count == 0) + int(
        assessment.negative_target_count == 0
    )
    return SemanticMaturityDeficits(
        semantic_records=max(
            policy.minimum_semantic_records - assessment.relevant_semantic_record_count,
            0,
        ),
        availability_dates=max(
            policy.minimum_unique_availability_dates - assessment.unique_availability_date_count,
            0,
        ),
        active_decision_rows=max(
            policy.minimum_active_decision_rows - assessment.active_decision_row_count,
            0,
        ),
        unique_sources=max(
            policy.minimum_unique_sources - assessment.unique_source_count,
            0,
        ),
        matured_labeled_rows=max(
            policy.minimum_matured_labeled_rows - assessment.matured_labeled_row_count,
            0,
        ),
        missing_target_classes=(missing_classes if policy.require_both_target_classes else 0),
    )


def maturity_observation_id(
    *,
    observed_at: datetime,
    workflow_run_id: str,
    source_commit_sha: str,
    market_snapshot_sha256: str,
    semantic_dataset_sha256: str,
    semantic_ledger_head_sha256: str | None,
    maturity: SemanticMaturityAssessment,
) -> str:
    return canonical_json_sha256(
        {
            "observed_at": observed_at.astimezone(UTC).isoformat(),
            "workflow_run_id": workflow_run_id,
            "source_commit_sha": source_commit_sha,
            "market_snapshot_sha256": market_snapshot_sha256,
            "semantic_dataset_sha256": semantic_dataset_sha256,
            "semantic_ledger_head_sha256": semantic_ledger_head_sha256,
            "maturity_assessment_id": maturity.assessment_id,
        }
    )


def make_maturity_observation(
    *,
    observed_at: datetime,
    workflow_run_id: str,
    source_commit_sha: str,
    market_snapshot_sha256: str,
    semantic_dataset_sha256: str,
    semantic_ledger_head_sha256: str | None,
    maturity: SemanticMaturityAssessment,
) -> SemanticMaturityObservation:
    normalized = observed_at.astimezone(UTC)
    return SemanticMaturityObservation(
        observation_id=maturity_observation_id(
            observed_at=normalized,
            workflow_run_id=workflow_run_id,
            source_commit_sha=source_commit_sha,
            market_snapshot_sha256=market_snapshot_sha256,
            semantic_dataset_sha256=semantic_dataset_sha256,
            semantic_ledger_head_sha256=semantic_ledger_head_sha256,
            maturity=maturity,
        ),
        observed_at=normalized,
        workflow_run_id=workflow_run_id,
        source_commit_sha=source_commit_sha,
        market_snapshot_sha256=market_snapshot_sha256,
        semantic_dataset_sha256=semantic_dataset_sha256,
        semantic_ledger_head_sha256=semantic_ledger_head_sha256,
        maturity=maturity,
        deficits=maturity_deficits(maturity),
        next_action=(
            "open_separate_predeclared_research_protocol"
            if maturity.status == "mature_for_research"
            else "continue_prospective_collection"
        ),
    )


def _canonical_line(record: SemanticMaturityObservation) -> bytes:
    payload = json.dumps(
        record.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )
    return (payload + "\n").encode("utf-8")


def maturity_record_sha256(record: SemanticMaturityObservation) -> str:
    return hashlib.sha256(_canonical_line(record)).hexdigest()


def verify_maturity_registry(path: str | Path) -> SemanticMaturityRegistryState:
    registry = Path(path)
    if not registry.exists():
        return SemanticMaturityRegistryState(None, None, 0, frozenset(), frozenset())
    previous_sha: str | None = None
    previous: SemanticMaturityObservation | None = None
    observation_ids: set[str] = set()
    workflow_run_ids: set[str] = set()
    count = 0
    with registry.open("rb") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if not raw.endswith(b"\n"):
                raise ValueError(f"Maturity registry line {line_number} is not newline-terminated")
            try:
                record = SemanticMaturityObservation.model_validate_json(raw)
            except Exception as exc:
                raise ValueError(f"Invalid maturity registry line {line_number}") from exc
            if record.previous_record_sha256 != previous_sha:
                raise ValueError(f"Maturity registry hash chain breaks at line {line_number}")
            if record.observation_id in observation_ids:
                raise ValueError(f"Duplicate maturity observation at line {line_number}")
            if record.workflow_run_id in workflow_run_ids:
                raise ValueError(f"Duplicate maturity workflow run at line {line_number}")
            if previous is not None and record.observed_at <= previous.observed_at:
                raise ValueError("Maturity observation times must be strictly increasing")
            previous_sha = maturity_record_sha256(record)
            previous = record
            observation_ids.add(record.observation_id)
            workflow_run_ids.add(record.workflow_run_id)
            count += 1
    return SemanticMaturityRegistryState(
        previous_sha,
        previous,
        count,
        frozenset(observation_ids),
        frozenset(workflow_run_ids),
    )


def append_maturity_observation(
    path: str | Path,
    observation: SemanticMaturityObservation,
) -> tuple[bool, str]:
    """Append one observation idempotently while preserving strict time order."""

    registry = Path(path)
    registry.parent.mkdir(parents=True, exist_ok=True)
    state = verify_maturity_registry(registry)
    if observation.observation_id in state.observation_ids:
        return False, state.head_sha256 or ""
    if observation.workflow_run_id in state.workflow_run_ids:
        raise ValueError("Workflow run already exists under another observation")
    if state.previous_record is not None and (
        observation.observed_at <= state.previous_record.observed_at
    ):
        raise ValueError("New maturity observation does not advance time")
    chained = observation.model_copy(update={"previous_record_sha256": state.head_sha256})
    payload = _canonical_line(chained)
    descriptor = os.open(
        registry,
        os.O_WRONLY | os.O_CREAT | os.O_APPEND,
        0o600,
    )
    try:
        os.write(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    head = hashlib.sha256(payload).hexdigest()
    verified = verify_maturity_registry(registry)
    if verified.head_sha256 != head:
        raise RuntimeError("Maturity registry head changed after append")
    return True, head
