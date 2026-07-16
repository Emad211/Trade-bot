from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from hybrid_trader.data.snapshot import canonical_json_sha256


SCREENING_FLAG_NAMES = (
    "net_return_above_baseline",
    "net_return_above_naive",
    "sharpe_above_baseline",
    "brier_not_worse",
    "majority_positive_folds",
    "positive_after_2x_cost",
)


def _scalar(frame: pd.DataFrame, column: str) -> float | None:
    if frame.empty or column not in frame:
        return None
    value = frame.iloc[0][column]
    return None if pd.isna(value) else float(value)


def assess(root: Path) -> dict[str, Any]:
    manifest = json.loads((root / "foundation_manifest.json").read_text("utf-8"))
    comparison = pd.read_csv(root / "baseline_vs_foundation.csv")
    folds = pd.read_csv(root / "scenario_fold_metrics.csv")
    stress = pd.read_csv(root / "scenario_cost_stress.csv")
    ablation = pd.read_csv(root / "ablation_summary.csv")
    results: list[dict[str, Any]] = []
    for scenario in ("timesfm", "chronos", "timesfm_chronos"):
        for model in sorted(comparison.model.astype(str).unique()):
            row = comparison.loc[(comparison.scenario == scenario) & (comparison.model == model)]
            naive_row = comparison.loc[
                (comparison.scenario == "naive") & (comparison.model == model)
            ]
            fold_rows = folds.loc[(folds.scenario == scenario) & (folds.model == model)]
            stress_2x = stress.loc[
                (stress.scenario == scenario)
                & (stress.model == model)
                & (stress.cost_multiplier.astype(float) == 2.0)
            ]
            candidate_net = _scalar(row, "net_return")
            naive_net = _scalar(naive_row, "net_return")
            delta_net_vs_naive = (
                candidate_net - naive_net
                if candidate_net is not None and naive_net is not None
                else None
            )
            delta_net = _scalar(row, "delta_net_return")
            delta_sharpe = _scalar(row, "delta_sharpe")
            delta_brier = _scalar(row, "delta_brier")
            positive_fold_ratio = (
                float((fold_rows.net_return > 0).mean()) if not fold_rows.empty else None
            )
            stressed_net = float(stress_2x.net_return.mean()) if not stress_2x.empty else None
            flags = {
                "net_return_above_baseline": delta_net is not None and delta_net > 0,
                "net_return_above_naive": (
                    delta_net_vs_naive is not None and delta_net_vs_naive > 0
                ),
                "sharpe_above_baseline": delta_sharpe is not None and delta_sharpe > 0,
                "brier_not_worse": delta_brier is not None and delta_brier <= 0,
                "majority_positive_folds": (
                    positive_fold_ratio is not None and positive_fold_ratio >= 0.5
                ),
                "positive_after_2x_cost": stressed_net is not None and stressed_net > 0,
            }
            results.append(
                {
                    "scenario": scenario,
                    "model": model,
                    "net_return": candidate_net,
                    "naive_net_return": naive_net,
                    "delta_net_return_vs_naive": delta_net_vs_naive,
                    "delta_net_return": delta_net,
                    "delta_sharpe": delta_sharpe,
                    "delta_brier": delta_brier,
                    "positive_fold_ratio": positive_fold_ratio,
                    "mean_net_return_at_2x_cost": stressed_net,
                    "flags": flags,
                    "all_screening_flags": all(flags.values()),
                }
            )

    contributions: list[dict[str, Any]] = []
    for model in sorted(ablation.model.astype(str).unique()):
        all_row = ablation.loc[(ablation.ablation == "all_features") & (ablation.model == model)]
        for feature_model in ("timesfm", "chronos"):
            without = ablation.loc[
                (ablation.ablation == f"without_{feature_model}") & (ablation.model == model)
            ]
            all_net = _scalar(all_row, "mean_net_return")
            without_net = _scalar(without, "mean_net_return")
            contributions.append(
                {
                    "feature_model": feature_model,
                    "model": model,
                    "all_features_net_return": all_net,
                    "without_feature_net_return": without_net,
                    "incremental_net_return": (
                        all_net - without_net
                        if all_net is not None and without_net is not None
                        else None
                    ),
                }
            )

    candidates = [
        {"scenario": row["scenario"], "model": row["model"]}
        for row in results
        if row["all_screening_flags"]
    ]
    failed_flags = Counter(
        flag_name for row in results for flag_name, passed in row["flags"].items() if not passed
    )
    screening_outcome = "candidate_passed" if candidates else "no_candidate_passed"
    recommendation = "human_review_candidates" if candidates else "retain_as_research_only"

    identity = {
        "dataset_sha256": manifest["dataset_sha256"],
        "foundation_manifest_sha256": manifest["manifest_sha256"],
        "screening_results": results,
        "ablation_contributions": contributions,
        "screening_outcome": screening_outcome,
        "screening_candidates": candidates,
        "failed_flag_counts": {
            name: int(failed_flags.get(name, 0)) for name in SCREENING_FLAG_NAMES
        },
        "recommendation": recommendation,
    }
    assessment: dict[str, Any] = {
        "schema_version": "1.2",
        "status": "human_review_required",
        "assessment_id": canonical_json_sha256(identity),
        **identity,
        "promotion_policy": (
            "Screening flags are necessary but not sufficient. A candidate must improve "
            "net return over both its market-only baseline and the zero-return challenger, "
            "then pass independent human review and a separately frozen prospective paper "
            "period. When no candidate passes every flag, foundation features remain "
            "research-only."
        ),
    }
    (root / "foundation_assessment.json").write_text(
        json.dumps(assessment, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    pd.DataFrame(results).drop(columns="flags").to_csv(
        root / "foundation_screening.csv", index=False
    )
    pd.DataFrame(contributions).to_csv(root / "foundation_ablation_contributions.csv", index=False)
    return assessment


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    print(json.dumps(assess(args.root), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
