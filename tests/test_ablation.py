import pandas as pd
import pytest

from hybrid_trader.ablation import build_ablation_plan, summarize_ablation


def test_ablation_plan_contains_incremental_and_leave_one_out() -> None:
    plan = build_ablation_plan({"market": ["a", "b"], "derivatives": ["c"], "fm": ["d"]})
    names = {item.name for item in plan}
    assert "all_features" in names
    assert "incremental_through_market" in names
    assert "incremental_through_derivatives" in names
    assert "without_market" in names
    assert "without_fm" in names


def test_ablation_rejects_overlapping_feature_groups() -> None:
    with pytest.raises(ValueError, match="only one"):
        build_ablation_plan({"a": ["x"], "b": ["x"]})


def test_ablation_summary_reports_positive_fold_rate() -> None:
    metrics = pd.DataFrame(
        {
            "ablation": ["all_features", "all_features"],
            "model": ["prior", "prior"],
            "fold": [0, 1],
            "net_return": [0.1, -0.05],
            "sharpe": [1.0, -0.5],
            "max_drawdown": [-0.1, -0.2],
            "brier": [0.24, 0.25],
        }
    )
    summary = summarize_ablation(metrics)
    assert summary["positive_fold_rate"].iloc[0] == 0.5
    assert summary["worst_drawdown"].iloc[0] == -0.2
