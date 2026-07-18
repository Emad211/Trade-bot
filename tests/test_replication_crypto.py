from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import pytest

from hybrid_trader.replication.crypto import (
    ContractLinearity,
    InstrumentVersion,
    LinearTwoLegInput,
    linear_two_leg_pnl,
    mark_index_basis,
    resolve_instrument_version,
)


def test_effective_dated_instrument_resolution() -> None:
    versions = [
        InstrumentVersion(
            venue_id="X",
            instrument_id="BTCUSDT",
            effective_from=datetime(2024, 1, 1, tzinfo=UTC),
            effective_to=datetime(2025, 1, 1, tzinfo=UTC),
            instrument_type="SWAP",
            base_currency="BTC",
            quote_currency="USDT",
            settlement_currency="USDT",
            contract_multiplier=1.0,
            linearity=ContractLinearity.LINEAR,
            tick_size=0.1,
            lot_size=0.001,
        )
    ]
    resolved = resolve_instrument_version(
        versions,
        venue_id="X",
        instrument_id="BTCUSDT",
        timestamp=datetime(2024, 6, 1, tzinfo=UTC),
    )
    assert resolved.linearity == ContractLinearity.LINEAR


def test_mark_index_basis_keeps_price_semantics_separate() -> None:
    result = mark_index_basis(pd.Series([101.0]), pd.Series([100.0]))
    assert result.iloc[0] == pytest.approx(0.01)


def test_two_leg_accounting_includes_all_costs() -> None:
    result = linear_two_leg_pnl(
        LinearTwoLegInput(
            spot_entry=100.0,
            spot_exit=110.0,
            spot_quantity=1.0,
            derivative_entry=105.0,
            derivative_exit=110.0,
            derivative_quantity=1.0,
            derivative_multiplier=1.0,
            derivative_side=-1,
            funding_cashflow=4.0,
            trading_fees=1.0,
            financing_cost=2.0,
        )
    )
    assert result["spot_pnl"] == pytest.approx(10.0)
    assert result["derivative_pnl"] == pytest.approx(-5.0)
    assert result["net_pnl"] == pytest.approx(6.0)
