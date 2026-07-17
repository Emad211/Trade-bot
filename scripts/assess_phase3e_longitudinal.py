from __future__ import annotations

import argparse
import json
from pathlib import Path

from hybrid_trader.phase3e import Phase3EPolicy, write_phase3e_assessment


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Assess the latest longitudinal AvalAI capture delta."
    )
    parser.add_argument("root", type=Path)
    parser.add_argument("--max-new-calls-per-run", type=int, default=4)
    parser.add_argument("--max-total-tokens-per-run", type=int, default=8_000)
    parser.add_argument("--max-failed-calls-per-run", type=int, default=0)
    parser.add_argument("--max-attempts-per-call", type=int, default=4)
    parser.add_argument("--minimum-successful-sources", type=int, default=1)
    args = parser.parse_args()

    policy = Phase3EPolicy(
        max_new_calls_per_run=args.max_new_calls_per_run,
        max_total_tokens_per_run=args.max_total_tokens_per_run,
        max_failed_calls_per_run=args.max_failed_calls_per_run,
        max_attempts_per_call=args.max_attempts_per_call,
        minimum_successful_sources=args.minimum_successful_sources,
    )
    path = write_phase3e_assessment(args.root, policy=policy)
    assessment = json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps(assessment, sort_keys=True, indent=2))
    if assessment["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
