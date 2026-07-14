"""Deterministic baseline probability models."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from hybrid_trader.models.base import FloatMatrix, FloatVector, IntVector


@dataclass
class PriorProbabilityModel:
    name: str = "prior"
    prior_: float = 0.5

    def fit(self, x: FloatMatrix, y: IntVector) -> PriorProbabilityModel:
        del x
        if y.size == 0:
            raise ValueError("Cannot fit on an empty target")
        self.prior_ = float(np.clip(y.mean(), 1e-6, 1 - 1e-6))
        return self

    def predict_proba(self, x: FloatMatrix) -> FloatVector:
        return np.full(x.shape[0], self.prior_, dtype=np.float64)


class RidgeLogisticModel:
    name = "ridge_logistic"

    def __init__(self, *, c: float = 1.0, random_seed: int = 42) -> None:
        self.pipeline = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        C=c,
                        solver="lbfgs",
                        max_iter=2000,
                        random_state=random_seed,
                    ),
                ),
            ]
        )

    def fit(self, x: FloatMatrix, y: IntVector) -> RidgeLogisticModel:
        if np.unique(y).size < 2:
            raise ValueError("Ridge logistic requires both target classes")
        self.pipeline.fit(x, y)
        return self

    def predict_proba(self, x: FloatMatrix) -> FloatVector:
        return np.asarray(self.pipeline.predict_proba(x)[:, 1], dtype=np.float64)
