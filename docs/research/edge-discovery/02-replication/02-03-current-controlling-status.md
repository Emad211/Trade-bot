# Report 2.3 — Current Controlling Status

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Report:** 3 of 5  
**Status date:** 2026-07-19  
**Status:** `PARTIALLY_COMPLETE — OFFICIAL CFTC SOURCE, PILOT, RELEASE LEDGER, AND VERSIONED PRODUCT REGISTRY VERIFIED; PROVIDER PRICE LINKAGE AND REMAINING REPLICATION GATES OPEN`

This document is the controlling status for Report 2.3. It supersedes older execution counts, source states, generic `PASS` wording, timing claims, and instrument-mapping descriptions when they conflict.

Detailed evidence is retained in:

- [Initial controlled execution report](02-03-controlled-empirical-and-code-replication.md)
- [Independent reality verification and corrections](02-03-independent-reality-verification-log.md)
- [Static analysis, tests, and coverage](02-03-static-analysis-and-test-verification.md)
- [Verified CFTC acquisition and pilot evidence](02-03-cftc-tff-2022-acquisition-and-pilot-evidence.md)
- [Machine-readable CFTC acquisition evidence](02-03-cftc-tff-2022-evidence.yaml)
- [Verified CFTC release-ledger evidence](02-03-cftc-tff-2022-release-ledger-evidence.md)
- [Machine-readable CFTC release-ledger evidence](02-03-cftc-tff-2022-release-ledger-evidence.yaml)
- [Verified CFTC instrument-registry evidence](02-03-cftc-tff-2022-instrument-registry-evidence.md)
- [Machine-readable CFTC instrument-registry evidence](02-03-cftc-tff-2022-instrument-registry-evidence.yaml)
- [Machine-readable execution manifest](02-03-replication-execution-manifest.yaml)

---

## 1. Repository and governance state

```text
Repository: Emad211/Trade-bot
Branch: agent/edge-research-reports
Draft PR: #41
Repository and branch through authenticated GitHub connector: CONFIRMED
Research PR state: OPEN, DRAFT, NOT MERGED
```

The previously discovered over-permission defect in `run_aqr_vintage_audit` remains corrected. Unverified files cannot receive an artifact-audit pass.

`ARTIFACT_AUDIT_PASS` still requires:

```text
official source identity
matching SHA-256 and byte count
retrieval time
license snapshot
long-term immutable storage key
explicit data/return unit
```

Current CFTC artifacts are staged in retention-limited GitHub Actions storage. Small deterministic derived contracts and registries are also retained in Git. Neither condition is equivalent to approved long-term immutable raw storage.

---

## 2. Verified implementation scopes

### 2.1 Hardened local replication package

```text
Ruff under repository rules: PASS
Mypy strict: PASS
Pytest: 15 passed
Statement coverage: 85.44%
Compileall: PASS
```

### 2.2 Official annual CFTC ZIP acquisition

```text
Workflow: CFTC TFF Historical 2022 Ingestion
Run ID: 29655608183
Conclusion: SUCCESS
```

Verified scope:

- official CFTC ZIP acquisition;
- ZIP CRC validation;
- member identity and hash verification;
- raw bundle and receipt upload.

### 2.3 Exact parser and dated pilot

```text
Workflow: CFTC TFF 2022 Pilot Derivation
Run ID: 29656055991
Conclusion: SUCCESS
```

Verified scope:

- exact archive, member, and schema checks;
- full-year parsing and diagnostics;
- deterministic `2022-09-13` pilot derivation;
- independent raw/member/schema/profile/pilot checks;
- raw-plus-derived bundle and receipt upload.

### 2.4 Fail-closed release ledger

```text
Workflow: CFTC TFF 2022 Release Ledger
Run ID: 29683053593
Conclusion: SUCCESS
```

Verified scope:

- all 52 scheduled release rows;
- federal-holiday and DST handling;
- hard verification that no row claims a verified actual historical release time;
- source-plus-ledger bundle and receipt upload.

### 2.5 Point-in-time reporting-to-product registry

```text
Workflow: CFTC TFF 2022 Instrument Registry
Run ID: 29685511829
Conclusion: SUCCESS
```

Verified scope:

- Ruff, strict mypy, and seven mapping tests;
- official archive acquisition and frozen pilot derivation;
- mapping-contract decoding and SHA-256 verification;
- all 54 CFTC reporting-code rows covered exactly once;
- special historical, aggregate, and nonstandard cases checked;
- hard verification that no row authorizes price linkage or returns;
- registry bundle and receipt upload.

Repository-wide legacy `ci` and `Replication Integrity` workflows are not green on this research branch. Their failures are not reclassified as passes. Claims here apply only to the explicitly verified scopes above.

---

## 3. Official source and parser identity

```text
Source ID:
CFTC_TFF_FUTURES_ONLY_HISTORICAL_TEXT_2022

Official URL:
https://www.cftc.gov/files/dea/history/fut_fin_txt_2022.zip

Raw filename:
fut_fin_txt_2022.zip

Raw byte count:
494559

Raw SHA-256:
94c9c1fdee9dfbe377a09923ddfe26b88d3460605dd076081f221ad367d88601
```

ZIP/member evidence:

```text
ZIP CRC: PASS
Non-directory member count: 1
Text member: FinFutYY.txt
Member byte count: 2105659
Member CRC32: 7c783c41
Member SHA-256:
7c309cb76da8bf432e1a347e5bfde169bcac31cec4e9e33742cf3a078328bb3b
```

Parser contract:

```text
Schema field count: 87
Schema SHA-256:
fe0123051e8e5f5bb8f0cf4a870b451951bd4fa131777096eb5d028115545d42

Annual rows: 2719
Unique report-date/contract keys: 2719
Report dates: 52
First date: 2022-01-04
Last date: 2022-12-27
Futures-only rows: 2719
```

Annual accounting diagnostics:

```text
Long exact-reconciliation differences: 37
Short exact-reconciliation differences: 33
Rows with accepted consolidated unit differences: 56
Material accounting failures: 0
```

Every nonzero difference is exactly one contract in magnitude and confined to consolidated rows for codes `12460+`, `13874+`, and `20974+`. This acceptance rule is frozen to the verified 2022 artifact and does not automatically transfer to another year or revision.

---

## 4. Dated pilot identity

```text
Report date: 2022-09-13
Rows: 54
Unique contract-market codes: 54
Minimum code: 020601
Maximum code: 43874A
Long reconciliation differences: 0
Short reconciliation differences: 0
Material accounting failures: 0
```

```text
Filename:
tff_futures_only_2022-09-13.canonical.csv

Byte count:
27954

SHA-256:
1be0028ba872ed56c970f6cd67b76c480b3653b170762c6e55f39dc10c3d268b
```

---

## 5. Fail-closed release ledger

CFTC's general publication rule is reconstructed without inventing actual historical release times.

```text
Filename:
cftc_tff_futures_only_2022_release_ledger.csv

Rows:
52

Byte count:
16914

SHA-256:
4196c1444a6f9fe878c131f79d5bb4827100b5727baefd1b23333d29babccb40

Actual release times verified:
0
```

Timing contract:

```text
scheduled_release_time:
third federal business day after report date at 15:30 America/New_York

provisional_available_at:
scheduled release plus five-minute parser allowance

conservative_available_at:
next federal business day at 15:30 America/New_York

actual_release_time:
null unless independently verified
```

Exactly two 2022 report dates are holiday-delayed by the reconstructed rule:

```text
2022-11-08 → 2022-11-14 15:30 EST — Veterans Day
2022-11-22 → 2022-11-28 15:30 EST — Thanksgiving Day
```

Pilot timing:

```text
Report date: 2022-09-13
Scheduled release: 2022-09-16T19:30:00Z
Provisional availability: 2022-09-16T19:35:00Z
Conservative availability: 2022-09-19T19:30:00Z
Actual release verified: false
```

---

## 6. Versioned reporting-to-product registry

The registry separates CFTC reporting identity, exchange product identity, and provider price identity.

```text
Registry version:
CFTC_TFF_2022_09_13_INSTRUMENT_REGISTRY_V1

Filename:
cftc_tff_2022-09-13_instrument_registry.csv

Rows:
54

Unique reporting codes:
54

Byte count:
38903

SHA-256:
70a8e89db716cfc8b1285f3b627188294abaae920c2b99b193f4501a7e525c74
```

Registry source identities:

```text
Pilot SHA-256:
1be0028ba872ed56c970f6cd67b76c480b3653b170762c6e55f39dc10c3d268b

Mapping-contract SHA-256:
4dd92e493f9752371cdfaef5f6bc90edf72b235cd0f4d444aa96aa9e628251c2

Official-source registry SHA-256:
bc861dbe5a7da1f27060d87cb588a51acdd6466dbb27c889cafc5c3680cd6fff
```

Classification counts:

```text
HISTORICAL_SCREEN_TRADABLE_ROOT_VERIFIED: 47
NON_TRADABLE_CONSOLIDATED_AGGREGATE: 3
HISTORICAL_LATER_DELISTED_ROOT_VERIFIED: 2
NON_STANDARD_EXECUTION_PRODUCT: 1
PRODUCT_IDENTITY_VERIFIED_TECHNICAL_SYMBOL_PENDING: 1
```

The consolidated reporting aggregates are:

```text
12460+ — DJIA Consolidated
13874+ — S&P 500 Consolidated
20974+ — NASDAQ-100 Consolidated
```

They have no exchange product root and must never receive a direct price series.

Special historical/nonstandard cases include:

```text
132741 — Eurodollar — GE — historical later-delisted product
157741 — Three-Month BSBY — BSB / BW — historical later-delisted product
13874W — Adjusted Interest Rate S&P 500 Total Return — ASR / security group 0B — nonstandard execution
240743 — Nikkei Stock Average, yen denominated — NIY
04360Y — Micro 10-Year Yield — product identity 10Y; technical provider symbol pending
```

Price-linkage state:

```text
Rows with price_linkage_authorized=true: 0
Rows with provider_contract_id populated: 0
Global price linkage authorized: false
Returns authorized: false
Empirical fitting authorized: false
```

A product root is not a provider contract-chain identity. No return may be computed from this registry alone.

---

## 7. Durable and staged artifacts

Small deterministic derived contracts are retained in Git as compressed Base64 text:

```text
02-03-cftc-tff-2022-instrument-map-contract.csv.gz.b64
02-03-cftc-tff-2022-instrument-registry.csv.gz.b64
```

The full raw/derived bundles are staged in GitHub Actions.

### Raw annual bundle

```text
Run ID: 29655608183
Artifact ID: 8432769852
Expiry: 2026-10-16
```

### Raw and dated-pilot bundle

```text
Run ID: 29656055991
Artifact ID: 8432902155
Expiry: 2026-10-16
```

### Source and release-ledger bundle

```text
Run ID: 29683053593
Artifact ID: 8441186298
Expiry: 2026-10-17
```

### Instrument-registry bundle

```text
Run ID: 29685511829
Artifact ID: 8441940834
Artifact digest:
c0e68748e7d1b7266ee4e4b7a9de1ebd59bbea829641499618a349bae0b5457a
Expiry: 2026-10-17
```

### Instrument-registry receipt

```text
Artifact ID: 8441941004
Artifact digest:
7ee9d381ffc852b6e432592945ffa69bb35cfcf65557acd98da3b19ba4809796
Expiry: 2026-10-17
```

The two registry artifact ZIP digests were independently recomputed after download and matched GitHub's recorded values.

Current storage classification:

```text
ACTIONS_ARTIFACT_STAGED_RETENTION_90_DAYS
```

This is not approved long-term immutable raw storage.

---

## 8. CFTC PRE API state

```text
API identity: VERIFIED
GitHub-runner reliability: FAILED_REPEATED_HTTP_503
Immutable PRE raw artifact: NOT ACQUIRED
PRE-versus-historical row cross-check: PENDING
```

The successful evidence comes from the official annual historical compressed archive. PRE is retained as a future manual diagnostic and row-level cross-check.

---

## 9. Remaining source and price-linkage gates

AQR workbooks, Moreira–Muir author factors, licensed traditional-futures histories, Chi et al. source data, and Binance/OKX pilot artifacts remain unavailable or un-ingested.

For CFTC positioning, the next hard gate is:

```text
PROVIDER_VINTAGE_CONTRACT_CHAIN_AND_POINT_IN_TIME_PRICE_SOURCE
```

It requires, per eligible product:

- provider reference-data source and license;
- effective-dated provider contract identifier;
- listed contract-month chain;
- expiration, first-notice, and last-trade dates;
- historical multiplier, tick, and quotation-currency versions;
- settlement-field definition;
- same-contract price observation contract;
- provider vintage or snapshot identity.

Until this gate passes, the project prohibits:

- assigning a price series by root resemblance;
- assigning any price to consolidated aggregate rows;
- projecting current metadata backward into 2022;
- continuous-futures PnL;
- positioning-return computation;
- signal fitting.

---

## 10. Hypothesis verdicts

| Hypothesis | Implementation/data progress | Empirical status |
|---|---|---|
| `EDGE-FUT-TREND-001` | Audit mechanics ready; raw futures still licensed | `INCONCLUSIVE` |
| `EDGE-RISK-POLICY-001` | Recursive overlay mechanics ready | `INCONCLUSIVE` |
| `EDGE-FUT-CARRY-001` | Same-contract and roll mechanics ready | `INCONCLUSIVE` |
| `EDGE-FUT-POSITION-001` | Official raw CFTC data, pilot, release ledger, and 54-row product registry verified; provider price linkage blocked | `INCONCLUSIVE` |
| `EDGE-CRYPTO-BASIS-001` | Instrument-version and basis mechanics ready | `INCONCLUSIVE` |
| `EDGE-CRYPTO-RV-001` | Linear two-leg accounting ready | `INCONCLUSIVE` |

No hypothesis has an economic pass.

---

## 11. Controlling authorization

```yaml
implementation: true
unit_testing: true
formula_validation: true
official_data_acquisition: true
cftc_release_ledger_construction: true
cftc_reporting_to_product_mapping: true
provider_price_linkage_contract_design: true
licensed_price_linkage_planning: true

price_series_assignment: false
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

## 12. Final controlling verdict

```text
REAL REPOSITORY WORK: CONFIRMED
REAL COMMITTED IMPLEMENTATION: CONFIRMED
OFFICIAL RAW CFTC ACQUISITION: CONFIRMED
EXACT SOURCE PARSER: CONFIRMED
DATED 54-ROW PILOT: CONFIRMED
FAIL-CLOSED 52-ROW RELEASE LEDGER: CONFIRMED
VERSIONED 54-ROW REPORTING-TO-PRODUCT REGISTRY: CONFIRMED
CONSOLIDATED AGGREGATE EXCLUSION: CONFIRMED
HISTORICAL AND NONSTANDARD SPECIAL CASES: RECORDED
REGISTRY SHA-256: CONFIRMED
INDEPENDENT ARTIFACT REHASH: CONFIRMED
PRICE-LINKAGE-AUTHORIZED ROWS: ZERO
PROVIDER CONTRACT IDENTIFIERS: ZERO
LONG-TERM IMMUTABLE RAW STORAGE: INCOMPLETE
PROVIDER CONTRACT-CHAIN AND PRICE VINTAGE: INCOMPLETE
PAPER-LEVEL NUMERICAL REPLICATION: NOT COMPLETE
TRADING EDGE: NOT ESTABLISHED
ALL SIX HYPOTHESES: INCONCLUSIVE
REPORT 2.4: BLOCKED
```
