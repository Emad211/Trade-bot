from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from hybrid_trader.config import load_config
from hybrid_trader.data.snapshot import read_snapshot
from hybrid_trader.event_ledger import verify_document_ledger
from hybrid_trader.features import build_supervised_frame
from hybrid_trader.semantic_dataset import (
    SemanticMaturityPolicy,
    build_semantic_dataset,
    write_semantic_dataset,
)
from hybrid_trader.semantic_features import SemanticFeatureSpec, load_semantic_ledger


def _utc(value: str, *, label: str) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
    return timestamp.tz_convert("UTC")


def _source_commit(value: str | None) -> str:
    resolved = value or os.environ.get("GITHUB_SHA", "")
    if len(resolved) != 40 or any(
        character not in "0123456789abcdef" for character in resolved
    ):
        raise ValueError("A lowercase 40-character source commit SHA is required")
    return resolved


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build an immutable point-in-time Phase 3F semantic dataset."
    )
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--document-ledger", type=Path, required=True)
    parser.add_argument("--semantic-ledger", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit-sha")
    parser.add_argument("--windows-hours", default="4,24,72")
    parser.add_argument("--allowed-assets", default="BTC,MARKET")
    parser.add_argument("--minimum-semantic-records", type=int, default=100)
    parser.add_argument("--minimum-availability-dates", type=int, default=30)
    parser.add_argument("--minimum-active-rows", type=int, default=50)
    parser.add_argument("--minimum-unique-sources", type=int, default=2)
    parser.add_argument("--minimum-matured-rows", type=int, default=500)
    args = parser.parse_args()

    as_of = _utc(args.as_of, label="as_of")
    windows = tuple(int(value) for value in args.windows_hours.split(",") if value)
    assets = tuple(value.strip().upper() for value in args.allowed_assets.split(",") if value)
    feature_spec = SemanticFeatureSpec(
        windows_hours=windows,
        allowed_assets=assets,
    )
    maturity_policy = SemanticMaturityPolicy(
        minimum_semantic_records=args.minimum_semantic_records,
        minimum_unique_availability_dates=args.minimum_availability_dates,
        minimum_active_decision_rows=args.minimum_active_rows,
        minimum_unique_sources=args.minimum_unique_sources,
        minimum_matured_labeled_rows=args.minimum_matured_rows,
    )

    market, market_manifest = read_snapshot(args.snapshot)
    config = load_config(args.config)
    supervised, market_features = build_supervised_frame(market, config)
    semantic = load_semantic_ledger(args.semantic_ledger)
    document_head, _, document_count, _ = verify_document_ledger(args.document_ledger)
    if document_count < semantic.state.count:
        raise ValueError("Semantic ledger contains more records than the document ledger")

    result = build_semantic_dataset(
        supervised,
        semantic.records,
        as_of=as_of,
        market_feature_columns=tuple(market_features),
        feature_spec=feature_spec,
    )
    manifest = write_semantic_dataset(
        result,
        args.output,
        market_snapshot_sha256=market_manifest.content_sha256,
        document_ledger_head_sha256=document_head,
        semantic_ledger_head_sha256=semantic.state.head_sha256,
        semantic_record_count=semantic.state.count,
        as_of=as_of,
        feature_spec=feature_spec,
        source_commit_sha=_source_commit(args.source_commit_sha),
        maturity_policy=maturity_policy,
        created_at=as_of.to_pydatetime(),
    )
    print(json.dumps(manifest.model_dump(mode="json"), sort_keys=True, indent=2))
    if manifest.maturity.status == "insufficient_prospective_sample":
        print(
            "Phase 3F maturity gate: insufficient prospective sample; "
            "model fitting remains disabled."
        )


if __name__ == "__main__":
    main()
