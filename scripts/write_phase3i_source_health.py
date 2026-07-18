"""Write a verified Phase 3I source-health assessment for one semantic state."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from hybrid_trader.phase3i_health import (
    Phase3ISourceHealthPolicy,
    assess_phase3i_source_health,
    write_phase3i_source_health,
)


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("assessed_at must be timezone-aware")
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify semantic ledgers and write one source-health assessment."
    )
    parser.add_argument("root", type=Path)
    parser.add_argument("--assessed-at", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--minimum-document-sources", type=int, default=4)
    parser.add_argument("--minimum-semantic-sources", type=int, default=4)
    parser.add_argument("--minimum-semantic-assets", type=int, default=3)
    parser.add_argument("--maximum-failed-required-sources", type=int, default=0)
    parser.add_argument("--maximum-failed-optional-sources", type=int, default=2)
    args = parser.parse_args()

    policy = Phase3ISourceHealthPolicy(
        minimum_document_sources=args.minimum_document_sources,
        minimum_semantic_sources=args.minimum_semantic_sources,
        minimum_semantic_assets=args.minimum_semantic_assets,
        maximum_failed_required_sources=args.maximum_failed_required_sources,
        maximum_failed_optional_sources=args.maximum_failed_optional_sources,
    )
    assessment = assess_phase3i_source_health(
        args.root,
        assessed_at=_timestamp(args.assessed_at),
        policy=policy,
    )
    path = write_phase3i_source_health(assessment, args.output)
    print(path.read_text(encoding="utf-8"), end="")
    if assessment.status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
