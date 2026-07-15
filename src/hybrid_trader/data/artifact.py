"""Immutable content-addressed artifacts for non-OHLCV point-in-time series."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TabularArtifactManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    artifact_id: str
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str
    source_type: str
    instrument: str
    row_count: int = Field(gt=0)
    event_start: datetime
    event_end: datetime
    availability_start: datetime
    availability_end: datetime
    availability_policy: str
    revision_policy: str
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
    def aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Artifact timestamps must be timezone-aware")
        return value.astimezone(UTC)


def _canonical(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(
        index=False,
        date_format="%Y-%m-%dT%H:%M:%S.%f%z",
        float_format="%.12g",
        lineterminator="\n",
    ).encode()


def _gzip(payload: bytes) -> bytes:
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", filename="", mtime=0) as handle:
        handle.write(payload)
    return bytes(buffer.getvalue())


def write_tabular_artifact(
    frame: pd.DataFrame,
    directory: str | Path,
    *,
    source_id: str,
    source_type: str,
    instrument: str,
    availability_policy: str,
    revision_policy: str,
    created_at: datetime,
    notes: str = "",
) -> TabularArtifactManifest:
    if frame.empty or not {"event_time", "available_at"}.issubset(frame):
        raise ValueError("Artifact requires non-empty event_time and available_at columns")
    data = frame.copy()
    data["event_time"] = pd.to_datetime(data.event_time, utc=True, errors="raise")
    data["available_at"] = pd.to_datetime(data.available_at, utc=True, errors="raise")
    data = data.sort_values(["event_time", "available_at"]).reset_index(drop=True)
    if data.event_time.duplicated().any() or (data.available_at < data.event_time).any():
        raise ValueError("Invalid event-time/availability contract")
    stamp = (
        created_at.replace(tzinfo=UTC) if created_at.tzinfo is None else created_at.astimezone(UTC)
    )
    availability_start = pd.Timestamp(data["available_at"].min())
    availability_end = pd.Timestamp(data["available_at"].max())
    if availability_end.to_pydatetime() > stamp:
        raise ValueError("Artifact contains information unavailable at created_at")
    payload = _canonical(data)
    digest = hashlib.sha256(payload).hexdigest()
    artifact_id = source_id.replace("/", "-").replace(":", "-").lower() + f"-{digest[:12]}"
    manifest = TabularArtifactManifest(
        artifact_id=artifact_id,
        content_sha256=digest,
        source_id=source_id,
        source_type=source_type,
        instrument=instrument,
        row_count=len(data),
        event_start=pd.Timestamp(data.event_time.iloc[0]).to_pydatetime(),
        event_end=pd.Timestamp(data.event_time.iloc[-1]).to_pydatetime(),
        availability_start=availability_start.to_pydatetime(),
        availability_end=availability_end.to_pydatetime(),
        availability_policy=availability_policy,
        revision_policy=revision_policy,
        created_at=stamp,
        columns=tuple(str(column) for column in data.columns),
        notes=notes,
    )
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    data_path, manifest_path = root / "data.csv.gz", root / "manifest.json"
    if data_path.exists() != manifest_path.exists():
        raise FileExistsError("Incomplete prior artifact")
    if manifest_path.exists():
        _, existing = read_tabular_artifact(root)
        if existing.content_sha256 == digest:
            return existing
        raise FileExistsError(f"Conflicting artifact {existing.artifact_id}")
    data_path.write_bytes(_gzip(payload))
    manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def read_tabular_artifact(
    directory: str | Path,
) -> tuple[pd.DataFrame, TabularArtifactManifest]:
    root = Path(directory)
    manifest = TabularArtifactManifest.model_validate_json((root / "manifest.json").read_text())
    payload = gzip.decompress((root / "data.csv.gz").read_bytes())
    if hashlib.sha256(payload).hexdigest() != manifest.content_sha256:
        raise ValueError("Artifact hash mismatch")
    data = pd.read_csv(io.BytesIO(payload))
    data["event_time"] = pd.to_datetime(data.event_time, utc=True)
    data["available_at"] = pd.to_datetime(data.available_at, utc=True)
    if len(data) != manifest.row_count or tuple(data.columns) != manifest.columns:
        raise ValueError("Artifact shape mismatch")
    availability_start = pd.Timestamp(data["available_at"].min())
    availability_end = pd.Timestamp(data["available_at"].max())
    checks = {
        "event_start": pd.Timestamp(manifest.event_start) == pd.Timestamp(data["event_time"].min()),
        "event_end": pd.Timestamp(manifest.event_end) == pd.Timestamp(data["event_time"].max()),
        "availability_start": pd.Timestamp(manifest.availability_start) == availability_start,
        "availability_end": pd.Timestamp(manifest.availability_end) == availability_end,
        "created_at": pd.Timestamp(manifest.created_at) >= availability_end,
    }
    failed = sorted(name for name, valid in checks.items() if not valid)
    if failed:
        raise ValueError(f"Artifact manifest does not match data: {failed}")
    return data, manifest
