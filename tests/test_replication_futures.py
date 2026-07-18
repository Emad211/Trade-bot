from __future__ import annotations

import pandas as pd
import pytest

from hybrid_trader.replication.futures import build_roll_ledger, same_contract_returns


def test_same_contract_return_excludes_roll_gap() -> None:
    frame = pd.DataFrame(
        {
            "contract_id": ["H24", "H24", "M24", "M24"],
            "event_time": pd.to_datetime(
                ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"], utc=True
            ),
            "settlement_price": [100.0, 101.0, 110.0, 111.0],
        }
    )
    result = same_contract_returns(frame)
    assert result.loc[result["contract_id"] == "M24", "simple_return"].iloc[0] != pytest.approx(
        110.0 / 101.0 - 1.0
    )
    assert pd.isna(result.loc[result["contract_id"] == "M24", "simple_return"].iloc[0])


def test_roll_ledger_records_contract_transition() -> None:
    selections = pd.DataFrame(
        {
            "product_id": ["CL", "CL", "CL"],
            "decision_time": pd.to_datetime(
                ["2024-01-31", "2024-02-29", "2024-03-31"], utc=True
            ),
            "contract_id": ["CLH24", "CLJ24", "CLJ24"],
        }
    )
    ledger = build_roll_ledger(selections)
    assert len(ledger) == 1
    assert ledger.iloc[0]["old_contract_id"] == "CLH24"
    assert ledger.iloc[0]["new_contract_id"] == "CLJ24"
