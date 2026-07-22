# Report 2.3O — OKX 2022 Instrument Source Identity Audit Evidence

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Issue:** `#51`  
**Evidence date:** 2026-07-21  
**Workflow:** `OKX 2022 Instrument Version Source Audit`  
**Run ID:** `29819157464`  
**Conclusion:** `SUCCESS`  
**Audit verdict:** `SOURCE_IDENTITIES_VERIFIED_NO_HISTORICAL_PROMOTION`

---

## 1. Verification result

The bounded source audit completed successfully with:

```text
Ruff format: PASS
Ruff lint: PASS
Mypy: PASS
Scoped tests: 21 passed
Bounded official-source fetch: PASS
Independent safe-evidence verification: PASS
```

Safe artifact:

```text
Artifact ID: 8490609657
Artifact digest: sha256:1a047568482057b68254d02589e79154980a6b13ea693e05a179d490ac7023cc
Evidence file: okx-2022-instrument-source-audit.json
Evidence bytes: 10,783
Evidence SHA-256: 5ef88fc780ec9280f0e7bf109e00743c50114a60e1aa353f3183f17ea7ab26df
Expiry: 2026-10-19
```

The artifact contains source hashes, marker counts, selected current metadata, and availability classifications only. It contains no raw HTML, full API response, market row, funding-rate value, or reconstructable ordered market series.

Machine-readable evidence:

- [Source-audit evidence](02-03-okx-2022-instrument-source-audit-evidence.yaml)
- [Controlling Issue #51 gate](02-03-okx-2022-instrument-version-and-archive-availability-gate.yaml)

---

## 2. Frozen official source identities

| Source | Date/class | SHA-256 | Permitted role |
|---|---|---|---|
| BTCUSDT perpetual launch notice | 2019-12-16 effective notice | `36c11f44cb93c03a8351fd91aeca44418280018c50c3a75e2d4e7911b70154f3` | Original listing and initial specification |
| BTCUSDT face-value adjustment | 2020-03-04 effective notice | `1362081470574b644b7ac9e0f61837fdbb576493bc229b8f88a795530583bd02` | Face-value change to `0.01 BTC` |
| BTC perpetual funding-rule adjustment | 2020-10-14 effective notice | `4c280b1ee14b4615ed67991517fba5149982fbca3c00ba4d14fc87c665c9c7e5` | Formula/clamp change evidence |
| Face-value postponement | 2021-05-08 postponement | `f9a688937a38c20db3d07ff1fec46aa1dbb84149cb56288a08a779d87213f820` | Evidence that proposed `0.001 BTC` change was not effective from this notice |
| Perpetual guide | 2022-06-20, currently revised | `8850988584350fac87031f34570af6edec87903d1d113b511fabdc836e4d8ef2` | Nearby later-state negative control only |
| Historical-data terms | 2023-10-26 service terms | `002e37e1084dee2155efc1ebaeacc41243a2173e269a293d5a3473fd0bb12e97` | Service-existence and license boundary |
| Current historical-data catalogue | Current page | `2d198cb05f57310acbf833554d9a63bb13c72735b698edc1052758a3879a1ec4` | Current lower-bound label only |
| API changelog | 2025-09-02 changelog | `d9c2f9748de42824d400db7bdd272f0e0482d8e97432c5af07862d3caa95d305` | Separate historical batch-API module boundary |

Source identity verification does not itself promote any field into the historical contract. Promotion requires a field-level effective interval and a closed change history.

---

## 3. Historically dated findings

### 3.1 Original BTCUSDT perpetual launch

The official launch notice records:

```text
Public live time: 2019-12-16 06:00 UTC
Underlying: BTC/USDT index
Settlement currency: USDT
Initial face value: 0.0001 BTC
Tick size: 0.1
Trading hours: 24/7
```

This establishes the original state, not automatically the March 2022 state.

### 3.2 Effective March 2020 face-value change

The official adjustment notice records:

```text
BTCUSDT perpetual face value:
0.0001 BTC → 0.01 BTC

Scheduled effective window:
2020-03-20 08:00–08:30 UTC
```

This is the last located affirmative effective face-value notice before the 2021 open gap.

### 3.3 October 2020 funding-rule evidence

The dated notice establishes a BTC funding-rule change with:

```text
Interest component: 0
BTC lower clamp: -0.375%
BTC upper clamp: +0.375%
Formula class: premium-index moving average minus interest, then clamp
```

The source identity and markers are verified, but the complete formula lineage through March 2022 is not yet closed.

### 3.4 May 2021 postponed proposal

The notice proposed:

```text
0.01 BTC → 0.001 BTC
Original scheduled time: 2021-05-25 09:00 UTC
Status: postponed; replacement time not provided in the notice
```

A focused official-source search in English and Chinese located the postponement but did not locate a completion, cancellation, or replacement notice. Absence of a located notice is **not** treated as proof that the value remained unchanged.

### 3.5 June 2022 guide

The currently rendered guide displays:

```text
Contract size: 0.01 BTC
Tick size: 0.1
Settlement currency: USDT
Funding times: 00:00, 08:00, 16:00 UTC
```

It remains a negative control because it was published after the March partition and the live page has subsequently been revised.

---

## 4. Current API negative control

Current response identity:

```text
Response bytes: 1,079
Response SHA-256: 1ad06f4d8d48b1523e622701762de0a42586072b6f01d98b9e75e8d9b7edb9ec
Fields in response object: 53
```

Selected present values:

```text
instId: BTC-USDT-SWAP
instFamily: BTC-USDT
instType: SWAP
ctType: linear
ctVal: 0.01
ctValCcy: BTC
settleCcy: USDT
tickSz: 0.1
lotSz: 0.01
minSz: 0.01
state: live
```

Time fields:

```text
listTime: 1573557408000 = 2019-11-12T11:16:48Z
contTdSwTime: 1611916860000 = 2021-01-29T10:41:00Z
Official public live time: 2019-12-16T06:00:00Z
```

Neither current time field equals the dated public launch time. Therefore the project does not reinterpret `listTime` or `contTdSwTime` as a historical listing timestamp for March 2022.

All current API values retain:

```text
historical_use_authorized: false
```

---

## 5. Availability boundaries

Three scopes remain separate:

### Service scope

The historical-data terms prove service existence no later than:

```text
2023-10-26
```

This does not prove that the March 2022 funding file existed on that date.

### Module scope

The API changelog proves a separate historical batch-query module no later than:

```text
2025-09-02
```

This does not prove original publication of the web-download file.

### Specific-file scope

For:

```text
BTC-USDT-SWAP-fundingrates-2022-03.zip
SHA-256: ce4fe9aaf1dfdee16e1d11cdabcbb405eb348966902950db1ca862dc86779013
```

historical publication time remains unverified.

Consequently:

```text
current retrieval may be backdated: false
specific-file available_at from this audit: null
```

The conservative research policy remains current verified retrieval time only.

---

## 6. Current blocker state

```text
Primary blocker: BLOCKED_INSTRUMENT_VERSION_HISTORY
Secondary blocker: BLOCKED_ARCHIVE_AVAILABILITY_TIMING
```

The primary blocker remains because the postponed 2021 face-value proposal has no located completion/cancellation/replacement notice and no frozen March 2022 specification closes every required field interval.

The secondary blocker remains because service-level and module-level evidence cannot establish the publication time of one specific archive object.

Issue #51 remains open. No final allowed outcome has yet been assigned.

---

## 7. Non-authorization

```text
Bulk acquisition: no
Public raw artifact: no
Redistribution: no
Basis calculation: no
Funding PnL: no
Returns: no
Empirical fitting: no
Parameter tuning: no
Strategy testing: no
Paper/live trading: no
Capital deployment: no
Report 2.4: blocked
Economic edge verdict: INCONCLUSIVE
```
