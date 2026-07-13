"""Minimal interface shared by forecasting challengers."""

from dataclasses import dataclass, field
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class ForecastOutput:
    point: FloatArray
    quantiles: dict[float, FloatArray] = field(default_factory=dict)


class TimeSeriesForecaster(Protocol):
    def predict(self, history: FloatArray, horizon: int) -> ForecastOutput:
        """Forecast a one-dimensional series."""
        ...
