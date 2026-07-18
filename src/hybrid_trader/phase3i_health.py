"""Source-health and semantic backlog reconciliation for Phase 3I."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hybrid_trader.avalai import AvalAICallRecord, verify_avalai_call_ledger
from hybrid_trader.avalai_capture import AvalAIProviderRunManifest
from hybrid_trader.event_capture_models import EventCaptureManifest, SourceCaptureAttempt
from hybrid_trader.event_capture_state import canonical_sha256
from hybrid_trader.event_ledger import load_document_index, verify_document_ledger
from hybrid_trader.semantic_extraction import SemanticEventRecord, verify_semantic_ledger


class Phase3ISourceHealthPolicy(BaseModel):
    """Frozen minimum diversity and source-integrity requirements."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    minimum_document_sources: int = Field(default=4, ge=1)
    minimum_semantic_sources: int = Field(default=4, ge=1)
    minimum_semantic_assets: int = Field(default=3, ge=1)
    maximum_failed_required_sources: int = Field(default=0, ge=0)
    maximum_failed_optional_sources: int = Field(default=2, ge=0)
    allow_source_metadata_drift: bool = False
    allow_zero_accepted_source_calls: bool = False


class Phase3ISourceHealthRecord(BaseModel):
    """Reconciled lifetime and latest-capture state for one source."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    latest_status: Literal["success", "failed", "not_observed"]
    latest_required: bool | None = None
    latest_parsed_documents: int = Field(ge=0)
    latest_relevance_accepted_documents: int = Field(ge=0)
    latest_relevance_rejected_documents: int = Field(ge=0)
    document_count: int = Field(ge=0)
    semantic_record_count: int = Field(ge=0)
    pending_semantic_document_count: int = Field(ge=0)
    successful_provider_call_count: int = Field(ge=0)
    failed_provider_call_count: int = Field(ge=0)
    semantic_assets: tuple[str, ...]
    source_metadata_variant_count: int = Field(ge=0)
    source_quality_values: tuple[float, ...]
    asset_tag_variants: tuple[tuple[str, ...], ...]

    @model_validator(mode="after")
    def validate_counts(self) -> Phase3ISourceHealthRecord:
        if self.semantic_record_count + self.pending_semantic_document_count != self.document_count:
            raise ValueError("Source document, semantic, and pending counts do not reconcile")
        if self.source_metadata_variant_count != len(
            set(zip(self.source_quality_values, self.asset_tag_variants, strict=True))
        ):
            raise ValueError("Source metadata variant count does not reconcile")
        return self


class Phase3ISourceHealthAssessment(BaseModel):
    """Machine-readable source-health verdict for one selected semantic state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    assessment_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: Literal["pass", "fail"]
    recommended_action: Literal["continue_maturity_monitoring", "halt_and_review"]
    model_fitting_allowed: bool = False
    paper_or_live_trading_allowed: bool = False
    assessed_at: datetime
    policy: Phase3ISourceHealthPolicy
    latest_capture_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    latest_provider_run_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    document_ledger_head_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    semantic_ledger_head_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    call_ledger_head_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    total_document_count: int = Field(ge=0)
    total_semantic_record_count: int = Field(ge=0)
    total_pending_semantic_document_count: int = Field(ge=0)
    total_successful_provider_call_count: int = Field(ge=0)
    total_failed_provider_call_count: int = Field(ge=0)
    document_source_count: int = Field(ge=0)
    semantic_source_count: int = Field(ge=0)
    semantic_assets: tuple[str, ...]
    failed_required_sources: tuple[str, ...]
    failed_optional_sources: tuple[str, ...]
    metadata_drift_sources: tuple[str, ...]
    zero_accepted_sources_called: tuple[str, ...]
    source_records: tuple[Phase3ISourceHealthRecord, ...]
    failure_reasons: tuple[str, ...]

    @field_validator("assessed_at")
    @classmethod
    def normalize_assessed_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Phase 3I health assessment time must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def enforce_safety_and_totals(self) -> Phase3ISourceHealthAssessment:
        if self.model_fitting_allowed or self.paper_or_live_trading_allowed:
            raise ValueError("Phase 3I cannot authorize fitting or trading")
        if sum(record.document_count for record in self.source_records) != self.total_document_count:
            raise ValueError("Phase 3I source document totals do not reconcile")
        if (
            sum(record.semantic_record_count for record in self.source_records)
            != self.total_semantic_record_count
        ):
            raise ValueError("Phase 3I semantic totals do not reconcile")
        if (
            sum(record.pending_semantic_document_count for record in self.source_records)
            != self.total_pending_semantic_document_count
        ):
            raise ValueError("Phase 3I backlog totals do not reconcile")
        if self.assessment_id != canonical_sha256(health_identity_payload(self)):
            raise ValueError("Phase 3I health assessment ID is not self-consistent")
        return self


def health_identity_payload(assessment: Phase3ISourceHealthAssessment) -> dict[str, object]:
    payload = assessment.model_dump(mode="json", exclude={"assessment_id"})
    return {str(key): value for key, value in payload.items()}


def _load_jsonl(path: Path, model: type[BaseModel]) -> tuple[BaseModel, ...]:
    if not path.exists() or path.stat().st_size == 0:
        return ()
    return tuple(
        model.model_validate_json(raw)
        for raw in path.read_bytes().splitlines()
        if raw
    )


def _latest_provider_run(root: Path) -> tuple[EventCaptureManifest, AvalAIProviderRunManifest]:
    runs_root = root / "state" / "avalai_runs"
    if not runs_root.is_dir():
        raise RuntimeError("Semantic state has no provider-run directory")
    runs: list[tuple[EventCaptureManifest, AvalAIProviderRunManifest]] = []
    for run_root in sorted(path for path in runs_root.iterdir() if path.is_dir()):
        provider = AvalAIProviderRunManifest.model_validate_json(
            (run_root / "provider_manifest.json").read_text(encoding="utf-8")
        )
        capture = EventCaptureManifest.model_validate_json(
            (root / provider.capture_manifest_relative_path).read_text(encoding="utf-8")
        )
        runs.append((capture, provider))
    if not runs:
        raise RuntimeError("Semantic state contains no provider run")
    runs.sort(key=lambda item: (item[0].capture_completed_at, item[0].capture_id))
    return runs[-1]


def _attempt_index(attempts: tuple[SourceCaptureAttempt, ...]) -> dict[str, SourceCaptureAttempt]:
    index: dict[str, SourceCaptureAttempt] = {}
    for attempt in attempts:
        if attempt.source_id in index:
            raise ValueError("Latest capture contains duplicate source attempts")
        index[attempt.source_id] = attempt
    return index


def assess_phase3i_source_health(
    root: str | Path,
    *,
    assessed_at: datetime,
    policy: Phase3ISourceHealthPolicy | None = None,
) -> Phase3ISourceHealthAssessment:
    """Verify ledgers and reconcile source health, backlog, calls, and metadata."""

    capture_root = Path(root)
    declared = policy or Phase3ISourceHealthPolicy()
    document_head, _, document_count, _ = verify_document_ledger(
        capture_root / "state" / "documents.jsonl"
    )
    semantic_state = verify_semantic_ledger(capture_root / "state" / "semantic_events.jsonl")
    call_state = verify_avalai_call_ledger(capture_root / "state" / "avalai_calls.jsonl")
    documents = load_document_index(capture_root / "state" / "documents.jsonl")
    semantic_records = tuple(
        record
        for record in _load_jsonl(
            capture_root / "state" / "semantic_events.jsonl",
            SemanticEventRecord,
        )
        if isinstance(record, SemanticEventRecord)
    )
    call_records = tuple(
        record
        for record in _load_jsonl(
            capture_root / "state" / "avalai_calls.jsonl",
            AvalAICallRecord,
        )
        if isinstance(record, AvalAICallRecord)
    )
    if len(documents) != document_count or len(semantic_records) != semantic_state.count:
        raise RuntimeError("Semantic state changed while Phase 3I loaded it")
    if len(call_records) != call_state.count:
        raise RuntimeError("Provider call state changed while Phase 3I loaded it")

    semantic_by_document: dict[str, SemanticEventRecord] = {}
    semantic_by_extraction: dict[str, SemanticEventRecord] = {}
    for record in semantic_records:
        if record.document_id in semantic_by_document:
            raise ValueError("More than one semantic record exists for a document")
        if record.extraction_key in semantic_by_extraction:
            raise ValueError("Semantic state contains duplicate extraction keys")
        document = documents.get(record.document_id)
        if document is None:
            raise ValueError("Semantic record references a missing document")
        if document.source_id != record.source_id:
            raise ValueError("Semantic record source disagrees with its document")
        if document.source_quality != record.document_source_quality:
            raise ValueError("Semantic record source quality disagrees with its document")
        if document.asset_tags != record.document_asset_tags:
            raise ValueError("Semantic record asset tags disagree with its document")
        semantic_by_document[record.document_id] = record
        semantic_by_extraction[record.extraction_key] = record

    successful_calls: dict[str, AvalAICallRecord] = {}
    failed_calls: dict[str, AvalAICallRecord] = {}
    for record in call_records:
        destination = successful_calls if record.status == "success" else failed_calls
        if record.extraction_key in destination:
            raise ValueError("Provider ledger contains duplicate call status for an extraction")
        destination[record.extraction_key] = record
    for extraction_key in successful_calls:
        if extraction_key not in semantic_by_extraction:
            raise ValueError("Successful provider call has no semantic record")

    latest_capture, latest_provider = _latest_provider_run(capture_root)
    attempt_by_source = _attempt_index(latest_capture.source_attempts)
    call_by_id = {record.call_id: record for record in call_records}
    latest_call_sources: set[str] = set()
    for call_id in latest_provider.new_call_ids:
        call = call_by_id.get(call_id)
        if call is None:
            raise ValueError("Latest provider manifest references a missing call")
        semantic = semantic_by_extraction.get(call.extraction_key)
        if semantic is not None:
            latest_call_sources.add(semantic.source_id)

    documents_by_source: dict[str, list[object]] = defaultdict(list)
    for document in documents.values():
        documents_by_source[document.source_id].append(document)
    semantics_by_source: dict[str, list[SemanticEventRecord]] = defaultdict(list)
    for record in semantic_records:
        semantics_by_source[record.source_id].append(record)
    successful_calls_by_source: Counter[str] = Counter()
    failed_calls_by_source: Counter[str] = Counter()
    for extraction_key in successful_calls:
        semantic = semantic_by_extraction[extraction_key]
        successful_calls_by_source[semantic.source_id] += 1
    for extraction_key in failed_calls:
        semantic = semantic_by_extraction.get(extraction_key)
        if semantic is not None:
            failed_calls_by_source[semantic.source_id] += 1

    source_ids = sorted(
        set(documents_by_source).union(semantics_by_source).union(attempt_by_source)
    )
    source_records: list[Phase3ISourceHealthRecord] = []
    metadata_drift_sources: list[str] = []
    failed_required_sources: list[str] = []
    failed_optional_sources: list[str] = []
    zero_accepted_sources_called: list[str] = []

    for source_id in source_ids:
        source_documents = documents_by_source.get(source_id, [])
        source_semantics = semantics_by_source.get(source_id, [])
        semantic_document_ids = {record.document_id for record in source_semantics}
        pending = sum(
            document.document_id not in semantic_document_ids for document in source_documents
        )
        variants = sorted(
            {
                (float(document.source_quality), tuple(document.asset_tags))
                for document in source_documents
            }
        )
        if len(variants) > 1:
            metadata_drift_sources.append(source_id)
        attempt = attempt_by_source.get(source_id)
        if attempt is None:
            latest_status: Literal["success", "failed", "not_observed"] = "not_observed"
            latest_required: bool | None = None
            parsed = accepted = rejected = 0
        else:
            latest_status = attempt.status
            latest_required = attempt.required
            parsed = attempt.parsed_documents
            accepted = attempt.relevance_accepted_documents
            rejected = attempt.relevance_rejected_documents
            if attempt.status == "failed":
                (failed_required_sources if attempt.required else failed_optional_sources).append(
                    source_id
                )
            if accepted == 0 and source_id in latest_call_sources:
                zero_accepted_sources_called.append(source_id)
        assets = tuple(sorted({record.signal.asset for record in source_semantics}))
        source_records.append(
            Phase3ISourceHealthRecord(
                source_id=source_id,
                latest_status=latest_status,
                latest_required=latest_required,
                latest_parsed_documents=parsed,
                latest_relevance_accepted_documents=accepted,
                latest_relevance_rejected_documents=rejected,
                document_count=len(source_documents),
                semantic_record_count=len(source_semantics),
                pending_semantic_document_count=pending,
                successful_provider_call_count=successful_calls_by_source[source_id],
                failed_provider_call_count=failed_calls_by_source[source_id],
                semantic_assets=assets,
                source_metadata_variant_count=len(variants),
                source_quality_values=tuple(variant[0] for variant in variants),
                asset_tag_variants=tuple(variant[1] for variant in variants),
            )
        )

    semantic_sources = {record.source_id for record in semantic_records}
    semantic_assets = tuple(sorted({record.signal.asset for record in semantic_records}))
    reasons: list[str] = []
    if len(documents_by_source) < declared.minimum_document_sources:
        reasons.append("insufficient_document_source_diversity")
    if len(semantic_sources) < declared.minimum_semantic_sources:
        reasons.append("insufficient_semantic_source_diversity")
    if len(semantic_assets) < declared.minimum_semantic_assets:
        reasons.append("insufficient_semantic_asset_diversity")
    if len(failed_required_sources) > declared.maximum_failed_required_sources:
        reasons.append("required_source_failure_budget_exceeded")
    if len(failed_optional_sources) > declared.maximum_failed_optional_sources:
        reasons.append("optional_source_failure_budget_exceeded")
    if metadata_drift_sources and not declared.allow_source_metadata_drift:
        reasons.append("source_metadata_drift_detected")
    if zero_accepted_sources_called and not declared.allow_zero_accepted_source_calls:
        reasons.append("zero_accepted_source_received_provider_call")

    status: Literal["pass", "fail"] = "pass" if not reasons else "fail"
    assessment = Phase3ISourceHealthAssessment.model_construct(
        assessment_id="0" * 64,
        schema_version="1.0",
        status=status,
        recommended_action=(
            "continue_maturity_monitoring" if status == "pass" else "halt_and_review"
        ),
        model_fitting_allowed=False,
        paper_or_live_trading_allowed=False,
        assessed_at=assessed_at,
        policy=declared,
        latest_capture_id=latest_capture.capture_id,
        latest_provider_run_id=latest_provider.provider_run_id,
        document_ledger_head_sha256=document_head,
        semantic_ledger_head_sha256=semantic_state.head_sha256,
        call_ledger_head_sha256=call_state.head_sha256,
        total_document_count=len(documents),
        total_semantic_record_count=len(semantic_records),
        total_pending_semantic_document_count=len(documents) - len(semantic_records),
        total_successful_provider_call_count=sum(successful_calls_by_source.values()),
        total_failed_provider_call_count=len(failed_calls),
        document_source_count=len(documents_by_source),
        semantic_source_count=len(semantic_sources),
        semantic_assets=semantic_assets,
        failed_required_sources=tuple(sorted(failed_required_sources)),
        failed_optional_sources=tuple(sorted(failed_optional_sources)),
        metadata_drift_sources=tuple(sorted(metadata_drift_sources)),
        zero_accepted_sources_called=tuple(sorted(zero_accepted_sources_called)),
        source_records=tuple(source_records),
        failure_reasons=tuple(reasons),
    )
    payload = assessment.model_dump(mode="json")
    payload["assessment_id"] = canonical_sha256(health_identity_payload(assessment))
    return Phase3ISourceHealthAssessment.model_validate(payload)


def write_phase3i_source_health(
    assessment: Phase3ISourceHealthAssessment,
    path: str | Path,
) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(assessment.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return output
