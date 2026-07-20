# Report 2.3 — Current Controlling Status

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Report:** 3 of 5  
**Status date:** 2026-07-20  
**Status:** `PARTIALLY_COMPLETE — OFFICIAL CFTC FOUNDATION AND BOUNDED SAFE CRYPTO SOURCE PROFILES VERIFIED; RAW RETENTION, PRICE/RETURN LINKAGE, AND PAPER-LEVEL GATES OPEN`

This document is the current controlling status for Report 2.3. It supersedes earlier source-access, workflow, and authorization descriptions when they conflict. Detailed technical evidence remains in the linked leaf reports and machine-readable manifests.

---

## 1. Evidence index

### Core verification

- [Initial controlled execution snapshot](02-03-controlled-empirical-and-code-replication.md)
- [Independent reality verification and corrections](02-03-independent-reality-verification-log.md)
- [Static analysis, tests, and coverage](02-03-static-analysis-and-test-verification.md)
- [Machine-readable execution manifest](02-03-replication-execution-manifest.yaml)

### CFTC foundation

- [Verified CFTC acquisition and dated-pilot evidence](02-03-cftc-tff-2022-acquisition-and-pilot-evidence.md)
- [Machine-readable CFTC acquisition evidence](02-03-cftc-tff-2022-evidence.yaml)
- [Verified CFTC release-ledger evidence](02-03-cftc-tff-2022-release-ledger-evidence.md)
- [Machine-readable release-ledger evidence](02-03-cftc-tff-2022-release-ledger-evidence.yaml)
- [Verified CFTC instrument-registry evidence](02-03-cftc-tff-2022-instrument-registry-evidence.md)
- [Machine-readable instrument-registry evidence](02-03-cftc-tff-2022-instrument-registry-evidence.yaml)

### Traditional-futures provider gates

- [Owner-accessible exchange-native source pivot](02-03-owner-accessible-exchange-native-source-pivot.md)
- [Verified Cboe VX public contract pilot](02-03-cboe-vx-public-contract-pilot-evidence.md)
- [CME public access and license gate](02-03-cme-public-access-and-license-gate.md)
- [Machine-readable CME gate](02-03-cme-public-access-and-license-gate.yaml)

### Crypto public-source gates

- [Official crypto source, license, and access selection](02-03-crypto-official-source-license-and-access-selection.md)
- [Verified OKX public funding metadata pilot](02-03-okx-public-funding-metadata-pilot-evidence.md)
- [Machine-readable OKX pilot evidence](02-03-okx-public-funding-metadata-pilot-evidence.yaml)
- [Verified Binance BTCUSDT ephemeral pilot](02-03-binance-btcusdt-public-ephemeral-pilot-evidence.md)
- [Machine-readable Binance pilot evidence](02-03-binance-btcusdt-public-ephemeral-pilot-evidence.yaml)

---

## 2. Repository and governance state

```text
Repository: Emad211/Trade-bot
Branch: agent/edge-research-reports
Draft PR: #41
PR state: OPEN, DRAFT, NOT MERGED
```

The previously found over-permission defect in the factor-artifact audit remains corrected. Unverified files cannot receive an artifact-audit pass.

`ARTIFACT_AUDIT_PASS` still requires, at minimum:

```text
official source identity
matching checksum and byte count
retrieval time
license snapshot
approved long-term immutable storage key
explicit data and return units
```

A successful engineering workflow, a safe metadata artifact, or retention-limited GitHub Actions storage is not an artifact-audit pass.

---

## 3. Verified CFTC foundation

### 3.1 Official annual source

```text
Source: CFTC TFF Futures Only historical text archive, 2022
Workflow: CFTC TFF Historical 2022 Ingestion
Run ID: 29655608183
Conclusion: SUCCESS
Raw ZIP bytes: 494559
Raw ZIP SHA-256: 94c9c1fdee9dfbe377a09923ddfe26b88d3460605dd076081f221ad367d88601
Text member SHA-256: 7c309cb76da8bf432e1a347e5bfde169bcac31cec4e9e33742cf3a078328bb3b
```

The source ZIP passed CRC and member-identity checks.

### 3.2 Exact parser and dated pilot

```text
Workflow: CFTC TFF 2022 Pilot Derivation
Run ID: 29656055991
Conclusion: SUCCESS
Schema fields: 87
Schema SHA-256: fe0123051e8e5f5bb8f0cf4a870b451951bd4fa131777096eb5d028115545d42
Annual rows / unique keys: 2719 / 2719
Report dates: 52
Pilot date: 2022-09-13
Pilot rows / unique reporting codes: 54 / 54
Pilot SHA-256: 1be0028ba872ed56c970f6cd67b76c480b3653b170762c6e55f39dc10c3d268b
```

The full-year artifact contains 56 consolidated rows with exactly one-contract reconciliation differences and zero material accounting failure. The acceptance rule is frozen to that source identity and does not automatically transfer to another vintage.

### 3.3 Fail-closed release ledger

```text
Workflow: CFTC TFF 2022 Release Ledger
Run ID: 29683053593
Conclusion: SUCCESS
Ledger rows: 52
Actual historical release times verified: 0
Ledger SHA-256: 4196c1444a6f9fe878c131f79d5bb4827100b5727baefd1b23333d29babccb40
```

Scheduled, provisional, conservative, and actual timestamps remain separate. An unverified actual release time is null rather than inferred.

### 3.4 Reporting-to-product registry

```text
Workflow: CFTC TFF 2022 Instrument Registry
Run ID: 29685511829
Conclusion: SUCCESS
Registry rows / unique reporting codes: 54 / 54
Registry SHA-256: 70a8e89db716cfc8b1285f3b627188294abaae920c2b99b193f4501a7e525c74
Rows with provider_contract_id: 0
Rows with price_linkage_authorized=true: 0
```

The registry distinguishes reporting identity from exchange product identity and provider price identity. A product root is not a point-in-time provider contract chain.

---

## 4. Traditional-futures provider and access state

```text
Databento: OPERATIONALLY_REJECTED_OWNER_ACCESS_CONSTRAINT
Cboe VX engineering pilot: VERIFIED; RAW RETENTION AND PRICE LINKAGE BLOCKED
CME historical settlement route: BLOCKED_LOGIN_ORDER_FEE_AND_LICENSE
ICE complete historical archive: BLOCKED_PAID_ARCHIVE
CFTC PRE row-level cross-check: PENDING; GITHUB RUNNERS REPEATEDLY RETURNED HTTP 503
```

### Cboe boundary

The public VX pilot verified exact contract files, explicit `Close` and `Settle` fields, parser behavior, and safe evidence handling. It did not authorize raw retention, canonical historical availability, price linkage, or return calculation.

### CME boundary

The Historical Daily Bulletin route leads to DataMine. The observed route requires account/login, licensing, ordering, and fees. Published terms do not grant this project ordinary permission for automated collection, private content-addressed retention, database construction, combination with CFTC data, or derived return creation. Issue #47 is closed as `not planned` until a real permission/license path exists.

No identity, payment, account, credential, jurisdiction, or access-control circumvention is permitted.

---

## 5. Verified OKX bounded public metadata pilot

```text
Workflow: OKX Public Funding Metadata Pilot
Run ID: 29760010859
Conclusion: SUCCESS
Endpoint: /api/v5/public/funding-rate-history
Instrument: BTC-USDT-SWAP
Validated rows: 100
Unique funding timestamps: 100
Observed interval: 28800 seconds x 99
Schema fields: 7
Schema SHA-256: 9e8a8e8502b0af8cf3a4d5645b786888906ee9c2de0a9d4a03133aa9297322bb
Safe artifact ID: 8468365676
Safe artifact digest: 872710f6a4b306d4f1113aaecbcfbab460f2b4ef5cad909187c9b1e4a60116c3
```

Independent inspection found no raw funding rows, funding-rate values, credentials, or reconstructable ordered market-data series in the artifact.

This is a bounded current-public-metadata profile. It is not a 2022 historical acquisition, bulk-retention approval, funding-PnL calculation, or edge verdict.

---

## 6. Verified Binance BTCUSDT ephemeral checksum pilot

### 6.1 Fixed scope

```text
Symbol: BTCUSDT
Month: 2024-01
Sources: Spot Klines, USD-M Klines, Mark, Index, Premium Index, Funding Rate
Official ZIP count: 6
Paired official checksum count: 6
```

### 6.2 Hosted verification

```text
Workflow: Binance BTCUSDT Public Ephemeral Pilot
Run ID: 29761078615
Conclusion: SUCCESS
Ruff: PASS
Strict mypy: PASS
Unit tests: 12 PASS
Official ZIP/checksum validation: PASS FOR SIX OBJECTS
Independent evidence verifier: PASS
No-raw-file proof: PASS
```

### 6.3 Observed contract

```text
Five hourly sources: 744 rows each
Five hourly grids exactly aligned: true
Hourly first / last ms: 1704067200000 / 1706742000000
Funding rows: 93
Funding first / last ms: 1704067200000 / 1706716800000
Funding timestamps with nonzero monthly-grid difference: 15
Maximum absolute funding grid jitter: 3 ms
Funding timestamps normalized or rewritten: false
```

Every observed ZIP SHA-256 matched its paired provider checksum. Exact source and member hashes are frozen in the Binance evidence manifest.

### 6.4 Safe artifact proof

```text
Safe evidence artifact ID: 8468794862
Safe evidence artifact digest: 575cc1a07f299dd52f8c1a889c78df4ba3989976e7d4ff33b11d0b38ac3ad344
Evidence JSON SHA-256: 93b8c06ba836a3d61b9fa0fba1b4b377f3518841b2c72db36b96ee6196fede7b

Receipt artifact ID: 8468795317
Receipt artifact digest: 3bcfc1a5a14170fe1bb636ab1603640a5dfaa222c91bf750c3404c9ca47eaf9c
Receipt JSON SHA-256: a0654baa54c25fb0f840ef31422e7108f2b9ead4347544fd24ab94f436da3f64
```

Both artifact ZIPs were independently opened outside the runner. Each contained exactly one JSON document. No CSV, provider ZIP, HTML, OHLC row, funding-rate row, basis row, or return row was present.

Issue #48 is closed as completed only for this bounded checksum/schema/timing engineering pilot.

### 6.5 Remaining Binance gates

```text
Persistent raw archive retention: NOT AUTHORIZED
Raw redistribution: NOT AUTHORIZED
Formal data-terms review: PENDING
Historical archive available_at: NOT ESTABLISHED
Point-in-time instrument/version metadata: NOT COMPLETE
Basis computation: NOT AUTHORIZED
Funding PnL: NOT AUTHORIZED
Returns: NOT AUTHORIZED
```

The official helper repository's MIT statement is recorded as source evidence but is not treated as a blanket legal conclusion for every retention, redistribution, jurisdictional, or derived-data use.

---

## 7. Current source classifications

```text
Official CFTC raw artifact: ACQUIRED_AND_ACTIONS_STAGED
CFTC release ledger: VERIFIED_SCHEDULED_FAIL_CLOSED
CFTC reporting-to-product registry: VERIFIED_PRICE_LINKAGE_DISABLED
Traditional-futures provider contract chain: NOT ACQUIRED
OKX bounded public funding metadata: VERIFIED_SAFE_PROFILE_ONLY
Binance six-object archive/checksum profile: VERIFIED_EPHEMERALLY_SAFE_METADATA_ONLY
AQR original/maintained workbooks: REMAINING ARTIFACT GATES OPEN
Moreira-Muir author artifact and reconciliation: SEPARATE OPEN REPLICATION SCOPE
Licensed traditional-futures histories: BLOCKED_OR_PENDING
```

Actions artifacts remain retention-limited and are not approved long-term immutable raw storage.

---

## 8. Hypothesis verdicts

| Hypothesis | Verified progress | Empirical status |
|---|---|---|
| `EDGE-FUT-TREND-001` | Mechanics ready; exact licensed price history incomplete | `INCONCLUSIVE` |
| `EDGE-RISK-POLICY-001` | Recursive overlay mechanics ready | `INCONCLUSIVE` |
| `EDGE-FUT-CARRY-001` | Same-contract and roll mechanics ready; provider chain incomplete | `INCONCLUSIVE` |
| `EDGE-FUT-POSITION-001` | Official CFTC raw source, pilot, release ledger, and product registry verified; provider price linkage blocked | `INCONCLUSIVE` |
| `EDGE-CRYPTO-BASIS-001` | Binance six-source checksum/schema/timing profile verified ephemerally; instrument versioning, retention, and returns blocked | `INCONCLUSIVE` |
| `EDGE-CRYPTO-RV-001` | Linear accounting mechanics ready; safe public source profiles exist but empirical construction remains unauthorized | `INCONCLUSIVE` |

No hypothesis has an economic pass.

---

## 9. Controlling authorization

```yaml
implementation: true
unit_testing: true
formula_validation: true
official_source_metadata_review: true
cftc_official_acquisition: true
cftc_release_ledger_construction: true
cftc_reporting_to_product_mapping: true
safe_public_source_hash_profile_retention: true
okx_bounded_public_metadata_probe: true
binance_ephemeral_checksum_validation: true
formal_terms_and_retention_review: true
point_in_time_instrument_metadata_design: true
historical_availability_research: true

traditional_futures_price_series_assignment: false
crypto_persistent_raw_retention: false
raw_redistribution: false
basis_computation: false
funding_pnl_computation: false
returns_computation: false
empirical_fitting: false
parameter_tuning: false
strategy_tournament: false
paper_trading: false
live_trading: false
leverage: false
capital_deployment: false
report_2_4_full_authorization: false
```

---

## 10. Next permitted gate

Issue #50 owns the next crypto step:

```text
Verify OKX 2022 historical funding delivery and revocable-retention contract
```

Only these outcomes are admitted:

```text
GO_PRIVATE_REVOCABLE_2022_FUNDING_PILOT
BLOCKED_ACCESS_OR_DELIVERY
BLOCKED_LICENSE_OR_RETENTION
```

The Binance path may continue only through formal retention/terms review, archive-publication timing research, and point-in-time instrument/version metadata. No basis or return calculation may begin from the engineering pilot alone.

---

## 11. Final controlling verdict

```text
REAL REPOSITORY WORK: CONFIRMED
OFFICIAL CFTC RAW SOURCE: CONFIRMED
CFTC PARSER, PILOT, RELEASE LEDGER, AND PRODUCT REGISTRY: CONFIRMED
TRADITIONAL-FUTURES PROVIDER PRICE LINKAGE: NOT AUTHORIZED
OKX BOUNDED SAFE METADATA PROFILE: CONFIRMED
BINANCE SIX-OBJECT CHECKSUM/SCHEMA/TIMING PROFILE: CONFIRMED EPHEMERALLY
BINANCE SAFE ARTIFACT CONTAINS MARKET ROWS: NO
CRYPTO RAW RETENTION AUTHORIZATION: NOT GRANTED
POINT-IN-TIME CRYPTO INSTRUMENT METADATA: INCOMPLETE
HISTORICAL CRYPTO ARCHIVE AVAILABLE_AT: INCOMPLETE
BASIS / FUNDING PNL / RETURNS: NOT COMPUTED
PAPER-LEVEL NUMERICAL REPLICATION: NOT COMPLETE
TRADING EDGE: NOT ESTABLISHED
ALL SIX HYPOTHESES: INCONCLUSIVE
REPORT 2.4: BLOCKED
```
