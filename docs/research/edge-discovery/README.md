# Edge Discovery Research Program

This directory is the durable research memory for the trading-system project. It is intentionally independent of the repository's previous market, asset, model, and timeframe choices. No earlier design decision is treated as a constraint unless it is re-established by evidence in this program.

## Objective

Build a defensible path from economic hypotheses to a live trading system without confusing prediction accuracy, backtest profitability, hidden risk premia, public-source visibility, or execution assumptions with a genuine exploitable edge.

## Research Tree

### 1. Edge Map — Complete

| Report | Scope | Status |
|---|---|---|
| [1.1 — Edge Definition and Proof Standard](01-edge-map/01-01-edge-definition-and-proof-standard.md) | Formal definition of edge, evidence hierarchy, hard rejection gates, and required hypothesis contract | Complete |
| [1.2 — Taxonomy of Edge Mechanisms](01-edge-map/01-02-taxonomy-of-edge-mechanisms.md) | Risk premia, behavioral mispricing, information, relative value, liquidity provision, execution, and risk-policy edge | Complete |
| [1.3 — Market, Instrument, Horizon, Competition, and Capacity Map](01-edge-map/01-03-market-instrument-horizon-competition-capacity-map.md) | Where each edge can realistically exist and whether an independent operator can compete | Complete |
| [1.4 — Falsification and Evidence Design](01-edge-map/01-04-falsification-and-evidence-design.md) | Negative controls, robustness, trial accounting, prospective tests, execution stress, and kill criteria | Complete |
| [1.5 — Edge Map Synthesis and Replication Admissions](01-edge-map/01-05-edge-map-synthesis.md) | Ranked hypotheses, admissions, deferrals, rejections, dependencies, and Section 2 handoff | Complete |

Machine-readable admissions: [replication admission manifest](01-edge-map/01-05-replication-admission-manifest.yaml).

Admitted research identities:

- `EDGE-FUT-CARRY-001`
- `EDGE-FUT-TREND-001`
- `EDGE-CRYPTO-BASIS-001`
- `EDGE-FUT-POSITION-001`
- `EDGE-RISK-POLICY-001`
- `EDGE-CRYPTO-RV-001`

Admission authorizes research replication only. It does not authorize fitting, parameter tuning, paper trading, live trading, leverage, automatic promotion, or capital deployment.

### 2. Research Replication — Partially complete

| Report | Scope | Status |
|---|---|---|
| [2.1 — Anchor Papers, Opposing Evidence, Modern Updates, Data, and Replication-Code Selection](02-replication/02-01-anchor-opposition-code-selection.md) | Binding paper roles, exactness classes, official data routes, code-admission rules, table-level targets, and kill criteria | Complete |
| [2.2 — Data, Timing, and Information-Contract Reconstruction](02-replication/02-02-data-timing-information-contract-reconstruction.md) | Availability clocks, immutable raw artifacts, source licenses, point-in-time instruments, futures rolls, regulator releases, crypto contract versions, lineage, costs, and acquisition decisions | Complete |
| [2.3 — Current Controlling Status](02-replication/02-03-current-controlling-status.md) | Verified CFTC foundation, traditional-provider blockers, safe OKX/Binance public-source profiles, and remaining empirical gates | Partially complete |
| 2.4 — Sensitivity, Cost, Failure, and Disagreement Analysis | Conditional analysis after exact artifact, timing, instrument, price, and return gates pass | Blocked |
| 2.5 — Replication dossier and continue/stop decisions | Final Section 2 synthesis | Planned |

#### Current Report 2.3 state

The current verified foundation includes:

- official CFTC 2022 TFF Futures Only archive acquisition;
- exact 87-field parser and 2,719-row annual profile;
- deterministic 54-row pilot for `2022-09-13`;
- fail-closed 52-row scheduled-release ledger with zero claimed actual historical release times;
- versioned 54-row reporting-to-product registry with zero provider contract IDs and zero price-linkage-authorized rows;
- a bounded Cboe VX contract-engineering pilot whose raw retention and canonical historical timing remain blocked;
- a bounded OKX public funding metadata profile whose artifact contains no funding-rate values or reconstructable market series;
- a bounded Binance BTCUSDT January 2024 checksum/schema/timing pilot whose artifact contains hashes and profiles only, with no raw or derived market rows.

Current hard blockers include:

```text
Traditional-futures provider contract chains and point-in-time prices: INCOMPLETE
Databento owner accessibility: REJECTED
Cboe raw retention / canonical historical timing: BLOCKED
CME historical route: BLOCKED_LOGIN_ORDER_FEE_AND_LICENSE
ICE complete history: BLOCKED_PAID_ARCHIVE
OKX 2022 historical delivery and revocable retention: OPEN GATE
Binance persistent raw retention and historical available_at: OPEN GATES
Basis / funding PnL / returns: NOT AUTHORIZED
Paper-level numerical replication: NOT COMPLETE
Economic edge: NOT ESTABLISHED
Report 2.4: BLOCKED
```

All six hypothesis verdicts remain `INCONCLUSIVE`.

## Report 2.3 Evidence Index

### Core verification and historical snapshots

- [Current controlling status](02-replication/02-03-current-controlling-status.md)
- [Initial controlled execution snapshot](02-replication/02-03-controlled-empirical-and-code-replication.md)
- [Replication execution manifest](02-replication/02-03-replication-execution-manifest.yaml)
- [Independent reality verification and correction log](02-replication/02-03-independent-reality-verification-log.md)
- [Static analysis, test, and coverage verification](02-replication/02-03-static-analysis-and-test-verification.md)
- [Provider-gate historical addendum](02-replication/02-03-provider-gate-controlling-addendum.md)
- [Provider-probe historical addendum](02-replication/02-03-provider-probe-controlling-addendum.md)

### CFTC source, timing, and product identity

- [Verified CFTC acquisition and dated-pilot evidence](02-replication/02-03-cftc-tff-2022-acquisition-and-pilot-evidence.md)
- [Machine-readable CFTC acquisition evidence](02-replication/02-03-cftc-tff-2022-evidence.yaml)
- [Verified CFTC release-ledger evidence](02-replication/02-03-cftc-tff-2022-release-ledger-evidence.md)
- [Machine-readable release-ledger evidence](02-replication/02-03-cftc-tff-2022-release-ledger-evidence.yaml)
- [Verified CFTC instrument-registry evidence](02-replication/02-03-cftc-tff-2022-instrument-registry-evidence.md)
- [Machine-readable instrument-registry evidence](02-replication/02-03-cftc-tff-2022-instrument-registry-evidence.yaml)
- [Versioned official CFTC mapping-source registry](02-replication/02-03-cftc-tff-instrument-mapping-sources.json)
- `02-replication/02-03-cftc-tff-2022-instrument-map-contract.csv.gz.b64`
- `02-replication/02-03-cftc-tff-2022-instrument-registry.csv.gz.b64`

### Traditional-futures provider gates

- [Provider price-linkage candidate evidence](02-replication/02-03-provider-price-linkage-candidate-evidence.md)
- [Machine-readable provider-candidate evidence](02-replication/02-03-provider-price-linkage-candidate-evidence.yaml)
- [Databento zero-purchase probe evidence](02-replication/02-03-databento-zero-purchase-probe-evidence.md)
- [Machine-readable Databento probe evidence](02-replication/02-03-databento-zero-purchase-probe-evidence.yaml)
- [Owner-accessible exchange-native source pivot](02-replication/02-03-owner-accessible-exchange-native-source-pivot.md)
- [Machine-readable owner-accessible source pivot](02-replication/02-03-owner-accessible-exchange-native-source-pivot.yaml)
- [Verified Cboe VX public contract pilot](02-replication/02-03-cboe-vx-public-contract-pilot-evidence.md)
- [Machine-readable Cboe VX pilot evidence](02-replication/02-03-cboe-vx-public-contract-pilot-evidence.yaml)
- [CME public access and license gate](02-replication/02-03-cme-public-access-and-license-gate.md)
- [Machine-readable CME gate](02-replication/02-03-cme-public-access-and-license-gate.yaml)

### Crypto public-source gates

- [Official crypto source, license, and access selection](02-replication/02-03-crypto-official-source-license-and-access-selection.md)
- [Machine-readable crypto source selection](02-replication/02-03-crypto-official-source-license-and-access-selection.yaml)
- [Verified OKX public funding metadata pilot](02-replication/02-03-okx-public-funding-metadata-pilot-evidence.md)
- [Machine-readable OKX pilot evidence](02-replication/02-03-okx-public-funding-metadata-pilot-evidence.yaml)
- [Verified Binance BTCUSDT ephemeral pilot](02-replication/02-03-binance-btcusdt-public-ephemeral-pilot-evidence.md)
- [Machine-readable Binance pilot evidence](02-replication/02-03-binance-btcusdt-public-ephemeral-pilot-evidence.yaml)

### Key workflows

- `.github/workflows/cftc-tff-historical-2022-ingestion.yml`
- `.github/workflows/cftc-tff-2022-pilot-derivation.yml`
- `.github/workflows/cftc-tff-2022-release-ledger.yml`
- `.github/workflows/cftc-tff-2022-instrument-registry.yml`
- `.github/workflows/cboe-vx-public-contract-pilot.yml`
- `.github/workflows/okx-public-funding-metadata-pilot.yml`
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

| Report | Scope | Status |
|---|---|---|
| 4.1 | Non-negotiable simple baselines | Planned |
| 4.2 | Candidate strategy families | Planned |
| 4.3 | Robustness, ablation, and falsification tournament | Planned |
| 4.4 | Prospective, shadow, and paper evaluation | Planned |
| 4.5 | Champion, ensemble, or reject-all decision | Planned |

### 5. Live Trading System

| Report | Scope | Status |
|---|---|---|
| 5.1 | Runtime architecture and state machines | Planned |
| 5.2 | Market connectivity, order management, and execution | Planned |
| 5.3 | Risk engine, reconciliation, and persistence | Planned |
| 5.4 | Monitoring, incident handling, and dry-run operations | Planned |
| 5.5 | Controlled deployment with minimal real capital | Planned |

## Bottom-Up Synthesis Rule

Each leaf report must contain:

1. Problem definition.
2. Evidence supporting and challenging the proposition.
3. Relevant production code and engineering practice.
4. Data and timing requirements.
5. Acceptance and rejection criteria.
6. Known limitations and unresolved questions.
7. An explicit implementation consequence.

Five leaf reports form one section-level synthesis. The five section syntheses form the final trading-system research and implementation blueprint.

## Governance Rules

- Every hypothesis, feature family, label, threshold, parameter range, asset, venue, horizon, and metric choice counts toward the research trial ledger.
- Negative results and access blockers are retained permanently.
- Historical evidence can qualify a candidate for prospective testing but cannot prove a live edge.
- Data availability time, executable prices, realistic costs, failure modes, capacity, owner accessibility, and license terms are part of the hypothesis.
- A single timestamp is prohibited; `available_at` governs usability.
- Continuous futures may support diagnostics but cannot create executable PnL.
- Public visibility is not permission to retain, redistribute, mine, combine, or derive returns.
- Safe evidence may retain hashes and non-market metadata while raw and derived market rows remain absent.
- Source-page verification is not raw-artifact acquisition.
- API reachability is not immutable ingestion.
- Actions staging is not long-term immutable storage.
- A scheduled release time is not a verified actual historical release time.
- A reporting code is not automatically a tradable instrument.
- A product root is not a provider contract-chain identity.
- Current product metadata may not be projected backward into historical observations.
- Provider credentials belong only in approved secret storage and must never be committed or pasted into chat.
- False identity, borrowed payment instruments, third-party accounts, credential sharing, and payment or jurisdiction circumvention are prohibited.
- A green engineering workflow may establish a blocker or safe metadata profile rather than an empirical pass.
- A derived-data pass is not an artifact-audit pass.
- An artifact-audit pass is not a paper-replication pass.
- A paper-replication pass is not an economic-edge pass.
- Blocked or licensed data remain blocked or pending; convenient substitutes cannot inherit exact verdicts.
- No admitted hypothesis is proven until it survives genuinely new forward data and realistic execution.
- The final outcome may legitimately be to reject every candidate.

## Branch

These reports are developed on `agent/edge-research-reports` under Draft PR #41 until the research package is mature enough for review and integration.
