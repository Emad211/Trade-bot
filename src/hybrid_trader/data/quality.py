"""Source quality and cross-venue diagnostics."""

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
            missing_bar_ratio=0,
            irregular_gap_count=0,
            maximum_gap_seconds=0,
            zero_volume_ratio=0,
            event_start=None,
            event_end=None,
            latest_available_at=None,
        )
    index = pd.DatetimeIndex(pd.to_datetime(frame.index, utc=True))
    interval = pd.Timedelta(timeframe_to_timedelta(timeframe))
    expected = pd.date_range(index.min(), index.max(), freq=interval, tz="UTC")
    missing = len(expected.difference(index))
    differences = index.to_series().diff().dropna()
    latest = pd.Timestamp(pd.to_datetime(frame.available_at, utc=True).iloc[-1])
    cutoff = _utc(as_of)
    return BarQualityReport(
        source_id=source_id,
        row_count=len(frame),
        expected_row_count=len(expected),
        missing_bar_count=missing,
        missing_bar_ratio=missing / len(expected) if len(expected) else 0,
        irregular_gap_count=int((differences != interval).sum()),
        maximum_gap_seconds=(
            float(differences.max().total_seconds()) if len(differences) else 0
        ),
        zero_volume_ratio=float((frame.volume == 0).mean()),
        event_start=index[0].to_pydatetime(),
        event_end=index[-1].to_pydatetime(),
        latest_available_at=latest.to_pydatetime(),
        stale_seconds_at_cutoff=max(0.0, float((cutoff - latest).total_seconds())),
    )


def cross_venue_quality(
    primary: pd.DataFrame,
    secondary: pd.DataFrame,
    *,
    primary_source_id: str,
    secondary_source_id: str,
) -> CrossVenueQualityReport:
    joined = primary[["close"]].rename(columns={"close": "a"}).join(
        secondary[["close"]].rename(columns={"close": "b"}), how="inner"
    )
    overlap = len(joined)
    denominator = max(1, min(len(primary), len(secondary)))
    if overlap < 2:
        corr = median = p95 = maximum = None
    else:
        raw_corr = np.log(joined.a).diff().corr(np.log(joined.b).diff())
        corr = float(raw_corr) if np.isfinite(raw_corr) else None
        spread = (joined.a / joined.b - 1).abs() * 10_000
        median, p95, maximum = map(
            float, (spread.median(), spread.quantile(0.95), spread.max())
        )
    return CrossVenueQualityReport(
        primary_source_id=primary_source_id,
        secondary_source_id=secondary_source_id,
        overlap_rows=overlap,
        overlap_ratio=min(1.0, overlap / denominator),
        return_correlation=corr,
        median_absolute_spread_bps=median,
        p95_absolute_spread_bps=p95,
        maximum_absolute_spread_bps=maximum,
    )


def column_missingness(frame: pd.DataFrame) -> dict[str, float]:
    return {str(column): float(frame[column].isna().mean()) for column in frame.columns}


def _utc(value: pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    return (
        timestamp.tz_localize("UTC")
        if timestamp.tzinfo is None
        else timestamp.tz_convert("UTC")
    )
