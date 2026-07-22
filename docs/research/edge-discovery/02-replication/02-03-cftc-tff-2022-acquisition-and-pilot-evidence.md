# Report 2.3C — Verified CFTC TFF 2022 Acquisition and Dated Pilot Evidence

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Parent:** [Report 2.3 controlling status](02-03-current-controlling-status.md)  
**Evidence date:** 2026-07-18  
**Status:** `RAW_OFFICIAL_ARTIFACT_ACQUIRED_AND_ACTIONS_STAGED; DATED_PILOT_DERIVED_AND_VERIFIED`

---

## 1. Decision

The project has now completed its first real official-data acquisition and deterministic derived-data pipeline.

The acquired source is the official CFTC annual historical compressed Text archive for the **Traders in Financial Futures — Futures Only** report family for calendar year 2022.

The work completed here is:

1. official source download in a GitHub-hosted runner;
2. raw ZIP preservation;
3. raw ZIP byte count and SHA-256;
4. ZIP CRC validation;
5. member-path, encryption, and size-safety checks;
6. member-level byte count, CRC32, and SHA-256;
7. exact parser binding to the acquired ZIP and member identities;
8. exact schema count and schema fingerprint;
9. full-year row, date, key, and accounting diagnostics;
10. deterministic derivation of the report-date pilot for `2022-09-13`;
11. independent rehash and row-level verification outside the GitHub Actions runner;
12. staging of raw and derived bundles in GitHub Actions artifacts for 90 days.

This work does **not** constitute:

- long-term immutable storage;
- an `ARTIFACT_AUDIT_PASS` under the full Report 2.2 contract;
- a cross-check against the CFTC Public Reporting Environment API;
- a paper-level empirical replication;
- a return or strategy result;
- evidence of a trading edge.

---

## 2. Official source identity

```text
Source ID:
CFTC_TFF_FUTURES_ONLY_HISTORICAL_TEXT_2022

Report family:
TFF_FUTURES_ONLY

Year:
2022

Official source URL:
https://www.cftc.gov/files/dea/history/fut_fin_txt_2022.zip
```

The source is an annual historical compressed Text archive published by the CFTC.

---

## 3. Successful hosted acquisition run

```text
Workflow:
CFTC TFF Historical 2022 Ingestion

Run ID:
29655608183

Workflow conclusion:
SUCCESS

Head branch:
agent/edge-research-reports
```

Every dedicated job step completed successfully:

- checkout;
- Python 3.11 setup;
- dependency installation;
- repository Ruff checks for the ingestion path;
- strict mypy for the ingestion module;
- ingestion unit tests;
- official ZIP download;
- independent ZIP and member hash verification;
- raw bundle upload;
- staging-receipt creation and upload.

The repository-wide legacy `ci` and `Replication Integrity` workflows were not green on this research branch. Their failures are not reclassified as successes. The dedicated CFTC acquisition workflow is the only hosted acquisition evidence claimed here.

---

## 4. Raw official ZIP evidence

```text
Raw filename:
fut_fin_txt_2022.zip

Raw byte count:
494559

Raw SHA-256:
94c9c1fdee9dfbe377a09923ddfe26b88d3460605dd076081f221ad367d88601

HTTP status:
200

Content type:
application/zip

Last-Modified:
Thu, 15 Jan 2026 17:02:23 GMT
```

The raw ZIP was independently downloaded from the successful Actions artifact and rehashed outside the runner. The independently computed SHA-256 matched the acquisition manifest.

ZIP CRC verification returned no failing member.

---

## 5. Text-member evidence

The archive contains exactly one non-directory member:

```text
Member name:
FinFutYY.txt

Uncompressed byte count:
2105659

Compressed byte count:
494437

CRC32:
7c783c41

Member SHA-256:
7c309cb76da8bf432e1a347e5bfde169bcac31cec4e9e33742cf3a078328bb3b
```

The member SHA-256 was independently recomputed outside the Actions runner and matched both the ZIP inventory and derivation manifest.

---

## 6. Actions staging evidence

### Raw acquisition bundle

```text
Artifact ID:
8432769852

Artifact name:
cftc-tff-historical-2022-a136191a0e68225cb8eed559eb4c0cef2482d810

Actions artifact digest:
d718393c4984a63be874ed72b4dcc0b2173f29717e4339d02b83e1f9ed614270

Retention expiry:
2026-10-16
```

### End-to-end raw and dated-pilot bundle

```text
Workflow:
CFTC TFF 2022 Pilot Derivation

Run ID:
29656055991

Workflow conclusion:
SUCCESS

Artifact ID:
8432902155

Artifact name:
cftc-tff-2022-raw-and-pilot-d9b25f814b3f383bbac6b408744ff07fb6c504a9

Actions artifact digest:
391a7bc682f02e0feec735342b33ae6a63a59c0db9432ee9812e4ebe17c83184

Retention expiry:
2026-10-16
```

### End-to-end staging receipt

```text
Receipt artifact ID:
8432902321

Receipt artifact digest:
49cbd8b7d2863e915291468652dc7cfecdac28364723cde40a29aa5d1fbb773c
```

GitHub Actions artifacts are deletable and retention-limited. Therefore the storage state is:

```text
ACTIONS_ARTIFACT_STAGED_RETENTION_90_DAYS
```

It is not labeled `IMMUTABLE_INGESTED`.

---

## 7. Exact annual parser contract

The parser is bound to:

```text
Archive SHA-256:
94c9c1fdee9dfbe377a09923ddfe26b88d3460605dd076081f221ad367d88601

Member SHA-256:
7c309cb76da8bf432e1a347e5bfde169bcac31cec4e9e33742cf3a078328bb3b

Schema field count:
87

Schema SHA-256:
fe0123051e8e5f5bb8f0cf4a870b451951bd4fa131777096eb5d028115545d42
```

A changed provider file must receive a new artifact identity and parser-contract version. It may not silently inherit this evidence.

---

## 8. Full-year parsed profile

```text
Data rows:
2719

Unique report-date/contract keys:
2719

Report dates:
52

First report date:
2022-01-04

Last report date:
2022-12-27

Futures-only rows:
2719
```

No duplicate report-date/contract key was observed.

### Open-interest reconciliation finding

Exact equality diagnostics across the full year found:

```text
Rows with a long-side unit difference:
37

Rows with a short-side unit difference:
33

Rows with any accepted consolidated unit difference:
56

Material accounting failures:
0
```

Every nonzero difference was exactly `+1` or `-1` and confined to three consolidated market codes whose contract-market code ends in `+`:

- `12460+` — DJIA Consolidated;
- `13874+` — S&P 500 Consolidated;
- `20974+` — NASDAQ-100 Consolidated.

The parser records these differences. It does not erase them or misreport them as exact equality. A difference is a material hard failure if:

- its absolute magnitude exceeds one contract;
- or it occurs outside a market identified as consolidated by both code and market name.

No material failure was observed in the acquired 2022 archive.

This rule is an empirical parser contract for this artifact version. It is not a general claim that every future CFTC archive may differ by one.

---

## 9. Frozen dated pilot

The first derived pilot is frozen at:

```text
Report date:
2022-09-13
```

Pilot profile:

```text
Rows:
54

Unique CFTC contract-market codes:
54

Minimum contract-market code:
020601

Maximum contract-market code:
43874A

Long exact-reconciliation differences:
0

Short exact-reconciliation differences:
0

Material accounting failures:
0
```

The pilot retains all 87 source fields and is deterministically sorted by stripped `CFTC_Contract_Market_Code`.

Derived file:

```text
tff_futures_only_2022-09-13.canonical.csv

Byte count:
27954

SHA-256:
1be0028ba872ed56c970f6cd67b76c480b3653b170762c6e55f39dc10c3d268b
```

The pilot SHA-256 was computed in the Actions runner, independently rechecked in the same workflow, and independently recomputed again after downloading the Actions artifact.

---

## 10. Implementation and workflow evidence

Implementation:

```text
src/hybrid_trader/replication/cftc_historical_ingestion.py
src/hybrid_trader/replication/cftc_historical_parser.py
scripts/ingest_cftc_tff_historical_2022.py
scripts/derive_cftc_tff_2022_pilot.py
```

Tests:

```text
tests/test_cftc_historical_ingestion.py
tests/test_cftc_historical_parser.py
```

Dedicated workflows:

```text
.github/workflows/cftc-tff-historical-2022-ingestion.yml
.github/workflows/cftc-tff-2022-pilot-derivation.yml
```

The end-to-end derivation workflow passed:

- Ruff;
- strict mypy;
- eight combined ingestion/parser unit tests;
- official ZIP acquisition;
- raw and member identity checks;
- schema checks;
- annual parser checks;
- pilot derivation;
- independent raw/member/schema/profile/pilot verification;
- raw-plus-derived artifact upload;
- staging-receipt upload.

---

## 11. PRE API result

The CFTC Public Reporting Environment endpoint for dataset `gpe5-46if` was confirmed reachable in some contexts, but repeated GitHub-hosted attempts were unreliable and frequently returned HTTP 503.

The PRE API path is therefore classified as:

```text
API_IDENTITY_VERIFIED
GITHUB_RUNNER_RELIABILITY_FAILED
ROW_LEVEL_CROSS_CHECK_PENDING
```

The PRE API acquisition workflow is not used as evidence of successful raw ingestion. The successful evidence in this report comes from the official annual historical compressed archive.

---

## 12. Current evidence classification

```text
Official source identity: CONFIRMED
Raw ZIP acquisition: CONFIRMED
Raw ZIP SHA-256: CONFIRMED
ZIP CRC: CONFIRMED
Member SHA-256: CONFIRMED
Exact schema identity: CONFIRMED
Annual parser profile: CONFIRMED
Dated pilot derivation: CONFIRMED
Pilot SHA-256: CONFIRMED
Independent artifact rehash: CONFIRMED
Actions staging: CONFIRMED
Long-term immutable storage: NOT COMPLETE
PRE API row-level cross-check: NOT COMPLETE
Artifact audit pass: NOT GRANTED
Paper replication pass: NOT GRANTED
Economic edge: NOT ESTABLISHED
```

---

## 13. Authorization consequence

This evidence authorizes:

- continued CFTC data engineering;
- effective-dated release-ledger construction;
- row-level PRE-versus-historical cross-check when the API becomes reliable;
- parser extension to additional frozen years under separate artifact identities;
- linkage planning to licensed futures price instruments.

It does not authorize:

- empirical fitting;
- parameter search;
- strategy selection;
- Report 2.4 full sensitivity analysis;
- paper trading;
- live trading;
- leverage;
- capital deployment.

All six edge hypotheses remain empirically `INCONCLUSIVE`.