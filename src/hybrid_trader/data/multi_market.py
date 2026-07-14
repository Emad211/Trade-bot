"""Cross-venue features, including local-currency premium."""

from __future__ import annotations

import numpy as np
import pandas as pd

from hybrid_trader.data.asof import merge_asof_features


def _close_events(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    required = {"close", "available_at"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{name} frame missing columns: {sorted(missing)}")
    return pd.DataFrame(
        {
            "available_at": pd.to_datetime(frame["available_at"], utc=True),
            name: frame["close"].to_numpy(float),
        }
    ).sort_values("available_at")


def add_local_market_premium(
    global_btc_quote: pd.DataFrame,
    local_btc_fiat: pd.DataFrame,
    local_stable_fiat: pd.DataFrame,
    *,
    tolerance: pd.Timedelta | None = None,
) -> pd.DataFrame:
    """Compute local BTC premium versus global BTC/stable x local stable/fiat."""

    if tolerance is None:
        tolerance = pd.Timedelta("8h")
    result = global_btc_quote.copy()
    local_btc = _close_events(local_btc_fiat, "local_btc_fiat")
    local_stable = _close_events(local_stable_fiat, "local_stable_fiat")
    result = merge_asof_features(
        result,
        local_btc,
        feature_columns=["local_btc_fiat"],
        tolerance=tolerance,
    )
    result = merge_asof_features(
        result,
        local_stable,
        feature_columns=["local_stable_fiat"],
        tolerance=tolerance,
    )
    implied = result["close"] * result["local_stable_fiat"]
    result["local_premium"] = result["local_btc_fiat"] / implied - 1.0
    result.loc[~np.isfinite(result["local_premium"]), "local_premium"] = np.nan
    return result
