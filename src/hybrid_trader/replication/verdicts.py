"""Machine-readable verdicts for empirical replication."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ReplicationStatus(StrEnum):
    PASS = "PASS"
    ARTIFACT_AUDIT_PASS = "ARTIFACT_AUDIT_PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"
    BLOCKED_BY_SOURCE_ACCESS = "BLOCKED_BY_SOURCE_ACCESS"
    PENDING_LICENSE = "PENDING_LICENSE"
    DATA_INVALID = "DATA_INVALID"
    IMPLEMENTATION_READY = "IMPLEMENTATION_READY"


class ReplicationVerdict(BaseModel):
    """A fail-closed result with evidence and limitations."""

    model_config = ConfigDict(extra="forbid")

    experiment_id: str
    status: ReplicationStatus
    exactness_class: str
    reasons: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    source_artifact_ids: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
