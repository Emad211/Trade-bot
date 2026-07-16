"""Provider-neutral semantic extraction with strict provenance and hash chaining."""

from __future__ import annotations

import hashlib
import json
import math
import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hybrid_trader.event_documents import DocumentEnvelope
from hybrid_trader.events import EventSignal

InferenceCallable = Callable[[str, str], dict[str, Any]]

KEYWORD_BASELINE_RULES = """hybrid-trader semantic baseline v1
Classify event type from fixed keywords. Direction is always neutral. Never emit an
order, exposure, leverage, price target, stop, or execution instruction.
"""


def _canonical_identity(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def make_extraction_key(
    *,
    document_id: str,
    model_id: str,
    model_revision: str,
    prompt_sha256: str,
    input_sha256: str,
) -> str:
    return _canonical_identity(
        {
            "document_id": document_id,
            "model_id": model_id,
            "model_revision": model_revision,
            "prompt_sha256": prompt_sha256,
            "input_sha256": input_sha256,
        }
    )


def make_signal_id(*, extraction_key: str, signal: EventSignal) -> str:
    return _canonical_identity(
        {
            "extraction_key": extraction_key,
            "signal": signal.model_dump(mode="json"),
        }
    )


class SemanticEventRecord(BaseModel):
    """A semantic feature record that cannot contain execution instructions."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.1"
    signal_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    extraction_key: str = Field(pattern=r"^[0-9a-f]{64}$")
    document_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{1,63}$")
    signal: EventSignal
    model_id: str = Field(min_length=1, max_length=200)
    model_revision: str = Field(min_length=1, max_length=200)
    prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    document_source_quality: float = Field(ge=0, le=1)
    document_asset_tags: tuple[str, ...] = ()
    document_available_at: datetime
    inference_started_at: datetime
    inference_completed_at: datetime
    available_at: datetime
    previous_record_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @field_validator(
        "document_available_at",
        "inference_started_at",
        "inference_completed_at",
        "available_at",
    )
    @classmethod
    def normalize_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Semantic event timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @field_validator("document_asset_tags")
    @classmethod
    def normalize_asset_tags(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(tag.upper().strip() for tag in value)
        if any(not tag for tag in normalized) or len(set(normalized)) != len(normalized):
            raise ValueError("document_asset_tags must be unique non-empty values")
        return normalized

    @model_validator(mode="after")
    def validate_timing_and_evidence(self) -> SemanticEventRecord:
        if self.inference_started_at < self.document_available_at:
            raise ValueError("Inference cannot start before the document is available")
        if self.inference_completed_at < self.inference_started_at:
            raise ValueError("Inference completion cannot precede inference start")
        if self.available_at != self.inference_completed_at:
            raise ValueError("Semantic features become available at inference completion")
        if self.signal.evidence_ids != (self.document_id,):
            raise ValueError("Single-document extraction must cite exactly its source document")
        if not math.isclose(
            self.signal.source_quality,
            self.document_source_quality,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError("Semantic source_quality must come from the document contract")
        if self.document_asset_tags:
            if self.signal.asset not in self.document_asset_tags:
                raise ValueError("Semantic asset must be one of the document asset tags")
        elif self.signal.asset != "MARKET":
            raise ValueError("Documents without asset tags must use the MARKET asset")
        expected_extraction_key = make_extraction_key(
            document_id=self.document_id,
            model_id=self.model_id,
            model_revision=self.model_revision,
            prompt_sha256=self.prompt_sha256,
            input_sha256=self.input_sha256,
        )
        if self.extraction_key != expected_extraction_key:
            raise ValueError("extraction_key does not match semantic provenance")
        expected_signal_id = make_signal_id(
            extraction_key=self.extraction_key,
            signal=self.signal,
        )
        if self.signal_id != expected_signal_id:
            raise ValueError("signal_id does not match semantic content and provenance")
        return self


def _normalize_inference_time(value: datetime, *, label: str) -> datetime:
    if value.tzinfo is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value.astimezone(UTC)


def make_semantic_record(
    envelope: DocumentEnvelope,
    signal: EventSignal,
    *,
    model_id: str,
    model_revision: str,
    prompt: str,
    inference_started_at: datetime,
    inference_completed_at: datetime,
) -> SemanticEventRecord:
    started = _normalize_inference_time(inference_started_at, label="inference_started_at")
    completed = _normalize_inference_time(inference_completed_at, label="inference_completed_at")
    prompt_sha = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    extraction_key = make_extraction_key(
        document_id=envelope.document.document_id,
        model_id=model_id,
        model_revision=model_revision,
        prompt_sha256=prompt_sha,
        input_sha256=envelope.document.content_sha256,
    )
    return SemanticEventRecord(
        signal_id=make_signal_id(extraction_key=extraction_key, signal=signal),
        extraction_key=extraction_key,
        document_id=envelope.document.document_id,
        source_id=envelope.document.source_id,
        signal=signal,
        model_id=model_id,
        model_revision=model_revision,
        prompt_sha256=prompt_sha,
        input_sha256=envelope.document.content_sha256,
        document_source_quality=envelope.document.source_quality,
        document_asset_tags=envelope.document.asset_tags,
        document_available_at=envelope.document.available_at,
        inference_started_at=started,
        inference_completed_at=completed,
        available_at=completed,
    )


def _event_type_and_severity(text: str) -> tuple[str, float]:
    normalized = text.lower()
    rules = (
        (("exploit", "hack", "vulnerability", "security incident"), "security_incident", 0.85),
        (("rate cut", "rate hike", "interest rate", "central bank", "fomc"), "monetary_policy", 0.65),
        (("sec ", "cftc", "regulat", "enforcement", "approval"), "regulation", 0.60),
        (("release", "version", "upgrade", "hard fork", "soft fork"), "protocol_release", 0.35),
    )
    for keywords, event_type, severity in rules:
        if any(keyword in normalized for keyword in keywords):
            return event_type, severity
    return "general_update", 0.20


class KeywordSemanticExtractor:
    """Deterministic plumbing baseline; not a trading model."""

    model_id = "deterministic-keyword-baseline"
    model_revision = "1.0"
    prompt = KEYWORD_BASELINE_RULES

    @property
    def prompt_sha256(self) -> str:
        return hashlib.sha256(self.prompt.encode("utf-8")).hexdigest()

    def extraction_key(self, envelope: DocumentEnvelope) -> str:
        return make_extraction_key(
            document_id=envelope.document.document_id,
            model_id=self.model_id,
            model_revision=self.model_revision,
            prompt_sha256=self.prompt_sha256,
            input_sha256=envelope.document.content_sha256,
        )

    def extract(
        self,
        envelope: DocumentEnvelope,
        *,
        inference_started_at: datetime | None = None,
        inference_completed_at: datetime | None = None,
    ) -> SemanticEventRecord:
        now = datetime.now(UTC)
        started = (
            _normalize_inference_time(inference_started_at, label="inference_started_at")
            if inference_started_at is not None
            else max(now, envelope.document.available_at)
        )
        completed = (
            _normalize_inference_time(inference_completed_at, label="inference_completed_at")
            if inference_completed_at is not None
            else started
        )
        event_type, severity = _event_type_and_severity(envelope.text)
        signal = EventSignal(
            asset=envelope.document.asset_tags[0] if envelope.document.asset_tags else "MARKET",
            event_time_utc=envelope.document.published_at or envelope.document.retrieved_at,
            event_type=event_type,
            direction="neutral",
            horizon="1d_3d" if severity >= 0.6 else "1w_plus",
            severity=severity,
            novelty=1.0,
            source_quality=envelope.document.source_quality,
            confidence=0.25,
            evidence_ids=(envelope.document.document_id,),
        )
        return make_semantic_record(
            envelope,
            signal,
            model_id=self.model_id,
            model_revision=self.model_revision,
            prompt=self.prompt,
            inference_started_at=started,
            inference_completed_at=completed,
        )


class CallableStructuredExtractor:
    """Adapter for a local or remote JSON-producing model callable."""

    def __init__(
        self,
        *,
        model_id: str,
        model_revision: str,
        prompt: str,
        inference: InferenceCallable,
    ) -> None:
        if not model_id or not model_revision or not prompt:
            raise ValueError("model_id, model_revision and prompt are required")
        self.model_id = model_id
        self.model_revision = model_revision
        self.prompt = prompt
        self.inference = inference

    def extract(self, envelope: DocumentEnvelope) -> SemanticEventRecord:
        started = max(datetime.now(UTC), envelope.document.available_at)
        payload = self.inference(self.prompt, envelope.text)
        completed = datetime.now(UTC)
        signal = EventSignal.model_validate(payload)
        return make_semantic_record(
            envelope,
            signal,
            model_id=self.model_id,
            model_revision=self.model_revision,
            prompt=self.prompt,
            inference_started_at=started,
            inference_completed_at=max(completed, started),
        )


def _canonical_line(record: SemanticEventRecord) -> bytes:
    payload = json.dumps(
        record.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )
    return (payload + "\n").encode("utf-8")


def semantic_record_sha256(record: SemanticEventRecord) -> str:
    return hashlib.sha256(_canonical_line(record)).hexdigest()


@dataclass(frozen=True)
class SemanticLedgerState:
    head_sha256: str | None
    previous_record: SemanticEventRecord | None
    count: int
    signal_ids: frozenset[str]
    extraction_keys: frozenset[str]
    document_ids: frozenset[str]


def verify_semantic_ledger(path: str | Path) -> SemanticLedgerState:
    ledger = Path(path)
    if not ledger.exists():
        return SemanticLedgerState(None, None, 0, frozenset(), frozenset(), frozenset())
    previous_sha: str | None = None
    previous: SemanticEventRecord | None = None
    signal_ids: set[str] = set()
    extraction_keys: set[str] = set()
    document_ids: set[str] = set()
    count = 0
    with ledger.open("rb") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if not raw.endswith(b"\n"):
                raise ValueError(f"Semantic ledger line {line_number} is not newline-terminated")
            try:
                record = SemanticEventRecord.model_validate_json(raw)
            except Exception as exc:
                raise ValueError(f"Invalid semantic ledger line {line_number}") from exc
            if record.previous_record_sha256 != previous_sha:
                raise ValueError(f"Semantic ledger hash chain breaks at line {line_number}")
            if record.signal_id in signal_ids:
                raise ValueError(f"Duplicate semantic signal at line {line_number}")
            if record.extraction_key in extraction_keys:
                raise ValueError(f"Duplicate semantic extraction at line {line_number}")
            if previous is not None:
                current_key = (record.available_at, record.source_id, record.extraction_key)
                previous_key = (previous.available_at, previous.source_id, previous.extraction_key)
                if current_key <= previous_key:
                    raise ValueError("Semantic event records must be strictly ordered")
            previous_sha = semantic_record_sha256(record)
            previous = record
            signal_ids.add(record.signal_id)
            extraction_keys.add(record.extraction_key)
            document_ids.add(record.document_id)
            count += 1
    return SemanticLedgerState(
        previous_sha,
        previous,
        count,
        frozenset(signal_ids),
        frozenset(extraction_keys),
        frozenset(document_ids),
    )


def _load_semantic_by_extraction_key(path: Path) -> dict[str, SemanticEventRecord]:
    state = verify_semantic_ledger(path)
    if state.count == 0:
        return {}
    result: dict[str, SemanticEventRecord] = {}
    with path.open("rb") as handle:
        for raw in handle:
            record = SemanticEventRecord.model_validate_json(raw)
            result[record.extraction_key] = record
    return result


def append_semantic_records(
    path: str | Path,
    records: tuple[SemanticEventRecord, ...] | list[SemanticEventRecord],
) -> tuple[int, str | None]:
    ledger = Path(path)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    state = verify_semantic_ledger(ledger)
    existing = _load_semantic_by_extraction_key(ledger)
    pending: list[SemanticEventRecord] = []
    for record in records:
        stored = existing.get(record.extraction_key)
        if stored is None:
            pending.append(record)
            continue
        if stored.signal_id != record.signal_id:
            raise ValueError(
                "The same document/model/prompt provenance produced conflicting semantic output"
            )
    pending.sort(key=lambda item: (item.available_at, item.source_id, item.extraction_key))
    if not pending:
        return 0, state.head_sha256

    previous_key = (
        (
            state.previous_record.available_at,
            state.previous_record.source_id,
            state.previous_record.extraction_key,
        )
        if state.previous_record is not None
        else None
    )
    payloads: list[bytes] = []
    next_head = state.head_sha256
    for item in pending:
        current_key = (item.available_at, item.source_id, item.extraction_key)
        if previous_key is not None and current_key <= previous_key:
            raise ValueError("New semantic records are not strictly ordered")
        chained = item.model_copy(update={"previous_record_sha256": next_head})
        payload = _canonical_line(chained)
        payloads.append(payload)
        next_head = hashlib.sha256(payload).hexdigest()
        previous_key = current_key

    descriptor = os.open(ledger, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        for payload in payloads:
            os.write(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return len(payloads), next_head
