"""Immutable, content-addressed point-in-time dataset snapshots."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator

from hybrid_trader.data.point_in_time import validate_point_in_time_bars


class SnapshotManifest(BaseModel):
    """Metadata required to reproduce and audit a point-in-time dataset."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    dataset_id: str
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source: str
    symbol: str
    timeframe: str
    row_count: int = Field(gt=0)
    event_start: datetime
    event_end: datetime
    availability_start: datetime
    availability_end: datetime
    source_latency_seconds: float = Field(ge=0)
    availability_policy: str = "bar_open_plus_timeframe_plus_source_latency"
    created_at: datetime
    columns: tuple[str, ...]
    notes: str = ""

    @field_validator(
        "event_start",
        "event_end",
        "availability_start",
        "availability_end",
        "created_at",
    )
    @classmethod
    def timestamps_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Snapshot timestamps must be timezone-aware")
        return value.astimezone(UTC)


def _canonical_csv_bytes(frame: pd.DataFrame) -> bytes:
    ordered = frame.copy()
    ordered.index.name = "timestamp"
    text = ordered.to_csv(
        date_format="%Y-%m-%dT%H:%M:%S.%f%z",
        float_format="%.12g",
        lineterminator="\n",
    )
    return text.encode("utf-8")


def frame_sha256(frame: pd.DataFrame) -> str:
    return hashlib.sha256(_canonical_csv_bytes(frame)).hexdigest()


def _deterministic_gzip(payload: bytes) -> bytes:
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", filename="", mtime=0) as handle:
        handle.write(payload)
    return buffer.getvalue()


def write_snapshot(
    frame: pd.DataFrame,
    directory: str | Path,
    *,
    source: str,
    symbol: str,
    timeframe: str,
    source_latency_seconds: float = 0.0,
    notes: str = "",
    created_at: datetime | None = None,
) -> SnapshotManifest:
    """Write an immutable snapshot directory and refuse conflicting rewrites."""

    data = validate_point_in_time_bars(frame, timeframe=timeframe)
    if data.empty:
        raise ValueError("Snapshot cannot be empty")
    digest = frame_sha256(data)
    dataset_id = f"{symbol.replace('/', '-').lower()}-{timeframe}-{digest[:12]}"
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    data_path = root / "data.csv.gz"
    manifest_path = root / "manifest.json"

    timestamp = created_at or datetime.now(UTC)
    timestamp = (
        timestamp.replace(tzinfo=UTC) if timestamp.tzinfo is None else timestamp.astimezone(UTC)
    )
    latest_availability = pd.Timestamp(data["available_at"].iloc[-1]).to_pydatetime()
    if latest_availability > timestamp:
        raise ValueError("Snapshot cannot contain observations unavailable at created_at")
    manifest = SnapshotManifest(
        dataset_id=dataset_id,
        content_sha256=digest,
        source=source,
        symbol=symbol,
        timeframe=timeframe,
        row_count=len(data),
        event_start=data.index[0].to_pydatetime(),
        event_end=data.index[-1].to_pydatetime(),
        availability_start=pd.Timestamp(data["available_at"].iloc[0]).to_pydatetime(),
        availability_end=pd.Timestamp(data["available_at"].iloc[-1]).to_pydatetime(),
        source_latency_seconds=source_latency_seconds,
        created_at=timestamp,
        columns=tuple(str(column) for column in data.columns),
        notes=notes,
    )

    if manifest_path.exists() != data_path.exists():
        raise FileExistsError("Snapshot directory contains an incomplete prior write")
    if manifest_path.exists():
        existing = read_snapshot(root)[1]
        if existing.content_sha256 != digest:
            raise FileExistsError(f"Snapshot directory already contains {existing.dataset_id}")
        return existing

    data_path.write_bytes(_deterministic_gzip(_canonical_csv_bytes(data)))
    manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def read_snapshot(directory: str | Path) -> tuple[pd.DataFrame, SnapshotManifest]:
    root = Path(directory)
    manifest_path = root / "manifest.json"
    data_path = root / "data.csv.gz"
    if not manifest_path.exists() or not data_path.exists():
        raise FileNotFoundError(f"Incomplete snapshot directory: {root}")
    manifest = SnapshotManifest.model_validate_json(manifest_path.read_text("utf-8"))
    with gzip.open(data_path, "rt", encoding="utf-8") as handle:
        data = pd.read_csv(handle)
    required_timestamps = {"timestamp", "open_available_at", "available_at"}
    missing = required_timestamps.difference(data.columns)
    if missing:
        raise ValueError(f"Snapshot data is missing timestamp columns: {sorted(missing)}")
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="raise")
    timestamp_columns = [
        column
        for column in data.columns
        if column in {"open_available_at", "available_at"} or column.endswith("__available_at")
    ]
    for column in timestamp_columns:
        data[column] = pd.to_datetime(data[column], utc=True, errors="raise")
    data = data.set_index("timestamp")
    data = validate_point_in_time_bars(data, timeframe=manifest.timeframe)
    if frame_sha256(data) != manifest.content_sha256:
        raise ValueError("Snapshot data hash does not match manifest")

    expected_dataset_id = (
        f"{manifest.symbol.replace('/', '-').lower()}-{manifest.timeframe}-"
        f"{manifest.content_sha256[:12]}"
    )
    structural_checks = {
        "dataset_id": manifest.dataset_id == expected_dataset_id,
        "row_count": manifest.row_count == len(data),
        "columns": manifest.columns == tuple(str(column) for column in data.columns),
        "event_start": pd.Timestamp(manifest.event_start) == data.index[0],
        "event_end": pd.Timestamp(manifest.event_end) == data.index[-1],
        "availability_start": pd.Timestamp(manifest.availability_start)
        == pd.Timestamp(data["available_at"].iloc[0]),
        "availability_end": pd.Timestamp(manifest.availability_end)
        == pd.Timestamp(data["available_at"].iloc[-1]),
        "created_at": pd.Timestamp(manifest.created_at)
        >= pd.Timestamp(data["available_at"].iloc[-1]),
    }
    failed = sorted(name for name, valid in structural_checks.items() if not valid)
    if failed:
        raise ValueError(f"Snapshot manifest does not match data: {failed}")
    return data, manifest


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(payload).hexdigest()
