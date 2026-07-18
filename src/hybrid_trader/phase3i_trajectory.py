"""Append-only Phase 3I semantic lineage and source-health trajectory."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hybrid_trader.event_capture_state import CaptureLock, canonical_sha256
from hybrid_trader.phase3g_trajectory import Phase3GTrajectoryEntry
from hybrid_trader.phase3i_health import Phase3ISourceHealthAssessment
from hybrid_trader.phase3i_lineage import SemanticStateSelection


class Phase3IHealthTrajectoryEntry(BaseModel):
    """One self-hashing source-health point linked to a Phase 3G maturity entry."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    entry_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    previous_entry_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    recorded_at: datetime
    as_of: datetime
    source_commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    phase3g_entry_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    phase3g_dataset_id: str = Field(pattern=r"^semantic-[0-9a-f]{12}$")
    phase3g_maturity_status: Literal[
        "mature_for_research",
        "insufficient_prospective_sample",
    ]
    phase3g_research_maturity_allowed: bool
    semantic_state_selection_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    semantic_workflow_name: Literal[
        "phase3e-longitudinal-events",
        "phase3h-avalai-pilot",
    ]
    semantic_workflow_run_id: str = Field(pattern=r"^[0-9]+$")
    semantic_artifact_id: int = Field(ge=1)
    semantic_artifact_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    semantic_artifact_created_at: datetime
    source_health_assessment_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_health_status: Literal["pass", "fail"]
    document_source_count: int = Field(ge=0)
    semantic_source_count: int = Field(ge=0)
    semantic_assets: tuple[str, ...]
    total_document_count: int = Field(ge=0)
    total_semantic_record_count: int = Field(ge=0)
    pending_semantic_document_count: int = Field(ge=0)
    metadata_drift_source_count: int = Field(ge=0)
    failed_required_source_count: int = Field(ge=0)
    failed_optional_source_count: int = Field(ge=0)
    model_fitting_authorized: bool = False
    paper_or_live_trading_authorized: bool = False
    prospective_decisions_created: bool = False

    @field_validator("recorded_at", "as_of", "semantic_artifact_created_at")
    @classmethod
    def normalize_timestamps(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Phase 3I trajectory timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_identity_and_safety(self) -> Phase3IHealthTrajectoryEntry:
        if (
            self.model_fitting_authorized
            or self.paper_or_live_trading_authorized
            or self.prospective_decisions_created
        ):
            raise ValueError("Phase 3I trajectory cannot authorize fitting or trading")
        expected_phase3g_permission = self.phase3g_maturity_status == "mature_for_research"
        if self.phase3g_research_maturity_allowed != expected_phase3g_permission:
            raise ValueError("Phase 3G maturity status and observed permission disagree")
        if self.entry_id != canonical_sha256(health_trajectory_identity_payload(self)):
            raise ValueError("Phase 3I trajectory entry ID is not self-consistent")
        return self


@dataclass(frozen=True)
class Phase3IHealthTrajectoryState:
    count: int
    head_sha256: str | None
    last_as_of: datetime | None
    phase3g_entry_ids: frozenset[str]
    semantic_selection_ids: frozenset[str]


def health_trajectory_identity_payload(
    entry: Phase3IHealthTrajectoryEntry,
) -> dict[str, object]:
    payload = entry.model_dump(mode="json", exclude={"entry_id"})
    return {str(key): value for key, value in payload.items()}


def load_last_phase3g_entry(path: str | Path) -> Phase3GTrajectoryEntry:
    ledger = Path(path)
    if not ledger.exists() or ledger.stat().st_size == 0:
        raise ValueError("Phase 3G trajectory is empty")
    payload = ledger.read_bytes()
    if not payload.endswith(b"\n"):
        raise ValueError("Phase 3G trajectory must end with a newline")
    return Phase3GTrajectoryEntry.model_validate_json(payload.splitlines()[-1])


def make_phase3i_health_trajectory_entry(
    phase3g_entry: Phase3GTrajectoryEntry,
    selection: SemanticStateSelection,
    health: Phase3ISourceHealthAssessment,
    *,
    recorded_at: datetime,
    previous_entry_sha256: str | None = None,
) -> Phase3IHealthTrajectoryEntry:
    """Bind state lineage and health to the exact current Phase 3G entry."""

    if health.semantic_ledger_head_sha256 != phase3g_entry.semantic_ledger_head_sha256:
        raise ValueError("Phase 3I health and Phase 3G semantic ledger heads disagree")
    selected = selection.selected_candidate
    candidate = Phase3IHealthTrajectoryEntry.model_construct(
        entry_id="0" * 64,
        schema_version="1.0",
        previous_entry_sha256=previous_entry_sha256,
        recorded_at=recorded_at,
        as_of=phase3g_entry.as_of,
        source_commit_sha=phase3g_entry.source_commit_sha,
        phase3g_entry_id=phase3g_entry.entry_id,
        phase3g_dataset_id=phase3g_entry.dataset_id,
        phase3g_maturity_status=phase3g_entry.maturity_status,
        phase3g_research_maturity_allowed=phase3g_entry.research_model_fitting_allowed,
        semantic_state_selection_id=selection.selection_id,
        semantic_workflow_name=selected.workflow_name,
        semantic_workflow_run_id=selected.workflow_run_id,
        semantic_artifact_id=selected.artifact_id,
        semantic_artifact_digest=selected.artifact_digest,
        semantic_artifact_created_at=selected.artifact_created_at,
        source_health_assessment_id=health.assessment_id,
        source_health_status=health.status,
        document_source_count=health.document_source_count,
        semantic_source_count=health.semantic_source_count,
        semantic_assets=health.semantic_assets,
        total_document_count=health.total_document_count,
        total_semantic_record_count=health.total_semantic_record_count,
        pending_semantic_document_count=health.total_pending_semantic_document_count,
        metadata_drift_source_count=len(health.metadata_drift_sources),
        failed_required_source_count=len(health.failed_required_sources),
        failed_optional_source_count=len(health.failed_optional_sources),
        model_fitting_authorized=False,
        paper_or_live_trading_authorized=False,
        prospective_decisions_created=False,
    )
    payload = candidate.model_dump(mode="json")
    payload["entry_id"] = canonical_sha256(health_trajectory_identity_payload(candidate))
    return Phase3IHealthTrajectoryEntry.model_validate(payload)


def verify_phase3i_health_trajectory(path: str | Path) -> Phase3IHealthTrajectoryState:
    ledger = Path(path)
    if not ledger.exists() or ledger.stat().st_size == 0:
        return Phase3IHealthTrajectoryState(0, None, None, frozenset(), frozenset())
    payload = ledger.read_bytes()
    if not payload.endswith(b"\n"):
        raise ValueError("Phase 3I health trajectory must end with a newline")
    previous: str | None = None
    last_as_of: datetime | None = None
    phase3g_ids: set[str] = set()
    selection_ids: set[str] = set()
    count = 0
    for raw in payload.splitlines():
        entry = Phase3IHealthTrajectoryEntry.model_validate_json(raw)
        if entry.previous_entry_sha256 != previous:
            raise ValueError("Phase 3I health trajectory chain link is invalid")
        if entry.phase3g_entry_id in phase3g_ids:
            raise ValueError("Phase 3I trajectory repeats a Phase 3G entry")
        if entry.semantic_state_selection_id in selection_ids:
            raise ValueError("Phase 3I trajectory repeats a semantic state selection")
        if last_as_of is not None and entry.as_of <= last_as_of:
            raise ValueError("Phase 3I trajectory as_of timestamps must increase")
        previous = entry.entry_id
        last_as_of = entry.as_of
        phase3g_ids.add(entry.phase3g_entry_id)
        selection_ids.add(entry.semantic_state_selection_id)
        count += 1
    return Phase3IHealthTrajectoryState(
        count=count,
        head_sha256=previous,
        last_as_of=last_as_of,
        phase3g_entry_ids=frozenset(phase3g_ids),
        semantic_selection_ids=frozenset(selection_ids),
    )


def append_phase3i_health_trajectory(
    path: str | Path,
    entry: Phase3IHealthTrajectoryEntry,
) -> Phase3IHealthTrajectoryState:
    ledger = Path(path)
    lock_path = ledger.with_name(f".{ledger.name}.lock")
    with CaptureLock(lock_path):
        state = verify_phase3i_health_trajectory(ledger)
        if entry.previous_entry_sha256 != state.head_sha256:
            raise ValueError("Phase 3I entry does not extend the current health trajectory")
        if entry.phase3g_entry_id in state.phase3g_entry_ids:
            raise ValueError("Phase 3G entry is already present in Phase 3I trajectory")
        if entry.semantic_state_selection_id in state.semantic_selection_ids:
            raise ValueError("Semantic state selection is already present in Phase 3I trajectory")
        if state.last_as_of is not None and entry.as_of <= state.last_as_of:
            raise ValueError("Phase 3I entry as_of must advance the health trajectory")
        ledger.parent.mkdir(parents=True, exist_ok=True)
        encoded = (
            json.dumps(
                entry.model_dump(mode="json"),
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
        descriptor = os.open(
            ledger,
            os.O_WRONLY | os.O_CREAT | os.O_APPEND,
            0o600,
        )
        try:
            os.write(descriptor, encoded)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    return verify_phase3i_health_trajectory(ledger)
