from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from hybrid_trader.config import AppConfig
from hybrid_trader.data.point_in_time import add_bar_availability
from hybrid_trader.data.schema import normalize_ohlcv


@pytest.fixture
def config() -> AppConfig:
    return AppConfig()


@pytest.fixture
def ohlcv() -> pd.DataFrame:
    bars = 700
    rng = np.random.default_rng(7)
    timestamps = pd.date_range("2024-01-01", periods=bars, freq="4h", tz="UTC")
    close = 30_000 * np.exp(np.cumsum(0.0005 + rng.normal(0, 0.012, bars)))
    open_ = np.r_[close[0], close[:-1]]
    spread = np.abs(rng.normal(0.008, 0.002, bars))
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": open_,
            "high": np.maximum(open_, close) * (1 + spread),
            "low": np.minimum(open_, close) * (1 - spread),
            "close": close,
            "volume": rng.lognormal(7, 0.3, bars),
        }
    )


@pytest.fixture
def normalized_ohlcv(ohlcv: pd.DataFrame) -> pd.DataFrame:
    return normalize_ohlcv(ohlcv)


@pytest.fixture
def pit_ohlcv(ohlcv: pd.DataFrame) -> pd.DataFrame:
    return add_bar_availability(
        ohlcv,
        timeframe="4h",
        source_latency=timedelta(seconds=30),
    )


@pytest.fixture
def config_path() -> Path:
    return Path("configs/btc_spot_4h.yaml")


@pytest.fixture
def smoke_config_path() -> Path:
    return Path("configs/btc_spot_4h_smoke.yaml")
