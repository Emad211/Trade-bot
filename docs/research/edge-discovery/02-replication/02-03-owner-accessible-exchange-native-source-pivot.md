# Report 2.3H — Owner-Accessible Exchange-Native Price-Source Pivot

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Parent:** [Provider-probe controlling addendum](02-03-provider-probe-controlling-addendum.md)  
**Decision date:** 2026-07-20  
**Status:** `DATABENTO_REJECTED; CBOE_BLOCKED; CME_BLOCKED; CRYPTO_OFFICIAL_SOURCE_PIVOT_REQUIRED`

---

## 1. Controlling decision

Traditional-futures historical price linkage remains blocked for this project owner under the currently verified sources.

Databento is operationally inaccessible to the owner without unavailable payment/account capabilities. The project will not use false identity information, borrowed payment methods, third-party accounts, shared credentials, misleading residence data, or jurisdiction/payment circumvention.

Cboe's public VX engineering pilot remains valid, but historical return use is blocked because the verified public terms do not authorize the required retention and derivative workflow, and the exact historical website-publication timestamp is not established.

CME is also blocked as a historical price source. Current delayed website values are reference-only; historical files route through DataMine account/order/license workflows, and the verified CME Data Terms do not authorize the intended systematic software/AI extraction, dataset compilation, derivative construction, and private retention without written consent.

ICE complete historical end-of-day packages remain paid and operationally inaccessible to the owner.

The next authorized source-search scope is therefore official crypto exchange data whose terms and delivery mechanism genuinely permit reproducible acquisition, private retention, checksum lineage, and internal derived research.

---

## 2. Non-negotiable accessibility and license gate

Every future source must pass all of the following:

```text
OWNER_ACCESSIBLE_WITHOUT_FALSE_IDENTITY
NO_UNAVAILABLE_FOREIGN_PAYMENT_METHOD_REQUIRED
NO_SANCTIONS_OR_JURISDICTION_CIRCUMVENTION
TERMS_AND_LICENSE_REVIEWED
AUTOMATED_ACQUISITION_EXPLICITLY_ALLOWED_OR_NOT_PROHIBITED
PRIVATE_RETENTION_ALLOWED
INTERNAL_DERIVED_RESEARCH_ALLOWED
RAW_BYTES_ACQUIRABLE
CHECKSUM_AND_LINEAGE_PRESERVABLE
POINT_IN_TIME_INSTRUMENT_IDENTITY_AVAILABLE
PRICE_OR_SETTLEMENT_SEMANTICS_EXPLICIT
HISTORICAL_AVAILABLE_AT_CONTRACT_AVAILABLE
```

Public URL accessibility alone does not pass this gate.

---

## 3. Traditional-futures source decisions

### 3.1 Databento

```text
Technical suitability: previously selected
Owner operational accessibility: failed
Final classification: OPERATIONALLY_REJECTED_OWNER_ACCESS_CONSTRAINT
Provider accepted: false
Purchase authorized: false
Price linkage authorized: false
```

### 3.2 Cboe Futures Exchange

```text
Public contract parser pilot: completed
Engineering evidence: valid
Private raw retention: not authorized
Historical publication timing: not verified
Historical return path: BLOCKED_LICENSE_OR_TIMING
```

Controlling records:

- `02-03-cboe-vx-license-and-historical-availability-decision.md`
- `02-03-cboe-vx-license-and-historical-availability-decision.yaml`
- Issue `#44`

### 3.3 CME Group

```text
Current delayed public reference pages: available
Historical 2022 anonymous flat-file access: not verified and not exposed
Historical route: DataMine account/order/license
Automated website extraction for intended software/AI workflow: not authorized
Historical return path: BLOCKED_LICENSE_AND_OWNER_ACCESS
```

Controlling records:

- `02-03-cme-historical-access-and-license-decision.md`
- `02-03-cme-historical-access-and-license-decision.yaml`
- Issue `#49`

### 3.4 ICE Futures U.S.

```text
Public report navigation: available
Complete historical 2022 end-of-day package: purchase or subscription required
Owner payment accessibility: unavailable
Historical return path: BLOCKED_PAID_ARCHIVE
```

---

## 4. Revised source hierarchy

```text
1. OFFICIAL_CRYPTO_EXCHANGE_ARCHIVE_OR_API
   Terms and retention review first
   Exact instrument-version and contract semantics required
   Bounded immutable pilot only after legal/access gate passes

2. WRITTENLY_LICENSED_TRADITIONAL_FUTURES_SOURCE
   Re-enter only after explicit permission or accessible executed license

3. PUBLIC_REFERENCE_PAGES
   Metadata and manual verification only
   No raw retention, automated extraction, or price linkage unless terms permit

4. COMMERCIAL_PROVIDER
   Deferred unless genuinely accessible without circumvention
```

A third-party continuous-futures series cannot inherit exchange-native or point-in-time exactness.

---

## 5. Next authorized empirical scope

The next bounded research action is an official crypto-source license and delivery probe for the existing hypotheses:

- `EDGE-CRYPTO-BASIS-001`
- `EDGE-CRYPTO-RV-001`

The first source candidate must be selected by access and terms evidence, not popularity. Candidate families may include official Binance public-data archives and official OKX APIs, but neither is authorized for raw retention or derived research until its exact terms and delivery behavior are reviewed.

The probe must establish:

- official host and source identity;
- anonymous or owner-accessible authentication requirements;
- applicable terms and jurisdiction restrictions;
- automated download/API permission;
- private retention permission;
- internal derived-use permission;
- instrument and contract-version metadata;
- historical timestamps and availability semantics;
- checksum or reproducible content identity;
- bounded pilot size and explicit stop conditions.

---

## 6. Authorization state

```yaml
databento_provider_candidate: false
databento_operationally_rejected: true
cboe_historical_return_source: false
cme_historical_return_source: false
ice_complete_historical_source: false
circumvention_authorized: false

crypto_official_source_terms_probe: true
crypto_official_source_metadata_probe: true
crypto_raw_acquisition: false
crypto_raw_retention: false
crypto_derived_returns: false

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

## 7. Final controlling verdict

```text
DATABENTO: OPERATIONALLY REJECTED
CBOE HISTORICAL RETURN PATH: BLOCKED LICENSE OR TIMING
CME HISTORICAL RETURN PATH: BLOCKED LICENSE AND OWNER ACCESS
ICE COMPLETE HISTORICAL PATH: BLOCKED PAID ARCHIVE
TRADITIONAL-FUTURES PRICE LINKAGE: ZERO AUTHORIZED ROWS
CRYPTO OFFICIAL-SOURCE TERMS PROBE: AUTHORIZED
CRYPTO RAW ACQUISITION: NOT YET AUTHORIZED
RETURNS: NOT AUTHORIZED
PAPER REPLICATION: NOT COMPLETE
ECONOMIC EDGE: NOT ESTABLISHED
REPORT 2.4: BLOCKED
```
