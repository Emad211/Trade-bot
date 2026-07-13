"""Fixed-cutoff Phase 2C real-data benchmark orchestration.

Public data only. This module cannot load credentials or submit orders.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import traceback
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal, cast

import numpy as np
import pandas as pd
import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hybrid_trader.ablation import build_ablation_plan, summarize_ablation
from hybrid_trader.cli import _prepare_supervised, _run_benchmark
from hybrid_trader.config import AppConfig, load_config
from hybrid_trader.data.artifact import TabularArtifactManifest, write_tabular_artifact
from hybrid_trader.data.asof import merge_asof_features
from hybrid_trader.data.ccxt_source import CCXTOHLCVSource
from hybrid_trader.data.derivatives import CCXTDerivativesSource
from hybrid_trader.data.fred_source import FredCsvSource, FredFetchResult
from hybrid_trader.data.quality import (
    BarQualityReport,
    CrossVenueQualityReport,
    bar_quality,
    column_missingness,
    cross_venue_quality,
)
from hybrid_trader.data.snapshot import (
    SnapshotManifest,
    canonical_json_sha256,
    write_snapshot,
)

_SAFE = re.compile(r"[^a-z0-9_-]+")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SpotVenueSpec(StrictModel):
    exchange_id: str
    symbol: str = "BTC/USD"
    required: bool = False
    exchange_options: dict[str, Any] = Field(default_factory=dict)


class DerivativeVenueSpec(StrictModel):
    exchange_id: str
    symbol: str
    exchange_options: dict[str, Any] = Field(default_factory=dict)


class FredSeriesSpec(StrictModel):
    series_id: str
    feature_name: str
    required: bool = False
    release_lag_hours: float = Field(default=24, ge=0)
    source_latency_seconds: float = Field(default=300, ge=0)
    tolerance_days: float = Field(default=10, gt=0)
    revision_policy: Literal["market_price_latest_vintage"] = (
        "market_price_latest_vintage"
    )


class Phase2CSpec(StrictModel):
    schema_version: str = "1.0"
    timeframe: str = "4h"
    start: datetime
    end: datetime
    as_of: datetime
    spot_required_count: int = Field(default=2, ge=2)
    spot_sources: tuple[SpotVenueSpec, ...]
    derivative_sources: tuple[DerivativeVenueSpec, ...] = ()
    minimum_derivative_features: int = Field(default=1, ge=0, le=3)
    fred_series: tuple[FredSeriesSpec, ...] = ()
    source_latency_seconds: float = Field(default=30, ge=0)
    derivative_latency_seconds: float = Field(default=60, ge=0)
    page_limit: int = Field(default=1000, ge=50, le=2000)
    max_pages: int = Field(default=100, ge=1, le=500)
    cross_venue_tolerance_hours: float = Field(default=8, gt=0)

    @field_validator("start", "end", "as_of")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Phase 2C timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_contract(self) -> Phase2CSpec:
        if not self.start < self.end <= self.as_of:
            raise ValueError("Phase 2C requires start < end <= as_of")
        if len(self.spot_sources) < self.spot_required_count:
            raise ValueError("spot_sources cannot satisfy spot_required_count")
        ids = [item.exchange_id for item in self.spot_sources]
        if len(ids) != len(set(ids)):
            raise ValueError("Spot exchange IDs must be unique")
        return self


class SourceAttempt(StrictModel):
    source_id: str
    source_type: str
    provider: str
    instrument: str
    status: Literal["success", "failure"]
    required: bool
    retrieved_at: datetime
    observation_cutoff: datetime
    availability_policy: str
    revision_policy: str
    latency_seconds: float = Field(ge=0)
    row_count: int = Field(default=0, ge=0)
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    payload_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    event_start: datetime | None = None
    event_end: datetime | None = None
    availability_start: datetime | None = None
    availability_end: datetime | None = None
    error: str | None = None


class Phase2CRegistry(StrictModel):
    registry_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    created_at: datetime
    observation_cutoff: datetime
    spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    combined_snapshot_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    attempts: tuple[SourceAttempt, ...]


class Phase2CResult(StrictModel):
    output_dir: str
    registry_id: str
    combined_snapshot_sha256: str
    successful_spot_sources: tuple[str, ...]
    successful_derivative_features: tuple[str, ...]
    successful_macro_features: tuple[str, ...]
    experiment_id: str
    report_sha256: str


SpotFactory = Callable[[SpotVenueSpec], CCXTOHLCVSource]
DerivativeFactory = Callable[[DerivativeVenueSpec], CCXTDerivativesSource]
FredFactory = Callable[[FredSeriesSpec], FredCsvSource]


def load_phase2c_spec(path: str | Path) -> Phase2CSpec:
    with Path(path).open("r", encoding="utf-8") as handle:
        return Phase2CSpec.model_validate(yaml.safe_load(handle) or {})


def _safe(value: str) -> str:
    result = _SAFE.sub("-", value.lower()).strip("-")
    if not result:
        raise ValueError("Empty safe identifier")
    return result


def _utc(value: datetime | pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    return (
        timestamp.tz_localize("UTC")
        if timestamp.tzinfo is None
        else timestamp.tz_convert("UTC")
    )


def _dump(path: Path, value: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    return str(canonical_json_sha256(value))


def _spot_factory(spec: SpotVenueSpec) -> CCXTOHLCVSource:
    return CCXTOHLCVSource(
        spec.exchange_id, exchange_options=spec.exchange_options
    )


def _derivative_factory(spec: DerivativeVenueSpec) -> CCXTDerivativesSource:
    return CCXTDerivativesSource(
        spec.exchange_id, exchange_options=spec.exchange_options
    )


def _fred_factory(spec: FredSeriesSpec) -> FredCsvSource:
    return FredCsvSource(
        spec.series_id,
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
    return frame.loc[
        (event >= start) & (event <= end) & (available <= as_of)
    ].copy()


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
            manifest = write_tabular_artifact(
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
                    manifest,
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
                "fold": int(fold),
                "large_move_threshold": cutoff,
                "large_move_rows": len(large),
                "directional_accuracy": float(
                    (
                        predicted.to_numpy()
                        == (large.target_return > 0).to_numpy()
                    ).mean()
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
                "best_positive_fold_share": (
                    float(positive.max() / total) if total > 0 else None
                ),
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
        cells = [
            str(value).replace("|", "\\|").replace("\n", " ")
            for value in values
        ]
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
    stress_summary = stress.groupby(
        ["model", "cost_multiplier"], as_index=False
    ).agg(
        mean_net_return=("net_return", "mean"),
        mean_sharpe=("sharpe", "mean"),
    )
    missing = pd.DataFrame(
        sorted(missingness.items(), key=lambda item: item[1], reverse=True),
        columns=["column", "missing_ratio"],
    )
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


def run_phase2c(
    *,
    spec: Phase2CSpec,
    benchmark_config: AppConfig,
    output_dir: str | Path,
    spot_factory: SpotFactory = _spot_factory,
    derivative_factory: DerivativeFactory = _derivative_factory,
    fred_factory: FredFactory = _fred_factory,
    feature_caches: tuple[Path, ...] = (),
) -> Phase2CResult:
    root = Path(output_dir)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"Non-empty output: {root}")
    root.mkdir(parents=True, exist_ok=True)
    retrieved = datetime.now(UTC)
    start, end, as_of = _utc(spec.start), _utc(spec.end), _utc(spec.as_of)
    since_ms, until_ms = int(start.timestamp() * 1000), int(end.timestamp() * 1000)
    attempts: list[SourceAttempt] = []
    spot_frames: dict[str, pd.DataFrame] = {}
    spot_manifests: dict[str, SnapshotManifest] = {}
    quality: list[BarQualityReport] = []
    cross: list[CrossVenueQualityReport] = []

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
            frame = frame.loc[
                (frame.index >= start) & (frame.index <= end)
            ].copy()
            if frame.empty:
                raise RuntimeError("No spot rows")
            manifest = write_snapshot(
                frame,
                root / "sources" / "spot" / _safe(venue.exchange_id),
                source=source_id,
                symbol=venue.symbol,
                timeframe=spec.timeframe,
                source_latency_seconds=spec.source_latency_seconds,
                created_at=spec.as_of,
                notes="Independent public spot source",
            )
            spot_frames[venue.exchange_id] = frame
            spot_manifests[venue.exchange_id] = manifest
            quality.append(
                bar_quality(
                    frame,
                    source_id=source_id,
                    timeframe=spec.timeframe,
                    as_of=as_of,
                )
            )
            attempts.append(
                _attempt_spot(source_id, venue, spec, manifest, retrieved)
            )
        except Exception as exc:
            attempts.append(
                _attempt_failure(
                    source_id,
                    "spot_ohlcv",
                    venue.exchange_id,
                    venue.symbol,
                    venue.required,
                    spec,
                    "bar_open_plus_timeframe_plus_source_latency",
                    "exchange_history_subject_to_vendor_corrections",
                    spec.source_latency_seconds,
                    retrieved,
                    exc,
                )
            )

    if len(spot_frames) < spec.spot_required_count:
        raise RuntimeError(
            f"Need {spec.spot_required_count} spot sources; got {len(spot_frames)}"
        )
    required_failures = [
        item for item in attempts if item.required and item.status == "failure"
    ]
    if required_failures:
        raise RuntimeError(f"Required source failed: {required_failures[0].source_id}")

    primary = next(
        item.exchange_id
        for item in spec.spot_sources
        if item.exchange_id in spot_frames
    )
    combined = spot_frames[primary].copy()
    extra: list[str] = []
    for exchange_id, secondary in spot_frames.items():
        if exchange_id == primary:
            continue
        cross.append(
            cross_venue_quality(
                combined,
                secondary,
                primary_source_id=primary,
                secondary_source_id=exchange_id,
            )
        )
        combined, columns = _merge_secondary(
            combined,
            secondary,
            exchange_id,
            pd.Timedelta(hours=spec.cross_venue_tolerance_hours),
        )
        extra.extend(columns)

    derivative_successes: list[str] = []
    families = {
        "funding": (
            ["funding_rate"],
            "event_plus_latency",
            pd.Timedelta("3d"),
        ),
        "open_interest": (
            ["open_interest"],
            "interval_close_plus_latency",
            pd.Timedelta("12h"),
        ),
        "basis": (
            ["mark_price", "index_price", "basis"],
            "interval_close_plus_latency",
            pd.Timedelta("12h"),
        ),
    }
    for kind, (columns, policy, tolerance) in families.items():
        combined, ok = _collect_derivative(
            kind=kind,
            columns=columns,
            policy=policy,
            tolerance=tolerance,
            spec=spec,
            root=root,
            combined=combined,
            attempts=attempts,
            retrieved=retrieved,
            factory=derivative_factory,
            since_ms=since_ms,
            until_ms=until_ms,
        )
        if ok:
            derivative_successes.append(kind)
            extra.extend(columns)
    if len(derivative_successes) < spec.minimum_derivative_features:
        raise RuntimeError("Insufficient derivative feature families")

    macro_successes: list[str] = []
    for item in spec.fred_series:
        source_id = f"fred:{item.series_id}"
        try:
            result: FredFetchResult = fred_factory(item).fetch(
                start=start, end=end, as_of=as_of
            )
            manifest = write_tabular_artifact(
                result.frame,
                root / "sources" / "fred" / _safe(item.series_id),
                source_id=source_id,
                source_type="market_context",
                instrument=item.series_id,
                availability_policy=(
                    f"event_plus_{item.release_lag_hours:g}h_plus_latency"
                ),
                revision_policy=result.revision_policy,
                created_at=spec.as_of,
                notes=result.url,
            )
            combined = merge_asof_features(
                combined,
                result.frame,
                feature_columns=[item.feature_name],
                provenance_column=f"{item.feature_name}__available_at",
                tolerance=pd.Timedelta(days=item.tolerance_days),
            )
            extra.append(item.feature_name)
            macro_successes.append(item.feature_name)
            attempts.append(
                _attempt_artifact(
                    source_id,
                    "market_context",
                    "fred",
                    item.series_id,
                    item.required,
                    spec,
                    manifest,
                    item.source_latency_seconds,
                    result.retrieved_at,
                    result.payload_sha256,
                )
            )
        except Exception as exc:
            attempts.append(
                _attempt_failure(
                    source_id,
                    "market_context",
                    "fred",
                    item.series_id,
                    item.required,
                    spec,
                    "event_plus_release_lag",
                    item.revision_policy,
                    item.source_latency_seconds,
                    retrieved,
                    exc,
                )
            )
            if item.required:
                raise

    successful_ids = [
        item.source_id for item in attempts if item.status == "success"
    ]
    combined_manifest = write_snapshot(
        combined,
        root / "combined_snapshot",
        source="phase2c:" + ";".join(successful_ids),
        symbol=spot_manifests[primary].symbol,
        timeframe=spec.timeframe,
        source_latency_seconds=spec.source_latency_seconds,
        created_at=spec.as_of,
        notes=f"Primary spot={primary}; public research data",
    )
    spec_payload = spec.model_dump(mode="json")
    identity = {
        "observation_cutoff": spec.as_of,
        "spec": spec_payload,
        "combined_snapshot_sha256": combined_manifest.content_sha256,
        "attempts": [
            item.model_dump(mode="json", exclude={"retrieved_at"})
            for item in attempts
        ],
    }
    registry = Phase2CRegistry(
        registry_id=str(canonical_json_sha256(identity)),
        created_at=retrieved,
        observation_cutoff=spec.as_of,
        spec_sha256=str(canonical_json_sha256(spec_payload)),
        combined_snapshot_sha256=combined_manifest.content_sha256,
        attempts=tuple(attempts),
    )
    _dump(root / "source_registry.json", registry.model_dump(mode="json"))
    missingness: dict[str, float] = column_missingness(combined)
    _dump(
        root / "quality_report.json",
        {
            "spot": [item.model_dump(mode="json") for item in quality],
            "cross_venue": [item.model_dump(mode="json") for item in cross],
            "combined_missingness": missingness,
        },
    )

    unique_extra = list(dict.fromkeys(extra))
    benchmark_dir = root / "benchmark" / "all_features"
    metrics, predictions, stress = _run_benchmark(
        snapshot_dir=root / "combined_snapshot",
        config=benchmark_config,
        output=benchmark_dir,
        feature_caches=list(feature_caches),
        extra_features=unique_extra,
    )
    experiment = cast(
        dict[str, Any],
        json.loads((benchmark_dir / "experiment.json").read_text()),
    )
    experiment_id = str(experiment["experiment_id"])

    _, all_features, _, _ = _prepare_supervised(
        root / "combined_snapshot",
        benchmark_config,
        list(feature_caches),
        unique_extra,
    )
    cross_columns = [column for column in unique_extra if column.startswith("spot_")]
    derivative_columns = [
        column
        for column in unique_extra
        if column
        in {"funding_rate", "open_interest", "mark_price", "index_price", "basis"}
    ]
    macro_columns = [
        column for column in unique_extra if column in macro_successes
    ]
    foundation_columns = [
        column
        for column in all_features
        if column.startswith(("timesfm_", "chronos_", "naive_"))
    ]
    external = set(
        cross_columns + derivative_columns + macro_columns + foundation_columns
    )
    groups: dict[str, list[str]] = {
        "market": [column for column in all_features if column not in external]
    }
    if cross_columns:
        groups["cross_venue"] = cross_columns
    if derivative_columns:
        groups["derivatives"] = derivative_columns
    if macro_columns:
        groups["macro_market_context"] = macro_columns
    if foundation_columns:
        groups["foundation_models"] = foundation_columns
    _dump(root / "feature_groups.json", groups)

    ablations: list[pd.DataFrame] = []
    for run in build_ablation_plan(groups):
        if run.name == "all_features":
            run_metrics = metrics.copy()
        else:
            run_metrics = _run_benchmark(
                snapshot_dir=root / "combined_snapshot",
                config=benchmark_config,
                output=root / "benchmark" / "ablation" / run.name,
                feature_caches=list(feature_caches),
                extra_features=unique_extra,
                override_feature_columns=list(run.columns),
            )[0]
        run_metrics.insert(0, "ablation", run.name)
        ablations.append(run_metrics)
    ablation_metrics = pd.concat(ablations, ignore_index=True)
    ablation_metrics.to_csv(root / "ablation_fold_metrics.csv", index=False)
    summarize_ablation(ablation_metrics).to_csv(
        root / "ablation_summary.csv", index=False
    )

    conditional = _conditional(predictions)
    concentration = _concentration(metrics)
    conditional.to_csv(root / "conditional_large_moves.csv", index=False)
    concentration.to_csv(root / "fold_concentration.csv", index=False)
    summary = metrics.groupby("model", as_index=False).mean(numeric_only=True)
    report = _report(
        spec,
        registry,
        quality,
        cross,
        missingness,
        summary,
        stress,
        conditional,
        concentration,
        experiment_id,
    )
    (root / "phase2c_report.md").write_text(report)
    report_sha = hashlib.sha256(report.encode()).hexdigest()
    (root / "phase2c_report.sha256").write_text(
        f"{report_sha}  phase2c_report.md\n"
    )
    freeze: dict[str, Any] = {
        "schema_version": "1.0",
        "status": "candidate_not_activated",
        "created_at": datetime.now(UTC).isoformat(),
        "dataset_sha256": combined_manifest.content_sha256,
        "experiment_id": experiment_id,
        "source_tree_sha256": experiment["source_tree_sha256"],
        "observation_cutoff": spec.as_of.isoformat(),
        "activation_rule": "human review after ablation and stressed costs",
        "github_sha": os.environ.get("GITHUB_SHA"),
    }
    freeze["freeze_sha256"] = str(canonical_json_sha256(freeze))
    _dump(root / "prospective" / "freeze_candidate.json", freeze)
    (root / "prospective" / "decisions.jsonl").touch()
    return Phase2CResult(
        output_dir=str(root),
        registry_id=registry.registry_id,
        combined_snapshot_sha256=combined_manifest.content_sha256,
        successful_spot_sources=tuple(spot_frames),
        successful_derivative_features=tuple(derivative_successes),
        successful_macro_features=tuple(macro_successes),
        experiment_id=experiment_id,
        report_sha256=report_sha,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--feature-cache", type=Path, action="append", default=[])
    args = parser.parse_args()
    try:
        result = run_phase2c(
            spec=load_phase2c_spec(args.spec),
            benchmark_config=load_config(args.config),
            output_dir=args.output,
            feature_caches=tuple(args.feature_cache),
        )
    except Exception:
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "failure.txt").write_text(traceback.format_exc())
        raise
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
