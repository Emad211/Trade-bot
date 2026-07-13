import builtins

import numpy as np
import pytest

from hybrid_trader.data.ccxt_source import CCXTOHLCVSource
from hybrid_trader.forecasting.timesfm_adapter import TimesFMForecaster


def _block_import(monkeypatch: pytest.MonkeyPatch, blocked: str) -> None:
    original_import = builtins.__import__

    def guarded_import(name: str, *args: object, **kwargs: object) -> object:
        if name == blocked:
            raise ImportError(f"blocked optional dependency: {blocked}")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)


def test_ccxt_adapter_has_actionable_optional_dependency_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_import(monkeypatch, "ccxt")
    with pytest.raises(RuntimeError, match="exchange"):
        CCXTOHLCVSource("kraken").fetch("BTC/USD", "4h", max_pages=1)


def test_timesfm_adapter_has_actionable_optional_dependency_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_import(monkeypatch, "timesfm")
    with pytest.raises(RuntimeError, match="forecast"):
        TimesFMForecaster().predict(np.array([0.0, 0.1], dtype=float), horizon=2)
