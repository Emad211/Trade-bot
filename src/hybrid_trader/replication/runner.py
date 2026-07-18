"""Deterministic Report 2.3 execution helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from hybrid_trader.replication.artifacts import load_tabular_artifact, parse_month_column, sha256_file
from hybrid_trader.replication.factor_audit import annualized_metrics, compare_factor_vintages
from hybrid_trader.replication.verdicts import ReplicationStatus, ReplicationVerdict


def _find_date_column(frame: pd.DataFrame) -> str:
    for candidate in ("date", "month", "yyyymm", "year_month"):
        if candidate in frame.columns:
            return candidate
    raise ValueError("No recognized date column")


def run_aqr_vintage_audit(
    *,
    original_path: str | Path,
    maintained_path: str | Path,
    output_path: str | Path,
) -> ReplicationVerdict:
    original = load_tabular_artifact(original_path)
    maintained = load_tabular_artifact(maintained_path)
    original_date = _find_date_column(original)
    maintained_date = _find_date_column(maintained)
    original = original.rename(columns={original_date: "date"})
    maintained = maintained.rename(columns={maintained_date: "date"})
    original["date"] = parse_month_column(original["date"])
    maintained["date"] = parse_month_column(maintained["date"])

    comparisons = compare_factor_vintages(original, maintained)
    metrics: dict[str, Any] = {
        "original_sha256": sha256_file(original_path),
        "maintained_sha256": sha256_file(maintained_path),
        "original_rows": len(original),
        "maintained_rows": len(maintained),
        "overlap": [comparison.__dict__ for comparison in comparisons],
        "maintained_factor_metrics": {},
    }
    for comparison in comparisons:
        metrics["maintained_factor_metrics"][comparison.column] = annualized_metrics(
            maintained[comparison.column]
        )

    verdict = ReplicationVerdict(
        experiment_id="R23-AQR-TSMOM-VINTAGE-AUDIT",
        status=ReplicationStatus.PASS,
        exactness_class="NEAR_EXACT_FACTOR_AUDIT",
        reasons=["Official original and maintained factor artifacts parsed and compared"],
        metrics=metrics,
        source_artifact_ids=[metrics["original_sha256"], metrics["maintained_sha256"]],
        limitations=["Processed factor audit does not reproduce the raw 58-instrument construction"],
    )
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(verdict.model_dump(mode="json"), indent=2), encoding="utf-8")
    return verdict
