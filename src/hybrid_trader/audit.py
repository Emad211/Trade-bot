"""Point-in-time snapshot quality and cross-venue consistency audits."""

from __future__ import annotations

from collections.abc import Sequence
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from hybrid_trader.data.snapshot import SnapshotManifest, read_snapshot
from hybrid_trader.data.timeframe import timeframe_to_timedelta


class SnapshotAudit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    dataset_id: str
    source: str
    symbol: str
    timeframe: str
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    row_count: int = Field(gt=0)
    expected_rows: int = Field(gt=0)
    missing_bar_count: int = Field(ge=0)
    coverage_ratio: float = Field(ge=0, le=1)
    longest_gap_bars: int = Field(ge=0)
    null_value_count: int = Field(ge=0)
    nonfinite_numeric_count: int = Field(ge=0)
    median_full_bar_latency_seconds: float = Field(ge=0)
    maximum_full_bar_latency_seconds: float = Field(ge=0)
    close_return_mean: float
    close_return_volatility: float = Field(ge=0)


class CrossVenueAudit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    left_dataset_id: str
    right_dataset_id: str
    overlap_rows: int = Field(ge=0)
    overlap_start: str | None
    overlap_end: str | None
    close_return_correlation: float | None
    direction_agreement: float | None = Field(default=None, ge=0, le=1)
    median_absolute_close_spread_bps: float | None = Field(default=None, ge=0)
    p95_absolute_close_spread_bps: float | None = Field(default=None, ge=0)
    maximum_absolute_close_spread_bps: float | None = Field(default=None, ge=0)
    relative_price_ratio_std_bps: float | None = Field(default=None, ge=0)


class DatasetAuditReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    snapshots: tuple[SnapshotAudit, ...]
    cross_venue: tuple[CrossVenueAudit, ...]


def _finite_or_none(value: float) -> float | None:
    return float(value) if np.isfinite(value) else None


def audit_snapshot(path: str | Path) -> tuple[pd.DataFrame, SnapshotManifest, SnapshotAudit]:
    frame, manifest = read_snapshot(path)
    interval = pd.Timedelta(timeframe_to_timedelta(manifest.timeframe))
    observed_index = pd.DatetimeIndex(frame.index)
    expected_index = pd.date_range(observed_index[0], observed_index[-1], freq=interval, tz="UTC")
    missing = expected_index.difference(observed_index)
    observed_diffs = frame.index.to_series().diff().dropna()
    longest_gap = max(0, round(observed_diffs.max() / interval) - 1) if len(observed_diffs) else 0
    numeric = frame.select_dtypes(include=[np.number]).to_numpy(dtype=float)
    latency = (
        pd.to_datetime(frame["available_at"], utc=True) - pd.Series(frame.index, index=frame.index)
    ).dt.total_seconds()
    returns = np.log(frame["close"]).diff().dropna()
    audit = SnapshotAudit(
        dataset_id=manifest.dataset_id,
        source=manifest.source,
        symbol=manifest.symbol,
        timeframe=manifest.timeframe,
        content_sha256=manifest.content_sha256,
        row_count=len(frame),
        expected_rows=len(expected_index),
        missing_bar_count=len(missing),
        coverage_ratio=len(frame) / len(expected_index),
        longest_gap_bars=longest_gap,
        null_value_count=int(frame.isna().sum().sum()),
        nonfinite_numeric_count=int((~np.isfinite(numeric)).sum()),
        median_full_bar_latency_seconds=float(latency.median()),
        maximum_full_bar_latency_seconds=float(latency.max()),
        close_return_mean=float(returns.mean()) if len(returns) else 0.0,
        close_return_volatility=float(returns.std(ddof=0)) if len(returns) else 0.0,
    )
    return frame, manifest, audit


def compare_snapshots(
    left: tuple[pd.DataFrame, SnapshotManifest],
    right: tuple[pd.DataFrame, SnapshotManifest],
) -> CrossVenueAudit:
    left_frame, left_manifest = left
    right_frame, right_manifest = right
    if left_manifest.timeframe != right_manifest.timeframe:
        raise ValueError("Cross-venue comparison requires identical timeframes")
    joined = (
        left_frame[["close"]]
        .rename(columns={"close": "left_close"})
        .join(right_frame[["close"]].rename(columns={"close": "right_close"}), how="inner")
    )
    if joined.empty:
        return CrossVenueAudit(
            left_dataset_id=left_manifest.dataset_id,
            right_dataset_id=right_manifest.dataset_id,
            overlap_rows=0,
            overlap_start=None,
            overlap_end=None,
            close_return_correlation=None,
        )
    left_return = np.log(joined["left_close"]).diff()
    right_return = np.log(joined["right_close"]).diff()
    valid = left_return.notna() & right_return.notna()
    correlation = left_return.loc[valid].corr(right_return.loc[valid]) if valid.any() else np.nan
    direction = np.sign(left_return.loc[valid].to_numpy()) == np.sign(
        right_return.loc[valid].to_numpy()
    )
    midpoint = (joined["left_close"] + joined["right_close"]) / 2.0
    spread_bps = (joined["left_close"] - joined["right_close"]).abs() / midpoint * 10_000
    price_ratio = np.log(joined["left_close"] / joined["right_close"])
    return CrossVenueAudit(
        left_dataset_id=left_manifest.dataset_id,
        right_dataset_id=right_manifest.dataset_id,
        overlap_rows=len(joined),
        overlap_start=joined.index[0].isoformat(),
        overlap_end=joined.index[-1].isoformat(),
        close_return_correlation=_finite_or_none(float(correlation)),
        direction_agreement=float(direction.mean()) if len(direction) else None,
        median_absolute_close_spread_bps=float(spread_bps.median()),
        p95_absolute_close_spread_bps=float(spread_bps.quantile(0.95)),
        maximum_absolute_close_spread_bps=float(spread_bps.max()),
        relative_price_ratio_std_bps=float(price_ratio.std(ddof=0) * 10_000),
    )


def audit_snapshots(paths: Sequence[str | Path]) -> DatasetAuditReport:
    if len(paths) < 2:
        raise ValueError("At least two snapshots are required")
    loaded = [audit_snapshot(path) for path in paths]
    audits = tuple(item[2] for item in loaded)
    pairs = tuple(
        compare_snapshots((loaded[i][0], loaded[i][1]), (loaded[j][0], loaded[j][1]))
        for i, j in combinations(range(len(loaded)), 2)
    )
    return DatasetAuditReport(snapshots=audits, cross_venue=pairs)


def audit_tables(report: DatasetAuditReport) -> tuple[pd.DataFrame, pd.DataFrame]:
    snapshot_rows: list[dict[str, Any]] = [audit.model_dump() for audit in report.snapshots]
    pair_rows: list[dict[str, Any]] = [audit.model_dump() for audit in report.cross_venue]
    return pd.DataFrame(snapshot_rows), pd.DataFrame(pair_rows)
