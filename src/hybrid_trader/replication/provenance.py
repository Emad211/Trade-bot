"""Source-access and immutable-artifact provenance contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from hybrid_trader.replication.artifacts import sha256_file


class SourceAccessStatus(StrEnum):
    UNKNOWN = "UNKNOWN"
    METADATA_VERIFIED = "METADATA_VERIFIED"
    API_REACHABLE = "API_REACHABLE"
    RAW_ARTIFACT_ACQUIRED = "RAW_ARTIFACT_ACQUIRED"
    IMMUTABLE_INGESTED = "IMMUTABLE_INGESTED"
    LICENSE_PENDING = "LICENSE_PENDING"
    BLOCKED = "BLOCKED"


class ArtifactProvenance(BaseModel):
    """Evidence that a local file is the declared official immutable artifact."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    official_locator: str
    access_status: SourceAccessStatus
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    byte_count: int | None = Field(default=None, gt=0)
    retrieved_at: datetime | None = None
    license_snapshot_id: str | None = None
    immutable_storage_key: str | None = None

    @model_validator(mode="after")
    def validate_evidence(self) -> "ArtifactProvenance":
        acquired = {
            SourceAccessStatus.RAW_ARTIFACT_ACQUIRED,
            SourceAccessStatus.IMMUTABLE_INGESTED,
        }
        if self.access_status in acquired:
            required = {
                "sha256": self.sha256,
                "byte_count": self.byte_count,
                "retrieved_at": self.retrieved_at,
            }
            missing = [name for name, value in required.items() if value is None]
            if missing:
                raise ValueError(f"Acquired artifacts require {missing}")
        if self.access_status == SourceAccessStatus.IMMUTABLE_INGESTED:
            if not self.license_snapshot_id or not self.immutable_storage_key:
                raise ValueError(
                    "Immutable ingestion requires license_snapshot_id and immutable_storage_key"
                )
        return self

    @property
    def is_immutable_official(self) -> bool:
        return self.access_status == SourceAccessStatus.IMMUTABLE_INGESTED

    def verify_local_file(self, path: str | Path) -> str:
        source = Path(path)
        actual_size = source.stat().st_size
        actual_sha256 = sha256_file(source)
        if self.byte_count is not None and actual_size != self.byte_count:
            raise ValueError(
                f"Artifact byte count mismatch for {self.source_id}: "
                f"expected {self.byte_count}, got {actual_size}"
            )
        if self.sha256 is not None and actual_sha256 != self.sha256:
            raise ValueError(
                f"Artifact SHA-256 mismatch for {self.source_id}: "
                f"expected {self.sha256}, got {actual_sha256}"
            )
        return actual_sha256
