"""Phase 3G prospective market/semantic overlap orchestration."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hybrid_trader.config import AppConfig
from hybrid_trader.data.snapshot import canonical_json_sha256, read_snapshot
from hybrid_trader.event_ledger import verify_document_ledger
from hybrid_trader.features import build_supervised_frame
from hybrid_trader.phase2c_sources import SpotFactory
from hybrid_trader.phase3g_market import (
    Phase3GMarketSpec,
    collect_phase3g_market,
)
from hybrid_trader.phase3g_trajectory import (
    append_phase3g_trajectory,
    make_phase3g_trajectory_entry,
    verify_phase3g_trajectory,
)
from hybrid_trader.semantic_dataset import (
    SemanticMaturityPolicy,
    build_semantic_dataset,
    write_semantic_dataset,
)
from hybrid_trader.semantic_features import SemanticFeatureSpec, load_semantic_ledger


class Phase3GOverlapManifest(BaseModel):
    """Cross-artifact identity for one prospective overlap build."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    overlap_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    as_of: datetime
    source_commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    market_run_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    market_snapshot_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    dataset_id: str = Field(pattern=r"^semantic-[0-9a-f]{12}$")
    dataset_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    document_ledger_head_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    semantic_ledger_head_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    document_count: int = Field(ge=0)
    semantic_record_count: int = Field(ge=0)
    trajectory_entry_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    trajectory_head_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    trajectory_count: int = Field(ge=1)
    active_decision_row_count: int = Field(ge=0)
    matured_labeled_row_count: int = Field(ge=0)
    maturity_status: str
    research_model_fitting_allowed: bool
    model_fitting_executed: bool = False
    prospective_decisions_created: bool = False
    credentials_used: bool = False
    created_at: datetime

    @field_validator("as_of", "created_at")
    @classmethod
    def normalize_timestamps(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Phase 3G overlap timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_safety(self) -> Phase3GOverlapManifest:
        if self.model_fitting_executed:
            raise ValueError("Phase 3G cannot execute model fitting")
        if self.prospective_decisions_created or self.credentials_used:
            raise ValueError("Phase 3G overlap violated its safety boundary")
        if self.trajectory_head_sha256 != self.trajectory_entry_id:
            raise ValueError("Phase 3G overlap must end at its new trajectory entry")
        return self


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def _require_empty_decisions(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError("Prospective decision ledger is missing")
    if path.read_text(encoding="utf-8").strip():
        raise RuntimeError("Prospective decision ledger is not empty")


def run_phase3g_overlap(
    *,
    market_spec: Phase3GMarketSpec,
    benchmark_config: AppConfig,
    semantic_state_root: str | Path,
    output_dir: str | Path,
    source_commit_sha: str,
    feature_spec: SemanticFeatureSpec | None = None,
    maturity_policy: SemanticMaturityPolicy | None = None,
    spot_factory: SpotFactory | None = None,
    trajectory_path: str | Path | None = None,
    recorded_at: datetime | None = None,
) -> Phase3GOverlapManifest:
    """Build one current overlap artifact and append its maturity trajectory."""

    root = Path(output_dir)
    market_root = root / "market"
    dataset_root = root / "dataset"
    overlap_path = root / "overlap_manifest.json"
    if overlap_path.exists() or market_root.exists() or dataset_root.exists():
        raise FileExistsError("Phase 3G overlap output already contains a run")
    root.mkdir(parents=True, exist_ok=True)

    state_root = Path(semantic_state_root)
    document_ledger = state_root / "documents.jsonl"
    semantic_ledger = state_root / "semantic_events.jsonl"
    decision_ledger = state_root / "prospective_decisions.jsonl"
    _require_empty_decisions(decision_ledger)
    document_head, _, document_count, _ = verify_document_ledger(document_ledger)
    semantic_state = load_semantic_ledger(semantic_ledger)
    if semantic_state.state.count > document_count:
        raise ValueError("Semantic ledger contains more records than the document ledger")

    if spot_factory is None:
        market_manifest = collect_phase3g_market(
            market_spec,
            market_root,
            source_commit_sha=source_commit_sha,
            retrieved_at=recorded_at,
        )
    else:
        market_manifest = collect_phase3g_market(
            market_spec,
            market_root,
            source_commit_sha=source_commit_sha,
            spot_factory=spot_factory,
            retrieved_at=recorded_at,
        )
    market_frame, snapshot_manifest = read_snapshot(market_root / "combined_snapshot")
    if snapshot_manifest.content_sha256 != market_manifest.combined_snapshot_sha256:
        raise RuntimeError("Phase 3G market snapshot disagrees with its manifest")

    supervised, market_features = build_supervised_frame(market_frame, benchmark_config)
    semantic_spec = feature_spec or SemanticFeatureSpec()
    build_result = build_semantic_dataset(
        supervised,
        semantic_state.records,
        as_of=market_spec.as_of,
        market_feature_columns=tuple(market_features),
        feature_spec=semantic_spec,
    )
    dataset_manifest = write_semantic_dataset(
        build_result,
        dataset_root,
        market_snapshot_sha256=market_manifest.combined_snapshot_sha256,
        document_ledger_head_sha256=document_head,
        semantic_ledger_head_sha256=semantic_state.state.head_sha256,
        semantic_record_count=semantic_state.state.count,
        as_of=market_spec.as_of,
        feature_spec=semantic_spec,
        source_commit_sha=source_commit_sha,
        maturity_policy=maturity_policy,
        created_at=market_spec.as_of,
    )

    trajectory_ledger = (
        Path(trajectory_path)
        if trajectory_path is not None
        else root / "state" / "maturity_trajectory.jsonl"
    )
    trajectory_before = verify_phase3g_trajectory(trajectory_ledger)
    timestamp = recorded_at or datetime.now(UTC)
    entry = make_phase3g_trajectory_entry(
        market_manifest,
        dataset_manifest,
        recorded_at=timestamp,
        previous_entry_sha256=trajectory_before.head_sha256,
    )
    trajectory_after = append_phase3g_trajectory(trajectory_ledger, entry)
    if trajectory_after.head_sha256 is None:
        raise AssertionError("Phase 3G trajectory append did not create a head")

    maturity = dataset_manifest.maturity
    identity = {
        "schema_version": "1.0",
        "as_of": market_spec.as_of,
        "source_commit_sha": source_commit_sha,
        "market_run_id": market_manifest.run_id,
        "market_snapshot_sha256": market_manifest.combined_snapshot_sha256,
        "dataset_id": dataset_manifest.dataset_id,
        "dataset_content_sha256": dataset_manifest.content_sha256,
        "document_ledger_head_sha256": document_head,
        "semantic_ledger_head_sha256": semantic_state.state.head_sha256,
        "document_count": document_count,
        "semantic_record_count": semantic_state.state.count,
        "trajectory_entry_id": entry.entry_id,
        "trajectory_head_sha256": trajectory_after.head_sha256,
        "trajectory_count": trajectory_after.count,
        "active_decision_row_count": maturity.active_decision_row_count,
        "matured_labeled_row_count": maturity.matured_labeled_row_count,
        "maturity_status": maturity.status,
        "research_model_fitting_allowed": maturity.research_model_fitting_allowed,
        "model_fitting_executed": False,
        "prospective_decisions_created": False,
        "credentials_used": False,
    }
    manifest = Phase3GOverlapManifest(
        overlap_id=canonical_json_sha256(identity),
        created_at=timestamp,
        **identity,
    )
    _write_json(overlap_path, manifest.model_dump(mode="json"))
    _write_json(root / "trajectory_entry.json", entry.model_dump(mode="json"))
    return manifest
