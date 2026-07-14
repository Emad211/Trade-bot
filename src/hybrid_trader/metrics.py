"""Probability-quality metrics used by sealed tests."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score

FloatVector = NDArray[np.float64]
IntVector = NDArray[np.int64]


def expected_calibration_error(
    y: IntVector, probabilities: FloatVector, *, bins: int = 10
) -> float:
    if bins <= 1:
        raise ValueError("bins must be greater than one")
    edges = np.linspace(0.0, 1.0, bins + 1)
    # Include probability 1.0 in the final bin.
    assignments = np.minimum(np.digitize(probabilities, edges[1:-1], right=False), bins - 1)
    total = len(y)
    error = 0.0
    for bucket in range(bins):
        mask = assignments == bucket
        count = int(mask.sum())
        if count == 0:
            continue
        error += count / total * abs(float(probabilities[mask].mean()) - float(y[mask].mean()))
    return float(error)


def probability_metrics(y: IntVector, probabilities: FloatVector) -> dict[str, float]:
    if y.size == 0 or y.size != probabilities.size:
        raise ValueError("Labels and probabilities must have equal non-zero length")
    if not np.isfinite(probabilities).all() or ((probabilities < 0) | (probabilities > 1)).any():
        raise ValueError("Probabilities must be finite and inside [0, 1]")
    predicted = (probabilities >= 0.5).astype(np.int64)
    auc = float(roc_auc_score(y, probabilities)) if np.unique(y).size > 1 else float("nan")
    return {
        "accuracy": float(accuracy_score(y, predicted)),
        "brier": float(brier_score_loss(y, probabilities)),
        "log_loss": float(log_loss(y, probabilities, labels=[0, 1])),
        "roc_auc": auc,
        "ece": expected_calibration_error(y, probabilities),
        "realized_positive_rate": float(y.mean()),
        "predicted_positive_rate": float(probabilities.mean()),
    }
