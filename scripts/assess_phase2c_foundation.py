from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from hybrid_trader.data.snapshot import canonical_json_sha256


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
            row = comparison.loc[
                (comparison.scenario == scenario) & (comparison.model == model)
            ]
            fold_rows = folds.loc[
                (folds.scenario == scenario) & (folds.model == model)
            ]
            stress_2x = stress.loc[
                (stress.scenario == scenario)
                & (stress.model == model)
                & (stress.cost_multiplier.astype(float) == 2.0)
            ]
            delta_net = _scalar(row, "delta_net_return")
            delta_sharpe = _scalar(row, "delta_sharpe")
            delta_brier = _scalar(row, "delta_brier")
            positive_fold_ratio = (
                float((fold_rows.net_return > 0).mean()) if not fold_rows.empty else None
            )
            stressed_net = (
                float(stress_2x.net_return.mean()) if not stress_2x.empty else None
            )
            flags = {
                "net_return_above_baseline": delta_net is not None and delta_net > 0,
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
        all_row = ablation.loc[
            (ablation.ablation == "all_features") & (ablation.model == model)
        ]
        for feature_model in ("timesfm", "chronos"):
            without = ablation.loc[
                (ablation.ablation == f"without_{feature_model}")
                & (ablation.model == model)
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

    identity = {
        "dataset_sha256": manifest["dataset_sha256"],
        "foundation_manifest_sha256": manifest["manifest_sha256"],
        "screening_results": results,
        "ablation_contributions": contributions,
    }
    assessment: dict[str, Any] = {
        "schema_version": "1.0",
        "status": "human_review_required",
        "assessment_id": canonical_json_sha256(identity),
        **identity,
        "promotion_policy": (
            "Flags are screening evidence only. Promotion requires independent "
            "human review and a separately frozen prospective paper period."
        ),
    }
    (root / "foundation_assessment.json").write_text(
        json.dumps(assessment, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    pd.DataFrame(results).drop(columns="flags").to_csv(
        root / "foundation_screening.csv", index=False
    )
    pd.DataFrame(contributions).to_csv(
        root / "foundation_ablation_contributions.csv", index=False
    )
    return assessment


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    print(json.dumps(assess(args.root), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
