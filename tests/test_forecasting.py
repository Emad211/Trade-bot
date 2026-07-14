import numpy as np
import pytest

from hybrid_trader.forecasting import NaiveReturnForecaster


def test_naive_forecast_is_zero() -> None:
    output = NaiveReturnForecaster().predict(np.array([0.1, -0.2], dtype=float), 3)
    np.testing.assert_array_equal(output.point, np.zeros(3))


def test_naive_forecast_validates_horizon() -> None:
    with pytest.raises(ValueError):
        NaiveReturnForecaster().predict(np.array([0.1], dtype=float), 0)
