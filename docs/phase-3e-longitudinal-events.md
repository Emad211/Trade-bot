# Phase 3E — longitudinal prospective AvalAI collection

## Purpose

Phase 3E carries the prospective document, semantic and provider-call ledgers across
scheduled runs while imposing a hard extraction budget before any new AvalAI call.
It measures collection reliability and data coverage only. It is not a predictive or
trading experiment.

## State restoration

The workflow searches for the most recent successful `phase3e-longitudinal-events`
run and downloads its digest-addressed artifact. Only the compact `state/` directory
is restored; raw feed payloads from older runs are not copied forward.

Before a new capture, the restored state must pass the complete Phase 3C verifier:

- document, semantic and provider-call hash chains;
- provider/capture manifest linkage;
- provider-run checksum inventories;
- extraction-key consistency;
- secret-pattern scan;
- empty prospective decision ledger.

The new run records the previous workflow run ID, artifact ID, artifact digest and
whether restoration succeeded in `phase3e_run_context.json`. If a previous run is
declared but state was not verified and restored, the assessment fails closed.

## Hard pre-call budget

`capture_events` accepts `maximum_new_semantic_records`. All newly observed documents
are appended to the document ledger, but only the first deterministic N missing
extraction keys are passed to the semantic provider. Remaining documents stay in the
ledger and become recovery candidates in a later run.

The ordering is deterministic:

```text
retrieved_at → source_id → document_id
```

This is a true pre-call limit, not merely a warning after cost has already been
incurred.

## Latest-run assessment

`hybrid_trader.phase3e` verifies the complete longitudinal state, then assesses only
the newest provider-run delta. It enforces:

- maximum new calls per run;
- maximum actual token use per run;
- maximum failed calls and retry attempts;
- minimum successful source coverage;
- one semantic record per successful new provider call;
- no repeated extraction key from prior call-ledger state;
- valid restoration context;
- empty prospective decision ledger;
- no credential-shaped material in compact state.

It also reports new and total document/semantic/call counts, pending documents,
latency and token use.

## Workflow cadence

The final workflow supports manual execution and a conservative weekly schedule on
Monday at 06:17 UTC. Each run allows at most four new semantic extractions and 8,000
actual tokens. The provider remains pinned to `gpt-5-mini-2025-08-07`.

Artifacts contain the complete current compact state plus only the current run's raw
feed payloads. Git stores source code and compact reviewed evidence, not longitudinal
raw payload archives.

## Safety boundary

Phase 3E cannot write a prospective paper decision or construct an order, exposure,
leverage, stop, target, exchange or wallet action. A successful run permits continued
data collection only. Predictive use requires a separately frozen event dataset,
labels, calibration, ablation, economic-value testing and a new Phase 3A robustness
assessment.
