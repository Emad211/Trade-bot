from pathlib import Path

import numpy as np
import pandas as pd

from hybrid_trader.forecasting.base import ForecastOutput
from hybrid_trader.forecasting.batched import BatchRollingSpec, rolling_batched_features
from hybrid_trader.forecasting.rolling import (
    RollingForecastSpec,
    cache_rolling_features,
    read_cached_rolling_features,
)


class FakeBatchForecaster:
    def __init__(self) -> None:
        self.calls = 0

    def predict_batch(self, histories, horizon):
        self.calls += 1
        outputs = []
        for history in histories:
            base = float(history[-1])
            point = base + np.arange(1, horizon + 1, dtype=float)
            outputs.append(
                ForecastOutput(
                    point=point,
                    quantiles={0.1: point - 1.0, 0.9: point + 1.0},
                )
            )
        return outputs


def test_batched_rolling_uses_correct_horizon_step() -> None:
    index = pd.date_range("2026-01-01", periods=20, freq="4h", tz="UTC")
    series = pd.Series(np.arange(20, dtype=float), index=index)
    availability = pd.Series(index + pd.Timedelta(hours=4), index=index)
    model = FakeBatchForecaster()
    features = rolling_batched_features(
        series,
        model,
        BatchRollingSpec(
            context_length=4,
            min_history=4,
            horizon=3,
            stride=3,
            batch_size=2,
            prefix="fake",
            inference_latency_seconds=10,
        ),
        availability=availability,
    )
    assert len(features) == 17
    assert model.calls == 3
    # Origin is index 3, whose last value is 3. Steps are 4, 5, 6.
    assert features.loc[index[3], "fake_point_1"] == 4
    assert features.loc[index[4], "fake_point_1"] == 5
    assert features.loc[index[5], "fake_point_1"] == 6
    assert features.loc[index[5], "fake_forecast_age_bars"] == 2
    assert features.loc[index[5], "forecast_origin_at"] == index[3]
    assert features.loc[index[5], "forecast_origin_available_at"] == index[3] + pd.Timedelta(
        hours=4
    )
    assert features.loc[index[5], "forecast_step"] == 3
    assert features.loc[index[3], "available_at"] == index[3] + pd.Timedelta(hours=4, seconds=10)


def test_batched_features_round_trip_with_stride_greater_than_one(
    tmp_path: Path,
) -> None:
    index = pd.date_range("2026-01-01", periods=20, freq="4h", tz="UTC")
    series = pd.Series(np.arange(20, dtype=float), index=index)
    availability = pd.Series(index + pd.Timedelta(hours=4), index=index)
    batch_spec = BatchRollingSpec(
        context_length=4,
        min_history=4,
        horizon=3,
        stride=3,
        batch_size=2,
        prefix="fake",
        inference_latency_seconds=10,
    )
    features = rolling_batched_features(
        series,
        FakeBatchForecaster(),
        batch_spec,
        availability=availability,
    )
    cache_spec = RollingForecastSpec(
        context_length=batch_spec.context_length,
        min_history=batch_spec.min_history,
        horizon=batch_spec.horizon,
        stride=batch_spec.stride,
        prefix=batch_spec.prefix,
        inference_latency_seconds=batch_spec.inference_latency_seconds,
    )
    cache_rolling_features(
        features,
        tmp_path / "cache",
        dataset_sha256="a" * 64,
        model_id="fake/batch",
        model_revision="rev-1",
        spec=cache_spec,
    )
    loaded, _ = read_cached_rolling_features(tmp_path / "cache")
    pd.testing.assert_frame_equal(loaded, features, check_freq=False)
