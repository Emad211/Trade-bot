"""Predeclared Phase 2C experiment and source contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hybrid_trader.data.snapshot import canonical_json_sha256
from hybrid_trader.data.timeframe import timeframe_to_timedelta

RevisionPolicy = Literal["append_only", "revisable", "unknown"]
DatasetKind = Literal[
    "spot_ohlcv",
    "funding",
    "open_interest",
    "basis",
    "macro",
    "local_market",
    "foundation_features",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SourceContract(StrictModel):
    source_id: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9._-]*$")
    dataset_kind: DatasetKind
    provider: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    timeframe: str | None = None
    retrieval_method: str = Field(min_length=1)
    event_time_policy: str = Field(min_length=1)
    availability_time_policy: str = Field(min_length=1)
    source_latency_seconds: float = Field(ge=0)
    revision_policy: RevisionPolicy
    credentials_required: bool = False
    notes: str = ""

    @field_validator("timeframe")
    @classmethod
    def validate_timeframe(cls, value: str | None) -> str | None:
        if value is not None:
            timeframe_to_timedelta(value)
        return value

    @model_validator(mode="after")
    def reject_private_data_contracts(self) -> SourceContract:
        if self.credentials_required:
            raise ValueError("Phase 2C source contracts must use public, credential-free data")
        if self.dataset_kind in {"spot_ohlcv", "open_interest", "basis"} and self.timeframe is None:
            raise ValueError(f"{self.dataset_kind} requires an explicit timeframe")
        return self

    @property
    def contract_sha256(self) -> str:
        return canonical_json_sha256(self.model_dump(mode="json"))


class PromotionGate(StrictModel):
    minimum_test_folds: int = Field(default=3, ge=1)
    minimum_positive_fold_rate: float = Field(default=0.5, ge=0, le=1)
    maximum_fold_concentration: float = Field(default=0.65, gt=0, le=1)
    maximum_drawdown: float = Field(default=-0.25, ge=-1, le=0)
    require_positive_two_x_cost_return: bool = True


class Phase2CSpec(StrictModel):
    schema_version: str = "1.0"
    experiment_name: str = Field(min_length=1)
    as_of: datetime
    since: datetime
    canonical_spot_source: str
    sources: tuple[SourceContract, ...]
    model_matrix: tuple[str, ...]
    large_move_quantile: float = Field(default=0.9, gt=0.5, lt=1)
    gate: PromotionGate = PromotionGate()

    @field_validator("as_of", "since")
    @classmethod
    def normalize_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Phase 2C timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_plan(self) -> Phase2CSpec:
        if self.since >= self.as_of:
            raise ValueError("since must precede as_of")
        source_ids = [source.source_id for source in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("source_id values must be unique")
        spot_sources = [source for source in self.sources if source.dataset_kind == "spot_ohlcv"]
        if len(spot_sources) < 2:
            raise ValueError("Phase 2C requires at least two independent spot sources")
        if self.canonical_spot_source not in {source.source_id for source in spot_sources}:
            raise ValueError("canonical_spot_source must reference a declared spot source")
        if not self.model_matrix or len(self.model_matrix) != len(set(self.model_matrix)):
            raise ValueError("model_matrix must be non-empty and unique")
        return self

    @property
    def plan_sha256(self) -> str:
        return canonical_json_sha256(self.model_dump(mode="json"))


def load_phase2c_spec(path: str | Path) -> Phase2CSpec:
    spec_path = Path(path)
    if not spec_path.exists():
        raise FileNotFoundError(f"Phase 2C specification not found: {spec_path}")
    with spec_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    return Phase2CSpec.model_validate(raw)
