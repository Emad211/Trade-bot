from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hybrid_trader.replication.factor_audit import (
    annualized_metrics,
    compare_factor_vintages,
    volatility_managed_returns,
)


def test_compare_factor_vintages_detects_revision() -> None:
    dates = pd.date_range("2000-01-31", periods=4, freq="ME", tz="UTC")
    original = pd.DataFrame({"date": dates, "tsmom": [0.01, -0.02, 0.03, 0.04]})
    maintained = pd.DataFrame({"date": dates, "tsmom": [0.01, -0.01, 0.03, 0.04]})
    result = compare_factor_vintages(original, maintained)[0]
    assert result.changed_count == 1
    assert result.max_absolute_difference == pytest.approx(0.01)


def test_annualized_metrics_reports_drawdown() -> None:
    metrics = annualized_metrics(pd.Series([0.10, -0.20, 0.10, 0.05]))
    assert metrics["count"] == 4
    assert metrics["maximum_drawdown"] < 0


def test_volatility_management_uses_lagged_variance() -> None:
    returns = pd.Series(np.linspace(-0.04, 0.05, 40))
    result = volatility_managed_returns(
        returns,
        variance_lookback=6,
        calibration_observations=20,
        max_leverage=3.0,
    )
    assert result.loc[:5, "weight"].isna().all()
    assert result["weight"].dropna().abs().max() <= 3.0
    assert result.loc[20:, "calibration"].eq(False).all()
