from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from hybrid_trader.data.snapshot import read_snapshot
from hybrid_trader.forecasting.rolling import read_cached_rolling_features

REQUIRED = (
    "feature_caches/naive/manifest.json",
    "feature_caches/timesfm/manifest.json",
    "feature_caches/chronos/manifest.json",
    "scenario_summary.csv",
    "scenario_fold_metrics.csv",
    "scenario_cost_stress.csv",
    "baseline_vs_foundation.csv",
    "ablation_summary.csv",
    "foundation_manifest.json",
    "prospective_decisions.jsonl",
)


def verify(root: Path, baseline_root: Path) -> dict[str, object]:
    missing = [item for item in REQUIRED if not (root / item).exists()]
    if missing:
        raise ValueError(f"Missing foundation artifacts: {missing}")
    _, snapshot = read_snapshot(baseline_root / "combined_snapshot")
    caches = {}
    for name in ("naive", "timesfm", "chronos"):
        _, manifest = read_cached_rolling_features(
            root / "feature_caches" / name,
            expected_dataset_sha256=snapshot.content_sha256,
        )
        caches[name] = manifest
    if not caches["timesfm"].model_revision or not caches["chronos"].model_revision:
        raise ValueError("Foundation model revisions must be pinned")
    scenarios = pd.read_csv(root / "scenario_summary.csv")
    expected_scenarios = {"naive", "timesfm", "chronos", "timesfm_chronos"}
    if not expected_scenarios.issubset(set(scenarios.scenario.astype(str))):
        raise ValueError("Foundation scenario matrix is incomplete")
    expected_models = {"trend", "prior", "ridge_logistic", "lightgbm", "catboost"}
    if not expected_models.issubset(set(scenarios.model.astype(str))):
        raise ValueError("Foundation model matrix is incomplete")
    stress = pd.read_csv(root / "scenario_cost_stress.csv")
    if not {1.0, 1.5, 2.0}.issubset(set(stress.cost_multiplier.astype(float))):
        raise ValueError("Foundation cost-stress matrix is incomplete")
    foundation = json.loads((root / "foundation_manifest.json").read_text("utf-8"))
    if foundation["status"] != "historical_challenger_not_activated":
        raise ValueError("Historical foundation run cannot activate trading")
    if foundation["dataset_sha256"] != snapshot.content_sha256:
        raise ValueError("Foundation manifest dataset mismatch")
    if (root / "prospective_decisions.jsonl").read_text("utf-8").strip():
        raise ValueError("Historical foundation run fabricated prospective decisions")
    result: dict[str, object] = {
        "verified": True,
        "dataset_sha256": snapshot.content_sha256,
        "timesfm_revision": caches["timesfm"].model_revision,
        "chronos_revision": caches["chronos"].model_revision,
        "scenarios": sorted(expected_scenarios),
        "models": sorted(expected_models),
        "manifest_sha256": foundation["manifest_sha256"],
    }
    (root / "verification.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--baseline-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.root, args.baseline_root), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
