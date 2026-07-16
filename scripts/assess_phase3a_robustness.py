from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from hybrid_trader.candidate_robustness import assess_candidate_robustness
from hybrid_trader.robustness_policy import load_robustness_policy


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply the predeclared Phase 3A robustness gate to sealed predictions."
    )
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--cost-stress", type=Path, required=True)
    parser.add_argument("--trial-metrics", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    predictions = pd.read_csv(args.predictions, compression="infer", low_memory=False)
    cost_stress = pd.read_csv(args.cost_stress)
    trial_metrics = pd.read_csv(args.trial_metrics)
    policy = load_robustness_policy(args.policy)
    summary, regimes, assessment = assess_candidate_robustness(
        predictions,
        cost_stress,
        trial_metrics,
        policy,
    )

    args.output.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output / "robustness_summary.csv", index=False)
    regimes.to_csv(args.output / "regime_summary.csv", index=False)
    (args.output / "robustness_assessment.json").write_text(
        json.dumps(assessment, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.output / "prospective_decisions.jsonl").write_text("", encoding="utf-8")
    print(json.dumps(assessment, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
