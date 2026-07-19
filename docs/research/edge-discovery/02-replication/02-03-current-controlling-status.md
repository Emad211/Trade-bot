# Report 2.3 — Current Controlling Status

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Report:** 3 of 5  
**Status date:** 2026-07-19  
**Status:** `PARTIALLY_COMPLETE — OFFICIAL CFTC RAW ARTIFACT, DATED PILOT, AND FAIL-CLOSED RELEASE LEDGER VERIFIED; REMAINING REPLICATION GATES OPEN`

This document is the controlling status for Report 2.3. It supersedes older execution counts, source states, generic `PASS` wording, and timing claims in earlier snapshots when they conflict.

Detailed evidence is retained in:

- [Initial controlled execution report](02-03-controlled-empirical-and-code-replication.md)
- [Independent reality verification and corrections](02-03-independent-reality-verification-log.md)
- [Static analysis, tests, and coverage](02-03-static-analysis-and-test-verification.md)
- [Verified CFTC TFF acquisition and pilot evidence](02-03-cftc-tff-2022-acquisition-and-pilot-evidence.md)
- [Machine-readable CFTC TFF acquisition evidence](02-03-cftc-tff-2022-evidence.yaml)
- [Verified CFTC TFF release-ledger evidence](02-03-cftc-tff-2022-release-ledger-evidence.md)
- [Machine-readable CFTC release-ledger evidence](02-03-cftc-tff-2022-release-ledger-evidence.yaml)
- [Machine-readable execution manifest](02-03-replication-execution-manifest.yaml)

---

## 1. Verified repository and implementation state

```text
Repository: Emad211/Trade-bot
Branch: agent/edge-research-reports
Draft PR: #41
Repository and branch through authenticated GitHub connector: CONFIRMED
Committed replication source independently reconstructed: CONFIRMED
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

The current CFTC artifacts are staged in retention-limited GitHub Actions storage. They are not `IMMUTABLE_INGESTED` and do not receive `ARTIFACT_AUDIT_PASS`.

---

## 2. Local and hosted code verification

The hardened replication package previously passed locally:

```text
Ruff under repository rules: PASS
Mypy strict: PASS
Pytest: 15 passed
Statement coverage: 85.44%
Compileall: PASS
```

Dedicated CFTC hosted workflows have now passed independently.

### Official annual ZIP acquisition

```text
Workflow: CFTC TFF Historical 2022 Ingestion
Run ID: 29655608183
Conclusion: SUCCESS
```

Passed scope:

- Ruff and strict mypy;
- ingestion tests;
- official ZIP acquisition;
- ZIP CRC and member-hash verification;
- raw-bundle and receipt upload.

### End-to-end annual parser and dated pilot

```text
Workflow: CFTC TFF 2022 Pilot Derivation
Run ID: 29656055991
Conclusion: SUCCESS
```

Passed scope:

- Ruff and strict mypy;
- eight ingestion/parser tests;
- official ZIP acquisition;
- exact archive, member, and schema checks;
- full-year diagnostics;
- deterministic `2022-09-13` pilot derivation;
- independent raw/member/schema/profile/pilot checks;
- raw-plus-derived bundle and receipt upload.

### Fail-closed 2022 release ledger

```text
Workflow: CFTC TFF 2022 Release Ledger
Run ID: 29683053593
Conclusion: SUCCESS
```

Passed scope:

- Ruff and strict mypy;
- historical source-parser and release-ledger tests;
- official annual ZIP acquisition;
- derivation of all 52 scheduled release rows;
- independent source/hash/count/DST/holiday/timing checks;
- hard verification that no row claims an actual historical release time;
- source-plus-ledger bundle and receipt upload.

The repository-wide legacy `ci` and `Replication Integrity` workflows are not green on this research branch. Their failures are not reclassified as passes. Claims in this document apply only to the explicitly verified scopes above.

---

## 3. Verified official raw artifact

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

ZIP and member evidence:

```text
ZIP CRC: PASS
Non-directory member count: 1
Text member: FinFutYY.txt
Member byte count: 2105659
Member CRC32: 7c783c41
Member SHA-256:
7c309cb76da8bf432e1a347e5bfde169bcac31cec4e9e33742cf3a078328bb3b
```

These values were computed in GitHub Actions and independently recomputed after downloading the Actions artifacts.

---

## 4. Exact parser contract and annual findings

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

Full-year accounting diagnostics:

```text
Long exact-reconciliation differences: 37
Short exact-reconciliation differences: 33
Rows with accepted consolidated unit differences: 56
Material accounting failures: 0
```

Every nonzero difference is exactly one contract in magnitude and confined to consolidated rows for codes `12460+`, `13874+`, and `20974+`. The differences are recorded rather than erased. This acceptance rule is specific to the frozen 2022 artifact and does not automatically transfer to another year or provider revision.

---

## 5. Deterministic dated pilot

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

Derived file identity:

```text
Filename:
tff_futures_only_2022-09-13.canonical.csv

Byte count:
27954

SHA-256:
1be0028ba872ed56c970f6cd67b76c480b3653b170762c6e55f39dc10c3d268b
```

The pilot retains all 87 source fields and is deterministically sorted by stripped `CFTC_Contract_Market_Code`.

---

## 6. Fail-closed 2022 release ledger

CFTC states that COT data are generally released at 3:30 p.m. Eastern on the third business day after the Tuesday as-of date. CFTC also states that a complete historical list of release dates is not maintained. Therefore the project reconstructs scheduled release times but does not invent historical actual release times.

Ledger identity:

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
scheduled release plus 5-minute parser allowance

conservative_available_at:
next federal business day at 15:30 America/New_York

actual_release_time:
null unless independently verified
```

DST profile:

```text
Eastern Standard Time rows (-05:00): 18
Eastern Daylight Time rows (-04:00): 34
```

Exactly two report dates are holiday-delayed under the official-rule reconstruction:

```text
2022-11-08 → 2022-11-14 at 15:30 EST
Reason: Veterans Day on 2022-11-11

2022-11-22 → 2022-11-28 at 15:30 EST
Reason: Thanksgiving Day on 2022-11-24
```

Pilot timing:

```text
Report date: 2022-09-13
Scheduled release: 2022-09-16T19:30:00Z
Provisional availability: 2022-09-16T19:35:00Z
Conservative availability: 2022-09-19T19:30:00Z
Actual release verified: false
```

A later experiment must predeclare whether it uses provisional or conservative availability. It may not represent either as a verified actual historical timestamp.

---

## 7. Retention-limited Actions staging

### Raw annual bundle

```text
Run ID: 29655608183
Artifact ID: 8432769852
Artifact digest:
d718393c4984a63be874ed72b4dcc0b2173f29717e4339d02b83e1f9ed614270
Expiry: 2026-10-16
```

### Raw and dated-pilot bundle

```text
Run ID: 29656055991
Artifact ID: 8432902155
Artifact digest:
391a7bc682f02e0feec735342b33ae6a63a59c0db9432ee9812e4ebe17c83184
Expiry: 2026-10-16
```

### Source and release-ledger bundle

```text
Run ID: 29683053593
Artifact ID: 8441186298
Artifact digest:
d71233533837dc367e2161293ec5e381f33a316e2e055a96bb89c3199ecf294c
Expiry: 2026-10-17
```

### Release-ledger receipt

```text
Artifact ID: 8441186496
Artifact digest:
577ba3fffa7b8bfadb5ee4a9eacb9bd6aeb0f1126cab8a68e8c6fe8a149b6f2b
Expiry: 2026-10-17
```

Current storage classification:

```text
ACTIONS_ARTIFACT_STAGED_RETENTION_90_DAYS
```

GitHub Actions artifacts are deletable and expire. Long-term immutable storage remains incomplete.

---

## 8. CFTC PRE API state

The Public Reporting Environment identity `gpe5-46if` is verified. Repeated GitHub-hosted acquisition attempts produced persistent HTTP 503 responses, so PRE is retained as a manual diagnostic and future row-level cross-check rather than the primary ingestion source.

```text
API identity: VERIFIED
GitHub-runner reliability: FAILED_REPEATED_HTTP_503
Immutable PRE raw artifact: NOT ACQUIRED
PRE-versus-historical row cross-check: PENDING
```

The successful raw and release-ledger evidence comes from the official annual historical compressed archive.

---

## 9. Remaining source states

### AQR original and maintained TSMOM workbooks

```text
Official page/locator: VERIFIED
Raw binary acquired: NO
Long-term immutable ingestion: NO
Factor audit: BLOCKED
```

### Moreira–Muir factor artifact

```text
Paper identity: VERIFIED
Author factor artifact acquired: NO
Empirical audit: NOT COMPLETE
```

### Licensed traditional futures and Chi et al.

```text
Required exact data: NOT ACQUIRED
Status: PENDING_LICENSE or INCONCLUSIVE_DATA_ACCESS
```

### Binance and OKX

```text
Official documentation/metadata: VERIFIED
Official pilot artifact ingested: NO
Constructive empirical experiment: NOT STARTED
```

---

## 10. Hypothesis verdicts

| Hypothesis | Implementation/data progress | Empirical status |
|---|---|---|
| `EDGE-FUT-TREND-001` | Audit mechanics ready; raw futures still licensed | `INCONCLUSIVE` |
| `EDGE-RISK-POLICY-001` | Recursive overlay mechanics ready | `INCONCLUSIVE` |
| `EDGE-FUT-CARRY-001` | Same-contract and roll mechanics ready | `INCONCLUSIVE` |
| `EDGE-FUT-POSITION-001` | Official raw artifact, dated pilot, and fail-closed scheduled-release ledger verified | `INCONCLUSIVE` |
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
cftc_release_ledger_construction: complete
cftc_scheduled_release_usage_for_data_engineering: true
cftc_conservative_availability_policy_testing: true
cftc_actual_release_time_claims: false
cftc_contract_to_instrument_mapping: true
licensed_price_linkage_planning: true

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
LOCAL HARDENED CHECKS: PASS
DEDICATED CFTC RAW ACQUISITION WORKFLOW: PASS
DEDICATED CFTC PILOT DERIVATION WORKFLOW: PASS
DEDICATED CFTC RELEASE-LEDGER WORKFLOW: PASS
RAW OFFICIAL CFTC ZIP ACQUISITION: CONFIRMED
RAW ZIP/MEMBER HASHES AND CRC: CONFIRMED
EXACT 87-FIELD PARSER CONTRACT: CONFIRMED
FULL-YEAR PROFILE: CONFIRMED
DATED 54-ROW PILOT: CONFIRMED
FAIL-CLOSED 52-ROW SCHEDULED-RELEASE LEDGER: CONFIRMED
ACTUAL HISTORICAL RELEASE TIMES: NOT VERIFIED
ACTIONS STAGING: CONFIRMED, RETENTION-LIMITED
LONG-TERM IMMUTABLE INGESTION: INCOMPLETE
PRE API CROSS-CHECK: INCOMPLETE
PAPER-LEVEL NUMERICAL REPLICATION: NOT COMPLETE
TRADING EDGE: NOT ESTABLISHED
ALL SIX HYPOTHESES: INCONCLUSIVE
REPORT 2.4: BLOCKED
```
