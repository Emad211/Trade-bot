from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from hybrid_trader.forecasting import (
    Chronos2Forecaster,
    ChronosSettings,
    NaiveReturnForecaster,
    TimesFMForecaster,
    TimesFMSettings,
)
from hybrid_trader.forecasting.rolling import (
    RollingForecastSpec,
    cache_rolling_features,
    read_cached_rolling_features,
    rolling_forecast_features,
)


class FakeTensor:
    def __init__(self, values: np.ndarray) -> None:
        self.values = values

    def detach(self) -> "FakeTensor":
        return self

    def cpu(self) -> "FakeTensor":
        return self

    def __array__(self, dtype=None):
        return np.asarray(self.values, dtype=dtype)


class FakeChronosPipeline:
    def predict_quantiles(self, **kwargs):
        horizon = kwargs["prediction_length"]
        quantiles = kwargs["quantile_levels"]
        values = np.zeros((1, horizon, len(quantiles)), dtype=float)
        for index, level in enumerate(quantiles):
            values[0, :, index] = level
        return FakeTensor(values), FakeTensor(np.full((1, horizon), 0.5))


class FakeTimesFMModel:
    def forecast(self, *, horizon: int, inputs):
        del inputs
        point = np.full((1, horizon), 0.2)
        matrix = np.zeros((1, horizon, 10))
        matrix[:, :, 0] = 0.2
        for index in range(1, 10):
            matrix[:, :, index] = index / 10
        return point, matrix


class IncrementForecaster:
    def predict(self, history: np.ndarray, horizon: int):
        from hybrid_trader.forecasting.base import ForecastOutput

        base = float(history[-1])
        point = base + np.arange(1, horizon + 1)
        return ForecastOutput(point=point, quantiles={0.1: point - 1, 0.9: point + 1})


def test_naive_forecast_is_zero() -> None:
    output = NaiveReturnForecaster().predict(np.array([0.1, -0.2], dtype=float), 3)
    np.testing.assert_array_equal(output.point, np.zeros(3))


def test_naive_forecast_validates_history() -> None:
    with pytest.raises(ValueError):
        NaiveReturnForecaster().predict(np.array([np.nan], dtype=float), 1)


def test_timesfm_adapter_contract_without_model_download() -> None:
    model = TimesFMForecaster(TimesFMSettings(max_context=8, max_horizon=4))
    model._model = FakeTimesFMModel()
    output = model.predict(np.arange(10, dtype=float), 3)
    np.testing.assert_allclose(output.point, 0.2)
    assert set(output.quantiles) == {round(value, 1) for value in np.arange(0.1, 1.0, 0.1)}
    np.testing.assert_allclose(output.quantiles[0.9], 0.9)


def test_timesfm_adapter_rejects_bad_shape() -> None:
    class BadModel:
        def forecast(self, *, horizon: int, inputs):
            del inputs
            return np.zeros((1, horizon + 1)), np.zeros((1, horizon, 10))

    model = TimesFMForecaster(TimesFMSettings(max_horizon=4))
    model._model = BadModel()
    with pytest.raises(RuntimeError, match="point shape"):
        model.predict(np.arange(10, dtype=float), 2)


def test_chronos_adapter_contract_without_model_download() -> None:
    model = Chronos2Forecaster(ChronosSettings(context_length=8))
    model._pipeline = FakeChronosPipeline()
    output = model.predict(np.arange(10, dtype=float), 3)
    np.testing.assert_allclose(output.point, 0.5)
    assert output.quantiles[0.1].shape == (3,)


def test_chronos_settings_validate_quantiles() -> None:
    with pytest.raises(ValueError):
        ChronosSettings(quantile_levels=(0.9, 0.1))


def test_rolling_features_use_history_ending_at_origin() -> None:
    index = pd.date_range("2024-01-01", periods=8, freq="4h", tz="UTC")
    series = pd.Series(np.arange(8, dtype=float), index=index)
    availability = pd.Series(index + pd.Timedelta(hours=4), index=index)
    spec = RollingForecastSpec(
        context_length=4,
        min_history=3,
        horizon=2,
        stride=2,
        prefix="fake",
        inference_latency_seconds=5,
    )
    result = rolling_forecast_features(
        series, IncrementForecaster(), spec, availability=availability
    )
    assert result.index.tolist() == [index[2], index[4], index[6]]
    assert result["fake_point_1"].iloc[0] == 3
    assert result["fake_point_sum"].iloc[0] == 7
    assert result["forecast_origin_at"].iloc[0] == index[2]
    assert result["forecast_origin_available_at"].iloc[0] == index[2] + pd.Timedelta(hours=4)
    assert result["forecast_step"].iloc[0] == 1
    assert result["available_at"].iloc[0] == index[2] + pd.Timedelta(hours=4, seconds=5)


def test_feature_cache_round_trip_and_dataset_binding(tmp_path: Path) -> None:
    index = pd.date_range("2024-01-01", periods=3, freq="4h", tz="UTC")
    frame = pd.DataFrame(
        {
            "forecast_origin_at": index,
            "forecast_origin_available_at": index + pd.Timedelta(hours=4),
            "available_at": index + pd.Timedelta(hours=4),
            "forecast_step": [1.0, 1.0, 1.0],
            "fake_point_1": [1.0, 2.0, 3.0],
        },
        index=index,
    )
    frame.index.name = "timestamp"
    spec = RollingForecastSpec(context_length=4, min_history=2, prefix="fake")
    dataset_sha = "a" * 64
    digest = cache_rolling_features(
        frame,
        tmp_path / "cache",
        dataset_sha256=dataset_sha,
        model_id="fake/model",
        model_revision="rev-1",
        spec=spec,
    )
    loaded, manifest = read_cached_rolling_features(
        tmp_path / "cache", expected_dataset_sha256=dataset_sha
    )
    assert digest == manifest.feature_sha256
    pd.testing.assert_frame_equal(loaded, frame, check_freq=False)
    with pytest.raises(ValueError, match="different dataset"):
        read_cached_rolling_features(tmp_path / "cache", expected_dataset_sha256="b" * 64)


def test_feature_cache_detects_tampering(tmp_path: Path) -> None:
    index = pd.date_range("2024-01-01", periods=2, freq="4h", tz="UTC")
    frame = pd.DataFrame({"fake_point_1": [1.0, 2.0]}, index=index)
    spec = RollingForecastSpec(context_length=2, min_history=1, prefix="fake")
    cache_rolling_features(
        frame,
        tmp_path / "cache",
        dataset_sha256="a" * 64,
        model_id="fake/model",
        model_revision=None,
        spec=spec,
    )
    payload = bytearray((tmp_path / "cache" / "features.csv.gz").read_bytes())
    payload[-4] ^= 1
    (tmp_path / "cache" / "features.csv.gz").write_bytes(payload)
    with pytest.raises((OSError, EOFError, ValueError)):
        read_cached_rolling_features(tmp_path / "cache")


def test_feature_cache_accepts_carried_forecast_with_explicit_origin(tmp_path: Path) -> None:
    index = pd.date_range("2024-01-01", periods=3, freq="4h", tz="UTC")
    frame = pd.DataFrame(
        {
            "forecast_origin_at": [index[0], index[0], index[0]],
            "forecast_origin_available_at": [index[0] + pd.Timedelta(hours=4)] * 3,
            "available_at": [index[0] + pd.Timedelta(hours=4, seconds=10)] * 3,
            "forecast_step": [1.0, 2.0, 3.0],
            "fake_point_1": [0.1, 0.2, 0.3],
        },
        index=index,
    )
    frame.index.name = "timestamp"
    spec = RollingForecastSpec(
        context_length=4,
        min_history=2,
        horizon=3,
        stride=3,
        prefix="fake",
        inference_latency_seconds=10,
    )
    cache_rolling_features(
        frame,
        tmp_path / "cache",
        dataset_sha256="a" * 64,
        model_id="fake/model",
        model_revision="rev-1",
        spec=spec,
    )
    loaded, manifest = read_cached_rolling_features(tmp_path / "cache")
    assert manifest.schema_version == "1.3"
    pd.testing.assert_frame_equal(loaded, frame, check_freq=False)


def test_feature_cache_rejects_future_forecast_origin(tmp_path: Path) -> None:
    index = pd.date_range("2024-01-01", periods=2, freq="4h", tz="UTC")
    frame = pd.DataFrame(
        {
            "forecast_origin_at": [index[0], index[1] + pd.Timedelta(hours=4)],
            "forecast_origin_available_at": [index[0] + pd.Timedelta(hours=4)] * 2,
            "available_at": [index[0] + pd.Timedelta(hours=4, seconds=10)] * 2,
            "forecast_step": [1.0, 2.0],
            "fake_point_1": [0.1, 0.2],
        },
        index=index,
    )
    spec = RollingForecastSpec(context_length=4, min_history=2, horizon=2, stride=2, prefix="fake")
    with pytest.raises(ValueError, match="origin cannot be after"):
        cache_rolling_features(
            frame,
            tmp_path / "cache",
            dataset_sha256="a" * 64,
            model_id="fake/model",
            model_revision="rev-1",
            spec=spec,
        )
