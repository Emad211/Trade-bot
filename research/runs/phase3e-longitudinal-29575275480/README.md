# Phase 3E restored longitudinal run evidence

This directory records compact, secret-free evidence from the first independently
audited Phase 3E run that restored a previous successful compact-state artifact.

## Identity

- Workflow run: `29575275480`
- Source commit: `a931137a0509b13818ddff39b90a009150b44503`
- Artifact ID: `8404763802`
- Artifact digest: `sha256:41a4afc354faecd4cbbad2a7ef55e6f00e21d48eb904bf4b0f8d8d5cf0f05ba8`
- Assessment ID: `699688ed9c5ded3b6393558b33bc5ec6eb2703b0bfaf63e4d1514907c60217ee`

## Restoration evidence

The run restored and verified compact state from:

- previous workflow run: `29575162946`;
- previous artifact ID: `8404720372`;
- previous artifact digest:
  `sha256:b93be811eaa753d1da5e0286ebd6d97fc79d215c60ab9acbb8bf53b7379ddf83`.

The full document, semantic and provider-call ledgers passed verification before new
provider calls were allowed.

## Latest-run delta

- previous/total provider calls: 4 / 8;
- new calls: 4;
- successful/failed new calls: 4 / 0;
- maximum attempts: 1;
- latest input/output/total tokens: 2,499 / 374 / 2,873;
- token ceiling: 8,000;
- mean/maximum latency: 4.10 / 6.58 seconds;
- successful/failed sources: 2 / 0;
- new documents: 0;
- new semantic records: 4;
- total documents/semantic records: 20 / 8;
- pending semantic documents: 12;
- duplicate extraction keys called: 0;
- prospective decisions: 0;
- credential-pattern findings: 0.

All top-level and nested checksum inventories were independently verified after the
artifact was downloaded. Raw payloads and provider trace records remain in the
Actions artifact rather than Git history.

## Interpretation

The result validates restoration, hard pre-call budgeting and longitudinal state
continuity. It permits continued data collection only. The 12 pending documents are
intentional deferred work under the per-run budget, not missing data. No predictive,
economic, paper-trading or live-trading claim follows from this result.
