# Edge Discovery Research Program

This directory is the durable research memory for the trading-system project. It is intentionally independent of the repository's previous market, asset, model, and timeframe choices. No earlier design decision is treated as a constraint unless it is re-established by evidence in this program.

## Objective

Build a defensible path from economic hypotheses to a live trading system without confusing prediction accuracy, backtest profitability, hidden risk premia, or execution assumptions with a genuine exploitable edge.

## Research Tree

### 1. Edge Map — Complete

| Report | Scope | Status |
|---|---|---|
| [1.1 — Edge Definition and Proof Standard](01-edge-map/01-01-edge-definition-and-proof-standard.md) | Formal definition of edge, evidence hierarchy, hard rejection gates, and required hypothesis contract | Complete |
| [1.2 — Taxonomy of Edge Mechanisms](01-edge-map/01-02-taxonomy-of-edge-mechanisms.md) | Risk premia, behavioral mispricing, information, relative value, liquidity provision, execution, and risk-policy edge | Complete |
| [1.3 — Market, Instrument, Horizon, Competition, and Capacity Map](01-edge-map/01-03-market-instrument-horizon-competition-capacity-map.md) | Where each edge can realistically exist and whether an independent operator can compete | Complete |
| [1.4 — Falsification and Evidence Design](01-edge-map/01-04-falsification-and-evidence-design.md) | Negative controls, robustness, trial accounting, prospective tests, execution stress, and kill criteria | Complete |
| [1.5 — Edge Map Synthesis and Replication Admissions](01-edge-map/01-05-edge-map-synthesis.md) | Ranked hypotheses, admissions, deferrals, rejections, dependencies, and Section 2 handoff | Complete |

The machine-readable admissions and dependencies are stored in [the replication admission manifest](01-edge-map/01-05-replication-admission-manifest.yaml).

Section 1 admits the following hypothesis identities for formal, dependent, or conditional replication:

- `EDGE-FUT-CARRY-001`
- `EDGE-FUT-TREND-001`
- `EDGE-CRYPTO-BASIS-001`
- `EDGE-FUT-POSITION-001`
- `EDGE-RISK-POLICY-001`
- `EDGE-CRYPTO-RV-001`

Admission authorizes research replication only. It does not authorize paper trading, live trading, leverage, automatic promotion, or capital deployment.

### 2. Research Replication

| Report | Scope | Status |
|---|---|---|
| [2.1 — Anchor Papers, Opposing Evidence, Modern Updates, Data, and Replication-Code Selection](02-replication/02-01-anchor-opposition-code-selection.md) | Binding paper roles, exactness classes, official data routes, code-admission rules, table-level targets, and kill criteria | Complete |
| [2.2 — Data, Timing, and Information-Contract Reconstruction](02-replication/02-02-data-timing-information-contract-reconstruction.md) | Availability clocks, immutable raw artifacts, source licenses, point-in-time instruments, futures rolls, regulator releases, crypto contract versions, lineage, costs, and acquisition decisions | Complete |
| [2.3 — Current Controlling Status](02-replication/02-03-current-controlling-status.md) | Independently reverified implementation, first official CFTC raw acquisition, exact parser contract, dated pilot, remaining empirical gates | Partially complete — first official artifact and pilot verified; remaining gates open |
| 2.4 — Sensitivity, Cost, Failure, and Disagreement Analysis | Conditional sensitivity analysis on numerically reconstructed evidence | Blocked until Report 2.3 artifact gates pass |
| 2.5 | Replication dossier and continue/stop decisions | Planned |

Report 2.1 selects what must be replicated. Report 2.2 freezes what each datum means and when it becomes usable. Report 2.3 now contains one real official CFTC raw artifact and a deterministic dated pilot, but it does not claim a paper-level numerical replication or an economic edge.

Report 2.2 machine-readable contracts:

- [Data-contract manifest](02-replication/02-02-data-contract-manifest.yaml)
- [Source and license registry](02-replication/02-02-source-license-registry.yaml)
- [Instrument and point-in-time universe manifest](02-replication/02-02-instrument-universe-manifest.yaml)
- [Lineage and timing schema](02-replication/02-02-lineage-timing-schema.yaml)

Report 2.3 evidence and implementation:

- [Current controlling status](02-replication/02-03-current-controlling-status.md)
- [Initial controlled execution snapshot](02-replication/02-03-controlled-empirical-and-code-replication.md)
- [Replication execution manifest](02-replication/02-03-replication-execution-manifest.yaml)
- [Independent reality verification and correction log](02-replication/02-03-independent-reality-verification-log.md)
- [Static analysis, test, and coverage verification](02-replication/02-03-static-analysis-and-test-verification.md)
- [Verified CFTC TFF acquisition and pilot evidence](02-replication/02-03-cftc-tff-2022-acquisition-and-pilot-evidence.md)
- [Machine-readable CFTC TFF evidence](02-replication/02-03-cftc-tff-2022-evidence.yaml)
- `.github/workflows/replication-integrity.yml`
- `.github/workflows/cftc-tff-historical-2022-ingestion.yml`
- `.github/workflows/cftc-tff-2022-pilot-derivation.yml`
- `src/hybrid_trader/replication/`
- `tests/test_replication_*.py`

Report 2.3 currently records:

- the original committed implementation was independently reconstructed from authenticated GitHub commit content;
- an over-permissive factor-audit verdict was found and corrected;
- the hardened local replication suite passed Ruff, strict mypy, 15 tests, 85.44% statement coverage, and compilation;
- the dedicated CFTC annual-ZIP workflow passed in GitHub Actions;
- the dedicated CFTC end-to-end acquisition/parser/pilot workflow passed in GitHub Actions;
- the official CFTC 2022 TFF Futures Only ZIP was acquired with raw SHA-256 `94c9c1f...88601`;
- its only member, `FinFutYY.txt`, passed CRC and has SHA-256 `7c309cb7...8bb3b`;
- the exact source schema has 87 fields and fingerprint `fe012305...45d42`;
- the full-year profile contains 2,719 unique report-date/contract rows across 52 dates;
- 56 consolidated rows have recorded unit reconciliation differences, with no material accounting failure;
- the `2022-09-13` pilot contains 54 unique market codes and zero reconciliation difference;
- the canonical pilot CSV has SHA-256 `1be0028b...d268b`;
- raw and derived bundles are staged in GitHub Actions artifacts until 2026-10-16;
- Actions staging is retention-limited and is not long-term immutable ingestion;
- the CFTC PRE API identity is verified, but row-level cross-check is pending because repeated GitHub-runner calls returned HTTP 503;
- AQR workbooks, Moreira–Muir factor artifacts, licensed traditional-futures histories, Chi et al. source data, and Binance/OKX pilot artifacts remain unavailable or un-ingested;
- no paper-level numerical replication is complete;
- all six empirical edge verdicts remain `INCONCLUSIVE`.

Empirical fitting, parameter tuning, a strategy tournament, paper trading, live trading, leverage, and capital deployment remain unauthorized.

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
3. Review of relevant production code and engineering practice.
4. Data and timing requirements.
5. Acceptance and rejection criteria.
6. Known limitations and unresolved questions.
7. An explicit implementation consequence.

Five leaf reports form one section-level synthesis. The five section syntheses form the final trading-system research and implementation blueprint.

## Governance Rules

- Every hypothesis, feature family, label, threshold, parameter range, asset, venue, horizon, and metric choice counts toward the research trial ledger.
- Negative results are retained permanently.
- Historical evidence can qualify a candidate for prospective testing but cannot prove a live edge.
- No strategy is promoted because it uses a complex model, a famous paper, or a high backtest Sharpe ratio.
- Data availability time, executable prices, realistic costs, failure modes, and capacity are part of the hypothesis itself.
- Primitive effects must be reported separately before signal integration.
- Exact, near-exact, constructive, and theoretical reproductions are separate experiment identities.
- No hypothesis may skip its strongest selected opposing evidence.
- A single timestamp field is prohibited; `available_at` governs usability.
- Continuous futures may support signal diagnostics but cannot create executable PnL.
- Public data under provider terms are not assumed redistributable.
- Implementation tests are not empirical paper replications.
- Source-page verification is not raw-artifact acquisition.
- API reachability is not immutable ingestion.
- Raw acquisition is not immutable ingestion until checksum, retrieval, license, and storage evidence exist.
- Actions staging is not long-term immutable storage.
- A derived-data pass is not an artifact-audit pass.
- An artifact-audit pass is not a paper-replication pass.
- A paper-replication pass is not an economic-edge pass.
- Blocked or licensed data must remain blocked or pending; a convenient substitute cannot inherit an exact verdict.
- An admitted hypothesis remains unproven until it survives genuinely new forward data and realistic execution.
- The final outcome may legitimately be to reject every candidate.

## Branch

These reports are developed on `agent/edge-research-reports` until the research package is mature enough for review and integration.
