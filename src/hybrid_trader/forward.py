"""Tamper-evident prospective paper-decision ledger."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ForwardDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    recorded_at: datetime
    decision_time: datetime
    symbol: str = Field(min_length=1)
    dataset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    experiment_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    probability: float = Field(ge=0, le=1)
    threshold: float = Field(gt=0, lt=1)
    desired_exposure: float = Field(ge=0, le=1)
    reason_codes: tuple[str, ...] = ()
    previous_record_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @field_validator("recorded_at", "decision_time")
    @classmethod
    def normalize_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Forward-test timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_temporal_contract(self) -> ForwardDecision:
        if self.recorded_at < self.decision_time:
            raise ValueError("recorded_at cannot precede decision_time")
        if len(set(self.reason_codes)) != len(self.reason_codes):
            raise ValueError("reason_codes cannot contain duplicates")
        return self


def _canonical_line(decision: ForwardDecision) -> bytes:
    payload = json.dumps(
        decision.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )
    return (payload + "\n").encode("utf-8")


def record_sha256(decision: ForwardDecision) -> str:
    return hashlib.sha256(_canonical_line(decision)).hexdigest()


def make_forward_decision(
    *,
    decision_time: datetime,
    symbol: str,
    dataset_sha256: str,
    experiment_id: str,
    probability: float,
    threshold: float,
    desired_exposure: float,
    reason_codes: tuple[str, ...] = (),
    previous_record_sha256: str | None = None,
    recorded_at: datetime | None = None,
) -> ForwardDecision:
    now = recorded_at or datetime.now(UTC)
    return ForwardDecision(
        recorded_at=now,
        decision_time=decision_time,
        symbol=symbol,
        dataset_sha256=dataset_sha256,
        experiment_id=experiment_id,
        probability=probability,
        threshold=threshold,
        desired_exposure=desired_exposure,
        reason_codes=reason_codes,
        previous_record_sha256=previous_record_sha256,
    )


def verify_forward_ledger(
    path: str | Path,
) -> tuple[str | None, ForwardDecision | None, int]:
    ledger = Path(path)
    if not ledger.exists():
        return None, None, 0
    previous_sha: str | None = None
    previous_decision: ForwardDecision | None = None
    count = 0
    with ledger.open("rb") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if not raw.endswith(b"\n"):
                raise ValueError(f"Forward ledger line {line_number} is not newline-terminated")
            try:
                decision = ForwardDecision.model_validate_json(raw)
            except Exception as exc:
                raise ValueError(f"Invalid forward ledger line {line_number}") from exc
            if decision.previous_record_sha256 != previous_sha:
                raise ValueError(f"Forward ledger hash chain breaks at line {line_number}")
            if previous_decision is not None:
                if decision.decision_time <= previous_decision.decision_time:
                    raise ValueError("Forward decision times must increase strictly")
                if decision.recorded_at < previous_decision.recorded_at:
                    raise ValueError("Forward recording times cannot move backward")
            previous_sha = record_sha256(decision)
            previous_decision = decision
            count += 1
    return previous_sha, previous_decision, count


def ledger_head(path: str | Path) -> tuple[str | None, ForwardDecision | None]:
    head, decision, _ = verify_forward_ledger(path)
    return head, decision


def append_forward_decision(path: str | Path, decision: ForwardDecision) -> str:
    ledger = Path(path)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    head, previous = ledger_head(ledger)
    if decision.previous_record_sha256 != head:
        raise ValueError("Decision previous hash does not match the current ledger head")
    if previous is not None and decision.decision_time <= previous.decision_time:
        raise ValueError("Decision time must be later than the current ledger head")
    payload = _canonical_line(decision)
    descriptor = os.open(ledger, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return hashlib.sha256(payload).hexdigest()
