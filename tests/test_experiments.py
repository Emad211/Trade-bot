from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from hybrid_trader.experiments import (
    make_manifest,
    source_tree_sha256,
    write_experiment_artifacts,
)


def test_manifest_identity_excludes_created_at() -> None:
    kwargs = dict(
        dataset_sha256="a" * 64,
        split_plan={"initial_train": 100},
        feature_columns=["x"],
        models=["prior"],
        config={"key": "value"},
        source_sha256="b" * 64,
    )
    first = make_manifest(**kwargs, created_at=datetime(2026, 1, 1, tzinfo=UTC))
    second = make_manifest(**kwargs, created_at=datetime(2026, 1, 2, tzinfo=UTC))
    assert first.experiment_id == second.experiment_id
    assert first.created_at != second.created_at


def test_source_tree_hash_changes_with_source(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "a.py").write_text("x = 1\n")
    first = source_tree_sha256(package)
    (package / "a.py").write_text("x = 2\n")
    assert source_tree_sha256(package) != first


def test_artifact_writer_creates_auditable_files(tmp_path: Path) -> None:
    metrics = pd.DataFrame({"model": ["prior"], "fold": [0], "net_return": [0.1], "sharpe": [1.0]})
    predictions = pd.DataFrame({"model": ["prior"], "probability": [0.5]})
    stress = pd.DataFrame(
        {"model": ["prior"], "fold": [0], "cost_multiplier": [1.0], "net_return": [0.1]}
    )
    manifest = make_manifest(
        dataset_sha256="a" * 64,
        split_plan={"initial_train": 100},
        feature_columns=["x"],
        models=["prior"],
        config={},
        source_sha256="b" * 64,
    )
    root = write_experiment_artifacts(
        tmp_path / "experiment",
        metrics=metrics,
        predictions=predictions,
        cost_stress=stress,
        manifest=manifest,
    )
    assert (root / "fold_metrics.csv").exists()
    assert (root / "predictions.csv.gz").exists()
    assert (root / "summary.csv").exists()
    assert (root / "cost_stress.csv").exists()
    assert (root / "experiment.json").exists()
    assert (root / "experiment.sha256").exists()
