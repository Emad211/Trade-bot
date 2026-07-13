"""Auditable schema for future LLM/RAG event extraction."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EventSignal(BaseModel):
    """Constrained output accepted from an event-extraction model."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    asset: str
    event_time_utc: datetime
    event_type: str
    direction: Literal["bullish", "bearish", "neutral"]
    horizon: Literal["intraday", "1d_3d", "1w_plus"]
    severity: float = Field(ge=0, le=1)
    novelty: float = Field(ge=0, le=1)
    source_quality: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    evidence_ids: tuple[str, ...] = ()
