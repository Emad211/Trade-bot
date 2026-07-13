"""Phase 2C reports for concentration, tail behavior, costs and promotion gates."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from hybrid_trader.phase2c import Phase2CSpec


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, (np.floating, float)):
        return None if not np.isfinite(float(value)) else float(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    return value


@dataclass(frozen=True)
class ReportArtifacts:
    model_summary: pd.DataFrame
    conditional_large_moves: pd.DataFrame
    cost_resilience: pd.DataFrame
    gate_results: pd.DataFrame
    payload: dict[str, Any]


def _safe_compound(values: pd.Series) -> float:
    array = values.to_numpy(dtype=float)
    if not np.isfinite(array).all() or (array <= -1).any():
        return float("nan")
    return float(np.prod(1.0 + array) - 1.0)


def summarize_models(metrics: pd.DataFrame) -> pd.DataFrame:
    required = {"fold", "model", "net_return", "sharpe", "max_drawdown", "brier"}
    missing = required.difference(metrics.columns)
    if missing:
        raise ValueError(f"Fold metrics missing: {sorted(missing)}")
    rows: list[dict[str, Any]] = []
    for model, group in metrics.groupby("model", sort=True):
        absolute = group["net_return"].abs()
        concentration = float(absolute.max() / absolute.sum()) if absolute.sum() > 0 else 0.0
        rows.append(
            {
                "model": model,
                "folds": len(group),
                "compounded_net_return": _safe_compound(group["net_return"]),
                "mean_net_return": float(group["net_return"].mean()),
                "median_net_return": float(group["net_return"].median()),
                "positive_fold_rate": float((group["net_return"] > 0).mean()),
                "worst_fold_return": float(group["net_return"].min()),
                "best_fold_return": float(group["net_return"].max()),
                "fold_concentration": concentration,
                "mean_sharpe": float(group["sharpe"].mean()),
                "worst_drawdown": float(group["max_drawdown"].min()),
                "mean_brier": float(group["brier"].mean(skipna=True)),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["compounded_net_return", "mean_sharpe"], ascending=False, na_position="last"
    )


def summarize_large_moves(predictions: pd.DataFrame, *, quantile: float) -> pd.DataFrame:
    required = {"model", "target_return", "net_return", "gross_return", "exposure"}
    missing = required.difference(predictions.columns)
    if missing:
        raise ValueError(f"Predictions missing: {sorted(missing)}")
    if not 0.5 < quantile < 1:
        raise ValueError("large-move quantile must be inside (0.5, 1)")

    unique_target = predictions[["target_return"]].reset_index().drop_duplicates(subset="timestamp")
    cutoff = float(unique_target["target_return"].abs().quantile(quantile))
    rows: list[dict[str, Any]] = []
    for model, group in predictions.groupby("model", sort=True):
        large = group.loc[group["target_return"].abs() >= cutoff].copy()
        upside = large.loc[large["target_return"] > 0]
        downside = large.loc[large["target_return"] < 0]
        active = large.loc[large["exposure"] > 0]
        probability_source = (
            large["probability"]
            if "probability" in large
            else pd.Series(np.nan, index=large.index, dtype=float)
        )
        probability = pd.to_numeric(probability_source, errors="coerce")
        directional_accuracy = float("nan")
        if probability.notna().any() and "target_positive" in large:
            valid = probability.notna() & large["target_positive"].notna()
            if valid.any():
                directional_accuracy = float(
                    (
                        (probability.loc[valid] >= 0.5).astype(int)
                        == large.loc[valid, "target_positive"]
                    ).mean()
                )
        rows.append(
            {
                "model": model,
                "large_move_quantile": quantile,
                "absolute_return_cutoff": cutoff,
                "observations": len(large),
                "active_observations": len(active),
                "active_rate": float((large["exposure"] > 0).mean()) if len(large) else 0.0,
                "large_move_net_return": _safe_compound(large["net_return"]),
                "large_move_mean_net_return": float(large["net_return"].mean())
                if len(large)
                else 0.0,
                "active_trade_hit_rate": float((active["gross_return"] > 0).mean())
                if len(active)
                else float("nan"),
                "mean_exposure_upside": float(upside["exposure"].mean())
                if len(upside)
                else float("nan"),
                "mean_exposure_downside": float(downside["exposure"].mean())
                if len(downside)
                else float("nan"),
                "directional_accuracy": directional_accuracy,
            }
        )
    return pd.DataFrame(rows)


def summarize_cost_resilience(cost_stress: pd.DataFrame) -> pd.DataFrame:
    required = {"model", "fold", "cost_multiplier", "net_return", "max_drawdown"}
    missing = required.difference(cost_stress.columns)
    if missing:
        raise ValueError(f"Cost-stress metrics missing: {sorted(missing)}")
    rows: list[dict[str, Any]] = []
    for (model, _multiplier), group in cost_stress.groupby(["model", "cost_multiplier"], sort=True):
        multiplier_value = float(group["cost_multiplier"].iloc[0])
        rows.append(
            {
                "model": model,
                "cost_multiplier": multiplier_value,
                "folds": len(group),
                "compounded_net_return": _safe_compound(group["net_return"]),
                "mean_net_return": float(group["net_return"].mean()),
                "positive_fold_rate": float((group["net_return"] > 0).mean()),
                "worst_drawdown": float(group["max_drawdown"].min()),
            }
        )
    return pd.DataFrame(rows)


def evaluate_promotion_gates(
    model_summary: pd.DataFrame,
    cost_resilience: pd.DataFrame,
    spec: Phase2CSpec,
) -> pd.DataFrame:
    two_x_rows = cost_resilience.loc[np.isclose(cost_resilience["cost_multiplier"], 2.0)]
    two_x_returns = {
        str(row.model): float(str(row.compounded_net_return))
        for row in two_x_rows.itertuples(index=False)
    }
    rows: list[dict[str, Any]] = []
    for row in model_summary.to_dict(orient="records"):
        model = str(row["model"])
        stress_return = two_x_returns[model] if model in two_x_returns else float("nan")
        checks = {
            "enough_folds": int(row["folds"]) >= spec.gate.minimum_test_folds,
            "positive_fold_rate": float(row["positive_fold_rate"])
            >= spec.gate.minimum_positive_fold_rate,
            "fold_concentration": float(row["fold_concentration"])
            <= spec.gate.maximum_fold_concentration,
            "maximum_drawdown": float(row["worst_drawdown"]) >= spec.gate.maximum_drawdown,
            "two_x_cost_positive": bool(np.isfinite(stress_return) and stress_return > 0)
            if spec.gate.require_positive_two_x_cost_return
            else True,
        }
        passed = all(checks.values())
        rows.append(
            {
                "model": model,
                **checks,
                "two_x_cost_compounded_return": stress_return,
                "gate_passed": passed,
                "classification": "candidate" if passed else "reject_or_insufficient",
            }
        )
    return pd.DataFrame(rows)


def build_phase2c_report(experiment_dir: str | Path, spec: Phase2CSpec) -> ReportArtifacts:
    root = Path(experiment_dir)
    metrics = pd.read_csv(root / "fold_metrics.csv")
    predictions = pd.read_csv(root / "predictions.csv.gz", index_col=0, parse_dates=True)
    stress = pd.read_csv(root / "cost_stress.csv")
    experiment = json.loads((root / "experiment.json").read_text("utf-8"))

    summary = summarize_models(metrics)
    conditional = summarize_large_moves(predictions, quantile=spec.large_move_quantile)
    resilience = summarize_cost_resilience(stress)
    gates = evaluate_promotion_gates(summary, resilience, spec)
    present_models = set(summary["model"].astype(str))
    expected_models = set(spec.model_matrix)
    missing_models = sorted(expected_models.difference(present_models))
    payload = _json_safe(
        {
            "schema_version": "1.0",
            "experiment_name": spec.experiment_name,
            "plan_sha256": spec.plan_sha256,
            "experiment_id": experiment["experiment_id"],
            "dataset_sha256": experiment["dataset_sha256"],
            "large_move_quantile": spec.large_move_quantile,
            "matrix_coverage": {
                "expected": sorted(expected_models),
                "present": sorted(present_models),
                "missing": missing_models,
                "complete": not missing_models,
            },
            "execution_status": "complete" if not missing_models else "incomplete_model_matrix",
            "models": summary.to_dict(orient="records"),
            "conditional_large_moves": conditional.to_dict(orient="records"),
            "cost_resilience": resilience.to_dict(orient="records"),
            "promotion_gates": gates.to_dict(orient="records"),
        }
    )
    return ReportArtifacts(
        model_summary=summary,
        conditional_large_moves=conditional,
        cost_resilience=resilience,
        gate_results=gates,
        payload=payload,
    )


def _markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    columns = list(frame.columns)
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows: list[str] = []
    for values in frame.itertuples(index=False, name=None):
        rendered = []
        for value in values:
            if isinstance(value, float):
                rendered.append("nan" if np.isnan(value) else f"{value:.6g}")
            else:
                rendered.append(str(value))
        rows.append("| " + " | ".join(rendered) + " |")
    return "\n".join([header, separator, *rows])


def write_phase2c_report(artifacts: ReportArtifacts, output_dir: str | Path) -> Path:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    artifacts.model_summary.to_csv(root / "model_summary.csv", index=False)
    artifacts.conditional_large_moves.to_csv(root / "conditional_large_moves.csv", index=False)
    artifacts.cost_resilience.to_csv(root / "cost_resilience.csv", index=False)
    artifacts.gate_results.to_csv(root / "promotion_gates.csv", index=False)
    (root / "phase2c_report.json").write_text(
        json.dumps(artifacts.payload, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    markdown = [
        "# Phase 2C benchmark report",
        "",
        f"- Experiment: `{artifacts.payload['experiment_name']}`",
        f"- Plan SHA-256: `{artifacts.payload['plan_sha256']}`",
        f"- Experiment ID: `{artifacts.payload['experiment_id']}`",
        f"- Execution status: `{artifacts.payload['execution_status']}`",
        f"- Missing matrix entries: `{', '.join(artifacts.payload['matrix_coverage']['missing']) or 'none'}`",
        "",
        "## Model summary",
        "",
        _markdown_table(artifacts.model_summary),
        "",
        "## Conditional performance on large moves",
        "",
        _markdown_table(artifacts.conditional_large_moves),
        "",
        "## Cost resilience",
        "",
        _markdown_table(artifacts.cost_resilience),
        "",
        "## Promotion gates",
        "",
        _markdown_table(artifacts.gate_results),
        "",
        "> Gate passage is a research-candidate classification, not permission for live trading.",
        "",
    ]
    (root / "phase2c_report.md").write_text("\n".join(markdown), encoding="utf-8")
    return root
