"""Point-in-time source collection helpers for Phase 2C."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from hybrid_trader.data.artifact import TabularArtifactManifest, write_tabular_artifact
from hybrid_trader.data.asof import merge_asof_features
from hybrid_trader.data.ccxt_source import CCXTOHLCVSource
from hybrid_trader.data.derivatives import CCXTDerivativesSource
from hybrid_trader.data.fred_source import FredCsvSource
from hybrid_trader.data.snapshot import SnapshotManifest, canonical_json_sha256
from hybrid_trader.data.stooq_source import StooqCsvSource
from hybrid_trader.phase2c_contracts import (
    DerivativeVenueSpec,
    FredSeriesSpec,
    Phase2CSpec,
    SourceAttempt,
    SpotVenueSpec,
    StooqSeriesSpec,
)

_SAFE = re.compile(r"[^a-z0-9_-]+")

SpotFactory = Callable[[SpotVenueSpec], CCXTOHLCVSource]
DerivativeFactory = Callable[[DerivativeVenueSpec], CCXTDerivativesSource]
FredFactory = Callable[[FredSeriesSpec], FredCsvSource]
StooqFactory = Callable[[StooqSeriesSpec], StooqCsvSource]


def _safe(value: str) -> str:
    result = _SAFE.sub("-", value.lower()).strip("-")
    if not result:
        raise ValueError("Empty safe identifier")
    return result


def _utc(value: datetime | pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    return timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp.tz_convert("UTC")


def _dump(path: Path, value: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    return str(canonical_json_sha256(value))


def _spot_factory(spec: SpotVenueSpec) -> CCXTOHLCVSource:
    return CCXTOHLCVSource(spec.exchange_id, exchange_options=spec.exchange_options)


def _derivative_factory(spec: DerivativeVenueSpec) -> CCXTDerivativesSource:
    return CCXTDerivativesSource(spec.exchange_id, exchange_options=spec.exchange_options)


def _fred_factory(spec: FredSeriesSpec) -> FredCsvSource:
    return FredCsvSource(
        spec.series_id,
        spec.feature_name,
        release_lag=timedelta(hours=spec.release_lag_hours),
        source_latency=timedelta(seconds=spec.source_latency_seconds),
    )


def _stooq_factory(spec: StooqSeriesSpec) -> StooqCsvSource:
    return StooqCsvSource(
        spec.symbol,
        spec.feature_name,
        release_lag=timedelta(hours=spec.release_lag_hours),
        source_latency=timedelta(seconds=spec.source_latency_seconds),
    )


def _attempt_failure(
    source_id: str,
    source_type: str,
    provider: str,
    instrument: str,
    required: bool,
    spec: Phase2CSpec,
    policy: str,
    revision: str,
    latency: float,
    retrieved: datetime,
    exc: BaseException,
) -> SourceAttempt:
    return SourceAttempt(
        source_id=source_id,
        source_type=source_type,
        provider=provider,
        instrument=instrument,
        status="failure",
        required=required,
        retrieved_at=retrieved,
        observation_cutoff=spec.as_of,
        availability_policy=policy,
        revision_policy=revision,
        latency_seconds=latency,
        error=f"{type(exc).__name__}: {exc}"[:2000],
    )


def _attempt_spot(
    source_id: str,
    venue: SpotVenueSpec,
    spec: Phase2CSpec,
    manifest: SnapshotManifest,
    retrieved: datetime,
) -> SourceAttempt:
    return SourceAttempt(
        source_id=source_id,
        source_type="spot_ohlcv",
        provider=venue.exchange_id,
        instrument=venue.symbol,
        status="success",
        required=venue.required,
        retrieved_at=retrieved,
        observation_cutoff=spec.as_of,
        availability_policy="bar_open_plus_timeframe_plus_source_latency",
        revision_policy="exchange_history_subject_to_vendor_corrections",
        latency_seconds=spec.source_latency_seconds,
        row_count=manifest.row_count,
        content_sha256=manifest.content_sha256,
        event_start=manifest.event_start,
        event_end=manifest.event_end,
        availability_start=manifest.availability_start,
        availability_end=manifest.availability_end,
    )


def _attempt_artifact(
    source_id: str,
    source_type: str,
    provider: str,
    instrument: str,
    required: bool,
    spec: Phase2CSpec,
    manifest: TabularArtifactManifest,
    latency: float,
    retrieved: datetime,
    payload_sha256: str | None = None,
) -> SourceAttempt:
    return SourceAttempt(
        source_id=source_id,
        source_type=source_type,
        provider=provider,
        instrument=instrument,
        status="success",
        required=required,
        retrieved_at=retrieved,
        observation_cutoff=spec.as_of,
        availability_policy=manifest.availability_policy,
        revision_policy=manifest.revision_policy,
        latency_seconds=latency,
        row_count=manifest.row_count,
        content_sha256=manifest.content_sha256,
        payload_sha256=payload_sha256,
        event_start=manifest.event_start,
        event_end=manifest.event_end,
        availability_start=manifest.availability_start,
        availability_end=manifest.availability_end,
    )


def _filter(
    frame: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    as_of: pd.Timestamp,
) -> pd.DataFrame:
    event = pd.to_datetime(frame.event_time, utc=True)
    available = pd.to_datetime(frame.available_at, utc=True)
    return frame.loc[(event >= start) & (event <= end) & (available <= as_of)].copy()


def _merge_secondary(
    primary: pd.DataFrame,
    secondary: pd.DataFrame,
    exchange_id: str,
    tolerance: pd.Timedelta,
) -> tuple[pd.DataFrame, list[str]]:
    label = _safe(exchange_id)
    close_col = f"spot_{label}_close"
    external = pd.DataFrame(
        {
            "available_at": secondary.available_at,
            close_col: secondary.close.to_numpy(float),
        }
    )
    merged = merge_asof_features(
        primary,
        external,
        feature_columns=[close_col],
        provenance_column=f"{close_col}__available_at",
        tolerance=tolerance,
    )
    spread_col = f"spot_{label}_spread_bps"
    merged[spread_col] = (merged.close / merged[close_col] - 1) * 10_000
    return merged, [close_col, spread_col]


def _collect_derivative(
    *,
    kind: str,
    columns: list[str],
    policy: str,
    tolerance: pd.Timedelta,
    spec: Phase2CSpec,
    root: Path,
    combined: pd.DataFrame,
    attempts: list[SourceAttempt],
    retrieved: datetime,
    factory: DerivativeFactory,
    since_ms: int,
    until_ms: int,
) -> tuple[pd.DataFrame, bool]:
    start, end, as_of = _utc(spec.start), _utc(spec.end), _utc(spec.as_of)
    latency = timedelta(seconds=spec.derivative_latency_seconds)
    for venue in spec.derivative_sources:
        source_id = f"derivative:{kind}:{venue.exchange_id}:{venue.symbol}"
        try:
            source = factory(venue)
            if kind == "funding":
                frame = source.fetch_funding_history(
                    venue.symbol,
                    since_ms=since_ms,
                    until_ms=until_ms,
                    max_pages=spec.max_pages,
                    source_latency=latency,
                )
            elif kind == "open_interest":
                frame = source.fetch_open_interest_history(
                    venue.symbol,
                    spec.timeframe,
                    since_ms=since_ms,
                    until_ms=until_ms,
                    max_pages=spec.max_pages,
                    source_latency=latency,
                )
            else:
                frame = source.fetch_basis_history(
                    venue.symbol,
                    spec.timeframe,
                    since_ms=since_ms,
                    until_ms=until_ms,
                    max_pages=spec.max_pages,
                    source_latency=latency,
                )
            frame = _filter(frame, start, end, as_of)
            if frame.empty:
                raise RuntimeError("No observable rows")
            derivative_manifest = write_tabular_artifact(
                frame,
                root / "sources" / "derivatives" / kind / _safe(venue.exchange_id),
                source_id=source_id,
                source_type=kind,
                instrument=venue.symbol,
                availability_policy=policy,
                revision_policy="exchange_history_subject_to_vendor_corrections",
                created_at=spec.as_of,
                notes="Public endpoint only; no credentials.",
            )
            combined = merge_asof_features(
                combined,
                frame,
                feature_columns=columns,
                provenance_column=f"{kind}__available_at",
                tolerance=tolerance,
            )
            attempts.append(
                _attempt_artifact(
                    source_id,
                    kind,
                    venue.exchange_id,
                    venue.symbol,
                    False,
                    spec,
                    derivative_manifest,
                    spec.derivative_latency_seconds,
                    retrieved,
                )
            )
            return combined, True
        except Exception as exc:
            attempts.append(
                _attempt_failure(
                    source_id,
                    kind,
                    venue.exchange_id,
                    venue.symbol,
                    False,
                    spec,
                    policy,
                    "exchange_history_subject_to_vendor_corrections",
                    spec.derivative_latency_seconds,
                    retrieved,
                    exc,
                )
            )
    return combined, False
