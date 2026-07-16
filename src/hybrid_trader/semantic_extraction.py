"""Provider-neutral semantic extraction with strict provenance and hash chaining."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable
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


class SemanticEventRecord(BaseModel):
    """A semantic feature record that cannot contain execution instructions."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    signal_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    document_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str
    signal: EventSignal
    model_id: str = Field(min_length=1, max_length=200)
    model_revision: str = Field(min_length=1, max_length=200)
    prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
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

    @model_validator(mode="after")
    def validate_timing_and_evidence(self) -> SemanticEventRecord:
        if self.inference_started_at < self.document_available_at:
            raise ValueError("Inference cannot start before the document is available")
        if self.inference_completed_at < self.inference_started_at:
            raise ValueError("Inference completion cannot precede inference start")
        if self.available_at != self.inference_completed_at:
            raise ValueError("Semantic features become available at inference completion")
        if self.document_id not in self.signal.evidence_ids:
            raise ValueError("Semantic signal must cite its source document")
        if self.input_sha256 != self.document_id and len(self.input_sha256) != 64:
            raise ValueError("Invalid semantic input hash")
        return self


def _canonical_identity(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


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
    started = inference_started_at.astimezone(UTC)
    completed = inference_completed_at.astimezone(UTC)
    prompt_sha = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    identity = {
        "document_id": envelope.document.document_id,
        "signal": signal.model_dump(mode="json"),
        "model_id": model_id,
        "model_revision": model_revision,
        "prompt_sha256": prompt_sha,
        "input_sha256": envelope.document.content_sha256,
        "inference_started_at": started.isoformat(),
        "inference_completed_at": completed.isoformat(),
    }
    return SemanticEventRecord(
        signal_id=_canonical_identity(identity),
        document_id=envelope.document.document_id,
        source_id=envelope.document.source_id,
        signal=signal,
        model_id=model_id,
        model_revision=model_revision,
        prompt_sha256=prompt_sha,
        input_sha256=envelope.document.content_sha256,
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

    def extract(
        self,
        envelope: DocumentEnvelope,
        *,
        inference_started_at: datetime | None = None,
        inference_completed_at: datetime | None = None,
    ) -> SemanticEventRecord:
        started = (inference_started_at or datetime.now(UTC)).astimezone(UTC)
        completed = (inference_completed_at or started).astimezone(UTC)
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
    """Adapter for a local or remote JSON-producing model callable.

    The callable receives the immutable prompt and transient document text. Provider
    credentials, retries and transport are intentionally outside this research core.
    """

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
        started = datetime.now(UTC)
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
            inference_completed_at=completed,
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


def verify_semantic_ledger(
    path: str | Path,
) -> tuple[str | None, SemanticEventRecord | None, int, frozenset[str]]:
    ledger = Path(path)
    if not ledger.exists():
        return None, None, 0, frozenset()
    previous_sha: str | None = None
    previous: SemanticEventRecord | None = None
    signal_ids: set[str] = set()
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
            if previous is not None:
                current_key = (record.available_at, record.source_id, record.signal_id)
                previous_key = (previous.available_at, previous.source_id, previous.signal_id)
                if current_key <= previous_key:
                    raise ValueError("Semantic event records must be strictly ordered")
            previous_sha = semantic_record_sha256(record)
            previous = record
            signal_ids.add(record.signal_id)
            count += 1
    return previous_sha, previous, count, frozenset(signal_ids)


def append_semantic_records(
    path: str | Path,
    records: tuple[SemanticEventRecord, ...] | list[SemanticEventRecord],
) -> tuple[int, str | None]:
    ledger = Path(path)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    head, previous, _, existing_ids = verify_semantic_ledger(ledger)
    pending = [record for record in records if record.signal_id not in existing_ids]
    pending.sort(key=lambda item: (item.available_at, item.source_id, item.signal_id))
    if not pending:
        return 0, head

    previous_key = (
        (previous.available_at, previous.source_id, previous.signal_id)
        if previous is not None
        else None
    )
    payloads: list[bytes] = []
    next_head = head
    for item in pending:
        current_key = (item.available_at, item.source_id, item.signal_id)
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
