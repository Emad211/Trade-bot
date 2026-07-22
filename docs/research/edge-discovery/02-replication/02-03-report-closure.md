# Report 2.3 — Final Closure Matrix and Section 2 Handoff Boundary

**Status date:** 2026-07-21  
**Issue:** #60  
**Current synchronization state:** `COMPLETE_WITH_EXPLICIT_BLOCKERS`  
**Target final outcome:** `COMPLETE_WITH_EXPLICIT_BLOCKERS`

## Executive decision

Report 2.3 has reached substantive closure: every in-scope source, timing, instrument, retention, accounting, execution, and source-health domain has a bounded positive result, an explicit blocker, an owner-input requirement, or a non-authorization decision.

Completion does **not** mean that any hypothesis has passed empirical replication. It means that there is no remaining ambiguous research gate inside Report 2.3.

```text
All six hypothesis verdicts: INCONCLUSIVE
Paper-level empirical replication: NOT COMPLETE
Economic edge: NOT ESTABLISHED
Report 2.4: BLOCKED
```

Issue #60 may be closed only after general CI and Replication Integrity both succeed on the exact synchronized closure head. No repository mutation is permitted after that verification before closure.

## Closure summary

- Total classified domains: 27
- Positive results remain bounded to source, schema, contract, metadata, or synthetic semantics.
- Historical blockers are retained rather than repaired with current metadata.
- Owner-input requirements are separated from research defects.
- Numerical economic work remains prohibited.

## Complete closure matrix

| Domain | Status | Established | Not established | Re-entry condition |
|---|---|---|---|---|
| CFTC 2022 TFF Futures Only acquisition and schema | `VERIFIED` | Official archive identity, exact 87-field parser, 2,719 unique annual rows, deterministic dated pilot. | Tradable return series, maturity-specific contract chain, paper replication, or economic edge. | Requires a separately admitted point-in-time price and contract-chain source before returns. |
| CFTC release ledger and availability timing | `VERIFIED_BOUNDED` | A fail-closed 52-row release ledger with scheduled release identities and zero fabricated timestamps. | Actual historical website/API publication timestamps. | Immutable provider release receipts or contemporaneous timestamp evidence. |
| CFTC reporting-to-product registry | `VERIFIED_BOUNDED` | 54 reporting identities mapped to product-level research identities. | Provider contract IDs, maturity chains, roll rules, or authorized price linkage. | A licensed point-in-time provider contract registry and predeclared roll contract. |
| Databento traditional-futures route | `BLOCKED` | Zero-purchase metadata/access probe and owner-access constraints. | Owner-accessible licensed historical prices or contract chains. | Owner obtains an accessible licensed account/product route. |
| Cboe VX historical price and return route | `BLOCKED` | Parser engineering, settlement-event timing, permission request package, and no-lookahead boundary. | Private retention permission, exact historical publication time, or CFTC-to-VX contract linkage. | Written Cboe permission or executed license covering retention, combination, and derived internal returns. |
| CME historical settlements route | `BLOCKED` | Access, order, fee, and license boundary documented. | Owner-accessible licensed historical settlement chain. | Owner login/order/license route with point-in-time contract data. |
| ICE complete historical archive route | `BLOCKED` | Paid archive boundary documented. | Complete licensed historical archive in the research environment. | Owner-approved paid archive acquisition and license review. |
| Moreira-Muir author-published target series | `VERIFIED` | Official target snapshot, schema, units, missingness, and six-pair volatility-scaling property. | Real-time implementability, recursive performance, costs, or economic edge. | No re-entry needed for the target contract; empirical use requires the recursive gate. |
| Kenneth French current daily factor sources | `VERIFIED_CURRENT_REVISED` | Three official daily source identities, hashes, schemas, units, date ranges, and factor mapping. | Exact paper-era vintage or historical publication timestamps. | Historical daily vintages and publication receipts for exact historical reconstruction. |
| Kenneth French current monthly factor sources | `VERIFIED_CURRENT_REVISED` | Three official monthly source contracts and safe current-snapshot evidence. | Exact paper-era monthly vintage or row-level public redistribution rights. | Vintage-specific official archives and explicit data-rights review. |
| Moreira-Muir current source reconciliation | `VERIFIED_CURRENT_REVISED` | Current daily/monthly factor mapping and revision differences retained as evidence. | Exact historical author input vintage. | Vintage evidence if exact historical replication is pursued. |
| Moreira-Muir recursive real-time reconstruction contract | `VERIFIED_CONTRACT_ONLY` | Leakage-safe recursive policy, burn-in, variance definitions, leverage/cost sensitivity families, trial ledger, and kill criteria frozen before performance. | Performance, Sharpe, alpha, utility, empirical paper replication, or edge. | A separately authorized empirical issue after exact availability, cost, and trial-governance checks. |
| OKX March 2022 funding archive identity | `VERIFIED_BOUNDED` | Archive identity, 93 timestamps, 8-hour grid, private revocable retention/deletion controls. | Historical instrument specification, exact archive first-publication time, basis, PnL, or returns. | Historical version and publication evidence. |
| OKX March 2022 instrument/version history | `BLOCKED` | Known launch/change notices and explicit refusal to backdate current metadata. | Complete March 2022 contract specification. | Contemporaneous official instrument snapshot or versioned archive. |
| OKX historical archive publication available_at | `BLOCKED` | Current object identity and current modification evidence. | First-publication time of the March 2022 object. | Immutable provider publication ledger or contemporaneous receipt. |
| OKX prospective instrument and funding-source registry | `VERIFIED_PROSPECTIVE_ONLY` | Two append-only content-addressed observations with predecessor and stream-tail checks. | Historical backfill or economic calculations. | Continue prospective observations under the same versioned contract. |
| OKX spot/swap/mark/index source linkage | `VERIFIED_METADATA_ONLY` | Exact public source identities, schema fingerprints, clocks, and non-monotonic cache diagnostic. | Retained prices, executable values, basis, or returns. | Owner-controlled raw batch under Issues #54/#55. |
| OKX private synchronized raw-retention lifecycle | `VERIFIED_CONTRACT_ONLY` | Owner-only permissions, leases, content addressing, rollback, deletion receipts, and zero public raw leakage. | A real owner raw batch. | Owner-controlled private storage, encryption keys, and explicit confirmation. |
| OKX disabled owner-side one-batch runner | `OWNER_INPUT_REQUIRED` | Fail-closed retain/delete runner and synthetic lifecycle. | Real network execution or retained real raw batch. | Owner supplies private path, keys, attestations, and exact confirmation. |
| OKX fee, fill, funding-bill, and position accounting | `VERIFIED_SEMANTICS_ONLY` | Account-specific query identities, sign/currency rules, fill chronology, funding subtypes, and anti-double-counting contract. | Owner-account fee rates or numerical costs. | Owner read-only credentials with trading/withdrawal disabled and safe metadata-only snapshot. |
| OKX executable-price, slippage, latency, and cost semantics | `VERIFIED_SEMANTICS_ONLY` | Executable quote identities, fill lifecycle, partial fills, clocks, direction-aware slippage, and non-overlapping cost components. | Real order/book/fill inputs or numerical transaction costs. | Separately authorized prospective execution experiment plus owner fee snapshot. |
| OKX source health, sequence continuity, and sampling abort | `VERIFIED_CONTRACT_ONLY` | 22 health states, explicit policy thresholds, REST error classification, seqId/prevSeqId continuity, checksum-deprecation handling, quarantine, and no carry-forward. | Empirically selected thresholds or real execution use. | Versioned owner policy and separately admitted real sampling/execution context. |
| Binance BTCUSDT public archive integrity pilot | `VERIFIED_EPHEMERAL_ONLY` | Six official objects, provider checksums, ZIP safety, schemas, rows, and timestamp grids verified ephemerally. | Persistent raw retention, exact historical available_at, instrument history, or returns. | Satisfy the three independent Binance blockers. |
| Binance persistent retention and redistribution rights | `BLOCKED` | Public archive access and software-repository license identified. | Complete archive-data rights chain for retention, redistribution, public derivation, or commercial reuse. | Explicit archive-data terms/license covering intended use. |
| Binance object-level historical publication time | `BLOCKED` | General daily/monthly schedule and update-log mechanism. | Exact first-publication timestamp for each historical object. | Immutable object-level publication metadata or contemporaneous receipt. |
| Binance historical instrument/version identity | `BLOCKED` | Archive path and symbol identity. | Complete point-in-time tick/lot/rule/funding/delisting version history. | Versioned official instrument archive for the target period. |
| Basis, funding PnL, returns, costs, and paper-level empirical replication | `NOT_AUTHORIZED` | Prerequisite evidence, blocker map, accounting/execution/health contracts, and re-entry conditions. | Any hypothesis performance, paper replication pass, or economic edge. | Only through a new explicitly authorized gate after all required source/owner inputs pass. |

## Owner-input boundary

The following are not research-document omissions; they require actions or secrets controlled by the owner:

1. owner-controlled private storage, encryption keys, and explicit confirmation for a real OKX raw batch;
2. read-only OKX credentials with trading and withdrawal permissions disabled for account-specific fee metadata;
3. a separately authorized real prospective order/book/fill experiment;
4. licensed/paid traditional-futures data routes where required.

No owner credential, key, account value, or private raw market payload may enter GitHub, Actions logs, or public artifacts.

## Section 2 handoff boundary

Report 2.3 hands Section 2 forward with a complete evidence and blocker map, but it does **not** authorize Report 2.4.

A future Report 2.4 gate must explicitly identify which hypothesis and which source route has satisfied all of the following:

- point-in-time source and instrument identity;
- historical or prospective availability clocks;
- permitted retention and derived use;
- executable-price identity;
- account-specific fee input where applicable;
- source-health and abort policy;
- frozen cost, sensitivity, and trial-accounting contract.

Until a route satisfies those conditions, sensitivity, cost, failure, disagreement, returns, Sharpe, alpha, or utility calculations remain blocked.

## Final synchronization requirement

The closure is provisionally frozen in:

- `02-03-report-closure-matrix.yaml`
- `02-03-report-closure.md`
- `02-03-current-controlling-status.md`
- the program README

The exact closure head must pass both general CI and Replication Integrity. Their run IDs and conclusions are recorded in the Issue #60 closure comment; no repository mutation may occur between that verification and issue closure.
