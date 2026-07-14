"""Probability calibration fitted on a dedicated chronological partition."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from sklearn.linear_model import LogisticRegression

FloatVector = NDArray[np.float64]
IntVector = NDArray[np.int64]


class PlattCalibrator:
    def __init__(self, *, random_seed: int = 42) -> None:
        self.random_seed = random_seed
        self._model: LogisticRegression | None = None
        self._constant: float | None = None

    @staticmethod
    def _logit(probabilities: FloatVector) -> FloatVector:
        clipped = np.clip(probabilities, 1e-6, 1 - 1e-6)
        return np.log(clipped / (1 - clipped))

    def fit(self, probabilities: FloatVector, y: IntVector) -> PlattCalibrator:
        if probabilities.size != y.size or y.size == 0:
            raise ValueError("Calibration probabilities and labels must have equal non-zero length")
        if (
            not np.isfinite(probabilities).all()
            or ((probabilities < 0) | (probabilities > 1)).any()
        ):
            raise ValueError("Calibration probabilities must be finite and inside [0, 1]")
        if np.unique(y).size < 2 or np.std(probabilities) < 1e-12:
            self._constant = float(np.clip(y.mean(), 1e-6, 1 - 1e-6))
            self._model = None
            return self
        model = LogisticRegression(C=1.0, solver="lbfgs", random_state=self.random_seed)
        model.fit(self._logit(probabilities).reshape(-1, 1), y)
        self._model = model
        self._constant = None
        return self

    def transform(self, probabilities: FloatVector) -> FloatVector:
        if (
            not np.isfinite(probabilities).all()
            or ((probabilities < 0) | (probabilities > 1)).any()
        ):
            raise ValueError("Probabilities must be finite and inside [0, 1]")
        if self._constant is not None:
            return np.full(probabilities.size, self._constant, dtype=np.float64)
        if self._model is None:
            raise RuntimeError("Calibrator is not fitted")
        return np.asarray(
            self._model.predict_proba(self._logit(probabilities).reshape(-1, 1))[:, 1],
            dtype=np.float64,
        )
