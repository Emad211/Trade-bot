"""Conservative BTC spot long/flat trend baseline."""

import numpy as np
import pandas as pd

from hybrid_trader.config import AppConfig
from hybrid_trader.features import compute_features


def generate_trend_exposure(data: pd.DataFrame, config: AppConfig) -> pd.DataFrame:
    """Return features plus desired end-of-bar exposure.

    Exposure is a decision made at the current close and must be shifted by the
    execution/backtest layer before it earns a return.
    """

    frame = compute_features(data, config)
    entry = (
        (frame["close"] > frame["donchian_entry_high"])
        & (frame["ema_fast"] > frame["ema_slow"])
        & (frame["realized_volatility"] <= config.strategy.max_annualized_volatility)
    )
    exit_signal = (frame["close"] < frame["donchian_exit_low"]) | (
        frame["ema_fast"] < frame["ema_slow"]
    )

    active = False
    regime = np.zeros(len(frame), dtype=float)
    for idx, (should_enter, should_exit) in enumerate(
        zip(entry.fillna(False), exit_signal.fillna(False), strict=True)
    ):
        if active and should_exit:
            active = False
        elif not active and should_enter:
            active = True
        regime[idx] = 1.0 if active else 0.0

    volatility = frame["realized_volatility"].replace(0, np.nan)
    sized_exposure = (config.risk.target_annualized_volatility / volatility).clip(
        upper=config.risk.max_exposure
    )
    sized_exposure = sized_exposure.where(
        sized_exposure >= config.risk.min_exposure,
        0.0,
    )

    frame["entry_signal"] = entry.astype(bool)
    frame["exit_signal"] = exit_signal.astype(bool)
    frame["trend_regime"] = regime
    frame["desired_exposure"] = (pd.Series(regime, index=frame.index) * sized_exposure).fillna(0.0)
    return frame
