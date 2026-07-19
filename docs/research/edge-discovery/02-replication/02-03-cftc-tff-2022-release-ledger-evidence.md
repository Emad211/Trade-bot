# Report 2.3D — Verified CFTC TFF 2022 Release-Ledger Evidence

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Parent:** [Report 2.3 controlling status](02-03-current-controlling-status.md)  
**Evidence date:** 2026-07-19  
**Status:** `SCHEDULE_RECONSTRUCTED_AND_ACTIONS_STAGED; ACTUAL_HISTORICAL_RELEASE_TIMES_UNVERIFIED`

---

## 1. Decision

The project now has a deterministic release ledger for every report date in the verified official 2022 CFTC Traders in Financial Futures — Futures Only archive.

The ledger is not represented as a historical actual-publication ledger. CFTC states that COT reports are generally published at 3:30 p.m. Eastern on the third business day after the Tuesday as-of date, while also stating that a complete historical list of release dates is not maintained. Accordingly:

- `scheduled_release_time` is reconstructed from the official CFTC rule and the official 2022 federal-holiday calendar;
- `actual_release_time` remains null for all 52 rows;
- `provisional_available_at` is scheduled release plus a five-minute parser allowance;
- `conservative_available_at` is the next federal business day at 3:30 p.m. Eastern;
- no row is allowed to claim `actual_release_verified=true`.

This is the first usable timing contract for `EDGE-FUT-POSITION-001`, but it does not establish a position signal, a return, a paper replication, or an economic edge.

---

## 2. Source lineage

The report-date calendar comes from the previously verified official CFTC archive:

```text
Source archive:
fut_fin_txt_2022.zip

Archive SHA-256:
94c9c1fdee9dfbe377a09923ddfe26b88d3460605dd076081f221ad367d88601

Text member:
FinFutYY.txt

Member SHA-256:
7c309cb76da8bf432e1a347e5bfde169bcac31cec4e9e33742cf3a078328bb3b

Schema SHA-256:
fe0123051e8e5f5bb8f0cf4a870b451951bd4fa131777096eb5d028115545d42
```

Official rule and calendar evidence:

- CFTC COT guidance: reports are generally released Friday at 3:30 p.m. Eastern using the immediately preceding Tuesday's data; the historical description also identifies the release as the third business day after the as-of date.
- OPM 2022 federal-holiday schedule: the frozen holiday calendar used to identify non-business days.
- CFTC historical special announcements: the 2022 entry records contract-name shortening but no COT release-delay event.
- CFTC also states that it does not maintain a complete list of historical release dates. This limitation is preserved rather than silently replaced by inference.

---

## 3. Deterministic release rule

For each report date `t`:

```text
processing_business_days = first three US federal business days after t
scheduled_release_date   = third processing business day
scheduled_release_time   = 15:30 America/New_York
provisional_available_at = scheduled_release_time + 5 minutes
conservative_available_at = next federal business day at 15:30 America/New_York
```

Weekends and the frozen OPM-observed federal holidays are excluded from the processing-day count.

The ledger explicitly distinguishes:

```text
scheduled_release_time
provisional_available_at
conservative_available_at
actual_release_time
```

The last field is empty in every row.

---

## 4. Ledger identity

```text
Filename:
cftc_tff_futures_only_2022_release_ledger.csv

Rows:
52

Byte count:
16914

SHA-256:
4196c1444a6f9fe878c131f79d5bb4827100b5727baefd1b23333d29babccb40

First report date:
2022-01-04

Last report date:
2022-12-27

Actual release times verified:
0
```

The CSV is stored in the successful GitHub Actions artifact and is deterministically reproducible from the committed source archive parser and release-ledger code. Its bytes were independently rehashed outside the runner.

---

## 5. Eastern-time and DST verification

```text
Rows released under Eastern Standard Time (-05:00):
18

Rows released under Eastern Daylight Time (-04:00):
34
```

Examples:

```text
Report date: 2022-01-04
Scheduled Eastern time: 2022-01-07T15:30:00-05:00
Scheduled UTC time:     2022-01-07T20:30:00Z
```

```text
Report date: 2022-09-13
Scheduled Eastern time: 2022-09-16T15:30:00-04:00
Scheduled UTC time:     2022-09-16T19:30:00Z
```

The workflow hard-fails if these conversions change.

---

## 6. Federal-holiday delays

Exactly two 2022 report dates require a delayed scheduled release under the third-business-day rule.

### Veterans Day

```text
Report date:
2022-11-08

Processing business days:
2022-11-09
2022-11-10
2022-11-14

Skipped federal holiday:
2022-11-11 — Veterans Day

Scheduled release:
2022-11-14T15:30:00-05:00
2022-11-14T20:30:00Z
```

### Thanksgiving Day

```text
Report date:
2022-11-22

Processing business days:
2022-11-23
2022-11-25
2022-11-28

Skipped federal holiday:
2022-11-24 — Thanksgiving Day

Scheduled release:
2022-11-28T15:30:00-05:00
2022-11-28T20:30:00Z
```

No other report date in the official 2022 archive is classified as holiday-delayed by this rule.

---

## 7. Frozen pilot timing

For the already derived 54-row pilot:

```text
Report date:
2022-09-13

Scheduled release:
2022-09-16T15:30:00-04:00
2022-09-16T19:30:00Z

Provisional availability:
2022-09-16T19:35:00Z

Conservative availability:
2022-09-19T15:30:00-04:00
2022-09-19T19:30:00Z

Actual release verified:
false
```

A research path using this pilot must declare which timing field it uses. It may not silently convert the scheduled or provisional field into an actual-release claim.

---

## 8. Successful hosted verification

```text
Workflow:
CFTC TFF 2022 Release Ledger

Run ID:
29683053593

Workflow conclusion:
SUCCESS

Branch head commit:
254eb75e37bfcd69bf2a51314254d7d72614198e

Pull-request merge-test commit recorded by Actions:
1aefd0c4f2b892b626a407ae4cd9a2d2d774e4ac
```

Every dedicated workflow step passed:

- checkout and Python 3.11 setup;
- dependency installation;
- Ruff;
- strict mypy;
- historical-ingestion, historical-parser, and release-ledger tests;
- official annual ZIP acquisition;
- release-ledger derivation;
- independent source/hash/count/DST/holiday/timing verification;
- source-plus-ledger bundle upload;
- staging-receipt creation and upload.

The repository-wide legacy `ci` and `Replication Integrity` workflows remain separate and are not represented as passing.

---

## 9. Actions staging evidence

### Source and release-ledger bundle

```text
Artifact ID:
8441186298

Artifact digest:
d71233533837dc367e2161293ec5e381f33a316e2e055a96bb89c3199ecf294c

Retention expiry:
2026-10-17
```

### Receipt

```text
Artifact ID:
8441186496

Artifact digest:
577ba3fffa7b8bfadb5ee4a9eacb9bd6aeb0f1126cab8a68e8c6fe8a149b6f2b

Retention expiry:
2026-10-17
```

Both artifact ZIP digests were independently recomputed after downloading them outside the Actions runner and matched GitHub's recorded digests.

Current storage state:

```text
ACTIONS_ARTIFACT_STAGED_RETENTION_90_DAYS
```

This is not long-term immutable storage.

---

## 10. Evidence classification

```text
Official 2022 report-date calendar: CONFIRMED
Official CFTC release rule: CONFIRMED
Official OPM 2022 holiday calendar: CONFIRMED
Scheduled release reconstruction: CONFIRMED
DST conversion: CONFIRMED
Holiday-delay reconstruction: CONFIRMED
Release-ledger SHA-256: CONFIRMED
Independent artifact rehash: CONFIRMED
Actual historical release times: NOT VERIFIED
Long-term immutable storage: NOT COMPLETE
Artifact audit pass: NOT GRANTED
Paper replication pass: NOT GRANTED
Economic edge: NOT ESTABLISHED
```

---

## 11. Authorization consequence

This evidence authorizes:

- use of the release ledger for continued CFTC data engineering;
- explicit comparison of provisional versus conservative availability policies;
- construction of the CFTC contract-market-code to tradable-instrument mapping;
- planning of point-in-time futures-price linkage;
- later PRE-versus-historical publication cross-check when the API is reliable.

It does not authorize:

- treating scheduled times as verified actual times;
- fitting a position signal;
- selecting a strategy;
- Report 2.4 full sensitivity analysis;
- paper trading;
- live trading;
- leverage;
- capital deployment.

`EDGE-FUT-POSITION-001` remains empirically `INCONCLUSIVE`.
