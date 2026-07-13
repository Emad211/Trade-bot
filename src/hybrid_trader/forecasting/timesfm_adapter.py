"""Optional TimesFM 2.5 adapter using the official PyTorch API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from hybrid_trader.forecasting.base import FloatArray, ForecastOutput


@dataclass(frozen=True)
class TimesFMSettings:
    model_id: str = "google/timesfm-2.5-200m-pytorch"
    revision: str | None = None
    max_context: int = 1024
    max_horizon: int = 256
    use_quantiles: bool = True

    def __post_init__(self) -> None:
        if not 1 <= self.max_context <= 16_384:
            raise ValueError("max_context must be in [1, 16384]")
        if not 1 <= self.max_horizon <= 1_000:
            raise ValueError("max_horizon must be in [1, 1000]")


class TimesFMForecaster:
    """Lazy-loading adapter around the official TimesFM 2.5 PyTorch API."""

    def __init__(self, settings: TimesFMSettings | None = None) -> None:
        self.settings = settings or TimesFMSettings()
        self._model: Any | None = None

    def _load(self) -> Any:
        if self._model is not None:
            return self._model
        try:
            import timesfm
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("Install TimesFM with: pip install -e '.[forecast]'") from exc

        kwargs: dict[str, Any] = {}
        if self.settings.revision is not None:
            kwargs["revision"] = self.settings.revision
        model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(self.settings.model_id, **kwargs)
        model.compile(
            timesfm.ForecastConfig(
                max_context=self.settings.max_context,
                max_horizon=self.settings.max_horizon,
                normalize_inputs=True,
                use_continuous_quantile_head=self.settings.use_quantiles,
                force_flip_invariance=True,
                infer_is_positive=False,
                fix_quantile_crossing=True,
            )
        )
        self._model = model
        return model

    def predict(self, history: FloatArray, horizon: int) -> ForecastOutput:
        if history.ndim != 1 or history.size == 0:
            raise ValueError("history must be a non-empty one-dimensional array")
        if not np.isfinite(history).all():
            raise ValueError("history must be finite")
        if not 0 < horizon <= self.settings.max_horizon:
            raise ValueError(f"horizon must be in [1, {self.settings.max_horizon}]")

        model = self._load()
        point, quantile_matrix = model.forecast(
            horizon=horizon,
            inputs=[history[-self.settings.max_context :].astype(float)],
        )
        point_array = np.asarray(point[0], dtype=np.float64)
        if point_array.shape != (horizon,):
            raise RuntimeError(f"Unexpected TimesFM point shape: {point_array.shape}")
        if not np.isfinite(point_array).all():
            raise RuntimeError("TimesFM returned non-finite point forecasts")
        quantiles: dict[float, FloatArray] = {}
        if self.settings.use_quantiles:
            matrix = np.asarray(quantile_matrix[0], dtype=np.float64)
            # Official output: mean followed by q10 ... q90.
            if matrix.shape != (horizon, 10):
                raise RuntimeError(f"Unexpected TimesFM quantile shape: {matrix.shape}")
            if not np.isfinite(matrix).all():
                raise RuntimeError("TimesFM returned non-finite quantile forecasts")
            for column, quantile in enumerate(np.arange(0.1, 1.0, 0.1), start=1):
                quantiles[float(round(quantile, 1))] = matrix[:, column]
        return ForecastOutput(point=point_array, quantiles=quantiles)
