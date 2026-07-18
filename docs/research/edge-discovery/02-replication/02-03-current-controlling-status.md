# Report 2.3 — Current Controlling Status

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Report:** 3 of 5  
**Status date:** 2026-07-18  
**Status:** `PARTIALLY_COMPLETE — IMPLEMENTATION_INDEPENDENTLY_REVERIFIED; OFFICIAL EMPIRICAL ARTIFACTS PENDING`

This document is the controlling status for Report 2.3. It supersedes older execution counts, static-analysis states, generic `PASS` wording, and source-access labels in the initial execution snapshot when they conflict.

The original execution snapshot is retained for audit history:

- [Initial controlled execution report](02-03-controlled-empirical-and-code-replication.md)

The detailed verification evidence is retained separately:

- [Independent reality verification and corrections](02-03-independent-reality-verification-log.md)
- [Static analysis, tests, and coverage](02-03-static-analysis-and-test-verification.md)
- [Machine-readable execution manifest](02-03-replication-execution-manifest.yaml)

---

## Verified repository work

```text
Repository: Emad211/Trade-bot
Branch: agent/edge-research-reports
Repository and branch through authenticated GitHub connector: CONFIRMED
Original committed source independently reconstructed: CONFIRMED
```

A direct clone from the isolated compute container was blocked by container DNS. That failure is not treated as repository evidence because the authenticated GitHub connector returned the branch, commits, file contents, and compare state.

---

## Defect discovered and corrected

The initial `run_aqr_vintage_audit` could return a generic `PASS` after parsing any two local files. It did not require evidence that the files came from the official source or had been immutably ingested.

That was a real over-permission defect.

The hardened implementation now requires the following before `ARTIFACT_AUDIT_PASS`:

```text
official source identity
IMMUTABLE_INGESTED provenance state
matching SHA-256
matching byte count
retrieval time
license snapshot
immutable storage key
explicit return unit
```

Unverified local files receive at most:

```text
IMPLEMENTATION_READY
```

`ARTIFACT_AUDIT_PASS` remains a processed-artifact audit. It is not a raw paper replication, opposing-evidence pass, economic-edge verdict, or deployment authorization.

---

## Independently executed local verification

The original fixture suite was reconstructed from authenticated GitHub commit content and rerun:

```text
11 tests passed
compileall passed
```

After provenance and verdict hardening, the final local verification was:

```text
Ruff under repository rules: PASS
Mypy strict: PASS for 9 replication source files
Pytest: 15 passed
Statement coverage of hybrid_trader.replication: 85.44%
Required coverage threshold: 80%
Compileall: PASS
```

The tests use deterministic synthetic fixtures. They establish only the tested implementation invariants.

They do not establish:

- a published table;
- a paper result;
- profitability;
- an economic edge;
- production exchange safety.

---

## GitHub-hosted CI

A workflow exists at:

```text
.github/workflows/replication-integrity.yml
```

At the controlling-status cutoff:

```text
WORKFLOW FILE: COMMITTED
WORKFLOW RUN OBSERVED: NO
COMBINED STATUS: EMPTY
GITHUB-HOSTED CI VERDICT: UNVERIFIED
```

A local pass is not represented as a hosted CI pass.

---

## Corrected official-source states

### AQR original and maintained TSMOM workbooks

```text
OFFICIAL PAGE/LOCATOR: VERIFIED
RAW BINARY ACQUIRED: NO
IMMUTABLE INGESTION: NO
ARTIFACT AUDIT: BLOCKED
```

### Moreira–Muir factor artifact

```text
PAPER IDENTITY: VERIFIED
AUTHOR FACTOR ARTIFACT ACQUIRED: NO
EMPIRICAL AUDIT: NOT COMPLETE
```

### CFTC TFF Futures Only

```text
DATASET ID: gpe5-46if
OFFICIAL DATASET PAGE: VERIFIED
OFFICIAL STRUCTURED API RESPONSE: OBSERVED
RAW RESPONSE BYTES PERSISTED: NO
SHA-256 RECORDED IN IMMUTABLE STORAGE: NO
STATUS: API_REACHABLE_RAW_INGESTION_PENDING
```

API reachability does not count as raw acquisition or immutable ingestion.

### CFTC Legacy and Disaggregated

```text
OFFICIAL METADATA: VERIFIED
IMMUTABLE RAW INGESTION: PENDING
COMPRESSED-FILE CROSS-CHECK: NOT COMPLETE
```

### Binance and OKX

```text
OFFICIAL DOCUMENTATION/METADATA: VERIFIED
PILOT ARCHIVE/API ARTIFACT IMMUTABLY INGESTED: NO
CONSTRUCTIVE EMPIRICAL EXPERIMENT: NOT STARTED
```

### Licensed traditional futures and Chi et al.

```text
REQUIRED EXACT SOURCE DATA: NOT ACQUIRED
STATUS: PENDING_LICENSE or INCONCLUSIVE_DATA_ACCESS
```

---

## Hypothesis verdicts

| Hypothesis | Implementation status | Empirical status |
|---|---|---|
| `EDGE-FUT-TREND-001` | Audit mechanics ready | `INCONCLUSIVE` |
| `EDGE-RISK-POLICY-001` | Recursive overlay mechanics ready | `INCONCLUSIVE` |
| `EDGE-FUT-CARRY-001` | Same-contract and roll mechanics ready | `INCONCLUSIVE` |
| `EDGE-FUT-POSITION-001` | Release-time mechanics ready | `INCONCLUSIVE` |
| `EDGE-CRYPTO-BASIS-001` | Instrument-version and basis mechanics ready | `INCONCLUSIVE` |
| `EDGE-CRYPTO-RV-001` | Linear two-leg accounting ready | `INCONCLUSIVE` |

No hypothesis has an economic pass.

---

## Controlling authorization

```yaml
implementation: true
unit_testing: true
formula_validation: true
official_data_acquisition: true

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

## Final controlling verdict

```text
REAL REPOSITORY WORK: CONFIRMED
REAL COMMITTED IMPLEMENTATION: CONFIRMED
INDEPENDENT TEST RERUN: CONFIRMED
OVER-PERMISSIVE VERDICT DEFECT: FOUND AND CORRECTED
LOCAL RUFF/MYPY/PYTEST/COVERAGE: PASS
GITHUB-HOSTED CI: UNVERIFIED
OFFICIAL IMMUTABLE ARTIFACT INGESTION: INCOMPLETE
PAPER-LEVEL NUMERICAL REPLICATION: NOT COMPLETE
TRADING EDGE: NOT ESTABLISHED
ALL SIX HYPOTHESES: INCONCLUSIVE
REPORT 2.4: BLOCKED
```
