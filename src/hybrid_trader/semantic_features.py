"""Point-in-time aggregation of prospective semantic event records."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hybrid_trader.semantic_extraction import (
    SemanticEventRecord,
    SemanticLedgerState,
    verify_semantic_ledger,
)

_DIRECTION_VALUE = {"bearish": -1.0, "neutral": 0.0, "bullish": 1.0}


class SemanticFeatureSpec(BaseModel):
    """Frozen event windows and asset universe for Phase 3F features."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    windows_hours: tuple[int, ...] = (4, 24, 72)
    allowed_assets: tuple[str, ...] = ("BTC", "MARKET")
    prefix: str = Field(default="semantic", pattern=r"^[a-z][a-z0-9_]{1,31}$")

    @field_validator("windows_hours")
    @classmethod
    def validate_windows(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        if not value:
            raise ValueError("At least one semantic window is required")
        if any(window <= 0 for window in value):
            raise ValueError("Semantic windows must be positive")
        if tuple(sorted(set(value))) != value:
            raise ValueError("Semantic windows must be sorted and unique")
        return value

    @field_validator("allowed_assets")
    @classmethod
    def normalize_assets(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(asset.strip().upper() for asset in value)
        if not normalized or any(not asset for asset in normalized):
            raise ValueError("At least one non-empty semantic asset is required")
        if len(set(normalized)) != len(normalized):
            raise ValueError("Semantic assets must be unique")
        return normalized

    @model_validator(mode="after")
    def require_market_or_explicit_asset(self) -> SemanticFeatureSpec:
        if "MARKET" not in self.allowed_assets and len(self.allowed_assets) < 1:
            raise ValueError("Semantic asset policy is empty")
        return self


@dataclass(frozen=True)
class LoadedSemanticLedger:
    records: tuple[SemanticEventRecord, ...]
    state: SemanticLedgerState


def load_semantic_ledger(path: str | Path) -> LoadedSemanticLedger:
    """Verify and load a semantic ledger without weakening its hash-chain rules."""

    ledger = Path(path)
    state = verify_semantic_ledger(ledger)
    if state.count == 0:
        return LoadedSemanticLedger((), state)
    records: list[SemanticEventRecord] = []
    with ledger.open("rb") as handle:
        for raw in handle:
            records.append(SemanticEventRecord.model_validate_json(raw))
    if len(records) != state.count:
        raise RuntimeError("Semantic ledger count changed while it was being read")
    return LoadedSemanticLedger(tuple(records), state)


def _normalize_decision_times(decision_times: pd.Series) -> pd.Series:
    values = pd.to_datetime(decision_times, utc=True, errors="coerce")
    if values.isna().any():
        raise ValueError("Semantic decision times contain invalid timestamps")
    if not values.is_monotonic_increasing:
        raise ValueError("Semantic decision times must be sorted")
    if values.duplicated().any():
        raise ValueError("Semantic decision times must be unique")
    return values


def _records_frame(
    records: Iterable[SemanticEventRecord],
    *,
    allowed_assets: frozenset[str],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    seen_signal_ids: set[str] = set()
    seen_extraction_keys: set[str] = set()
    for record in records:
        if record.signal_id in seen_signal_ids:
            raise ValueError("Duplicate semantic signal ID in feature input")
        if record.extraction_key in seen_extraction_keys:
            raise ValueError("Duplicate semantic extraction key in feature input")
        seen_signal_ids.add(record.signal_id)
        seen_extraction_keys.add(record.extraction_key)
        if record.signal.asset not in allowed_assets:
            continue
        direction = _DIRECTION_VALUE[record.signal.direction]
        weight = (
            record.signal.source_quality
            * record.signal.confidence
            * max(record.signal.severity, 1e-12)
        )
        rows.append(
            {
                "signal_id": record.signal_id,
                "source_id": record.source_id,
                "available_at": pd.Timestamp(record.available_at),
                "direction": direction,
                "weight": float(weight),
                "severity": float(record.signal.severity),
                "novelty": float(record.signal.novelty),
                "confidence": float(record.signal.confidence),
                "source_quality": float(record.signal.source_quality),
            }
        )
    if not rows:
        return pd.DataFrame(
            columns=[
                "signal_id",
                "source_id",
                "available_at",
                "direction",
                "weight",
                "severity",
                "novelty",
                "confidence",
                "source_quality",
            ]
        )
    frame = pd.DataFrame(rows).sort_values(["available_at", "source_id", "signal_id"])
    frame["available_at"] = pd.to_datetime(frame["available_at"], utc=True)
    return frame.reset_index(drop=True)


def _window_features(
    events: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    window_hours: int,
    prefix: str,
) -> dict[str, float]:
    window = pd.Timedelta(hours=window_hours)
    lower = decision_time - window
    selected = events.loc[
        (events["available_at"] > lower) & (events["available_at"] <= decision_time)
    ]
    label = f"{prefix}_{window_hours}h"
    count = len(selected)
    result: dict[str, float] = {
        f"{label}_event_count": float(count),
        f"{label}_bullish_count": 0.0,
        f"{label}_bearish_count": 0.0,
        f"{label}_neutral_count": 0.0,
        f"{label}_direction_balance": 0.0,
        f"{label}_weighted_direction": 0.0,
        f"{label}_severity_mean": 0.0,
        f"{label}_severity_max": 0.0,
        f"{label}_novelty_mean": 0.0,
        f"{label}_novelty_max": 0.0,
        f"{label}_confidence_mean": 0.0,
        f"{label}_source_quality_mean": 0.0,
        f"{label}_unique_source_count": 0.0,
        f"{label}_last_event_age_seconds": float(window.total_seconds()),
    }
    if selected.empty:
        return result
    directions = selected["direction"].to_numpy(dtype=float)
    result[f"{label}_bullish_count"] = float((directions > 0).sum())
    result[f"{label}_bearish_count"] = float((directions < 0).sum())
    result[f"{label}_neutral_count"] = float((directions == 0).sum())
    result[f"{label}_direction_balance"] = float(directions.mean())
    weights = selected["weight"].to_numpy(dtype=float)
    weight_sum = float(weights.sum())
    if weight_sum > 0:
        result[f"{label}_weighted_direction"] = float(
            np.dot(directions, weights) / weight_sum
        )
    for column in ("severity", "novelty"):
        values = selected[column].to_numpy(dtype=float)
        result[f"{label}_{column}_mean"] = float(values.mean())
        result[f"{label}_{column}_max"] = float(values.max())
    result[f"{label}_confidence_mean"] = float(selected["confidence"].mean())
    result[f"{label}_source_quality_mean"] = float(selected["source_quality"].mean())
    result[f"{label}_unique_source_count"] = float(selected["source_id"].nunique())
    last_available = pd.Timestamp(selected["available_at"].iloc[-1])
    age = (decision_time - last_available).total_seconds()
    if age < 0:
        raise AssertionError("Future semantic event entered a decision row")
    result[f"{label}_last_event_age_seconds"] = float(age)
    return result


def aggregate_semantic_features(
    decision_times: pd.Series,
    records: Iterable[SemanticEventRecord],
    spec: SemanticFeatureSpec | None = None,
) -> pd.DataFrame:
    """Aggregate only records observable by each decision time.

    `signal.event_time_utc` is deliberately ignored for feature inclusion. A record
    becomes usable only at `SemanticEventRecord.available_at`, which is inference
    completion under the Phase 3B/3C contracts.
    """

    feature_spec = spec or SemanticFeatureSpec()
    decisions = _normalize_decision_times(decision_times)
    events = _records_frame(
        records,
        allowed_assets=frozenset(feature_spec.allowed_assets),
    )
    rows: list[dict[str, float]] = []
    for decision in decisions:
        decision_time = pd.Timestamp(decision)
        row: dict[str, float] = {}
        for window_hours in feature_spec.windows_hours:
            row.update(
                _window_features(
                    events,
                    decision_time=decision_time,
                    window_hours=window_hours,
                    prefix=feature_spec.prefix,
                )
            )
        rows.append(row)
    output = pd.DataFrame(rows, index=decision_times.index)
    if output.empty:
        columns = semantic_feature_columns(feature_spec)
        return pd.DataFrame(index=decision_times.index, columns=columns, dtype=float)
    if not np.isfinite(output.to_numpy(dtype=float)).all():
        raise ValueError("Semantic feature aggregation produced non-finite values")
    return output.astype(float)


def semantic_feature_columns(spec: SemanticFeatureSpec | None = None) -> list[str]:
    """Return the exact ordered semantic feature contract."""

    feature_spec = spec or SemanticFeatureSpec()
    suffixes = (
        "event_count",
        "bullish_count",
        "bearish_count",
        "neutral_count",
        "direction_balance",
        "weighted_direction",
        "severity_mean",
        "severity_max",
        "novelty_mean",
        "novelty_max",
        "confidence_mean",
        "source_quality_mean",
        "unique_source_count",
        "last_event_age_seconds",
    )
    return [
        f"{feature_spec.prefix}_{window}h_{suffix}"
        for window in feature_spec.windows_hours
        for suffix in suffixes
    ]
