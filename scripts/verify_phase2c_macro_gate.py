from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from hybrid_trader.phase2c import load_phase2c_spec

REQUIRED_SERIES = {
    "NASDAQCOM": "nasdaq_composite",
    "DTWEXBGS": "usd_broad_index",
    "GOLDAMGBD228NLBM": "gold_usd_am",
}


def verify_macro_gate(root: Path, spec_path: Path) -> dict[str, object]:
    spec = load_phase2c_spec(spec_path)
    registry = json.loads((root / "source_registry.json").read_text("utf-8"))
    quality = json.loads((root / "quality_report.json").read_text("utf-8"))
    missingness = quality["combined_missingness"]
    start, end = pd.Timestamp(spec.start), pd.Timestamp(spec.end)
    accepted = []
    successful = {
        item["instrument"]: item
        for item in registry["attempts"]
        if item["source_type"] == "market_context" and item["status"] == "success"
    }
    for series_id, feature_name in REQUIRED_SERIES.items():
        item = successful.get(series_id)
        if item is None:
            raise ValueError(f"Required market-context series failed: {series_id}")
        event_start = pd.Timestamp(item["event_start"])
        event_end = pd.Timestamp(item["event_end"])
        if event_start > start + pd.Timedelta(days=14):
            raise ValueError(f"{series_id} starts too late")
        if event_end < end - pd.Timedelta(days=14):
            raise ValueError(f"{series_id} is stale at the fixed endpoint")
        if item["row_count"] < 500:
            raise ValueError(f"{series_id} has insufficient daily observations")
        ratio = float(missingness.get(feature_name, 1.0))
        if ratio > 0.05:
            raise ValueError(
                f"{feature_name} missingness exceeds 5%: {ratio:.4f}"
            )
        accepted.append(
            {
                "series_id": series_id,
                "feature_name": feature_name,
                "row_count": item["row_count"],
                "event_start": item["event_start"],
                "event_end": item["event_end"],
                "missing_ratio": ratio,
                "payload_sha256": item.get("payload_sha256"),
            }
        )
    result: dict[str, object] = {
        "verified": True,
        "required_market_context": accepted,
    }
    (root / "macro_gate_verification.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            verify_macro_gate(args.root, args.spec), sort_keys=True, indent=2
        )
    )


if __name__ == "__main__":
    main()
