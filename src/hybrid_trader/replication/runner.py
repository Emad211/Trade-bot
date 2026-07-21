"""Deterministic Report 2.3 execution helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

import pandas as pd

from hybrid_trader.replication.artifacts import (
    load_tabular_artifact,
    parse_month_column,
    sha256_file,
)
from hybrid_trader.replication.factor_audit import (
    annualized_metrics,
    compare_factor_vintages,
)
from hybrid_trader.replication.provenance import ArtifactProvenance
from hybrid_trader.replication.verdicts import ReplicationStatus, ReplicationVerdict


def _find_date_column(frame: pd.DataFrame) -> str:
    for candidate in ("date", "month", "yyyymm", "year_month"):
        if candidate in frame.columns:
            return candidate
    raise ValueError("No recognized date column")


def _as_decimal_returns(
    values: pd.Series, return_scale: Literal["decimal", "percent"]
) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    return numeric / 100.0 if return_scale == "percent" else numeric


def run_aqr_vintage_audit(
    *,
    original_path: str | Path,
    maintained_path: str | Path,
    output_path: str | Path,
    return_scale: Literal["decimal", "percent"] | None = None,
    original_provenance: ArtifactProvenance | None = None,
    maintained_provenance: ArtifactProvenance | None = None,
) -> ReplicationVerdict:
    """Audit two factor vintages without upgrading unverified local files to a pass.

    `ARTIFACT_AUDIT_PASS` is possible only when both inputs are immutable official
    artifacts whose recorded size and SHA-256 match the local bytes, and the return
    unit is explicitly declared. This is still not a raw-paper replication verdict.
    """

    original_sha256 = (
        original_provenance.verify_local_file(original_path)
        if original_provenance is not None
        else sha256_file(original_path)
    )
    maintained_sha256 = (
        maintained_provenance.verify_local_file(maintained_path)
        if maintained_provenance is not None
        else sha256_file(maintained_path)
    )

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
        "original_sha256": original_sha256,
        "maintained_sha256": maintained_sha256,
        "original_rows": len(original),
        "maintained_rows": len(maintained),
        "overlap": [comparison.__dict__ for comparison in comparisons],
        "return_scale": return_scale,
        "maintained_factor_metrics": {},
    }
    if return_scale is not None:
        for comparison in comparisons:
            metrics["maintained_factor_metrics"][comparison.column] = annualized_metrics(
                _as_decimal_returns(maintained[comparison.column], return_scale)
            )

    immutable = bool(
        original_provenance
        and maintained_provenance
        and original_provenance.is_immutable_official
        and maintained_provenance.is_immutable_official
    )
    auditable_pass = immutable and return_scale is not None

    status = (
        ReplicationStatus.ARTIFACT_AUDIT_PASS
        if auditable_pass
        else ReplicationStatus.IMPLEMENTATION_READY
    )
    reasons = ["Factor vintages parsed and compared deterministically"]
    limitations = ["Processed factor audit does not reproduce the raw 58-instrument construction"]
    source_artifact_ids: list[str] = []
    exactness_class = "UNVERIFIED_LOCAL_FACTOR_AUDIT"

    if auditable_pass:
        reasons.append("Both files matched immutable official provenance records")
        source_artifact_ids = [original_sha256, maintained_sha256]
        exactness_class = "NEAR_EXACT_FACTOR_AUDIT"
    else:
        limitations.append(
            "No artifact-level pass is permitted until both inputs are immutable official "
            "artifacts and return units are declared"
        )

    verdict = ReplicationVerdict(
        experiment_id="R23-AQR-TSMOM-VINTAGE-AUDIT",
        status=status,
        exactness_class=exactness_class,
        reasons=reasons,
        metrics=metrics,
        source_artifact_ids=source_artifact_ids,
        limitations=limitations,
    )
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(verdict.model_dump(mode="json"), indent=2), encoding="utf-8")
    return verdict
