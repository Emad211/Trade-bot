# Edge Discovery Research Program

This directory is the durable research memory for the second-generation trading-system project. Earlier asset, model, market, and timeframe choices are not constraints unless they are re-established by evidence in this program.

## Objective

Build a defensible path from economic hypotheses to a live trading system without confusing prediction accuracy, backtest profitability, hidden risk premia, public-source visibility, or execution assumptions with genuine exploitable edge.

## Research tree

### 1. Edge Map — Complete

| Report | Scope | Status |
|---|---|---|
| [1.1 — Edge Definition and Proof Standard](01-edge-map/01-01-edge-definition-and-proof-standard.md) | Edge definition, evidence hierarchy, rejection gates, and hypothesis contract | Complete |
| [1.2 — Taxonomy of Edge Mechanisms](01-edge-map/01-02-taxonomy-of-edge-mechanisms.md) | Risk premia, behavioral, information, relative-value, liquidity, execution, and risk-policy mechanisms | Complete |
| [1.3 — Market, Instrument, Horizon, Competition, and Capacity Map](01-edge-map/01-03-market-instrument-horizon-competition-capacity-map.md) | Realistic venues, horizons, competition, and capacity | Complete |
| [1.4 — Falsification and Evidence Design](01-edge-map/01-04-falsification-and-evidence-design.md) | Negative controls, trial accounting, prospective tests, stress, and kill criteria | Complete |
| [1.5 — Edge Map Synthesis and Replication Admissions](01-edge-map/01-05-edge-map-synthesis.md) | Ranked hypotheses, admissions, deferrals, rejections, and Section 2 handoff | Complete |

Machine-readable admissions: [replication admission manifest](01-edge-map/01-05-replication-admission-manifest.yaml).

Admitted research identities:

- `EDGE-FUT-CARRY-001`
- `EDGE-FUT-TREND-001`
- `EDGE-CRYPTO-BASIS-001`
- `EDGE-FUT-POSITION-001`
- `EDGE-RISK-POLICY-001`
- `EDGE-CRYPTO-RV-001`

Admission authorizes research replication only. It does not authorize fitting, tuning, strategy tournaments, paper/live trading, leverage, automatic promotion, or capital deployment.

### 2. Research Replication — Partially complete

| Report | Scope | Status |
|---|---|---|
| [2.1 — Anchor Papers, Opposing Evidence, Modern Updates, Data, and Replication-Code Selection](02-replication/02-01-anchor-opposition-code-selection.md) | Paper roles, exactness classes, data routes, code admission, table targets, and kill criteria | Complete |
| [2.2 — Data, Timing, and Information-Contract Reconstruction](02-replication/02-02-data-timing-information-contract-reconstruction.md) | Availability clocks, licenses, immutable artifacts, instruments, releases, rolls, crypto versions, lineage, and costs | Complete |
| [2.3 — Current Controlling Status](02-replication/02-03-current-controlling-status.md) | Verified foundations, blockers, bounded source profiles, and prospective source-version monitoring | Partially complete |
| 2.4 — Sensitivity, Cost, Failure, and Disagreement Analysis | Conditional analysis after artifact, timing, instrument, price, and return gates pass | Blocked |
| 2.5 — Replication dossier and continue/stop decisions | Final Section 2 synthesis | Planned |

## Current Report 2.3 state

Verified foundations include:

- official CFTC 2022 TFF Futures Only acquisition, exact 87-field parser, 2,719-row annual profile, and deterministic dated pilot;
- a fail-closed 52-row CFTC release ledger with zero claimed actual historical release times;
- a 54-row reporting-to-product registry with zero provider contract IDs and zero authorized price linkages;
- bounded Cboe VX, OKX, and Binance source-contract pilots with safe evidence only;
- verified OKX March 2022 funding archive identity, schema, timestamp grid, deletion proof, and private revocable-retention controls;
- a completed OKX historical instrument/version gate that refused to backdate current metadata;
- an append-only, content-addressed OKX prospective registry with two verified observations for both the instrument and funding-source streams;
- verified prospective spot, swap, mark, and index source-linkage metadata with non-monotonic provider-cache timing preserved;
- an owner-controlled private four-source sampling contract and a disabled-by-default one-batch runner, both validated synthetically with zero real raw execution;
- a fail-closed account-fee, per-fill, funding-bill, position-aggregate, and current funding-formula accounting contract;
- repository-wide static analysis, unit testing, package-smoke, and dedicated source workflows.

Gate outcomes:

```text
Issue #50: CLOSED — GO_PRIVATE_REVOCABLE_2022_FUNDING_PILOT
Issue #51: CLOSED — BLOCKED_INSTRUMENT_VERSION_HISTORY
Independent Issue #51 blocker: BLOCKED_ARCHIVE_AVAILABILITY_TIMING
Issue #52: CLOSED — GO_PROSPECTIVE_OKX_POINT_IN_TIME_REGISTRY
Issue #53: CLOSED — GO_PROSPECTIVE_OKX_PRICE_LINKAGE_METADATA_PILOT
Issue #54: CLOSED — GO_OWNER_CONTROLLED_PRIVATE_OKX_SAMPLING_CONTRACT
Issue #55: CLOSED — GO_OWNER_SIDE_OKX_ONE_BATCH_RUNNER_READY
Issue #56: CLOSED — GO_OKX_FEE_AND_FUNDING_ACCOUNTING_CONTRACT
Independent Issue #56 blocker: BLOCKED_ACCOUNT_SPECIFIC_FEE_SNAPSHOT
```

The GO outcomes are deliberately narrow. They authorize prospective source/version monitoring, safe metadata linkage, tested private-retention and owner-runner contracts, and synthetic accounting validation. They do not repair history, execute a real raw batch, acquire owner fee rates, or authorize basis, funding PnL, returns, numerical transaction costs, fitting, tuning, strategy tests, paper/live trading, leverage, Report 2.4, or capital deployment.

Current hard blockers:

```text
Traditional-futures provider contract chains and point-in-time prices: INCOMPLETE
Databento owner accessibility: REJECTED
Cboe raw retention / canonical historical timing: BLOCKED
CME historical route: BLOCKED_LOGIN_ORDER_FEE_AND_LICENSE
ICE complete history: BLOCKED_PAID_ARCHIVE
OKX March 2022 complete instrument/version history: BLOCKED
OKX March 2022 archive publication available_at: BLOCKED
Real owner-controlled OKX raw batch: NOT EXECUTED
Owner-account-specific fee snapshot: BLOCKED_OWNER_READ_ONLY_CREDENTIALS
Executable-price / spread / slippage / impact / latency contract: INCOMPLETE
Binance persistent raw retention and historical available_at: OPEN GATES
Basis / funding PnL / returns / transaction costs: NOT AUTHORIZED
Paper-level numerical replication: NOT COMPLETE
Economic edge: NOT ESTABLISHED
Report 2.4: BLOCKED
```

All six hypothesis verdicts remain `INCONCLUSIVE`.

## Report 2.3 evidence index

### Core verification

- [Current controlling status](02-replication/02-03-current-controlling-status.md)
- [Initial controlled execution snapshot](02-replication/02-03-controlled-empirical-and-code-replication.md)
- [Replication execution manifest](02-replication/02-03-replication-execution-manifest.yaml)
- [Independent reality verification and correction log](02-replication/02-03-independent-reality-verification-log.md)
- [Static analysis, test, and coverage verification](02-replication/02-03-static-analysis-and-test-verification.md)

### CFTC source, timing, and identity

- [Verified CFTC acquisition and dated-pilot evidence](02-replication/02-03-cftc-tff-2022-acquisition-and-pilot-evidence.md)
- [Machine-readable CFTC acquisition evidence](02-replication/02-03-cftc-tff-2022-evidence.yaml)
- [Verified release-ledger evidence](02-replication/02-03-cftc-tff-2022-release-ledger-evidence.md)
- [Machine-readable release-ledger evidence](02-replication/02-03-cftc-tff-2022-release-ledger-evidence.yaml)
- [Verified instrument-registry evidence](02-replication/02-03-cftc-tff-2022-instrument-registry-evidence.md)
- [Machine-readable instrument-registry evidence](02-replication/02-03-cftc-tff-2022-instrument-registry-evidence.yaml)

### Traditional-futures provider gates

- [Provider price-linkage candidate evidence](02-replication/02-03-provider-price-linkage-candidate-evidence.md)
- [Databento zero-purchase probe evidence](02-replication/02-03-databento-zero-purchase-probe-evidence.md)
- [Owner-accessible exchange-native source pivot](02-replication/02-03-owner-accessible-exchange-native-source-pivot.md)
- [Verified Cboe VX public contract pilot](02-replication/02-03-cboe-vx-public-contract-pilot-evidence.md)
- [CME public access and license gate](02-replication/02-03-cme-public-access-and-license-gate.md)

### Crypto source, retention, historical, and prospective gates

- [Official crypto source, license, and access selection](02-replication/02-03-crypto-official-source-license-and-access-selection.md)
- [Verified OKX public funding metadata pilot](02-replication/02-03-okx-public-funding-metadata-pilot-evidence.md)
- [OKX 2022 funding delivery and retention gate](02-replication/02-03-okx-2022-funding-delivery-and-retention-gate.md)
- [OKX private revocable retention contract](02-replication/02-03-okx-private-revocable-retention-contract.yaml)
- [OKX 2022 instrument/version and archive-availability gate](02-replication/02-03-okx-2022-instrument-version-and-archive-availability-gate.md)
- [OKX 2022 gate decision](02-replication/02-03-okx-2022-instrument-version-and-archive-availability-decision.md)
- [OKX prospective point-in-time registry gate](02-replication/02-03-okx-prospective-point-in-time-registry-gate.yaml)
- [Initial prospective registry evidence](02-replication/02-03-okx-prospective-registry-initial-evidence.yaml)
- [Initial prospective registry snapshot](02-replication/02-03-okx-prospective-registry-initial-snapshot.json)
- [Second prospective registry evidence](02-replication/02-03-okx-prospective-registry-second-evidence.yaml)
- [Second prospective registry snapshot](02-replication/02-03-okx-prospective-registry-second-snapshot.json)
- [Verified prospective price-linkage metadata](02-replication/02-03-okx-prospective-price-linkage-metadata-evidence.md)
- [Owner-controlled private synchronized-sampling contract](02-replication/02-03-okx-private-synchronized-sampling-contract-evidence.md)
- [Disabled owner-side one-batch runner](02-replication/02-03-okx-owner-side-one-batch-runner-evidence.md)
- [Verified fee and funding accounting contract](02-replication/02-03-okx-fee-and-funding-accounting-contract-evidence.md)
- [Verified Binance BTCUSDT ephemeral pilot](02-replication/02-03-binance-btcusdt-public-ephemeral-pilot-evidence.md)

### Key workflows

- `.github/workflows/ci.yml`
- `.github/workflows/replication-integrity.yml`
- `.github/workflows/cftc-tff-historical-2022-ingestion.yml`
- `.github/workflows/cftc-tff-2022-release-ledger.yml`
- `.github/workflows/cftc-tff-2022-instrument-registry.yml`
- `.github/workflows/okx-2022-instrument-version-source-audit.yml`
- `.github/workflows/okx-prospective-registry-initial-snapshot.yml`
- `.github/workflows/okx-prospective-registry-second-snapshot.yml`
- `.github/workflows/okx-prospective-price-linkage-metadata-pilot.yml`
- `.github/workflows/okx-private-revocable-retention-contract.yml`
- `.github/workflows/okx-private-synchronized-sampling-contract.yml`
- `.github/workflows/okx-owner-side-one-batch-runner.yml`
- `.github/workflows/okx-fee-accounting-contract.yml`
- `.github/workflows/binance-btcusdt-public-ephemeral-pilot.yml`

### 3. Dataset and Experiment System

| Report | Scope | Status |
|---|---|---|
| 3.1 | Point-in-time universe, markets, venues, and sources | Planned |
| 3.2 | Immutable storage, provenance, vintages, and versioning | Planned |
| 3.3 | Labels, execution semantics, and all-in cost contract | Planned |
| 3.4 | Sealed benchmarks, experiment registry, and audit design | Planned |
| 3.5 | Final research dataset audit and release | Planned |

### 4. Strategy Tournament

All reports remain planned and unauthorized.

### 5. Live Trading System

All reports remain planned and unauthorized.

## Governance rules

- Negative results and access blockers are retained permanently.
- Historical evidence may qualify a candidate for prospective testing but cannot prove a live edge.
- Data availability, executable prices, costs, failure modes, capacity, owner accessibility, and license terms are part of the hypothesis.
- Current metadata may not be projected backward.
- Missing provider timestamps remain null.
- Observation gaps are not interpolated and continuity is not inferred.
- A reporting code is not automatically a tradable instrument.
- A product root is not a provider contract-chain identity.
- Public visibility is not permission to retain, redistribute, mine, combine, or derive returns.
- Safe evidence may retain hashes and non-market metadata while raw and derived market rows remain absent.
- A green engineering workflow may establish a blocker or a safe metadata contract rather than an empirical pass.
- An artifact-audit pass is not a paper-replication pass.
- A paper-replication pass is not an economic-edge pass.
- No admitted hypothesis is proven until it survives genuinely new forward data and realistic execution.
- The final outcome may legitimately be to reject every candidate.

## Branch

These reports are developed on `agent/edge-research-reports` through draft PR #41. The PR remains draft and is not authorized for merge until the remaining Report 2.3 gates and final synchronization checks are complete.
