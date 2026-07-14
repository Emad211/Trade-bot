from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd

from hybrid_trader.data.snapshot import read_snapshot
from hybrid_trader.data.timeframe import timeframe_to_timedelta
from hybrid_trader.phase2c import load_phase2c_spec


def verify_strict(root: Path, spec_path: Path) -> dict[str, object]:
    spec = load_phase2c_spec(spec_path)
    _, combined = read_snapshot(root / "combined_snapshot")
    registry = json.loads((root / "source_registry.json").read_text("utf-8"))
    quality = json.loads((root / "quality_report.json").read_text("utf-8"))
    interval = pd.Timedelta(timeframe_to_timedelta(spec.timeframe))
    start = pd.Timestamp(spec.start)
    end = pd.Timestamp(spec.end)
    expected = math.floor((end - start) / interval) + 1

    covered_spot = []
    for attempt in registry["attempts"]:
        if attempt["source_type"] != "spot_ohlcv" or attempt["status"] != "success":
            continue
        event_start = pd.Timestamp(attempt["event_start"])
        event_end = pd.Timestamp(attempt["event_end"])
        coverage = attempt["row_count"] / expected
        if event_start <= start + interval and event_end >= end - interval and coverage >= 0.95:
            covered_spot.append(
                {
                    "source_id": attempt["source_id"],
                    "row_count": attempt["row_count"],
                    "coverage_ratio": coverage,
                    "event_start": attempt["event_start"],
                    "event_end": attempt["event_end"],
                }
            )
    if len(covered_spot) < spec.spot_required_count:
        raise ValueError(f"Only {len(covered_spot)} spot sources cover >=95% of the fixed window")
    if combined.row_count / expected < 0.95:
        raise ValueError("Combined snapshot covers less than 95% of the fixed window")

    acceptable_pairs = []
    for item in quality.get("cross_venue", []):
        correlation = item.get("return_correlation")
        if item.get("overlap_ratio", 0) >= 0.95 and correlation is not None and correlation >= 0.95:
            acceptable_pairs.append(item)
    if not acceptable_pairs:
        raise ValueError("No cross-venue pair has >=95% overlap and >=0.95 return correlation")

    derivative = []
    for attempt in registry["attempts"]:
        if attempt["source_type"] not in {"funding", "open_interest", "basis"}:
            continue
        if attempt["status"] != "success":
            continue
        event_start = pd.Timestamp(attempt["event_start"])
        event_end = pd.Timestamp(attempt["event_end"])
        span_days = float((event_end - event_start) / pd.Timedelta(days=1))
        stale_days = float((end - event_end) / pd.Timedelta(days=1))
        if attempt["row_count"] >= 100 and span_days >= 180 and stale_days <= 7:
            derivative.append(
                {
                    "source_id": attempt["source_id"],
                    "source_type": attempt["source_type"],
                    "row_count": attempt["row_count"],
                    "span_days": span_days,
                    "stale_days": stale_days,
                }
            )
    if len({item["source_type"] for item in derivative}) < spec.minimum_derivative_features:
        raise ValueError("Derivative history is too short or stale for the fixed benchmark")

    metrics = pd.read_csv(root / "benchmark/all_features/fold_metrics.csv")
    expected_models = {"trend", "prior", "ridge_logistic", "lightgbm", "catboost"}
    if not expected_models.issubset(set(metrics.model.astype(str))):
        raise ValueError("Strict model matrix is incomplete")
    stress = pd.read_csv(root / "benchmark/all_features/cost_stress.csv")
    if not {1.0, 1.5, 2.0}.issubset(set(stress.cost_multiplier.astype(float))):
        raise ValueError("Strict cost matrix is incomplete")
    freeze = json.loads((root / "prospective/freeze_candidate.json").read_text("utf-8"))
    if freeze["status"] != "candidate_not_activated":
        raise ValueError("Historical run activated a candidate")
    if (root / "prospective/decisions.jsonl").read_text("utf-8").strip():
        raise ValueError("Historical run contains prospective decisions")

    result: dict[str, object] = {
        "verified": True,
        "fixed_window": {
            "start": spec.start,
            "end": spec.end,
            "expected_bars": expected,
        },
        "combined_snapshot_sha256": combined.content_sha256,
        "covered_spot_sources": covered_spot,
        "acceptable_cross_venue_pairs": acceptable_pairs,
        "acceptable_derivative_sources": derivative,
        "models": sorted(expected_models),
    }
    (root / "strict_verification.json").write_text(
        json.dumps(result, sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            verify_strict(args.root, args.spec),
            sort_keys=True,
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
