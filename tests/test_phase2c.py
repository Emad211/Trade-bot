from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from hybrid_trader.config import load_config
from hybrid_trader.data.fred_source import FredFetchResult
from hybrid_trader.data.point_in_time import add_bar_availability
from hybrid_trader.phase2c import (
    DerivativeVenueSpec,
    FredSeriesSpec,
    Phase2CSpec,
    SpotVenueSpec,
    run_phase2c,
)


def _bars(offset: float = 0.0, rows: int = 600) -> pd.DataFrame:
    timestamp = pd.date_range("2025-01-01", periods=rows, freq="4h", tz="UTC")
    steps = np.arange(rows)
    close = 30000 * np.exp(0.0003 * steps + 0.025 * np.sin(steps / 9)) + offset
    open_ = np.r_[close[0], close[:-1]]
    raw = pd.DataFrame(
        {
            "timestamp": timestamp,
            "open": open_,
            "high": np.maximum(open_, close) * 1.002,
            "low": np.minimum(open_, close) * 0.998,
            "close": close,
            "volume": 100 + 10 * np.cos(steps / 7),
        }
    )
    return add_bar_availability(raw, timeframe="4h", source_latency=timedelta(seconds=30))


class FakeSpot:
    def __init__(self, frame: pd.DataFrame) -> None:
        self.frame = frame

    def fetch_point_in_time(self, *args, **kwargs) -> pd.DataFrame:
        return self.frame.copy()


class FakeDerivatives:
    def __init__(self, rows: int = 600) -> None:
        self.event = pd.date_range("2025-01-01", periods=rows, freq="4h", tz="UTC")

    def fetch_funding_history(self, *args, **kwargs) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "event_time": self.event,
                "available_at": self.event + pd.Timedelta(minutes=1),
                "funding_rate": np.sin(np.arange(len(self.event)) / 20) / 10000,
            }
        )

    def fetch_open_interest_history(self, *args, **kwargs) -> pd.DataFrame:
        raise RuntimeError("unsupported in fake")

    def fetch_basis_history(self, *args, **kwargs) -> pd.DataFrame:
        raise RuntimeError("unsupported in fake")


class FakeFred:
    def __init__(self, spec: FredSeriesSpec) -> None:
        self.spec = spec

    def fetch(self, *, start, end, as_of) -> FredFetchResult:
        event = pd.date_range(start.normalize(), end.normalize(), freq="D", tz="UTC")
        frame = pd.DataFrame(
            {
                "event_time": event,
                "available_at": event + pd.Timedelta(days=1),
                self.spec.feature_name: np.linspace(100, 120, len(event)),
            }
        )
        frame = frame.loc[frame.available_at <= as_of]
        return FredFetchResult(
            frame=frame,
            url="https://example.invalid",
            payload_sha256="1" * 64,
            retrieved_at=datetime(2026, 1, 1, tzinfo=UTC),
            revision_policy="market_price_latest_vintage",
        )


def test_phase2c_injected_end_to_end(tmp_path: Path) -> None:
    first, second = _bars(), _bars(5.0)
    frames = {"a": first, "b": second}
    spec = Phase2CSpec(
        timeframe="4h",
        start=first.index[0].to_pydatetime(),
        end=first.index[-2].to_pydatetime(),
        as_of=(first["available_at"].iloc[-1] + pd.Timedelta(hours=1)).to_pydatetime(),
        spot_required_count=2,
        spot_sources=(SpotVenueSpec(exchange_id="a"), SpotVenueSpec(exchange_id="b")),
        derivative_sources=(DerivativeVenueSpec(exchange_id="d", symbol="BTC/USDT:USDT"),),
        minimum_derivative_features=1,
        fred_series=(FredSeriesSpec(series_id="TEST", feature_name="macro_test"),),
        max_pages=2,
    )
    result = run_phase2c(
        spec=spec,
        benchmark_config=load_config("configs/btc_spot_4h_smoke.yaml"),
        output_dir=tmp_path / "run",
        spot_factory=lambda venue: FakeSpot(frames[venue.exchange_id]),
        derivative_factory=lambda venue: FakeDerivatives(),
        fred_factory=lambda item: FakeFred(item),
    )
    assert len(result.successful_spot_sources) == 2
    assert result.successful_derivative_features == ("funding",)
    metrics = pd.read_csv(tmp_path / "run/benchmark/all_features/fold_metrics.csv")
    assert {"trend", "prior", "ridge_logistic"}.issubset(set(metrics.model))
    registry = json.loads((tmp_path / "run/source_registry.json").read_text())
    assert registry["combined_snapshot_sha256"] == result.combined_snapshot_sha256
    assert (tmp_path / "run/prospective/decisions.jsonl").read_text() == ""
