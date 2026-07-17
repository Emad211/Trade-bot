"""Immutable Phase 3F semantic datasets and prospective maturity gates."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hybrid_trader.data.snapshot import canonical_json_sha256
from hybrid_trader.semantic_extraction import SemanticEventRecord
from hybrid_trader.semantic_features import (
    SemanticFeatureSpec,
    aggregate_semantic_features,
    semantic_feature_columns,
)

_REQUIRED_TARGET_COLUMNS = (
    "decision_time",
    "label_available_at",
    "target_return",
    "target_positive",
)


class SemanticMaturityPolicy(BaseModel):
    """Predeclared minimum prospective sample before any model fitting."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    minimum_semantic_records: int = Field(default=100, ge=1)
    minimum_unique_availability_dates: int = Field(default=30, ge=1)
    minimum_active_decision_rows: int = Field(default=50, ge=1)
    minimum_unique_sources: int = Field(default=2, ge=1)
    minimum_matured_labeled_rows: int = Field(default=500, ge=1)
    require_both_target_classes: bool = True


class SemanticMaturityAssessment(BaseModel):
    """Machine-readable maturity verdict; never a trading promotion verdict."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    assessment_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: Literal["mature_for_research", "insufficient_prospective_sample"]
    research_model_fitting_allowed: bool
    paper_or_live_trading_allowed: bool = False
    policy: SemanticMaturityPolicy
    relevant_semantic_record_count: int = Field(ge=0)
    unique_availability_date_count: int = Field(ge=0)
    unique_source_count: int = Field(ge=0)
    active_decision_row_count: int = Field(ge=0)
    matured_labeled_row_count: int = Field(ge=0)
    positive_target_count: int = Field(ge=0)
    negative_target_count: int = Field(ge=0)
    failure_reasons: tuple[str, ...]

    @model_validator(mode="after")
    def validate_verdict(self) -> SemanticMaturityAssessment:
        expected = self.status == "mature_for_research"
        if self.research_model_fitting_allowed != expected:
            raise ValueError("Maturity status and model-fitting permission disagree")
        if self.paper_or_live_trading_allowed:
            raise ValueError("Phase 3F can never authorize paper or live trading")
        return self


class SemanticDatasetManifest(BaseModel):
    """Immutable identity and provenance for one Phase 3F dataset."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    dataset_id: str = Field(pattern=r"^semantic-[0-9a-f]{12}$")
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    market_snapshot_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    document_ledger_head_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    semantic_ledger_head_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    semantic_record_count: int = Field(ge=0)
    relevant_semantic_record_count: int = Field(ge=0)
    as_of: datetime
    feature_spec: SemanticFeatureSpec
    feature_spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    row_count: int = Field(ge=0)
    candidate_row_count: int = Field(ge=0)
    excluded_unmatured_label_count: int = Field(ge=0)
    market_feature_columns: tuple[str, ...]
    semantic_feature_columns: tuple[str, ...]
    target_columns: tuple[str, ...] = _REQUIRED_TARGET_COLUMNS
    index_start: datetime | None = None
    index_end: datetime | None = None
    decision_start: datetime | None = None
    decision_end: datetime | None = None
    label_availability_end: datetime | None = None
    maturity: SemanticMaturityAssessment
    created_at: datetime

    @field_validator(
        "as_of",
        "index_start",
        "index_end",
        "decision_start",
        "decision_end",
        "label_availability_end",
        "created_at",
    )
    @classmethod
    def normalize_timestamps(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Semantic dataset timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_dataset_counts(self) -> SemanticDatasetManifest:
        if self.row_count > self.candidate_row_count:
            raise ValueError("Semantic dataset rows cannot exceed candidate rows")
        if self.row_count + self.excluded_unmatured_label_count != self.candidate_row_count:
            raise ValueError("Semantic dataset candidate counts do not reconcile")
        if self.maturity.matured_labeled_row_count != self.row_count:
            raise ValueError("Manifest maturity row count disagrees with dataset")
        return self


@dataclass(frozen=True)
class SemanticDatasetBuildResult:
    frame: pd.DataFrame
    market_feature_columns: tuple[str, ...]
    semantic_feature_columns: tuple[str, ...]
    candidate_row_count: int
    excluded_unmatured_label_count: int
    relevant_records: tuple[SemanticEventRecord, ...]


def _utc_timestamp(value: datetime | pd.Timestamp, *, label: str) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError(f"{label} must be timezone-aware")
    return timestamp.tz_convert("UTC")


def _validate_market_frame(
    frame: pd.DataFrame,
    *,
    market_feature_columns: tuple[str, ...],
) -> pd.DataFrame:
    if frame.empty:
        raise ValueError("Semantic dataset market frame cannot be empty")
    required = set(_REQUIRED_TARGET_COLUMNS).union(market_feature_columns)
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Semantic dataset frame missing columns: {sorted(missing)}")
    if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise ValueError("Semantic dataset market index must be unique and sorted")
    if len(set(market_feature_columns)) != len(market_feature_columns):
        raise ValueError("Market feature columns cannot contain duplicates")
    result = frame.copy()
    for column in ("decision_time", "label_available_at"):
        result[column] = pd.to_datetime(result[column], utc=True, errors="coerce")
        if result[column].isna().any():
            raise ValueError(f"{column} contains invalid timestamps")
    if not result["decision_time"].is_monotonic_increasing:
        raise ValueError("decision_time must be sorted")
    if result["decision_time"].duplicated().any():
        raise ValueError("decision_time must be unique")
    numeric_columns = [*market_feature_columns, "target_return", "target_positive"]
    for column in numeric_columns:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    finite_market = np.isfinite(
        result.loc[:, list(market_feature_columns)].to_numpy(dtype=float)
    ).all(axis=1)
    if not finite_market.all():
        raise ValueError("Market features contain non-finite values")
    return result


def _relevant_records(
    records: tuple[SemanticEventRecord, ...] | list[SemanticEventRecord],
    *,
    spec: SemanticFeatureSpec,
    as_of: pd.Timestamp,
) -> tuple[SemanticEventRecord, ...]:
    allowed = frozenset(spec.allowed_assets)
    relevant = tuple(
        record
        for record in records
        if record.signal.asset in allowed and pd.Timestamp(record.available_at) <= as_of
    )
    signal_ids = [record.signal_id for record in relevant]
    extraction_keys = [record.extraction_key for record in relevant]
    if len(signal_ids) != len(set(signal_ids)):
        raise ValueError("Relevant semantic records contain duplicate signal IDs")
    if len(extraction_keys) != len(set(extraction_keys)):
        raise ValueError("Relevant semantic records contain duplicate extraction keys")
    return relevant


def build_semantic_dataset(
    market_frame: pd.DataFrame,
    records: tuple[SemanticEventRecord, ...] | list[SemanticEventRecord],
    *,
    as_of: datetime | pd.Timestamp,
    market_feature_columns: tuple[str, ...] | list[str],
    feature_spec: SemanticFeatureSpec | None = None,
) -> SemanticDatasetBuildResult:
    """Build matured rows with semantic features observable at each decision time."""

    spec = feature_spec or SemanticFeatureSpec()
    market_columns = tuple(market_feature_columns)
    frame = _validate_market_frame(
        market_frame,
        market_feature_columns=market_columns,
    )
    cutoff = _utc_timestamp(as_of, label="as_of")
    candidates = frame.loc[frame["decision_time"] <= cutoff].copy()
    if candidates.empty:
        raise ValueError("No market decision rows are observable by as_of")
    relevant = _relevant_records(tuple(records), spec=spec, as_of=cutoff)
    semantic = aggregate_semantic_features(candidates["decision_time"], relevant, spec)
    semantic_columns = tuple(semantic_feature_columns(spec))
    if tuple(semantic.columns) != semantic_columns:
        raise RuntimeError("Semantic aggregation columns do not match the feature contract")
    candidates = candidates.join(semantic)
    target_ready = (
        candidates["label_available_at"].notna()
        & (candidates["label_available_at"] <= cutoff)
        & candidates["target_return"].notna()
        & candidates["target_positive"].notna()
    )
    matured = candidates.loc[target_ready].copy()
    ordered_columns = [
        "decision_time",
        "label_available_at",
        *market_columns,
        *semantic_columns,
        "target_return",
        "target_positive",
    ]
    matured = matured.loc[:, ordered_columns]
    if not matured.empty:
        numeric_columns = [
            *market_columns,
            *semantic_columns,
            "target_return",
            "target_positive",
        ]
        if not np.isfinite(matured[numeric_columns].to_numpy(dtype=float)).all():
            raise ValueError("Matured semantic dataset contains non-finite numeric values")
    return SemanticDatasetBuildResult(
        frame=matured,
        market_feature_columns=market_columns,
        semantic_feature_columns=semantic_columns,
        candidate_row_count=len(candidates),
        excluded_unmatured_label_count=int((~target_ready).sum()),
        relevant_records=relevant,
    )


def assess_semantic_maturity(
    result: SemanticDatasetBuildResult,
    *,
    policy: SemanticMaturityPolicy | None = None,
) -> SemanticMaturityAssessment:
    """Assess sample maturity before any predictive model is allowed to fit."""

    declared_policy = policy or SemanticMaturityPolicy()
    records = result.relevant_records
    dates = {pd.Timestamp(record.available_at).tz_convert("UTC").date() for record in records}
    sources = {record.source_id for record in records}
    largest_window = max(
        int(column.split("_")[-3][:-1])
        for column in result.semantic_feature_columns
        if column.endswith("_event_count")
    )
    active_column = next(
        column
        for column in result.semantic_feature_columns
        if column.endswith(f"_{largest_window}h_event_count")
    )
    active_rows = int((result.frame[active_column] > 0).sum()) if not result.frame.empty else 0
    target = (
        result.frame["target_positive"].to_numpy(dtype=float)
        if not result.frame.empty
        else np.asarray([], dtype=float)
    )
    positives = int((target == 1.0).sum())
    negatives = int((target == 0.0).sum())

    reasons: list[str] = []
    if len(records) < declared_policy.minimum_semantic_records:
        reasons.append("insufficient_semantic_records")
    if len(dates) < declared_policy.minimum_unique_availability_dates:
        reasons.append("insufficient_unique_availability_dates")
    if active_rows < declared_policy.minimum_active_decision_rows:
        reasons.append("insufficient_active_decision_rows")
    if len(sources) < declared_policy.minimum_unique_sources:
        reasons.append("insufficient_source_diversity")
    if len(result.frame) < declared_policy.minimum_matured_labeled_rows:
        reasons.append("insufficient_matured_labeled_rows")
    if declared_policy.require_both_target_classes and (positives == 0 or negatives == 0):
        reasons.append("target_classes_not_both_observed")

    status: Literal["mature_for_research", "insufficient_prospective_sample"] = (
        "mature_for_research" if not reasons else "insufficient_prospective_sample"
    )
    identity = {
        "policy": declared_policy.model_dump(mode="json"),
        "relevant_signal_ids": [record.signal_id for record in records],
        "row_index": [str(index) for index in result.frame.index],
        "positive_target_count": positives,
        "negative_target_count": negatives,
        "failure_reasons": reasons,
    }
    return SemanticMaturityAssessment(
        assessment_id=canonical_json_sha256(identity),
        status=status,
        research_model_fitting_allowed=status == "mature_for_research",
        policy=declared_policy,
        relevant_semantic_record_count=len(records),
        unique_availability_date_count=len(dates),
        unique_source_count=len(sources),
        active_decision_row_count=active_rows,
        matured_labeled_row_count=len(result.frame),
        positive_target_count=positives,
        negative_target_count=negatives,
        failure_reasons=tuple(reasons),
    )


def _canonical_csv_bytes(frame: pd.DataFrame) -> bytes:
    ordered = frame.copy()
    ordered.index.name = "timestamp"
    return ordered.to_csv(
        date_format="%Y-%m-%dT%H:%M:%S.%f%z",
        float_format="%.12g",
        lineterminator="\n",
    ).encode("utf-8")


def _deterministic_gzip(payload: bytes) -> bytes:
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", filename="", mtime=0) as handle:
        handle.write(payload)
    return buffer.getvalue()


def write_semantic_dataset(
    result: SemanticDatasetBuildResult,
    directory: str | Path,
    *,
    market_snapshot_sha256: str,
    document_ledger_head_sha256: str | None,
    semantic_ledger_head_sha256: str | None,
    semantic_record_count: int,
    as_of: datetime | pd.Timestamp,
    feature_spec: SemanticFeatureSpec,
    source_commit_sha: str,
    maturity_policy: SemanticMaturityPolicy | None = None,
    created_at: datetime | None = None,
) -> SemanticDatasetManifest:
    """Write an immutable content-addressed dataset and strict manifest."""

    cutoff = _utc_timestamp(as_of, label="as_of")
    if not re_full_sha256(market_snapshot_sha256):
        raise ValueError("market_snapshot_sha256 must be a lowercase SHA-256")
    if len(source_commit_sha) != 40 or any(
        character not in "0123456789abcdef" for character in source_commit_sha
    ):
        raise ValueError("source_commit_sha must be a lowercase 40-character Git SHA")
    payload = _canonical_csv_bytes(result.frame)
    digest = hashlib.sha256(payload).hexdigest()
    maturity = assess_semantic_maturity(result, policy=maturity_policy)
    timestamp = created_at or datetime.now(UTC)
    if timestamp.tzinfo is None:
        raise ValueError("created_at must be timezone-aware")
    timestamp = timestamp.astimezone(UTC)
    feature_spec_sha = canonical_json_sha256(feature_spec.model_dump(mode="json"))
    frame = result.frame
    manifest = SemanticDatasetManifest(
        dataset_id=f"semantic-{digest[:12]}",
        content_sha256=digest,
        market_snapshot_sha256=market_snapshot_sha256,
        document_ledger_head_sha256=document_ledger_head_sha256,
        semantic_ledger_head_sha256=semantic_ledger_head_sha256,
        semantic_record_count=semantic_record_count,
        relevant_semantic_record_count=len(result.relevant_records),
        as_of=cutoff.to_pydatetime(),
        feature_spec=feature_spec,
        feature_spec_sha256=feature_spec_sha,
        source_commit_sha=source_commit_sha,
        row_count=len(frame),
        candidate_row_count=result.candidate_row_count,
        excluded_unmatured_label_count=result.excluded_unmatured_label_count,
        market_feature_columns=result.market_feature_columns,
        semantic_feature_columns=result.semantic_feature_columns,
        index_start=(pd.Timestamp(frame.index[0]).to_pydatetime() if len(frame) else None),
        index_end=(pd.Timestamp(frame.index[-1]).to_pydatetime() if len(frame) else None),
        decision_start=(
            pd.Timestamp(frame["decision_time"].iloc[0]).to_pydatetime() if len(frame) else None
        ),
        decision_end=(
            pd.Timestamp(frame["decision_time"].iloc[-1]).to_pydatetime() if len(frame) else None
        ),
        label_availability_end=(
            pd.Timestamp(frame["label_available_at"].max()).to_pydatetime() if len(frame) else None
        ),
        maturity=maturity,
        created_at=timestamp,
    )
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    data_path = root / "data.csv.gz"
    manifest_path = root / "manifest.json"
    maturity_path = root / "maturity.json"
    if any(path.exists() for path in (data_path, manifest_path, maturity_path)):
        if not all(path.exists() for path in (data_path, manifest_path, maturity_path)):
            raise FileExistsError("Semantic dataset directory contains an incomplete write")
        _, existing = read_semantic_dataset(root)
        if existing.content_sha256 == digest and existing == manifest:
            return existing
        raise FileExistsError(f"Semantic dataset directory already contains {existing.dataset_id}")
    data_path.write_bytes(_deterministic_gzip(payload))
    manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    maturity_path.write_text(
        json.dumps(maturity.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def re_full_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def read_semantic_dataset(
    directory: str | Path,
) -> tuple[pd.DataFrame, SemanticDatasetManifest]:
    """Read and fully verify a Phase 3F semantic dataset artifact."""

    root = Path(directory)
    manifest = SemanticDatasetManifest.model_validate_json(
        (root / "manifest.json").read_text(encoding="utf-8")
    )
    maturity = SemanticMaturityAssessment.model_validate_json(
        (root / "maturity.json").read_text(encoding="utf-8")
    )
    if maturity != manifest.maturity:
        raise ValueError("Semantic dataset maturity file disagrees with manifest")
    with gzip.open(root / "data.csv.gz", "rt", encoding="utf-8") as handle:
        frame = pd.read_csv(handle, index_col=0, parse_dates=True)
    frame.index = pd.to_datetime(frame.index, utc=True)
    for column in ("decision_time", "label_available_at"):
        frame[column] = pd.to_datetime(frame[column], utc=True, errors="raise")
    numeric_columns = [
        *manifest.market_feature_columns,
        *manifest.semantic_feature_columns,
        "target_return",
        "target_positive",
    ]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="raise").astype(float)
    if hashlib.sha256(_canonical_csv_bytes(frame)).hexdigest() != manifest.content_sha256:
        raise ValueError("Semantic dataset content hash does not match manifest")
    if tuple(frame.columns) != (
        "decision_time",
        "label_available_at",
        *manifest.market_feature_columns,
        *manifest.semantic_feature_columns,
        "target_return",
        "target_positive",
    ):
        raise ValueError("Semantic dataset columns do not match manifest")
    if len(frame) != manifest.row_count:
        raise ValueError("Semantic dataset row count does not match manifest")
    if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise ValueError("Semantic dataset index must be unique and sorted")
    if len(frame) and (
        (frame["decision_time"] > pd.Timestamp(manifest.as_of)).any()
        or (frame["label_available_at"] > pd.Timestamp(manifest.as_of)).any()
    ):
        raise ValueError("Semantic dataset contains rows unavailable at as_of")
    expected_feature_sha = canonical_json_sha256(manifest.feature_spec.model_dump(mode="json"))
    if expected_feature_sha != manifest.feature_spec_sha256:
        raise ValueError("Semantic feature specification hash does not match manifest")
    return frame, manifest
