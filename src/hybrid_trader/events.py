"""Auditable schema for constrained semantic event extraction."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class EventSignal(BaseModel):
    """Only structured semantic features; never an order or position instruction."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    asset: str = Field(min_length=1, max_length=32)
    event_time_utc: datetime
    event_type: str = Field(min_length=1, max_length=100)
    direction: Literal["bullish", "bearish", "neutral"]
    horizon: Literal["intraday", "1d_3d", "1w_plus"]
    severity: float = Field(ge=0, le=1)
    novelty: float = Field(ge=0, le=1)
    source_quality: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    evidence_ids: tuple[str, ...] = ()

    @field_validator("event_time_utc")
    @classmethod
    def normalize_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("event_time_utc must be timezone-aware")
        return value.astimezone(UTC)

    @field_validator("asset")
    @classmethod
    def normalize_asset(cls, value: str) -> str:
        return value.strip().upper()

    @model_validator(mode="after")
    def validate_evidence(self) -> EventSignal:
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("evidence_ids cannot contain duplicates")
        return self
