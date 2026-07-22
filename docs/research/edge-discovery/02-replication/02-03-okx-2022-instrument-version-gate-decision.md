# Report 2.3P — OKX 2022 Instrument-Version Gate Decision

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Issue:** `#51`  
**Decision date:** 2026-07-21  
**Primary outcome:** `BLOCKED_INSTRUMENT_VERSION_HISTORY`  
**Independent secondary blocker:** `BLOCKED_ARCHIVE_AVAILABILITY_TIMING`

Machine-readable decision:

- [OKX 2022 instrument-version gate decision](02-03-okx-2022-instrument-version-gate-decision.yaml)

---

## 1. Decision

Issue #51 is complete as a blocked gate.

The project cannot uniquely reconstruct the historically effective `BTC-USDT-SWAP` instrument and funding-rule contract for March 2022 without unsupported continuity assumptions.

Even if the instrument-version gap were later closed, the specific monthly archive has an independent timing blocker: its first public availability is not verified, and the currently delivered representation records a `Last-Modified` value in 2026.

The selected allowed outcome is therefore:

```text
BLOCKED_INSTRUMENT_VERSION_HISTORY
```

The archive-timing blocker remains explicit rather than being collapsed into the primary decision.

---

## 2. Evidence supporting the primary block

### Original specification

The dated 2019 launch notice records:

```text
Public live time: 2019-12-16T06:00:00Z
Settlement currency: USDT
Face value: 0.0001 BTC
Tick size: 0.1
```

### Effective 2020 face-value change

The dated March 2020 notice records:

```text
0.0001 BTC → 0.01 BTC
Scheduled window: 2020-03-20T08:00:00Z–08:30:00Z
```

### 2020 funding-rule evidence

The dated October 2020 notice records:

```text
Interest component: 0
BTC lower clamp: -0.375%
BTC upper clamp: +0.375%
```

### Open 2021 change-history gap

The May 2021 notice proposed:

```text
0.01 BTC → 0.001 BTC
Scheduled time: 2021-05-25T09:00:00Z
```

The same source states that the adjustment was postponed and provides no replacement time.

A focused official-source search in English and Chinese located the postponement but not a completion, cancellation, or replacement notice. The project does not interpret search absence as proof that `0.01 BTC` continued unchanged.

### Later and current evidence is not backdated

The currently rendered guide published in June 2022 displays `0.01 BTC` and a `0.1` tick size, but the page has subsequently been revised and postdates the target month.

The current instrument endpoint also displays:

```text
ctType: linear
ctVal: 0.01
ctValCcy: BTC
settleCcy: USDT
tickSz: 0.1
lotSz: 0.01
minSz: 0.01
```

These remain current-only negative controls.

The endpoint's `listTime` and `contTdSwTime` do not match the dated public launch time. Therefore those fields are not reinterpreted as historical listing semantics.

---

## 3. Evidence supporting the independent archive-timing block

The current archive catalogue labels perpetual funding data as available from March 2022 onward. That label identifies the earliest partition in the current catalogue, not the publication time of a specific file.

The project verified:

```text
Historical-data service existence by: 2023-10-26
Historical batch API module by: 2025-09-02
Current retrieval of March 2022 file: July 2026
```

The current file representation also returned:

```text
Last-Modified: 2026-02-07T11:42:16Z
ETag: "C107A7D014AA053CF61713BD33876C7C"
```

This metadata does not prove first publication on February 7, 2026. It does prove that the current byte representation cannot be assumed to be an unchanged 2022 vintage.

Consequently:

```text
Specific-file first publication time: unverified
Original 2022 object version: unverified
Later backfill or replacement: not excluded
Current bytes backdated to 2022: prohibited
```

The only defensible `available_at` for the current representation remains the verified current retrieval time.

---

## 4. What the verified funding file still establishes

The block does not invalidate the file's bounded technical identity.

The project still verified:

```text
ZIP SHA-256: ce4fe9aaf1dfdee16e1d11cdabcbb405eb348966902950db1ca862dc86779013
CSV SHA-256: 508195adcc2fd9e9a1978926d8da89af4054d79de4675268cbfb2ac9539e73da
Rows / unique timestamps: 93 / 93
Observed interval: exactly 8 hours
Timestamp range: 2022-02-28T16:00:00Z → 2022-03-31T08:00:00Z
```

The file can remain a candidate for explicitly retrospective, non-causal replication under the private revocable-retention contract. It cannot be represented as contemporaneously available data for a strategy operating in 2022.

---

## 5. Consequence for the research program

```text
Historical causal use of the monthly archive: blocked
Point-in-time March 2022 contract: blocked
Bulk acquisition: not authorized
Public raw artifact: not authorized
Redistribution: not authorized
Basis calculation: not authorized
Funding PnL: not authorized
Returns: not authorized
Empirical fitting: not authorized
Parameter tuning: not authorized
Strategy testing: not authorized
Paper/live trading: not authorized
Capital deployment: not authorized
Report 2.4: blocked
```

Dependent hypothesis verdicts remain:

```text
EDGE-CRYPTO-BASIS-001: INCONCLUSIVE
EDGE-CRYPTO-RV-001: INCONCLUSIVE
```

No economic pass is created by closing this gate.
