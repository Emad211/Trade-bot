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

## First exact-head result

Workflow run `29646846973` completed successfully on source commit
`1e3071d457173f2f6644f3beeaa04cccc0ae53b5`.

- artifact ID: `8430291832`;
- artifact digest:
  `sha256:d87d626ff69a9f07181a8c029ce29650219ac1a91c2ca56b99dc0b3af3601bb0`;
- semantic-state selection ID:
  `654daecdeae606516b95214b5d2f3a85ad541a7a6365ec6d1b228d0c83a1d13b`;
- source-health assessment ID:
  `4f059fc5e01d082f6bb1c79e42cdfc0446d33dad3fed0b57bd9af52947895dc0`.

The selector considered the newest successful Phase 3E and Phase 3H state artifacts
and selected the later diversified Phase 3H artifact from run `29645401163`, artifact
`8429886030`, with digest
`sha256:ec077f99caadaa28fc3142a9482b4f6160f4a338759692341825719d241fad91`.

The source-health gate passed:

- document sources: 4;
- semantic sources: 4;
- semantic assets: BTC, ETH, and MARKET;
- total documents: 38;
- total semantic records: 12;
- pending accepted documents: 26;
- required/optional source failures: 0 / 0;
- metadata-drift sources: 0;
- zero-accepted sources receiving a call: 0.

The current dataset contained 677 matured labeled rows and 11 relevant semantic
records. Its maturity verdict remained `insufficient_prospective_sample` because the
semantic-record, unique-availability-date, and active-window requirements were not yet
met. Both target classes and the minimum labeled-row count were already present.

Both trajectories advanced and independently verified:

- Phase 3G trajectory count/head: `2` /
  `e8e4cc89e20052b71a20b57c173a32c4e2e7e441feefb31d45f3be2a5d990c1f`;
- Phase 3I trajectory count/head: `2` /
  `93648d9f5fd2c1463767c6c7ef9b899045cc371f2afe678a67793a93dced7c82`.

All 24 artifact checksum records, the canonical dataset hash, semantic-state selection
and source-health hashes, and every Phase 3G/3I trajectory link were independently
verified after artifact download. Compact evidence is committed under
`research/runs/phase3i-overlap-29646846973/`.

## Safety boundary

A passing Phase 3I result permits continued maturity monitoring only. Even if the
underlying Phase 3G maturity entry eventually reports `mature_for_research`, Phase 3I
itself never authorizes model fitting, paper trading, or live trading. A separate,
predeclared experiment and Phase 3A robustness gate remain mandatory.
