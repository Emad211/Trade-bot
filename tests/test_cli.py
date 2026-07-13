import json
from pathlib import Path

from typer.testing import CliRunner

from hybrid_trader.cli import app

runner = CliRunner()


def test_cli_phase_one_commands(tmp_path: Path) -> None:
    data_path = tmp_path / "sample.csv"
    artifact_path = tmp_path / "baseline.csv"
    folds_path = tmp_path / "folds.csv"

    generated = runner.invoke(
        app,
        ["generate-sample", "--output", str(data_path), "--bars", "400", "--seed", "9"],
    )
    assert generated.exit_code == 0, generated.output

    validated = runner.invoke(app, ["validate-data", "--input", str(data_path)])
    assert validated.exit_code == 0, validated.output
    assert "Validated 400 bars" in validated.output

    backtested = runner.invoke(
        app,
        [
            "backtest",
            "--input",
            str(data_path),
            "--config",
            "configs/btc_spot_4h_smoke.yaml",
            "--output",
            str(artifact_path),
            "--json",
        ],
    )
    assert backtested.exit_code == 0, backtested.output
    assert artifact_path.exists()
    assert "final_equity" in backtested.output

    walked = runner.invoke(
        app,
        [
            "walk-forward",
            "--input",
            str(data_path),
            "--config",
            "configs/btc_spot_4h_smoke.yaml",
            "--initial-train",
            "180",
            "--test-size",
            "50",
            "--gap",
            "1",
            "--output",
            str(folds_path),
        ],
    )
    assert walked.exit_code == 0, walked.output
    assert folds_path.exists()


def test_cli_snapshot_foundation_benchmark_and_forward(tmp_path: Path) -> None:
    data_path = tmp_path / "sample.csv"
    snapshot = tmp_path / "snapshot"
    feature_cache = tmp_path / "features"
    experiment = tmp_path / "experiment"
    ledger = tmp_path / "forward.jsonl"

    generated = runner.invoke(
        app,
        ["generate-sample", "--output", str(data_path), "--bars", "500", "--seed", "11"],
    )
    assert generated.exit_code == 0, generated.output

    created = runner.invoke(
        app,
        [
            "create-snapshot",
            "--input",
            str(data_path),
            "--config",
            "configs/btc_spot_4h_smoke.yaml",
            "--output",
            str(snapshot),
            "--source",
            "synthetic-test",
        ],
    )
    assert created.exit_code == 0, created.output
    manifest = json.loads((snapshot / "manifest.json").read_text())

    foundation = runner.invoke(
        app,
        [
            "foundation-features",
            "--snapshot",
            str(snapshot),
            "--output",
            str(feature_cache),
            "--model",
            "naive",
            "--context-length",
            "64",
            "--min-history",
            "32",
            "--horizon",
            "1",
        ],
    )
    assert foundation.exit_code == 0, foundation.output

    benchmark = runner.invoke(
        app,
        [
            "benchmark",
            "--snapshot",
            str(snapshot),
            "--config",
            "configs/btc_spot_4h_smoke.yaml",
            "--output",
            str(experiment),
            "--feature-cache",
            str(feature_cache),
        ],
    )
    assert benchmark.exit_code == 0, benchmark.output
    assert (experiment / "fold_metrics.csv").exists()
    experiment_manifest = json.loads((experiment / "experiment.json").read_text())

    recorded = runner.invoke(
        app,
        [
            "forward-record",
            "--ledger",
            str(ledger),
            "--decision-time",
            "2026-01-01T00:00:00+03:30",
            "--dataset-sha256",
            manifest["content_sha256"],
            "--experiment-id",
            experiment_manifest["experiment_id"],
            "--probability",
            "0.7",
            "--threshold",
            "0.6",
            "--desired-exposure",
            "0.2",
            "--reason-code",
            "smoke",
        ],
    )
    assert recorded.exit_code == 0, recorded.output
    verified = runner.invoke(app, ["forward-verify", "--ledger", str(ledger)])
    assert verified.exit_code == 0, verified.output
    assert '"records": 1' in verified.output
