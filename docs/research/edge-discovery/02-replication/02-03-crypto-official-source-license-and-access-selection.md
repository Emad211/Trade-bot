# Report 2.3L — Official Crypto Source License and Access Selection

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Decision date:** 2026-07-20  
**Status:** `GO_OKX_BOUNDED_PUBLIC_FUNDING_METADATA_PILOT`

---

## 1. Decision

OKX is selected for the first bounded official crypto-source engineering pilot.

The selection authorizes only a public, unauthenticated, low-volume funding-history metadata pilot for one perpetual instrument. It does not authorize historical backtesting, bulk acquisition, redistribution, raw-data publication, strategy fitting, or trading.

```text
Selected venue: OKX
Selected endpoint family: public funding-rate history
Pilot instrument: BTC-USDT-SWAP
Authentication: none
Pilot purpose: access, schema, timestamp, and safe-handling verification
Raw market rows published: no
Returns computed: no
Economic edge tested: no
```

---

## 2. Why OKX was selected before Binance

### OKX

OKX's historical-data terms explicitly define personal use to include possession, retention, and use of historical data for development of the user's own trading strategy. The license is limited, revocable, non-exclusive, royalty-free, and prohibits redistribution or sublicensing.

The current API agreement permits personal non-commercial market-data use and recognizes unauthenticated public endpoints. It prohibits redistribution, commercial data products, competing analytics services, and excessive automated extraction.

The official public API documents:

- instrument identifiers such as `BTC-USDT-SWAP`;
- funding-rate history;
- realized funding rate;
- settlement timestamp;
- funding formula type;
- funding mechanism;
- public IP-based rate limits.

These properties provide a clearer bounded personal-research path than the currently verified Binance evidence.

### Binance

The official Binance public-data repository provides public archives, programmatic download examples, and per-file checksums. However, the repository's MIT license is not assumed to grant equivalent rights over the underlying market data itself. The market-data license scope and applicable owner/jurisdiction terms remain unresolved.

Binance remains a technical candidate, but is not authorized for raw acquisition or retention by this decision.

---

## 3. Pilot boundary

The first OKX pilot is deliberately narrow:

```text
Endpoint:
GET /api/v5/public/funding-rate-history

Instrument:
BTC-USDT-SWAP

Maximum records:
100

Current endpoint history horizon:
up to three months
```

The pilot will verify:

- HTTP and API success;
- exact source host and request fingerprint;
- response byte count and SHA-256 inside the ephemeral runner;
- top-level response schema;
- required row fields;
- one exact instrument ID;
- SWAP instrument type;
- numeric realized rates;
- millisecond funding timestamps;
- strictly unique funding timestamps;
- descending or ascending deterministic timestamp order;
- observed funding intervals rather than an assumed fixed eight-hour interval;
- absence of secrets or authenticated credentials;
- deletion of raw response bytes before artifact upload.

---

## 4. Safe-content policy

The repository and public GitHub Actions artifacts may retain only safe evidence:

- endpoint identity;
- request fingerprint;
- retrieval time;
- HTTP status;
- content type;
- raw response byte count;
- raw response SHA-256;
- row count;
- schema field names and schema fingerprint;
- minimum and maximum timestamps;
- observed interval counts;
- validation results;
- non-promotional verdicts.

They may not contain:

- raw funding rows;
- funding-rate values;
- a reconstructable ordered market-data series;
- account or API credentials;
- redistributed OKX market data.

Raw bytes must be deleted inside the ephemeral runner after validation and before evidence upload.

---

## 5. Important temporal limitation

The standard public funding-rate-history endpoint returns data only up to three months. Therefore this pilot cannot establish:

- March 2022 historical funding acquisition;
- point-in-time instrument metadata for 2022;
- historical availability at a 2022 decision time;
- a complete basis strategy dataset;
- any historical return.

The separate OKX historical-data download service advertises funding data from March 2022 onward, but its exact file delivery, identity, and safe-retention workflow must be independently verified before use.

---

## 6. Revocation and deletion obligation

The OKX historical-data license is revocable. If the license is revoked or expires, retained copies must be deleted. Any future private immutable storage design must therefore include:

- source-license version;
- license retrieval timestamp;
- revocation/deletion state;
- delete-by-policy support;
- no public redistribution.

This requirement prevents the project from labeling OKX content as permanently immutable without qualification.

---

## 7. Authorization

```yaml
okx_public_funding_metadata_pilot: true
okx_unauthenticated_low_volume_access: true
okx_ephemeral_raw_validation: true
okx_safe_hash_metadata_artifact: true
okx_public_raw_row_artifact: false
okx_bulk_historical_download: false
okx_private_long_term_retention: false
okx_2022_historical_funding_dataset: false
okx_returns_computation: false
binance_raw_acquisition: false
binance_retention: false
empirical_fitting: false
parameter_tuning: false
paper_trading: false
live_trading: false
capital_deployment: false
report_2_4_full_authorization: false
```

---

## 8. Stop conditions

The pilot must fail closed if:

- the endpoint requires authentication;
- the final host leaves the official OKX domain;
- HTTP or API status is unsuccessful;
- the instrument ID differs;
- rows contain missing or malformed required fields;
- timestamps duplicate or cannot be ordered;
- raw data remain in uploaded artifacts;
- the request volume exceeds the predeclared bound;
- terms or access conditions change materially.

---

## 9. Final verdict

```text
OKX LICENSE CLARITY FOR BOUNDED PERSONAL RESEARCH: PASS
OKX PUBLIC ENDPOINT IDENTITY: VERIFIED
OKX BOUNDED FUNDING METADATA PILOT: AUTHORIZED
OKX RAW DATA PUBLICATION: PROHIBITED
OKX 2022 HISTORICAL DATASET: NOT ACQUIRED
BINANCE LICENSE SCOPE: UNRESOLVED
CRYPTO RETURNS: NOT AUTHORIZED
EDGE-CRYPTO-BASIS-001: INCONCLUSIVE
EDGE-CRYPTO-RV-001: INCONCLUSIVE
```
