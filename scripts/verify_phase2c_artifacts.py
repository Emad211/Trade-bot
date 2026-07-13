from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from hybrid_trader.data.snapshot import read_snapshot

REQUIRED = (
    "source_registry.json",
    "quality_report.json",
    "combined_snapshot/manifest.json",
    "combined_snapshot/data.csv.gz",
    "benchmark/all_features/fold_metrics.csv",
    "benchmark/all_features/summary.csv",
    "benchmark/all_features/cost_stress.csv",
    "benchmark/all_features/experiment.json",
    "ablation_summary.csv",
    "conditional_large_moves.csv",
    "fold_concentration.csv",
    "phase2c_report.md",
    "phase2c_report.sha256",
    "prospective/freeze_candidate.json",
    "prospective/decisions.jsonl",
)


def verify(root: Path) -> dict[str, object]:
    missing = [name for name in REQUIRED if not (root / name).exists()]
    if missing:
        raise ValueError(f"Missing artifacts: {missing}")
    _, snapshot = read_snapshot(root / "combined_snapshot")
    registry = json.loads((root / "source_registry.json").read_text())
    attempts = registry["attempts"]
    spot_success = [
        item
        for item in attempts
        if item["source_type"] == "spot_ohlcv" and item["status"] == "success"
    ]
    derivative_success = [
        item
        for item in attempts
        if item["source_type"] in {"funding", "open_interest", "basis"}
        and item["status"] == "success"
    ]
    if len(spot_success) < 2:
        raise ValueError("At least two successful spot sources are required")
    if not derivative_success:
        raise ValueError("At least one derivative feature family is required")
    if registry["combined_snapshot_sha256"] != snapshot.content_sha256:
        raise ValueError("Registry/snapshot SHA mismatch")
    metrics = pd.read_csv(root / "benchmark/all_features/fold_metrics.csv")
    expected_models = {"trend", "prior", "ridge_logistic", "lightgbm", "catboost"}
    models = set(metrics.model.astype(str))
    if not expected_models.issubset(models):
        raise ValueError(f"Missing models: {sorted(expected_models - models)}")
    stress = pd.read_csv(root / "benchmark/all_features/cost_stress.csv")
    if not {1.0, 1.5, 2.0}.issubset(set(stress.cost_multiplier.astype(float))):
        raise ValueError("Cost-stress matrix is incomplete")
    report = (root / "phase2c_report.md").read_bytes()
    expected_sha = (root / "phase2c_report.sha256").read_text().split()[0]
    if hashlib.sha256(report).hexdigest() != expected_sha:
        raise ValueError("Report SHA mismatch")
    freeze = json.loads((root / "prospective/freeze_candidate.json").read_text())
    if freeze["status"] != "candidate_not_activated":
        raise ValueError("Historical workflow cannot activate prospective trading")
    if (root / "prospective/decisions.jsonl").read_text().strip():
        raise ValueError("Historical workflow must not fabricate prospective decisions")
    result: dict[str, object] = {
        "verified": True,
        "combined_snapshot_sha256": snapshot.content_sha256,
        "registry_id": registry["registry_id"],
        "spot_sources": [item["source_id"] for item in spot_success],
        "derivative_features": [item["source_type"] for item in derivative_success],
        "models": sorted(models),
        "report_sha256": expected_sha,
    }
    (root / "verification.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.root), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
