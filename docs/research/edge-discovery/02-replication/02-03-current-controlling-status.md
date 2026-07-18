# Report 2.3 — Current Controlling Status

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Report:** 3 of 5  
**Status date:** 2026-07-18  
**Status:** `PARTIALLY_COMPLETE — FIRST OFFICIAL RAW ARTIFACT ACQUIRED; FIRST DATED PILOT DERIVED; REMAINING REPLICATION GATES OPEN`

This document is the controlling status for Report 2.3. It supersedes older execution counts, source states, generic `PASS` wording, and CI descriptions in the initial execution snapshot when they conflict.

Historical and detailed evidence is retained in:

- [Initial controlled execution report](02-03-controlled-empirical-and-code-replication.md)
- [Independent reality verification and corrections](02-03-independent-reality-verification-log.md)
- [Static analysis, tests, and coverage](02-03-static-analysis-and-test-verification.md)
- [Verified CFTC TFF acquisition and pilot evidence](02-03-cftc-tff-2022-acquisition-and-pilot-evidence.md)
- [Machine-readable CFTC TFF evidence](02-03-cftc-tff-2022-evidence.yaml)
- [Machine-readable execution manifest](02-03-replication-execution-manifest.yaml)

---

## 1. Verified repository and implementation state

```text
Repository: Emad211/Trade-bot
Branch: agent/edge-research-reports
Draft PR: #41
Repository and branch through authenticated GitHub connector: CONFIRMED
Original committed replication source independently reconstructed: CONFIRMED
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

The newly acquired CFTC artifact is staged in retention-limited GitHub Actions storage. It is therefore not yet `IMMUTABLE_INGESTED` and does not receive `ARTIFACT_AUDIT_PASS`.

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

The dedicated CFTC workflows now provide additional real GitHub-hosted evidence.

### Official annual ZIP acquisition workflow

```text
Workflow: CFTC TFF Historical 2022 Ingestion
Run ID: 29655608183
Conclusion: SUCCESS
```

The workflow passed:

- Ruff;
- strict mypy;
- ingestion tests;
- official ZIP acquisition;
- ZIP CRC and member-hash verification;
- raw-bundle upload;
- staging-receipt upload.

### End-to-end parser and dated-pilot workflow

```text
Workflow: CFTC TFF 2022 Pilot Derivation
Run ID: 29656055991
Conclusion: SUCCESS
```

The workflow passed:

- Ruff;
- strict mypy;
- eight combined ingestion/parser tests;
- official ZIP acquisition;
- exact archive and member identity checks;
- exact schema verification;
- full-year parsing and diagnostics;
- deterministic `2022-09-13` pilot derivation;
- independent raw/member/schema/profile/pilot checks;
- raw-plus-derived artifact upload;
- receipt upload.

The repository-wide legacy `ci` and `Replication Integrity` workflows are not green on this research branch. Their failures are not reclassified as passes. The claims above apply only to the dedicated CFTC workflows and the already recorded local verification scope.

---

## 3. First verified official raw acquisition

The first real official artifact is:

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

ZIP validation:

```text
CRC: PASS
Non-directory member count: 1
Text member: FinFutYY.txt
Member byte count: 2105659
Member CRC32: 7c783c41
Member SHA-256:
7c309cb76da8bf432e1a347e5bfde169bcac31cec4e9e33742cf3a078328bb3b
```

These values were computed in GitHub Actions and independently recomputed after downloading the Actions artifact.

---

## 4. Retention-limited Actions staging

### Initial raw bundle

```text
Run ID: 29655608183
Artifact ID: 8432769852
Artifact digest:
d718393c4984a63be874ed72b4dcc0b2173f29717e4339d02b83e1f9ed614270
Expiry: 2026-10-16
```

### End-to-end raw and derived bundle

```text
Run ID: 29656055991
Artifact ID: 8432902155
Artifact digest:
391a7bc682f02e0feec735342b33ae6a63a59c0db9432ee9812e4ebe17c83184
Expiry: 2026-10-16
```

### Derivation receipt

```text
Artifact ID: 8432902321
Artifact digest:
49cbd8b7d2863e915291468652dc7cfecdac28364723cde40a29aa5d1fbb773c
```

Current storage classification:

```text
ACTIONS_ARTIFACT_STAGED_RETENTION_90_DAYS
```

GitHub Actions artifacts are deletable and expire. Long-term immutable storage remains incomplete.

---

## 5. Exact parser contract and annual findings

The parser is bound to the exact acquired archive and member hashes.

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

The full-year accounting diagnostic found:

```text
Long exact-reconciliation differences: 37
Short exact-reconciliation differences: 33
Rows with accepted consolidated unit differences: 56
Material accounting failures: 0
```

Every difference was exactly one contract in magnitude and confined to consolidated market rows whose contract-market code ends in `+` and whose market name identifies the row as consolidated.

Observed consolidated codes:

- `12460+` — DJIA Consolidated;
- `13874+` — S&P 500 Consolidated;
- `20974+` — NASDAQ-100 Consolidated.

These differences are recorded, not erased. The artifact-specific parser accepts them only as nonmaterial unit reconciliation differences. This rule does not automatically transfer to another year or revised artifact.

---

## 6. First deterministic dated pilot

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

Derived file:

```text
tff_futures_only_2022-09-13.canonical.csv

Byte count: 27954

SHA-256:
1be0028ba872ed56c970f6cd67b76c480b3653b170762c6e55f39dc10c3d268b
```

The pilot preserves all 87 source fields and is deterministically sorted by stripped `CFTC_Contract_Market_Code`.

The pilot hash was independently verified:

1. during derivation;
2. in a separate workflow verification step;
3. after downloading the Actions artifact outside the runner.

---

## 7. CFTC PRE API state

The Public Reporting Environment dataset identity `gpe5-46if` is verified. The endpoint returned structured data in some contexts, but repeated GitHub-hosted acquisition attempts produced persistent HTTP 503 responses.

Current PRE classification:

```text
API identity: VERIFIED
GitHub-runner reliability: FAILED_REPEATED_HTTP_503
Immutable PRE raw artifact: NOT ACQUIRED
PRE-versus-historical row cross-check: PENDING
```

The successful evidence comes from the official annual historical compressed archive, not from the unreliable PRE workflow.

The PRE workflow is not considered a passing PR gate.

---

## 8. Remaining official-source states

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

## 9. Hypothesis verdicts

| Hypothesis | Implementation/data progress | Empirical status |
|---|---|---|
| `EDGE-FUT-TREND-001` | Audit mechanics ready; raw futures still licensed | `INCONCLUSIVE` |
| `EDGE-RISK-POLICY-001` | Recursive overlay mechanics ready | `INCONCLUSIVE` |
| `EDGE-FUT-CARRY-001` | Same-contract and roll mechanics ready | `INCONCLUSIVE` |
| `EDGE-FUT-POSITION-001` | First official CFTC raw artifact and dated pilot acquired/derived | `INCONCLUSIVE` |
| `EDGE-CRYPTO-BASIS-001` | Instrument-version and basis mechanics ready | `INCONCLUSIVE` |
| `EDGE-CRYPTO-RV-001` | Linear two-leg accounting ready | `INCONCLUSIVE` |

No hypothesis has an economic pass.

---

## 10. Controlling authorization

```yaml
implementation: true
unit_testing: true
formula_validation: true
official_data_acquisition: true
cftc_release_ledger_construction: true
cftc_additional_year_versioning: true
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

## 11. Final controlling verdict

```text
REAL REPOSITORY WORK: CONFIRMED
REAL COMMITTED IMPLEMENTATION: CONFIRMED
LOCAL HARDENED CHECKS: PASS
DEDICATED CFTC RAW ACQUISITION WORKFLOW: PASS
DEDICATED CFTC END-TO-END PILOT WORKFLOW: PASS
RAW OFFICIAL CFTC ZIP ACQUISITION: CONFIRMED
RAW ZIP/MEMBER HASHES AND CRC: CONFIRMED
EXACT 87-FIELD PARSER CONTRACT: CONFIRMED
FULL-YEAR PROFILE: CONFIRMED
DATED 54-ROW PILOT: CONFIRMED
PILOT SHA-256: CONFIRMED
ACTIONS STAGING: CONFIRMED, RETENTION-LIMITED
LONG-TERM IMMUTABLE INGESTION: INCOMPLETE
PRE API CROSS-CHECK: INCOMPLETE
PAPER-LEVEL NUMERICAL REPLICATION: NOT COMPLETE
TRADING EDGE: NOT ESTABLISHED
ALL SIX HYPOTHESES: INCONCLUSIVE
REPORT 2.4: BLOCKED
```
