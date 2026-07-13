"""Sealed walk-forward model and trading evaluation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd

from hybrid_trader.calibration import PlattCalibrator
from hybrid_trader.config import AppConfig
from hybrid_trader.metrics import probability_metrics
from hybrid_trader.models.base import ProbabilityModel
from hybrid_trader.models.baselines import PriorProbabilityModel
from hybrid_trader.splits import SplitSpec, purge_unknown_labels, sealed_folds

ModelFactory = Callable[[], ProbabilityModel]


@dataclass(frozen=True)
class TradingEvaluation:
    frame: pd.DataFrame
    metrics: dict[str, float]


def _max_drawdown(equity: pd.Series) -> float:
    return float((equity / equity.cummax() - 1.0).min()) if len(equity) else 0.0


def evaluate_exposure_as_strategy(
    frame: pd.DataFrame,
    exposure: np.ndarray,
    *,
    config: AppConfig,
    cost_multiplier: float = 1.0,
) -> TradingEvaluation:
    """Evaluate a pre-declared long/flat exposure against execution-aligned returns."""

    if config.labels.holding_period_bars != 1:
        raise ValueError(
            "The current evaluator supports one-bar holding periods only; "
            "overlapping multi-bar positions require a portfolio book simulator"
        )
    if len(frame) != len(exposure):
        raise ValueError("Frame and exposure must have equal length")
    if cost_multiplier <= 0:
        raise ValueError("cost_multiplier must be positive")
    if "target_return" not in frame:
        raise ValueError("Trading frame must contain target_return")

    exposure = np.asarray(exposure, dtype=np.float64)
    if not np.isfinite(exposure).all():
        raise ValueError("Exposure must be finite")
    if (exposure < 0).any() or (exposure > config.risk.max_exposure + 1e-12).any():
        raise ValueError("Exposure violates the configured long/flat limits")
    target_returns = frame["target_return"].to_numpy(dtype=np.float64)
    if not np.isfinite(target_returns).all() or (target_returns <= -1).any():
        raise ValueError("Target returns must be finite and greater than -1")

    result = frame.copy()
    result["exposure"] = exposure
    result["turnover"] = result["exposure"].diff().abs().fillna(result["exposure"].abs())
    # Liquidate every sealed fold so no position or uncharged state crosses folds.
    if len(result):
        turnover = result["turnover"].to_numpy(dtype=np.float64, copy=True)
        turnover[-1] += float(result["exposure"].iloc[-1])
        result["turnover"] = turnover
    one_way = config.costs.one_way_rate * cost_multiplier
    result["trading_cost"] = result["turnover"] * one_way
    result["gross_return"] = result["exposure"] * result["target_return"]
    result["net_return"] = result["gross_return"] - result["trading_cost"]
    result["equity"] = (1.0 + result["net_return"]).cumprod()

    passive_net = result["target_return"].to_numpy(dtype=np.float64, copy=True)
    passive_gross = float(np.prod(1.0 + passive_net) - 1.0) if len(passive_net) else 0.0
    if len(passive_net):
        passive_net[0] -= one_way
        passive_net[-1] -= one_way
    passive_equity = pd.Series((1.0 + passive_net).cumprod(), index=result.index)

    periods = config.market.periods_per_year
    std = float(result["net_return"].std(ddof=0))
    entries = ((result["exposure"] > 0) & (result["exposure"].shift(1).fillna(0) == 0)).sum()
    metrics = {
        "net_return": float(result["equity"].iloc[-1] - 1) if len(result) else 0.0,
        "passive_return": float(passive_equity.iloc[-1] - 1) if len(result) else 0.0,
        "passive_gross_return": passive_gross,
        "annualized_volatility": std * np.sqrt(periods),
        "sharpe": float(result["net_return"].mean() / std * np.sqrt(periods)) if std else 0.0,
        "max_drawdown": _max_drawdown(result["equity"]),
        "turnover": float(result["turnover"].sum()),
        "trading_cost": float(result["trading_cost"].sum()),
        "average_exposure": float(result["exposure"].mean()),
        "entries": float(entries),
        "cost_multiplier": cost_multiplier,
    }
    return TradingEvaluation(frame=result, metrics=metrics)


def probability_to_exposure(
    frame: pd.DataFrame,
    probabilities: np.ndarray,
    *,
    threshold: float,
    config: AppConfig,
) -> np.ndarray:
    if len(frame) != len(probabilities):
        raise ValueError("Frame and probabilities must have equal length")
    if not 0 < threshold < 1:
        raise ValueError("threshold must be strictly between zero and one")
    required = {"realized_volatility"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Trading frame missing columns: {sorted(missing)}")
    probabilities = np.asarray(probabilities, dtype=np.float64)
    if not np.isfinite(probabilities).all() or ((probabilities < 0) | (probabilities > 1)).any():
        raise ValueError("Probabilities must be finite and inside [0, 1]")
    realized = frame["realized_volatility"].replace(0, np.nan)
    size = (config.risk.target_annualized_volatility / realized).clip(
        lower=0.0, upper=config.risk.max_exposure
    )
    size = size.where(size >= config.risk.min_exposure, 0.0).fillna(0.0)
    return np.where(probabilities >= threshold, size.to_numpy(dtype=np.float64), 0.0)


def evaluate_probabilities_as_strategy(
    frame: pd.DataFrame,
    probabilities: np.ndarray,
    *,
    threshold: float,
    config: AppConfig,
    cost_multiplier: float = 1.0,
) -> TradingEvaluation:
    exposure = probability_to_exposure(frame, probabilities, threshold=threshold, config=config)
    result = evaluate_exposure_as_strategy(
        frame, exposure, config=config, cost_multiplier=cost_multiplier
    )
    result.frame["probability"] = np.asarray(probabilities, dtype=np.float64)
    return TradingEvaluation(
        frame=result.frame,
        metrics={**result.metrics, "threshold": threshold},
    )


def choose_threshold(
    frame: pd.DataFrame,
    probabilities: np.ndarray,
    *,
    thresholds: tuple[float, ...],
    min_entries: int,
    drawdown_penalty: float,
    config: AppConfig,
) -> tuple[float, pd.DataFrame]:
    rows: list[dict[str, float]] = []
    for threshold in thresholds:
        evaluation = evaluate_probabilities_as_strategy(
            frame, probabilities, threshold=threshold, config=config
        )
        utility = evaluation.metrics["net_return"] - drawdown_penalty * abs(
            evaluation.metrics["max_drawdown"]
        )
        eligible = evaluation.metrics["entries"] >= min_entries
        rows.append({**evaluation.metrics, "utility": utility, "eligible": float(eligible)})
    table = pd.DataFrame(rows)
    candidates = table.loc[table["eligible"] == 1.0]
    if candidates.empty:
        candidates = table
    best = candidates.sort_values(["utility", "threshold"], ascending=[False, False]).iloc[0]
    return float(best["threshold"]), table


def _partition(frame: pd.DataFrame, partition: slice) -> pd.DataFrame:
    result = frame.iloc[partition].copy()
    return result.loc[result["target_positive"].notna()]


def _nan_probability_metrics() -> dict[str, float]:
    return {
        "accuracy": float("nan"),
        "brier": float("nan"),
        "log_loss": float("nan"),
        "roc_auc": float("nan"),
        "ece": float("nan"),
        "realized_positive_rate": float("nan"),
        "predicted_positive_rate": float("nan"),
    }


def run_sealed_benchmark(
    frame: pd.DataFrame,
    *,
    feature_columns: list[str],
    model_factories: list[ModelFactory],
    split_spec: SplitSpec,
    config: AppConfig,
    thresholds: tuple[float, ...] = (0.5, 0.55, 0.6, 0.65),
    min_entries: int = 3,
    drawdown_penalty: float = 0.5,
    cost_multipliers: tuple[float, ...] = (1.0, 1.5, 2.0),
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run train/calibrate/select/test without allowing final-test feedback."""

    if not feature_columns:
        raise ValueError("At least one feature column is required")
    if len(set(feature_columns)) != len(feature_columns):
        raise ValueError("Feature columns cannot contain duplicates")
    missing_features = set(feature_columns).difference(frame.columns)
    if missing_features:
        raise ValueError(f"Benchmark frame missing features: {sorted(missing_features)}")
    required = {
        "decision_time",
        "label_available_at",
        "target_positive",
        "target_return",
        "realized_volatility",
        "trend_desired_exposure",
    }
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Benchmark frame missing columns: {sorted(missing)}")
    decision_times = pd.to_datetime(frame["decision_time"], utc=True, errors="coerce")
    if decision_times.isna().any() or not decision_times.is_monotonic_increasing:
        raise ValueError("Benchmark decision_time must be valid and monotonic")
    if decision_times.duplicated().any():
        raise ValueError("Benchmark decision_time cannot contain duplicates")
    if not model_factories:
        raise ValueError("At least one model factory is required")

    folds = sealed_folds(len(frame), split_spec)
    if not folds:
        raise ValueError("No complete sealed fold can be constructed")
    metric_rows: list[dict[str, float | int | str]] = []
    prediction_frames: list[pd.DataFrame] = []
    stress_rows: list[dict[str, float | int | str]] = []

    for fold in folds:
        calibration_boundary = frame.iloc[fold.calibration.start]["decision_time"]
        validation_boundary = frame.iloc[fold.validation.start]["decision_time"]
        test_boundary = frame.iloc[fold.test.start]["decision_time"]
        train = purge_unknown_labels(frame, fold.train, known_by=calibration_boundary)
        calibration = purge_unknown_labels(frame, fold.calibration, known_by=validation_boundary)
        validation = purge_unknown_labels(frame, fold.validation, known_by=test_boundary)
        test = _partition(frame, fold.test)
        for name, partition in {
            "train": train,
            "calibration": calibration,
            "validation": validation,
            "test": test,
        }.items():
            if partition.empty:
                raise ValueError(f"Fold {fold.fold} has an empty {name} partition after purging")

        # Deterministic trend baseline: no calibration or threshold tuning.
        trend_exposure = test["trend_desired_exposure"].to_numpy(dtype=np.float64)
        trend_eval = evaluate_exposure_as_strategy(test, trend_exposure, config=config)
        metric_rows.append(
            {
                "fold": fold.fold,
                "model": "trend",
                "train_rows": len(train),
                "calibration_rows": len(calibration),
                "validation_rows": len(validation),
                "test_rows": len(test),
                **_nan_probability_metrics(),
                **trend_eval.metrics,
                "threshold": float("nan"),
            }
        )
        trend_predictions = trend_eval.frame.copy()
        trend_predictions.insert(0, "fold", fold.fold)
        trend_predictions.insert(1, "model", "trend")
        trend_predictions["probability"] = np.nan
        prediction_frames.append(trend_predictions)
        for multiplier in cost_multipliers:
            stressed = evaluate_exposure_as_strategy(
                test, trend_exposure, config=config, cost_multiplier=multiplier
            )
            stress_rows.append({"fold": fold.fold, "model": "trend", **stressed.metrics})

        x_train = train[feature_columns].to_numpy(dtype=np.float64)
        y_train = np.asarray(train["target_positive"].astype(int).to_numpy(), dtype=np.int64)
        x_cal = calibration[feature_columns].to_numpy(dtype=np.float64)
        y_cal = np.asarray(calibration["target_positive"].astype(int).to_numpy(), dtype=np.int64)
        x_val = validation[feature_columns].to_numpy(dtype=np.float64)
        x_test = test[feature_columns].to_numpy(dtype=np.float64)
        y_test = np.asarray(test["target_positive"].astype(int).to_numpy(), dtype=np.int64)

        for factory in model_factories:
            model = factory()
            if np.unique(y_train).size < 2:
                model = PriorProbabilityModel(name=f"{model.name}_prior_fallback").fit(
                    x_train, y_train
                )
            else:
                model.fit(x_train, y_train)
            raw_cal = model.predict_proba(x_cal)
            calibrator = PlattCalibrator(random_seed=config.ml.random_seed).fit(raw_cal, y_cal)
            val_prob = calibrator.transform(model.predict_proba(x_val))
            test_prob = calibrator.transform(model.predict_proba(x_test))
            threshold, _threshold_table = choose_threshold(
                validation,
                val_prob,
                thresholds=thresholds,
                min_entries=min_entries,
                drawdown_penalty=drawdown_penalty,
                config=config,
            )
            test_eval = evaluate_probabilities_as_strategy(
                test, test_prob, threshold=threshold, config=config
            )
            prob_metrics = probability_metrics(y_test, test_prob)
            metric_rows.append(
                {
                    "fold": fold.fold,
                    "model": model.name,
                    "train_rows": len(train),
                    "calibration_rows": len(calibration),
                    "validation_rows": len(validation),
                    "test_rows": len(test),
                    **prob_metrics,
                    **test_eval.metrics,
                }
            )
            predicted = test_eval.frame.copy()
            predicted.insert(0, "fold", fold.fold)
            predicted.insert(1, "model", model.name)
            predicted["target_positive"] = y_test
            prediction_frames.append(predicted)
            for multiplier in cost_multipliers:
                stressed = evaluate_probabilities_as_strategy(
                    test,
                    test_prob,
                    threshold=threshold,
                    config=config,
                    cost_multiplier=multiplier,
                )
                stress_rows.append({"fold": fold.fold, "model": model.name, **stressed.metrics})

    metrics = pd.DataFrame(metric_rows)
    predictions = pd.concat(prediction_frames).sort_index()
    stress = pd.DataFrame(stress_rows)
    return metrics, predictions, stress
