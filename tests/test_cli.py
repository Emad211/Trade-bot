from pathlib import Path

from typer.testing import CliRunner

from hybrid_trader.cli import app

runner = CliRunner()


def test_cli_sample_validate_backtest_and_walk_forward(tmp_path: Path) -> None:
    data_path = tmp_path / "sample.csv"
    artifact_path = tmp_path / "baseline.csv"
    folds_path = tmp_path / "folds.csv"
    config_path = Path("configs/btc_spot_4h.yaml")

    generated = runner.invoke(
        app,
        ["generate-sample", "--output", str(data_path), "--bars", "320", "--seed", "9"],
    )
    assert generated.exit_code == 0, generated.output
    assert data_path.exists()

    validated = runner.invoke(app, ["validate-data", "--input", str(data_path)])
    assert validated.exit_code == 0, validated.output
    assert "Validated 320 bars" in validated.output

    backtested = runner.invoke(
        app,
        [
            "backtest",
            "--input",
            str(data_path),
            "--config",
            str(config_path),
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
            str(config_path),
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
    assert "total_return" in walked.output


def test_cli_rejects_short_sample(tmp_path: Path) -> None:
    data_path = tmp_path / "short.csv"
    generated = runner.invoke(
        app,
        ["generate-sample", "--output", str(data_path), "--bars", "200"],
    )
    assert generated.exit_code == 0, generated.output

    result = runner.invoke(
        app,
        [
            "walk-forward",
            "--input",
            str(data_path),
            "--config",
            "configs/btc_spot_4h.yaml",
            "--initial-train",
            "180",
            "--test-size",
            "50",
        ],
    )
    assert result.exit_code != 0
