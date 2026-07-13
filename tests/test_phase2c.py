from datetime import UTC, datetime
from pathlib import Path

import pytest

from hybrid_trader.phase2c import Phase2CSpec, SourceContract, load_phase2c_spec


def _source(source_id: str, provider: str) -> SourceContract:
    return SourceContract(
        source_id=source_id,
        dataset_kind="spot_ohlcv",
        provider=provider,
        symbol="BTC/USD",
        timeframe="4h",
        retrieval_method="public api",
        event_time_policy="candle open",
        availability_time_policy="close plus latency",
        source_latency_seconds=30,
        revision_policy="append_only",
    )


def test_phase2c_plan_is_stable_and_requires_two_spot_sources(tmp_path: Path) -> None:
    spec = Phase2CSpec(
        experiment_name="unit",
        as_of=datetime(2026, 7, 13, tzinfo=UTC),
        since=datetime(2026, 3, 1, tzinfo=UTC),
        canonical_spot_source="left",
        sources=(_source("left", "A"), _source("right", "B")),
        model_matrix=("prior", "trend"),
    )
    assert len(spec.plan_sha256) == 64
    assert spec.plan_sha256 == Phase2CSpec.model_validate_json(spec.model_dump_json()).plan_sha256

    path = tmp_path / "spec.yaml"
    path.write_text(
        """
experiment_name: unit
as_of: 2026-07-13T00:00:00Z
since: 2026-03-01T00:00:00Z
canonical_spot_source: left
sources:
  - source_id: left
    dataset_kind: spot_ohlcv
    provider: A
    symbol: BTC/USD
    timeframe: 4h
    retrieval_method: public
    event_time_policy: open
    availability_time_policy: close plus latency
    source_latency_seconds: 30
    revision_policy: append_only
  - source_id: right
    dataset_kind: spot_ohlcv
    provider: B
    symbol: BTC/USD
    timeframe: 4h
    retrieval_method: public
    event_time_policy: open
    availability_time_policy: close plus latency
    source_latency_seconds: 30
    revision_policy: append_only
model_matrix: [prior, trend]
""".strip()
        + "\n"
    )
    loaded = load_phase2c_spec(path)
    assert loaded.plan_sha256 == load_phase2c_spec(path).plan_sha256

    with pytest.raises(ValueError, match="at least two"):
        Phase2CSpec(
            experiment_name="invalid",
            as_of=datetime(2026, 7, 13, tzinfo=UTC),
            since=datetime(2026, 3, 1, tzinfo=UTC),
            canonical_spot_source="left",
            sources=(_source("left", "A"),),
            model_matrix=("prior",),
        )


def test_source_contract_rejects_credentials() -> None:
    with pytest.raises(ValueError, match="credential-free"):
        SourceContract(
            source_id="private",
            dataset_kind="spot_ohlcv",
            provider="venue",
            symbol="BTC/USD",
            timeframe="4h",
            retrieval_method="private api",
            event_time_policy="open",
            availability_time_policy="close",
            source_latency_seconds=0,
            revision_policy="unknown",
            credentials_required=True,
        )
