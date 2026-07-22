# Report 2.3H — Verified Public Cboe VX Contract-Level Pilot Evidence

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Parent:** [Owner-accessible exchange-native source pivot](02-03-owner-accessible-exchange-native-source-pivot.md)  
**Issue:** `#43`  
**Evidence date:** 2026-07-19  
**Status:** `CONTRACT_LEVEL_ACQUISITION_AND_PARSER_VERIFIED; RAW_RETENTION_AND_PRICE_LINKAGE_BLOCKED`

---

## 1. Decision

The project has completed a bounded, owner-accessible, exchange-native engineering pilot for Cboe Futures Exchange VIX futures (`VX`).

The pilot verifies:

- direct retrieval from official Cboe contract-level URLs;
- exact byte and SHA-256 identities for two monthly contracts;
- explicit contract-month identities and expiration dates;
- an exact eleven-field source schema;
- separate `Close` and `Settle` fields;
- exact settlement-change reconciliation within the frozen tolerance;
- deterministic contract-level pilot derivation;
- absence of continuous or back-adjusted series construction;
- fail-closed handling of source changes, duplicate dates, wrong contract identity, HTML responses, and settlement inconsistencies.

The pilot does **not** authorize:

- redistribution or public redisplay of raw Cboe content;
- long-term raw retention;
- assignment of Cboe prices to the canonical CFTC registry;
- computation of returns;
- signal fitting;
- paper-level replication;
- an economic-edge verdict.

The controlling empirical status of `EDGE-FUT-POSITION-001` remains `INCONCLUSIVE`.

---

## 2. Negative result retained: historical daily-settlement endpoint

The initial official date-parameterized settlement endpoint was tested for `2022-09-16`.

```text
Response byte count:
38

SHA-256:
fb3907637b20ec51927e44bd0c06628cc47fb9cde8f317c743131a779dbaf39d

Header:
Product,Symbol,Expiration Date,Price

Data rows:
0
```

The endpoint was reachable and returned CSV bytes, but it did not return historical settlement rows for the requested 2022 date. It is therefore rejected as the source for this historical pilot.

Quarantine evidence:

```text
Workflow run:
29696287344

Artifact ID:
8445088746

Artifact digest:
9336393ff70e79b78dfafdbb97ec3c59ea41991923117ed3726d223547c2a42b

Retention expiry:
2026-10-17
```

This negative result remains part of the audit trail. The exploratory workflow that could re-upload raw data was subsequently removed.

---

## 3. Official contract-level source route

The successful route uses one official Cboe file per expiring contract. The URL identity is based on the contract expiration date rather than a continuous-series symbol.

### September 2022 monthly VX contract

```text
Filename:
VX_2022-09-21.csv

Contract identity:
U (Sep 2022)

Expiration / last source date:
2022-09-21

Raw byte count:
15819

Raw SHA-256:
a74598b17c5e92b068ee46ee38aefdfe8423d62153bee7d879ff4eddc2fbb626

Source rows:
186

First source date:
2021-12-27
```

### October 2022 monthly VX contract

```text
Filename:
VX_2022-10-19.csv

Contract identity:
V (Oct 2022)

Expiration / last source date:
2022-10-19

Raw byte count:
15850

Raw SHA-256:
270abe0333366e5395d88d6e56da51fa403962f03229d119a8208ece339c778d

Source rows:
187

First source date:
2022-01-24
```

The permanent parser rejects either file if its byte count or SHA-256 changes. A provider replacement must create a new evidence version rather than silently inheriting this verdict.

---

## 4. Exact source schema

The verified source fields are:

```text
Trade Date
Futures
Open
High
Low
Close
Settle
Change
Total Volume
EFP
Open Interest
```

Schema fingerprint:

```text
7ec53b473b1418928b26414f98e433de7886cf501fedc56a31e70a7a913af3f2
```

The source exposes both `Close` and `Settle`. The parser preserves both fields and never substitutes one for the other.

Across the complete two source files, numeric `Settle` differs from numeric `Close` on:

```text
September contract:
182 rows

October contract:
182 rows

Total:
364 rows
```

This demonstrates that a close-price substitution would materially alter the source semantics.

---

## 5. Parser contract

Permanent implementation:

```text
src/hybrid_trader/replication/cboe_vx_public.py
scripts/build_cboe_vx_public_contract_pilot.py
tests/test_cboe_vx_public.py
.github/workflows/cboe-vx-public-contract-pilot.yml
```

The parser hard-rejects:

- empty responses;
- HTML returned in place of CSV;
- byte-count changes;
- SHA-256 changes;
- schema changes;
- empty contract files;
- invalid dates;
- non-monotonic dates;
- duplicate dates;
- wrong contract identity;
- expiration mismatch;
- invalid or non-positive settlement values;
- invalid numerical fields;
- negative volume, EFP, or open interest;
- inconsistency between `Change` and the change in `Settle` beyond `0.0001`.

Date ordering and duplicate detection occur before settlement-delta validation so that malformed temporal identity receives the correct failure classification.

---

## 6. Deterministic pilot identity

Frozen window:

```text
2022-09-01 through 2022-09-30
```

Pilot output identity:

```text
Pilot version:
CBOE_VX_PUBLIC_CONTRACT_LEVEL_PILOT_V1

Contract count:
2

Rows:
35

September-contract rows:
14

October-contract rows:
21

First pilot date:
2022-09-01

Last pilot date:
2022-09-30
```

Deterministic CSV identity:

```text
Byte count:
12340

SHA-256:
ebe1326a06bc7c11a96e4ca2d489ddba74c73965653991017a958e6ce6f13ad0
```

Deterministic manifest identity:

```text
Byte count:
2153

SHA-256:
6b04d359de6030f11dcdc49cd8c1a401448879f472dbcf0b3d172e5d905f6b34
```

The pilot retains separate rows for each contract and each trade date. It does not splice contracts into a continuous history, apply a roll adjustment, or create executable PnL.

Every derived row retains:

```text
continuous_series: false
back_adjusted: false
settlement_is_explicit_exchange_field: true
price_linkage_authorized: false
returns_authorized: false
```

---

## 7. Local verification

The final local implementation passed:

```text
Pytest:
8 passed

Compileall:
PASS
```

Ruff and strict mypy were not available in the isolated local environment and were therefore not claimed locally. They were executed in the hosted workflow described below.

---

## 8. Permanent hosted verification

```text
Workflow:
Cboe VX Public Contract Pilot

Run ID:
29696828324

Conclusion:
SUCCESS

Branch commit that triggered the run:
6fc082c5e8465a695cd95db3e763e2545a554b43

Pull-request merge-test commit recorded in the receipt:
20d6a59b707da4aaf9d6226562b41fffaa651a35
```

Every permanent step passed:

- checkout and Python 3.11 setup;
- dependency installation;
- Ruff;
- strict mypy;
- eight Cboe parser tests;
- exact official contract-file acquisition;
- current Cboe terms-page retrieval;
- deterministic pilot construction;
- independent raw, schema, row-count, output-hash, and closed-gate verification;
- deletion of restricted raw, derived-price, and terms-page content before upload;
- safe evidence upload;
- safe receipt generation and upload.

The repository-wide legacy workflows remain separate and are not represented as passing.

---

## 9. Current Cboe terms identities

The hosted run retrieved the current Cboe terms pages and retained only their identities, not their HTML content.

### Website terms

```text
Byte count:
403966

SHA-256:
cb177fa2e8937d6390fab2098428135c7f037c98ad5495d0e3833b0a87063572
```

### Use of Content

```text
Byte count:
345651

SHA-256:
d9bda804159f65f732409aa0743915a1e0e0e4e36976b86f10ab95963cf55f5d
```

Controlling license classification:

```text
raw_redistribution_authorized: false
public_redisplay_authorized: false
internal_research_status: PENDING_FORMAL_LICENSE_INTERPRETATION
```

The project does not infer a redistribution right merely because a file is reachable from a public URL.

---

## 10. Restricted-content handling

The permanent workflow downloads the official Cboe contract files and terms pages only inside the ephemeral GitHub runner.

After validation, it deletes:

- the two raw contract CSV files;
- the derived price-row CSV;
- the downloaded terms HTML;
- response-header files.

The uploaded evidence artifact contains only one JSON evidence file. It contains hashes, byte counts, schema identity, manifest metadata, and closed authorization flags. It contains no CSV rows, no HTML, and no file named `VX_*`.

This is a deliberate correction to the earlier exploratory artifact, which temporarily staged raw Cboe files. That exploratory workflow was retired after the permanent safe-evidence workflow passed.

---

## 11. Safe artifact evidence

### Safe evidence bundle

```text
Artifact ID:
8445247846

Artifact digest:
f87327eb392cc84baeb0dd33669becc0837d0a4972586dcf7ee83dd7b17c360b

Retention expiry:
2026-10-17
```

The bundle contains only:

```text
cboe-vx-public-pilot-evidence.json
```

Internal evidence-file identity:

```text
Byte count:
4245

SHA-256:
0c32035b9e4c8a30e079d9f5e7760e58fa427312c83a8dbd97889d76fe8b341a
```

### Safe receipt

```text
Artifact ID:
8445247974

Artifact digest:
8a62084dcae1a1d788ac2ce16a1b191f501172731775648a2229f3b7cf8f0c91

Retention expiry:
2026-10-17
```

Internal receipt identity:

```text
Byte count:
847

SHA-256:
9e04384c52e4ec7ae8828fcc7842a6c9638411f1b9f3fbd739279a11b1829646
```

Both artifact ZIP digests were independently recomputed after download and matched GitHub's recorded digests. The ZIP contents were independently inspected and contained no `.csv`, `.html`, or `VX_*` file.

Storage classification:

```text
ACTIONS_SAFE_EVIDENCE_ONLY_RETENTION_90_DAYS
```

This is not raw immutable storage. Raw retention remains incomplete.

---

## 12. Evidence classification

```text
Official Cboe contract URLs: CONFIRMED
Exact raw acquisition during hosted run: CONFIRMED
Raw byte counts: CONFIRMED
Raw SHA-256 identities: CONFIRMED
Contract identities: CONFIRMED
Expiration identities: CONFIRMED
Exact schema: CONFIRMED
Separate Close and Settle fields: CONFIRMED
Settlement-change reconciliation: CONFIRMED
Contract-level pilot derivation: CONFIRMED
Continuous-series construction: NOT USED
Back adjustment: NOT USED
Permanent Ruff / mypy / tests: PASS
Independent safe-artifact rehash: PASS
Restricted raw public upload: PREVENTED
Raw retention: INCOMPLETE
Internal research license: PENDING_FORMAL_LICENSE_INTERPRETATION
Historical price availability timing: NOT VERIFIED
Canonical CFTC price linkage: NOT AUTHORIZED
Returns: NOT COMPUTED
Paper replication pass: NOT GRANTED
Economic edge: NOT ESTABLISHED
```

---

## 13. Authorization consequence

This evidence authorizes:

- continued Cboe source engineering;
- exact contract-level parser maintenance;
- schema and formula unit tests;
- license and historical-availability research;
- a future proposal for a narrowly scoped same-contract price-linkage gate.

It does not authorize:

- treating public reachability as a redistribution license;
- retaining or publishing raw Cboe data without an approved legal basis;
- assigning these contract prices to CFTC rows;
- constructing a continuous futures series;
- calculating positioning returns;
- signal fitting;
- Report 2.4 full sensitivity analysis;
- paper trading;
- live trading;
- leverage;
- capital deployment.

---

## 14. Remaining gates

Before price linkage can be authorized, the project must resolve:

1. the internal-research and retention interpretation of Cboe terms;
2. whether a compliant private immutable raw store is permitted;
3. the historical availability timestamp for each settlement observation;
4. the exact mapping from the CFTC `VX` reporting identity to eligible contract months on each decision date;
5. the same-contract observation rule at and after CFTC availability;
6. treatment of expiry and roll boundaries without roll-gap PnL;
7. an explicit no-lookahead validation against the CFTC release ledger.

Until those gates pass, the current pilot remains a verified data-engineering artifact rather than a price-linked empirical replication.

---

## 15. Final controlling verdict

```text
OWNER-ACCESSIBLE OFFICIAL SOURCE: CONFIRMED
CONTRACT-LEVEL RAW ACQUISITION: CONFIRMED DURING HOSTED RUN
EXACT RAW IDENTITIES: CONFIRMED
EXACT PARSER: CONFIRMED
EIGHT TESTS: PASS
RUFF: PASS
MYPY STRICT: PASS
DETERMINISTIC 35-ROW PILOT IDENTITY: CONFIRMED
CLOSE / SETTLE SEPARATION: CONFIRMED
CONTINUOUS OR BACK-ADJUSTED SERIES: NOT USED
SAFE EVIDENCE-ONLY ARTIFACT: CONFIRMED
RAW PUBLIC REDISTRIBUTION: PREVENTED
RAW RETENTION: INCOMPLETE
LICENSE INTERPRETATION: OPEN
HISTORICAL AVAILABILITY TIMING: OPEN
PRICE-LINKAGE-AUTHORIZED ROWS: ZERO
RETURNS AUTHORIZED: NO
PAPER REPLICATION: NOT COMPLETE
ECONOMIC EDGE: NOT ESTABLISHED
EDGE-FUT-POSITION-001: INCONCLUSIVE
REPORT 2.4: BLOCKED
```
