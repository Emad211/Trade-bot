"""Assess one diversified longitudinal Phase 3J capture delta."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from hybrid_trader.phase3i_health import Phase3ISourceHealthAssessment
from hybrid_trader.phase3j import Phase3JPolicy, assess_phase3j_run, write_phase3j_assessment


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Assess a bounded Phase 3J diversified longitudinal capture."
    )
    parser.add_argument("root", type=Path)
    parser.add_argument("--before-health", type=Path, required=True)
    parser.add_argument("--after-health", type=Path, required=True)
    parser.add_argument("--max-new-calls", type=int, default=4)
    parser.add_argument("--max-total-tokens", type=int, default=8_000)
    parser.add_argument("--max-failed-calls", type=int, default=0)
    parser.add_argument("--max-attempts-per-call", type=int, default=4)
    parser.add_argument("--minimum-successful-sources", type=int, default=2)
    parser.add_argument("--minimum-new-semantic-sources", type=int, default=2)
    parser.add_argument("--minimum-new-assets", type=int, default=2)
    parser.add_argument("--maximum-pending-documents", type=int, default=100)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    before = Phase3ISourceHealthAssessment.model_validate_json(
        args.before_health.read_text(encoding="utf-8")
    )
    after = Phase3ISourceHealthAssessment.model_validate_json(
        args.after_health.read_text(encoding="utf-8")
    )
    policy = Phase3JPolicy(
        max_new_calls=args.max_new_calls,
        max_total_tokens=args.max_total_tokens,
        max_failed_calls=args.max_failed_calls,
        max_attempts_per_call=args.max_attempts_per_call,
        minimum_successful_sources=args.minimum_successful_sources,
        minimum_new_semantic_sources_when_active=args.minimum_new_semantic_sources,
        minimum_new_assets_when_active=args.minimum_new_assets,
        maximum_pending_semantic_documents=args.maximum_pending_documents,
    )
    assessment = assess_phase3j_run(
        args.root,
        before_health=before,
        after_health=after,
        policy=policy,
    )
    path = write_phase3j_assessment(assessment, args.output)
    print(path.read_text(encoding="utf-8"), end="")
    if assessment.status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
