import numpy as np
import pandas as pd
import pytest

from hybrid_trader.config import AppConfig, CostConfig, load_config
from hybrid_trader.evaluation import (
    choose_threshold,
    evaluate_exposure_as_strategy,
    evaluate_probabilities_as_strategy,
    run_sealed_benchmark,
)
from hybrid_trader.features import build_supervised_frame
from hybrid_trader.models import PriorProbabilityModel, RidgeLogisticModel
from hybrid_trader.splits import SplitSpec
from hybrid_trader.strategies import generate_trend_exposure


def _trading_frame(rows: int = 6) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=rows, freq="4h", tz="UTC")
    return pd.DataFrame(
        {
            "target_return": [0.01, -0.01, 0.02, -0.005, 0.01, 0.0][:rows],
            "realized_volatility": [0.5] * rows,
        },
        index=index,
    )


def test_exposure_strategy_charges_final_liquidation(config: AppConfig) -> None:
    frame = _trading_frame()
    exposure = np.full(len(frame), 0.2)
    result = evaluate_exposure_as_strategy(frame, exposure, config=config)
    expected_turnover = 0.4
    assert result.metrics["turnover"] == pytest.approx(expected_turnover)
    assert result.metrics["trading_cost"] == pytest.approx((0.2 + 0.2) * config.costs.one_way_rate)


def test_probabilities_map_to_long_flat(config: AppConfig) -> None:
    frame = _trading_frame()
    probabilities = np.array([0.7, 0.4, 0.8, 0.2, 0.9, 0.1])
    result = evaluate_probabilities_as_strategy(frame, probabilities, threshold=0.6, config=config)
    assert (result.frame.loc[probabilities < 0.6, "exposure"] == 0).all()
    assert result.frame["exposure"].max() <= config.risk.max_exposure


def test_higher_cost_never_improves_same_exposure(config: AppConfig) -> None:
    frame = _trading_frame()
    exposure = np.array([0.2, 0.0, 0.2, 0.0, 0.2, 0.0])
    base = evaluate_exposure_as_strategy(frame, exposure, config=config, cost_multiplier=1)
    stressed = evaluate_exposure_as_strategy(frame, exposure, config=config, cost_multiplier=2)
    assert stressed.metrics["net_return"] <= base.metrics["net_return"]


def test_multi_bar_holding_is_rejected(config: AppConfig) -> None:
    changed = config.model_copy(
        update={"labels": config.labels.model_copy(update={"holding_period_bars": 2})}
    )
    with pytest.raises(ValueError, match="one-bar"):
        evaluate_exposure_as_strategy(_trading_frame(), np.zeros(6), config=changed)


def test_threshold_selection_is_validation_only_and_conservative(config: AppConfig) -> None:
    frame = _trading_frame()
    probabilities = np.array([0.8, 0.8, 0.8, 0.8, 0.8, 0.8])
    threshold, table = choose_threshold(
        frame,
        probabilities,
        thresholds=(0.5, 0.6),
        min_entries=0,
        drawdown_penalty=0,
        config=config,
    )
    assert threshold == 0.6
    assert len(table) == 2


def test_sealed_benchmark_produces_models_trend_and_cost_stress(
    pit_ohlcv: pd.DataFrame,
) -> None:
    config = load_config("configs/btc_spot_4h_smoke.yaml")
    supervised, feature_columns = build_supervised_frame(pit_ohlcv, config)
    trend = generate_trend_exposure(pit_ohlcv, config)
    supervised["trend_desired_exposure"] = trend.loc[
        supervised.index, "desired_exposure"
    ].to_numpy()
    spec = SplitSpec(
        initial_train=120,
        calibration_size=30,
        validation_size=30,
        test_size=30,
        step_size=30,
        embargo=1,
    )
    metrics, predictions, stress = run_sealed_benchmark(
        supervised,
        feature_columns=feature_columns,
        model_factories=[lambda: PriorProbabilityModel(), lambda: RidgeLogisticModel()],
        split_spec=spec,
        config=config,
        thresholds=(0.5, 0.55, 0.6),
        min_entries=0,
        cost_multipliers=(1.0, 2.0),
    )
    assert {"trend", "prior", "ridge_logistic"}.issubset(metrics["model"].unique())
    assert not predictions.empty
    assert set(stress["cost_multiplier"]) == {1.0, 2.0}
    assert (metrics["test_rows"] == 30).all()


def test_zero_cost_config_has_zero_trading_cost() -> None:
    config = AppConfig(costs=CostConfig(fee_bps=0, slippage_bps=0))
    result = evaluate_exposure_as_strategy(_trading_frame(), np.full(6, 0.2), config=config)
    assert result.metrics["trading_cost"] == 0
