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


def _to_numpy_batch(
    value: Any,
    *,
    batch_size: int,
    item_shape: tuple[int, ...],
    label: str,
) -> np.ndarray:
    """Normalize Chronos tensor or per-series list output to one strict batch array."""

    expected = (batch_size, *item_shape)
    if isinstance(value, (list, tuple)):
        if len(value) != batch_size:
            raise RuntimeError(
                f"Chronos {label} batch length {len(value)} does not match {batch_size}"
            )
        items: list[np.ndarray] = []
        for index, item in enumerate(value):
            array = _to_numpy(item)
            if array.shape == (1, *item_shape):
                array = array[0]
            if array.shape != item_shape:
                raise RuntimeError(f"Unexpected Chronos {label} item {index} shape: {array.shape}")
            items.append(array)
        return np.stack(items, axis=0)

    array = _to_numpy(value)
    if batch_size == 1 and array.shape == item_shape:
        array = array[np.newaxis, ...]
    if array.shape != expected:
        raise RuntimeError(f"Unexpected Chronos {label} shape: {array.shape}")
    return array


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
        quantile_tensor, mean_tensor = pipeline.predict_quantiles(
            inputs=[history[-self.settings.context_length :].astype(np.float32)],
            prediction_length=horizon,
            quantile_levels=list(self.settings.quantile_levels),
            context_length=self.settings.context_length,
        )
        quantile_array = _to_numpy_batch(
            quantile_tensor,
            batch_size=1,
            item_shape=(horizon, len(self.settings.quantile_levels)),
            label="quantile",
        )
        mean_array = _to_numpy_batch(
            mean_tensor,
            batch_size=1,
            item_shape=(horizon,),
            label="mean",
        )
        if not np.isfinite(quantile_array).all() or not np.isfinite(mean_array).all():
            raise RuntimeError("Chronos returned non-finite forecasts")
        quantiles = {
            level: quantile_array[0, :, index]
            for index, level in enumerate(self.settings.quantile_levels)
        }
        return ForecastOutput(point=mean_array[0], quantiles=quantiles)
