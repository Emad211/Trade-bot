from __future__ import annotations

import numpy as np
import pandas as pd

from hybrid_trader.candidate_robustness import assess_candidate_robustness
from hybrid_trader.robustness_policy import RobustnessPolicy


def _predictions() -> pd.DataFrame:
    rng = np.random.default_rng(21)
    timestamps = pd.date_range("2025-01-01", periods=600, freq="4h", tz="UTC")
    benchmark = rng.normal(0.0, 0.0008, size=600)
    good = benchmark + rng.normal(0.0006, 0.00015, size=600)
    bad = benchmark - 0.0004
    rows: list[pd.DataFrame] = []
    for model, returns in {
        "trend": benchmark,
        "good_model": good,
        "bad_model": bad,
    }.items():
        rows.append(
            pd.DataFrame(
                {
                    "timestamp": timestamps,
                    "fold": np.repeat(np.arange(6), 100),
                    "model": model,
                    "net_return": returns,
                    "realized_volatility": np.tile([0.3, 0.6, 1.0], 200),
                    "ema_ratio": np.tile([0.02, -0.02, 0.0], 200),
                }
            )
        )
    return pd.concat(rows, ignore_index=True)


def _cost_stress() -> pd.DataFrame:
    rows = []
    for model, value in {
        "trend": 0.002,
        "good_model": 0.04,
        "bad_model": -0.03,
    }.items():
        for fold in range(6):
            rows.append(
                {
                    "fold": fold,
                    "model": model,
                    "cost_multiplier": 2.0,
                    "net_return": value,
                }
            )
    return pd.DataFrame(rows)


def _trial_metrics() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ablation": ["a", "a", "a", "b", "b", "b"],
            "model": ["trend", "good_model", "bad_model"] * 2,
            "sharpe": [0.0, 0.2, -0.1, 0.1, 0.3, -0.2],
        }
    )


def test_candidate_robustness_passes_only_stable_candidate() -> None:
    policy = RobustnessPolicy(
        declared_trials=12,
        bootstrap_samples=1000,
        minimum_observations=500,
        minimum_psr=0.90,
        minimum_dsr=0.80,
        maximum_bootstrap_pvalue=0.05,
        minimum_positive_fold_ratio=0.5,
        maximum_top_fold_profit_share=0.30,
        maximum_top_three_fold_profit_share=0.60,
    )
    summary, regimes, assessment = assess_candidate_robustness(
        _predictions(),
        _cost_stress(),
        _trial_metrics(),
        policy,
    )
    good = summary.loc[summary.model == "good_model"].iloc[0]
    bad = summary.loc[summary.model == "bad_model"].iloc[0]
    assert bool(good.eligible_for_human_freeze_review)
    assert not bool(bad.eligible_for_human_freeze_review)
    assert assessment["verdict"] == "candidate_requires_human_freeze_review"
    assert assessment["automatic_promotion_allowed"] is False
    assert assessment["passing_candidates"] == ["good_model"]
    assert set(regimes.model) == {"good_model", "bad_model"}


def test_candidate_robustness_fails_when_trial_count_is_underdeclared() -> None:
    policy = RobustnessPolicy(declared_trials=2, bootstrap_samples=500)
    try:
        assess_candidate_robustness(
            _predictions(),
            _cost_stress(),
            _trial_metrics(),
            policy,
        )
    except ValueError as exc:
        assert "declared_trials" in str(exc)
    else:
        raise AssertionError("Underdeclared trial families must fail closed")
