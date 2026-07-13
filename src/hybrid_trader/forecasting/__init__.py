"""Forecasting adapters."""

from hybrid_trader.forecasting.base import ForecastOutput, TimeSeriesForecaster
from hybrid_trader.forecasting.chronos_adapter import Chronos2Forecaster, ChronosSettings
from hybrid_trader.forecasting.naive import NaiveReturnForecaster
from hybrid_trader.forecasting.timesfm_adapter import TimesFMForecaster, TimesFMSettings

__all__ = [
    "Chronos2Forecaster",
    "ChronosSettings",
    "ForecastOutput",
    "NaiveReturnForecaster",
    "TimeSeriesForecaster",
    "TimesFMForecaster",
    "TimesFMSettings",
]
