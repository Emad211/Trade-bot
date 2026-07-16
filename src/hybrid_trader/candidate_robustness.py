"""Phase 3A candidate assessment over sealed out-of-sample predictions."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from hybrid_trader.bootstrap_robustness import (
    circular_block_bootstrap,
    compounded_return,
    fold_concentration,
)
from hybrid_trader.data.snapshot import canonical_json_sha256
from hybrid_trader.regime_robustness import classify_market_regimes, regime_performance
from hybrid_trader.robustness_policy import RobustnessPolicy
from hybrid_trader.sharpe_robustness import sharpe_diagnostics


def _require_columns(frame: pd.DataFrame, columns: set[str], *, label: str) -> None:
    missing = columns.difference(frame.columns)
    if missing:
        raise ValueError(f"{label} missing columns: {sorted(missing)}")


def aggregate_trial_sharpes(trial_metrics: pd.DataFrame) -> np.ndarray:
    _require_columns(trial_metrics, {"model", "sharpe"}, label="trial metrics")
    grouping = [
        column for column in ("scenario", "ablation", "model") if column in trial_metrics.columns
    ]
    values = trial_metrics.groupby(grouping, dropna=False)["sharpe"].mean().to_numpy(dtype=float)
    values = values[np.isfinite(values)]
    if values.size < 2:
        raise ValueError("At least two finite trial Sharpe estimates are required")
    return values


def _aligned_model_returns(
    predictions: pd.DataFrame,
    *,
    model: str,
    benchmark_model: str,
) -> pd.DataFrame:
    keys = ["fold", "timestamp"]
    candidate = predictions.loc[
        predictions["model"].astype(str) == model,
        [*keys, "net_return", "realized_volatility", "ema_ratio"],
    ].copy()
    benchmark = predictions.loc[
        predictions["model"].astype(str) == benchmark_model,
        [*keys, "net_return"],
    ].copy()
    if candidate.empty or benchmark.empty:
        raise ValueError(f"Missing candidate or benchmark rows for {model}")
    if candidate.duplicated(keys).any() or benchmark.duplicated(keys).any():
        raise ValueError("Predictions must be unique per model, fold and timestamp")
    candidate = candidate.rename(columns={"net_return": "candidate_net_return"})
    benchmark = benchmark.rename(columns={"net_return": "benchmark_net_return"})
    aligned = candidate.merge(benchmark, on=keys, how="inner", validate="one_to_one")
    if len(aligned) != len(candidate) or len(aligned) != len(benchmark):
        raise ValueError(f"Candidate and benchmark histories are not fully aligned for {model}")
    return aligned.sort_values(keys).reset_index(drop=True)


def _fold_compounded_returns(aligned: pd.DataFrame) -> np.ndarray:
    return np.asarray(
        [
            compounded_return(group["candidate_net_return"].to_numpy(dtype=float))
            for _, group in aligned.groupby("fold", sort=True)
        ],
        dtype=np.float64,
    )


def _mean_two_x_cost_return(cost_stress: pd.DataFrame, *, model: str) -> float:
    _require_columns(
        cost_stress,
        {"model", "cost_multiplier", "net_return"},
        label="cost stress",
    )
    selected = cost_stress.loc[
        (cost_stress["model"].astype(str) == model)
        & np.isclose(cost_stress["cost_multiplier"].astype(float), 2.0)
    ]
    if selected.empty:
        raise ValueError(f"Missing 2x-cost rows for model {model}")
    return float(selected["net_return"].astype(float).mean())


def assess_candidate_robustness(
    predictions: pd.DataFrame,
    cost_stress: pd.DataFrame,
    trial_metrics: pd.DataFrame,
    policy: RobustnessPolicy,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Screen all non-benchmark models and return compact review artifacts."""

    _require_columns(
        predictions,
        {"timestamp", "fold", "model", "net_return", "realized_volatility", "ema_ratio"},
        label="predictions",
    )
    predictions = predictions.copy()
    predictions["timestamp"] = pd.to_datetime(predictions["timestamp"], utc=True, errors="raise")
    models = sorted(predictions["model"].astype(str).unique().tolist())
    if policy.benchmark_model not in models:
        raise ValueError(f"Benchmark model is absent: {policy.benchmark_model}")
    candidates = [model for model in models if model != policy.benchmark_model]
    if not candidates:
        raise ValueError("At least one non-benchmark candidate is required")

    trial_sharpes = aggregate_trial_sharpes(trial_metrics)
    if policy.declared_trials < trial_sharpes.size:
        raise ValueError("Policy declared_trials is smaller than the observed trial-family count")

    summary_rows: list[dict[str, Any]] = []
    regime_frames: list[pd.DataFrame] = []
    for model_index, model in enumerate(candidates):
        aligned = _aligned_model_returns(
            predictions,
            model=model,
            benchmark_model=policy.benchmark_model,
        )
        candidate_returns = aligned["candidate_net_return"].to_numpy(dtype=np.float64)
        benchmark_returns = aligned["benchmark_net_return"].to_numpy(dtype=np.float64)
        sharpe = sharpe_diagnostics(
            candidate_returns,
            trial_annualized_sharpes=trial_sharpes,
            declared_trials=policy.declared_trials,
            periods_per_year=policy.periods_per_year,
        )
        bootstrap = circular_block_bootstrap(
            candidate_returns,
            benchmark_returns,
            samples=policy.bootstrap_samples,
            block_length=policy.bootstrap_block_length,
            random_seed=policy.random_seed + model_index,
        )
        concentration = fold_concentration(_fold_compounded_returns(aligned))
        total_return = compounded_return(candidate_returns)
        two_x_cost_return = _mean_two_x_cost_return(cost_stress, model=model)

        flags = {
            "minimum_observations": candidate_returns.size >= policy.minimum_observations,
            "positive_total_return": (
                total_return > 0 if policy.require_positive_total_return else True
            ),
            "psr": sharpe.probabilistic_sharpe_ratio >= policy.minimum_psr,
            "dsr": sharpe.deflated_sharpe_ratio >= policy.minimum_dsr,
            "mean_improvement": bootstrap.observed_mean_difference > 0,
            "bootstrap_significance": (
                bootstrap.one_sided_pvalue <= policy.maximum_bootstrap_pvalue
                and bootstrap.confidence_interval_low > 0
            ),
            "positive_fold_ratio": (
                concentration.positive_fold_ratio >= policy.minimum_positive_fold_ratio
            ),
            "top_fold_concentration": (
                concentration.top_fold_profit_share <= policy.maximum_top_fold_profit_share
            ),
            "top_three_fold_concentration": (
                concentration.top_three_fold_profit_share
                <= policy.maximum_top_three_fold_profit_share
            ),
            "positive_two_x_cost_return": (
                two_x_cost_return > 0 if policy.require_positive_two_x_cost_return else True
            ),
        }
        summary_rows.append(
            {
                "model": model,
                "benchmark_model": policy.benchmark_model,
                "observations": int(candidate_returns.size),
                "total_return": total_return,
                "annualized_sharpe": sharpe.annualized_sharpe,
                "probabilistic_sharpe_ratio": sharpe.probabilistic_sharpe_ratio,
                "deflated_sharpe_ratio": sharpe.deflated_sharpe_ratio,
                "deflated_benchmark_annualized_sharpe": (
                    sharpe.deflated_benchmark_annualized_sharpe
                ),
                "skewness": sharpe.skewness,
                "pearson_kurtosis": sharpe.pearson_kurtosis,
                "mean_return_difference": bootstrap.observed_mean_difference,
                "bootstrap_pvalue": bootstrap.one_sided_pvalue,
                "bootstrap_ci_low": bootstrap.confidence_interval_low,
                "bootstrap_ci_high": bootstrap.confidence_interval_high,
                "positive_fold_ratio": concentration.positive_fold_ratio,
                "top_fold_profit_share": concentration.top_fold_profit_share,
                "top_three_fold_profit_share": concentration.top_three_fold_profit_share,
                "positive_profit_hhi": concentration.positive_profit_hhi,
                "mean_net_return_at_2x_cost": two_x_cost_return,
                "passed_rules": int(sum(flags.values())),
                "rule_count": len(flags),
                "eligible_for_human_freeze_review": bool(all(flags.values())),
                "failed_rules": ",".join(
                    sorted(name for name, passed in flags.items() if not passed)
                ),
            }
        )

        regimes = classify_market_regimes(
            aligned["realized_volatility"].to_numpy(dtype=np.float64),
            aligned["ema_ratio"].to_numpy(dtype=np.float64),
            low_volatility_threshold=policy.low_volatility_threshold,
            high_volatility_threshold=policy.high_volatility_threshold,
            trend_band=policy.trend_band,
        )
        regime_frame = regime_performance(
            candidate_returns,
            regimes,
            periods_per_year=policy.periods_per_year,
        )
        regime_frame.insert(0, "model", model)
        regime_frames.append(regime_frame)

    summary = pd.DataFrame(summary_rows).sort_values(
        ["eligible_for_human_freeze_review", "deflated_sharpe_ratio", "total_return"],
        ascending=[False, False, False],
    )
    regimes = pd.concat(regime_frames, ignore_index=True)
    passing = summary.loc[summary["eligible_for_human_freeze_review"]]
    verdict = (
        "candidate_requires_human_freeze_review" if not passing.empty else "no_candidate_passed"
    )
    action = "human_review_before_new_experiment" if not passing.empty else "retain_research_only"

    summary_records = json.loads(summary.to_json(orient="records"))
    regime_records = json.loads(regimes.to_json(orient="records"))
    identity = {
        "policy": policy.model_dump(mode="json"),
        "trial_sharpes": trial_sharpes.tolist(),
        "summary": summary_records,
        "regimes": regime_records,
    }
    assessment: dict[str, Any] = {
        "schema_version": "1.0",
        "assessment_id": canonical_json_sha256(identity),
        "verdict": verdict,
        "recommended_action": action,
        "automatic_promotion_allowed": False,
        "prospective_ledger_started": False,
        "candidate_count": len(candidates),
        "passing_candidate_count": int(len(passing)),
        "passing_candidates": passing["model"].astype(str).tolist(),
        "benchmark_model": policy.benchmark_model,
        "declared_trials": policy.declared_trials,
        "observed_trial_family_count": int(trial_sharpes.size),
        "policy": policy.model_dump(mode="json"),
    }
    return summary.reset_index(drop=True), regimes, assessment
