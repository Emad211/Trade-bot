"""Optional deterministic tree-model adapters."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer

from hybrid_trader.models.base import FloatMatrix, FloatVector, IntVector


class _ImputedModel:
    name: str

    def __init__(self) -> None:
        self.imputer = SimpleImputer(strategy="median", keep_empty_features=True)
        self.model: Any = None
        self._feature_names: list[str] | None = None

    def _as_frame(self, values: FloatMatrix) -> pd.DataFrame:
        if self._feature_names is None:
            self._feature_names = [f"Column_{index}" for index in range(values.shape[1])]
        if values.shape[1] != len(self._feature_names):
            raise ValueError("Feature count does not match the fitted model")
        return pd.DataFrame(values, columns=self._feature_names)

    def fit(self, x: FloatMatrix, y: IntVector) -> _ImputedModel:
        transformed = np.asarray(self.imputer.fit_transform(x), dtype=np.float64)
        self.model.fit(self._as_frame(transformed), y)
        return self

    def predict_proba(self, x: FloatMatrix) -> FloatVector:
        transformed = np.asarray(self.imputer.transform(x), dtype=np.float64)
        return np.asarray(
            self.model.predict_proba(self._as_frame(transformed))[:, 1], dtype=np.float64
        )


class LightGBMProbabilityModel(_ImputedModel):
    name = "lightgbm"

    def __init__(self, *, random_seed: int = 42) -> None:
        super().__init__()
        try:
            from lightgbm import LGBMClassifier
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Install ML extras with: pip install -e '.[ml]'") from exc
        self.model = LGBMClassifier(
            n_estimators=300,
            learning_rate=0.03,
            num_leaves=15,
            max_depth=5,
            min_child_samples=40,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_alpha=0.2,
            reg_lambda=1.0,
            random_state=random_seed,
            deterministic=True,
            force_col_wise=True,
            n_jobs=1,
            verbosity=-1,
        )


class CatBoostProbabilityModel(_ImputedModel):
    name = "catboost"

    def __init__(self, *, random_seed: int = 42) -> None:
        super().__init__()
        try:
            from catboost import CatBoostClassifier
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Install ML extras with: pip install -e '.[ml]'") from exc
        self.model = CatBoostClassifier(
            iterations=350,
            depth=5,
            learning_rate=0.03,
            loss_function="Logloss",
            random_seed=random_seed,
            random_strength=0.0,
            l2_leaf_reg=5.0,
            allow_writing_files=False,
            thread_count=1,
            verbose=False,
        )
