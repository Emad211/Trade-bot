from __future__ import annotations

import argparse
import json
import platform
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from hybrid_trader.ablation import build_ablation_plan, summarize_ablation
from hybrid_trader.cli import _prepare_supervised, _run_benchmark
from hybrid_trader.config import load_config
from hybrid_trader.data.snapshot import canonical_json_sha256, read_snapshot
from hybrid_trader.forecasting.batched import (
    BatchRollingSpec,
    Chronos2BatchForecaster,
    NaiveBatchForecaster,
    TimesFMBatchForecaster,
    rolling_batched_features,
)
from hybrid_trader.forecasting.chronos_adapter import ChronosSettings
from hybrid_trader.forecasting.rolling import (
    RollingForecastSpec,
    cache_rolling_features,
    read_cached_rolling_features,
)
from hybrid_trader.forecasting.timesfm_adapter import TimesFMSettings


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def _cache_spec(spec: BatchRollingSpec) -> RollingForecastSpec:
    return RollingForecastSpec(
        context_length=spec.context_length,
        horizon=spec.horizon,
        min_history=spec.min_history,
        stride=spec.stride,
        prefix=spec.prefix,
        inference_latency_seconds=spec.inference_latency_seconds,
    )


def _generate_cache(
    *,
    series: pd.Series,
    availability: pd.Series,
    forecaster: Any,
    spec: BatchRollingSpec,
    output: Path,
    dataset_sha256: str,
    model_id: str,
    revision: str | None,
) -> dict[str, Any]:
    started = time.perf_counter()
    features = rolling_batched_features(series, forecaster, spec, availability=availability)
    feature_sha = cache_rolling_features(
        features,
        output,
        dataset_sha256=dataset_sha256,
        model_id=model_id,
        model_revision=revision,
        spec=_cache_spec(spec),
    )
    _, manifest = read_cached_rolling_features(output, expected_dataset_sha256=dataset_sha256)
    return {
        "model_id": model_id,
        "revision": revision,
        "cache_id": manifest.cache_id,
        "feature_sha256": feature_sha,
        "rows": len(features),
        "columns": list(features.columns),
        "spec": asdict(spec),
        "runtime_seconds": time.perf_counter() - started,
    }


def _base_groups(root: Path) -> dict[str, list[str]]:
    path = root / "feature_groups.json"
    if not path.exists():
        return {}
    value = json.loads(path.read_text("utf-8"))
    if not isinstance(value, dict) or not all(isinstance(v, list) for v in value.values()):
        raise ValueError("Baseline feature_groups.json has an invalid shape")
    return {str(key): [str(column) for column in columns] for key, columns in value.items()}


def _baseline_extras(groups: dict[str, list[str]]) -> list[str]:
    return list(
        dict.fromkeys(
            column
            for name, columns in groups.items()
            if name != "foundation_models"
            for column in columns
        )
    )


def _scenario_comparison(
    baseline_root: Path, scenario_summaries: list[pd.DataFrame]
) -> pd.DataFrame:
    baseline = pd.read_csv(baseline_root / "benchmark/all_features/summary.csv")
    metrics = [
        column
        for column in ("net_return", "sharpe", "max_drawdown", "brier", "log_loss")
        if column in baseline.columns
    ]
    baseline = baseline[["model", *metrics]].copy()
    baseline = baseline.rename(columns={metric: f"baseline_{metric}" for metric in metrics})
    combined = pd.concat(scenario_summaries, ignore_index=True)
    merged = combined.merge(baseline, on="model", how="left")
    for metric in metrics:
        merged[f"delta_{metric}"] = merged[metric] - merged[f"baseline_{metric}"]
    return merged


def run(args: argparse.Namespace) -> None:
    baseline_root: Path = args.baseline_root
    output: Path = args.output
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"Output must be empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    config = load_config(args.config)
    data, snapshot_manifest = read_snapshot(baseline_root / "combined_snapshot")
    series = np.log(data["close"].astype(float)).diff().dropna()
    availability = pd.to_datetime(data.loc[series.index, "available_at"], utc=True)

    base_spec = dict(
        context_length=args.context,
        horizon=args.horizon,
        min_history=args.context,
        stride=args.stride,
        batch_size=args.batch_size,
        inference_latency_seconds=args.inference_latency_seconds,
    )
    cache_root = output / "feature_caches"
    caches: dict[str, Path] = {
        "naive": cache_root / "naive",
        "timesfm": cache_root / "timesfm",
        "chronos": cache_root / "chronos",
    }
    evidence: dict[str, dict[str, Any]] = {}
    evidence["naive"] = _generate_cache(
        series=series,
        availability=availability,
        forecaster=NaiveBatchForecaster(),
        spec=BatchRollingSpec(prefix="naive", **base_spec),
        output=caches["naive"],
        dataset_sha256=snapshot_manifest.content_sha256,
        model_id="naive-zero-return-batch",
        revision="deterministic-v1",
    )
    timesfm_settings = TimesFMSettings(
        model_id=args.timesfm_model,
        revision=args.timesfm_revision,
        max_context=args.context,
        max_horizon=args.horizon,
        use_quantiles=True,
    )
    evidence["timesfm"] = _generate_cache(
        series=series,
        availability=availability,
        forecaster=TimesFMBatchForecaster(timesfm_settings),
        spec=BatchRollingSpec(prefix="timesfm", **base_spec),
        output=caches["timesfm"],
        dataset_sha256=snapshot_manifest.content_sha256,
        model_id=args.timesfm_model,
        revision=args.timesfm_revision,
    )
    chronos_settings = ChronosSettings(
        model_id=args.chronos_model,
        revision=args.chronos_revision,
        device_map=args.device,
        context_length=args.context,
    )
    evidence["chronos"] = _generate_cache(
        series=series,
        availability=availability,
        forecaster=Chronos2BatchForecaster(chronos_settings),
        spec=BatchRollingSpec(prefix="chronos", **base_spec),
        output=caches["chronos"],
        dataset_sha256=snapshot_manifest.content_sha256,
        model_id=args.chronos_model,
        revision=args.chronos_revision,
    )

    groups = _base_groups(baseline_root)
    extras = _baseline_extras(groups)
    scenarios: dict[str, list[Path]] = {
        "naive": [caches["naive"]],
        "timesfm": [caches["timesfm"]],
        "chronos": [caches["chronos"]],
        "timesfm_chronos": [caches["timesfm"], caches["chronos"]],
    }
    summary_frames: list[pd.DataFrame] = []
    metric_frames: list[pd.DataFrame] = []
    stress_frames: list[pd.DataFrame] = []
    for scenario, scenario_caches in scenarios.items():
        metrics, _, stress = _run_benchmark(
            snapshot_dir=baseline_root / "combined_snapshot",
            config=config,
            output=output / "benchmark" / scenario,
            feature_caches=scenario_caches,
            extra_features=extras,
        )
        summary = metrics.groupby("model", as_index=False).mean(numeric_only=True)
        summary.insert(0, "scenario", scenario)
        metrics.insert(0, "scenario", scenario)
        stress.insert(0, "scenario", scenario)
        summary_frames.append(summary)
        metric_frames.append(metrics)
        stress_frames.append(stress)

    scenario_summary = pd.concat(summary_frames, ignore_index=True)
    scenario_metrics = pd.concat(metric_frames, ignore_index=True)
    scenario_stress = pd.concat(stress_frames, ignore_index=True)
    scenario_summary.to_csv(output / "scenario_summary.csv", index=False)
    scenario_metrics.to_csv(output / "scenario_fold_metrics.csv", index=False)
    scenario_stress.to_csv(output / "scenario_cost_stress.csv", index=False)
    _scenario_comparison(baseline_root, summary_frames).to_csv(
        output / "baseline_vs_foundation.csv", index=False
    )

    supervised, all_columns, _, _ = _prepare_supervised(
        baseline_root / "combined_snapshot",
        config,
        [caches["timesfm"], caches["chronos"]],
        extras,
    )
    del supervised
    timesfm_columns = [column for column in all_columns if column.startswith("timesfm_")]
    chronos_columns = [column for column in all_columns if column.startswith("chronos_")]
    external_foundation = set(timesfm_columns + chronos_columns)
    ablation_groups: dict[str, list[str]] = {
        "base_features": [column for column in all_columns if column not in external_foundation],
        "timesfm": timesfm_columns,
        "chronos": chronos_columns,
    }
    ablation_metrics: list[pd.DataFrame] = []
    for ablation in build_ablation_plan(ablation_groups):
        metrics, _, _ = _run_benchmark(
            snapshot_dir=baseline_root / "combined_snapshot",
            config=config,
            output=output / "ablation" / ablation.name,
            feature_caches=[caches["timesfm"], caches["chronos"]],
            extra_features=extras,
            override_feature_columns=list(ablation.columns),
        )
        metrics.insert(0, "ablation", ablation.name)
        ablation_metrics.append(metrics)
    combined_ablation = pd.concat(ablation_metrics, ignore_index=True)
    combined_ablation.to_csv(output / "ablation_fold_metrics.csv", index=False)
    summarize_ablation(combined_ablation).to_csv(output / "ablation_summary.csv", index=False)

    combined_experiment = json.loads(
        (output / "benchmark/timesfm_chronos/experiment.json").read_text("utf-8")
    )
    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "status": "historical_challenger_not_activated",
        "created_at": pd.Timestamp.now(tz="UTC").isoformat(),
        "dataset_sha256": snapshot_manifest.content_sha256,
        "baseline_registry_id": json.loads(
            (baseline_root / "source_registry.json").read_text("utf-8")
        )["registry_id"],
        "combined_experiment_id": combined_experiment["experiment_id"],
        "source_tree_sha256": combined_experiment["source_tree_sha256"],
        "device": args.device,
        "python": platform.python_version(),
        "models": evidence,
        "scenarios": list(scenarios),
    }
    manifest["manifest_sha256"] = canonical_json_sha256(manifest)
    _write_json(output / "foundation_manifest.json", manifest)
    (output / "prospective_decisions.jsonl").touch()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timesfm-model", default="google/timesfm-2.5-200m-pytorch")
    parser.add_argument("--timesfm-revision", required=True)
    parser.add_argument("--chronos-model", default="amazon/chronos-2")
    parser.add_argument("--chronos-revision", required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--context", type=int, default=256)
    parser.add_argument("--horizon", type=int, default=6)
    parser.add_argument("--stride", type=int, default=6)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--inference-latency-seconds", type=float, default=120.0)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
