"""Phase 2C diagnostic and research-report helpers."""

from __future__ import annotations

from typing import Any, cast

import numpy as np
import pandas as pd

from hybrid_trader.data.quality import BarQualityReport, CrossVenueQualityReport
from hybrid_trader.phase2c_contracts import Phase2CRegistry, Phase2CSpec


def _conditional(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (model, fold), group in predictions.groupby(["model", "fold"]):
        cutoff = float(group.target_return.abs().quantile(0.9))
        large = group.loc[group.target_return.abs() >= cutoff]
        if large.empty:
            continue
        if large.probability.notna().any():
            predicted = large.probability >= 0.5
        else:
            predicted = large.exposure > 0
        rows.append(
            {
                "model": str(model),
                "fold": int(cast(int, fold)),
                "large_move_threshold": cutoff,
                "large_move_rows": len(large),
                "directional_accuracy": float(
                    (predicted.to_numpy() == (large.target_return > 0).to_numpy()).mean()
                ),
                "net_return_sum": float(large.net_return.sum()),
            }
        )
    return pd.DataFrame(rows)


def _concentration(metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for model, group in metrics.groupby("model"):
        values = group.sort_values("fold").net_return.to_numpy(float)
        positive = np.clip(values, 0, None)
        total = positive.sum()
        rows.append(
            {
                "model": str(model),
                "folds": len(values),
                "mean_fold_net_return": float(values.mean()),
                "best_fold": float(values.max()),
                "worst_fold": float(values.min()),
                "positive_fold_ratio": float((values > 0).mean()),
                "best_positive_fold_share": (float(positive.max() / total) if total > 0 else None),
            }
        )
    return pd.DataFrame(rows)


def _markdown(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    columns = [str(column) for column in frame.columns]
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = []
    for values in frame.itertuples(index=False, name=None):
        cells = [str(value).replace("|", "\\|").replace("\n", " ") for value in values]
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, separator, *rows])


def _report(
    spec: Phase2CSpec,
    registry: Phase2CRegistry,
    quality: list[BarQualityReport],
    cross: list[CrossVenueQualityReport],
    missingness: dict[str, float],
    summary: pd.DataFrame,
    stress: pd.DataFrame,
    conditional: pd.DataFrame,
    concentration: pd.DataFrame,
    experiment_id: str,
) -> str:
    source_rows = pd.DataFrame(
        [
            {
                "source": item.source_id,
                "type": item.source_type,
                "status": item.status,
                "rows": item.row_count,
                "error": item.error or "",
            }
            for item in registry.attempts
        ]
    )
    stress_summary = stress.groupby(["model", "cost_multiplier"], as_index=False).agg(
        mean_net_return=("net_return", "mean"),
        mean_sharpe=("sharpe", "mean"),
    )
    missing = pd.DataFrame(
        list(missingness.items()),
        columns=["column", "missing_ratio"],
    ).sort_values("missing_ratio", ascending=False)
    parts = [
        "# Phase 2C real-data benchmark",
        "",
        f"- Observation cutoff: `{spec.as_of.isoformat()}`",
        f"- Registry ID: `{registry.registry_id}`",
        f"- Combined snapshot: `{registry.combined_snapshot_sha256}`",
        f"- Experiment ID: `{experiment_id}`",
        "",
        "> Historical research only; no credentials or orders were used.",
        "",
        "## Sources",
        "",
        _markdown(source_rows),
        "",
        "## Spot quality",
        "",
        _markdown(pd.DataFrame([item.model_dump(mode="json") for item in quality])),
        "",
        "## Cross-venue diagnostics",
        "",
        _markdown(pd.DataFrame([item.model_dump(mode="json") for item in cross])),
        "",
        "## Benchmark",
        "",
        _markdown(summary),
        "",
        "## Cost stress",
        "",
        _markdown(stress_summary),
        "",
        "## Fold concentration",
        "",
        _markdown(concentration),
        "",
        "## Large moves",
        "",
        _markdown(conditional),
        "",
        "## Missingness",
        "",
        _markdown(missing),
        "",
        "A positive historical result is not a deployment approval.",
        "",
    ]
    return "\n".join(parts)
