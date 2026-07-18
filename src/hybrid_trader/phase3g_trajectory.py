"""Append-only maturity trajectory for prospective Phase 3G overlap datasets."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hybrid_trader.event_capture_state import CaptureLock, canonical_sha256
from hybrid_trader.phase3g_market import Phase3GMarketManifest
from hybrid_trader.semantic_dataset import SemanticDatasetManifest


class Phase3GTrajectoryEntry(BaseModel):
    """One immutable point on the prospective maturity trajectory."""

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
    market_run_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    market_snapshot_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    dataset_id: str = Field(pattern=r"^semantic-[0-9a-f]{12}$")
    dataset_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    semantic_ledger_head_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    relevant_semantic_record_count: int = Field(ge=0)
    unique_availability_date_count: int = Field(ge=0)
    unique_source_count: int = Field(ge=0)
    active_decision_row_count: int = Field(ge=0)
    matured_labeled_row_count: int = Field(ge=0)
    maturity_status: Literal[
        "mature_for_research",
        "insufficient_prospective_sample",
    ]
    research_model_fitting_allowed: bool
    paper_or_live_trading_allowed: bool = False
    prospective_decisions_created: bool = False

    @field_validator("recorded_at", "as_of")
    @classmethod
    def normalize_timestamps(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Phase 3G trajectory timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_safety_and_identity(self) -> Phase3GTrajectoryEntry:
        if self.paper_or_live_trading_allowed or self.prospective_decisions_created:
            raise ValueError("Phase 3G trajectory cannot authorize or record trading")
        expected_model_permission = self.maturity_status == "mature_for_research"
        if self.research_model_fitting_allowed != expected_model_permission:
            raise ValueError("Phase 3G maturity status and model permission disagree")
        if self.entry_id != canonical_sha256(trajectory_identity_payload(self)):
            raise ValueError("Phase 3G trajectory entry ID is not self-consistent")
        return self


@dataclass(frozen=True)
class Phase3GTrajectoryState:
    count: int
    head_sha256: str | None
    last_as_of: datetime | None
    dataset_ids: frozenset[str]


def trajectory_identity_payload(entry: Phase3GTrajectoryEntry) -> dict[str, object]:
    """Return the canonical self-hash payload for one trajectory entry."""

    payload = entry.model_dump(mode="json", exclude={"entry_id"})
    return {str(key): value for key, value in payload.items()}


def make_phase3g_trajectory_entry(
    market: Phase3GMarketManifest,
    dataset: SemanticDatasetManifest,
    *,
    recorded_at: datetime,
    previous_entry_sha256: str | None = None,
) -> Phase3GTrajectoryEntry:
    """Bind one semantic dataset to the exact prospective market snapshot."""

    if dataset.market_snapshot_sha256 != market.combined_snapshot_sha256:
        raise ValueError("Phase 3G market and semantic dataset snapshot hashes disagree")
    if dataset.source_commit_sha != market.source_commit_sha:
        raise ValueError("Phase 3G market and dataset source commits disagree")
    if dataset.as_of != market.as_of:
        raise ValueError("Phase 3G market and semantic dataset as_of values disagree")
    maturity = dataset.maturity
    payload: dict[str, object] = {
        "schema_version": "1.0",
        "previous_entry_sha256": previous_entry_sha256,
        "recorded_at": recorded_at,
        "as_of": dataset.as_of,
        "source_commit_sha": dataset.source_commit_sha,
        "market_run_id": market.run_id,
        "market_snapshot_sha256": market.combined_snapshot_sha256,
        "dataset_id": dataset.dataset_id,
        "dataset_content_sha256": dataset.content_sha256,
        "semantic_ledger_head_sha256": dataset.semantic_ledger_head_sha256,
        "relevant_semantic_record_count": maturity.relevant_semantic_record_count,
        "unique_availability_date_count": maturity.unique_availability_date_count,
        "unique_source_count": maturity.unique_source_count,
        "active_decision_row_count": maturity.active_decision_row_count,
        "matured_labeled_row_count": maturity.matured_labeled_row_count,
        "maturity_status": maturity.status,
        "research_model_fitting_allowed": maturity.research_model_fitting_allowed,
        "paper_or_live_trading_allowed": False,
        "prospective_decisions_created": False,
    }
    return Phase3GTrajectoryEntry(
        entry_id=canonical_sha256(payload),
        **payload,
    )


def verify_phase3g_trajectory(path: str | Path) -> Phase3GTrajectoryState:
    """Verify self-hashes, chain links, time ordering and safety invariants."""

    ledger = Path(path)
    if not ledger.exists() or ledger.stat().st_size == 0:
        return Phase3GTrajectoryState(0, None, None, frozenset())
    payload = ledger.read_bytes()
    if not payload.endswith(b"\n"):
        raise ValueError("Phase 3G trajectory must end with a newline")

    previous: str | None = None
    last_as_of: datetime | None = None
    dataset_ids: set[str] = set()
    count = 0
    for raw_line in payload.splitlines():
        entry = Phase3GTrajectoryEntry.model_validate_json(raw_line)
        if entry.previous_entry_sha256 != previous:
            raise ValueError("Phase 3G trajectory chain link is invalid")
        if entry.dataset_id in dataset_ids:
            raise ValueError("Phase 3G trajectory contains a duplicate dataset ID")
        if last_as_of is not None and entry.as_of <= last_as_of:
            raise ValueError("Phase 3G trajectory as_of timestamps must increase")
        previous = entry.entry_id
        last_as_of = entry.as_of
        dataset_ids.add(entry.dataset_id)
        count += 1
    return Phase3GTrajectoryState(
        count=count,
        head_sha256=previous,
        last_as_of=last_as_of,
        dataset_ids=frozenset(dataset_ids),
    )


def append_phase3g_trajectory(
    path: str | Path,
    entry: Phase3GTrajectoryEntry,
) -> Phase3GTrajectoryState:
    """Append one verified entry under an exclusive filesystem lock."""

    ledger = Path(path)
    lock_path = ledger.with_name(f".{ledger.name}.lock")
    with CaptureLock(lock_path):
        state = verify_phase3g_trajectory(ledger)
        if entry.previous_entry_sha256 != state.head_sha256:
            raise ValueError("Phase 3G entry does not extend the current ledger head")
        if entry.dataset_id in state.dataset_ids:
            raise ValueError("Phase 3G dataset is already present in the trajectory")
        if state.last_as_of is not None and entry.as_of <= state.last_as_of:
            raise ValueError("Phase 3G entry as_of must advance the trajectory")
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
    return verify_phase3g_trajectory(ledger)
