"""Fixed-cutoff Phase 2C benchmark runner.

Public data only. This module cannot load credentials or submit orders.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import traceback
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pandas as pd

from hybrid_trader.ablation import build_ablation_plan, summarize_ablation
from hybrid_trader.cli import _prepare_supervised, _run_benchmark
from hybrid_trader.config import AppConfig, load_config
from hybrid_trader.data.artifact import write_tabular_artifact
from hybrid_trader.data.asof import merge_asof_features
from hybrid_trader.data.fred_source import FredFetchResult
from hybrid_trader.data.quality import (
    BarQualityReport,
    CrossVenueQualityReport,
    bar_quality,
    column_missingness,
    cross_venue_quality,
)
from hybrid_trader.data.snapshot import SnapshotManifest, canonical_json_sha256, write_snapshot
from hybrid_trader.data.stooq_source import StooqCsvSource, StooqFetchResult
from hybrid_trader.phase2c_contracts import (
    Phase2CRegistry,
    Phase2CResult,
    Phase2CSpec,
    SourceAttempt,
    StooqSeriesSpec,
    load_phase2c_spec,
)
from hybrid_trader.phase2c_reporting import _concentration, _conditional, _report
from hybrid_trader.phase2c_sources import (
    DerivativeFactory,
    FredFactory,
    SpotFactory,
    _attempt_artifact,
    _attempt_failure,
    _attempt_spot,
    _collect_derivative,
    _derivative_factory,
    _dump,
    _fred_factory,
    _merge_secondary,
    _safe,
    _spot_factory,
    _utc,
)

StooqFactory = Callable[[StooqSeriesSpec], StooqCsvSource]


def _stooq_factory(spec: StooqSeriesSpec) -> StooqCsvSource:
    return StooqCsvSource(
        spec.symbol,
        spec.feature_name,
        release_lag=timedelta(hours=spec.release_lag_hours),
        source_latency=timedelta(seconds=spec.source_latency_seconds),
    )


def run_phase2c(
    *,
    spec: Phase2CSpec,
    benchmark_config: AppConfig,
    output_dir: str | Path,
    spot_factory: SpotFactory = _spot_factory,
    derivative_factory: DerivativeFactory = _derivative_factory,
    fred_factory: FredFactory = _fred_factory,
    stooq_factory: StooqFactory = _stooq_factory,
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
            frame = frame.loc[(frame.index >= start) & (frame.index <= end)].copy()
            if frame.empty:
                raise RuntimeError("No spot rows")
            spot_manifest = write_snapshot(
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
            spot_manifests[venue.exchange_id] = spot_manifest
            quality.append(
                bar_quality(
                    frame,
                    source_id=source_id,
                    timeframe=spec.timeframe,
                    as_of=as_of,
                )
            )
            attempts.append(_attempt_spot(source_id, venue, spec, spot_manifest, retrieved))
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
        raise RuntimeError(f"Need {spec.spot_required_count} spot sources; got {len(spot_frames)}")
    required_failures = [item for item in attempts if item.required and item.status == "failure"]
    if required_failures:
        raise RuntimeError(f"Required source failed: {required_failures[0].source_id}")

    primary = next(
        item.exchange_id for item in spec.spot_sources if item.exchange_id in spot_frames
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
    for fred_item in spec.fred_series:
        source_id = f"fred:{fred_item.series_id}"
        try:
            fred_result: FredFetchResult = fred_factory(fred_item).fetch(
                start=start, end=end, as_of=as_of
            )
            macro_manifest = write_tabular_artifact(
                fred_result.frame,
                root / "sources" / "fred" / _safe(fred_item.series_id),
                source_id=source_id,
                source_type="market_context",
                instrument=fred_item.series_id,
                availability_policy=(f"event_plus_{fred_item.release_lag_hours:g}h_plus_latency"),
                revision_policy=fred_result.revision_policy,
                created_at=spec.as_of,
                notes=fred_result.url,
            )
            combined = merge_asof_features(
                combined,
                fred_result.frame,
                feature_columns=[fred_item.feature_name],
                provenance_column=f"{fred_item.feature_name}__available_at",
                tolerance=pd.Timedelta(days=fred_item.tolerance_days),
            )
            extra.append(fred_item.feature_name)
            macro_successes.append(fred_item.feature_name)
            attempts.append(
                _attempt_artifact(
                    source_id,
                    "market_context",
                    "fred",
                    fred_item.series_id,
                    fred_item.required,
                    spec,
                    macro_manifest,
                    fred_item.source_latency_seconds,
                    fred_result.retrieved_at,
                    fred_result.payload_sha256,
                )
            )
        except Exception as exc:
            attempts.append(
                _attempt_failure(
                    source_id,
                    "market_context",
                    "fred",
                    fred_item.series_id,
                    fred_item.required,
                    spec,
                    "event_plus_release_lag",
                    fred_item.revision_policy,
                    fred_item.source_latency_seconds,
                    retrieved,
                    exc,
                )
            )
            if fred_item.required:
                raise

    for stooq_item in spec.stooq_series:
        source_id = f"stooq:{stooq_item.symbol}"
        try:
            stooq_result: StooqFetchResult = stooq_factory(stooq_item).fetch(
                start=start, end=end, as_of=as_of
            )
            macro_manifest = write_tabular_artifact(
                stooq_result.frame,
                root / "sources" / "stooq" / _safe(stooq_item.symbol),
                source_id=source_id,
                source_type="market_context",
                instrument=stooq_item.symbol,
                availability_policy=(f"event_plus_{stooq_item.release_lag_hours:g}h_plus_latency"),
                revision_policy=stooq_result.revision_policy,
                created_at=spec.as_of,
                notes=stooq_result.url,
            )
            combined = merge_asof_features(
                combined,
                stooq_result.frame,
                feature_columns=[stooq_item.feature_name],
                provenance_column=f"{stooq_item.feature_name}__available_at",
                tolerance=pd.Timedelta(days=stooq_item.tolerance_days),
            )
            extra.append(stooq_item.feature_name)
            macro_successes.append(stooq_item.feature_name)
            attempts.append(
                _attempt_artifact(
                    source_id,
                    "market_context",
                    "stooq",
                    stooq_item.symbol,
                    stooq_item.required,
                    spec,
                    macro_manifest,
                    stooq_item.source_latency_seconds,
                    stooq_result.retrieved_at,
                    stooq_result.payload_sha256,
                )
            )
        except Exception as exc:
            attempts.append(
                _attempt_failure(
                    source_id,
                    "market_context",
                    "stooq",
                    stooq_item.symbol,
                    stooq_item.required,
                    spec,
                    "event_plus_release_lag",
                    stooq_item.revision_policy,
                    stooq_item.source_latency_seconds,
                    retrieved,
                    exc,
                )
            )
            if stooq_item.required:
                raise

    successful_ids = [item.source_id for item in attempts if item.status == "success"]
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
        "attempts": [item.model_dump(mode="json", exclude={"retrieved_at"}) for item in attempts],
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
        if column in {"funding_rate", "open_interest", "mark_price", "index_price", "basis"}
    ]
    macro_columns = [column for column in unique_extra if column in macro_successes]
    foundation_columns = [
        column for column in all_features if column.startswith(("timesfm_", "chronos_", "naive_"))
    ]
    external = set(cross_columns + derivative_columns + macro_columns + foundation_columns)
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
    summarize_ablation(ablation_metrics).to_csv(root / "ablation_summary.csv", index=False)

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
    (root / "phase2c_report.sha256").write_text(f"{report_sha}  phase2c_report.md\n")
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
