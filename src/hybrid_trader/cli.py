"""Command-line interface for data, sealed benchmarks and prospective research."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import typer
from rich.console import Console
from rich.table import Table

from hybrid_trader.ablation import build_ablation_plan, summarize_ablation
from hybrid_trader.audit import audit_snapshots, audit_tables
from hybrid_trader.backtest import run_backtest
from hybrid_trader.config import AppConfig, load_config
from hybrid_trader.data import (
    add_bar_availability,
    read_ohlcv_csv,
    read_snapshot,
    write_ohlcv_csv,
    write_snapshot,
)
from hybrid_trader.data.asof import merge_asof_features
from hybrid_trader.data.ccxt_source import CCXTOHLCVSource
from hybrid_trader.data.derivatives import CCXTDerivativesSource, UnsupportedPublicEndpoint
from hybrid_trader.data.multi_market import add_local_market_premium
from hybrid_trader.evaluation import ModelFactory, run_sealed_benchmark
from hybrid_trader.experiments import make_manifest, write_experiment_artifacts
from hybrid_trader.features import build_supervised_frame
from hybrid_trader.forecasting import (
    Chronos2Forecaster,
    ChronosSettings,
    NaiveReturnForecaster,
    TimesFMForecaster,
    TimesFMSettings,
)
from hybrid_trader.forecasting.base import TimeSeriesForecaster
from hybrid_trader.forecasting.rolling import (
    RollingForecastSpec,
    cache_rolling_features,
    read_cached_rolling_features,
    rolling_forecast_features,
)
from hybrid_trader.forward import (
    append_forward_decision,
    ledger_head,
    make_forward_decision,
    verify_forward_ledger,
)
from hybrid_trader.models import (
    CatBoostProbabilityModel,
    LightGBMProbabilityModel,
    PriorProbabilityModel,
    RidgeLogisticModel,
)
from hybrid_trader.phase2c import load_phase2c_spec
from hybrid_trader.registry import (
    ExperimentRecord,
    append_registry_record,
    file_sha256,
    verify_registry,
)
from hybrid_trader.reporting import build_phase2c_report, write_phase2c_report
from hybrid_trader.splits import SplitSpec
from hybrid_trader.strategies import generate_trend_exposure
from hybrid_trader.walkforward import run_walk_forward

app = typer.Typer(no_args_is_help=True, help="Hybrid Trader leakage-aware research CLI")
console = Console()


def _print_metrics(metrics: dict[str, float]) -> None:
    table = Table(title="Backtest metrics")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    for key, value in metrics.items():
        table.add_row(key, f"{value:.6f}")
    console.print(table)


def _iso_to_utc(value: str | None) -> pd.Timestamp | None:
    if value is None:
        return None
    timestamp = pd.Timestamp(value)
    return timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp.tz_convert("UTC")


def _model_factories(config: AppConfig) -> list[ModelFactory]:
    factories: dict[str, ModelFactory] = {
        "prior": lambda: PriorProbabilityModel(),
        "ridge_logistic": lambda: RidgeLogisticModel(
            c=config.ml.ridge_c, random_seed=config.ml.random_seed
        ),
        "lightgbm": lambda: LightGBMProbabilityModel(random_seed=config.ml.random_seed),
        "catboost": lambda: CatBoostProbabilityModel(random_seed=config.ml.random_seed),
    }
    unknown = set(config.ml.models).difference(factories)
    if unknown:
        raise ValueError(f"Unknown model names: {sorted(unknown)}")
    selected: list[ModelFactory] = []
    for name in config.ml.models:
        factory = factories[name]
        try:
            factory()
        except RuntimeError as exc:
            console.print(f"[yellow]Skipping {name}: {exc}[/yellow]")
            continue
        selected.append(factory)
    if not selected:
        raise RuntimeError("No benchmark model is available")
    return selected


def _load_feature_cache(path: Path, *, expected_dataset_sha256: str) -> tuple[pd.DataFrame, str]:
    frame, manifest = read_cached_rolling_features(
        path, expected_dataset_sha256=expected_dataset_sha256
    )
    return frame, manifest.feature_sha256


def _prepare_supervised(
    snapshot_dir: Path,
    config: AppConfig,
    feature_caches: list[Path],
    extra_features: list[str],
) -> tuple[pd.DataFrame, list[str], str, tuple[str, ...]]:
    data, manifest = read_snapshot(snapshot_dir)
    feature_hashes: list[str] = []
    feature_availability: list[pd.Series] = []
    for cache_index, cache in enumerate(feature_caches):
        feature_frame, feature_sha = _load_feature_cache(
            cache, expected_dataset_sha256=manifest.content_sha256
        )
        feature_hashes.append(feature_sha)
        if "available_at" in feature_frame:
            feature_availability.append(
                pd.to_datetime(feature_frame.pop("available_at"), utc=True).rename(
                    f"feature_available_at_{cache_index}"
                )
            )
        overlap = set(data.columns).intersection(feature_frame.columns)
        if overlap:
            raise ValueError(f"Feature cache duplicates columns: {sorted(overlap)}")
        data = data.join(feature_frame, how="left")
    if feature_availability:
        availability = pd.concat(
            [pd.to_datetime(data["available_at"], utc=True), *feature_availability], axis=1
        ).max(axis=1)
        data["available_at"] = pd.to_datetime(availability, utc=True)

    supervised, feature_columns = build_supervised_frame(data, config)
    trend = generate_trend_exposure(data, config)
    supervised["trend_desired_exposure"] = trend.loc[supervised.index, "desired_exposure"].to_numpy(
        dtype=float
    )

    auto_prefixes = (
        "funding_",
        "open_interest",
        "basis",
        "local_premium",
        "naive_",
        "timesfm_",
        "chronos_",
    )
    automatic = [
        column
        for column in supervised.columns
        if column.startswith(auto_prefixes)
        and not column.endswith("__available_at")
        and column not in feature_columns
    ]
    requested = [*automatic, *extra_features]
    missing = set(requested).difference(supervised.columns)
    if missing:
        raise ValueError(f"Requested feature columns not found: {sorted(missing)}")
    for column in requested:
        supervised[column] = pd.to_numeric(supervised[column], errors="coerce").replace(
            [np.inf, -np.inf], np.nan
        )
    feature_columns.extend(column for column in requested if column not in feature_columns)
    return supervised, feature_columns, manifest.content_sha256, tuple(feature_hashes)


def _run_benchmark(
    *,
    snapshot_dir: Path,
    config: AppConfig,
    output: Path,
    feature_caches: list[Path],
    extra_features: list[str],
    override_feature_columns: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    supervised, feature_columns, dataset_sha, feature_hashes = _prepare_supervised(
        snapshot_dir, config, feature_caches, extra_features
    )
    if override_feature_columns is not None:
        missing = set(override_feature_columns).difference(supervised.columns)
        if missing:
            raise ValueError(f"Ablation references missing columns: {sorted(missing)}")
        feature_columns = override_feature_columns
    split = SplitSpec(
        initial_train=config.evaluation.initial_train,
        calibration_size=config.evaluation.calibration_size,
        validation_size=config.evaluation.validation_size,
        test_size=config.evaluation.test_size,
        step_size=config.evaluation.step_size,
        embargo=config.evaluation.embargo,
    )
    factories = _model_factories(config)
    metrics, predictions, stress = run_sealed_benchmark(
        supervised,
        feature_columns=feature_columns,
        model_factories=factories,
        split_spec=split,
        config=config,
        thresholds=config.evaluation.thresholds,
        min_entries=config.evaluation.min_entries,
        drawdown_penalty=config.evaluation.drawdown_penalty,
        cost_multipliers=config.evaluation.cost_multipliers,
    )
    model_names = sorted(metrics["model"].unique().tolist())
    manifest = make_manifest(
        dataset_sha256=dataset_sha,
        split_plan=split.to_dict(),
        feature_columns=feature_columns,
        models=model_names,
        config=config.model_dump(mode="json"),
        feature_artifact_sha256=feature_hashes,
    )
    write_experiment_artifacts(
        output,
        metrics=metrics,
        predictions=predictions,
        cost_stress=stress,
        manifest=manifest,
    )
    return metrics, predictions, stress


@app.command("generate-sample")
def generate_sample(
    output: Path = typer.Option(Path("data/sample_btc_4h.csv"), "--output", "-o"),
    bars: int = typer.Option(1800, min=200),
    seed: int = typer.Option(42),
) -> None:
    """Generate deterministic synthetic OHLCV for smoke tests only."""

    rng = np.random.default_rng(seed)
    timestamps = pd.date_range("2023-01-01", periods=bars, freq="4h", tz="UTC")
    regime = np.where(np.arange(bars) % 360 < 240, 0.0008, -0.0004)
    log_returns = regime + rng.normal(0, 0.018, size=bars)
    close = 20_000 * np.exp(np.cumsum(log_returns))
    open_ = np.r_[close[0], close[:-1]]
    intrabar = np.abs(rng.normal(0.012, 0.005, size=bars))
    high = np.maximum(open_, close) * (1 + intrabar)
    low = np.minimum(open_, close) * np.maximum(0.01, 1 - intrabar)
    volume = rng.lognormal(mean=8.0, sigma=0.55, size=bars)
    frame = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )
    path = write_ohlcv_csv(frame, output)
    console.print(f"Wrote {bars} synthetic bars to [bold]{path}[/bold]")


@app.command("validate-data")
def validate_data(input_path: Path = typer.Option(..., "--input", "-i")) -> None:
    data = read_ohlcv_csv(input_path)
    console.print(f"Validated {len(data)} bars from {data.index.min()} through {data.index.max()}")


@app.command("download-ohlcv")
def download_ohlcv(
    exchange: str = typer.Option("kraken"),
    symbol: str = typer.Option("BTC/USD"),
    timeframe: str = typer.Option("4h"),
    output: Path = typer.Option(Path("data/btc_4h.csv"), "--output", "-o"),
    since_ms: int | None = typer.Option(None),
    max_pages: int = typer.Option(20, min=1, max=500),
) -> None:
    source = CCXTOHLCVSource(exchange)
    data = source.fetch(symbol, timeframe, since_ms=since_ms, max_pages=max_pages)
    path = write_ohlcv_csv(data, output)
    console.print(f"Wrote {len(data)} completed bars to [bold]{path}[/bold]")


@app.command("create-snapshot")
def create_snapshot(
    input_path: Path = typer.Option(..., "--input", "-i"),
    config_path: Path = typer.Option(..., "--config", "-c"),
    output: Path = typer.Option(..., "--output", "-o"),
    source: str = typer.Option("csv"),
) -> None:
    config = load_config(config_path)
    raw = read_ohlcv_csv(input_path)
    pit = add_bar_availability(
        raw.reset_index(),
        timeframe=config.market.timeframe,
        source_latency=timedelta(seconds=config.data.source_latency_seconds),
    )
    manifest = write_snapshot(
        pit,
        output,
        source=source,
        symbol=config.market.symbol,
        timeframe=config.market.timeframe,
        source_latency_seconds=config.data.source_latency_seconds,
    )
    console.print_json(manifest.model_dump_json())


@app.command("inspect-snapshot")
def inspect_snapshot(snapshot_dir: Path = typer.Option(..., "--snapshot")) -> None:
    _, manifest = read_snapshot(snapshot_dir)
    console.print_json(manifest.model_dump_json())


@app.command("download-real-snapshot")
def download_real_snapshot(
    output: Path = typer.Option(..., "--output", "-o"),
    config_path: Path = typer.Option(..., "--config", "-c"),
    global_exchange: str = typer.Option("kraken"),
    global_symbol: str = typer.Option("BTC/USD"),
    derivative_exchange: str | None = typer.Option(None),
    derivative_symbol: str = typer.Option("BTC/USDT:USDT"),
    local_exchange: str | None = typer.Option(None),
    local_btc_symbol: str = typer.Option("BTC/IRT"),
    local_stable_symbol: str = typer.Option("USDT/IRT"),
    since: str | None = typer.Option(None),
    until: str | None = typer.Option(None, help="Inclusive event-time cutoff"),
    as_of: str | None = typer.Option(
        None, help="Observation cutoff; defaults to the current UTC time"
    ),
    derivative_latency_seconds: float = typer.Option(60.0, min=0.0),
    max_pages: int = typer.Option(100, min=1, max=500),
    strict_optional_sources: bool = typer.Option(False),
) -> None:
    """Build a public-data snapshot; no API credentials or orders are used."""

    config = load_config(config_path)
    since_time = _iso_to_utc(since)
    until_time = _iso_to_utc(until)
    observed_at = _iso_to_utc(as_of) or pd.Timestamp.now(tz="UTC")
    if since_time is not None and since_time > observed_at:
        raise typer.BadParameter("since cannot be later than as_of")
    if until_time is not None and since_time is not None and until_time < since_time:
        raise typer.BadParameter("until cannot be earlier than since")
    effective_until = min(value for value in (until_time, observed_at) if value is not None)
    since_ms = int(since_time.timestamp() * 1000) if since_time is not None else None
    until_ms = int(effective_until.timestamp() * 1000)
    latency = timedelta(seconds=config.data.source_latency_seconds)
    derivative_latency = timedelta(seconds=derivative_latency_seconds)
    market = CCXTOHLCVSource(global_exchange).fetch_point_in_time(
        global_symbol,
        config.market.timeframe,
        source_latency=latency,
        since_ms=since_ms,
        until_ms=until_ms,
        max_pages=max_pages,
        now=observed_at.to_pydatetime(),
    )
    sources = [f"ccxt:{global_exchange}:{global_symbol}"]

    if derivative_exchange is not None:
        derivatives = CCXTDerivativesSource(derivative_exchange)
        derivative_jobs: list[tuple[str, Any, list[str]]] = [
            (
                "funding",
                lambda: derivatives.fetch_funding_history(
                    derivative_symbol,
                    since_ms=since_ms,
                    until_ms=until_ms,
                    max_pages=max_pages,
                    source_latency=derivative_latency,
                ),
                ["funding_rate"],
            ),
            (
                "open_interest",
                lambda: derivatives.fetch_open_interest_history(
                    derivative_symbol,
                    config.market.timeframe,
                    since_ms=since_ms,
                    until_ms=until_ms,
                    max_pages=max_pages,
                    source_latency=derivative_latency,
                ),
                ["open_interest"],
            ),
            (
                "basis",
                lambda: derivatives.fetch_basis_history(
                    derivative_symbol,
                    config.market.timeframe,
                    since_ms=since_ms,
                    until_ms=until_ms,
                    max_pages=max_pages,
                    source_latency=derivative_latency,
                ),
                ["mark_price", "index_price", "basis"],
            ),
        ]
        for name, job, columns in derivative_jobs:
            try:
                external = job()
                external = external.loc[
                    pd.to_datetime(external["available_at"], utc=True) <= observed_at
                ].copy()
                if external.empty:
                    raise RuntimeError(f"No {name} rows were observable by as_of")
                market = merge_asof_features(
                    market,
                    external,
                    feature_columns=columns,
                    provenance_column=f"{name}__available_at",
                )
                sources.append(f"ccxt:{derivative_exchange}:{name}")
            except (UnsupportedPublicEndpoint, RuntimeError) as exc:
                if strict_optional_sources:
                    raise
                console.print(f"[yellow]Skipping {name}: {exc}[/yellow]")

    if local_exchange is not None:
        local_btc = CCXTOHLCVSource(local_exchange).fetch_point_in_time(
            local_btc_symbol,
            config.market.timeframe,
            source_latency=latency,
            since_ms=since_ms,
            until_ms=until_ms,
            max_pages=max_pages,
            now=observed_at.to_pydatetime(),
        )
        local_stable = CCXTOHLCVSource(local_exchange).fetch_point_in_time(
            local_stable_symbol,
            config.market.timeframe,
            source_latency=latency,
            since_ms=since_ms,
            until_ms=until_ms,
            max_pages=max_pages,
            now=observed_at.to_pydatetime(),
        )
        market = add_local_market_premium(market, local_btc, local_stable)
        sources.append(f"ccxt:{local_exchange}:local-premium")

    manifest = write_snapshot(
        market,
        output,
        source=";".join(sources),
        symbol=global_symbol,
        timeframe=config.market.timeframe,
        source_latency_seconds=config.data.source_latency_seconds,
        created_at=observed_at.to_pydatetime(),
        notes=(
            "Public data only. Exchange availability is not trading permission. "
            f"Derivative latency={derivative_latency_seconds:.3f}s; "
            f"observation cutoff={observed_at.isoformat()}."
        ),
    )
    console.print_json(manifest.model_dump_json())


@app.command("foundation-features")
def foundation_features(
    snapshot_dir: Path = typer.Option(..., "--snapshot"),
    output: Path = typer.Option(..., "--output", "-o"),
    model: str = typer.Option("naive", help="naive, timesfm or chronos"),
    target: str = typer.Option("log_return", help="log_return or close"),
    context_length: int = typer.Option(512, min=32),
    min_history: int = typer.Option(128, min=16),
    horizon: int = typer.Option(3, min=1),
    stride: int = typer.Option(1, min=1),
    revision: str | None = typer.Option(None),
    device: str = typer.Option("cpu"),
    inference_latency_seconds: float = typer.Option(0.0, min=0.0),
) -> None:
    data, manifest = read_snapshot(snapshot_dir)
    if target == "log_return":
        series = np.log(data["close"]).diff().dropna()
    elif target == "close":
        series = data["close"]
    else:
        raise typer.BadParameter("target must be log_return or close")

    forecaster: TimeSeriesForecaster
    if model == "naive":
        forecaster = NaiveReturnForecaster()
        model_id, prefix = "naive-zero-return", "naive"
    elif model == "timesfm":
        timesfm_settings = TimesFMSettings(
            revision=revision,
            max_context=context_length,
            max_horizon=max(horizon, 1),
        )
        forecaster = TimesFMForecaster(timesfm_settings)
        model_id, prefix = timesfm_settings.model_id, "timesfm"
    elif model == "chronos":
        chronos_settings = ChronosSettings(
            revision=revision, device_map=device, context_length=context_length
        )
        forecaster = Chronos2Forecaster(chronos_settings)
        model_id, prefix = chronos_settings.model_id, "chronos"
    else:
        raise typer.BadParameter("model must be naive, timesfm or chronos")

    spec = RollingForecastSpec(
        context_length=context_length,
        horizon=horizon,
        min_history=min_history,
        stride=stride,
        prefix=prefix,
        inference_latency_seconds=inference_latency_seconds,
    )
    availability = pd.to_datetime(data.loc[series.index, "available_at"], utc=True)
    features = rolling_forecast_features(series, forecaster, spec, availability=availability)
    digest = cache_rolling_features(
        features,
        output,
        dataset_sha256=manifest.content_sha256,
        model_id=model_id,
        model_revision=revision,
        spec=spec,
    )
    console.print(f"Generated {len(features)} origins; feature SHA-256: [bold]{digest}[/bold]")


@app.command("benchmark")
def benchmark(
    snapshot_dir: Path = typer.Option(..., "--snapshot"),
    config_path: Path = typer.Option(..., "--config", "-c"),
    output: Path = typer.Option(..., "--output", "-o"),
    feature_cache: list[Path] | None = typer.Option(None, "--feature-cache"),
    extra_feature: list[str] | None = typer.Option(None, "--extra-feature"),
) -> None:
    config = load_config(config_path)
    metrics, _, _ = _run_benchmark(
        snapshot_dir=snapshot_dir,
        config=config,
        output=output,
        feature_caches=feature_cache or [],
        extra_features=extra_feature or [],
    )
    console.print(metrics.groupby("model").mean(numeric_only=True).to_string())


@app.command("ablation")
def ablation(
    snapshot_dir: Path = typer.Option(..., "--snapshot"),
    config_path: Path = typer.Option(..., "--config", "-c"),
    groups_path: Path = typer.Option(..., "--groups"),
    output: Path = typer.Option(..., "--output", "-o"),
    feature_cache: list[Path] | None = typer.Option(None, "--feature-cache"),
    extra_feature: list[str] | None = typer.Option(None, "--extra-feature"),
) -> None:
    config = load_config(config_path)
    groups = json.loads(groups_path.read_text("utf-8"))
    if not isinstance(groups, dict) or not all(
        isinstance(key, str)
        and isinstance(value, list)
        and all(isinstance(column, str) for column in value)
        for key, value in groups.items()
    ):
        raise typer.BadParameter("groups must be a JSON object of string lists")
    all_metrics: list[pd.DataFrame] = []
    for run in build_ablation_plan(groups):
        run_output = output / run.name
        metrics, _, _ = _run_benchmark(
            snapshot_dir=snapshot_dir,
            config=config,
            output=run_output,
            feature_caches=feature_cache or [],
            extra_features=extra_feature or [],
            override_feature_columns=list(run.columns),
        )
        metrics.insert(0, "ablation", run.name)
        all_metrics.append(metrics)
    combined = pd.concat(all_metrics, ignore_index=True)
    output.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output / "ablation_fold_metrics.csv", index=False)
    summary = summarize_ablation(combined)
    summary.to_csv(output / "ablation_summary.csv", index=False)
    console.print(summary.to_string(index=False))


def _artifact_hashes(paths: list[Path]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for supplied in paths:
        if not supplied.exists():
            raise FileNotFoundError(f"Artifact path not found: {supplied}")
        files = sorted(supplied.rglob("*")) if supplied.is_dir() else [supplied]
        for path in files:
            if not path.is_file():
                continue
            key = (
                f"{supplied.name}/{path.relative_to(supplied).as_posix()}"
                if supplied.is_dir()
                else supplied.name
            )
            if key in hashes:
                raise ValueError(f"Duplicate artifact registry key: {key}")
            hashes[key] = file_sha256(path)
    return hashes


@app.command("phase2c-plan")
def phase2c_plan(spec_path: Path = typer.Option(..., "--spec")) -> None:
    """Validate and print the immutable Phase 2C plan identity."""

    spec = load_phase2c_spec(spec_path)
    payload = {
        "experiment_name": spec.experiment_name,
        "plan_sha256": spec.plan_sha256,
        "as_of": spec.as_of.isoformat(),
        "since": spec.since.isoformat(),
        "spot_sources": [
            source.source_id for source in spec.sources if source.dataset_kind == "spot_ohlcv"
        ],
        "source_contract_sha256": {
            source.source_id: source.contract_sha256 for source in spec.sources
        },
        "model_matrix": list(spec.model_matrix),
    }
    console.print_json(json.dumps(payload))


@app.command("audit-snapshots")
def audit_snapshot_command(
    snapshots: list[Path] = typer.Option(..., "--snapshot"),
    output: Path = typer.Option(..., "--output", "-o"),
) -> None:
    """Audit two or more immutable spot snapshots and their cross-venue agreement."""

    report = audit_snapshots(snapshots)
    snapshot_table, pair_table = audit_tables(report)
    output.mkdir(parents=True, exist_ok=True)
    (output / "dataset_audit.json").write_text(
        report.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    snapshot_table.to_csv(output / "snapshot_quality.csv", index=False)
    pair_table.to_csv(output / "cross_venue_quality.csv", index=False)
    console.print(snapshot_table.to_string(index=False))
    console.print(pair_table.to_string(index=False))


@app.command("phase2c-report")
def phase2c_report_command(
    experiment_dir: Path = typer.Option(..., "--experiment"),
    spec_path: Path = typer.Option(..., "--spec"),
    output: Path = typer.Option(..., "--output", "-o"),
) -> None:
    """Build concentration, tail, cost-stress and promotion-gate reports."""

    spec = load_phase2c_spec(spec_path)
    report = build_phase2c_report(experiment_dir, spec)
    write_phase2c_report(report, output)
    console.print(report.gate_results.to_string(index=False))


@app.command("registry-append")
def registry_append_command(
    registry: Path = typer.Option(..., "--registry"),
    spec_path: Path = typer.Option(..., "--spec"),
    status: str = typer.Option(..., help="completed, null, failed or blocked"),
    dataset_sha256: list[str] | None = typer.Option(None, "--dataset-sha256"),
    experiment_dir: Path | None = typer.Option(None, "--experiment"),
    artifact: list[Path] | None = typer.Option(None, "--artifact"),
    notes: str = typer.Option(""),
) -> None:
    """Append an outcome without deleting null, failed or blocked experiments."""

    if status not in {"completed", "null", "failed", "blocked"}:
        raise typer.BadParameter("status must be completed, null, failed or blocked")
    spec = load_phase2c_spec(spec_path)
    experiment_id: str | None = None
    datasets = list(dataset_sha256 or [])
    summary: dict[str, float | int | str | bool | None] = {}
    artifact_paths = list(artifact or [])
    if experiment_dir is not None:
        manifest_path = experiment_dir / "experiment.json"
        manifest = json.loads(manifest_path.read_text("utf-8"))
        experiment_id = str(manifest["experiment_id"])
        datasets.append(str(manifest["dataset_sha256"]))
        artifact_paths.append(experiment_dir)
        summary_path = experiment_dir / "summary.csv"
        if summary_path.exists():
            table = pd.read_csv(summary_path)
            summary["models"] = int(table["model"].nunique()) if "model" in table else len(table)
            summary["summary_rows"] = len(table)
    datasets = list(dict.fromkeys(datasets))
    if status in {"completed", "null"} and not datasets:
        raise typer.BadParameter("Completed/null records require at least one dataset SHA-256")
    head, _, _ = verify_registry(registry)
    record = ExperimentRecord(
        recorded_at=datetime.now(UTC),
        status=status,
        plan_sha256=spec.plan_sha256,
        experiment_id=experiment_id,
        dataset_sha256=tuple(datasets),
        artifact_sha256=_artifact_hashes(artifact_paths),
        summary=summary,
        notes=notes,
        previous_record_sha256=head,
    )
    digest = append_registry_record(registry, record)
    console.print(f"Appended experiment registry record: [bold]{digest}[/bold]")


@app.command("registry-verify")
def registry_verify_command(registry: Path = typer.Option(..., "--registry")) -> None:
    head, record, count = verify_registry(registry)
    payload = {
        "records": count,
        "head_sha256": head,
        "last_status": record.status if record else None,
        "last_recorded_at": record.recorded_at.isoformat() if record else None,
    }
    console.print_json(json.dumps(payload))


@app.command("forward-record")
def forward_record(
    ledger: Path = typer.Option(Path("artifacts/forward/decisions.jsonl")),
    decision_time: str = typer.Option(...),
    symbol: str = typer.Option("BTC/USD"),
    dataset_sha256: str = typer.Option(...),
    experiment_id: str = typer.Option(...),
    probability: float = typer.Option(..., min=0, max=1),
    threshold: float = typer.Option(..., min=0.000001, max=0.999999),
    desired_exposure: float = typer.Option(..., min=0, max=1),
    reason_code: list[str] | None = typer.Option(None, "--reason-code"),
) -> None:
    head, _ = ledger_head(ledger)
    observed_timestamp = _iso_to_utc(decision_time)
    if observed_timestamp is None:
        raise typer.BadParameter("decision_time is required")
    decision = make_forward_decision(
        decision_time=observed_timestamp.to_pydatetime(),
        symbol=symbol,
        dataset_sha256=dataset_sha256,
        experiment_id=experiment_id,
        probability=probability,
        threshold=threshold,
        desired_exposure=desired_exposure,
        reason_codes=tuple(reason_code or []),
        previous_record_sha256=head,
    )
    digest = append_forward_decision(ledger, decision)
    console.print(f"Appended prospective decision: [bold]{digest}[/bold]")


@app.command("forward-verify")
def forward_verify(
    ledger: Path = typer.Option(Path("artifacts/forward/decisions.jsonl")),
) -> None:
    head, decision, count = verify_forward_ledger(ledger)
    payload = {
        "records": count,
        "head_sha256": head,
        "last_decision_time": decision.decision_time.isoformat() if decision else None,
    }
    console.print_json(json.dumps(payload))


@app.command("backtest")
def backtest(
    input_path: Path = typer.Option(..., "--input", "-i"),
    config_path: Path = typer.Option(..., "--config", "-c"),
    output: Path | None = typer.Option(None, "--output", "-o"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    config = load_config(config_path)
    data = read_ohlcv_csv(input_path)
    signal_frame = generate_trend_exposure(data, config)
    result = run_backtest(signal_frame, config)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        result.frame.to_csv(output)
    if json_output:
        console.print_json(json.dumps(result.metrics))
    else:
        _print_metrics(result.metrics)


@app.command("walk-forward")
def walk_forward(
    input_path: Path = typer.Option(..., "--input", "-i"),
    config_path: Path = typer.Option(..., "--config", "-c"),
    initial_train: int = typer.Option(600, min=150),
    test_size: int = typer.Option(120, min=20),
    gap: int = typer.Option(1, min=0),
    output: Path | None = typer.Option(None, "--output", "-o"),
) -> None:
    config = load_config(config_path)
    data = read_ohlcv_csv(input_path)
    results = run_walk_forward(
        data,
        config,
        initial_train=initial_train,
        test_size=test_size,
        gap=gap,
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        results.to_csv(output, index=False)
    console.print(results.to_string(index=False))


if __name__ == "__main__":
    app()
