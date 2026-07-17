from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from hybrid_trader.semantic_dataset import read_semantic_dataset
from hybrid_trader.semantic_monitor import (
    append_maturity_observation,
    make_maturity_observation,
    verify_maturity_registry,
)


def _utc(value: str) -> datetime:
    timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        raise ValueError("observed_at must include a timezone")
    return timestamp.astimezone(UTC)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Append one non-activating Phase 3G maturity observation."
    )
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--workflow-run-id", required=True)
    parser.add_argument("--source-commit-sha", required=True)
    args = parser.parse_args()

    _, manifest = read_semantic_dataset(args.dataset)
    observation = make_maturity_observation(
        observed_at=_utc(args.observed_at),
        workflow_run_id=args.workflow_run_id,
        source_commit_sha=args.source_commit_sha,
        market_snapshot_sha256=manifest.market_snapshot_sha256,
        semantic_dataset_sha256=manifest.content_sha256,
        semantic_ledger_head_sha256=manifest.semantic_ledger_head_sha256,
        maturity=manifest.maturity,
    )
    appended, head = append_maturity_observation(args.registry, observation)
    state = verify_maturity_registry(args.registry)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "appended": appended,
        "registry_count": state.count,
        "registry_head_sha256": head,
        "observation": observation.model_dump(mode="json"),
        "model_fitting_executed": False,
        "threshold_selection_executed": False,
        "prospective_decisions_created": False,
    }
    args.output.write_text(
        json.dumps(payload, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    checksum = hashlib.sha256(args.output.read_bytes()).hexdigest()
    args.output.with_name("PHASE3G_SHA256SUMS").write_text(
        f"{checksum}  {args.output.name}\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
