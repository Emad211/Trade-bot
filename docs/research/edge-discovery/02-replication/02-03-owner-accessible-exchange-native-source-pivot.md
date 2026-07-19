# Report 2.3H — Owner-Accessible Exchange-Native Price-Source Pivot

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Parent:** [Provider-probe controlling addendum](02-03-provider-probe-controlling-addendum.md)  
**Decision date:** 2026-07-19  
**Status:** `DATABENTO_OPERATIONALLY_REJECTED; PUBLIC_EXCHANGE_NATIVE_PIVOT_AUTHORIZED`

---

## 1. Decision

Databento is no longer an actionable provider candidate for this project owner.

The owner cannot obtain the required account and API-key access because the service requires payment, banking, or account-verification capabilities that are not practically available to the owner. The project will not use:

- fabricated personal or company information;
- borrowed payment cards;
- third-party account intermediaries;
- misleading residence or jurisdiction data;
- sanctions or payment-circumvention methods;
- another person's API credentials.

The provider classification is therefore:

```text
Provider:
DATABENTO

Technical candidate status:
PREVIOUSLY_SELECTED

Owner operational accessibility:
FAILED

Final operational classification:
OPERATIONALLY_REJECTED_OWNER_ACCESS_CONSTRAINT

Provider accepted:
false

Purchase authorized:
false

Price linkage authorized:
false

Returns authorized:
false
```

This is an accessibility rejection. It is not a claim that Databento's technical data quality is poor.

Issue `#42` is closed as `not planned` and preserves the reason for the decision.

---

## 2. New non-negotiable accessibility gate

A source may not be promoted merely because it is technically suitable.

Every future source must pass all of the following:

```text
OWNER_ACCESSIBLE_WITHOUT_FALSE_IDENTITY
NO_UNAVAILABLE_FOREIGN_PAYMENT_METHOD_REQUIRED
NO_SANCTIONS_OR_JURISDICTION_CIRCUMVENTION
TERMS_AND_LICENSE_REVIEWED
RAW_BYTES_ACQUIRABLE
CHECKSUM_AND_LINEAGE_PRESERVABLE
POINT_IN_TIME_CONTRACT_IDENTITY_AVAILABLE
SETTLEMENT_SEMANTICS_EXPLICIT
```

Failure of the first three requirements is an operational rejection even when the data is otherwise high quality.

---

## 3. Official exchange-source assessment

### 3.1 Cboe Futures Exchange

Official public locations:

- `https://www.cboe.com/markets/us/futures/market-statistics/historical-data/futures`
- `https://www.cboe.com/markets/us/futures/market-statistics/settlement/futures/daily/`
- `https://www.cboe.com/markets/us/futures/market-statistics/settlement/futures/final/`

The official historical-data page identifies contract-level CFE price and volume detail for selected futures products from 2013 to the present. The public settlement pages expose daily and final settlement tables and CSV-download controls.

Current classification:

```text
Source family:
CBOE_PUBLIC_CFE_HISTORY_AND_SETTLEMENTS

Owner-accessibility evidence:
PUBLIC_WEB_ACCESS_OBSERVED

Payment evidence:
NO_PAYMENT_REQUIRED_FOR_PUBLIC_PAGES_OBSERVED

Historical contract-level candidate:
VX

Decision:
GO_FOR_PUBLIC_VX_PILOT
```

This decision authorizes only acquisition and validation of a bounded VX pilot. It does not authorize a return, signal, or strategy.

Required pilot evidence:

- exact contract-month symbol;
- trade date;
- open, high, low, close, and settlement fields where available;
- expiration identity;
- public-page or CSV source URL;
- retrieval timestamp;
- raw SHA-256 and byte count;
- schema fingerprint;
- settlement-field interpretation;
- Cboe terms snapshot;
- no continuous-series substitution.

### 3.2 CME Group

Official public locations:

- `https://www.cmegroup.com/market-data/daily-bulletin.html`
- `https://www.cmegroup.com/articles/faqs/access-to-cme-group-settlement-data-faq.html`

CME states that settlement prices on product pages are delayed until midnight Central Time and are then freely available to view. The Daily Bulletin webpage publishes the previous trade date and links historical Daily Bulletin access to CME DataMine.

CME's official documentation also states that DataMine requires a CME login and an ordering process. The settlement-access FAQ describes retrieval or subscription fees for several End of Market datasets, while earlier CME notices described selected midnight settlement files as free of charge. These statements do not prove that the required 2022 historical files are accessible to this owner without an unavailable payment method.

Current classification:

```text
Source family:
CME_PUBLIC_DELAYED_WEBSITE_AND_DATAMINE

Current delayed product-page settlements:
PUBLIC_REFERENCE_AVAILABLE

Historical 2022 flat-file accessibility:
NOT VERIFIED FOR OWNER

Official documentation state:
ACCESS_AND_FEE_PATH_REQUIRES_EMPIRICAL_PROBE

Decision:
CONDITIONAL_ACCESS_PROBE_REQUIRED
```

Allowed next actions:

- test public delayed product pages without login;
- test Historical Daily Bulletin navigation without ordering;
- test whether a free CME account can retrieve the exact bounded 2022 files without payment details;
- record every redirect, login wall, order screen, terms page, and fee request.

Not allowed:

- assuming that a file is free because an older notice used the phrase `free of charge`;
- treating current delayed pages as proof of 2022 bulk-history accessibility;
- assigning CME prices before contract-level bytes and lineage are acquired.

### 3.3 ICE Futures U.S.

Official public locations:

- `https://www.ice.com/report-center`
- `https://www.ice.com/report-center/data-subscription`

The ICE Report Center exposes public report categories including deliveries, settlements, end-of-day reports, volume, and open interest. ICE also states that end-of-day report packages are available by annual subscription and that historical End-of-Day packages are available for one-off purchase.

Current classification:

```text
Source family:
ICE_REPORT_CENTER

Public report navigation:
AVAILABLE

Complete historical 2022 End-of-Day package:
PURCHASE_OR_SUBSCRIPTION_REQUIRED

Owner payment accessibility:
NOT AVAILABLE

Decision:
BLOCKED_PAID_ARCHIVE
```

Public ICE reports may support metadata or isolated verification when directly accessible, but they may not be represented as a complete historical price source.

---

## 4. Revised source hierarchy

The provider hierarchy is now:

```text
1. CBOE_PUBLIC_EXCHANGE_NATIVE
   First executable pilot: VX contract-level history

2. CME_PUBLIC_DELAYED_OR_FREE_ACCESS_PROBE
   Current public reference pages first
   Historical 2022 access only after a real no-payment acquisition test

3. ICE_PUBLIC_REPORTS_ONLY
   Isolated public evidence allowed
   Full historical package blocked where purchase is required

4. COMMERCIAL_PROVIDER
   Deferred unless genuinely accessible to the owner without circumvention
```

A convenient third-party continuous-futures series cannot inherit exchange-native exactness.

---

## 5. Revised empirical scope

The original 54-row pilot cannot currently receive complete cross-market price linkage.

The immediate empirical scope becomes:

```text
Pilot identity:
CBOE_VX_PUBLIC_CONTRACT_LEVEL_PILOT_V1

Purpose:
Validate end-to-end public exchange-native contract identity,
settlement parsing, lineage, and same-contract return mechanics.

Exactness:
CONSTRUCTIVE_OR_NEAR_EXACT_ENGINEERING_PILOT

Paper replication:
NOT CLAIMED

Economic edge:
NOT TESTED
```

The VX pilot must not be generalized to CME or ICE products.

---

## 6. Stop conditions

The public exchange-native path must stop if:

- the historical contract CSV requires payment or an inaccessible account;
- the downloaded object is not an individual contract-month history;
- settlement cannot be distinguished from close;
- timestamps or contract identifiers are ambiguous;
- the source silently serves a continuous or back-adjusted series;
- source terms prohibit the intended internal research use;
- raw bytes cannot be retained with checksum and retrieval evidence;
- a current page is projected backward as 2022 historical evidence.

---

## 7. Authorization state

```yaml
databento_provider_candidate: false
databento_operationally_rejected: true
circumvention_authorized: false

cboe_public_vx_acquisition: true
cboe_contract_level_parser_design: true
cboe_source_terms_capture: true
cboe_same_contract_formula_validation: true

cme_public_access_probe: true
cme_historical_price_linkage: false
ice_public_report_probe: true
ice_historical_package_purchase: false

price_series_assignment: false
returns_computation: false
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

## 8. Final controlling verdict

```text
DATABENTO ACCESSIBILITY: FAILED FOR OWNER
DATABENTO OPERATIONAL STATUS: REJECTED
CIRCUMVENTION: PROHIBITED
CBOE PUBLIC VX PILOT: AUTHORIZED FOR ACQUISITION AND VALIDATION
CME HISTORICAL 2022 ACCESS: UNVERIFIED
ICE COMPLETE HISTORICAL ACCESS: BLOCKED BY PAID ARCHIVE
PROVIDER CONTRACT IDS: ZERO
PRICE-LINKAGE-AUTHORIZED ROWS: ZERO
RETURNS AUTHORIZED: NO
PAPER REPLICATION: NOT COMPLETE
ECONOMIC EDGE: NOT ESTABLISHED
EDGE-FUT-POSITION-001: INCONCLUSIVE
REPORT 2.4: BLOCKED
```
