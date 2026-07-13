"""Batched, leakage-safe rolling inference for time-series foundation models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np
import pandas as pd

from hybrid_trader.forecasting.base import FloatArray, ForecastOutput
from hybrid_trader.forecasting.chronos_adapter import Chronos2Forecaster, ChronosSettings
from hybrid_trader.forecasting.timesfm_adapter import TimesFMForecaster, TimesFMSettings


class BatchForecaster(Protocol):
    """A forecaster that evaluates independent one-dimensional histories in a batch."""

    def predict_batch(
        self, histories: list[FloatArray], horizon: int
    ) -> list[ForecastOutput]: ...


@dataclass(frozen=True)
class BatchRollingSpec:
    context_length: int = 256
    horizon: int = 6
    min_history: int = 256
    stride: int = 6
    batch_size: int = 16
    prefix: str = "foundation"
    inference_latency_seconds: float = 0.0

    def __post_init__(self) -> None:
        if self.context_length <= 0 or self.horizon <= 0 or self.min_history <= 0:
            raise ValueError("context, horizon and minimum history must be positive")
        if self.min_history > self.context_length:
            raise ValueError("min_history cannot exceed context_length")
        if self.stride <= 0 or self.batch_size <= 0:
            raise ValueError("stride and batch_size must be positive")
        if self.horizon < self.stride:
            raise ValueError(
                "horizon must cover stride so carried forecasts retain the correct step"
            )
        if self.inference_latency_seconds < 0:
            raise ValueError("inference latency cannot be negative")
        if not self.prefix:
            raise ValueError("prefix cannot be empty")


class NaiveBatchForecaster:
    """Zero-return batch baseline with the same contract as foundation models."""

    def predict_batch(
        self, histories: list[FloatArray], horizon: int
    ) -> list[ForecastOutput]:
        if horizon <= 0 or not histories:
            raise ValueError("positive horizon and at least one history are required")
        for history in histories:
            if history.ndim != 1 or history.size == 0:
                raise ValueError("histories must be non-empty one-dimensional arrays")
        return [
            ForecastOutput(point=np.zeros(horizon, dtype=np.float64))
            for _ in histories
        ]


class TimesFMBatchForecaster:
    """Batch wrapper around the official TimesFM 2.5 PyTorch API."""

    def __init__(self, settings: TimesFMSettings) -> None:
        self.settings = settings
        self._adapter = TimesFMForecaster(settings)

    def predict_batch(
        self, histories: list[FloatArray], horizon: int
    ) -> list[ForecastOutput]:
        if not histories:
            raise ValueError("At least one history is required")
        if not 0 < horizon <= self.settings.max_horizon:
            raise ValueError("horizon exceeds the configured TimesFM maximum")
        inputs: list[np.ndarray] = []
        for history in histories:
            if history.ndim != 1 or history.size == 0:
                raise ValueError("histories must be non-empty one-dimensional arrays")
            truncated = history[-self.settings.max_context :].astype(float)
            if not np.isfinite(truncated).all():
                raise ValueError("TimesFM history contains non-finite values")
            inputs.append(truncated)
        model = self._adapter._load()
        point, quantile_matrix = model.forecast(horizon=horizon, inputs=inputs)
        point_array = np.asarray(point, dtype=np.float64)
        matrix = np.asarray(quantile_matrix, dtype=np.float64)
        expected_point = (len(inputs), horizon)
        if point_array.shape != expected_point:
            raise RuntimeError(f"Unexpected TimesFM point shape: {point_array.shape}")
        expected_quantiles = (len(inputs), horizon, 10)
        if matrix.shape != expected_quantiles:
            raise RuntimeError(f"Unexpected TimesFM quantile shape: {matrix.shape}")
        if not np.isfinite(point_array).all() or not np.isfinite(matrix).all():
            raise RuntimeError("TimesFM returned non-finite forecasts")
        results: list[ForecastOutput] = []
        for batch_index in range(len(inputs)):
            quantiles = {
                float(round(level, 1)): matrix[batch_index, :, column]
                for column, level in enumerate(np.arange(0.1, 1.0, 0.1), start=1)
            }
            results.append(
                ForecastOutput(point=point_array[batch_index], quantiles=quantiles)
            )
        return results


class Chronos2BatchForecaster:
    """Batch wrapper around Chronos-2 ``predict_quantiles``."""

    def __init__(self, settings: ChronosSettings) -> None:
        self.settings = settings
        self._adapter = Chronos2Forecaster(settings)

    def predict_batch(
        self, histories: list[FloatArray], horizon: int
    ) -> list[ForecastOutput]:
        if not histories or horizon <= 0:
            raise ValueError("positive horizon and at least one history are required")
        inputs: list[np.ndarray] = []
        for history in histories:
            if history.ndim != 1 or history.size == 0:
                raise ValueError("histories must be non-empty one-dimensional arrays")
            truncated = history[-self.settings.context_length :].astype(np.float32)
            if not np.isfinite(truncated).all():
                raise ValueError("Chronos history contains non-finite values")
            inputs.append(truncated)
        pipeline: Any = self._adapter._load()
        quantile_tensor, mean_tensor = pipeline.predict_quantiles(
            inputs=inputs,
            prediction_length=horizon,
            quantile_levels=list(self.settings.quantile_levels),
            context_length=self.settings.context_length,
        )
        quantile_array = np.asarray(quantile_tensor.detach().cpu(), dtype=np.float64)
        mean_array = np.asarray(mean_tensor.detach().cpu(), dtype=np.float64)
        expected_quantiles = (len(inputs), horizon, len(self.settings.quantile_levels))
        if quantile_array.shape != expected_quantiles:
            raise RuntimeError(f"Unexpected Chronos quantile shape: {quantile_array.shape}")
        if mean_array.shape != (len(inputs), horizon):
            raise RuntimeError(f"Unexpected Chronos mean shape: {mean_array.shape}")
        if not np.isfinite(quantile_array).all() or not np.isfinite(mean_array).all():
            raise RuntimeError("Chronos returned non-finite forecasts")
        return [
            ForecastOutput(
                point=mean_array[index],
                quantiles={
                    level: quantile_array[index, :, quantile_index]
                    for quantile_index, level in enumerate(self.settings.quantile_levels)
                },
            )
            for index in range(len(inputs))
        ]


def rolling_batched_features(
    series: pd.Series,
    forecaster: BatchForecaster,
    spec: BatchRollingSpec,
    *,
    availability: pd.Series,
) -> pd.DataFrame:
    """Generate batched forecasts and align each carried row to its horizon step.

    A forecast created at origin ``t`` supplies step 1 to decision row ``t``, step
    2 to ``t+1`` and so on until the next refresh. This avoids incorrectly
    carrying the first-step forecast across all rows between refreshes.
    """

    if series.empty or not series.index.is_monotonic_increasing or series.index.has_duplicates:
        raise ValueError("series must be non-empty, uniquely indexed and sorted")
    observed = pd.to_datetime(availability.reindex(series.index), utc=True, errors="coerce")
    if observed.isna().any():
        raise ValueError("availability must cover every series row")
    values = series.to_numpy(dtype=np.float64)
    origins = list(range(spec.min_history - 1, len(series), spec.stride))
    rows: list[dict[str, float | pd.Timestamp]] = []
    latency = pd.Timedelta(seconds=spec.inference_latency_seconds)

    for batch_start in range(0, len(origins), spec.batch_size):
        batch_origins = origins[batch_start : batch_start + spec.batch_size]
        histories: list[FloatArray] = []
        valid_origins: list[int] = []
        for origin in batch_origins:
            start = max(0, origin + 1 - spec.context_length)
            history = values[start : origin + 1]
            if np.isfinite(history).all():
                histories.append(np.asarray(history, dtype=np.float64))
                valid_origins.append(origin)
        if not histories:
            continue
        forecasts = forecaster.predict_batch(histories, spec.horizon)
        if len(forecasts) != len(valid_origins):
            raise RuntimeError("Batch forecaster returned the wrong number of outputs")
        for origin, forecast in zip(valid_origins, forecasts, strict=True):
            point = np.asarray(forecast.point, dtype=np.float64)
            if point.shape != (spec.horizon,) or not np.isfinite(point).all():
                raise RuntimeError("Invalid batch point forecast")
            quantiles = {
                level: np.asarray(values_at_level, dtype=np.float64)
                for level, values_at_level in forecast.quantiles.items()
            }
            if any(
                values_at_level.shape != (spec.horizon,)
                or not np.isfinite(values_at_level).all()
                for values_at_level in quantiles.values()
            ):
                raise RuntimeError("Invalid batch quantile forecast")
            origin_available = pd.Timestamp(observed.iloc[origin]) + latency
            coverage = min(spec.stride, spec.horizon, len(series) - origin)
            for offset in range(coverage):
                row: dict[str, float | pd.Timestamp] = {
                    "timestamp": pd.Timestamp(series.index[origin + offset]),
                    "available_at": origin_available,
                    f"{spec.prefix}_point_1": float(point[offset]),
                    f"{spec.prefix}_point_sum": float(point[offset:].sum()),
                    f"{spec.prefix}_forecast_age_bars": float(offset),
                }
                for level, values_at_level in sorted(quantiles.items()):
                    label = str(level).replace(".", "p")
                    row[f"{spec.prefix}_q{label}_1"] = float(values_at_level[offset])
                    row[f"{spec.prefix}_q{label}_sum"] = float(
                        values_at_level[offset:].sum()
                    )
                rows.append(row)
    if not rows:
        raise ValueError("No batched rolling forecasts were generated")
    result = pd.DataFrame(rows).set_index("timestamp").sort_index()
    if result.index.has_duplicates:
        raise RuntimeError("Batched forecast alignment produced duplicate decision rows")
    return result
