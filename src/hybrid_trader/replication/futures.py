"""Contract-aware futures return and roll audits."""

from __future__ import annotations

import numpy as np
import pandas as pd


def same_contract_returns(
    records: pd.DataFrame,
    *,
    contract_column: str = "contract_id",
    timestamp_column: str = "event_time",
    price_column: str = "settlement_price",
) -> pd.DataFrame:
    required = {contract_column, timestamp_column, price_column}
    missing = required - set(records.columns)
    if missing:
        raise ValueError(f"Missing futures fields: {sorted(missing)}")

    frame = records.copy()
    frame[timestamp_column] = pd.to_datetime(frame[timestamp_column], utc=True, errors="raise")
    frame[price_column] = pd.to_numeric(frame[price_column], errors="raise")
    if frame.duplicated([contract_column, timestamp_column]).any():
        raise ValueError("Duplicate contract/timestamp observations")
    prices = frame[price_column].to_numpy(dtype=float)
    if not np.isfinite(prices).all() or (prices <= 0).any():
        raise ValueError("Futures prices must be finite and positive")

    frame = frame.sort_values([contract_column, timestamp_column]).reset_index(drop=True)
    frame["previous_price"] = frame.groupby(contract_column, sort=False)[price_column].shift(1)
    frame["simple_return"] = frame[price_column] / frame["previous_price"] - 1.0
    frame["log_return"] = np.log(frame[price_column] / frame["previous_price"])
    frame["same_contract"] = frame["previous_price"].notna()
    return frame


def build_roll_ledger(
    selections: pd.DataFrame,
    *,
    product_column: str = "product_id",
    timestamp_column: str = "decision_time",
    contract_column: str = "contract_id",
) -> pd.DataFrame:
    required = {product_column, timestamp_column, contract_column}
    missing = required - set(selections.columns)
    if missing:
        raise ValueError(f"Missing selection fields: {sorted(missing)}")
    frame = selections.copy()
    frame[timestamp_column] = pd.to_datetime(frame[timestamp_column], utc=True, errors="raise")
    if frame.duplicated([product_column, timestamp_column]).any():
        raise ValueError("Duplicate product decisions")
    frame = frame.sort_values([product_column, timestamp_column]).reset_index(drop=True)
    frame["old_contract_id"] = frame.groupby(product_column, sort=False)[contract_column].shift(1)
    changed = frame["old_contract_id"].notna() & (
        frame["old_contract_id"] != frame[contract_column]
    )
    ledger = frame.loc[
        changed,
        [product_column, timestamp_column, "old_contract_id", contract_column],
    ].rename(columns={contract_column: "new_contract_id"})
    return ledger.reset_index(drop=True)


def assert_no_cross_contract_pnl(returns: pd.DataFrame) -> None:
    required = {"same_contract", "simple_return"}
    if not required.issubset(returns.columns):
        raise ValueError("Return frame lacks audit columns")
    invalid = returns.loc[~returns["same_contract"] & returns["simple_return"].notna()]
    if not invalid.empty:
        raise ValueError("Cross-contract price gaps were treated as returns")
