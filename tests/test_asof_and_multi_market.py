import numpy as np
import pandas as pd
import pytest

from hybrid_trader.data.asof import merge_asof_features
from hybrid_trader.data.multi_market import add_local_market_premium
from hybrid_trader.data.schema import MarketDataError


def test_asof_never_selects_future_feature(pit_ohlcv: pd.DataFrame) -> None:
    external = pd.DataFrame(
        {
            "available_at": [
                pit_ohlcv["available_at"].iloc[2],
                pit_ohlcv["available_at"].iloc[5],
            ],
            "funding_rate": [0.001, 0.002],
        }
    )
    result = merge_asof_features(pit_ohlcv.iloc[:8], external, feature_columns=["funding_rate"])
    assert np.isnan(result["funding_rate"].iloc[0])
    assert result["funding_rate"].iloc[4] == pytest.approx(0.001)
    assert result["funding_rate"].iloc[7] == pytest.approx(0.002)
    assert result["funding_rate__available_at"].iloc[7] <= result["available_at"].iloc[7]


def test_asof_rejects_duplicate_availability(pit_ohlcv: pd.DataFrame) -> None:
    timestamp = pit_ohlcv["available_at"].iloc[2]
    external = pd.DataFrame({"available_at": [timestamp, timestamp], "basis": [0.1, 0.2]})
    with pytest.raises(MarketDataError, match="unique"):
        merge_asof_features(pit_ohlcv, external, feature_columns=["basis"])


def test_asof_rejects_column_collision(pit_ohlcv: pd.DataFrame) -> None:
    external = pd.DataFrame(
        {
            "available_at": [pit_ohlcv["available_at"].iloc[0]],
            "close": [1.0],
        }
    )
    with pytest.raises(MarketDataError, match="already exist"):
        merge_asof_features(pit_ohlcv, external, feature_columns=["close"])


def test_local_premium_uses_all_three_available_legs(pit_ohlcv: pd.DataFrame) -> None:
    global_market = pit_ohlcv.iloc[:3].copy()
    local_btc = pit_ohlcv.iloc[:3].copy()
    local_stable = pit_ohlcv.iloc[:3].copy()
    global_market["close"] = [20_000.0, 21_000.0, 22_000.0]
    local_stable["close"] = [50_000.0, 51_000.0, 52_000.0]
    local_btc["close"] = global_market["close"] * local_stable["close"] * 1.05
    result = add_local_market_premium(global_market, local_btc, local_stable)
    np.testing.assert_allclose(result["local_premium"], 0.05)
