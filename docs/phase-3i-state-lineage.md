# Phase 3I — semantic state lineage and source-health trajectory

## Purpose

Phase 3I prevents the scheduled market/semantic overlap workflow from silently using
an older semantic state after a newer independently verified artifact exists. It also
adds source-health and pending-backlog history without changing the existing Phase 3G
maturity trajectory schema.

This phase is a lineage and data-quality control. It does not fit a model, select a
threshold, create a paper decision, or place an order.

## Workflow-specific discovery

GitHub Actions run discovery is performed through the exact workflow endpoints for:

- `phase3e-longitudinal-events.yml`;
- `phase3h-avalai-pilot.yml`.

The latest successful run from each workflow is paired with its non-expired state
artifact. Raw API results are converted into strict, self-hashing
`SemanticStateCandidate` records.

The selection order is frozen as:

```text
artifact creation time
→ workflow completion time
→ workflow priority for an exact tie
→ numeric workflow run ID
```

Phase 3H has priority over Phase 3E only when the timestamps are exactly equal. An
expired artifact, a duplicate identity, or a state older than an explicit minimum
cutoff is ineligible. The resulting `SemanticStateSelection` records every considered
and rejected candidate and is itself self-hashing.

## State admission

After selection, only the compact `state/` directory is restored. Before it can enter
an overlap run, the complete Phase 3C verifier checks:

- document, semantic, and provider-call hash chains;
- capture/provider manifest linkage;
- nested checksum inventories;
- extraction-key integrity;
- the empty prospective decision ledger;
- absence of credential-shaped material.

The selected workflow name, run ID, artifact ID, artifact digest, source commit, and
selection ID are stored in the Phase 3I artifact.

## Source-health reconciliation

`phase3i_health` derives its counts directly from the verified ledgers. For each
source it records:

- latest capture status and required/optional policy;
- parsed, accepted, and rejected document counts;
- lifetime document and semantic counts;
- pending semantic backlog;
- successful and failed provider-call counts when provenance allows mapping;
- observed semantic assets;
- distinct source-quality and asset-tag metadata variants.

The assessment fails closed for:

- insufficient document, semantic-source, or asset diversity;
- required-source failures beyond the policy;
- excessive optional-source failures;
- source metadata drift across immutable history;
- a provider call from a source with zero accepted documents;
- any ledger or provenance mismatch.

Backlog is reported rather than automatically failed because the hard per-run provider
budget intentionally defers accepted documents. Rejected documents are never counted
as backlog.

## Trajectory design

The existing `maturity_trajectory.jsonl` remains byte-compatible with Phase 3G.
Phase 3I adds a separate append-only `source_health_trajectory.jsonl`.

Each source-health entry binds:

- the exact current Phase 3G trajectory entry and dataset;
- the self-hashing semantic-state selection;
- the selected workflow artifact identity;
- the source-health assessment;
- source and asset diversity;
- total documents, semantic records, and pending backlog;
- failed-source and metadata-drift counts.

The trajectory is self-hashing, strictly time ordered, and rejects duplicate Phase 3G
entries or repeated semantic-state selections.

## Scheduled transition

The old Phase 3G workflow remains available for manual historical reproduction, but
its weekly schedule is retired. `phase3i-diversified-overlap.yml` becomes the single
scheduled overlap path and runs after the longitudinal collection window.

## Safety boundary

A passing Phase 3I result permits continued maturity monitoring only. Even if the
underlying Phase 3G maturity entry eventually reports `mature_for_research`, Phase 3I
itself never authorizes model fitting, paper trading, or live trading. A separate,
predeclared experiment and Phase 3A robustness gate remain mandatory.
