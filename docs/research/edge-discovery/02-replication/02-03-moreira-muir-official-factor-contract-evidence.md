# Report 2.3H — Moreira-Muir Official Factor Snapshot and Scaling-Contract Evidence

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Hypothesis:** `EDGE-RISK-POLICY-001`  
**Evidence date:** 2026-07-19  
**Status:** `OFFICIAL_SNAPSHOT_AND_SCALING_CONTRACT_VERIFIED; PAPER_REPLICATION_NOT_COMPLETE`

## 1. Decision

The project acquired the current volatility-managed factor file directly from Tyler Muir's official author domain and verified its exact identity, schema, date continuity, missingness contract, percent-return unit, and managed-versus-unmanaged unconditional-volatility matching.

```text
Official author bytes acquired: yes
Exact source identity frozen: yes
Parser and adversarial tests: verified
Six managed/unmanaged pairs audited: yes
Predeclared volatility-match tolerance: 2.5%
Pairs within tolerance: 6 / 6
Raw or row-level data published: no
Annualized performance calculated: no
Sharpe calculated: no
Alpha calculated: no
Paper replication pass: no
Economic edge: not established
```

This milestone confirms the published data contract and one mechanical property claimed by the author page. It does not establish implementability, alpha, utility improvement, robustness, live tradability, or a genuine edge.

## 2. Official source identity

Author data page:

```text
https://tylersmuir.com/data.html
```

Official CSV:

```text
https://tylersmuir.com/data/VolManagedFactors.csv
```

Frozen snapshot:

```text
Snapshot ID:
MOREIRA_MUIR_VOL_MANAGED_FACTORS_2026_01_V1

CSV byte count:
113060

CSV SHA-256:
e9d92955e6ef2154aa55d05eed7b9237a313b987aad9afb0fdffd2103a81a6ba

Author-page byte count:
4783

Author-page SHA-256:
364b782f386b84f76039bc8d2d1814eced273b3f9d5505f0bd3a0d7af2d45633
```

The author page declares:

- monthly original and volatility-managed factor returns;
- returns expressed in percent;
- inverse-prior-month-realized-variance scaling;
- subsequent rescaling so that the managed factor has the same unconditional standard deviation as the original factor.

The project preserves the percent unit. No implicit division by 100 is allowed.

## 3. Exact schema and calendar contract

```text
Rows: 1189
Columns: 14
Frequency: monthly
First month: 1927-01
Last month: 2026-01
Duplicate months: 0
Missing calendar months: 0
```

Exact column order:

```text
Date
Mkt-RF_VM
SMB_VM
HML_VM
Mom_VM
RMW_VM
CMA_VM
Mkt-RF
SMB
HML
Mom
RMW
CMA
RF
```

Managed/unmanaged pairs:

```text
Mkt-RF_VM ↔ Mkt-RF
SMB_VM    ↔ SMB
HML_VM    ↔ HML
Mom_VM    ↔ Mom
RMW_VM    ↔ RMW
CMA_VM    ↔ CMA
```

Missingness contract:

```text
Mkt-RF / SMB / HML / Mom pairs:
0 missing rows

RMW pair:
439 leading missing rows
750 overlapping observations
1963-08 through 2026-01

CMA pair:
439 leading missing rows
750 overlapping observations
1963-08 through 2026-01

RF:
0 missing rows
```

The parser rejects paired missingness disagreement, internal missing gaps, unexpected late-start counts, duplicate months, calendar gaps, invalid dates, nonfinite values, unexpected columns, HTML responses, changed byte counts, and changed source hashes.

## 4. Volatility-scaling contract

The audit compares each managed series with its unmanaged counterpart over the exact common non-missing interval.

Predeclared gate:

```text
absolute(managed sample standard deviation / unmanaged sample standard deviation - 1)
≤ 0.025
```

The threshold was frozen before reading the pair results. All six pairs are retained and reported.

| Factor | Overlap | Managed SD (%) | Unmanaged SD (%) | Ratio | Relative error | Gate |
|---|---:|---:|---:|---:|---:|---|
| Mkt-RF | 1189 | 5.316163621550 | 5.316163387930 | 1.000000043945 | 0.000000043945 | Pass |
| SMB | 1189 | 3.157752694636 | 3.157752291497 | 1.000000127666 | 0.000000127666 | Pass |
| HML | 1189 | 3.561157915821 | 3.561157430844 | 1.000000136185 | 0.000000136185 | Pass |
| Mom | 1189 | 4.681737529301 | 4.681738807403 | 0.999999727003 | 0.000000272997 | Pass |
| RMW | 750 | 2.222240666903 | 2.222240492919 | 1.000000078292 | 0.000000078292 | Pass |
| CMA | 750 | 2.063563216400 | 2.063562152597 | 1.000000515518 | 0.000000515518 | Pass |

```text
Scaling gate:
VOLATILITY_SCALING_CONTRACT_MATCH

Maximum observed relative standard-deviation error:
0.000000515518
```

The maximum error is far below the predeclared 2.5% tolerance. This confirms that the distributed managed series are scaled to essentially the same unconditional sample volatility as their unmanaged counterparts over the available overlap.

This result does not test whether the scaling constant was available in real time. A maintained author file may use a full-sample unconditional normalization and is not automatically a prospective policy.

## 5. Permanent implementation

```text
src/hybrid_trader/replication/moreira_muir.py
scripts/audit_moreira_muir_official_factors.py
tests/test_moreira_muir.py
.github/workflows/moreira-muir-official-factor-contract-audit.yml
```

Permanent controls include:

- exact source byte count and SHA-256;
- exact schema and column order;
- canonical monthly dates;
- no duplicated or missing months;
- paired missingness and contiguous late-start validation;
- finite numeric values;
- explicit percent-return metadata;
- all-six-pair volatility matching;
- fail-closed changed-snapshot rejection;
- raw-content deletion before artifact upload;
- closed gates for performance, alpha, paper replication, and edge;
- safe floating metrics canonicalized to 12 decimal places.

After canonicalization, the test suite contains 12 adversarial and contract tests.

## 6. Hosted verification

Two independent clean-head executions passed all permanent steps:

```text
Run 1: 29698955657
Run 2: 29698976996
```

Each run passed:

- Python 3.11 setup;
- project dependency installation;
- repository Ruff rules;
- strict mypy;
- 12 parser and contract tests;
- exact official author-file acquisition;
- exact snapshot validation;
- six-pair scaling-contract audit;
- independent identity and closed-gate verification;
- raw-content removal;
- safe evidence and receipt upload.

A temporary determinism workflow also ran the evidence writer twice in independent Python processes and required byte-for-byte equality before committing the canonicalization. That temporary workflow was subsequently deleted.

## 7. Cross-run deterministic evidence

The ZIP containers have different digests because GitHub artifact archives include run-dependent ZIP metadata. The three files inside the safe evidence bundles are byte-identical across the two independent hosted runs:

```text
safe-factor-contract-evidence.json
Byte count: 5481
SHA-256: a254600f17ec665cede4a30a6dabb91d7664c3c420d7a338e0455d2765559ec6

safe-factor-contract-summary.json
Byte count: 520
SHA-256: 5c967101beca0066d7fb964dee945f88a48ee85983cff45d9c5308bc6affe8cf

safe-scaling-gate.json
Byte count: 924
SHA-256: 0f28fe871f757286fb2f774c70fd977da33b54a92466cd67bb0feefa5da3cce9
```

```text
Cross-run internal-file equality: PASS
```

## 8. Safe artifact evidence

Canonical clean-head run 2:

```text
Safe contract artifact ID:
8445875126

Safe contract artifact digest:
8ea6406e5949a0589ca5258f988913c264f32976808a5a7c83d722748d0ac47c

Safe receipt artifact ID:
8445875305

Safe receipt artifact digest:
ec0fa42adb61d90b55fc0305844bb7d3fdc81fc036b129bdc48688a90984489a

Retention expiry:
2026-10-17
```

Independent inspection confirmed that the safe contract artifact contains only the three JSON files listed above. It contains no author CSV, HTML page, response headers, or row-level return data.

Storage classification:

```text
ACTIONS_SAFE_EVIDENCE_ONLY_RETENTION_90_DAYS
```

This is not immutable retention of the official raw source.

## 9. Explicit non-claims

The following were intentionally not calculated or granted:

```text
Annualized mean or volatility comparison: not calculated
Sharpe ratio: not calculated
Alpha or appraisal ratio: not calculated
Optimal managed/unmanaged combination: not calculated
Turnover or implementation cost: not calculated
Crisis performance: not calculated
Utility improvement: not calculated
Recursive real-time policy: not constructed
Leverage cap sensitivity: not tested
Estimator sensitivity: not tested
Opposing evidence replication: not complete
Paper replication pass: not granted
Economic edge: not established
```

The author-provided managed returns are a published target series. They are not treated as a leakage-safe live policy merely because the file is public.

## 10. Next gate

The next gate is a frozen recursive real-time replication contract. It must specify before empirical calculation:

1. the public unmanaged factor source and exact data vintages;
2. daily observations used to estimate prior-month variance;
3. timing of factor availability;
4. recursive scaling estimation without full-sample leakage;
5. a leverage cap;
6. managed-only and optimal-combination benchmarks;
7. turnover and cost assumptions;
8. fixed estimator and cap sensitivity families;
9. crisis, utility, and appraisal-ratio targets;
10. the strongest opposing evidence and modern update;
11. trial-ledger consequences;
12. kill criteria.

## 11. Final verdict

```text
OFFICIAL AUTHOR SOURCE: CONFIRMED
EXACT SNAPSHOT IDENTITY: CONFIRMED
SCHEMA AND MONTHLY CALENDAR: CONFIRMED
PERCENT RETURN UNIT: CONFIRMED
MANAGED/UNMANAGED PAIRS: CONFIRMED_6
UNCONDITIONAL VOLATILITY-MATCH CONTRACT: PASS_6_OF_6
SAFE EVIDENCE DETERMINISM: PASS_ACROSS_2_HOSTED_RUNS
RAW SOURCE IMMUTABLE RETENTION: INCOMPLETE
RECURSIVE REAL-TIME REPLICATION: NOT STARTED
PAPER REPLICATION: NOT COMPLETE
ECONOMIC EDGE: NOT ESTABLISHED
EDGE-RISK-POLICY-001: INCONCLUSIVE
REPORT 2.4: BLOCKED
```
