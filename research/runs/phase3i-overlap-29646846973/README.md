# Phase 3I semantic-state lineage and source-health evidence

This directory records compact, reviewed evidence from the first successful exact-head
Phase 3I overlap run.

## Identity

- Workflow run: `29646846973`
- Source commit: `1e3071d457173f2f6644f3beeaa04cccc0ae53b5`
- Artifact ID: `8430291832`
- Artifact digest: `sha256:d87d626ff69a9f07181a8c029ce29650219ac1a91c2ca56b99dc0b3af3601bb0`
- Semantic-state selection ID: `654daecdeae606516b95214b5d2f3a85ad541a7a6365ec6d1b228d0c83a1d13b`
- Source-health assessment ID: `4f059fc5e01d082f6bb1c79e42cdfc0446d33dad3fed0b57bd9af52947895dc0`

## State lineage

The deterministic selector considered the newest successful Phase 3E and Phase 3H
artifacts and selected the later diversified Phase 3H state:

- selected workflow: `phase3h-avalai-pilot`;
- selected run: `29645401163`;
- selected artifact: `8429886030`;
- selected digest: `sha256:ec077f99caadaa28fc3142a9482b4f6160f4a338759692341825719d241fad91`.

The rejected candidate remained recorded in the self-hashing selection. The selected
compact state passed document, semantic, provider-call, manifest, checksum, and empty
decision-ledger verification before market overlap construction.

## Source health

The source-health gate passed.

- document sources: 4;
- semantic sources: 4;
- semantic assets: BTC, ETH, and MARKET;
- total documents: 38;
- total semantic records: 12;
- pending accepted documents: 26;
- failed required sources: 0;
- failed optional sources: 0;
- metadata-drift sources: 0;
- zero-accepted sources receiving a provider call: 0.

Per-source pending semantic counts were 1 for Bitcoin Core, 7 for Bitcoin Optech, 9
for Federal Reserve, and 9 for Geth. The SEC source had 20 rejected documents, zero
documents in the accepted ledger, zero backlog, and zero provider calls.

## Maturity and trajectories

The market/semantic dataset contained 677 matured labeled rows and 11 relevant
semantic records. The maturity verdict remained:

```text
insufficient_prospective_sample
```

The unmet conditions were semantic-record count, unique availability dates, and active
semantic decision rows. Both target classes and the labeled-row minimum were already
present, but model fitting remained disabled.

- dataset ID: `semantic-e84544eb0093`;
- dataset content SHA-256: `e84544eb00938baa19e52e29c97dea59aeb8df30682d4097f6ae4f22ed5bf92c`;
- Phase 3G trajectory count: 2;
- Phase 3G head: `e8e4cc89e20052b71a20b57c173a32c4e2e7e441feefb31d45f3be2a5d990c1f`;
- Phase 3I trajectory count: 2;
- Phase 3I head: `93648d9f5fd2c1463767c6c7ef9b899045cc371f2afe678a67793a93dced7c82`.

## Independent audit

After artifact download, all 24 checksum records, the canonical dataset content hash,
the semantic-state candidate and selection hashes, the source-health assessment hash,
and every Phase 3G/3I trajectory link and entry hash were independently verified.

No model fitting, threshold selection, prospective decision, paper-trading action, or
live-trading action occurred. The result permits continued diversified maturity
monitoring only.
