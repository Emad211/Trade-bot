# Report 2.3F — Verified Provider-Candidate and Point-in-Time Price-Linkage Gate

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Parent:** Report 2.3 controlling status  
**Evidence date:** 2026-07-19  
**Status:** `PRIMARY_INTEGRATION_CANDIDATE_SELECTED; AUTHENTICATED_PROVIDER_ACCEPTANCE_NOT_COMPLETE`

---

## 1. Decision

The project has selected **Databento as the primary technical integration candidate** for the first provider-specific futures reference-data and settlement probe.

Databento has not been accepted as the project's price provider.

No authenticated Databento API request was executed in this milestone. No data was purchased. No provider-specific contract identifier was accepted. No price row or return was authorized.

The decision is deliberately split into two states:

```text
Primary integration candidate:
DATABENTO

Accepted provider:
none
```

The candidate decision is based on the possibility of testing three venue datasets through a common historical interface:

```text
CME and CBOT:
GLBX.MDP3

ICE Futures U.S.:
IFUS.IMPACT

Cboe Futures Exchange:
XCBF.PITCH
```

The candidate must still survive an authenticated, point-in-time, zero-purchase metadata and cost probe before any provider acceptance decision can be made.

---

## 2. Why this is the correct next gate

The previous instrument registry established reporting and exchange-product identities for all 54 CFTC pilot rows, but intentionally left every provider contract identifier empty.

A root such as `ES`, `ZN`, `DX`, or `VX` is not sufficient to construct historical returns.

Before a price series can be accepted, the project must establish:

1. the exact provider dataset;
2. dataset availability over the required 2022 dates;
3. dataset condition and quality state for those dates;
4. point-in-time parent-to-child contract resolution;
5. the exact child contract identifier;
6. activation or listing time;
7. expiration or last-trade time;
8. minimum price increment;
9. multiplier or unit quantity;
10. quotation currency;
11. official settlement records;
12. cost before download;
13. license and redistribution terms;
14. request and response hashes;
15. immutable storage identity.

Until these conditions pass, a provider root is only a candidate lookup key.

---

## 3. Verified input identity

The candidate plan is derived from the previously verified registry:

```text
Registry version:
CFTC_TFF_2022_09_13_INSTRUMENT_REGISTRY_V1

Registry rows:
54

Registry SHA-256:
70a8e89db716cfc8b1285f3b627188294abaae920c2b99b193f4501a7e525c74
```

The committed registry is decoded from:

```text
docs/research/edge-discovery/02-replication/
02-03-cftc-tff-2022-instrument-registry.csv.gz.b64
```

The provider planner refuses a changed registry hash, row count, version, duplicate reporting code, or nondeterministic ordering.

---

## 4. Provider-candidate contract identity

The machine-readable candidate contract is:

```text
docs/research/edge-discovery/02-replication/
02-03-provider-price-linkage-candidate-contract.yaml
```

Identity:

```text
Contract ID:
CFTC_TFF_2022_09_13_PROVIDER_PRICE_LINKAGE_CANDIDATE_V1

Contract SHA-256:
8614c71dc7a6db2aebaf08db0b8d5b4566d92c69d31bbe424fc2e73780fa9832
```

Official provider and exchange-native source locations are versioned in:

```text
02-03-provider-price-linkage-official-sources.json
```

Source-registry SHA-256:

```text
68b73fdb5f3c83b90606fb51c8a7378dc9a1e23a1df4260c94ed0cd439903770
```

The source registry includes official material from:

- Databento historical dataset, futures, symbology, statistics, and pricing documentation;
- CME DataMine and CME Reference Data;
- Cboe historical futures data;
- ICE Report Center and ICE Data Services.

Exchange-native sources remain required audit fallbacks even if a common provider later passes the integration gate.

---

## 5. Deterministic provider-candidate plan

Filename:

```text
databento-provider-candidate-plan.csv
```

Identity:

```text
Plan version:
CFTC_TFF_2022_09_13_DATABENTO_CANDIDATE_PLAN_V1

Rows:
54

Unique CFTC reporting codes:
54

Byte count:
28918

SHA-256:
cd2430c7fdd0b3a68a1093925d755c242081372fbe41668cc53436893c274062
```

A deterministic compressed copy is retained in Git:

```text
02-03-provider-candidate-plan.csv.gz.b64
```

Compression identities:

```text
Gzip byte count:
2216

Gzip SHA-256:
875dbcafa91c06234163dfdab1c37c4b0983cc34c749472f59adada101a47e08

Base64 text byte count:
2957

Base64 text SHA-256:
7df59daeb615a4cf5692729703ba41da32f96780116966c1fb367f0284e7e624
```

This Git copy is a durable derived artifact. It is not a substitute for immutable storage of purchased or licensed raw provider responses.

---

## 6. Candidate coverage

The 47 ordinary historical screen-tradable rows receive theoretical dataset candidates:

```text
GLBX.MDP3:
43 ordinary CME/CBOT product roots

IFUS.IMPACT:
3 ordinary ICE Futures U.S. product roots

XCBF.PITCH:
1 ordinary CFE product root
```

The full 54-row classification remains:

```text
Ordinary screen-tradable candidate rows:
47

Non-tradable consolidated aggregate rows:
3

Historical later-delisted rows:
2

Nonstandard execution rows:
1

Technical-symbol-pending rows:
1
```

Candidate coverage is not authenticated coverage.

The plan has not yet confirmed that each dataset:

- is entitled for the project account;
- covers the requested 2022 period;
- has acceptable condition for the requested dates;
- resolves each parent symbol to the expected historical child contracts;
- supplies complete definition and settlement evidence;
- satisfies cost and license constraints.

---

## 7. Consolidated aggregates remain excluded

The following three CFTC reporting rows receive no provider candidate, dataset, or parent symbol:

```text
12460+ — DJIA Consolidated
13874+ — S&P 500 Consolidated
20974+ — NASDAQ-100 Consolidated
```

Their candidate state is:

```text
NOT_APPLICABLE_NON_TRADABLE_AGGREGATE
```

They must never receive a direct price series.

A future component-level reconstruction would require a separately specified aggregation contract. It cannot assign an arbitrary index future to a consolidated reporting row.

---

## 8. Historical and nonstandard cases remain blocked

### 8.1 Eurodollar

```text
CFTC code:
132741

Exchange root:
GE

Candidate dataset:
GLBX.MDP3

Candidate status:
PENDING_AUTHENTICATED_EXPIRED_HISTORY_AND_2022_VINTAGE_PROBE
```

The project must prove the historical expired Eurodollar contract chain. Current SOFR metadata cannot replace it.

### 8.2 Three-Month BSBY

```text
CFTC code:
157741

Exchange product code:
BSB

Historical order-entry identity:
BW

Candidate status:
PENDING_AUTHENTICATED_EXPIRED_HISTORY_AND_2022_VINTAGE_PROBE
```

The later delisting requires evidence tied to the 2022 provider vintage.

### 8.3 Adjusted Interest Rate S&P 500 Total Return

```text
CFTC code:
13874W

Product identity:
ASR / security group 0B

Candidate status:
BLOCKED_EXCHANGE_NATIVE_NONSTANDARD_EXECUTION_CONTRACT_REQUIRED
```

This product cannot inherit ordinary central-limit-order-book, settlement, or execution assumptions.

### 8.4 Micro 10-Year Yield

```text
CFTC code:
04360Y

Product identity:
10Y

Candidate status:
PENDING_AUTHENTICATED_PARENT_AND_TECHNICAL_SYMBOL_RESOLUTION
```

The exchange product identity exists, but the technical provider symbol remains unverified.

---

## 9. Required schemas and settlement semantics

Every eligible provider candidate requires both:

```text
definition
statistics
```

The settlement contract requires:

```text
Statistics stat_type:
3

Final flag:
required

Actual flag:
required

OHLCV as settlement substitute:
prohibited
```

Daily OHLCV bars must not be silently treated as official settlement prices.

The definition contract requires, at minimum:

- outright future classification;
- spread exclusion;
- raw symbol;
- provider instrument identifier;
- activation or listing time;
- expiration or last-trade time;
- minimum price increment;
- multiplier or unit quantity;
- quote currency.

First-notice and other lifecycle fields must be added from provider or exchange-native reference evidence where applicable.

---

## 10. Authenticated probe request

The project generated, but did not execute, a representative authenticated probe request.

Filename:

```text
authenticated-probe-request.json
```

Identity:

```text
Byte count:
3382

SHA-256:
04ee25ae4f7ff9f09b6e50e2526d5282e9a6202601fb281028f86a52c1c269be
```

Representative roots:

```text
ZN — GLBX.MDP3 — ZN.FUT
ES — GLBX.MDP3 — ES.FUT
NIY — GLBX.MDP3 — NIY.FUT
DX — IFUS.IMPACT — DX.FUT
VX — XCBF.PITCH — VX.FUT
```

The probe requires metadata operations equivalent to:

- list datasets;
- list schemas;
- get dataset range;
- get dataset condition;
- get cost;
- resolve parent symbols;
- retrieve definition records;
- retrieve final actual settlement statistics.

The probe state is:

```text
Authentication secret expected:
DATABENTO_API_KEY

Execution status:
BLOCKED_MISSING_AUTHENTICATED_ACCOUNT_AND_EXPLICIT_COST_APPROVAL

Maximum authorized cost:
USD 0.00

Purchase authorized:
false
```

No provider request was made and no account entitlement was inferred.

---

## 11. Hosted verification

Workflow:

```text
CFTC TFF 2022 Provider Candidate Plan
```

Successful run:

```text
Run ID:
29687144619

Conclusion:
SUCCESS

Branch head associated with the successful run:
e0b8e25a2cc5b84596e9a6f058505c878cf4d960

Pull-request merge-test commit recorded in the receipt:
bd318c6cb4480a9bbe11bbe0c0d81478c89dfa82
```

Every dedicated workflow step passed:

- checkout and Python 3.11 setup;
- project dependency installation;
- Ruff;
- strict mypy;
- seven provider-plan unit tests;
- deterministic plan construction;
- independent contract, source, row, coverage, special-case, and hash verification;
- bundle upload;
- receipt creation and upload;
- non-promotional workflow summary.

An earlier hosted run failed only on repository-specific Ruff import spacing in the entrypoint. The exact failure was captured, the formatting was corrected, and the temporary diagnostic workflow was removed. No business rule or empirical result was changed by that correction.

Repository-wide legacy workflows remain separate and are not represented as passing.

---

## 12. Hosted artifact evidence

### 12.1 Candidate-plan bundle

```text
Artifact ID:
8442435407

Artifact digest:
d23721a77dc1c16e434df6cb4fdf4491ab1c9f3698be344d26182662dac0b5cc

Retention expiry:
2026-10-17
```

### 12.2 Receipt

```text
Artifact ID:
8442435528

Artifact digest:
9084ecc59f80dbe23d063e9f8fdd957c202cb568a1de6b999fd73182718d5465

Retention expiry:
2026-10-17
```

Both artifact ZIP digests were independently recomputed after download and matched GitHub's recorded digests.

The files inside the bundle were independently rehashed outside the runner:

```text
Candidate CSV SHA-256:
cd2430c7fdd0b3a68a1093925d755c242081372fbe41668cc53436893c274062

Probe request SHA-256:
04ee25ae4f7ff9f09b6e50e2526d5282e9a6202601fb281028f86a52c1c269be

Manifest SHA-256:
7f8c69a1b0866f8540999d6d47f7399791e84937d00754d7a17c4576ea930698
```

Storage classification:

```text
ACTIONS_ARTIFACT_STAGED_RETENTION_90_DAYS
```

This is not approved long-term immutable provider-response storage.

---

## 13. Current authorization state

```text
Primary integration candidate:
DATABENTO

Accepted provider:
none

Authenticated provider probe executed:
false

Dataset entitlements verified:
false

Dataset 2022 conditions verified:
false

Point-in-time parent resolution verified:
false

Definition records acquired:
false

Final actual settlements acquired:
false

Cost quote acquired:
false

License snapshot acquired:
false

Provider contract identifiers populated:
0

Price-linkage-authorized rows:
0

Returns authorized:
false

Purchase authorized:
false
```

The plan does not modify the underlying 54-row instrument registry's authorization state.

---

## 14. Evidence classification

```text
Provider requirements contract: CONFIRMED
Official source registry: CONFIRMED
Primary technical candidate: SELECTED_NOT_ACCEPTED
Theoretical ordinary-root coverage: CONFIRMED_47
GLBX candidate rows: CONFIRMED_43
IFUS candidate rows: CONFIRMED_3
XCBF candidate rows: CONFIRMED_1
Aggregate exclusion: CONFIRMED_3
Representative authenticated probe: GENERATED_NOT_EXECUTED
Provider API entitlement: NOT VERIFIED
Provider dataset condition: NOT VERIFIED
Provider contract-chain identity: NOT VERIFIED
Provider settlement evidence: NOT ACQUIRED
Provider cost evidence: NOT ACQUIRED
Provider license snapshot: NOT ACQUIRED
Price-linkage authorization: ZERO_ROWS
Returns authorization: NOT GRANTED
Paper replication pass: NOT GRANTED
Economic edge: NOT ESTABLISHED
```

---

## 15. Authorization consequence

This milestone authorizes:

- implementation of an authenticated metadata-only probe client;
- exact hashing of provider requests and responses;
- zero-purchase entitlement, range, condition, schema, symbology, and cost checks;
- representative definition and settlement probes for `ZN`, `ES`, `NIY`, `DX`, and `VX`;
- exchange-native cross-check design;
- provider rejection if any mandatory gate fails.

It does not authorize:

- spending provider credits or cash;
- bulk market-data download;
- accepting Databento as the provider;
- writing provider contract IDs into the canonical registry;
- assigning prices by root-symbol similarity;
- assigning prices to consolidated aggregates;
- treating OHLCV as official settlement;
- constructing continuous-futures PnL;
- computing a positioning return;
- fitting a signal;
- Report 2.4 full sensitivity analysis;
- paper trading;
- live trading;
- leverage;
- capital deployment.

`EDGE-FUT-POSITION-001` remains empirically `INCONCLUSIVE`.
