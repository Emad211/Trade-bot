"""Deterministic semantic-state artifact lineage for Phase 3I."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hybrid_trader.event_capture_state import canonical_sha256

SemanticWorkflowName = Literal[
    "phase3e-longitudinal-events",
    "phase3h-avalai-pilot",
]

_WORKFLOW_PRIORITY: dict[str, int] = {
    "phase3e-longitudinal-events": 1,
    "phase3h-avalai-pilot": 2,
}


class SemanticStateCandidate(BaseModel):
    """One successful workflow artifact eligible for semantic-state restoration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    candidate_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    workflow_name: SemanticWorkflowName
    workflow_run_id: str = Field(pattern=r"^[0-9]+$")
    run_created_at: datetime
    run_completed_at: datetime
    source_commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    artifact_id: int = Field(ge=1)
    artifact_name: str = Field(min_length=1, max_length=200)
    artifact_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    artifact_created_at: datetime
    artifact_expired: bool = False

    @field_validator("run_created_at", "run_completed_at", "artifact_created_at")
    @classmethod
    def normalize_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Semantic state lineage timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_identity_and_time(self) -> SemanticStateCandidate:
        if self.run_completed_at < self.run_created_at:
            raise ValueError("Semantic state workflow completion precedes creation")
        if self.artifact_created_at < self.run_created_at:
            raise ValueError("Semantic state artifact predates its workflow run")
        if self.candidate_id != canonical_sha256(candidate_identity_payload(self)):
            raise ValueError("Semantic state candidate ID is not self-consistent")
        return self


class SemanticStateSelection(BaseModel):
    """Self-hashing result of the frozen newest-state selection policy."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    selection_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    selected_at: datetime
    selected_candidate: SemanticStateCandidate
    considered_candidate_ids: tuple[str, ...]
    rejected_candidate_ids: tuple[str, ...]
    policy: Literal["newest_verified_artifact_v1"] = "newest_verified_artifact_v1"

    @field_validator("selected_at")
    @classmethod
    def normalize_selected_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Semantic state selection time must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_selection_identity(self) -> SemanticStateSelection:
        considered = set(self.considered_candidate_ids)
        rejected = set(self.rejected_candidate_ids)
        if len(considered) != len(self.considered_candidate_ids):
            raise ValueError("Semantic state selection contains duplicate candidates")
        if self.selected_candidate.candidate_id not in considered:
            raise ValueError("Selected semantic state was not considered")
        if self.selected_candidate.candidate_id in rejected:
            raise ValueError("Selected semantic state is also marked rejected")
        if rejected != considered.difference({self.selected_candidate.candidate_id}):
            raise ValueError("Rejected semantic candidates do not reconcile")
        if self.selection_id != canonical_sha256(selection_identity_payload(self)):
            raise ValueError("Semantic state selection ID is not self-consistent")
        return self


def candidate_identity_payload(candidate: SemanticStateCandidate) -> dict[str, object]:
    payload = candidate.model_dump(mode="json", exclude={"candidate_id"})
    return {str(key): value for key, value in payload.items()}


def selection_identity_payload(selection: SemanticStateSelection) -> dict[str, object]:
    payload = selection.model_dump(mode="json", exclude={"selection_id"})
    return {str(key): value for key, value in payload.items()}


def make_semantic_state_candidate(
    *,
    workflow_name: SemanticWorkflowName,
    workflow_run_id: str,
    run_created_at: datetime,
    run_completed_at: datetime,
    source_commit_sha: str,
    artifact_id: int,
    artifact_name: str,
    artifact_digest: str,
    artifact_created_at: datetime,
    artifact_expired: bool = False,
) -> SemanticStateCandidate:
    candidate = SemanticStateCandidate.model_construct(
        candidate_id="0" * 64,
        schema_version="1.0",
        workflow_name=workflow_name,
        workflow_run_id=workflow_run_id,
        run_created_at=run_created_at,
        run_completed_at=run_completed_at,
        source_commit_sha=source_commit_sha,
        artifact_id=artifact_id,
        artifact_name=artifact_name,
        artifact_digest=artifact_digest,
        artifact_created_at=artifact_created_at,
        artifact_expired=artifact_expired,
    )
    payload = candidate.model_dump(mode="json")
    payload["candidate_id"] = canonical_sha256(candidate_identity_payload(candidate))
    return SemanticStateCandidate.model_validate(payload)


def _candidate_sort_key(candidate: SemanticStateCandidate) -> tuple[datetime, datetime, int, int]:
    return (
        candidate.artifact_created_at,
        candidate.run_completed_at,
        _WORKFLOW_PRIORITY[candidate.workflow_name],
        int(candidate.workflow_run_id),
    )


def select_semantic_state(
    candidates: tuple[SemanticStateCandidate, ...] | list[SemanticStateCandidate],
    *,
    selected_at: datetime,
    minimum_artifact_created_at: datetime | None = None,
) -> SemanticStateSelection:
    """Select the newest non-expired artifact under a stable, auditable ordering."""

    if selected_at.tzinfo is None:
        raise ValueError("selected_at must be timezone-aware")
    if minimum_artifact_created_at is not None and minimum_artifact_created_at.tzinfo is None:
        raise ValueError("minimum_artifact_created_at must be timezone-aware")
    candidate_ids = [candidate.candidate_id for candidate in candidates]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("Semantic state candidates contain duplicate identities")
    eligible = [candidate for candidate in candidates if not candidate.artifact_expired]
    if minimum_artifact_created_at is not None:
        cutoff = minimum_artifact_created_at.astimezone(UTC)
        eligible = [candidate for candidate in eligible if candidate.artifact_created_at >= cutoff]
    if not eligible:
        raise ValueError("No eligible semantic state artifact is available")
    selected = max(eligible, key=_candidate_sort_key)
    considered = tuple(sorted(candidate_ids))
    rejected = tuple(
        candidate_id for candidate_id in considered if candidate_id != selected.candidate_id
    )
    selection = SemanticStateSelection.model_construct(
        selection_id="0" * 64,
        schema_version="1.0",
        selected_at=selected_at,
        selected_candidate=selected,
        considered_candidate_ids=considered,
        rejected_candidate_ids=rejected,
        policy="newest_verified_artifact_v1",
    )
    payload = selection.model_dump(mode="json")
    payload["selection_id"] = canonical_sha256(selection_identity_payload(selection))
    return SemanticStateSelection.model_validate(payload)


def load_semantic_state_candidates(path: str | Path) -> tuple[SemanticStateCandidate, ...]:
    """Load a strict JSON array produced by the workflow-specific discovery step."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Semantic state candidates file must contain a JSON array")
    return tuple(SemanticStateCandidate.model_validate(item) for item in payload)


def write_semantic_state_selection(selection: SemanticStateSelection, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(selection.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return output
