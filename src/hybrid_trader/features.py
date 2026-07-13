"""Leakage-aware feature engineering."""

from __future__ import annotations

import numpy as np
import pandas as pd

from hybrid_trader.config import AppConfig
from hybrid_trader.labels import LabelSpec, add_execution_labels


def compute_features(data: pd.DataFrame, config: AppConfig) -> pd.DataFrame:
    """Create technical and risk features using only current and past bars."""

    result = data.copy()
    close = result["close"]
    high = result["high"]
    low = result["low"]

    result["simple_return"] = close.pct_change()
    result["log_return"] = np.log(close).diff()
    for window in config.features.return_windows:
        result[f"log_return_{window}"] = np.log(close / close.shift(window))
    for window in config.features.volatility_windows:
        result[f"realized_vol_{window}"] = result["log_return"].rolling(
            window, min_periods=window
        ).std(ddof=0) * np.sqrt(config.market.periods_per_year)

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

    result["realized_volatility"] = result["log_return"].rolling(
        config.strategy.volatility_window,
        min_periods=config.strategy.volatility_window,
    ).std(ddof=0) * np.sqrt(config.market.periods_per_year)

    volume_mean = (
        result["volume"]
        .rolling(config.features.volume_window, min_periods=config.features.volume_window)
        .mean()
    )
    volume_std = (
        result["volume"]
        .rolling(config.features.volume_window, min_periods=config.features.volume_window)
        .std(ddof=0)
    )
    result["volume_zscore"] = (result["volume"] - volume_mean) / volume_std.replace(0, np.nan)
    result["bar_range_pct"] = (high - low) / close
    denominator = (high - low).replace(0, np.nan)
    result["close_location"] = (close - low) / denominator
    return result


def build_supervised_frame(data: pd.DataFrame, config: AppConfig) -> tuple[pd.DataFrame, list[str]]:
    """Build a finite core feature/label frame and return the exact feature contract."""

    featured = compute_features(data, config)
    labeled = add_execution_labels(
        featured,
        LabelSpec(
            execution_delay_bars=config.labels.execution_delay_bars,
            holding_period_bars=config.labels.holding_period_bars,
            positive_threshold_bps=config.labels.positive_threshold_bps,
        ),
    )
    requested = [
        *(f"log_return_{window}" for window in config.features.return_windows),
        *(f"realized_vol_{window}" for window in config.features.volatility_windows),
        "ema_ratio",
        "atr_pct",
        "volume_zscore",
        "bar_range_pct",
        "close_location",
    ]
    feature_columns = list(dict.fromkeys(requested))
    finite = np.isfinite(labeled[feature_columns].to_numpy(dtype=float)).all(axis=1)
    valid = finite & labeled["target_positive"].notna() & labeled["label_available_at"].notna()
    result = labeled.loc[valid].copy()
    if result.empty:
        raise ValueError("No supervised rows remain after feature warm-up and label alignment")
    return result, feature_columns
