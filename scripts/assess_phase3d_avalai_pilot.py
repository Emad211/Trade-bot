from __future__ import annotations

import argparse
import json
from pathlib import Path

from hybrid_trader.phase3d import Phase3DPolicy, write_phase3d_assessment


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Assess the bounded prospective AvalAI data-quality pilot."
    )
    parser.add_argument("root", type=Path)
    parser.add_argument("--max-new-calls", type=int, default=2)
    parser.add_argument("--max-total-tokens", type=int, default=4_000)
    parser.add_argument("--max-failed-calls", type=int, default=0)
    parser.add_argument("--max-attempts-per-call", type=int, default=4)
    parser.add_argument("--minimum-provider-runs", type=int, default=2)
    parser.add_argument("--minimum-successful-sources", type=int, default=2)
    args = parser.parse_args()

    policy = Phase3DPolicy(
        max_new_calls=args.max_new_calls,
        max_total_tokens=args.max_total_tokens,
        max_failed_calls=args.max_failed_calls,
        max_attempts_per_call=args.max_attempts_per_call,
        minimum_provider_runs=args.minimum_provider_runs,
        minimum_successful_sources=args.minimum_successful_sources,
    )
    path = write_phase3d_assessment(args.root, policy=policy)
    assessment = json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps(assessment, sort_keys=True, indent=2))
    if assessment["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
