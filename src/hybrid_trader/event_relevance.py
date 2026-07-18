"""Deterministic pre-provider relevance decisions for prospective feed documents."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from hybrid_trader.event_source_spec import FeedRelevanceSpec
from hybrid_trader.prospective_document import DocumentEnvelope

_WHITESPACE = re.compile(r"\s+")
RelevanceReason = Literal[
    "accepted_no_filter",
    "accepted_include_match",
    "accepted_no_include_terms",
    "rejected_excluded_term",
    "rejected_missing_include_term",
]


class RelevanceDecision(BaseModel):
    """Self-hashing decision produced before any semantic-provider call."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    decision_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    document_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str
    policy_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    accepted: bool
    reason: RelevanceReason
    matched_include_terms: tuple[str, ...] = ()
    matched_exclude_terms: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_identity_and_reason(self) -> RelevanceDecision:
        if self.decision_id != relevance_decision_id(self):
            raise ValueError("Relevance decision ID is not self-consistent")
        if self.accepted and self.reason.startswith("rejected_"):
            raise ValueError("Accepted relevance decision has a rejection reason")
        if not self.accepted and self.reason.startswith("accepted_"):
            raise ValueError("Rejected relevance decision has an acceptance reason")
        if self.reason == "rejected_excluded_term" and not self.matched_exclude_terms:
            raise ValueError("Excluded relevance decision must record a matched term")
        return self


def normalize_relevance_text(value: str) -> str:
    """Normalize Unicode, case and whitespace without language-model inference."""

    normalized = unicodedata.normalize("NFKC", value).casefold()
    return _WHITESPACE.sub(" ", normalized).strip()


def relevance_policy_sha256(policy: FeedRelevanceSpec | None) -> str:
    payload = (
        {"schema_version": "1.0", "filter": None}
        if policy is None
        else policy.model_dump(mode="json")
    )
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def relevance_identity_payload(decision: RelevanceDecision) -> dict[str, object]:
    payload = decision.model_dump(mode="json", exclude={"decision_id"})
    return {str(key): value for key, value in payload.items()}


def relevance_decision_id(decision: RelevanceDecision) -> str:
    encoded = json.dumps(
        relevance_identity_payload(decision),
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _decision(
    envelope: DocumentEnvelope,
    *,
    policy_sha256: str,
    accepted: bool,
    reason: RelevanceReason,
    matched_include_terms: tuple[str, ...] = (),
    matched_exclude_terms: tuple[str, ...] = (),
) -> RelevanceDecision:
    candidate = RelevanceDecision.model_construct(
        decision_id="0" * 64,
        document_id=envelope.document.document_id,
        source_id=envelope.document.source_id,
        policy_sha256=policy_sha256,
        accepted=accepted,
        reason=reason,
        matched_include_terms=matched_include_terms,
        matched_exclude_terms=matched_exclude_terms,
    )
    payload = candidate.model_dump(mode="json")
    payload["decision_id"] = relevance_decision_id(candidate)
    return RelevanceDecision.model_validate(payload)


def evaluate_relevance(
    envelope: DocumentEnvelope,
    policy: FeedRelevanceSpec | None,
) -> RelevanceDecision:
    """Evaluate one title/summary before any AvalAI request is constructed."""

    policy_sha = relevance_policy_sha256(policy)
    if policy is None:
        return _decision(
            envelope,
            policy_sha256=policy_sha,
            accepted=True,
            reason="accepted_no_filter",
        )

    searchable = normalize_relevance_text(f"{envelope.document.title}\n{envelope.text}")
    matched_include = tuple(term for term in policy.include_any_terms if term in searchable)
    matched_exclude = tuple(term for term in policy.exclude_any_terms if term in searchable)
    if matched_exclude:
        return _decision(
            envelope,
            policy_sha256=policy_sha,
            accepted=False,
            reason="rejected_excluded_term",
            matched_include_terms=matched_include,
            matched_exclude_terms=matched_exclude,
        )
    if policy.include_any_terms and not matched_include:
        return _decision(
            envelope,
            policy_sha256=policy_sha,
            accepted=False,
            reason="rejected_missing_include_term",
        )
    return _decision(
        envelope,
        policy_sha256=policy_sha,
        accepted=True,
        reason=(
            "accepted_include_match" if policy.include_any_terms else "accepted_no_include_terms"
        ),
        matched_include_terms=matched_include,
    )


def relevance_decisions_sha256(decisions: tuple[RelevanceDecision, ...]) -> str:
    payload = [decision.model_dump(mode="json") for decision in decisions]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()
