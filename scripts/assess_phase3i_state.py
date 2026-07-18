from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from hybrid_trader.phase3g_trajectory import verify_phase3g_trajectory
from hybrid_trader.phase3i_health import (
    Phase3ISourceHealthPolicy,
    assess_phase3i_source_health,
    write_phase3i_source_health,
)
from hybrid_trader.phase3i_lineage import SemanticStateSelection
from hybrid_trader.phase3i_trajectory import (
    append_phase3i_health_trajectory,
    load_last_phase3g_entry,
    make_phase3i_health_trajectory_entry,
    verify_phase3i_health_trajectory,
)


def _timestamp(value: str, *, label: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must be timezone-aware")
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Assess selected semantic state and append Phase 3I health trajectory."
    )
    parser.add_argument("--semantic-root", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--phase3g-trajectory", type=Path, required=True)
    parser.add_argument("--phase3i-trajectory", type=Path, required=True)
    parser.add_argument("--assessed-at", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--minimum-document-sources", type=int, default=4)
    parser.add_argument("--minimum-semantic-sources", type=int, default=4)
    parser.add_argument("--minimum-semantic-assets", type=int, default=3)
    parser.add_argument("--maximum-failed-required-sources", type=int, default=0)
    parser.add_argument("--maximum-failed-optional-sources", type=int, default=2)
    args = parser.parse_args()

    assessed_at = _timestamp(args.assessed_at, label="assessed_at")
    selection = SemanticStateSelection.model_validate_json(
        args.selection.read_text(encoding="utf-8")
    )
    policy = Phase3ISourceHealthPolicy(
        minimum_document_sources=args.minimum_document_sources,
        minimum_semantic_sources=args.minimum_semantic_sources,
        minimum_semantic_assets=args.minimum_semantic_assets,
        maximum_failed_required_sources=args.maximum_failed_required_sources,
        maximum_failed_optional_sources=args.maximum_failed_optional_sources,
    )
    health = assess_phase3i_source_health(
        args.semantic_root,
        assessed_at=assessed_at,
        policy=policy,
    )
    args.output.mkdir(parents=True, exist_ok=True)
    write_phase3i_source_health(health, args.output / "source_health.json")

    phase3g_state = verify_phase3g_trajectory(args.phase3g_trajectory)
    if phase3g_state.count < 1 or phase3g_state.head_sha256 is None:
        raise RuntimeError("Phase 3G trajectory is empty")
    phase3g_entry = load_last_phase3g_entry(args.phase3g_trajectory)
    phase3i_state = verify_phase3i_health_trajectory(args.phase3i_trajectory)
    entry = make_phase3i_health_trajectory_entry(
        phase3g_entry,
        selection,
        health,
        recorded_at=assessed_at,
        previous_entry_sha256=phase3i_state.head_sha256,
    )
    updated = append_phase3i_health_trajectory(args.phase3i_trajectory, entry)
    summary = {
        "schema_version": "1.0",
        "semantic_state_selection_id": selection.selection_id,
        "selected_workflow_name": selection.selected_candidate.workflow_name,
        "selected_workflow_run_id": selection.selected_candidate.workflow_run_id,
        "selected_artifact_id": selection.selected_candidate.artifact_id,
        "selected_artifact_digest": selection.selected_candidate.artifact_digest,
        "source_health_assessment_id": health.assessment_id,
        "source_health_status": health.status,
        "phase3g_entry_id": phase3g_entry.entry_id,
        "phase3i_entry_id": entry.entry_id,
        "phase3i_trajectory_count": updated.count,
        "phase3i_trajectory_head": updated.head_sha256,
        "document_source_count": health.document_source_count,
        "semantic_source_count": health.semantic_source_count,
        "semantic_assets": list(health.semantic_assets),
        "total_document_count": health.total_document_count,
        "total_semantic_record_count": health.total_semantic_record_count,
        "pending_semantic_document_count": health.total_pending_semantic_document_count,
        "metadata_drift_sources": list(health.metadata_drift_sources),
        "failed_required_sources": list(health.failed_required_sources),
        "failed_optional_sources": list(health.failed_optional_sources),
        "model_fitting_executed": False,
        "prospective_decisions_created": False,
    }
    (args.output / "phase3i_summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True, indent=2))
    if health.status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
