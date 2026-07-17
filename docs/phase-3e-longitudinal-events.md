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

## First restored-state result

Workflow run `29575275480` passed all restoration, budget, quality and security gates.

- current artifact ID: `8404763802`;
- current artifact digest:
  `sha256:41a4afc354faecd4cbbad2a7ef55e6f00e21d48eb904bf4b0f8d8d5cf0f05ba8`;
- assessment ID:
  `699688ed9c5ded3b6393558b33bc5ec6eb2703b0bfaf63e4d1514907c60217ee`;
- restored previous run/artifact: `29575162946` / `8404720372`;
- restored artifact digest:
  `sha256:b93be811eaa753d1da5e0286ebd6d97fc79d215c60ab9acbb8bf53b7379ddf83`;
- previous/total calls: 4 / 8;
- new successful/failed calls: 4 / 0;
- latest token use: 2,873 of 8,000;
- maximum attempts: 1;
- mean/maximum latency: 4.10 / 6.58 seconds;
- source success/failure: 2 / 0;
- new semantic records: 4;
- pending semantic documents: 12;
- duplicate extraction keys called: 0;
- prospective decisions: 0;
- credential-pattern findings: 0.

Independent post-download inspection verified every top-level and nested checksum.
The pending documents are intentional deferred work under the hard per-run budget and
will be recovery candidates in later scheduled runs. Compact evidence is committed
under `research/runs/phase3e-longitudinal-29575275480/`.

## Safety boundary

Phase 3E cannot write a prospective paper decision or construct an order, exposure,
leverage, stop, target, exchange or wallet action. A successful run permits continued
data collection only. Predictive use requires a separately frozen event dataset,
labels, calibration, ablation, economic-value testing and a new Phase 3A robustness
assessment.
