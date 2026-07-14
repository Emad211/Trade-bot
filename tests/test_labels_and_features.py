import numpy as np
import pandas as pd
import pytest

from hybrid_trader.config import AppConfig, LabelConfig
from hybrid_trader.features import build_supervised_frame, compute_features
from hybrid_trader.labels import LabelSpec, add_execution_labels


def test_label_uses_delayed_open_to_open_contract(pit_ohlcv: pd.DataFrame) -> None:
    result = add_execution_labels(
        pit_ohlcv,
        LabelSpec(execution_delay_bars=1, holding_period_bars=1),
    )
    expected = pit_ohlcv["open"].iloc[3] / pit_ohlcv["open"].iloc[2] - 1
    assert result["target_return"].iloc[0] == pytest.approx(expected)
    assert result["entry_time"].iloc[0] == pit_ohlcv.index[2]
    assert result["exit_time"].iloc[0] == pit_ohlcv.index[3]
    assert result["label_available_at"].iloc[0] == pit_ohlcv["open_available_at"].iloc[3]


def test_label_rejects_execution_before_late_decision(pit_ohlcv: pd.DataFrame) -> None:
    broken = pit_ohlcv.copy()
    broken["available_at"] = broken["available_at"] + pd.Timedelta(hours=9)
    with pytest.raises(ValueError, match="entry before"):
        add_execution_labels(
            broken,
            LabelSpec(execution_delay_bars=1, holding_period_bars=1),
        )


def test_features_shift_donchian_levels(normalized_ohlcv: pd.DataFrame, config: AppConfig) -> None:
    result = compute_features(normalized_ohlcv, config)
    index = config.strategy.donchian_entry
    expected = normalized_ohlcv["high"].iloc[:index].max()
    assert result["donchian_entry_high"].iloc[index] == pytest.approx(expected)


def test_supervised_frame_is_finite_and_chronological(
    pit_ohlcv: pd.DataFrame, config: AppConfig
) -> None:
    result, columns = build_supervised_frame(pit_ohlcv, config)
    assert result.index.is_monotonic_increasing
    assert np.isfinite(result[columns].to_numpy()).all()
    assert result["target_positive"].isin([0.0, 1.0]).all()
    assert (result["label_available_at"] > result["decision_time"]).all()


def test_positive_threshold_changes_target(pit_ohlcv: pd.DataFrame, config: AppConfig) -> None:
    strict = config.model_copy(
        update={
            "labels": LabelConfig(
                execution_delay_bars=1, holding_period_bars=1, positive_threshold_bps=500
            )
        }
    )
    baseline, _ = build_supervised_frame(pit_ohlcv, config)
    filtered, _ = build_supervised_frame(pit_ohlcv, strict)
    assert filtered["target_positive"].mean() <= baseline["target_positive"].mean()
