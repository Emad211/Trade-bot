from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from hybrid_trader.event_documents import (
    DocumentEnvelope,
    ProspectiveDocument,
    document_identity_payload,
    make_document_id,
)
from hybrid_trader.events import EventSignal
from hybrid_trader.semantic_dataset import (
    SemanticMaturityPolicy,
    assess_semantic_maturity,
    build_semantic_dataset,
    read_semantic_dataset,
    write_semantic_dataset,
)
from hybrid_trader.semantic_extraction import make_semantic_record
from hybrid_trader.semantic_features import (
    SemanticFeatureSpec,
    aggregate_semantic_features,
)


def _record(
    *,
    source_id: str,
    title: str,
    direction: str,
    event_time: datetime,
    available_at: datetime,
) -> object:
    text = title
    content_sha = __import__("hashlib").sha256(text.encode()).hexdigest()
    identity = document_identity_payload(
        source_id=source_id,
        canonical_url=f"https://example.com/{source_id}/{title.replace(' ', '-')}",
        title=title,
        published_at=event_time,
        content_sha256=content_sha,
    )
    document = ProspectiveDocument(
        document_id=make_document_id(**identity),
        source_id=source_id,
        canonical_url=identity["canonical_url"],
        title=title,
        published_at=event_time,
        retrieved_at=available_at - timedelta(minutes=2),
        available_at=available_at - timedelta(minutes=2),
        source_quality=0.9,
        asset_tags=("BTC",),
        content_sha256=content_sha,
        content_length=len(text.encode()),
        feed_payload_sha256="0" * 64,
    )
    signal = EventSignal(
        asset="BTC",
        event_time_utc=event_time,
        event_type="test_event",
        direction=direction,
        horizon="1d_3d",
        severity=0.5,
        novelty=0.6,
        source_quality=0.9,
        confidence=0.7,
        evidence_ids=(document.document_id,),
    )
    return make_semantic_record(
        DocumentEnvelope(document=document, text=text),
        signal,
        model_id="test-model",
        model_revision="test-model-v1",
        prompt="strict semantic test",
        inference_started_at=available_at - timedelta(minutes=1),
        inference_completed_at=available_at,
    )


def _market_frame() -> pd.DataFrame:
    index = pd.date_range("2026-07-17T08:00:00Z", periods=4, freq="4h")
    return pd.DataFrame(
        {
            "decision_time": index + pd.Timedelta(hours=4),
            "label_available_at": index + pd.to_timedelta([8, 12, 16, 20], unit="h"),
            "market_feature": [0.1, 0.2, -0.1, 0.3],
            "target_return": [0.01, -0.02, 0.03, -0.01],
            "target_positive": [1.0, 0.0, 1.0, 0.0],
        },
        index=index,
    )


def test_semantic_features_use_inference_availability_not_event_time() -> None:
    decision_index = pd.Index(["row"])
    decisions = pd.Series(
        [pd.Timestamp("2026-07-17T12:00:00Z")],
        index=decision_index,
    )
    available_record = _record(
        source_id="source-a",
        title="future dated but already observed",
        direction="bullish",
        event_time=datetime(2026, 7, 18, tzinfo=UTC),
        available_at=datetime(2026, 7, 17, 11, tzinfo=UTC),
    )
    unavailable_record = _record(
        source_id="source-b",
        title="old event retrieved later",
        direction="bearish",
        event_time=datetime(2026, 7, 16, tzinfo=UTC),
        available_at=datetime(2026, 7, 17, 13, tzinfo=UTC),
    )
    features = aggregate_semantic_features(
        decisions,
        [available_record, unavailable_record],
        SemanticFeatureSpec(windows_hours=(4,), allowed_assets=("BTC",)),
    )
    assert features.loc["row", "semantic_4h_event_count"] == 1.0
    assert features.loc["row", "semantic_4h_bullish_count"] == 1.0
    assert features.loc["row", "semantic_4h_bearish_count"] == 0.0


def test_semantic_dataset_excludes_labels_not_mature_at_as_of() -> None:
    frame = _market_frame()
    result = build_semantic_dataset(
        frame,
        [],
        as_of=pd.Timestamp("2026-07-17T18:00:00Z"),
        market_feature_columns=("market_feature",),
        feature_spec=SemanticFeatureSpec(windows_hours=(4,), allowed_assets=("BTC",)),
    )
    assert result.candidate_row_count == 2
    assert result.excluded_unmatured_label_count == 1
    assert len(result.frame) == 1
    assert result.frame["label_available_at"].max() <= pd.Timestamp(
        "2026-07-17T18:00:00Z"
    )


def test_maturity_gate_fails_current_small_sample_and_can_pass_low_test_policy() -> None:
    frame = _market_frame()
    records = [
        _record(
            source_id="source-a",
            title="event a",
            direction="bullish",
            event_time=datetime(2026, 7, 17, 7, tzinfo=UTC),
            available_at=datetime(2026, 7, 17, 9, tzinfo=UTC),
        ),
        _record(
            source_id="source-b",
            title="event b",
            direction="bearish",
            event_time=datetime(2026, 7, 18, 7, tzinfo=UTC),
            available_at=datetime(2026, 7, 18, 9, tzinfo=UTC),
        ),
    ]
    result = build_semantic_dataset(
        frame,
        records,
        as_of=pd.Timestamp("2026-07-18T08:00:00Z"),
        market_feature_columns=("market_feature",),
        feature_spec=SemanticFeatureSpec(windows_hours=(24,), allowed_assets=("BTC",)),
    )
    default = assess_semantic_maturity(result)
    assert default.status == "insufficient_prospective_sample"
    assert default.research_model_fitting_allowed is False
    assert default.paper_or_live_trading_allowed is False

    permissive = assess_semantic_maturity(
        result,
        policy=SemanticMaturityPolicy(
            minimum_semantic_records=1,
            minimum_unique_availability_dates=1,
            minimum_active_decision_rows=1,
            minimum_unique_sources=1,
            minimum_matured_labeled_rows=2,
        ),
    )
    assert permissive.status == "mature_for_research"
    assert permissive.research_model_fitting_allowed is True
    assert permissive.paper_or_live_trading_allowed is False


def test_semantic_dataset_artifact_is_idempotent_and_tamper_evident(
    tmp_path: Path,
) -> None:
    frame = _market_frame()
    record = _record(
        source_id="source-a",
        title="event a",
        direction="neutral",
        event_time=datetime(2026, 7, 17, 7, tzinfo=UTC),
        available_at=datetime(2026, 7, 17, 9, tzinfo=UTC),
    )
    spec = SemanticFeatureSpec(windows_hours=(24,), allowed_assets=("BTC",))
    result = build_semantic_dataset(
        frame,
        [record],
        as_of=pd.Timestamp("2026-07-18T08:00:00Z"),
        market_feature_columns=("market_feature",),
        feature_spec=spec,
    )
    kwargs = {
        "market_snapshot_sha256": "a" * 64,
        "document_ledger_head_sha256": "b" * 64,
        "semantic_ledger_head_sha256": "c" * 64,
        "semantic_record_count": 1,
        "as_of": pd.Timestamp("2026-07-18T08:00:00Z"),
        "feature_spec": spec,
        "source_commit_sha": "d" * 40,
        "created_at": datetime(2026, 7, 18, 8, tzinfo=UTC),
    }
    first = write_semantic_dataset(result, tmp_path / "dataset", **kwargs)
    second = write_semantic_dataset(result, tmp_path / "dataset", **kwargs)
    assert first == second
    loaded, manifest = read_semantic_dataset(tmp_path / "dataset")
    expected = result.frame.copy()
    expected.index.name = "timestamp"
    pd.testing.assert_frame_equal(loaded, expected, check_freq=False)
    assert manifest.content_sha256 == first.content_sha256

    manifest_path = tmp_path / "dataset" / "manifest.json"
    payload = json.loads(manifest_path.read_text())
    payload["content_sha256"] = "e" * 64
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="content hash"):
        read_semantic_dataset(tmp_path / "dataset")
