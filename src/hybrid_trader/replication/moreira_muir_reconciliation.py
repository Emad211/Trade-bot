"""Reconcile published Moreira-Muir unmanaged factors to current official sources."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .kenneth_french_monthly import (
    SNAPSHOT_ID as MONTHLY_SNAPSHOT_ID,
)
from .kenneth_french_monthly import (
    SOURCE_CONTRACTS as MONTHLY_SOURCE_CONTRACTS,
)
from .kenneth_french_monthly import (
    build_selected_monthly_panel,
    parse_monthly_zip,
    validate_data_library_page,
)
from .moreira_muir import (
    EXPECTED_SHA256 as AUTHOR_SOURCE_SHA256,
)
from .moreira_muir import (
    SNAPSHOT_ID as AUTHOR_SNAPSHOT_ID,
)
from .moreira_muir import parse_official_factor_bytes, validate_author_page

RECONCILIATION_ID = "MOREIRA_MUIR_CURRENT_MONTHLY_SOURCE_RECONCILIATION_V1"
RECONCILIATION_FACTORS = (
    "Mkt-RF",
    "SMB",
    "HML",
    "Mom",
    "RMW",
    "CMA",
    "RF",
)
SAFE_DECIMAL_PLACES = 12
NUMERICAL_ZERO_TOLERANCE = 1e-12


@dataclass(frozen=True)
class FactorSourceReconciliation:
    factor: str
    overlap_count: int
    first_overlap_month: str
    last_overlap_month: str
    exact_equal_count: int
    exact_mismatch_count: int
    numerical_tolerance_mismatch_count: int
    maximum_absolute_difference_percent: float
    mean_absolute_difference_percent: float
    first_exact_mismatch_month: str | None
    last_exact_mismatch_month: str | None
    difference_vector_sha256: str
    exact_current_source_match: bool


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_difference(value: float) -> float:
    if abs(value) <= NUMERICAL_ZERO_TOLERANCE:
        return 0.0
    return round(value, SAFE_DECIMAL_PLACES)


def reconcile_unmanaged_factors(
    author_frame: pd.DataFrame,
    monthly_panel: pd.DataFrame,
) -> tuple[FactorSourceReconciliation, ...]:
    """Compare source identities only; do not calculate investment performance."""

    if "Date" not in author_frame.columns:
        raise ValueError("Author frame lacks Date")
    author = author_frame.set_index("Date")
    if not isinstance(monthly_panel.index, pd.DatetimeIndex):
        raise ValueError("Monthly panel must use a DatetimeIndex")

    results: list[FactorSourceReconciliation] = []
    for factor in RECONCILIATION_FACTORS:
        if factor not in author.columns:
            raise ValueError(f"Author frame lacks {factor}")
        if factor not in monthly_panel.columns:
            raise ValueError(f"Monthly panel lacks {factor}")
        paired = pd.concat(
            [
                author[[factor]].rename(columns={factor: "author"}),
                monthly_panel[[factor]].rename(columns={factor: "current"}),
            ],
            axis=1,
            join="inner",
        ).dropna()
        if paired.empty:
            raise ValueError(f"No overlapping observations for {factor}")
        if not paired.index.is_monotonic_increasing or not paired.index.is_unique:
            raise ValueError(f"Invalid reconciliation index for {factor}")

        difference = paired["author"] - paired["current"]
        exact_mismatch = difference != 0.0
        tolerance_mismatch = difference.abs() > NUMERICAL_ZERO_TOLERANCE
        canonical_rows = [
            f"{pd.Timestamp(month).strftime('%Y-%m')}|{_canonical_difference(float(value)):.12f}"
            for month, value in difference.items()
        ]
        mismatch_months = paired.index[exact_mismatch]
        absolute_difference = difference.abs()
        maximum = float(absolute_difference.max())
        mean = float(absolute_difference.mean())
        if not math.isfinite(maximum) or not math.isfinite(mean):
            raise ValueError(f"Non-finite reconciliation metric for {factor}")
        results.append(
            FactorSourceReconciliation(
                factor=factor,
                overlap_count=len(paired),
                first_overlap_month=pd.Timestamp(paired.index[0]).strftime("%Y-%m"),
                last_overlap_month=pd.Timestamp(paired.index[-1]).strftime("%Y-%m"),
                exact_equal_count=int((~exact_mismatch).sum()),
                exact_mismatch_count=int(exact_mismatch.sum()),
                numerical_tolerance_mismatch_count=int(tolerance_mismatch.sum()),
                maximum_absolute_difference_percent=round(maximum, SAFE_DECIMAL_PLACES),
                mean_absolute_difference_percent=round(mean, SAFE_DECIMAL_PLACES),
                first_exact_mismatch_month=(
                    pd.Timestamp(mismatch_months[0]).strftime("%Y-%m")
                    if len(mismatch_months)
                    else None
                ),
                last_exact_mismatch_month=(
                    pd.Timestamp(mismatch_months[-1]).strftime("%Y-%m")
                    if len(mismatch_months)
                    else None
                ),
                difference_vector_sha256=sha256_bytes(
                    ("\n".join(canonical_rows) + "\n").encode("utf-8")
                ),
                exact_current_source_match=not bool(exact_mismatch.any()),
            )
        )
    return tuple(results)


def safe_reconciliation_evidence(
    *,
    author_csv: bytes,
    author_page: bytes,
    data_library_page: bytes,
    monthly_zips: Mapping[str, bytes],
) -> dict[str, Any]:
    if set(monthly_zips) != set(MONTHLY_SOURCE_CONTRACTS):
        raise ValueError("Monthly ZIP set is incomplete or contains extras")
    author_frame = parse_official_factor_bytes(author_csv)
    author_page_identity = validate_author_page(author_page)
    data_library_identity = validate_data_library_page(data_library_page)
    parsed_monthly = {
        key: parse_monthly_zip(monthly_zips[key], contract)
        for key, contract in MONTHLY_SOURCE_CONTRACTS.items()
    }
    monthly_panel = build_selected_monthly_panel(parsed_monthly)
    reconciliations = reconcile_unmanaged_factors(author_frame, monthly_panel)
    exact_match_count = sum(item.exact_current_source_match for item in reconciliations)
    mismatch_count = len(reconciliations) - exact_match_count
    gate = (
        "EXACT_CURRENT_SOURCE_MATCH"
        if mismatch_count == 0
        else "CURRENT_SOURCE_REVISION_DIFFERENCES_RETAINED"
    )
    return {
        "schema_version": "1.0",
        "reconciliation_id": RECONCILIATION_ID,
        "author_snapshot_id": AUTHOR_SNAPSHOT_ID,
        "author_source_sha256": AUTHOR_SOURCE_SHA256,
        "author_page": author_page_identity,
        "monthly_snapshot_id": MONTHLY_SNAPSHOT_ID,
        "data_library": data_library_identity,
        "monthly_source_identities": {
            key: {
                "zip_sha256": source.zip_sha256,
                "member_sha256": source.member_sha256,
            }
            for key, source in parsed_monthly.items()
        },
        "factor_results": [asdict(item) for item in reconciliations],
        "factor_count": len(reconciliations),
        "exact_match_factor_count": exact_match_count,
        "mismatch_factor_count": mismatch_count,
        "gate": gate,
        "data_state": "CURRENT_REVISED_PUBLIC_RECONSTRUCTION_SOURCE",
        "paper_vintage_verified": False,
        "row_level_data_uploaded": False,
        "performance_calculated": False,
        "annualized_return_calculated": False,
        "sharpe_calculated": False,
        "alpha_calculated": False,
        "paper_replication_pass": False,
        "economic_edge_verdict": "INCONCLUSIVE",
    }


def write_safe_reconciliation_evidence(
    *,
    author_csv_path: str | Path,
    author_page_path: str | Path,
    data_library_path: str | Path,
    monthly_zip_paths: Mapping[str, str | Path],
    output_dir: str | Path,
) -> dict[str, Any]:
    evidence = safe_reconciliation_evidence(
        author_csv=Path(author_csv_path).read_bytes(),
        author_page=Path(author_page_path).read_bytes(),
        data_library_page=Path(data_library_path).read_bytes(),
        monthly_zips={key: Path(value).read_bytes() for key, value in monthly_zip_paths.items()},
    )
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    evidence_bytes = (json.dumps(evidence, indent=2, sort_keys=True) + "\n").encode()
    (output_root / "safe-source-reconciliation-evidence.json").write_bytes(evidence_bytes)
    summary = {
        "reconciliation_id": RECONCILIATION_ID,
        "gate": evidence["gate"],
        "factor_count": evidence["factor_count"],
        "exact_match_factor_count": evidence["exact_match_factor_count"],
        "mismatch_factor_count": evidence["mismatch_factor_count"],
        "factor_results": [
            {
                "factor": item["factor"],
                "overlap_count": item["overlap_count"],
                "exact_mismatch_count": item["exact_mismatch_count"],
                "maximum_absolute_difference_percent": item["maximum_absolute_difference_percent"],
                "difference_vector_sha256": item["difference_vector_sha256"],
            }
            for item in evidence["factor_results"]
        ],
        "safe_evidence_sha256": sha256_bytes(evidence_bytes),
        "performance_calculated": False,
        "paper_replication_pass": False,
    }
    (output_root / "safe-source-reconciliation-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return evidence
