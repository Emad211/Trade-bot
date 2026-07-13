import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from hybrid_trader.phase2c import Phase2CSpec, SourceContract
from hybrid_trader.reporting import build_phase2c_report, write_phase2c_report


def _spec() -> Phase2CSpec:
    sources = tuple(
        SourceContract(
            source_id=source_id,
            dataset_kind="spot_ohlcv",
            provider=source_id,
            symbol="BTC/USD",
            timeframe="4h",
            retrieval_method="public",
            event_time_policy="open",
            availability_time_policy="close",
            source_latency_seconds=30,
            revision_policy="append_only",
        )
        for source_id in ("left", "right")
    )
    return Phase2CSpec(
        experiment_name="unit-report",
        as_of=datetime(2026, 7, 13, tzinfo=UTC),
        since=datetime(2026, 3, 1, tzinfo=UTC),
        canonical_spot_source="left",
        sources=sources,
        model_matrix=("prior", "trend"),
    )


def test_phase2c_report_writes_strict_json_and_tail_metrics(tmp_path: Path) -> None:
    experiment = tmp_path / "experiment"
    output = tmp_path / "report"
    experiment.mkdir()
    metrics = pd.DataFrame(
        {
            "fold": [0, 1, 2, 0, 1, 2],
            "model": ["prior"] * 3 + ["trend"] * 3,
            "net_return": [0.02, -0.01, 0.03, 0.01, 0.02, -0.01],
            "sharpe": [1.0, -0.5, 1.2, 0.4, 0.8, -0.2],
            "max_drawdown": [-0.03, -0.04, -0.02, -0.02, -0.03, -0.04],
            "brier": [0.24, 0.25, 0.23, np.nan, np.nan, np.nan],
        }
    )
    metrics.to_csv(experiment / "fold_metrics.csv", index=False)
    index = pd.date_range("2026-01-01", periods=12, freq="4h", tz="UTC")
    predictions = []
    for model in ("prior", "trend"):
        frame = pd.DataFrame(
            {
                "model": model,
                "target_return": np.linspace(-0.08, 0.08, 12),
                "target_positive": [0] * 6 + [1] * 6,
                "net_return": np.linspace(-0.005, 0.006, 12),
                "gross_return": np.linspace(-0.004, 0.007, 12),
                "exposure": [0.2] * 12,
                "probability": [0.55] * 12 if model == "prior" else [np.nan] * 12,
            },
            index=index,
        )
        frame.index.name = "timestamp"
        predictions.append(frame)
    pd.concat(predictions).to_csv(
        experiment / "predictions.csv.gz", compression={"method": "gzip", "mtime": 0}
    )
    stress = pd.DataFrame(
        {
            "fold": [0, 1, 2] * 4,
            "model": ["prior"] * 6 + ["trend"] * 6,
            "cost_multiplier": [1.0] * 3 + [2.0] * 3 + [1.0] * 3 + [2.0] * 3,
            "net_return": [0.02, 0.01, 0.02, 0.01, 0.0, 0.01, 0.01, 0.02, 0.01, 0.0, -0.01, 0.0],
            "max_drawdown": [-0.03] * 12,
        }
    )
    stress.to_csv(experiment / "cost_stress.csv", index=False)
    (experiment / "experiment.json").write_text(
        json.dumps({"experiment_id": "a" * 64, "dataset_sha256": "b" * 64})
    )

    report = build_phase2c_report(experiment, _spec())
    write_phase2c_report(report, output)
    payload = json.loads((output / "phase2c_report.json").read_text())
    assert payload["experiment_id"] == "a" * 64
    assert len(payload["models"]) == 2
    assert (output / "phase2c_report.md").exists()
    assert set(report.gate_results["classification"]) <= {"candidate", "reject_or_insufficient"}
