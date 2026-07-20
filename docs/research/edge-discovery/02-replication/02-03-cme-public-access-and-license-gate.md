# Report 2.3I — CME Public Access, Historical Availability, and License Gate

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Parent:** [Owner-accessible exchange-native source pivot](02-03-owner-accessible-exchange-native-source-pivot.md)  
**Decision date:** 2026-07-20  
**Status:** `BLOCKED_LOGIN_ORDER_FEE_AND_LICENSE`

---

## 1. Decision

The bounded public-access probe for CME Group historical settlement data is complete.

The project may view the current website Daily Bulletin and current delayed website settlement references in an ordinary browser. It may not treat those current pages as evidence that exact 2022 historical contract-level settlement files are anonymously downloadable, owner-accessible, licensable for the intended automated research workflow, or available under a permission set that supports private reproducible retention and derived return construction.

The historical path is blocked under the evidence currently available:

```text
CME current website reference pages: PUBLICLY VIEWABLE
CME Historical Daily Bulletin route: DATAMINE
Anonymous exact 2022 file acquisition: NOT ESTABLISHED
CME login requirement: CONFIRMED
Order process: CONFIRMED
License agreement requirement: CONFIRMED
Retrieval/data fees: CONFIRMED
Automated website collection for this project: NOT AUTHORIZED
Private reproducible raw retention: NOT AUTHORIZED
Derived return construction: NOT AUTHORIZED
Owner-accessible no-payment path: NOT ESTABLISHED
Final gate: BLOCKED_LOGIN_ORDER_FEE_AND_LICENSE
```

No CME market-data bytes were downloaded or retained by this probe.

---

## 2. Scope of the probe

The probe was deliberately limited to official public CME Group pages and ordinary public navigation. It did not:

- create or use a CME account;
- submit personal, billing, or jurisdiction information;
- begin an order;
- accept a data license;
- use borrowed credentials or payment methods;
- scrape website market data;
- call undocumented endpoints;
- bypass access controls;
- download a current or historical CME data object;
- compute a return or assign a price to a CFTC row.

The objective was to determine whether a bounded exact 2022 historical settlement object could be obtained anonymously, without payment, and under terms compatible with the project’s required automated, reproducible, private research pipeline.

---

## 3. Official pages reviewed

The probe reviewed only official CME Group sources:

1. Daily Bulletin  
   `https://www.cmegroup.com/market-data/daily-bulletin.html`

2. Access to CME Group Settlement Data FAQ  
   `https://www.cmegroup.com/articles/faqs/access-to-cme-group-settlement-data-faq.html`

3. CME DataMine  
   `https://www.cmegroup.com/datamine.html`

4. CME Data Terms of Use / Market Data Explanation and Disclaimer  
   `https://www.cmegroup.com/trading/market-data-explanation-disclaimer.html`

5. CME Website Terms of Use  
   `https://www.cmegroup.com/tools-information/cme-website-terms-of-use.html`

6. CME Group Data Services Portal — Getting Started  
   `https://www.cmegroup.com/tools-information/webhelp/data-services-portal/Content/GettingStarted.html`

7. CME Group Information Policies  
   `https://www.cmegroup.com/market-data/license-data/information-policies.html`

Evidence was reviewed on 2026-07-20.

---

## 4. Public Daily Bulletin finding

The public Daily Bulletin page exposes the previous trade date’s bulletin and states that:

- the preliminary bulletin updates around midnight Central Time on the following business day;
- the final bulletin updates at 10:00 Central Time on the next business day;
- website market data are reference-only;
- the Historical Daily Bulletin link points to CME DataMine.

This establishes current public viewing behavior. It does not establish anonymous historical 2022 flat-file access, original 2022 publication timestamps, or permission for automated collection and retention.

The project therefore classifies the current page as:

```text
CURRENT_PUBLIC_REFERENCE_ONLY
```

It is not an admitted historical price source.

---

## 5. Historical delivery path

CME’s official settlement-data FAQ states that legacy FTP settlement and bulletin files were moved to DataMine. It maps historical objects such as:

```text
DailyBulletin_pdf_YYYYMMD.zip
cme.settle.YYYYMMDD.csv
cbt.settle.YYYYMMDD.csv
nymex.settle.YYYYMMDD.csv
comex.settle.YYYYMMDD.csv
```

to DataMine products.

The same FAQ states that:

- DataMine is the flat-file delivery route;
- DataMine access requires a CME Group login and an ordering process;
- DataMine retrieval carries a DataMine fee and, depending on use, applicable license fees;
- End-of-Market subscriptions have stated monthly price points;
- the migrated files are accessed through licensing links rather than the former anonymous FTP path.

The DataMine page independently presents the sequence:

```text
create account or login
request a data license
place an order
receive and access data
```

A one-time historical period is described as a one-time order.

Therefore:

```text
ANONYMOUS_HISTORICAL_FILE_ROUTE: NOT FOUND
ACCOUNTLESS_2022_ACQUISITION: NOT ESTABLISHED
ORDERLESS_2022_ACQUISITION: NOT ESTABLISHED
NO_FEE_2022_ACQUISITION: NOT ESTABLISHED
```

---

## 6. Terms and intended-use conflict

The CME Data Terms define website settlement prices, volume, open interest, and related fields as CME Data. The terms permit personal non-commercial viewing in the form presented on the website, while reserving broader rights.

Without prior written authorization, the terms prohibit activities that are central to the proposed research pipeline, including combinations of:

- collecting or copying CME Data;
- electronic extraction or systematic retrieval;
- compiling a database or collection;
- text and data mining;
- modifying or creating derivative works;
- using CME Data in development of software, machine learning, or artificial-intelligence systems;
- using website CME Data to validate or complement CME data feeds.

The project’s required workflow would need to:

1. download exact contract-level historical data;
2. preserve raw bytes in content-addressed storage;
3. repeatedly parse and verify the data;
4. combine it with CFTC positioning records;
5. derive point-in-time features and same-contract returns;
6. retain lineage, checksums, and reproducibility evidence;
7. use code to execute the process.

Those activities are not authorized by ordinary public website viewing permission.

Public visibility is therefore not treated as a research-data license.

---

## 7. Owner-accessibility result

The owner-accessibility gate requires a source to be usable without false identity, unavailable foreign payment methods, credential sharing, or jurisdiction/payment circumvention.

The observed historical route requires account, licensing, ordering, and potentially billing. No verified anonymous and no-payment 2022 route was found.

The project will not:

- provide false identity or residence information;
- use another person’s CME account;
- borrow payment credentials;
- evade jurisdiction or billing controls;
- treat a current browser page as a substitute for licensed historical files;
- scrape market-data pages in conflict with the published terms.

Operational classification:

```text
OWNER_ACCESSIBLE_WITHOUT_FALSE_IDENTITY: UNPROVEN
NO_UNAVAILABLE_PAYMENT_METHOD_REQUIRED: FAILED_OR_UNPROVEN
TERMS_COMPATIBLE_WITH_AUTOMATED_PIPELINE: FAILED
RAW_BYTES_ACQUIRABLE_UNDER_CURRENT_PERMISSION: FAILED
```

---

## 8. Historical timing consequence

Even if current settlement values are visible after midnight Central Time, that fact does not prove:

- the exact contemporaneous availability timestamp of a 2022 historical file;
- that the current website publication process was identical in 2022;
- that a DataMine-retained object preserves its original first-publication timestamp;
- that a product-page value is a valid contract-level executable price for a CFTC release decision.

No `actual_release_time`, `source_update_time`, or historical `available_at` is inferred from current retrospective retrieval.

Timing classification:

```text
CURRENT_DELAYED_PUBLICATION_RULE: DOCUMENTED
2022_ORIGINAL_PUBLICATION_TIMESTAMP: NOT VERIFIED
2022_PROJECT_USABLE_AVAILABLE_AT: NOT ESTABLISHED
```

---

## 9. Exactness consequence

The CFTC TFF reporting rows are report-market aggregates and are not themselves exchange contract identifiers. A valid CME linkage would require, before any return calculation:

- exact DCM and product identity;
- exact maturity-specific contract ID;
- contract specification version;
- settlement field semantics;
- original historical availability time;
- expiry and roll state;
- same-contract holding-price pair;
- a predeclared mapping rule;
- a license compatible with retention and derivation.

No such licensed CME contract-level artifact was acquired.

Therefore:

```text
CME_PROVIDER_CONTRACT_IDS: 0
CFTC_TO_CME_LINKED_ROWS: 0
CME_SETTLEMENT_VALUES_ADMITTED: 0
CME_RETURNS_COMPUTED: 0
```

---

## 10. Current authorization

```yaml
cme_public_page_viewing: true
cme_public_metadata_review: true
cme_terms_review: true
cme_permission_or_license_inquiry_preparation: true

cme_automated_website_collection: false
cme_historical_2022_raw_acquisition: false
cme_private_raw_retention: false
cme_cftc_price_linkage: false
cme_derived_features: false
cme_return_computation: false
cme_empirical_fitting: false

paper_trading: false
live_trading: false
leverage: false
capital_deployment: false
report_2_4_full_authorization: false
```

---

## 11. Re-entry conditions

CME historical data may re-enter the project only if at least one of these paths becomes real and documented:

1. CME provides written permission or an executed agreement covering private electronic retention, automated reproducible processing, combination with CFTC data, internal derived features/returns, and the intended retention period.
2. An official CME product is genuinely accessible to the owner without prohibited circumvention, with a license that explicitly covers the intended workflow.
3. CME publishes a new public downloadable dataset whose terms expressly permit the required automated internal research use and retention.

Before re-entry, the project must record:

- agreement or permission identity;
- permitted use class;
- retention and deletion rules;
- redistribution limits;
- fees and owner accessibility;
- exact product/file identity;
- historical publication-time evidence;
- checksum and storage lineage.

A login page, catalog entry, price quote, or public product page alone is insufficient.

---

## 12. Final controlling verdict

```text
PUBLIC CURRENT DAILY BULLETIN: VIEWABLE REFERENCE
HISTORICAL DAILY BULLETIN: DATAMINE ORDER ROUTE
EXACT 2022 RAW BYTES: NOT ACQUIRED
ANONYMOUS NO-PAYMENT ACCESS: NOT ESTABLISHED
LICENSE FOR AUTOMATED RESEARCH PIPELINE: NOT GRANTED
HISTORICAL AVAILABLE_AT: NOT VERIFIED
CFTC-TO-CME LINKAGE: NOT AUTHORIZED
RETURNS: NOT AUTHORIZED
FINAL CME GATE: BLOCKED_LOGIN_ORDER_FEE_AND_LICENSE
EDGE-FUT-POSITION-001: INCONCLUSIVE
REPORT 2.4: BLOCKED
```

This result is an access, permission, and timing blocker. It is not evidence against the economic hypothesis and is not a statement about the technical quality of licensed CME data.