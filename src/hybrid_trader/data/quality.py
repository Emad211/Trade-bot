"""Deterministic source-quality and cross-venue diagnostics."""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from hybrid_trader.data.timeframe import timeframe_to_timedelta


class BarQualityReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    row_count: int = Field(ge=0)
    expected_row_count: int = Field(ge=0)
    missing_bar_count: int = Field(ge=0)
    missing_bar_ratio: float = Field(ge=0, le=1)
    duplicate_timestamp_count: int = Field(ge=0)
    irregular_gap_count: int = Field(ge=0)
    maximum_gap_seconds: float = Field(ge=0)
    zero_volume_ratio: float = Field(ge=0, le=1)
    event_start: datetime | None
    event_end: datetime | None
    latest_available_at: datetime | None
    stale_seconds_at_cutoff: float | None = Field(default=None, ge=0)


class CrossVenueQualityReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    primary_source_id: str
    secondary_source_id: str
    primary_rows: int = Field(ge=0)
    secondary_rows: int = Field(ge=0)
    overlap_rows: int = Field(ge=0)
    overlap_ratio: float = Field(ge=0, le=1)
    return_correlation: float | None
    median_absolute_spread_bps: float | None = Field(default=None, ge=0)
    p95_absolute_spread_bps: float | None = Field(default=None, ge=0)
    maximum_absolute_spread_bps: float | None = Field(default=None, ge=0)


def bar_quality(
    frame: pd.DataFrame,
    *,
    source_id: str,
    timeframe: str,
    as_of: pd.Timestamp,
) -> BarQualityReport:
    if frame.empty:
        return BarQualityReport(
            source_id=source_id,
            row_count=0,
            expected_row_count=0,
            missing_bar_count=0,
            missing_bar_ratio=0.0,
            duplicate_timestamp_count=0,
            irregular_gap_count=0,
            maximum_gap_seconds=0.0,
            zero_volume_ratio=0.0,
            event_start=None,
            event_end=None,
            latest_available_at=None,
            stale_seconds_at_cutoff=None,
        )
    index = pd.DatetimeIndex(pd.to_datetime(frame.index, utc=True))
    interval = pd.Timedelta(timeframe_to_timedelta(timeframe))
    expected = pd.date_range(index.min(), index.max(), freq=interval, tz="UTC")
    missing_count = len(expected.difference(index))
    differences = index.to_series().diff().dropna()
    irregular = differences.loc[differences != interval]
    latest_available = pd.Timestamp(pd.to_datetime(frame["available_at"], utc=True).iloc[-1])
    cutoff = _utc(as_of)
    stale_seconds = max(0.0, float((cutoff - latest_available).total_seconds()))
    expected_count = len(expected)
    return BarQualityReport(
        source_id=source_id,
        row_count=len(frame),
        expected_row_count=expected_count,
        missing_bar_count=missing_count,
        missing_bar_ratio=(missing_count / expected_count) if expected_count else 0.0,
        duplicate_timestamp_count=int(index.duplicated().sum()),
        irregular_gap_count=len(irregular),
        maximum_gap_seconds=(float(differences.max().total_seconds()) if len(differences) else 0.0),
        zero_volume_ratio=float((frame["volume"] == 0).mean()),
        event_start=index[0].to_pydatetime(),
        event_end=index[-1].to_pydatetime(),
        latest_available_at=latest_available.to_pydatetime(),
        stale_seconds_at_cutoff=stale_seconds,
    )


def cross_venue_quality(
    primary: pd.DataFrame,
    secondary: pd.DataFrame,
    *,
    primary_source_id: str,
    secondary_source_id: str,
) -> CrossVenueQualityReport:
    joined = primary[["close"]].rename(columns={"close": "primary_close"}).join(
        secondary[["close"]].rename(columns={"close": "secondary_close"}), how="inner"
    )
    overlap = len(joined)
    denominator = max(1, min(len(primary), len(secondary)))
    if overlap < 2:
        correlation: float | None = None
        median: float | None = None
        p95: float | None = None
        maximum: float | None = None
    else:
        primary_returns = np.log(joined["primary_close"]).diff()
        secondary_returns = np.log(joined["secondary_close"]).diff()
        raw_correlation = primary_returns.corr(secondary_returns)
        correlation = float(raw_correlation) if np.isfinite(raw_correlation) else None
        spread = (joined["primary_close"] / joined["secondary_close"] - 1.0).abs() * 10_000
        median = float(spread.median())
        p95 = float(spread.quantile(0.95))
        maximum = float(spread.max())
    return CrossVenueQualityReport(
        primary_source_id=primary_source_id,
        secondary_source_id=secondary_source_id,
        primary_rows=len(primary),
        secondary_rows=len(secondary),
        overlap_rows=overlap,
        overlap_ratio=min(1.0, overlap / denominator),
        return_correlation=correlation,
        median_absolute_spread_bps=median,
        p95_absolute_spread_bps=p95,
        maximum_absolute_spread_bps=maximum,
    )


def column_missingness(frame: pd.DataFrame) -> dict[str, float]:
    return {column: float(frame[column].isna().mean()) for column in frame.columns}


def _utc(value: pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    return timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp.tz_convert("UTC")
