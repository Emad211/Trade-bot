from __future__ import annotations

import argparse
import json
from pathlib import Path

from hybrid_trader.phase3h import Phase3HPilotPolicy, write_phase3h_assessment


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Assess the latest bounded Phase 3H source-diversity pilot."
    )
    parser.add_argument("root", type=Path)
    parser.add_argument("--max-new-calls", type=int, default=4)
    parser.add_argument("--max-total-tokens", type=int, default=8_000)
    parser.add_argument("--max-failed-calls", type=int, default=0)
    parser.add_argument("--max-attempts-per-call", type=int, default=4)
    parser.add_argument("--minimum-successful-sources", type=int, default=2)
    parser.add_argument("--minimum-new-semantic-sources", type=int, default=2)
    parser.add_argument("--minimum-new-assets", type=int, default=2)
    parser.add_argument(
        "--required-new-source",
        action="append",
        dest="required_new_sources",
    )
    parser.add_argument(
        "--required-new-asset",
        action="append",
        dest="required_new_assets",
    )
    parser.add_argument("--minimum-relevance-rejections", type=int, default=1)
    args = parser.parse_args()

    policy = Phase3HPilotPolicy(
        max_new_calls=args.max_new_calls,
        max_total_tokens=args.max_total_tokens,
        max_failed_calls=args.max_failed_calls,
        max_attempts_per_call=args.max_attempts_per_call,
        minimum_successful_sources=args.minimum_successful_sources,
        minimum_new_semantic_sources=args.minimum_new_semantic_sources,
        minimum_new_assets=args.minimum_new_assets,
        required_new_sources=tuple(
            args.required_new_sources
            or (
                "bitcoin-optech-newsletters",
                "federal-reserve-monetary-policy",
            )
        ),
        required_new_assets=tuple(args.required_new_assets or ("BTC", "MARKET")),
        minimum_relevance_rejections=args.minimum_relevance_rejections,
    )
    path = write_phase3h_assessment(args.root, policy=policy)
    assessment = json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps(assessment, sort_keys=True, indent=2))
    if assessment["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
