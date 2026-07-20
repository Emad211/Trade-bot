# Report 2.3K — CME Historical Settlement Access and Website-Data Decision

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Decision date:** 2026-07-20  
**Status:** `BLOCKED_LICENSE_AND_OWNER_ACCESS`

---

## 1. Final operational decision

CME Group is not an authorized historical contract-price source for this project under the currently verified access and terms evidence.

```text
Source family:
CME_PUBLIC_DELAYED_WEBSITE_AND_DATAMINE

Historical 2022 contract-level settlement acquisition:
BLOCKED

Website-data systematic extraction:
NOT AUTHORIZED

Private raw retention for the intended research pipeline:
NOT AUTHORIZED

CFTC-to-CME price linkage:
NOT AUTHORIZED

Historical returns:
NOT AUTHORIZED
```

This is an operational compliance decision for this repository. It is not legal advice and it is not a claim that CME data quality is poor.

---

## 2. Official access evidence

The official Daily Bulletin page exposes the previous trade date and states that preliminary bulletin data updates at approximately midnight Central Time on the following business day, with the final bulletin updating at 10:00 a.m. Central Time.

The same page directs historical Daily Bulletin access to CME DataMine rather than exposing a public historical file archive.

CME DataMine describes the historical-data workflow as:

1. select data;
2. create an account or log in to place an order;
3. request a data license;
4. receive and access the data.

The DataMine page characterizes historical access as a self-service purchase and extraction process. A one-time historical period is an order, not an anonymously downloadable public artifact.

The official settlement-access FAQ states that:

- website product-page settlement data are delayed until midnight Central Time and then available to view;
- historical flat-file delivery is through DataMine;
- DataMine retrieval is associated with licensing and DataMine fees;
- users are directed to create a CME Group login and start an ordering process.

The former public settlement FTP directory no longer contains the historical settlement files required by this project. The directory currently exposes only a technical subdirectory, an empty marker file, and legal text. The former bulletin directory returns not found.

---

## 3. Terms evidence

The CME Data Terms of Use classify settlement prices, volume, open interest, bid/ask, open, close, high/low, and related information as CME Data.

The terms permit only personal non-commercial website use in the form presented. They state that non-commercial use does not include software development or machine-learning/AI development without prior written consent.

Without prior written authorization, the terms prohibit activities required by this project, including:

- collecting or copying CME Data;
- systematic retrieval;
- electronic extraction or scrubbing;
- compiling datasets or databases;
- downloading other than view-only links;
- modifying or creating derivative works;
- using CME Data in software or AI development;
- using website automation to retrieve or analyze CME Data.

The intended repository workflow requires reproducible automated acquisition, private content-addressed retention, parser development, combination with CFTC positioning data, construction of derived returns, and permanent lineage evidence. Those activities are not authorized by the verified public website terms.

---

## 4. Why current delayed website values are insufficient

Current delayed product-page settlement values do not establish access to the exact 2022 contract-month files required for the replication.

They also do not prove:

- the historical value vintage visible at each 2022 decision time;
- an effective-dated contract chain;
- a reproducible historical raw artifact;
- permission to retain or process the data in this software repository;
- a contract-level same-contract price series with immutable lineage.

A current page may not be projected backward as historical evidence.

---

## 5. Exactness consequence

Report 2.1 requires licensed price data for complete traditional-futures return replication.

CME product roots in the CFTC instrument registry do not provide provider contract identifiers or historical contract-month price observations. Root resemblance is not sufficient.

No CME row may receive:

```text
provider_contract_id
price_linkage_authorized=true
return_series_id
```

No continuous or back-adjusted third-party series may inherit CME exchange-native exactness.

---

## 6. Re-entry conditions

CME may re-enter review only if one of the following is obtained and documented:

1. written CME permission or an executed license covering automated acquisition, private electronic retention, software processing, combination with CFTC data, internal derived returns, and reproducibility evidence; or
2. a separate official CME delivery channel whose license explicitly permits the complete intended internal-research workflow and is genuinely accessible to the project owner without false identity, unavailable payment methods, or circumvention.

The re-entry package must also provide exact 2022 contract identities, settlement semantics, historical publication timing, and immutable artifact lineage.

---

## 7. Current authorization

```yaml
cme_public_page_manual_reference: true
cme_terms_and_access_research: true
cme_automated_website_extraction: false
cme_historical_datamine_order: false
cme_raw_retention: false
cme_contract_price_linkage: false
cme_returns_computation: false
cme_empirical_fitting: false
paper_trading: false
live_trading: false
capital_deployment: false
```

---

## 8. Final verdict

```text
PUBLIC CURRENT REFERENCE PAGE: AVAILABLE
ANONYMOUS HISTORICAL 2022 FLAT FILE: NOT AVAILABLE
DATAMINE LOGIN/ORDER/LICENSE PATH: CONFIRMED
WEBSITE DATA SOFTWARE/AI USE WITHOUT WRITTEN CONSENT: NOT AUTHORIZED
HISTORICAL CONTRACT PRICE SOURCE: BLOCKED
PRICE LINKAGE: NOT AUTHORIZED
RETURNS: NOT AUTHORIZED
EDGE-FUT-POSITION-001: INCONCLUSIVE
```
