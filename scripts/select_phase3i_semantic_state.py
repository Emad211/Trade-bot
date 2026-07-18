from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from hybrid_trader.phase3i_lineage import (
    make_semantic_state_candidate,
    select_semantic_state,
    write_semantic_state_selection,
)


def _timestamp(value: str, *, label: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must be timezone-aware")
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Select the newest eligible Phase 3E/3H semantic-state artifact."
    )
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--selected-at", required=True)
    parser.add_argument("--minimum-artifact-created-at")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    raw = json.loads(args.candidates.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("Raw semantic candidates must be a JSON array")
    candidates = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("Each raw semantic candidate must be a JSON object")
        candidates.append(
            make_semantic_state_candidate(
                workflow_name=item["workflow_name"],
                workflow_run_id=str(item["workflow_run_id"]),
                run_created_at=_timestamp(item["run_created_at"], label="run_created_at"),
                run_completed_at=_timestamp(
                    item["run_completed_at"], label="run_completed_at"
                ),
                source_commit_sha=item["source_commit_sha"],
                artifact_id=int(item["artifact_id"]),
                artifact_name=item["artifact_name"],
                artifact_digest=item["artifact_digest"],
                artifact_created_at=_timestamp(
                    item["artifact_created_at"], label="artifact_created_at"
                ),
                artifact_expired=bool(item.get("artifact_expired", False)),
            )
        )
    selection = select_semantic_state(
        candidates,
        selected_at=_timestamp(args.selected_at, label="selected_at"),
        minimum_artifact_created_at=(
            _timestamp(
                args.minimum_artifact_created_at,
                label="minimum_artifact_created_at",
            )
            if args.minimum_artifact_created_at
            else None
        ),
    )
    path = write_semantic_state_selection(selection, args.output)
    print(path.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
