from __future__ import annotations

import importlib.util
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd
import pytest


def _load_assessor() -> Callable[[Path], dict[str, Any]]:
    script = (
        Path(__file__).resolve().parents[1] / "scripts" / "assess_phase2c_foundation.py"
    )
    spec = importlib.util.spec_from_file_location("assess_phase2c_foundation", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load assessment script: {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.assess


assess = _load_assessor()


def _write_inputs(root: Path, *, timesfm_net_return: float) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "foundation_manifest.json").write_text(
        json.dumps(
            {
                "dataset_sha256": "a" * 64,
                "manifest_sha256": "b" * 64,
            }
        ),
        encoding="utf-8",
    )
    comparison_rows: list[dict[str, object]] = []
    for scenario, net_return in (
        ("naive", 0.05),
        ("timesfm", timesfm_net_return),
        ("chronos", 0.04),
        ("timesfm_chronos", 0.04),
    ):
        comparison_rows.append(
            {
                "scenario": scenario,
                "model": "ridge_logistic",
                "net_return": net_return,
                "delta_net_return": 0.01 if scenario != "naive" else 0.0,
                "delta_sharpe": 0.2 if scenario != "naive" else 0.0,
                "delta_brier": -0.001 if scenario != "naive" else 0.0,
            }
        )
    pd.DataFrame(comparison_rows).to_csv(
        root / "baseline_vs_foundation.csv", index=False
    )

    pd.DataFrame(
        [
            {
                "scenario": scenario,
                "model": "ridge_logistic",
                "net_return": 0.01,
            }
            for scenario in ("timesfm", "chronos", "timesfm_chronos")
            for _ in range(4)
        ]
    ).to_csv(root / "scenario_fold_metrics.csv", index=False)
    pd.DataFrame(
        [
            {
                "scenario": scenario,
                "model": "ridge_logistic",
                "cost_multiplier": 2.0,
                "net_return": 0.01,
            }
            for scenario in ("timesfm", "chronos", "timesfm_chronos")
        ]
    ).to_csv(root / "scenario_cost_stress.csv", index=False)
    pd.DataFrame(
        [
            {
                "ablation": "all_features",
                "model": "ridge_logistic",
                "mean_net_return": 0.02,
            },
            {
                "ablation": "without_timesfm",
                "model": "ridge_logistic",
                "mean_net_return": 0.01,
            },
            {
                "ablation": "without_chronos",
                "model": "ridge_logistic",
                "mean_net_return": 0.01,
            },
        ]
    ).to_csv(root / "ablation_summary.csv", index=False)


def test_assessment_rejects_candidate_that_does_not_beat_naive(
    tmp_path: Path,
) -> None:
    _write_inputs(tmp_path, timesfm_net_return=0.04)

    result = assess(tmp_path)

    assert result["screening_outcome"] == "no_candidate_passed"
    assert result["screening_candidates"] == []
    timesfm = next(
        row for row in result["screening_results"] if row["scenario"] == "timesfm"
    )
    assert timesfm["delta_net_return_vs_naive"] == pytest.approx(-0.01)
    assert timesfm["flags"]["net_return_above_naive"] is False
    assert timesfm["all_screening_flags"] is False


def test_assessment_can_screen_candidate_that_beats_naive(tmp_path: Path) -> None:
    _write_inputs(tmp_path, timesfm_net_return=0.06)

    result = assess(tmp_path)

    assert result["screening_outcome"] == "candidate_passed"
    assert result["screening_candidates"] == [
        {"scenario": "timesfm", "model": "ridge_logistic"}
    ]
    assert result["schema_version"] == "1.2"
