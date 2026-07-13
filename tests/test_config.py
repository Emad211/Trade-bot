import pytest
from pydantic import ValidationError

from hybrid_trader.config import AppConfig, StrategyConfig, load_config


def test_loads_repository_config(config_path) -> None:
    loaded = load_config(config_path)
    assert loaded.market.symbol == "BTC/USD"
    assert loaded.costs.one_way_rate == pytest.approx(0.0025)


def test_rejects_fast_window_above_slow() -> None:
    with pytest.raises(ValidationError):
        StrategyConfig(ema_fast=100, ema_slow=20)


def test_config_is_immutable() -> None:
    config = AppConfig()
    with pytest.raises(ValidationError):
        config.costs = config.costs  # type: ignore[misc]
