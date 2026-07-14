"""Leakage-safe rolling foundation-model feature generation and caching."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from hybrid_trader.data.snapshot import canonical_json_sha256
from hybrid_trader.forecasting.base import TimeSeriesForecaster


@dataclass(frozen=True)
class RollingForecastSpec:
    context_length: int = 512
    horizon: int = 1
    min_history: int = 128
    stride: int = 1
    prefix: str = "foundation"
    inference_latency_seconds: float = 0.0

    def __post_init__(self) -> None:
        if self.context_length <= 0 or self.horizon <= 0 or self.min_history <= 0:
            raise ValueError("Rolling forecast lengths must be positive")
        if self.min_history > self.context_length:
            raise ValueError("min_history cannot exceed context_length")
        if self.stride <= 0:
            raise ValueError("stride must be positive")
        if self.inference_latency_seconds < 0:
            raise ValueError("inference_latency_seconds cannot be negative")
        if not self.prefix or not self.prefix.replace("_", "").isalnum():
            raise ValueError(
                "prefix must be non-empty and contain only letters, digits or underscores"
            )


class RollingFeatureManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.2"
    cache_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    dataset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    model_id: str
    model_revision: str | None
    spec: dict[str, object]
    feature_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    row_count: int = Field(gt=0)
    columns: tuple[str, ...]


def rolling_forecast_features(
    series: pd.Series,
    forecaster: TimeSeriesForecaster,
    spec: RollingForecastSpec,
    *,
    availability: pd.Series | None = None,
) -> pd.DataFrame:
    """Forecast each origin using history ending exactly at that origin."""

    if not isinstance(series.index, pd.DatetimeIndex):
        raise ValueError("Forecast series requires a DatetimeIndex")
    if not series.index.is_monotonic_increasing or series.index.has_duplicates:
        raise ValueError("Forecast series index must be unique and sorted")
    observed_availability: pd.Series | None = None
    if availability is not None:
        observed_availability = pd.to_datetime(availability.reindex(series.index), utc=True)
        if observed_availability.isna().any():
            raise ValueError("Availability must cover every forecast-series timestamp")

    values = series.to_numpy(dtype=np.float64)
    rows: list[dict[str, float | pd.Timestamp]] = []
    latency = pd.Timedelta(seconds=spec.inference_latency_seconds)
    for origin in range(spec.min_history - 1, len(series), spec.stride):
        start = max(0, origin + 1 - spec.context_length)
        history = values[start : origin + 1]
        if not np.isfinite(history).all():
            continue
        forecast = forecaster.predict(history, spec.horizon)
        point = np.asarray(forecast.point, dtype=float)
        if point.shape != (spec.horizon,):
            raise RuntimeError(f"Unexpected point forecast shape {point.shape}")
        row: dict[str, float | pd.Timestamp] = {
            "timestamp": pd.Timestamp(series.index[origin]),
            f"{spec.prefix}_point_1": float(point[0]),
            f"{spec.prefix}_point_last": float(point[-1]),
            f"{spec.prefix}_point_sum": float(point.sum()),
        }
        if observed_availability is not None:
            row["available_at"] = pd.Timestamp(observed_availability.iloc[origin]) + latency
        for level, values_at_level in sorted(forecast.quantiles.items()):
            quantile = np.asarray(values_at_level, dtype=float)
            if quantile.shape != (spec.horizon,):
                raise RuntimeError(f"Unexpected quantile forecast shape {quantile.shape}")
            label = str(level).replace(".", "p")
            row[f"{spec.prefix}_q{label}_1"] = float(quantile[0])
            row[f"{spec.prefix}_q{label}_last"] = float(quantile[-1])
            row[f"{spec.prefix}_q{label}_sum"] = float(quantile.sum())
        rows.append(row)
    if not rows:
        raise ValueError("No rolling forecasts were generated")
    return pd.DataFrame(rows).set_index("timestamp").sort_index()


def _canonical_feature_bytes(frame: pd.DataFrame) -> bytes:
    ordered = frame.copy()
    ordered.index.name = "timestamp"
    return ordered.to_csv(
        date_format="%Y-%m-%dT%H:%M:%S.%f%z",
        float_format="%.12g",
        lineterminator="\n",
    ).encode()


def _cache_identity_payload(
    *,
    dataset_sha256: str,
    model_id: str,
    model_revision: str | None,
    spec: RollingForecastSpec | dict[str, object],
    feature_sha256: str,
    row_count: int,
    columns: tuple[str, ...],
) -> dict[str, object]:
    return {
        "schema_version": "1.2",
        "dataset_sha256": dataset_sha256,
        "model_id": model_id,
        "model_revision": model_revision,
        "spec": asdict(spec) if isinstance(spec, RollingForecastSpec) else spec,
        "feature_sha256": feature_sha256,
        "row_count": row_count,
        "columns": columns,
    }


def cache_rolling_features(
    frame: pd.DataFrame,
    output_dir: str | Path,
    *,
    dataset_sha256: str,
    model_id: str,
    model_revision: str | None,
    spec: RollingForecastSpec,
) -> str:
    if frame.empty:
        raise ValueError("Feature cache cannot be empty")
    if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise ValueError("Feature cache index must be unique and sorted")
    if frame.columns.duplicated().any():
        raise ValueError("Feature cache columns must be unique")
    if "available_at" in frame:
        available = pd.to_datetime(frame["available_at"], utc=True, errors="coerce")
        origins = pd.to_datetime(frame.index, utc=True, errors="coerce")
        if available.isna().any() or np.asarray(pd.isna(origins), dtype=bool).any():
            raise ValueError("Feature cache contains invalid timestamps")
        if (available.to_numpy() < origins.to_numpy()).any():
            raise ValueError("Forecast features cannot be available before their origin")

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    data_path = root / "features.csv.gz"
    manifest_path = root / "manifest.json"
    csv_payload = _canonical_feature_bytes(frame)
    feature_sha = hashlib.sha256(csv_payload).hexdigest()
    columns = tuple(str(column) for column in frame.columns)
    identity_payload = _cache_identity_payload(
        dataset_sha256=dataset_sha256,
        model_id=model_id,
        model_revision=model_revision,
        spec=spec,
        feature_sha256=feature_sha,
        row_count=len(frame),
        columns=columns,
    )
    identity = RollingFeatureManifest(
        cache_id=canonical_json_sha256(identity_payload),
        dataset_sha256=dataset_sha256,
        model_id=model_id,
        model_revision=model_revision,
        spec=asdict(spec),
        feature_sha256=feature_sha,
        row_count=len(frame),
        columns=columns,
    )

    if data_path.exists() != manifest_path.exists():
        raise FileExistsError("Feature-cache directory contains an incomplete prior write")
    if manifest_path.exists():
        _, existing = read_cached_rolling_features(root)
        if existing == identity:
            return feature_sha
        raise FileExistsError(f"Feature-cache directory already contains {existing.cache_id}")

    data_path.write_bytes(gzip.compress(csv_payload, mtime=0))
    manifest_path.write_text(
        json.dumps(identity.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return feature_sha


def read_cached_rolling_features(
    path: str | Path,
    *,
    expected_dataset_sha256: str | None = None,
) -> tuple[pd.DataFrame, RollingFeatureManifest]:
    """Load and cryptographically verify a foundation-feature cache."""

    root = Path(path)
    manifest = RollingFeatureManifest.model_validate_json(
        (root / "manifest.json").read_text("utf-8")
    )
    if expected_dataset_sha256 is not None and manifest.dataset_sha256 != expected_dataset_sha256:
        raise ValueError("Feature cache was generated from a different dataset snapshot")
    payload = gzip.decompress((root / "features.csv.gz").read_bytes())
    if hashlib.sha256(payload).hexdigest() != manifest.feature_sha256:
        raise ValueError("Feature cache hash does not match its manifest")
    frame = pd.read_csv(io.BytesIO(payload), index_col=0, parse_dates=True)
    frame.index = pd.to_datetime(frame.index, utc=True)
    if "available_at" in frame:
        frame["available_at"] = pd.to_datetime(frame["available_at"], utc=True)
    for column in frame.columns:
        if column != "available_at":
            frame[column] = pd.to_numeric(frame[column], errors="raise").astype(float)
    if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise ValueError("Feature cache index must be unique and sorted")
    if (
        len(frame) != manifest.row_count
        or tuple(str(column) for column in frame.columns) != manifest.columns
    ):
        raise ValueError("Feature cache shape does not match its manifest")
    identity_payload = _cache_identity_payload(
        dataset_sha256=manifest.dataset_sha256,
        model_id=manifest.model_id,
        model_revision=manifest.model_revision,
        spec=manifest.spec,
        feature_sha256=manifest.feature_sha256,
        row_count=manifest.row_count,
        columns=manifest.columns,
    )
    if canonical_json_sha256(identity_payload) != manifest.cache_id:
        raise ValueError("Feature cache identity does not match its manifest")
    if (
        "available_at" in frame
        and (
            pd.to_datetime(frame["available_at"], utc=True).to_numpy()
            < pd.to_datetime(frame.index, utc=True).to_numpy()
        ).any()
    ):
        raise ValueError("Feature cache contains availability before forecast origin")
    return frame, manifest
