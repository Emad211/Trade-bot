"""Optional Chronos-2 adapter using the official quantile API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from hybrid_trader.forecasting.base import FloatArray, ForecastOutput


@dataclass(frozen=True)
class ChronosSettings:
    model_id: str = "amazon/chronos-2"
    revision: str | None = None
    device_map: str = "cpu"
    context_length: int = 2048
    quantile_levels: tuple[float, ...] = (0.1, 0.25, 0.5, 0.75, 0.9)

    def __post_init__(self) -> None:
        if self.context_length <= 0:
            raise ValueError("context_length must be positive")
        if (
            not self.quantile_levels
            or len(set(self.quantile_levels)) != len(self.quantile_levels)
            or any(not 0 < level < 1 for level in self.quantile_levels)
            or tuple(sorted(self.quantile_levels)) != self.quantile_levels
        ):
            raise ValueError("quantile_levels must be unique, sorted and strictly inside (0, 1)")


def _to_numpy(value: Any) -> np.ndarray:
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    return np.asarray(value, dtype=np.float64)


def normalize_chronos_quantile_output(
    quantile_output: Any,
    mean_output: Any,
    *,
    batch_size: int,
    horizon: int,
    quantile_count: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Normalize current and legacy Chronos-2 quantile return contracts.

    Current Chronos-2 returns two lists. Each list element represents one input
    task and includes an explicit variate axis. Older adapters exposed stacked
    tensors directly. This function supports both contracts while requiring every
    input in this project to remain univariate and shape-exact.
    """

    quantiles_are_sequence = isinstance(quantile_output, (list, tuple))
    means_are_sequence = isinstance(mean_output, (list, tuple))
    if quantiles_are_sequence != means_are_sequence:
        raise RuntimeError("Chronos quantile and mean outputs use different container types")

    if quantiles_are_sequence:
        if len(quantile_output) != batch_size or len(mean_output) != batch_size:
            raise RuntimeError(
                "Chronos returned the wrong number of per-series forecast outputs"
            )
        quantile_items: list[np.ndarray] = []
        mean_items: list[np.ndarray] = []
        for index, (quantile_item, mean_item) in enumerate(
            zip(quantile_output, mean_output, strict=True)
        ):
            quantile_array = _to_numpy(quantile_item)
            mean_array = _to_numpy(mean_item)
            if quantile_array.shape == (1, horizon, quantile_count):
                quantile_array = quantile_array[0]
            elif quantile_array.shape != (horizon, quantile_count):
                raise RuntimeError(
                    f"Unexpected Chronos quantile shape for item {index}: "
                    f"{quantile_array.shape}"
                )
            if mean_array.shape == (1, horizon):
                mean_array = mean_array[0]
            elif mean_array.shape != (horizon,):
                raise RuntimeError(
                    f"Unexpected Chronos mean shape for item {index}: {mean_array.shape}"
                )
            quantile_items.append(quantile_array)
            mean_items.append(mean_array)
        quantiles = np.stack(quantile_items, axis=0)
        means = np.stack(mean_items, axis=0)
    else:
        quantiles = _to_numpy(quantile_output)
        means = _to_numpy(mean_output)
        if quantiles.shape == (batch_size, 1, horizon, quantile_count):
            quantiles = quantiles[:, 0]
        if means.shape == (batch_size, 1, horizon):
            means = means[:, 0]

    expected_quantiles = (batch_size, horizon, quantile_count)
    expected_means = (batch_size, horizon)
    if quantiles.shape != expected_quantiles:
        raise RuntimeError(f"Unexpected Chronos quantile shape: {quantiles.shape}")
    if means.shape != expected_means:
        raise RuntimeError(f"Unexpected Chronos mean shape: {means.shape}")
    if not np.isfinite(quantiles).all() or not np.isfinite(means).all():
        raise RuntimeError("Chronos returned non-finite forecasts")
    return quantiles, means


class Chronos2Forecaster:
    def __init__(self, settings: ChronosSettings | None = None) -> None:
        self.settings = settings or ChronosSettings()
        self._pipeline: Any | None = None

    def _load(self) -> Any:
        if self._pipeline is not None:
            return self._pipeline
        try:
            from chronos import Chronos2Pipeline
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("Install Chronos with: pip install -e '.[forecast]'") from exc
        kwargs: dict[str, Any] = {"device_map": self.settings.device_map}
        if self.settings.revision is not None:
            kwargs["revision"] = self.settings.revision
        self._pipeline = Chronos2Pipeline.from_pretrained(self.settings.model_id, **kwargs)
        return self._pipeline

    def predict(self, history: FloatArray, horizon: int) -> ForecastOutput:
        if history.ndim != 1 or history.size == 0:
            raise ValueError("history must be a non-empty one-dimensional array")
        if not np.isfinite(history).all():
            raise ValueError("history must be finite")
        if horizon <= 0:
            raise ValueError("horizon must be positive")
        pipeline = self._load()
        quantile_output, mean_output = pipeline.predict_quantiles(
            inputs=[history[-self.settings.context_length :].astype(np.float32)],
            prediction_length=horizon,
            quantile_levels=list(self.settings.quantile_levels),
            context_length=self.settings.context_length,
        )
        quantile_array, mean_array = normalize_chronos_quantile_output(
            quantile_output,
            mean_output,
            batch_size=1,
            horizon=horizon,
            quantile_count=len(self.settings.quantile_levels),
        )
        quantiles = {
            level: quantile_array[0, :, index]
            for index, level in enumerate(self.settings.quantile_levels)
        }
        return ForecastOutput(point=mean_array[0], quantiles=quantiles)
