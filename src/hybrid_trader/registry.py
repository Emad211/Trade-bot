"""Tamper-evident registry that retains successful, null, blocked and failed experiments."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ExperimentStatus = Literal["completed", "null", "failed", "blocked"]


class ExperimentRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    recorded_at: datetime
    status: ExperimentStatus
    plan_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    experiment_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    dataset_sha256: tuple[str, ...]
    artifact_sha256: dict[str, str]
    summary: dict[str, float | int | str | bool | None]
    notes: str = ""
    previous_record_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @field_validator("recorded_at")
    @classmethod
    def normalize_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Registry timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @field_validator("dataset_sha256")
    @classmethod
    def validate_datasets(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) != len(set(value)):
            raise ValueError("dataset_sha256 values must be unique")
        if any(
            len(item) != 64 or any(char not in "0123456789abcdef" for char in item)
            for item in value
        ):
            raise ValueError("dataset_sha256 values must be lowercase SHA-256 strings")
        return value

    @field_validator("artifact_sha256")
    @classmethod
    def validate_artifacts(cls, value: dict[str, str]) -> dict[str, str]:
        if len(value) != len(set(value)):
            raise ValueError("artifact names must be unique")
        for digest in value.values():
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                raise ValueError("artifact hashes must be lowercase SHA-256 strings")
        return value

    @model_validator(mode="after")
    def validate_status_contract(self) -> ExperimentRecord:
        if self.status in {"completed", "null"}:
            if self.experiment_id is None:
                raise ValueError("completed/null records require experiment_id")
            if not self.dataset_sha256:
                raise ValueError("completed/null records require at least one dataset")
        return self


def _canonical_line(record: ExperimentRecord) -> bytes:
    payload = json.dumps(record.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return (payload + "\n").encode()


def record_sha256(record: ExperimentRecord) -> str:
    return hashlib.sha256(_canonical_line(record)).hexdigest()


def verify_registry(path: str | Path) -> tuple[str | None, ExperimentRecord | None, int]:
    registry = Path(path)
    if not registry.exists():
        return None, None, 0
    previous_sha: str | None = None
    previous: ExperimentRecord | None = None
    count = 0
    with registry.open("rb") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if not raw.endswith(b"\n"):
                raise ValueError(f"Registry line {line_number} is not newline-terminated")
            try:
                record = ExperimentRecord.model_validate_json(raw)
            except Exception as exc:
                raise ValueError(f"Invalid registry line {line_number}") from exc
            if record.previous_record_sha256 != previous_sha:
                raise ValueError(f"Registry hash chain breaks at line {line_number}")
            if previous is not None and record.recorded_at < previous.recorded_at:
                raise ValueError("Registry timestamps cannot move backward")
            previous_sha = record_sha256(record)
            previous = record
            count += 1
    return previous_sha, previous, count


def append_registry_record(path: str | Path, record: ExperimentRecord) -> str:
    registry = Path(path)
    registry.parent.mkdir(parents=True, exist_ok=True)
    head, previous, _ = verify_registry(registry)
    if record.previous_record_sha256 != head:
        raise ValueError("Record previous hash does not match the registry head")
    if previous is not None and record.recorded_at < previous.recorded_at:
        raise ValueError("Registry timestamp cannot precede the current head")
    payload = _canonical_line(record)
    descriptor = os.open(registry, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return hashlib.sha256(payload).hexdigest()


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
