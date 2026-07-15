from __future__ import annotations

import numpy as np
import pytest

from hybrid_trader.forecasting.batched import Chronos2BatchForecaster
from hybrid_trader.forecasting.chronos_adapter import (
    Chronos2Forecaster,
    ChronosSettings,
    normalize_chronos_quantile_output,
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


class OfficialListPipeline:
    def predict_quantiles(self, **kwargs):
        horizon = kwargs["prediction_length"]
        quantile_count = len(kwargs["quantile_levels"])
        inputs = kwargs["inputs"]
        quantiles = []
        means = []
        for index, _ in enumerate(inputs):
            values = np.zeros((1, horizon, quantile_count), dtype=float)
            for quantile_index in range(quantile_count):
                values[0, :, quantile_index] = index + quantile_index / 10
            quantiles.append(FakeTensor(values))
            means.append(FakeTensor(np.full((1, horizon), index + 0.5)))
        return quantiles, means


def test_single_chronos_adapter_accepts_official_list_contract() -> None:
    model = Chronos2Forecaster(ChronosSettings(context_length=8))
    model._pipeline = OfficialListPipeline()
    output = model.predict(np.arange(10, dtype=float), 3)
    np.testing.assert_allclose(output.point, 0.5)
    assert output.quantiles[0.1].shape == (3,)
    assert output.quantiles[0.9].shape == (3,)


def test_batched_chronos_adapter_accepts_official_list_contract() -> None:
    model = Chronos2BatchForecaster(ChronosSettings(context_length=8))
    model._adapter._pipeline = OfficialListPipeline()
    outputs = model.predict_batch(
        [np.arange(10, dtype=float), np.arange(20, dtype=float)],
        4,
    )
    assert len(outputs) == 2
    np.testing.assert_allclose(outputs[0].point, 0.5)
    np.testing.assert_allclose(outputs[1].point, 1.5)
    assert outputs[0].quantiles[0.1].shape == (4,)


def test_chronos_output_rejects_multivariate_item_for_univariate_adapter() -> None:
    quantiles = [FakeTensor(np.zeros((2, 3, 5), dtype=float))]
    means = [FakeTensor(np.zeros((2, 3), dtype=float))]
    with pytest.raises(RuntimeError, match="quantile shape for item 0"):
        normalize_chronos_quantile_output(
            quantiles,
            means,
            batch_size=1,
            horizon=3,
            quantile_count=5,
        )


def test_chronos_output_rejects_mixed_container_contracts() -> None:
    quantiles = [FakeTensor(np.zeros((1, 3, 5), dtype=float))]
    means = FakeTensor(np.zeros((1, 3), dtype=float))
    with pytest.raises(RuntimeError, match="different container types"):
        normalize_chronos_quantile_output(
            quantiles,
            means,
            batch_size=1,
            horizon=3,
            quantile_count=5,
        )
