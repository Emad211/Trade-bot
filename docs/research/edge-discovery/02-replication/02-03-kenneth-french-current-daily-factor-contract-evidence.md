# Report 2.3I — Kenneth French Current Daily Factor Source Contract Evidence

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Hypothesis:** `EDGE-RISK-POLICY-001`  
**Evidence date:** 2026-07-19  
**Status:** `CURRENT_REVISED_DAILY_SOURCE_CONTRACT_VERIFIED; PAPER_VINTAGE_NOT_VERIFIED`

## 1. Decision

Three current daily factor archives were acquired directly from the official Kenneth French Data Library, parsed with an exact fail-closed contract, and assigned only to predeclared factor roles.

```text
Official Dartmouth ZIPs acquired: 3 / 3
ZIP integrity and safe extraction: pass
Exact source identities frozen: yes
Exact daily parser: verified
Adversarial tests: 13 passed
Return unit: PERCENT
Raw or row-level data published: no
Monthly factor returns calculated: no
Strategy performance calculated: no
Paper-vintage daily archives verified: no
Paper replication pass: no
Economic edge: not established
```

The sources are labeled:

```text
CURRENT_REVISED_PUBLIC_RECONSTRUCTION_SOURCE
```

They are not represented as the exact data vintage available to Moreira and Muir in the paper.

## 2. Official source and revision warning

Data Library:

```text
https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
```

Frozen page identity:

```text
Byte count: 245739
SHA-256: 436a8b99c1d1039b28f494756bbe5b79857a314251cc0b0e4d495fa229cd384e
```

The official page states that:

- CRSP Legacy Format `FIZ` was discontinued after the December 2024 release;
- Flat File Format 2.0 `CIZ` is used beginning with the January 2025 release;
- the full history of returns is reconstructed when portfolios are updated;
- historical returns may change after CRSP revisions.

Consequences:

```text
Current file ≠ paper historical vintage
Current file ≠ unrevised immutable time-series
Monthly archive availability ≠ verified daily archive availability
```

The current snapshot may support a revised public reconstruction, not an exact historical-vintage replication.

## 3. Frozen daily source identities

### 3.1 Fama/French 3 Factors daily

```text
URL:
https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/
F-F_Research_Data_Factors_daily_CSV.zip

ZIP byte count: 177699
ZIP SHA-256:
af8aec07d55c98caa15045a77b87455be68cb8847b2ee5bd03bf5c2c8a3f96e2

Member:
F-F_Research_Data_Factors_daily.csv

Member byte count: 1208053
Member SHA-256:
f051e37d30c129359c6801d9d2a715c929b19aa3be0ffe684b93995ede9ffebb
CRC32: 042c4b83

Rows: 26253
Dates: 1926-07-01 through 2026-05-29
Header: Date, Mkt-RF, SMB, HML, RF
Missing sentinels: 0
```

Selected roles:

```text
Mkt-RF
SMB
HML
RF
```

### 3.2 Fama/French 5 Factors daily

```text
URL:
https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/
F-F_Research_Data_5_Factors_2x3_daily_CSV.zip

ZIP byte count: 149700
ZIP SHA-256:
bcf32ecc9e2bb20383784ac98891e42146a0091eec6ec77d3b5bf0d4e981e3f6

Member:
F-F_Research_Data_5_Factors_2x3_daily.csv

Member byte count: 1013735
Member SHA-256:
8b6cf2992ccdc6086fc11b594b74ca8095843622deaee0602196b8deab0287b1
CRC32: 52b63b11

Rows: 15833
Dates: 1963-07-01 through 2026-05-29
Header: Date, Mkt-RF, SMB, HML, RMW, CMA, RF
Missing sentinels: 0
```

Selected roles:

```text
RMW
CMA
```

The FF5 versions of `Mkt-RF`, `SMB`, `HML`, and `RF` are not silently substituted for the FF3 definitions.

### 3.3 Momentum Factor daily

```text
URL:
https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/
F-F_Momentum_Factor_daily_CSV.zip

ZIP byte count: 89788
ZIP SHA-256:
f4237e2e36dffa13fd7823f55376316a94b5ac663af951dd9eaca8ed2c678bcf

Member:
F-F_Momentum_Factor_daily.csv

Member byte count: 427515
Member SHA-256:
3f396e1381861a65f7cd37c86483f163e17fb2516a2ad4d0f66a312d48a860b2
CRC32: 2e0f1b00

Rows: 26152
Dates: 1926-11-03 through 2026-05-29
Normalized header: Date, Mom
Missing sentinels: 0
```

The official Momentum CSV contains a trailing delimiter on the header, daily records, and footer lines. The parser removes at most one trailing empty CSV cell and continues to reject internal blank factor values.

```text
Trailing-delimiter line count: 26154
```

## 4. Predeclared factor-source mapping

```text
Mkt-RF <- FF3 daily Mkt-RF
SMB    <- FF3 daily SMB
HML    <- FF3 daily HML
RMW    <- FF5 daily RMW
CMA    <- FF5 daily CMA
Mom    <- Momentum daily Mom
RF     <- FF3 daily RF
```

This mapping follows the factor families described in the Moreira-Muir paper and prevents performance-driven switching between the FF3 and FF5 versions of shared factor names.

The selected combined daily panel spans:

```text
1926-07-01 through 2026-05-29
```

Coverage is factor-specific; outer-joining the panel does not invent pre-inception observations.

## 5. Permanent implementation

```text
src/hybrid_trader/replication/kenneth_french_daily.py
scripts/audit_kenneth_french_daily_sources.py
tests/test_kenneth_french_daily.py
.github/workflows/kenneth-french-daily-factor-contract-audit.yml
```

Permanent controls include:

- exact Data Library page hash and revision-warning phrases;
- exact ZIP byte counts and SHA-256 identities;
- exactly one safe ZIP member;
- ZIP traversal, encryption, size, CRC, and member-name checks;
- exact member hashes and schemas;
- sorted and unique daily dates;
- missing-sentinel handling;
- internal blank rejection;
- normalization of at most one official trailing delimiter;
- explicit percent unit;
- fixed factor-source mapping;
- current-revised data-state label;
- two independent evidence-writer executions with byte-for-byte comparison;
- closed gates for monthly aggregation, performance, recursive strategy, paper pass, and edge.

The permanent test suite contains 13 adversarial and contract tests.

## 6. Hosted verification

```text
Workflow:
Kenneth French Daily Factor Contract Audit

Run ID:
29699911713

Conclusion:
SUCCESS

Branch commit that triggered the trusted run:
d1568bf4c27236b0fe624ef5c5f7a2cae9d1c4b3

Pull-request merge-test commit recorded in the receipt:
fbdc674c8a73d32c7d89ab2e21395e42c8fa82cf
```

All permanent workflow steps passed:

- Ruff;
- strict mypy;
- 13 parser and contract tests;
- exact official acquisition;
- exact current-snapshot audit executed twice;
- byte-for-byte safe-output comparison;
- source mapping and closed-gate verification;
- raw-content deletion;
- safe artifact and receipt upload.

Failed and exploratory V1/V2/diagnostic workflows were retained long enough to identify the official Momentum trailing delimiter, then removed after the permanent audit passed.

## 7. Safe artifact evidence

```text
Safe contract artifact ID:
8446136292

Safe contract artifact digest:
9e662d91e0a3499d034c098ac1f05f1f13134372f7925bb0b7009a2040b2713d

Safe receipt artifact ID:
8446136497

Safe receipt artifact digest:
ef3ddf949f52d8db01367f621f314cfd32d5e7781cb41c5c66ef5e2a3d8589f3

Retention expiry:
2026-10-17
```

Internal safe files:

```text
safe-daily-factor-contract-evidence.json
Byte count: 5477
SHA-256: ebb0edb42f8e0de49da3cb75653d40c56ff969269042225344fd42832fe767f5

safe-daily-factor-contract-summary.json
Byte count: 1838
SHA-256: eb9c0cdd4cefb2d82ef02daa172d278a2dc1147e143f9d7283b6f1ecccd57580

kenneth-french-daily-contract-receipt.json
Byte count: 841
SHA-256: fb8812c300d2988ff453cd0694651c7d949aac9c5c91e2025741340565fc55da
```

Independent inspection confirmed that the safe artifact contains only the evidence and summary JSON files. It contains no ZIP, CSV, HTML, or row-level factor data.

Storage classification:

```text
ACTIONS_SAFE_EVIDENCE_ONLY_RETENTION_90_DAYS
```

This is not immutable retention of the official raw snapshots.

## 8. Separation from monthly factor returns

The Moreira-Muir paper uses:

- daily factor observations in month `t` to estimate realized variance;
- a separate monthly factor return in month `t+1` as the return being scaled.

Therefore the project will not silently compound daily returns and call the result the official monthly factor series. The monthly Kenneth French source files must be acquired and contracted separately.

## 9. Explicit non-claims

```text
Exact paper data vintage: not verified
Daily historical vintage archive: not verified
Monthly factor source contract: not yet verified
Daily-to-monthly reconciliation: not calculated
Realized-variance estimator convention: not yet identified
Scaling constant policy: not yet frozen
Managed return series: not constructed
Annualized performance: not calculated
Sharpe: not calculated
Alpha: not calculated
Transaction costs: not calculated
Recursive strategy: not constructed
Paper replication: not complete
Economic edge: not established
```

## 10. Next gate

The next gate must acquire the current official monthly FF3, FF5, and Momentum files and freeze:

1. monthly source identities and units;
2. the exact factor mapping;
3. current revised versus paper-vintage labels;
4. paper sample and modern-update windows;
5. the realized-variance convention candidates;
6. the retrospective full-sample normalization used for the published target;
7. a separate recursive no-lookahead normalization;
8. fixed leverage caps and cost scenarios;
9. opposing evidence, trial accounting, and kill criteria.

## 11. Final verdict

```text
OFFICIAL CURRENT DAILY SOURCES: CONFIRMED_3
EXACT ZIP AND MEMBER IDENTITIES: CONFIRMED
SAFE ZIP PARSER: CONFIRMED
PERCENT RETURN UNIT: CONFIRMED
FACTOR-SOURCE MAPPING: FROZEN
CURRENT-REVISED DATA LABEL: CONFIRMED
FIZ-TO-CIZ / REVISION WARNING: RETAINED
SAFE EVIDENCE DETERMINISM: PASS
RAW IMMUTABLE RETENTION: INCOMPLETE
PAPER DAILY VINTAGE: NOT VERIFIED
MONTHLY SOURCE CONTRACT: NOT YET VERIFIED
RECURSIVE POLICY: NOT STARTED
PAPER REPLICATION: NOT COMPLETE
ECONOMIC EDGE: NOT ESTABLISHED
EDGE-RISK-POLICY-001: INCONCLUSIVE
REPORT 2.4: BLOCKED
```
