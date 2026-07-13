"""Forecast model adapters."""

from hybrid_trader.forecasting.base import ForecastOutput, TimeSeriesForecaster
from hybrid_trader.forecasting.naive import NaiveReturnForecaster

__all__ = ["ForecastOutput", "NaiveReturnForecaster", "TimeSeriesForecaster"]
