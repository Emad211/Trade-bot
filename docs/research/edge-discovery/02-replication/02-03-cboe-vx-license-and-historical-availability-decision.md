# Report 2.3 — Cboe VX License and Historical Availability Decision

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Status date:** 2026-07-19  
**Status:** `BLOCKED_LICENSE_OR_TIMING`

This report is the controlling decision for Issue #44. It follows the successful Cboe VX contract-level engineering pilot but does not convert that engineering pass into permission to retain data, build a derived historical dataset, assign prices to the CFTC registry, or calculate returns.

## 1. Decision

```text
Cboe engineering source identity: VERIFIED
Parser and schema mechanics: VERIFIED
Private raw retention: NOT AUTHORIZED
Derived CFTC-to-price dataset: NOT AUTHORIZED
Historical settlement publication time: NOT VERIFIED
Same-day Friday settlement at CFTC release: PROHIBITED_LOOKAHEAD
Canonical price linkage: NOT AUTHORIZED
Return computation: NOT AUTHORIZED
Final gate result: BLOCKED_LICENSE_OR_TIMING
```

The current source remains useful for parser, schema, contract-identity, formula, and fail-closed engineering tests. It does not currently support historical empirical return work.

## 2. Controlling source identities

### 2.1 Cboe website terms

Official location:

```text
https://www.cboe.com/terms
```

Snapshot identity captured in hosted run `29696828324`:

```text
Byte count: 403966
SHA-256: cb177fa2e8937d6390fab2098428135c7f037c98ad5495d0e3833b0a87063572
```

The current terms allow a user to view, print, and download one copy of website materials for personal non-commercial use connected with Cboe products, while restricting other copying, electronic storage, derivative creation, use to verify or correct other data, publication, distribution, and other uses without prior written consent.

The intended project use would include multiple restricted activities:

- content-addressed private electronic retention;
- repeated reproducible processing;
- combining Cboe prices with CFTC positioning data;
- creating derived contract-level features and returns;
- using Cboe observations to verify and interpret another dataset;
- retaining lineage evidence for independent reproduction.

Public URL accessibility does not override these restrictions.

### 2.2 Cboe Use of Content process

Official location:

```text
https://www.cboe.com/en/use-of-content/
```

Snapshot identity captured in hosted run `29696828324`:

```text
Byte count: 345651
SHA-256: d9bda804159f65f732409aa0743915a1e0e0e4e36976b86f10ab95963cf55f5d
```

Cboe states that requested use requires advance approval and that approval is contingent on a license agreement signed by both the requester and Cboe. Submitting a request does not itself grant permission.

### 2.3 Market-data licensing route

Official locations:

```text
https://www.cboe.com/market_data_services/document_library/
https://www.cboe.com/market_data_services/onboarding
```

The market-data route requires a Cboe data agreement and onboarding. The project does not assume that this route is free, geographically accessible to the owner, or equivalent to permission for historical website CSV use.

## 3. Timing evidence

### 3.1 Settlement event time

Cboe's VIX FAQ describes the normal daily settlement time for VIX futures as:

```text
15:00 America/Chicago
```

Official location:

```text
https://www.cboe.com/tradable_products/vix/faqs
```

Cboe's U.S. futures hours page also identifies the VX/VXM post-settlement start time as 3:00 p.m. Central Time.

Official location:

```text
https://www.cboe.com/about/hours/us-futures
```

This establishes the settlement calculation event, not the exact historical website-publication timestamp.

### 3.2 CFTC release versus VX settlement on the frozen pilot date

For the frozen CFTC report date `2022-09-13`:

```text
Scheduled CFTC release:
2022-09-16T15:30:00-04:00
2022-09-16T19:30:00Z

VX daily settlement event:
2022-09-16T15:00:00-05:00
2022-09-16T20:00:00Z
```

Therefore:

```text
CFTC release precedes same-day VX settlement by 30 minutes.
```

Using the Friday `2022-09-16` VX settlement at the CFTC release decision time would be lookahead even if publication were instantaneous.

### 3.3 Publication time remains unknown

The official pages establish the settlement event and display current settlement observations, but the project has not obtained an authoritative historical timestamp proving when each 2022 settlement became publicly retrievable.

The contract-level CSVs retrieved in 2026 are later historical archives. Their current retrievability cannot prove contemporaneous availability in September 2022.

Consequently:

```text
historical_settlement_published_at: null
historical_available_at: null
```

No estimated delay is promoted to verified history.

## 4. Anchor-compatibility finding

Report 2.1 classifies `EDGE-FUT-POSITION-001` as:

```text
Positioning reconstruction: EXACT_PUBLIC
Complete return replication: EXACT_LICENSED
```

The anchor paper uses CFTC positioning with licensed Thomson Reuters Datastream prices and tests long-short sorts across asset classes. The CFTC VIX row is a reporting-market aggregate and is not a maturity-specific contract identifier.

Therefore:

- `VX/U2` cannot be assigned directly to the CFTC row merely because it is the nearest expiration;
- `VX/V2` cannot be chosen merely to avoid settlement week;
- a single-contract proxy would be a constructive modeling choice, not exact replication;
- an open-interest-weighted basket would also be a new experiment and requires a separately frozen contract;
- no modeling choice may be selected after observing performance.

The current Cboe pilot validates contract mechanics only.

## 5. Current authorization

```yaml
cboe_engineering_tests: true
synthetic_fixture_tests: true
hash_and_schema_verification: true
permission_request_preparation: true
prospective_contract_design: true

private_raw_retention: false
historical_derived_dataset: false
cftc_price_linkage: false
historical_return_computation: false
prospective_price_storage: false
empirical_fitting: false
parameter_tuning: false
strategy_tournament: false
paper_trading: false
live_trading: false
leverage: false
capital_deployment: false
report_2_4_full_authorization: false
```

## 6. Re-entry criteria

The Cboe route may re-enter price-linkage review only after all of the following are documented:

1. written Cboe permission or an executed license explicitly covering the intended internal use;
2. permission for private electronic retention of exact source files;
3. permission to combine the data with CFTC observations and create internal derived features and returns;
4. permission to retain hashes, metadata, and reproducibility evidence;
5. an approved private immutable-storage contract;
6. a prospective or authoritative historical availability rule;
7. a frozen maturity-representation contract compatible with the declared replication class;
8. a separate review that grants price-linkage authorization.

## 7. Next path

A permission-request package is maintained at:

```text
02-03-cboe-content-permission-request-package.md
```

A no-lookahead timing and contract-representation contract is maintained at:

```text
02-03-cboe-vx-prospective-no-lookahead-contract.yaml
```

Until written permission is obtained, the project should prioritize other owner-accessible sources whose terms explicitly permit reproducible internal research and private retention.

## 8. Final verdict

```text
OFFICIAL SOURCE AND CONTRACT MECHANICS: CONFIRMED
SETTLEMENT EVENT TIME: CONFIRMED_15_00_AMERICA_CHICAGO
HISTORICAL PUBLICATION TIME: NOT VERIFIED
SAME-DAY SETTLEMENT AT 15:30 ET CFTC RELEASE: LOOKAHEAD
PRIVATE ELECTRONIC RETENTION: NOT AUTHORIZED UNDER CURRENT EVIDENCE
CFTC-LINKED DERIVED DATASET: NOT AUTHORIZED UNDER CURRENT EVIDENCE
CBOE HISTORICAL RETURN WORK: BLOCKED_LICENSE_OR_TIMING
PAPER REPLICATION: NOT COMPLETE
ECONOMIC EDGE: NOT ESTABLISHED
EDGE-FUT-POSITION-001: INCONCLUSIVE
REPORT 2.4: BLOCKED
```
