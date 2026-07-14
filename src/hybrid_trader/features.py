"""Leakage-aware feature engineering."""

import numpy as np
import pandas as pd

from hybrid_trader.config import AppConfig


def compute_features(data: pd.DataFrame, config: AppConfig) -> pd.DataFrame:
    """Create technical and risk features using only current/past bars."""

    result = data.copy()
    close = result["close"]
    high = result["high"]
    low = result["low"]

    result["simple_return"] = close.pct_change()
    result["log_return"] = np.log(close).diff()
    result["ema_fast"] = close.ewm(
        span=config.strategy.ema_fast, adjust=False, min_periods=config.strategy.ema_fast
    ).mean()
    result["ema_slow"] = close.ewm(
        span=config.strategy.ema_slow, adjust=False, min_periods=config.strategy.ema_slow
    ).mean()
    result["ema_ratio"] = result["ema_fast"] / result["ema_slow"] - 1.0

    previous_close = close.shift(1)
    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    result["atr"] = true_range.rolling(
        config.strategy.atr_window, min_periods=config.strategy.atr_window
    ).mean()
    result["atr_pct"] = result["atr"] / close

    # Shift rolling extrema by one bar so the current bar never defines its own breakout level.
    result["donchian_entry_high"] = (
        high.rolling(
            config.strategy.donchian_entry,
            min_periods=config.strategy.donchian_entry,
        )
        .max()
        .shift(1)
    )
    result["donchian_exit_low"] = (
        low.rolling(
            config.strategy.donchian_exit,
            min_periods=config.strategy.donchian_exit,
        )
        .min()
        .shift(1)
    )

    result["realized_volatility"] = (
        result["log_return"]
        .rolling(
            config.strategy.volatility_window,
            min_periods=config.strategy.volatility_window,
        )
        .std(ddof=0)
        * np.sqrt(config.market.periods_per_year)
    )

    volume_mean = result["volume"].rolling(30, min_periods=30).mean()
    volume_std = result["volume"].rolling(30, min_periods=30).std(ddof=0)
    result["volume_zscore"] = (result["volume"] - volume_mean) / volume_std.replace(0, np.nan)
    return result
