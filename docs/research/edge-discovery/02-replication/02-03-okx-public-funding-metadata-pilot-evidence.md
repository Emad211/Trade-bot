# Report 2.3M — Verified OKX Public Funding Metadata Pilot

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Decision date:** 2026-07-20  
**Status:** `PUBLIC_ENDPOINT_AND_SAFE_METADATA_PIPELINE_VERIFIED`

---

## 1. Result

The first bounded OKX public funding-history pilot completed successfully in a GitHub-hosted runner.

The pilot establishes:

- unauthenticated official endpoint accessibility;
- bounded retrieval for one explicit perpetual instrument;
- response and schema identity evidence;
- funding timestamp ordering and interval validation;
- strict prevention of raw-row persistence and publication;
- independent inspection of the uploaded safe artifact.

It does not establish a historical 2022 dataset, basis returns, funding PnL, or an economic edge.

---

## 2. Source contract

```text
Venue:
OKX

Official host:
www.okx.com

Endpoint:
/api/v5/public/funding-rate-history

Instrument:
BTC-USDT-SWAP

Instrument type:
SWAP

Authentication:
None

Requested maximum rows:
100
```

The official endpoint documentation states that this endpoint returns funding history for up to three months and that `fundingTime` is the settlement time in Unix milliseconds. The response distinguishes predicted `fundingRate` from actual `realizedRate`.

---

## 3. Hosted verification

```text
Workflow:
OKX Public Funding Metadata Pilot

Run ID:
29760010859

Conclusion:
SUCCESS
```

Completed hosted steps:

- Python 3.11 environment;
- repository dependency installation;
- Ruff;
- strict mypy;
- six bounded unit tests;
- official unauthenticated endpoint request;
- response validation;
- independent safe-evidence inspection;
- safe artifact upload.

---

## 4. Observed safe evidence

```text
HTTP status:
200

API code:
0

Content type:
application/json;charset=UTF-8

Response byte count:
19568

Response SHA-256:
34996b90d7f1157024861e63a9a8666d08e08a31705390a53d0b98338541605c

Rows validated:
100

Unique funding timestamps:
100

Timestamp order:
DESCENDING

Observed interval:
28800 seconds x 99
```

The observed eight-hour interval is an empirical result for this returned window. It is not coded as a universal assumption because OKX documents that funding frequency may change for some contracts.

---

## 5. Schema evidence

Observed schema fields:

```text
formulaType
fundingRate
fundingTime
instId
instType
method
realizedRate
```

```text
Schema field count:
7

Schema SHA-256:
9e8a8e8502b0af8cf3a4d5645b786888906ee9c2de0a9d4a03133aa9297322bb
```

The validator required every row to match `BTC-USDT-SWAP` and `SWAP`, required finite decimal funding fields, required millisecond timestamps, rejected duplicates, and rejected nondeterministic ordering.

---

## 6. Safe artifact evidence

```text
Artifact ID:
8468365676

Artifact name:
okx-public-funding-safe-evidence-d20eb8d94e146f0270ec8da0e7c69618f36ca3d1

Artifact digest:
872710f6a4b306d4f1113aaecbcfbab460f2b4ef5cad909187c9b1e4a60116c3

Retention expiry:
2026-10-18
```

The artifact was downloaded and independently inspected outside the Actions runner.

It contains exactly:

```text
okx-funding-probe-evidence.json
safe-evidence-receipt.json
```

Independent file evidence:

```text
okx-funding-probe-evidence.json
bytes: 1214
SHA-256: ea1deaff4e31ce2de38638752ae518309342dcdc46c722391e158f8dc0764131

safe-evidence-receipt.json
bytes: 543
SHA-256: 4ad7f74d011561001d120394d00b83be020e3d12995f09a82084b0c877b61b66
```

No raw funding row, ordered funding-rate series, funding-rate value, API credential, or account information is present.

---

## 7. License and handling state

OKX historical-data terms explicitly allow personal possession, retention, and strategy development, while prohibiting redistribution and sublicensing. The license is revocable and requires deletion if revoked or expired.

The public API agreement also limits market data to personal non-commercial use and prohibits redistribution and excessive automated extraction.

Therefore the current handling state is:

```text
Ephemeral low-volume validation: permitted
Safe hash/profile evidence: retained
Public raw-row artifact: prohibited
Bulk acquisition: not authorized
Private long-term raw retention design: not complete
Deletion-on-revocation control: required
```

---

## 8. Binance comparison

The existing Binance pilot is technically broader and validates provider checksums for multiple BTCUSDT archives. However:

- raw retention remains unauthorized;
- the market-data license scope is not considered resolved merely because the helper repository is MIT-licensed;
- the latest observed Binance hosted run failed during ephemeral acquisition and did not produce successful safe evidence on that run.

This does not prove Binance is unusable. It means OKX currently has the clearer verified personal-retention language and the successful current hosted access result.

---

## 9. Limitations

This pilot cannot establish:

- March 2022 funding data acquisition;
- exact historical instrument metadata in 2022;
- mark/index/spot alignment;
- funding cash-flow accounting;
- trading fees or execution costs;
- a complete basis dataset;
- a basis or relative-value return;
- an economic edge.

The standard public endpoint is limited to recent history. The separate historical-data service requires a distinct file-delivery and retention audit before any 2022 dataset is admitted.

---

## 10. Authorization consequence

```yaml
okx_public_endpoint_access: true
okx_bounded_metadata_validation: true
okx_safe_evidence_retention: true
okx_historical_download_delivery_probe: true
okx_raw_publication: false
okx_bulk_raw_retention: false
okx_2022_dataset_admission: false
basis_computation: false
funding_pnl_computation: false
returns_computation: false
empirical_fitting: false
paper_trading: false
live_trading: false
capital_deployment: false
report_2_4_full_authorization: false
```

---

## 11. Final verdict

```text
OFFICIAL OKX PUBLIC ENDPOINT: VERIFIED
UNAUTHENTICATED ACCESS: VERIFIED
BOUNDED SAFE PIPELINE: VERIFIED
RAW ROW LEAKAGE: NOT OBSERVED
CURRENT FUNDING SCHEMA: VERIFIED
2022 HISTORICAL FUNDING DATA: NOT ACQUIRED
RETURNS: NOT COMPUTED
EDGE-CRYPTO-BASIS-001: INCONCLUSIVE
EDGE-CRYPTO-RV-001: INCONCLUSIVE
ECONOMIC EDGE: NOT ESTABLISHED
```
