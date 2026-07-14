"""Leakage-safe as-of joins for alternative data."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from hybrid_trader.data.schema import MarketDataError


def merge_asof_features(
    market: pd.DataFrame,
    external: pd.DataFrame,
    *,
    feature_columns: Sequence[str],
    external_available_at: str = "available_at",
    market_decision_time: str = "available_at",
    prefix: str = "",
    provenance_column: str | None = None,
    tolerance: pd.Timedelta | None = None,
) -> pd.DataFrame:
    """Backward as-of join using availability rather than event date.

    The selected external observation timestamp is preserved in a provenance
    column so staleness and leakage can be audited row by row.
    """

    if market.empty:
        raise MarketDataError("Market frame cannot be empty")
    if external.empty:
        raise MarketDataError("External frame cannot be empty")
    if not feature_columns:
        raise MarketDataError("At least one external feature column is required")
    missing_market = {market_decision_time}.difference(market.columns)
    missing_external = {external_available_at, *feature_columns}.difference(external.columns)
    if missing_market:
        raise MarketDataError(f"Market frame missing: {sorted(missing_market)}")
    if missing_external:
        raise MarketDataError(f"External frame missing: {sorted(missing_external)}")

    left = market.copy()
    left[market_decision_time] = pd.to_datetime(left[market_decision_time], utc=True)
    left["__row_order"] = range(len(left))
    left_sorted = left.sort_values(market_decision_time)

    right = external.loc[:, [external_available_at, *feature_columns]].copy()
    right[external_available_at] = pd.to_datetime(right[external_available_at], utc=True)
    if right[external_available_at].isna().any():
        raise MarketDataError("External availability contains invalid timestamps")
    right = right.sort_values(external_available_at)
    if right[external_available_at].duplicated().any():
        raise MarketDataError("External availability timestamps must be unique")

    rename = {column: f"{prefix}{column}" for column in feature_columns}
    provenance = provenance_column or f"{prefix}{feature_columns[0]}__available_at"
    output_columns = {*rename.values(), provenance}
    overlap = output_columns.intersection(left.columns)
    if overlap:
        raise MarketDataError(f"As-of output columns already exist: {sorted(overlap)}")
    right = right.rename(columns={external_available_at: provenance, **rename})

    merged = pd.merge_asof(
        left_sorted,
        right,
        left_on=market_decision_time,
        right_on=provenance,
        direction="backward",
        tolerance=tolerance,
        allow_exact_matches=True,
    )
    leak = merged[provenance].notna() & (merged[provenance] > merged[market_decision_time])
    if leak.any():  # pragma: no cover - defensive assertion around pandas
        raise AssertionError("As-of join selected future information")
    merged = merged.sort_values("__row_order").drop(columns="__row_order")
    merged.index = market.index
    return merged
