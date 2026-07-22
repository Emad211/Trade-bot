# Report 2.3 — Final Binance Retention, Publication-Timing, and Version Decision

**Status date:** 2026-07-21  
**Issue:** #59  
**Status:** `BLOCKED_VERIFIED`

## Preserved verified result

The January 2024 BTCUSDT ephemeral pilot remains valid. Six official archive objects and their paired provider checksum objects were downloaded and validated in memory. ZIP identity, provider checksum equality, ZIP safety, schemas, row counts, month boundaries, and timestamp grids were verified. No raw ZIP, CSV, price row, funding row, basis row, or return row was retained.

```text
EPHEMERAL_INTEGRITY_VALIDATION: VERIFIED
```

## Final blockers

```text
PERSISTENT_RAW_RETENTION: BLOCKED_BINANCE_DATA_RIGHTS_CHAIN
REDISTRIBUTION_OR_PUBLIC_DERIVATION: BLOCKED_BINANCE_DATA_RIGHTS_CHAIN
HISTORICAL_OBJECT_AVAILABLE_AT: BLOCKED_BINANCE_OBJECT_PUBLICATION_TIMING
HISTORICAL_INSTRUMENT_VERSION: BLOCKED_BINANCE_INSTRUMENT_VERSION_HISTORY
```

## Why the schedule is insufficient

The official repository states that daily data becomes available the next day and monthly data on the first Monday. This is a generic delivery schedule, not an immutable publication timestamp for an individual object. It cannot prove the exact first time a specific historical ZIP or checksum was public.

The same official source states that archived files may later be updated and provides a replacement log. Therefore current bytes and a current checksum cannot establish which bytes were available at an earlier point in time unless the object has a complete versioned publication lineage.

## Why the license boundary remains blocked

The public-data repository displays an MIT license. That establishes a repository license label but does not, without an explicit archive-data terms chain, prove every intended right for persistent retention, redistribution, publication of derived data, commercial reuse, or future revocation handling. Public downloadability is not treated as a complete data-rights contract.

## Why the instrument boundary remains blocked

A symbol and archive path do not prove a complete point-in-time instrument specification. The evidence does not establish historical tick/lot rules, contract or symbol status, funding-rule identity, or complete delisting/relisting and rule-change lineage for the partition.

## Reopening requirements

The gate may be reopened only with explicit archive-data terms, object-level publication/version evidence, and a point-in-time instrument/rule ledger. A generic schedule, current checksum, repository license label, or current downloadability is insufficient.

## Non-authorization

No additional raw download is required by this decision. Persistent retention, redistribution, historical repair, basis, funding PnL, returns, costs, fitting, strategy testing, Report 2.4, and trading remain unauthorized.

All six hypotheses remain `INCONCLUSIVE`; no economic edge is established.
