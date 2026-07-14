import numpy as np
import pytest

from hybrid_trader.calibration import PlattCalibrator
from hybrid_trader.metrics import expected_calibration_error, probability_metrics
from hybrid_trader.models import PriorProbabilityModel, RidgeLogisticModel


def test_prior_probability_model() -> None:
    x = np.zeros((4, 2), dtype=float)
    y = np.array([0, 1, 1, 1], dtype=np.int64)
    model = PriorProbabilityModel().fit(x, y)
    np.testing.assert_allclose(model.predict_proba(np.zeros((2, 2))), 0.75)


def test_ridge_logistic_handles_missing_values() -> None:
    x = np.array([[0.0, np.nan], [1.0, 2.0], [2.0, 1.0], [3.0, np.nan]])
    y = np.array([0, 0, 1, 1], dtype=np.int64)
    model = RidgeLogisticModel().fit(x, y)
    probabilities = model.predict_proba(x)
    assert np.isfinite(probabilities).all()
    assert ((probabilities >= 0) & (probabilities <= 1)).all()


def test_platt_calibrator_constant_case() -> None:
    probabilities = np.full(4, 0.5)
    y = np.array([0, 1, 1, 1], dtype=np.int64)
    calibrator = PlattCalibrator().fit(probabilities, y)
    np.testing.assert_allclose(calibrator.transform(np.array([0.2, 0.8])), 0.75)


def test_platt_calibrator_requires_fit() -> None:
    with pytest.raises(RuntimeError):
        PlattCalibrator().transform(np.array([0.5]))


def test_probability_metrics_are_bounded() -> None:
    y = np.array([0, 0, 1, 1], dtype=np.int64)
    probabilities = np.array([0.1, 0.4, 0.6, 0.9])
    metrics = probability_metrics(y, probabilities)
    assert metrics["accuracy"] == 1.0
    assert 0 <= metrics["brier"] <= 1
    assert 0 <= metrics["ece"] <= 1
    assert metrics["roc_auc"] == 1.0


def test_ece_rejects_invalid_bins() -> None:
    with pytest.raises(ValueError):
        expected_calibration_error(np.array([0, 1], dtype=np.int64), np.array([0.2, 0.8]), bins=1)
