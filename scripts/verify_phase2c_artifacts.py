"""Fail closed when a Phase 2C evidence bundle is incomplete."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pandas as pd

from hybrid_trader.data.snapshot import read_snapshot


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root: Path) -> dict[str, object]:
    required = [
        "source_registry.json",
        "quality_report.json",
        "combined_snapshot/data.csv.gz",
        "combined_snapshot/manifest.json",
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
    ]
    missing = [item for item in required if not (root / item).exists()]
    if missing:
        raise ValueError(f"Missing Phase 2C artifacts: {missing}")

    data, snapshot = read_snapshot(root / "combined_snapshot")
    registry = cast(
        dict[str, Any], json.loads((root / "source_registry.json").read_text("utf-8"))
    )
    attempts = cast(list[dict[str, Any]], registry["attempts"])
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
        raise ValueError(f"Only {len(spot_success)} independent spot sources succeeded")
    if not derivative_success:
        raise ValueError("No derivative feature family succeeded")
    if registry["combined_snapshot_sha256"] != snapshot.content_sha256:
        raise ValueError("Registry and combined snapshot SHA do not match")

    metrics = pd.read_csv(root / "benchmark/all_features/fold_metrics.csv")
    summary = pd.read_csv(root / "benchmark/all_features/summary.csv")
    stress = pd.read_csv(root / "benchmark/all_features/cost_stress.csv")
    required_models = {"trend", "prior", "ridge_logistic", "lightgbm", "catboost"}
    missing_models = required_models.difference(metrics["model"].unique())
    if missing_models:
        raise ValueError(f"Benchmark is missing models: {sorted(missing_models)}")
    if set(stress["cost_multiplier"].round(6)) != {1.0, 1.5, 2.0}:
        raise ValueError("Cost stress multipliers are incomplete")
    if summary.empty or metrics.empty or data.empty:
        raise ValueError("Phase 2C produced an empty core artifact")

    expected_report_hash = (root / "phase2c_report.sha256").read_text("utf-8").split()[0]
    actual_report_hash = _sha256(root / "phase2c_report.md")
    if expected_report_hash != actual_report_hash:
        raise ValueError("Report SHA-256 does not match")
    freeze = cast(
        dict[str, Any],
        json.loads((root / "prospective/freeze_candidate.json").read_text("utf-8")),
    )
    if freeze["status"] != "candidate_not_activated":
        raise ValueError("Historical automation must not activate a strategy")
    if (root / "prospective/decisions.jsonl").read_text("utf-8"):
        raise ValueError("Historical automation must not fabricate prospective decisions")

    verification: dict[str, object] = {
        "schema_version": "1.0",
        "combined_snapshot_sha256": snapshot.content_sha256,
        "rows": len(data),
        "successful_spot_sources": len(spot_success),
        "successful_derivative_features": sorted(
            {str(item["source_type"]) for item in derivative_success}
        ),
        "models": sorted(metrics["model"].unique().tolist()),
        "folds": int(metrics["fold"].nunique()),
        "report_sha256": actual_report_hash,
        "status": "verified",
    }
    (root / "verification.json").write_text(
        json.dumps(verification, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return verification


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.root), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
