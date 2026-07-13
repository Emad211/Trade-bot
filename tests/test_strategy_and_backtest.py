import pandas as pd

from hybrid_trader.backtest import run_backtest
from hybrid_trader.config import AppConfig, CostConfig
from hybrid_trader.data.schema import normalize_ohlcv
from hybrid_trader.strategies import generate_trend_exposure


def test_signal_is_executed_one_bar_later(ohlcv: pd.DataFrame, config: AppConfig) -> None:
    data = normalize_ohlcv(ohlcv)
    signals = generate_trend_exposure(data, config)
    result = run_backtest(signals, config)
    expected = signals["desired_exposure"].shift(1).fillna(0.0)
    pd.testing.assert_series_equal(
        result.frame["executed_exposure"], expected, check_names=False
    )


def test_costs_never_improve_equity(ohlcv: pd.DataFrame, config: AppConfig) -> None:
    data = normalize_ohlcv(ohlcv)
    signals = generate_trend_exposure(data, config)
    costly = run_backtest(signals, config)
    free_config = config.model_copy(update={"costs": CostConfig(fee_bps=0, slippage_bps=0)})
    free = run_backtest(signals, free_config)
    assert costly.metrics["final_equity"] <= free.metrics["final_equity"]


def test_exposure_respects_cap(ohlcv: pd.DataFrame, config: AppConfig) -> None:
    data = normalize_ohlcv(ohlcv)
    signals = generate_trend_exposure(data, config)
    assert signals["desired_exposure"].max() <= config.risk.max_exposure
    assert signals["desired_exposure"].min() >= 0
