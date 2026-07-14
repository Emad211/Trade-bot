"""Typed Phase 2C experiment contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SpotVenueSpec(StrictModel):
    exchange_id: str
    symbol: str = "BTC/USD"
    required: bool = False
    exchange_options: dict[str, Any] = Field(default_factory=dict)


class DerivativeVenueSpec(StrictModel):
    exchange_id: str
    symbol: str
    exchange_options: dict[str, Any] = Field(default_factory=dict)


class FredSeriesSpec(StrictModel):
    series_id: str
    feature_name: str
    required: bool = False
    release_lag_hours: float = Field(default=24, ge=0)
    source_latency_seconds: float = Field(default=300, ge=0)
    tolerance_days: float = Field(default=10, gt=0)
    revision_policy: Literal["market_price_latest_vintage"] = "market_price_latest_vintage"


class StooqSeriesSpec(StrictModel):
    symbol: str
    feature_name: str
    required: bool = False
    release_lag_hours: float = Field(default=24, ge=0)
    source_latency_seconds: float = Field(default=300, ge=0)
    tolerance_days: float = Field(default=10, gt=0)
    revision_policy: Literal["market_price_latest_vintage"] = "market_price_latest_vintage"


class Phase2CSpec(StrictModel):
    schema_version: str = "1.0"
    timeframe: str = "4h"
    start: datetime
    end: datetime
    as_of: datetime
    spot_required_count: int = Field(default=2, ge=2)
    spot_sources: tuple[SpotVenueSpec, ...]
    derivative_sources: tuple[DerivativeVenueSpec, ...] = ()
    minimum_derivative_features: int = Field(default=1, ge=0, le=3)
    fred_series: tuple[FredSeriesSpec, ...] = ()
    stooq_series: tuple[StooqSeriesSpec, ...] = ()
    source_latency_seconds: float = Field(default=30, ge=0)
    derivative_latency_seconds: float = Field(default=60, ge=0)
    page_limit: int = Field(default=1000, ge=50, le=2000)
    max_pages: int = Field(default=100, ge=1, le=500)
    cross_venue_tolerance_hours: float = Field(default=8, gt=0)

    @field_validator("start", "end", "as_of")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Phase 2C timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_contract(self) -> Phase2CSpec:
        if not self.start < self.end <= self.as_of:
            raise ValueError("Phase 2C requires start < end <= as_of")
        if len(self.spot_sources) < self.spot_required_count:
            raise ValueError("spot_sources cannot satisfy spot_required_count")
        ids = [item.exchange_id for item in self.spot_sources]
        if len(ids) != len(set(ids)):
            raise ValueError("Spot exchange IDs must be unique")
        return self


class SourceAttempt(StrictModel):
    source_id: str
    source_type: str
    provider: str
    instrument: str
    status: Literal["success", "failure"]
    required: bool
    retrieved_at: datetime
    observation_cutoff: datetime
    availability_policy: str
    revision_policy: str
    latency_seconds: float = Field(ge=0)
    row_count: int = Field(default=0, ge=0)
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    payload_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    event_start: datetime | None = None
    event_end: datetime | None = None
    availability_start: datetime | None = None
    availability_end: datetime | None = None
    error: str | None = None


class Phase2CRegistry(StrictModel):
    registry_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    created_at: datetime
    observation_cutoff: datetime
    spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    combined_snapshot_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    attempts: tuple[SourceAttempt, ...]


class Phase2CResult(StrictModel):
    output_dir: str
    registry_id: str
    combined_snapshot_sha256: str
    successful_spot_sources: tuple[str, ...]
    successful_derivative_features: tuple[str, ...]
    successful_macro_features: tuple[str, ...]
    experiment_id: str
    report_sha256: str


def load_phase2c_spec(path: str | Path) -> Phase2CSpec:
    with Path(path).open("r", encoding="utf-8") as handle:
        return Phase2CSpec.model_validate(yaml.safe_load(handle) or {})
