"""Deterministic pre-provider selection for bounded semantic extraction."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import Literal

from hybrid_trader.event_documents import DocumentEnvelope

SemanticSelectionStrategy = Literal["global_order", "source_round_robin"]


def _round_robin(
    envelopes: Sequence[DocumentEnvelope],
    *,
    source_order: Sequence[str],
) -> list[DocumentEnvelope]:
    buckets: dict[str, list[DocumentEnvelope]] = {}
    for envelope in envelopes:
        buckets.setdefault(envelope.document.source_id, []).append(envelope)

    ordered_sources = [source_id for source_id in source_order if source_id in buckets]
    ordered_sources.extend(sorted(set(buckets).difference(ordered_sources)))

    positions = {source_id: 0 for source_id in ordered_sources}
    selected: list[DocumentEnvelope] = []
    remaining = len(envelopes)
    while remaining:
        progressed = False
        for source_id in ordered_sources:
            position = positions[source_id]
            bucket = buckets[source_id]
            if position >= len(bucket):
                continue
            selected.append(bucket[position])
            positions[source_id] = position + 1
            remaining -= 1
            progressed = True
        if not progressed:
            raise RuntimeError("Round-robin semantic selection made no progress")
    return selected


def select_semantic_envelopes(
    envelopes: Iterable[DocumentEnvelope],
    *,
    extraction_key: Callable[[DocumentEnvelope], str],
    existing_extraction_keys: frozenset[str],
    strategy: SemanticSelectionStrategy,
    source_order: Sequence[str],
    maximum_records: int | None,
) -> tuple[DocumentEnvelope, ...]:
    """Select missing semantic work before provider calls.

    The default `global_order` preserves the Phase 3E behavior exactly. The optional
    `source_round_robin` policy interleaves sources while preserving the existing
    deterministic order within each source. Documents rejected by Phase 3H relevance
    filtering never reach this function.
    """

    if maximum_records is not None and maximum_records < 1:
        raise ValueError("maximum_records must be positive")
    candidates = [
        envelope
        for envelope in envelopes
        if extraction_key(envelope) not in existing_extraction_keys
    ]
    if strategy == "global_order":
        ordered = candidates
    elif strategy == "source_round_robin":
        ordered = _round_robin(candidates, source_order=source_order)
    else:
        raise ValueError(f"Unsupported semantic selection strategy: {strategy}")
    if maximum_records is not None:
        ordered = ordered[:maximum_records]
    return tuple(ordered)
