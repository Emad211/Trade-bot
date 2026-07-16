# Phase 3B — prospective semantic event stream

## Purpose

Phase 3B adds a prospective-only public event layer for later hybrid-model research.
It records when a feed was actually retrieved, preserves tamper-evident metadata and
creates constrained semantic features. It does not make trading decisions.

This phase exists because a publication timestamp is not evidence that the research
system possessed the document at that time. For every raw document:

```text
available_at = retrieved_at
```

For every semantic feature:

```text
available_at = inference_completed_at
```

Published time remains descriptive metadata. It is never used as an earlier feature
availability time.

## Safety boundary

The event pipeline cannot:

- send, cancel or construct an exchange order;
- choose exposure, leverage, a stop, a price target or a wallet action;
- write a prospective paper decision;
- infer availability from an article's claimed publication time;
- accept arbitrary output fields from a semantic model;
- promote a historical result into paper or live trading.

`EventSignal` uses a strict Pydantic schema with `extra="forbid"`. The current
keyword extractor always emits a neutral direction and low confidence. It is a
plumbing baseline, not an alpha model.

## Source contract

Every feed is declared in `configs/phase3b_event_sources.yaml` with:

- a stable source ID;
- an HTTPS feed URL;
- an explicit domain allow-list;
- a bounded payload size and item count;
- source quality and asset tags;
- required or optional status.

Feed URLs reject embedded credentials, localhost and non-global literal IP
addresses. Entry URLs are canonicalized, common tracking parameters are removed and
only allow-listed domains are accepted.

## Persistent state layout

A capture root separates compact state from transient raw payloads:

```text
phase3b-events/
├── state/
│   ├── documents.jsonl
│   ├── semantic_events.jsonl
│   ├── prospective_decisions.jsonl
│   └── captures/<capture_id>/
│       ├── capture_manifest.json
│       ├── source_attempts.json
│       ├── raw_payloads.json
│       └── SHA256SUMS
└── raw/<capture_id>/<source_id>.xml
```

`documents.jsonl` and `semantic_events.jsonl` are append-only SHA-256 hash chains.
The decision ledger is created empty and any non-empty content causes capture to fail
closed. A filesystem lock prevents simultaneous writers.

Raw XML is uploaded as a GitHub Actions artifact and is not intended for Git history.
Compact ledgers, manifests and hashes can be reviewed and committed separately.

## Identity and retry semantics

A document ID is derived from canonical source, URL, title, published metadata and
content hash. Retrieval time is intentionally excluded so a repeated observation is
recognized as the same document.

A semantic extraction key is derived from:

- document ID;
- model ID and immutable revision;
- prompt SHA-256;
- input content SHA-256.

Inference start and completion times are recorded as availability provenance, but do
not change the semantic identity. Re-running the same extraction is therefore
idempotent. A different output for the same extraction key is rejected as a conflict.

If a document is present but its semantic record is missing, a later capture may
recover only that semantic record without duplicating the document.

## Capture command

```bash
python scripts/capture_phase3b_events.py \
  --config configs/phase3b_event_sources.yaml \
  --output artifacts/phase3b-events
```

A failed required source still produces a failure manifest and source-attempt evidence,
but does not append new document or semantic state.

## Research use

No existing Phase 2C or Phase 3A candidate is re-opened by this work. A future model
experiment using these events must declare a new immutable experiment identity,
consume only records available before each decision time, and pass the Phase 3A
robustness gate before any separately reviewed forward-only paper period.
