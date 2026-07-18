"""Prospective-only public BTC market snapshots for Phase 3G."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hybrid_trader.data.ccxt_source import CCXTOHLCVSource
from hybrid_trader.data.quality import (
    BarQualityReport,
    CrossVenueQualityReport,
    bar_quality,
    cross_venue_quality,
)
from hybrid_trader.data.snapshot import (
    SnapshotManifest,
    canonical_json_sha256,
    write_snapshot,
)
from hybrid_trader.phase2c_contracts import SpotVenueSpec
from hybrid_trader.phase2c_sources import _merge_secondary, _safe, _spot_factory

SpotFactory = Callable[[SpotVenueSpec], CCXTOHLCVSource]


class Phase3GMarketSpec(BaseModel):
    """Frozen current-market collection contract."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    timeframe: str = "4h"
    as_of: datetime
    lookback_days: int = Field(default=120, ge=30, le=730)
    spot_required_count: int = Field(default=2, ge=2)
    spot_sources: tuple[SpotVenueSpec, ...]
    source_latency_seconds: float = Field(default=30, ge=0)
    page_limit: int = Field(default=200, ge=50, le=2_000)
    max_pages: int = Field(default=100, ge=1, le=500)
    cross_venue_tolerance_hours: float = Field(default=8, gt=0, le=48)

    @field_validator("as_of")
    @classmethod
    def normalize_as_of(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Phase 3G as_of must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_sources(self) -> Phase3GMarketSpec:
        if len(self.spot_sources) < self.spot_required_count:
            raise ValueError("spot_sources cannot satisfy spot_required_count")
        identifiers = [source.exchange_id for source in self.spot_sources]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Phase 3G spot exchange IDs must be unique")
        return self


class Phase3GSourceAttempt(BaseModel):
    """Auditable outcome for one public spot source."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    provider: str
    instrument: str
    required: bool
    status: Literal["success", "failure"]
    retrieved_at: datetime
    observation_cutoff: datetime
    availability_policy: Literal["bar_open_plus_timeframe_plus_source_latency"]
    revision_policy: Literal["exchange_history_subject_to_vendor_corrections"]
    latency_seconds: float = Field(ge=0)
    row_count: int = Field(default=0, ge=0)
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    event_start: datetime | None = None
    event_end: datetime | None = None
    availability_start: datetime | None = None
    availability_end: datetime | None = None
    error: str | None = None


class Phase3GMarketManifest(BaseModel):
    """Identity and evidence for one prospective market collection."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    run_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    as_of: datetime
    window_start: datetime
    window_end: datetime
    source_commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    primary_source: str
    successful_spot_sources: tuple[str, ...]
    combined_snapshot_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_attempts: tuple[Phase3GSourceAttempt, ...]
    bar_quality: tuple[BarQualityReport, ...]
    cross_venue_quality: tuple[CrossVenueQualityReport, ...]
    market_data_only: bool = True
    credentials_used: bool = False
    trading_decisions_created: bool = False
    created_at: datetime

    @field_validator("as_of", "window_start", "window_end", "created_at")
    @classmethod
    def normalize_timestamps(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Phase 3G manifest timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_safety_and_window(self) -> Phase3GMarketManifest:
        if not self.window_start < self.window_end <= self.as_of:
            raise ValueError("Phase 3G manifest window is invalid")
        if len(self.successful_spot_sources) < 2:
            raise ValueError("Phase 3G requires at least two successful spot sources")
        if not self.market_data_only or self.credentials_used or self.trading_decisions_created:
            raise ValueError("Phase 3G market collection violated its safety boundary")
        return self


def _utc(value: datetime | pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError("Phase 3G timestamps must be timezone-aware")
    return timestamp.tz_convert("UTC")


def _validate_commit_sha(value: str) -> str:
    if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("source_commit_sha must be a lowercase 40-character Git SHA")
    return value


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def _success_attempt(
    *,
    venue: SpotVenueSpec,
    source_id: str,
    manifest: SnapshotManifest,
    spec: Phase3GMarketSpec,
    retrieved_at: datetime,
) -> Phase3GSourceAttempt:
    return Phase3GSourceAttempt(
        source_id=source_id,
        provider=venue.exchange_id,
        instrument=venue.symbol,
        required=venue.required,
        status="success",
        retrieved_at=retrieved_at,
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


def _failure_attempt(
    *,
    venue: SpotVenueSpec,
    source_id: str,
    spec: Phase3GMarketSpec,
    retrieved_at: datetime,
    error: BaseException,
) -> Phase3GSourceAttempt:
    return Phase3GSourceAttempt(
        source_id=source_id,
        provider=venue.exchange_id,
        instrument=venue.symbol,
        required=venue.required,
        status="failure",
        retrieved_at=retrieved_at,
        observation_cutoff=spec.as_of,
        availability_policy="bar_open_plus_timeframe_plus_source_latency",
        revision_policy="exchange_history_subject_to_vendor_corrections",
        latency_seconds=spec.source_latency_seconds,
        error=f"{type(error).__name__}: {error}"[:2_000],
    )


def collect_phase3g_market(
    spec: Phase3GMarketSpec,
    output_dir: str | Path,
    *,
    source_commit_sha: str,
    spot_factory: SpotFactory = _spot_factory,
    retrieved_at: datetime | None = None,
) -> Phase3GMarketManifest:
    """Collect a current multi-venue public snapshot without account access."""

    commit_sha = _validate_commit_sha(source_commit_sha)
    root = Path(output_dir)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"Phase 3G output directory is not empty: {root}")
    root.mkdir(parents=True, exist_ok=True)

    cutoff = _utc(spec.as_of)
    start = cutoff - pd.Timedelta(days=spec.lookback_days)
    end = cutoff
    observed_at = retrieved_at or datetime.now(UTC)
    if observed_at.tzinfo is None:
        raise ValueError("retrieved_at must be timezone-aware")
    observed_at = observed_at.astimezone(UTC)
    since_ms = int(start.timestamp() * 1_000)
    until_ms = int(end.timestamp() * 1_000)

    frames: dict[str, pd.DataFrame] = {}
    snapshots: dict[str, SnapshotManifest] = {}
    attempts: list[Phase3GSourceAttempt] = []
    quality_reports: list[BarQualityReport] = []

    for venue in spec.spot_sources:
        source_id = f"spot:{venue.exchange_id}:{venue.symbol}"
        try:
            frame = spot_factory(venue).fetch_point_in_time(
                venue.symbol,
                spec.timeframe,
                source_latency=timedelta(seconds=spec.source_latency_seconds),
                since_ms=since_ms,
                until_ms=until_ms,
                page_limit=spec.page_limit,
                max_pages=spec.max_pages,
                now=spec.as_of,
            )
            available = pd.to_datetime(frame["available_at"], utc=True, errors="coerce")
            if available.isna().any():
                raise ValueError("Spot source returned invalid availability timestamps")
            frame = frame.loc[
                (frame.index >= start) & (frame.index <= end) & (available <= cutoff)
            ].copy()
            if frame.empty:
                raise RuntimeError("Spot source returned no fully available bars")
            if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
                raise ValueError("Spot source index must be unique and sorted")
            snapshot = write_snapshot(
                frame,
                root / "sources" / _safe(venue.exchange_id),
                source=source_id,
                symbol=venue.symbol,
                timeframe=spec.timeframe,
                source_latency_seconds=spec.source_latency_seconds,
                created_at=spec.as_of,
                notes="Prospective public Phase 3G spot source",
            )
            frames[venue.exchange_id] = frame
            snapshots[venue.exchange_id] = snapshot
            quality_reports.append(
                bar_quality(
                    frame,
                    source_id=source_id,
                    timeframe=spec.timeframe,
                    as_of=cutoff,
                )
            )
            attempts.append(
                _success_attempt(
                    venue=venue,
                    source_id=source_id,
                    manifest=snapshot,
                    spec=spec,
                    retrieved_at=observed_at,
                )
            )
        except Exception as error:
            attempts.append(
                _failure_attempt(
                    venue=venue,
                    source_id=source_id,
                    spec=spec,
                    retrieved_at=observed_at,
                    error=error,
                )
            )

    required_failures = [
        attempt for attempt in attempts if attempt.required and attempt.status == "failure"
    ]
    if required_failures:
        _write_json(
            root / "source_attempts.json",
            [attempt.model_dump(mode="json") for attempt in attempts],
        )
        raise RuntimeError(f"Required Phase 3G source failed: {required_failures[0].source_id}")
    if len(frames) < spec.spot_required_count:
        _write_json(
            root / "source_attempts.json",
            [attempt.model_dump(mode="json") for attempt in attempts],
        )
        raise RuntimeError(
            f"Phase 3G requires {spec.spot_required_count} spot sources; got {len(frames)}"
        )

    primary = next(venue.exchange_id for venue in spec.spot_sources if venue.exchange_id in frames)
    combined = frames[primary].copy()
    cross_reports: list[CrossVenueQualityReport] = []
    for exchange_id, secondary in frames.items():
        if exchange_id == primary:
            continue
        cross_reports.append(
            cross_venue_quality(
                combined,
                secondary,
                primary_source_id=primary,
                secondary_source_id=exchange_id,
            )
        )
        combined, _ = _merge_secondary(
            combined,
            secondary,
            exchange_id,
            pd.Timedelta(hours=spec.cross_venue_tolerance_hours),
        )

    combined_available = pd.to_datetime(combined["available_at"], utc=True, errors="coerce")
    if combined_available.isna().any() or (combined_available > cutoff).any():
        raise ValueError("Combined Phase 3G snapshot contains unavailable bars")
    combined_snapshot = write_snapshot(
        combined,
        root / "combined_snapshot",
        source=f"phase3g-primary:{primary}",
        symbol=next(venue.symbol for venue in spec.spot_sources if venue.exchange_id == primary),
        timeframe=spec.timeframe,
        source_latency_seconds=spec.source_latency_seconds,
        created_at=spec.as_of,
        notes="Prospective Phase 3G primary snapshot with secondary venue diagnostics",
    )

    spec_payload = spec.model_dump(mode="json")
    spec_sha = canonical_json_sha256(spec_payload)
    successful_sources = tuple(
        venue.exchange_id for venue in spec.spot_sources if venue.exchange_id in frames
    )
    identity = {
        "schema_version": "1.0",
        "as_of": spec.as_of,
        "window_start": start.to_pydatetime(),
        "window_end": end.to_pydatetime(),
        "source_commit_sha": commit_sha,
        "spec_sha256": spec_sha,
        "primary_source": primary,
        "successful_spot_sources": successful_sources,
        "combined_snapshot_sha256": combined_snapshot.content_sha256,
        "source_attempts": [attempt.model_dump(mode="json") for attempt in attempts],
        "bar_quality": [report.model_dump(mode="json") for report in quality_reports],
        "cross_venue_quality": [report.model_dump(mode="json") for report in cross_reports],
    }
    manifest = Phase3GMarketManifest(
        run_id=canonical_json_sha256(identity),
        as_of=spec.as_of,
        window_start=start.to_pydatetime(),
        window_end=end.to_pydatetime(),
        source_commit_sha=commit_sha,
        spec_sha256=spec_sha,
        primary_source=primary,
        successful_spot_sources=successful_sources,
        combined_snapshot_sha256=combined_snapshot.content_sha256,
        source_attempts=tuple(attempts),
        bar_quality=tuple(quality_reports),
        cross_venue_quality=tuple(cross_reports),
        created_at=observed_at,
    )
    _write_json(root / "spec.json", spec_payload)
    _write_json(
        root / "source_attempts.json",
        [attempt.model_dump(mode="json") for attempt in attempts],
    )
    _write_json(
        root / "quality.json",
        {
            "bar_quality": [report.model_dump(mode="json") for report in quality_reports],
            "cross_venue_quality": [report.model_dump(mode="json") for report in cross_reports],
        },
    )
    _write_json(root / "manifest.json", manifest.model_dump(mode="json"))
    return manifest
