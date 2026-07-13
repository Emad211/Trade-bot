"""Command-line interface for data, backtests and validation."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import typer
from rich.console import Console
from rich.table import Table

from hybrid_trader.backtest import run_backtest
from hybrid_trader.config import load_config
from hybrid_trader.data import read_ohlcv_csv, write_ohlcv_csv
from hybrid_trader.data.ccxt_source import CCXTOHLCVSource
from hybrid_trader.strategies import generate_trend_exposure
from hybrid_trader.walkforward import run_walk_forward

app = typer.Typer(no_args_is_help=True, help="Hybrid Trader Phase-1 research CLI")
console = Console()


def _print_metrics(metrics: dict[str, float]) -> None:
    table = Table(title="Backtest metrics")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    for key, value in metrics.items():
        table.add_row(key, f"{value:.6f}")
    console.print(table)


@app.command("generate-sample")
def generate_sample(
    output: Path = typer.Option(Path("data/sample_btc_4h.csv"), "--output", "-o"),
    bars: int = typer.Option(1200, min=200),
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
    """Validate an OHLCV CSV and fail on unsafe data."""

    data = read_ohlcv_csv(input_path)
    console.print(
        f"Validated {len(data)} bars from {data.index.min()} through {data.index.max()}"
    )


@app.command("download-ohlcv")
def download_ohlcv(
    exchange: str = typer.Option("kraken"),
    symbol: str = typer.Option("BTC/USD"),
    timeframe: str = typer.Option("4h"),
    output: Path = typer.Option(Path("data/btc_4h.csv"), "--output", "-o"),
    since_ms: int | None = typer.Option(None),
    max_pages: int = typer.Option(20, min=1, max=500),
) -> None:
    """Download public candles through CCXT; no credentials are used."""

    source = CCXTOHLCVSource(exchange)
    data = source.fetch(
        symbol,
        timeframe,
        since_ms=since_ms,
        max_pages=max_pages,
    )
    path = write_ohlcv_csv(data, output)
    console.print(f"Wrote {len(data)} bars to [bold]{path}[/bold]")


@app.command("backtest")
def backtest(
    input_path: Path = typer.Option(..., "--input", "-i"),
    config_path: Path = typer.Option(..., "--config", "-c"),
    output: Path | None = typer.Option(None, "--output", "-o"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Run the Phase-1 long/flat trend baseline."""

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
    """Run expanding-window out-of-sample evaluation."""

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
