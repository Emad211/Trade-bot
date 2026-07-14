from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from hybrid_trader.phase2c import load_phase2c_spec


def verify_macro_gate(root: Path, spec_path: Path) -> dict[str, object]:
    spec = load_phase2c_spec(spec_path)
    registry = json.loads((root / "source_registry.json").read_text("utf-8"))
    quality = json.loads((root / "quality_report.json").read_text("utf-8"))
    missingness = quality["combined_missingness"]
    start, end = pd.Timestamp(spec.start), pd.Timestamp(spec.end)
    required = [
        ("fred", item.series_id, item.feature_name)
        for item in spec.fred_series
        if item.required
    ] + [
        ("stooq", item.symbol, item.feature_name)
        for item in spec.stooq_series
        if item.required
    ] + [
        ("yahoo", item.symbol, item.feature_name)
        for item in spec.yahoo_series
        if item.required
    ]
    if not required:
        raise ValueError("At least one required market-context series is needed")
    successful = {
        (item["provider"], item["instrument"]): item
        for item in registry["attempts"]
        if item["source_type"] == "market_context" and item["status"] == "success"
    }
    accepted = []
    for provider, instrument, feature_name in required:
        item = successful.get((provider, instrument))
        if item is None:
            raise ValueError(f"Required market-context source failed: {provider}:{instrument}")
        event_start = pd.Timestamp(item["event_start"])
        event_end = pd.Timestamp(item["event_end"])
        if event_start > start + pd.Timedelta(days=14):
            raise ValueError(f"{provider}:{instrument} starts too late")
        if event_end < end - pd.Timedelta(days=14):
            raise ValueError(f"{provider}:{instrument} is stale at the fixed endpoint")
        if item["row_count"] < 500:
            raise ValueError(f"{provider}:{instrument} has insufficient daily observations")
        ratio = float(missingness.get(feature_name, 1.0))
        if ratio > 0.05:
            raise ValueError(f"{feature_name} missingness exceeds 5%: {ratio:.4f}")
        accepted.append(
            {
                "provider": provider,
                "instrument": instrument,
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
    print(json.dumps(verify_macro_gate(args.root, args.spec), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
