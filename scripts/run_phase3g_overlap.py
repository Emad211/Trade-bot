from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

from hybrid_trader.config import load_config
from hybrid_trader.phase2c_contracts import SpotVenueSpec
from hybrid_trader.phase3g_market import Phase3GMarketSpec
from hybrid_trader.phase3g_overlap import run_phase3g_overlap
from hybrid_trader.semantic_dataset import SemanticMaturityPolicy
from hybrid_trader.semantic_features import SemanticFeatureSpec


def _aware_datetime(value: str, *, label: str) -> datetime:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
    return timestamp.tz_convert("UTC").to_pydatetime()


def _source_commit(value: str | None) -> str:
    resolved = value or os.environ.get("GITHUB_SHA", "")
    if len(resolved) != 40 or any(
        character not in "0123456789abcdef" for character in resolved
    ):
        raise ValueError("A lowercase 40-character source commit SHA is required")
    return resolved


def _market_spec(path: Path, *, as_of: datetime) -> Phase3GMarketSpec:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Phase 3G market config must contain a mapping")
    sources = payload.pop("spot_sources", None)
    if not isinstance(sources, list):
        raise ValueError("Phase 3G market config requires spot_sources")
    return Phase3GMarketSpec(
        **payload,
        as_of=as_of,
        spot_sources=tuple(SpotVenueSpec.model_validate(source) for source in sources),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run one prospective Phase 3G market/semantic overlap build."
    )
    parser.add_argument("--market-config", type=Path, required=True)
    parser.add_argument("--benchmark-config", type=Path, required=True)
    parser.add_argument("--semantic-state-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--trajectory-path", type=Path)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--source-commit-sha")
    parser.add_argument("--windows-hours", default="4,24,72")
    parser.add_argument("--allowed-assets", default="BTC,MARKET")
    parser.add_argument("--minimum-semantic-records", type=int, default=100)
    parser.add_argument("--minimum-availability-dates", type=int, default=30)
    parser.add_argument("--minimum-active-rows", type=int, default=50)
    parser.add_argument("--minimum-unique-sources", type=int, default=2)
    parser.add_argument("--minimum-matured-rows", type=int, default=500)
    args = parser.parse_args()

    as_of = _aware_datetime(args.as_of, label="as_of")
    windows = tuple(int(value) for value in args.windows_hours.split(",") if value)
    assets = tuple(value.strip().upper() for value in args.allowed_assets.split(",") if value)
    manifest = run_phase3g_overlap(
        market_spec=_market_spec(args.market_config, as_of=as_of),
        benchmark_config=load_config(args.benchmark_config),
        semantic_state_root=args.semantic_state_root,
        output_dir=args.output,
        trajectory_path=args.trajectory_path,
        source_commit_sha=_source_commit(args.source_commit_sha),
        feature_spec=SemanticFeatureSpec(
            windows_hours=windows,
            allowed_assets=assets,
        ),
        maturity_policy=SemanticMaturityPolicy(
            minimum_semantic_records=args.minimum_semantic_records,
            minimum_unique_availability_dates=args.minimum_availability_dates,
            minimum_active_decision_rows=args.minimum_active_rows,
            minimum_unique_sources=args.minimum_unique_sources,
            minimum_matured_labeled_rows=args.minimum_matured_rows,
        ),
        recorded_at=as_of,
    )
    print(json.dumps(manifest.model_dump(mode="json"), sort_keys=True, indent=2))
    if manifest.research_model_fitting_allowed:
        print(
            "Phase 3G maturity reached research threshold; a separate frozen "
            "experiment is still required before any model fitting."
        )
    else:
        print("Phase 3G remains below the predeclared research maturity threshold.")


if __name__ == "__main__":
    main()
