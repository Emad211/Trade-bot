# Report 2.3A — Independent Reality Verification and Corrections

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Parent:** [Report 2.3](02-03-controlled-empirical-and-code-replication.md)  
**Verification date:** 2026-07-18  
**Status:** Complete for the checks explicitly listed below  
**Purpose:** Independently verify that the repository changes, tests, source-access claims, and reported limitations are real; correct any claim that is broader than the available evidence.

---

# 1. Verification standard

This log uses the following evidence levels.

| Level | Meaning |
|---|---|
| `COMMIT_CONFIRMED` | GitHub returned the branch, commit, path, and committed content through the authenticated repository connector |
| `CODE_RECONSTRUCTED` | The exact committed source was reconstructed outside the repository from GitHub commit content |
| `TEST_RERUN` | Tests were executed again in a separate temporary environment |
| `OFFICIAL_PAGE_VERIFIED` | The official publisher, regulator, exchange, or repository page was reached |
| `API_REACHABLE` | An official API endpoint returned structured data |
| `RAW_ARTIFACT_ACQUIRED` | Raw bytes were downloaded and a byte count and SHA-256 were recorded |
| `IMMUTABLE_INGESTED` | Raw bytes, license snapshot, retrieval time, checksum, and immutable storage key were recorded |
| `EMPIRICALLY_REPLICATED` | A paper-specific table or result was reconstructed from the required source artifact |

No lower level inherits the meaning of a higher level.

In particular:

- a commit is not a passing test;
- a passing synthetic test is not a paper replication;
- an official webpage is not a downloaded artifact;
- a reachable API is not immutable ingestion;
- a parsed workbook is not proof that the workbook came from the official source;
- an artifact audit is not an economic edge verdict.

---

# 2. Repository and branch verification

The repository connector independently confirmed:

```text
repository: Emad211/Trade-bot
branch: agent/edge-research-reports
comparison base: main
status: diverged
ahead_by at verification start: 36
behind_by at verification start: 1
```

The comparison returned the expected research reports, manifests, replication package, and test files.

Verdict:

```text
REPOSITORY: CONFIRMED
BRANCH: CONFIRMED
RESEARCH FILES: CONFIRMED
```

A direct `git clone` was also attempted in the isolated compute container. It failed because that container could not resolve `github.com`. This is recorded as:

```text
DIRECT_CLONE: BLOCKED_BY_CONTAINER_DNS
```

It is not interpreted as evidence that the repository or branch is absent, because the authenticated GitHub connector independently returned the branch and committed objects.

---

# 3. Independent reconstruction of the committed implementation

The following committed modules were reconstructed from GitHub commit content in a new temporary directory:

```text
src/hybrid_trader/replication/
├── __init__.py
├── factor_audit.py
├── futures.py
├── cftc.py
├── crypto.py
└── verdicts.py
```

The following committed tests were reconstructed separately:

```text
tests/
├── test_replication_factor_audit.py
├── test_replication_futures.py
├── test_replication_cftc.py
└── test_replication_crypto.py
```

For the files whose SHA-256 values were recorded in the Report 2.3 execution manifest, the independently reconstructed bytes matched the recorded SHA-256 values. Examples:

| File | Independently calculated SHA-256 | Existing manifest match |
|---|---|---|
| `artifacts.py` before hardening | `f85f25b24e11b12b1ec5f8f88dc6006a62eb51b7f106ace3acd46bfd38e0175d` | Yes |
| `runner.py` before hardening | `edf37d98bca49292336e0542eec9f75730b8e8971b046b7588d7801564a42485` | Yes |
| `verdicts.py` before hardening | `47b51ecc050092e89049a03d65bc09e163ec6ff5343de32195796b0e915ddb8f` | Yes |

This establishes that the rerun used the same source bytes represented by the commits, rather than a newly invented approximation.

---

# 4. Independent test rerun

## 4.1 Original committed test set

Environment:

```text
Python 3.13.5
pandas 2.2.3
numpy 2.3.5
pydantic 2.13.4
pytest 9.0.2
```

Command:

```bash
PYTHONPATH=/tmp/replication-audit/src \
python -m pytest -q /tmp/replication-audit/tests
```

Independent result before provenance hardening:

```text
...........                                                              [100%]
11 passed in 0.13s
```

Compilation result:

```text
python -m compileall -q src tests
PASS
```

This independently confirms the original claim that the committed invariant tests pass on controlled synthetic fixtures.

It does not confirm a paper result.

## 4.2 Hardened provenance test set

The audit found that the original `run_aqr_vintage_audit` could return `PASS` after parsing any two local files. It calculated hashes, but it did not require proof that the files were the official artifacts or that they had been immutably ingested.

This was a real over-permission defect.

The implementation was hardened by adding:

- effective source-access states;
- immutable artifact provenance;
- required SHA-256, byte count, retrieval time, license snapshot, and storage key;
- local-file checksum verification;
- explicit factor return units;
- a distinct `ARTIFACT_AUDIT_PASS` status;
- prohibition on granting an artifact pass to unverified local files.

Four new tests were added:

1. unverified local files cannot receive an artifact pass;
2. immutable official files with matching provenance can receive `ARTIFACT_AUDIT_PASS`;
3. a mismatched checksum is rejected;
4. immutable status without license and storage evidence is rejected.

Independent hardened result:

```text
...............                                                          [100%]
15 passed in 0.14s
```

Compilation result:

```text
PASS
```

`ruff` and `mypy` were not installed in the isolated container. No claim of a Ruff or mypy pass is made.

GitHub Actions did not report a status check for the branch at this verification point. No claim of a CI pass is made.

---

# 5. Correction to the factor-audit verdict model

## 5.1 Previous behavior

The previous runner used:

```text
status = PASS
reason = official original and maintained artifacts parsed and compared
```

after receiving two local paths.

The code could not independently establish that those paths came from the official publisher.

## 5.2 Corrected behavior

The corrected runner distinguishes:

```text
UNVERIFIED_LOCAL_FACTOR_AUDIT
IMPLEMENTATION_READY
ARTIFACT_AUDIT_PASS
```

`ARTIFACT_AUDIT_PASS` requires all of the following:

```text
both provenance objects exist
both access states are IMMUTABLE_INGESTED
both local byte counts match
both local SHA-256 values match
both license snapshots exist
both immutable storage keys exist
return units are explicitly declared
```

Even `ARTIFACT_AUDIT_PASS` is only a processed-factor artifact audit. It is not:

- raw 58-instrument reconstruction;
- reproduction of every paper table;
- survival of opposing tests;
- evidence of a live edge.

---

# 6. Official-source verification results

## 6.1 AQR Time Series Momentum

Verified:

- the official AQR original-paper dataset page exists;
- the page identifies the original Time Series Momentum dataset;
- the page states that the study uses 58 instruments and the January 1985 through December 2009 sample;
- the official workbook locator is exposed by the page.

Not achieved:

- workbook bytes were not successfully downloaded into controlled storage;
- no byte count or SHA-256 was recorded;
- no license snapshot was attached to raw bytes;
- no workbook table was empirically audited.

Status:

```text
OFFICIAL_PAGE_VERIFIED
RAW_ARTIFACT_ACQUIRED = false
IMMUTABLE_INGESTED = false
EMPIRICALLY_REPLICATED = false
```

## 6.2 CFTC TFF Futures Only

Verified:

- the official CFTC dataset page exists;
- dataset identifier `gpe5-46if` is correct;
- the official raw JSON resource endpoint returned structured TFF Futures Only records;
- returned rows include report dates, market codes, position categories, open interest, and `FutOnly` classification.

Not achieved:

- the raw HTTP response bytes were not persisted by the isolated environment;
- no response checksum was recorded in immutable storage;
- the API output was not cross-checked against an official compressed historical file;
- no complete exceptional-release ledger was attached.

Corrected status:

```text
API_REACHABLE
RAW_ARTIFACT_ACQUIRED = false
IMMUTABLE_INGESTED = false
```

The earlier label `BLOCKED_BY_SOURCE_ACCESS` was too broad for this endpoint. The correct label is:

```text
API_REACHABLE_RAW_INGESTION_PENDING
```

This correction does not grant an empirical positioning verdict.

## 6.3 CFTC Legacy and Disaggregated

Verified:

- official dataset pages and identifiers exist;
- report families are distinct;
- official pages expose API/OData access mechanisms.

Not achieved in this verification:

- immutable raw acquisition;
- compressed-file cross-check;
- full release-history reconstruction.

Status:

```text
METADATA_VERIFIED_RAW_INGESTION_PENDING
```

## 6.4 Binance public market data

Verified:

- the official public-data repository exists;
- the official archive is documented;
- checksum sidecar files are part of the archive contract;
- the official repository documents timestamp-unit changes and archive update history.

Not achieved:

- no archive ZIP was successfully persisted in controlled storage;
- no checksum sidecar was acquired and compared;
- no pilot interval was parsed.

Status:

```text
OFFICIAL_METADATA_VERIFIED
RAW_ARTIFACT_ACQUIRED = false
```

## 6.5 OKX

Verified:

- official API documentation exists;
- the project has documented the need to retain mark, index, funding, instrument, and candle-confirmation semantics separately.

Not achieved:

- no official pilot archive or API response was immutably ingested during this verification.

Status:

```text
OFFICIAL_DOCUMENTATION_VERIFIED
RAW_ARTIFACT_ACQUIRED = false
```

---

# 7. Claims that remain valid

The following claims were independently supported:

1. the branch and committed files exist;
2. the original 11 synthetic invariant tests pass when independently reconstructed;
3. compilation passes for the reconstructed package and tests;
4. same-contract return logic excludes a cross-contract roll gap in the tested fixture;
5. the CFTC timing code uses Friday 15:30 Eastern as a normal baseline and supports explicit overrides;
6. the volatility overlay uses lagged variance in the tested fixture;
7. the linear two-leg accounting subtracts declared costs in the tested fixture;
8. all six economic hypotheses remain empirically inconclusive;
9. no paper trading, live trading, leverage, or capital deployment is authorized.

---

# 8. Claims that are not established

The following are not established and must not be stated as completed:

- numerical reproduction of Moskowitz–Ooi–Pedersen;
- numerical reproduction of Moreira–Muir;
- numerical reproduction of Szymanowska, Boons–Prado, or Fan et al.;
- exact reproduction of Chi et al.;
- profitability of crypto relative value after real fills;
- complete historical CFTC release timing;
- a production-ready exchange accounting engine;
- a CI pass;
- an economic edge in any of the six hypotheses.

---

# 9. Current evidence-state summary

```text
GITHUB BRANCH AND COMMITS: CONFIRMED
ORIGINAL SYNTHETIC TEST RERUN: 11 PASS
HARDENED SYNTHETIC TEST RERUN: 15 PASS
COMPILEALL: PASS
RUFF: NOT RUN
MYPY: NOT RUN
GITHUB CI: NO STATUS REPORTED
AQR RAW WORKBOOKS: NOT ACQUIRED
CFTC TFF API: REACHABLE
CFTC TFF IMMUTABLE RAW INGESTION: PENDING
BINANCE PILOT ARCHIVE: NOT ACQUIRED
OKX PILOT DATA: NOT ACQUIRED
LICENSED FUTURES DATA: PENDING
PAPER-LEVEL NUMERICAL REPLICATION: NOT COMPLETE
ECONOMIC EDGE VERDICT: INCONCLUSIVE FOR ALL SIX
REPORT 2.4 FULL AUTHORIZATION: FALSE
```

---

# 10. Binding corrections

1. `PASS` is no longer used for a local factor-file parse.
2. `ARTIFACT_AUDIT_PASS` is distinct from an empirical paper pass.
3. Immutable official provenance is required for an artifact audit pass.
4. Return scale must be declared as decimal or percent.
5. Checksum mismatch is a hard failure.
6. TFF official API status is corrected to `API_REACHABLE_RAW_INGESTION_PENDING`.
7. API reachability does not count as raw acquisition.
8. Raw acquisition does not count as immutable ingestion.
9. Synthetic tests remain implementation evidence only.
10. Report 2.4 remains blocked.

---

# Final verification verdict

```text
REAL REPOSITORY WORK: CONFIRMED
REAL COMMITTED IMPLEMENTATION: CONFIRMED
INDEPENDENT TEST RERUN: CONFIRMED
OVER-PERMISSIVE VERDICT DEFECT: FOUND AND CORRECTED
OFFICIAL SOURCE METADATA: PARTIALLY VERIFIED
OFFICIAL RAW ARTIFACT INGESTION: NOT COMPLETE
PAPER REPLICATION: NOT COMPLETE
TRADING EDGE: NOT ESTABLISHED
```
