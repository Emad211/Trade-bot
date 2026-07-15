from __future__ import annotations

import numpy as np
import pytest

from hybrid_trader.forecasting.batched import Chronos2BatchForecaster
from hybrid_trader.forecasting.chronos_adapter import (
    Chronos2Forecaster,
    ChronosSettings,
    _to_numpy_batch,
)


class FakeTensor:
    def __init__(self, values: np.ndarray) -> None:
        self.values = values

    def detach(self) -> FakeTensor:
        return self

    def cpu(self) -> FakeTensor:
        return self

    def __array__(self, dtype=None):
        return np.asarray(self.values, dtype=dtype)


class ListChronosPipeline:
    def predict_quantiles(self, **kwargs):
        inputs = kwargs["inputs"]
        horizon = kwargs["prediction_length"]
        levels = kwargs["quantile_levels"]
        quantiles = []
        means = []
        for item_index, _ in enumerate(inputs):
            quantile_values = np.zeros((horizon, len(levels)), dtype=float)
            for level_index, level in enumerate(levels):
                quantile_values[:, level_index] = level + item_index
            quantiles.append(FakeTensor(quantile_values))
            means.append(FakeTensor(np.full(horizon, 0.5 + item_index)))
        return quantiles, means


def test_to_numpy_batch_stacks_per_series_outputs() -> None:
    values = [FakeTensor(np.full((3, 2), index)) for index in (1.0, 2.0)]
    result = _to_numpy_batch(
        values,
        batch_size=2,
        item_shape=(3, 2),
        label="quantile",
    )
    assert result.shape == (2, 3, 2)
    np.testing.assert_allclose(result[0], 1.0)
    np.testing.assert_allclose(result[1], 2.0)


def test_to_numpy_batch_rejects_wrong_batch_length_and_ragged_items() -> None:
    with pytest.raises(RuntimeError, match="batch length"):
        _to_numpy_batch(
            [FakeTensor(np.zeros((3, 2)))],
            batch_size=2,
            item_shape=(3, 2),
            label="quantile",
        )
    with pytest.raises(RuntimeError, match="item 1 shape"):
        _to_numpy_batch(
            [FakeTensor(np.zeros((3, 2))), FakeTensor(np.zeros((4, 2)))],
            batch_size=2,
            item_shape=(3, 2),
            label="quantile",
        )


def test_single_chronos_adapter_accepts_list_outputs() -> None:
    settings = ChronosSettings(context_length=8, quantile_levels=(0.1, 0.5, 0.9))
    model = Chronos2Forecaster(settings)
    model._pipeline = ListChronosPipeline()
    result = model.predict(np.arange(10, dtype=float), horizon=3)
    assert result.point.shape == (3,)
    np.testing.assert_allclose(result.point, 0.5)
    np.testing.assert_allclose(result.quantiles[0.9], 0.9)


def test_batched_chronos_adapter_accepts_list_outputs() -> None:
    settings = ChronosSettings(context_length=8, quantile_levels=(0.1, 0.5, 0.9))
    model = Chronos2BatchForecaster(settings)
    model._adapter._pipeline = ListChronosPipeline()
    outputs = model.predict_batch(
        [np.arange(10, dtype=float), np.arange(10, 20, dtype=float)],
        horizon=3,
    )
    assert len(outputs) == 2
    np.testing.assert_allclose(outputs[0].point, 0.5)
    np.testing.assert_allclose(outputs[1].point, 1.5)
    np.testing.assert_allclose(outputs[1].quantiles[0.1], 1.1)
