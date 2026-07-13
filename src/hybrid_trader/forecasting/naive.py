"""Naive forecast baseline that every foundation model must beat."""

import numpy as np

from hybrid_trader.forecasting.base import FloatArray, ForecastOutput


class NaiveReturnForecaster:
    """Predict zero future return for stationary return series."""

    def predict(self, history: FloatArray, horizon: int) -> ForecastOutput:
        if history.ndim != 1 or history.size == 0:
            raise ValueError("history must be a non-empty one-dimensional array")
        if horizon <= 0:
            raise ValueError("horizon must be positive")
        return ForecastOutput(point=np.zeros(horizon, dtype=np.float64))
