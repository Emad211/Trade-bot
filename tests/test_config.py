import pytest
from pydantic import ValidationError

from hybrid_trader.config import (
    AppConfig,
    EvaluationConfig,
    FeatureConfig,
    MarketConfig,
    RiskConfig,
    StrategyConfig,
    load_config,
)


def test_loads_repository_config(config_path) -> None:
    loaded = load_config(config_path)
    assert loaded.market.symbol == "BTC/USD"
    assert loaded.costs.one_way_rate == pytest.approx(0.0025)
    assert loaded.labels.execution_delay_bars == 1


def test_rejects_fast_window_above_slow() -> None:
    with pytest.raises(ValidationError):
        StrategyConfig(ema_fast=100, ema_slow=20)


def test_rejects_invalid_timeframe() -> None:
    with pytest.raises(ValidationError):
        MarketConfig(timeframe="hourly")


def test_rejects_unsorted_feature_windows() -> None:
    with pytest.raises(ValidationError):
        FeatureConfig(return_windows=(2, 1))


def test_rejects_duplicate_thresholds() -> None:
    with pytest.raises(ValidationError):
        EvaluationConfig(thresholds=(0.5, 0.5))


def test_rejects_exposure_floor_above_cap() -> None:
    with pytest.raises(ValidationError):
        RiskConfig(min_exposure=0.6, max_exposure=0.3)


def test_config_is_immutable() -> None:
    config = AppConfig()
    with pytest.raises(ValidationError):
        config.costs = config.costs  # type: ignore[misc]
