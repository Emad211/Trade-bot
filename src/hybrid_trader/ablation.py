"""Feature-group ablation plans and comparative reports."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class AblationRun:
    name: str
    columns: tuple[str, ...]


def build_ablation_plan(
    groups: dict[str, list[str]],
    *,
    include_incremental: bool = True,
    include_leave_one_out: bool = True,
) -> list[AblationRun]:
    """Build auditable incremental and leave-one-group-out comparisons."""

    if not groups:
        raise ValueError("At least one feature group is required")
    if any(not columns for columns in groups.values()):
        raise ValueError("Feature groups cannot be empty")

    ordered_names = list(groups)
    flattened = [column for name in ordered_names for column in groups[name]]
    if len(flattened) != len(set(flattened)):
        raise ValueError("A feature column may belong to only one ablation group")
    all_columns = tuple(flattened)

    plan: list[AblationRun] = [AblationRun(name="all_features", columns=all_columns)]
    if include_incremental:
        active: list[str] = []
        for name in ordered_names[:-1]:
            active.extend(groups[name])
            plan.append(AblationRun(name=f"incremental_through_{name}", columns=tuple(active)))
    if include_leave_one_out and len(groups) > 1:
        for omitted in ordered_names:
            columns = tuple(
                column for name in ordered_names if name != omitted for column in groups[name]
            )
            plan.append(AblationRun(name=f"without_{omitted}", columns=columns))
    return plan


def summarize_ablation(metrics: pd.DataFrame) -> pd.DataFrame:
    required = {"ablation", "model", "fold", "net_return", "sharpe", "max_drawdown", "brier"}
    missing = required.difference(metrics.columns)
    if missing:
        raise ValueError(f"Ablation metrics missing: {sorted(missing)}")
    return (
        metrics.groupby(["ablation", "model"], as_index=False)
        .agg(
            folds=("fold", "count"),
            mean_net_return=("net_return", "mean"),
            median_net_return=("net_return", "median"),
            positive_fold_rate=("net_return", lambda values: float((values > 0).mean())),
            mean_sharpe=("sharpe", "mean"),
            worst_drawdown=("max_drawdown", "min"),
            mean_brier=("brier", "mean"),
        )
        .sort_values(["mean_net_return", "mean_sharpe"], ascending=False)
    )
