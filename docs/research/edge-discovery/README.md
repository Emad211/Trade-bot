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
| 2.3 — Exact Empirical and Code Replication | Controlled acquisition, public-factor audits, direct opposing tests, table reconstruction, and exact-versus-constructive verdicts | Next |
| 2.4 | Sensitivity, cost, failure, and disagreement analysis | Planned |
| 2.5 | Replication dossier and continue/stop decisions | Planned |

Report 2.1 selects what must be replicated. Report 2.2 freezes what each datum means and when it becomes usable.

Report 2.2 machine-readable contracts:

- [Data-contract manifest](02-replication/02-02-data-contract-manifest.yaml)
- [Source and license registry](02-replication/02-02-source-license-registry.yaml)
- [Instrument and point-in-time universe manifest](02-replication/02-02-instrument-universe-manifest.yaml)
- [Lineage and timing schema](02-replication/02-02-lineage-timing-schema.yaml)

The first permitted Report 2.3 sequence is:

1. AQR TSMOM original-versus-maintained factor audit;
2. Moreira–Muir public factor and formula audit;
3. CFTC report-release, category, and revision parser validation;
4. Binance/OKX archive completeness and effective-dated rule audit;
5. traditional-futures licensed-data procurement decision.

Exact traditional-futures replication remains pending licensed expired-contract histories. Chi et al. remains exact-inconclusive until the original licensed data are obtained. Public Binance/OKX work is a separately identified constructive experiment. Empirical fitting, paper trading, live trading, leverage, and capital deployment remain unauthorized.

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
- An admitted hypothesis remains unproven until it survives genuinely new forward data and realistic execution.
- The final outcome may legitimately be to reject every candidate.

## Branch

These reports are developed on `agent/edge-research-reports` until the research package is mature enough for review and integration.
