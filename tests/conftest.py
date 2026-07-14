from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from hybrid_trader.config import AppConfig


@pytest.fixture
def config() -> AppConfig:
    return AppConfig()


@pytest.fixture
def ohlcv() -> pd.DataFrame:
    bars = 500
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
def config_path() -> Path:
    return Path("configs/btc_spot_4h.yaml")
