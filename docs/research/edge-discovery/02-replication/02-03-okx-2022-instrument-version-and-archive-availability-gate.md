# Report 2.3N — OKX BTC-USDT-SWAP 2022 Instrument-Version and Archive-Availability Gate

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Issue:** `#51`  
**Status date:** 2026-07-21  
**Status:** `OPEN — HISTORICAL INSTRUMENT VERSION AND ARCHIVE AVAILABLE_AT NOT YET FROZEN`  
**Machine-readable companion:** [gate manifest](02-03-okx-2022-instrument-version-and-archive-availability-gate.yaml)

---

## 1. Purpose

Issue #50 established that OKX currently delivers a real March 2022 funding archive for the `BTC-USDT` perpetual family and that one bounded owner-controlled private pilot can be governed by a revocable-retention contract.

That result does **not** establish either of the following:

1. the exact contract specification and funding-rule version effective during March 2022; or
2. the time at which the monthly archive first became available to a historical decision-maker.

Issue #51 separates these questions from delivery and retention.

The gate must prevent two distinct forms of backdating:

```text
current instrument metadata → projected into March 2022
current archive downloadability → projected into March 2022
```

Neither projection is allowed.

---

## 2. Parent evidence

The verified parent artifact is:

```text
Instrument family: BTC-USDT
Provider contract identity in file: BTC-USDT-SWAP
Partition label: 2022-03
ZIP SHA-256: ce4fe9aaf1dfdee16e1d11cdabcbb405eb348966902950db1ca862dc86779013
CSV SHA-256: 508195adcc2fd9e9a1978926d8da89af4054d79de4675268cbfb2ac9539e73da
Rows / unique funding timestamps: 93 / 93
Minimum timestamp: 2022-02-28T16:00:00Z
Maximum timestamp: 2022-03-31T08:00:00Z
Observed spacing: 8 hours for all 92 intervals
```

These observations establish that the delivered file contains an eight-hour settlement grid. They do not establish:

- contract face value;
- minimum order size;
- tick size;
- funding formula;
- cap and floor;
- index composition;
- mark-price formula;
- margin tiers;
- liquidation rules; or
- archive publication time.

---

## 3. Official evidence currently located

### 3.1 March 2020 face-value adjustment

Official source:

`https://www.okx.com/help/adjustment-of-face-value-for-usdt-margined-perpetual-swap-futures-trading`

The dated announcement states that the BTCUSDT perpetual-swap face value was scheduled to change from:

```text
0.0001 BTC → 0.01 BTC
```

during:

```text
2020-03-20 08:00–08:30 UTC
```

This is the last located affirmative effective-value announcement before the unresolved 2021 proposal.

It does not prove that `0.01 BTC` remained unchanged through March 2022.

### 3.2 Postponed May 2021 proposal

Official source:

`https://www.okx.com/help/postponement-of-face-value-adjustment`

The notice describes a proposed BTCUSDT perpetual-swap face-value change:

```text
0.01 BTC → 0.001 BTC
```

originally scheduled for:

```text
2021-05-25 09:00 UTC
```

The same official page states that the adjustment was postponed and that a new time would be announced later.

Consequences:

- `0.001 BTC` cannot be treated as effective merely because it appeared in the proposal;
- `0.01 BTC` cannot be assumed to have remained effective merely because the proposal was postponed;
- an official completion, cancellation, replacement, migration, or later specification is needed to close the gap.

### 3.3 Perpetual guide published June 2022

Official source:

`https://www.okx.com/help/i-perpetual-swaps`

The current page records an original publication date of 2022-06-20 and a later update date. It currently describes the BTCUSDT perpetual contract as:

```text
Underlying: BTC/USDT index
Settlement currency: USDT
Contract size: 0.01 BTC
Tick size: 0.1
Trading hours: 24/7
Funding times: 00:00, 08:00, 16:00 UTC
```

This source is useful but not sufficient for the March 2022 verdict because:

1. its publication date is after the pilot month;
2. the live page has been updated after publication;
3. the project does not yet have a frozen June 2022 page vintage;
4. a nearby later state is not proof of the preceding state.

### 3.4 Current historical-data page

Official source:

`https://www.okx.com/en-gb/historical-data`

The current page states that perpetual funding-rate history is available from March 2022 onward.

This establishes the lower label of the current archive catalogue. It does not establish:

- whether the March 2022 file was published during March 2022;
- whether it was published after month-end;
- whether it was introduced much later as a backfill;
- whether the current file bytes match an originally published version;
- any historical decision-time `available_at`.

### 3.5 Current public instrument endpoint

Current API candidate:

`https://www.okx.com/api/v5/public/instruments?instType=SWAP&instId=BTC-USDT-SWAP`

This endpoint may be used only as:

```text
CURRENT_SCHEMA_AND_IDENTITY_NEGATIVE_CONTROL
```

It cannot supply March 2022 values unless OKX provides versioned historical metadata or a dated source independently confirms each field.

---

## 4. Preliminary field-level status

| Field | Current evidence | March 2022 status |
|---|---|---|
| Provider instrument ID | Filename and current identifier use `BTC-USDT-SWAP` | Strong candidate; version lineage still required |
| Instrument type | `SWAP` in official delivery request | Verified for delivered family |
| Settlement currency | Nearby June 2022 guide says USDT | Not yet frozen for March 2022 |
| Linear/inverse status | USDT-margined structure strongly implies linear | Not yet frozen from a dated March source |
| Contract face value | 2020 effective notice says `0.01 BTC`; 2021 `0.001 BTC` proposal postponed; June 2022 guide currently says `0.01 BTC` | Open change-history gap |
| Tick size | June 2022 guide currently says `0.1` | Not yet frozen for March 2022 |
| Lot/minimum order size | Current API can report present values | Historical values unresolved |
| Funding interval | 93 verified timestamps on an exact eight-hour grid | Verified empirically for the delivered March partition |
| Funding settlement times | Grid corresponds to 00:00, 08:00, 16:00 UTC | Verified empirically |
| Funding formula | Later/current documentation exists | March 2022 formula unresolved |
| Funding cap/floor | Contract-dependent and historically mutable | Unresolved |
| Mark/index dependencies | General mechanism documented | Exact March 2022 versions unresolved |
| Listing/activation date | Contract predates located 2020 adjustment | Exact original listing evidence unresolved |
| Archive publication time | Current file is downloadable now | Historical `available_at` unresolved |

---

## 5. Required version registry

Every accepted contract field must eventually be represented as:

```yaml
field_name: contract_face_value
value: "..."
effective_from: "..."
effective_to: "... or null"
source_id: "..."
source_published_at: "..."
retrieved_at: "..."
source_sha256: "..."
evidence_class: OFFICIAL_DATED_EFFECTIVE_NOTICE
historical_use_authorized: true_or_false
```

Rules:

- a current API response has `historical_use_authorized: false`;
- a proposed but postponed change has `historical_use_authorized: false`;
- a dated effective announcement may authorize only the fields and interval it actually establishes;
- an unclosed change-history gap blocks the affected field;
- no field may be filled by “most likely” inference.

---

## 6. Archive-availability contract

The following times must remain separate:

```text
funding settlement time
partition label
file object creation time
file publication time
catalogue listing time
retrieval time
research available_at
```

Current evidence proves only:

```text
retrieval succeeded in July 2026
provider currently labels funding history as available from March 2022
```

Until stronger evidence is found, the conservative policy is:

```text
historical archive available_at = current verified retrieval time
```

This policy prevents historical use of the monthly file and therefore blocks any claim that a strategy operating in 2022 could have consumed the archive contemporaneously.

The raw funding settlements may still be useful later for non-causal paper reconstruction, but only after the research protocol labels them as retrospectively obtained data rather than contemporaneously available data.

---

## 7. Required next evidence

1. Official completion, cancellation, or replacement history for the postponed 2021 face-value adjustment.
2. A dated instrument specification effective no later than March 2022.
3. Historical tick size, lot size, minimum order size, settlement currency, and linear/inverse status.
4. Funding formula, interest component, cap/floor, and settlement policy effective in March 2022.
5. Version history for mark price, index price, and premium-index dependencies.
6. Object metadata or dated provider evidence for the monthly archive's first publication.
7. Evidence distinguishing an original contemporaneous file from a later backfill.
8. Content hashes and retrieval timestamps for every official source used.

---

## 8. Allowed outcomes

```text
GO_OKX_2022_POINT_IN_TIME_INSTRUMENT_CONTRACT
BLOCKED_INSTRUMENT_VERSION_HISTORY
BLOCKED_ARCHIVE_AVAILABILITY_TIMING
```

A `GO` outcome requires both:

1. a sufficiently complete point-in-time instrument version for the intended calculation; and
2. an explicit availability policy that does not backdate current retrieval.

If the instrument contract can be reconstructed but archive timing cannot, the gate remains blocked by archive availability.

---

## 9. Explicit non-authorization

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
```

---

## 10. Current verdict

```text
Verified March 2022 funding settlement grid: YES
Verified bounded file identity: YES
Verified private revocable retention mechanism: YES
March 2022 contract version fully reconstructed: NO
Funding formula version fully reconstructed: NO
Historical archive publication available_at verified: NO
Current download backdated to 2022: NO
Issue #51 final outcome: NOT YET ASSIGNED
All dependent edge hypotheses: INCONCLUSIVE
```
