from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from hybrid_trader.config import load_config
from hybrid_trader.data.point_in_time import add_bar_availability
from hybrid_trader.event_documents import (
    DocumentEnvelope,
    ProspectiveDocument,
    document_identity_payload,
    make_document_id,
)
from hybrid_trader.event_ledger import append_documents
from hybrid_trader.events import EventSignal
from hybrid_trader.phase2c_contracts import SpotVenueSpec
from hybrid_trader.phase3g_market import Phase3GMarketSpec
from hybrid_trader.phase3g_overlap import run_phase3g_overlap
from hybrid_trader.phase3g_trajectory import verify_phase3g_trajectory
from hybrid_trader.semantic_dataset import read_semantic_dataset
from hybrid_trader.semantic_extraction import append_semantic_records, make_semantic_record
from hybrid_trader.semantic_features import SemanticFeatureSpec


def _bars(*, offset: float = 0.0, rows: int = 220) -> pd.DataFrame:
    index = pd.date_range("2026-06-01T00:00:00Z", periods=rows, freq="4h")
    steps = np.arange(rows, dtype=float)
    close = 60_000 * np.exp(0.0002 * steps + 0.01 * np.sin(steps / 8)) + offset
    raw = pd.DataFrame(
        {
            "timestamp": index,
            "open": np.r_[close[0], close[:-1]],
            "high": close * 1.002,
            "low": close * 0.998,
            "close": close,
            "volume": 100 + 5 * np.cos(steps / 7),
        }
    )
    return add_bar_availability(
        raw,
        timeframe="4h",
        source_latency=timedelta(seconds=30),
    )


class FakeSpot:
    def __init__(self, frame: pd.DataFrame) -> None:
        self.frame = frame

    def fetch_point_in_time(self, *args, **kwargs) -> pd.DataFrame:
        del args, kwargs
        return self.frame.copy()


def _state(root: Path, *, available_at: datetime) -> None:
    root.mkdir(parents=True)
    text = "Bitcoin protocol release observed prospectively"
    content_sha = hashlib.sha256(text.encode()).hexdigest()
    identity = document_identity_payload(
        source_id="bitcoin-core",
        canonical_url="https://example.com/bitcoin-release",
        title="Bitcoin release",
        published_at=available_at - timedelta(hours=2),
        content_sha256=content_sha,
    )
    document = ProspectiveDocument(
        document_id=make_document_id(**identity),
        source_id="bitcoin-core",
        canonical_url=identity["canonical_url"],
        title=identity["title"],
        published_at=identity["published_at"],
        retrieved_at=available_at - timedelta(minutes=2),
        available_at=available_at - timedelta(minutes=2),
        source_quality=0.95,
        asset_tags=("BTC",),
        content_sha256=content_sha,
        content_length=len(text.encode()),
        feed_payload_sha256="0" * 64,
    )
    signal = EventSignal(
        asset="BTC",
        event_time_utc=available_at - timedelta(hours=2),
        event_type="protocol_release",
        direction="bullish",
        horizon="1d_3d",
        severity=0.4,
        novelty=0.7,
        source_quality=0.95,
        confidence=0.65,
        evidence_ids=(document.document_id,),
    )
    semantic = make_semantic_record(
        DocumentEnvelope(document=document, text=text),
        signal,
        model_id="test-model",
        model_revision="test-model-v1",
        prompt="strict prospective test",
        inference_started_at=available_at - timedelta(minutes=1),
        inference_completed_at=available_at,
    )
    append_documents(root / "documents.jsonl", [document])
    append_semantic_records(root / "semantic_events.jsonl", [semantic])
    (root / "prospective_decisions.jsonl").write_text("", encoding="utf-8")


def _market_spec(as_of: datetime) -> Phase3GMarketSpec:
    return Phase3GMarketSpec(
        as_of=as_of,
        lookback_days=60,
        spot_sources=(
            SpotVenueSpec(exchange_id="venue-a", symbol="BTC/USD", required=True),
            SpotVenueSpec(exchange_id="venue-b", symbol="BTC/USDT", required=True),
        ),
        page_limit=50,
        max_pages=10,
    )


def test_phase3g_overlap_builds_active_rows_without_backfill(tmp_path: Path) -> None:
    primary = _bars()
    secondary = _bars(offset=2.0)
    as_of = primary["available_at"].iloc[-1].to_pydatetime() + timedelta(hours=1)
    semantic_available = as_of - timedelta(hours=20)
    state = tmp_path / "semantic-state"
    _state(state, available_at=semantic_available)
    frames = {"venue-a": primary, "venue-b": secondary}

    manifest = run_phase3g_overlap(
        market_spec=_market_spec(as_of),
        benchmark_config=load_config("configs/btc_spot_4h_smoke.yaml"),
        semantic_state_root=state,
        output_dir=tmp_path / "overlap",
        source_commit_sha="a" * 40,
        feature_spec=SemanticFeatureSpec(
            windows_hours=(4, 24, 72),
            allowed_assets=("BTC",),
        ),
        spot_factory=lambda venue: FakeSpot(frames[venue.exchange_id]),
        recorded_at=as_of,
    )

    assert manifest.active_decision_row_count > 0
    assert manifest.model_fitting_executed is False
    assert manifest.prospective_decisions_created is False
    assert manifest.credentials_used is False
    assert manifest.trajectory_count == 1
    trajectory = verify_phase3g_trajectory(
        tmp_path / "overlap" / "state" / "maturity_trajectory.jsonl"
    )
    assert trajectory.head_sha256 == manifest.trajectory_entry_id

    dataset, dataset_manifest = read_semantic_dataset(tmp_path / "overlap" / "dataset")
    assert dataset_manifest.market_snapshot_sha256 == manifest.market_snapshot_sha256
    count_columns = [
        column
        for column in dataset_manifest.semantic_feature_columns
        if column.endswith("_event_count")
    ]
    assert dataset[count_columns].to_numpy(dtype=float).sum() > 0
    before = dataset["decision_time"] < pd.Timestamp(semantic_available)
    assert dataset.loc[before, count_columns].to_numpy(dtype=float).sum() == 0


def test_phase3g_overlap_rejects_nonempty_decision_ledger_before_market_collection(
    tmp_path: Path,
) -> None:
    primary = _bars()
    as_of = primary["available_at"].iloc[-1].to_pydatetime() + timedelta(hours=1)
    state = tmp_path / "semantic-state"
    _state(state, available_at=as_of - timedelta(hours=20))
    (state / "prospective_decisions.jsonl").write_text('{"decision":"forbidden"}\n')

    with pytest.raises(RuntimeError, match="decision ledger is not empty"):
        run_phase3g_overlap(
            market_spec=_market_spec(as_of),
            benchmark_config=load_config("configs/btc_spot_4h_smoke.yaml"),
            semantic_state_root=state,
            output_dir=tmp_path / "overlap",
            source_commit_sha="b" * 40,
            spot_factory=lambda venue: FakeSpot(primary),
            recorded_at=as_of,
        )
    assert not (tmp_path / "overlap" / "market").exists()
