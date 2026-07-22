# Report 2.3E — Verified CFTC TFF 2022 Point-in-Time Instrument Registry Evidence

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Parent:** [Report 2.3 controlling status](02-03-current-controlling-status.md)  
**Evidence date:** 2026-07-19  
**Status:** `REPORTING_AND_PRODUCT_IDENTITIES_VERSIONED; PRICE_LINKAGE_FAIL_CLOSED`

---

## 1. Decision

The project now has a deterministic, versioned registry connecting every CFTC contract-market code in the verified `2022-09-13` TFF Futures Only pilot to a point-in-time exchange-product identity or to an explicit non-tradable aggregate classification.

The registry covers all 54 pilot rows. It does not authorize a single provider price series, contract chain, return, fitted signal, or strategy result.

The three identity layers remain separate:

1. **CFTC reporting identity** — the code and reportable market in the official CFTC file;
2. **exchange product identity** — the exchange product/root or explicit aggregate/nonstandard classification;
3. **provider price identity** — the effective-dated provider contract identifier and contract-chain evidence required before a price series may be used.

Only the first two layers have meaningful coverage in this registry. The third layer remains empty and blocked.

---

## 2. Verified source lineage

The registry is derived from the previously verified official CFTC pilot:

```text
Pilot report date:
2022-09-13

Pilot rows:
54

Pilot SHA-256:
1be0028ba872ed56c970f6cd67b76c480b3653b170762c6e55f39dc10c3d268b
```

The mapping contract and official-source registry are separately versioned:

```text
Uncompressed mapping-contract SHA-256:
4dd92e493f9752371cdfaef5f6bc90edf72b235cd0f4d444aa96aa9e628251c2

Official-source registry SHA-256:
bc861dbe5a7da1f27060d87cb588a51acdd6466dbb27c889cafc5c3680cd6fff
```

The committed mapping contract is stored as gzip-compressed Base64 text. The hosted workflow decodes it, verifies the uncompressed SHA-256, and only then permits registry construction.

Official evidence roles include:

- the CFTC historical pilot for reporting identity, DCM code, market name, commodity group, and contract units;
- the CFTC strike-price/product table for product/reporting code evidence;
- official CME product and change notices for CME/CBOT identities and special historical cases;
- official Cboe product documentation for VIX futures;
- official ICE product-family documentation for ICE U.S. identities.

The complete source identifiers and official locations are stored in:

```text
docs/research/edge-discovery/02-replication/
02-03-cftc-tff-instrument-mapping-sources.json
```

---

## 3. Hosted verification

```text
Workflow:
CFTC TFF 2022 Instrument Registry

Run ID:
29685511829

Workflow conclusion:
SUCCESS

Branch head that triggered the run:
585b5b8a56cd0088bd696252b64f7925d0dabfcb

Pull-request merge-test commit recorded by Actions:
2da604ef45fa0ef508cabcf15e3463d43c1b50b3
```

Every dedicated workflow step passed:

- checkout and Python 3.11 setup;
- dependency installation;
- Ruff;
- strict mypy;
- seven mapping tests;
- official CFTC archive acquisition;
- deterministic pilot derivation;
- mapping-contract decoding and SHA-256 verification;
- registry construction;
- fail-closed special-case and authorization checks;
- staged bundle upload;
- receipt generation and upload.

Repository-wide legacy workflows are separate and are not represented as passing.

---

## 4. Registry identity

```text
Filename:
cftc_tff_2022-09-13_instrument_registry.csv

Registry version:
CFTC_TFF_2022_09_13_INSTRUMENT_REGISTRY_V1

Rows:
54

Unique CFTC contract-market codes:
54

Byte count:
38903

SHA-256:
70a8e89db716cfc8b1285f3b627188294abaae920c2b99b193f4501a7e525c74
```

The CSV was hashed inside the hosted workflow, compared with its manifest, downloaded from the Actions artifact, and independently rehashed outside the runner.

---

## 5. Mapping classification

```text
HISTORICAL_SCREEN_TRADABLE_ROOT_VERIFIED: 47
NON_TRADABLE_CONSOLIDATED_AGGREGATE: 3
HISTORICAL_LATER_DELISTED_ROOT_VERIFIED: 2
NON_STANDARD_EXECUTION_PRODUCT: 1
PRODUCT_IDENTITY_VERIFIED_TECHNICAL_SYMBOL_PENDING: 1
```

These classes describe identity evidence only. `HISTORICAL_SCREEN_TRADABLE_ROOT_VERIFIED` does not imply that a provider price series, expired contract chain, multiplier vintage, or roll schedule has been accepted.

---

## 6. Non-tradable consolidated aggregates

The following reporting codes are explicitly classified as aggregates and must never receive a direct price series:

```text
12460+ — DJIA Consolidated
13874+ — S&P 500 Consolidated
20974+ — NASDAQ-100 Consolidated
```

For all three rows:

```text
mapping_class:
NON_TRADABLE_CONSOLIDATED_AGGREGATE

tradability:
NOT_A_TRADABLE_INSTRUMENT

exchange_product_code:
empty

price_linkage_status:
NOT_APPLICABLE_AGGREGATE_MUST_NEVER_RECEIVE_PRICE_SERIES
```

A later strategy may use component-level instruments only under separately declared aggregation rules. It may not assign an arbitrary equity-index future to a consolidated CFTC row.

---

## 7. Historical and nonstandard cases

### 7.1 Eurodollar

```text
CFTC code: 132741
Exchange product code: GE
Class: HISTORICAL_LATER_DELISTED_ROOT_VERIFIED
Price-linkage status:
BLOCKED_REQUIRES_EXPIRED_CONTRACT_HISTORY_AND_2022_PROVIDER_VINTAGE
```

The root identity is historical. Current replacement products or current provider metadata cannot be projected backward into the 2022 observation.

### 7.2 Three-Month BSBY

```text
CFTC code: 157741
Exchange product code: BSB
Historical order-entry/security-group identity: BW
Class: HISTORICAL_LATER_DELISTED_ROOT_VERIFIED
Price-linkage status:
BLOCKED_REQUIRES_2022_HISTORICAL_PROVIDER_VINTAGE
```

The later delisting is retained as lifecycle evidence. It does not invalidate the product identity on the pilot date, but it makes current metadata insufficient.

### 7.3 Adjusted Interest Rate S&P 500 Total Return

```text
CFTC code: 13874W
Exchange product code: ASR
Security group: 0B
Class: NON_STANDARD_EXECUTION_PRODUCT
Price-linkage status:
BLOCKED_NONSTANDARD_CLEARPORT_EFRP_AND_BTIC_PRICE_SEMANTICS
```

This product cannot inherit ordinary central-limit-order-book price and execution assumptions.

### 7.4 Nikkei Stock Average, yen denominated

```text
CFTC code: 240743
Exchange product code: NIY
Class: HISTORICAL_SCREEN_TRADABLE_ROOT_VERIFIED
Price-linkage status:
BLOCKED_PENDING_PROVIDER_CONTRACT_CHAIN_AND_VINTAGE
```

The exchange root is not yet a provider contract-chain identity.

### 7.5 Micro 10-Year Yield

```text
CFTC code: 04360Y
Exchange product code: 10Y
Class: PRODUCT_IDENTITY_VERIFIED_TECHNICAL_SYMBOL_PENDING
Price-linkage status:
BLOCKED_PENDING_PROVIDER_REFERENCE_DATA_AND_CONTRACT_CHAIN
```

The product identity is preserved while the technical provider symbol and contract-chain contract remain unresolved.

---

## 8. Price-linkage state

Price-linkage classifications across all rows are:

```text
BLOCKED_PENDING_PROVIDER_CONTRACT_CHAIN_AND_VINTAGE: 47
NOT_APPLICABLE_AGGREGATE_MUST_NEVER_RECEIVE_PRICE_SERIES: 3
BLOCKED_REQUIRES_EXPIRED_CONTRACT_HISTORY_AND_2022_PROVIDER_VINTAGE: 1
BLOCKED_REQUIRES_2022_HISTORICAL_PROVIDER_VINTAGE: 1
BLOCKED_NONSTANDARD_CLEARPORT_EFRP_AND_BTIC_PRICE_SEMANTICS: 1
BLOCKED_PENDING_PROVIDER_REFERENCE_DATA_AND_CONTRACT_CHAIN: 1
```

Global authorization checks:

```text
Rows with price_linkage_authorized=true: 0
Rows with provider_contract_id populated: 0
Global price linkage authorized: false
Returns authorized: false
Empirical fitting authorized: false
```

This is intentional. Product identity is not promoted into price identity.

---

## 9. Actions staging evidence

### Registry bundle

```text
Artifact ID:
8441940834

Artifact digest:
c0e68748e7d1b7266ee4e4b7a9de1ebd59bbea829641499618a349bae0b5457a

Retention expiry:
2026-10-17
```

### Receipt

```text
Artifact ID:
8441941004

Artifact digest:
7ee9d381ffc852b6e432592945ffa69bb35cfcf65557acd98da3b19ba4809796

Retention expiry:
2026-10-17
```

Both artifact ZIP digests were independently recomputed after download and matched GitHub's recorded values.

Current storage classification:

```text
ACTIONS_ARTIFACT_STAGED_RETENTION_90_DAYS
```

This is not long-term immutable storage.

---

## 10. Evidence classification

```text
Official CFTC reporting identity coverage: CONFIRMED_54_OF_54
Versioned exchange-product identity coverage: CONFIRMED_54_OF_54
Consolidated aggregate exclusion: CONFIRMED_3_OF_3
Historical delisted-product classification: CONFIRMED_2_OF_2
Nonstandard execution classification: CONFIRMED_1_OF_1
Technical-symbol-pending classification: CONFIRMED_1_OF_1
Registry SHA-256: CONFIRMED
Independent artifact rehash: CONFIRMED
Provider contract-chain identity: NOT COMPLETE
Effective-dated multiplier/tick/currency contract: NOT COMPLETE
Price-linkage authorization: ZERO_ROWS
Returns authorization: NOT GRANTED
Paper replication pass: NOT GRANTED
Economic edge: NOT ESTABLISHED
```

---

## 11. Authorization consequence

This evidence authorizes:

- construction of provider-specific reference-data contracts;
- effective-dated futures contract-chain mapping;
- explicit multiplier, tick, quotation-currency, first-notice, last-trade, and settlement-field contracts;
- separate treatment of delisted products and nonstandard execution products;
- planning of same-contract return linkage after provider evidence exists.

It does not authorize:

- assigning a price series by root-symbol resemblance alone;
- assigning any price to consolidated aggregate rows;
- projecting current product metadata backward into 2022;
- constructing continuous-futures PnL;
- computing a positioning return;
- fitting a signal;
- Report 2.4 full sensitivity analysis;
- paper trading;
- live trading;
- leverage;
- capital deployment.

`EDGE-FUT-POSITION-001` remains empirically `INCONCLUSIVE`.
