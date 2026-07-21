# Report 2.3 — Current Controlling Status

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Report:** 3 of 5  
**Status date:** 2026-07-21  
**Status:** `PARTIALLY_COMPLETE — VERIFIED CFTC FOUNDATION, BOUNDED CRYPTO SOURCE CONTRACTS, CLOSED OKX HISTORICAL BLOCKER, AND ADMITTED PROSPECTIVE OKX REGISTRY; PRICE, RETURN, PAPER-LEVEL, AND REPORT 2.4 GATES REMAIN BLOCKED`

This document is the current controlling status for Report 2.3. It supersedes earlier workflow, source-access, timing, retention, authorization, and next-gate descriptions whenever they conflict. Leaf reports and machine-readable manifests remain the evidence layer.

---

## 1. Repository and governance state

```text
Repository: Emad211/Trade-bot
Branch: agent/edge-research-reports
Draft PR: #41
PR state: OPEN, DRAFT, NOT MERGED

Issue #50: CLOSED — GO_PRIVATE_REVOCABLE_2022_FUNDING_PILOT
Issue #51: CLOSED — BLOCKED_INSTRUMENT_VERSION_HISTORY
Issue #51 independent blocker: BLOCKED_ARCHIVE_AVAILABILITY_TIMING
Issue #52: CLOSED — GO_PROSPECTIVE_OKX_POINT_IN_TIME_REGISTRY
```

The Issue #52 GO is narrow. It authorizes only prospective, append-only source/version monitoring from the verified collection start forward. It does not repair historical evidence or authorize any economic test.

All six admitted hypotheses remain `INCONCLUSIVE`:

```text
EDGE-FUT-CARRY-001
EDGE-FUT-TREND-001
EDGE-CRYPTO-BASIS-001
EDGE-FUT-POSITION-001
EDGE-RISK-POLICY-001
EDGE-CRYPTO-RV-001
```

---

## 2. Repository-wide verification

Verified baseline commit:

```text
Head SHA: 65dcfe90c22dd64077d915ddf7d2d5c76c0bc529
Merge-test SHA: cda585dc97fe054624aa3f8611733b62fd459812
```

General CI:

```text
Workflow run: 29826614793
Python 3.11 quality: SUCCESS
Python 3.12 quality: SUCCESS
Optional ML integration: SUCCESS
Package smoke and clean-wheel import: SUCCESS
Formatting: SUCCESS
Lint: SUCCESS
Mypy: SUCCESS
Core tests: SUCCESS
Dependency consistency: SUCCESS
```

Replication Integrity:

```text
Workflow run: 29826614980
Conclusion: SUCCESS
Isolated Python 3.11 environment: SUCCESS
Ruff: SUCCESS
Mypy: SUCCESS
Complete non-optional test suite: SUCCESS
Replication package coverage: 73.49%
Frozen workflow threshold: 70%
Coverage XML export: SUCCESS
Coverage JSON export: SUCCESS
Artifact ID: 8493564355
Artifact digest: sha256:df43f9fa2647f30f784240dcc115a6fc426e003c9da41265e05a1bc2e9bff505
```

The repository-wide `pyproject.toml` coverage default remains 75%. Replication Integrity deliberately enforces its separately frozen 70% package threshold exactly once; XML and JSON serialization no longer re-apply the unrelated global threshold.

---

## 3. Verified CFTC foundation

### 3.1 Official annual source and parser

```text
Source: CFTC TFF Futures Only historical text archive, 2022
Archive bytes: 494559
Archive SHA-256: 94c9c1fdee9dfbe377a09923ddfe26b88d3460605dd076081f221ad367d88601
Member SHA-256: 7c309cb76da8bf432e1a347e5bfde169bcac31cec4e9e33742cf3a078328bb3b
Schema fields: 87
Schema SHA-256: fe0123051e8e5f5bb8f0cf4a870b451951bd4fa131777096eb5d028115545d42
Annual rows / unique keys: 2719 / 2719
Report dates: 52
Pilot date: 2022-09-13
Pilot rows / reporting codes: 54 / 54
Pilot SHA-256: 1be0028ba872ed56c970f6cd67b76c480b3653b170762c6e55f39dc10c3d268b
```

### 3.2 Release ledger

```text
Ledger rows: 52
Actual historical release times verified: 0
Ledger SHA-256: 4196c1444a6f9fe878c131f79d5bb4827100b5727baefd1b23333d29babccb40
```

Scheduled, provisional, conservative, and actual timestamps remain distinct. Unverified actual release times remain null.

### 3.3 Reporting-to-product registry

```text
Registry rows / unique reporting codes: 54 / 54
Provider contract IDs: 0
Price-linkage-authorized rows: 0
Registry SHA-256: 70a8e89db716cfc8b1285f3b627188294abaae920c2b99b193f4501a7e525c74
```

A CFTC reporting identity is not automatically an exchange product, provider contract chain, executable price series, or return authorization.

---

## 4. Traditional-futures provider state

```text
Databento: OPERATIONALLY_REJECTED_OWNER_ACCESS_CONSTRAINT
Cboe VX engineering pilot: VERIFIED; RAW RETENTION AND CANONICAL HISTORICAL TIMING BLOCKED
CME historical settlements: BLOCKED_LOGIN_ORDER_FEE_AND_LICENSE
ICE complete historical archive: BLOCKED_PAID_ARCHIVE
Traditional-futures provider price linkage: NOT ACQUIRED
Traditional-futures returns: NOT AUTHORIZED
```

No false identity, borrowed payment instrument, third-party account, shared credential, or payment/jurisdiction circumvention is permitted.

---

## 5. OKX historical funding and retention evidence

### 5.1 Verified March 2022 archive identity

```text
Delivery endpoint: POST /priapi/v5/broker/public/trade-data/download-link
Module / type / family: 3 / SWAP / BTC-USDT
Partition: 2022-03
Official file: BTC-USDT-SWAP-fundingrates-2022-03.zip
ZIP bytes: 1403
ZIP SHA-256: ce4fe9aaf1dfdee16e1d11cdabcbb405eb348966902950db1ca862dc86779013
CSV bytes: 4546
CSV SHA-256: 508195adcc2fd9e9a1978926d8da89af4054d79de4675268cbfb2ac9539e73da
Fields: instrument_name, funding_rate, funding_time
Rows / unique timestamps: 93 / 93
Minimum UTC timestamp: 2022-02-28T16:00:00Z
Maximum UTC timestamp: 2022-03-31T08:00:00Z
Observed interval: 28800000 ms x 92
```

Raw ZIP and CSV bytes were deleted before safe evidence upload. No funding-rate value, raw row, or reconstructable ordered series was published.

### 5.2 Private revocable retention

Issue #50 closed as:

```text
GO_PRIVATE_REVOCABLE_2022_FUNDING_PILOT
```

This authorizes only an owner-controlled one-month private pilot under encryption, owner-only access, backup/sync exclusion, a maximum 30-day lease, revocation/expiry deletion, and deletion receipts. It does not authorize bulk acquisition, permanent storage, public upload, returns, or trading.

### 5.3 Historical instrument and archive decision

Issue #51 closed with the primary outcome:

```text
BLOCKED_INSTRUMENT_VERSION_HISTORY
```

Independent remaining blocker:

```text
BLOCKED_ARCHIVE_AVAILABILITY_TIMING
```

The official source audit verified dated launch, face-value, funding-rule, postponement, service, catalog, changelog, and current-API sources. It did not prove a complete March 2022 contract version or the first publication time of the specific March archive.

The current archive representation reported `Last-Modified: 2026-02-07T11:42:16Z`. This is not treated as first publication time, but it prevents representing the currently retrieved bytes as an unchanged 2022 vintage.

Current metadata, current downloadability, provider time fields, and absence of a completion notice are not projected backward.

---

## 6. Prospective OKX point-in-time registry

Issue #52 closed as:

```text
GO_PROSPECTIVE_OKX_POINT_IN_TIME_REGISTRY
```

### 6.1 Collection boundary

```text
Mode: PROSPECTIVE_ONLY
Collection start: 2026-07-21T10:30:16.294785Z
Effective semantics: FIRST_OBSERVED_NOT_PROVIDER_EFFECTIVE
Historical backfill: false
Provider timestamp inference: false
Observation-gap interpolation: false
```

### 6.2 Initial snapshot

```text
Workflow run: 29822410788
Artifact ID: 8491912580
Artifact digest: sha256:3d9c58788f5c1f07b83be906cd97b7780c125edad32306f4a1c14db3ef2b6407
Evidence SHA-256: 729dfb417385a6ccdb9efbb39c0b856eb86a69db89f5c47044080920b2593a75
Instrument version ID: 90e429110215d9f4df991d9447b96a1bc31cccf54f88af63a7dd96702c480b3f
Instrument observation ID: 66c27d62616ce0f25355e3acd5e0fd2dcdbcde0a13fa7db1bcf20d34cfa104f4
Funding-source version ID: dcb752c70225b47c0e3aa9ff0ce89dca5154dbd95c24a5fb84ddbe126913ae4d
Funding-source observation ID: 122a88bbc72fefb3b43a20ffd5212b91856d9a1b6f2f2fd7a6cc54c09fd1e234
```

### 6.3 Second snapshot and append-only proof

```text
Workflow run: 29823341681
Artifact ID: 8492272929
Artifact digest: sha256:8cf07b6b3de36514be49f8ff7bf654fb2f9c11d1a59b6cc0ffc71b5cc352269d
Evidence SHA-256: e34c9931cdc5a263b5abfe263a76ff60e327989f91ec32050367370baf265c27
Previous snapshot SHA-256: 729dfb417385a6ccdb9efbb39c0b856eb86a69db89f5c47044080920b2593a75
Registry committed at: 2026-07-21T10:44:35.402300Z
```

Verified properties:

```text
Predecessor chain valid: true
Stream-tail references valid: true
Registry commit time monotonic: true
Observation IDs unique: true
Version IDs content-addressed: true
Historical backfill: false
Gap continuity inferred: false
Provider timestamp inferred: false
```

Both streams remained unchanged during the second observation:

```text
Instrument content version changed: false
Instrument changed fields: []
New instrument observation: 96812116bee5dceae618714ad199f05b80609ba8b0bf6ab1ba908b6935a2a807

Funding-source content version changed: false
Funding-source changed fields: []
New funding observation: c9d49d39fda12f75d0991c2cf3b31728918f1e51267845b9f5a8698edcb01b96
```

The registry may retain safe hashes, schema fields, selected non-market instrument fields, source-health diagnostics, and clocks. It may not retain raw funding values or reconstructable ordered market series.

---

## 7. Binance bounded profile

The January 2024 BTCUSDT pilot verified six official ZIP/checksum pairs covering spot, USD-M futures, mark, index, premium index, and funding data. Safe artifacts contain hashes and profiles only.

```text
Persistent raw retention: NOT AUTHORIZED
Historical archive available_at: NOT ESTABLISHED
Point-in-time historical instrument versions: INCOMPLETE
Basis / funding PnL / returns: NOT AUTHORIZED
```

---

## 8. Controlling authorization

```yaml
implementation: true
unit_testing: true
formula_validation: true
official_source_metadata_review: true
safe_hash_and_schema_retention: true
cftc_official_acquisition: true
cftc_release_ledger_construction: true
cftc_reporting_to_product_mapping: true
okx_bounded_public_metadata_probe: true
okx_march_2022_ephemeral_file_validation: true
okx_private_revocable_one_month_pilot: true
okx_prospective_registry_collection: true
okx_content_version_monitoring: true
okx_source_health_monitoring: true
okx_append_only_observation_chaining: true
historical_backfill: false
traditional_futures_price_linkage: false
basis_computation: false
funding_pnl_computation: false
returns_computation: false
empirical_fitting: false
parameter_tuning: false
strategy_testing: false
paper_trading: false
live_trading: false
leverage: false
capital_deployment: false
report_2_4_authorized: false
```

---

## 9. Remaining Report 2.3 blockers

```text
Traditional-futures exact provider contract chains and prices: INCOMPLETE
Historical OKX March 2022 instrument contract: BLOCKED
Historical OKX March 2022 archive publication available_at: BLOCKED
Binance historical retention, available_at, and instrument versions: INCOMPLETE
Executable price, mark, index, and cost linkage: INCOMPLETE
Basis, funding PnL, and returns: NOT AUTHORIZED
Paper-level numerical replication: NOT COMPLETE
Economic edge: NOT ESTABLISHED
Report 2.4: BLOCKED
```

The next work must preserve the distinction between prospective source monitoring and economic testing. A green source registry does not authorize returns or establish edge.
