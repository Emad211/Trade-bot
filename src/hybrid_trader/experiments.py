"""Reproducible experiment manifests and artifact writing."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from hybrid_trader.data.snapshot import canonical_json_sha256


class ExperimentManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.1"
    experiment_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    dataset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_tree_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    feature_artifact_sha256: tuple[str, ...]
    split_plan_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    feature_columns: tuple[str, ...]
    models: tuple[str, ...]
    config: dict[str, Any]
    package_versions: dict[str, str]
    created_at: datetime


def installed_versions(packages: tuple[str, ...]) -> dict[str, str]:
    versions = {"python": platform.python_version()}
    for package in packages:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "not-installed"
    return versions


def source_tree_sha256(package_root: str | Path | None = None) -> str:
    """Hash all Python source files with their relative paths."""

    root = Path(package_root) if package_root is not None else Path(__file__).resolve().parent
    digest = hashlib.sha256()
    files = sorted(path for path in root.rglob("*.py") if path.is_file())
    if not files:
        raise ValueError(f"No Python source files found under {root}")
    for path in files:
        relative = path.relative_to(root).as_posix().encode()
        digest.update(relative)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def make_manifest(
    *,
    dataset_sha256: str,
    split_plan: dict[str, Any],
    feature_columns: list[str],
    models: list[str],
    config: dict[str, Any],
    feature_artifact_sha256: tuple[str, ...] = (),
    source_sha256: str | None = None,
    created_at: datetime | None = None,
) -> ExperimentManifest:
    versions = installed_versions(
        (
            "hybrid-trader",
            "numpy",
            "pandas",
            "pydantic",
            "scikit-learn",
            "lightgbm",
            "catboost",
            "timesfm",
            "chronos-forecasting",
        )
    )
    source_sha = source_sha256 or source_tree_sha256()
    identity = {
        "dataset_sha256": dataset_sha256,
        "source_tree_sha256": source_sha,
        "feature_artifact_sha256": feature_artifact_sha256,
        "split_plan": split_plan,
        "feature_columns": feature_columns,
        "models": models,
        "config": config,
        "package_versions": versions,
    }
    experiment_id = canonical_json_sha256(identity)
    return ExperimentManifest(
        experiment_id=experiment_id,
        dataset_sha256=dataset_sha256,
        source_tree_sha256=source_sha,
        feature_artifact_sha256=feature_artifact_sha256,
        split_plan_sha256=canonical_json_sha256(split_plan),
        feature_columns=tuple(feature_columns),
        models=tuple(models),
        config=config,
        package_versions=versions,
        created_at=created_at or datetime.now(UTC),
    )


def write_experiment_artifacts(
    output_dir: str | Path,
    *,
    metrics: pd.DataFrame,
    predictions: pd.DataFrame,
    cost_stress: pd.DataFrame,
    manifest: ExperimentManifest,
) -> Path:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()):
        raise FileExistsError(f"Experiment output directory is not empty: {root}")
    metrics.to_csv(root / "fold_metrics.csv", index=False)
    predictions.to_csv(root / "predictions.csv.gz", compression={"method": "gzip", "mtime": 0})
    summary = metrics.groupby("model", as_index=False).mean(numeric_only=True)
    summary.to_csv(root / "summary.csv", index=False)
    cost_stress.to_csv(root / "cost_stress.csv", index=False)
    (root / "experiment.json").write_text(
        json.dumps(manifest.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    digest = hashlib.sha256((root / "experiment.json").read_bytes()).hexdigest()
    (root / "experiment.sha256").write_text(f"{digest}  experiment.json\n", encoding="utf-8")
    return root
