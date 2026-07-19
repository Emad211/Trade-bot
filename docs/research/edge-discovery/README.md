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
| [2.3 — Current Controlling Status](02-replication/02-03-current-controlling-status.md) | Official CFTC acquisition, parser, dated pilot, release ledger, versioned product registry, and remaining empirical gates | Partially complete |
| [2.3 — Provider-Gate Controlling Addendum](02-replication/02-03-provider-gate-controlling-addendum.md) | Provider requirements and fail-closed price authorization | Historical snapshot; superseded where conflicting |
| [2.3 — Provider-Probe Controlling Addendum](02-replication/02-03-provider-probe-controlling-addendum.md) | Permanent Databento zero-purchase probe and verified missing-secret blocker | Historical verified blocker; provider subsequently rejected for owner accessibility |
| [2.3 — Owner-Accessible Exchange-Native Source Pivot](02-replication/02-03-owner-accessible-exchange-native-source-pivot.md) | Owner-accessibility gate, Databento operational rejection, Cboe/CME/ICE public-source decisions, and VX pilot handoff | Current controlling provider-source decision |
| 2.4 — Sensitivity, Cost, Failure, and Disagreement Analysis | Conditional sensitivity analysis on numerically reconstructed evidence | Blocked until Report 2.3 artifact and price-linkage gates pass |
| 2.5 | Replication dossier and continue/stop decisions | Planned |

Report 2.1 selects what must be replicated. Report 2.2 freezes what each datum means and when it becomes usable. Report 2.3 contains a real official CFTC raw artifact, an exact parser, a deterministic dated pilot, a fail-closed scheduled-release ledger, and a 54-row reporting-to-product registry. Databento was technically evaluated but is now operationally rejected because the required account, payment, or banking path is not practically accessible to the project owner. The program has pivoted to owner-accessible exchange-native sources and has authorized a bounded public Cboe VX acquisition-and-validation pilot. It does not claim verified historical actual release times, accepted cross-market price providers, provider contract-chain identities, returns, a paper-level numerical replication, or an economic edge.

Report 2.2 machine-readable contracts:

- [Data-contract manifest](02-replication/02-02-data-contract-manifest.yaml)
- [Source and license registry](02-replication/02-02-source-license-registry.yaml)
- [Instrument and point-in-time universe manifest](02-replication/02-02-instrument-universe-manifest.yaml)
- [Lineage and timing schema](02-replication/02-02-lineage-timing-schema.yaml)

Report 2.3 evidence and implementation:

- [Current controlling status](02-replication/02-03-current-controlling-status.md)
- [Owner-accessible exchange-native source pivot](02-replication/02-03-owner-accessible-exchange-native-source-pivot.md)
- [Machine-readable owner-accessible source pivot](02-replication/02-03-owner-accessible-exchange-native-source-pivot.yaml)
- [Provider-gate controlling addendum](02-replication/02-03-provider-gate-controlling-addendum.md)
- [Provider-probe controlling addendum](02-replication/02-03-provider-probe-controlling-addendum.md)
- [Initial controlled execution snapshot](02-replication/02-03-controlled-empirical-and-code-replication.md)
- [Replication execution manifest](02-replication/02-03-replication-execution-manifest.yaml)
- [Independent reality verification and correction log](02-replication/02-03-independent-reality-verification-log.md)
- [Static analysis, test, and coverage verification](02-replication/02-03-static-analysis-and-test-verification.md)
- [Verified CFTC TFF acquisition and pilot evidence](02-replication/02-03-cftc-tff-2022-acquisition-and-pilot-evidence.md)
- [Machine-readable CFTC acquisition evidence](02-replication/02-03-cftc-tff-2022-evidence.yaml)
- [Verified CFTC release-ledger evidence](02-replication/02-03-cftc-tff-2022-release-ledger-evidence.md)
- [Machine-readable CFTC release-ledger evidence](02-replication/02-03-cftc-tff-2022-release-ledger-evidence.yaml)
- [Verified CFTC instrument-registry evidence](02-replication/02-03-cftc-tff-2022-instrument-registry-evidence.md)
- [Machine-readable CFTC instrument-registry evidence](02-replication/02-03-cftc-tff-2022-instrument-registry-evidence.yaml)
- [Provider-candidate and point-in-time price-linkage evidence](02-replication/02-03-provider-price-linkage-candidate-evidence.md)
- [Machine-readable provider-candidate evidence](02-replication/02-03-provider-price-linkage-candidate-evidence.yaml)
- [Databento zero-purchase probe evidence](02-replication/02-03-databento-zero-purchase-probe-evidence.md)
- [Machine-readable Databento probe evidence](02-replication/02-03-databento-zero-purchase-probe-evidence.yaml)
- [Versioned official CFTC mapping-source registry](02-replication/02-03-cftc-tff-instrument-mapping-sources.json)
- `02-replication/02-03-cftc-tff-2022-instrument-map-contract.csv.gz.b64`
- `02-replication/02-03-cftc-tff-2022-instrument-registry.csv.gz.b64`
- `02-replication/02-03-provider-candidate-plan.csv.gz.b64`
- `.github/workflows/cftc-tff-historical-2022-ingestion.yml`
- `.github/workflows/cftc-tff-2022-pilot-derivation.yml`
- `.github/workflows/cftc-tff-2022-release-ledger.yml`
- `.github/workflows/cftc-tff-2022-instrument-registry.yml`
- `.github/workflows/cftc-tff-2022-provider-candidate-plan.yml`
- `.github/workflows/databento-zero-purchase-metadata-probe.yml`
- `src/hybrid_trader/replication/`
- `tests/test_replication_*.py`
- `tests/test_cftc_*.py`
- `tests/test_provider_price_linkage.py`
- `tests/test_databento_metadata_probe.py`

Report 2.3 currently records:

- the original committed implementation was independently reconstructed from authenticated GitHub commit content;
- an over-permissive factor-audit verdict was found and corrected;
- the hardened local replication suite passed Ruff, strict mypy, 15 tests, 85.44% statement coverage, and compilation;
- dedicated hosted CFTC acquisition, pilot, release-ledger, instrument-registry, provider-candidate, and Databento gate-evaluation workflows passed in their explicitly defined scopes;
- the official CFTC 2022 TFF Futures Only ZIP was acquired with raw SHA-256 `94c9c1f...88601`;
- its only member, `FinFutYY.txt`, passed CRC and has SHA-256 `7c309cb7...8bb3b`;
- the exact source schema has 87 fields and fingerprint `fe012305...45d42`;
- the full-year profile contains 2,719 unique report-date/contract rows across 52 dates;
- 56 consolidated rows have recorded one-unit reconciliation differences, with no material accounting failure;
- the `2022-09-13` pilot contains 54 unique market codes and zero reconciliation difference;
- the canonical pilot CSV has SHA-256 `1be0028b...d268b`;
- the scheduled-release ledger contains 52 rows and has SHA-256 `4196c144...ccb40`;
- all 52 historical actual-release fields remain unverified and null;
- the versioned instrument registry contains 54 unique reporting-code rows, is 38,903 bytes, and has SHA-256 `70a8e89d...25c74`;
- 47 rows have historical screen-tradable product roots, three are non-tradable consolidated aggregates, two are historical later-delisted products, one is a nonstandard execution product, and one still requires a technical provider symbol;
- the Databento candidate and zero-purchase client were implemented and tested, but authenticated provider access was unavailable;
- Databento is classified `OPERATIONALLY_REJECTED_OWNER_ACCESS_CONSTRAINT` and Issue #42 is closed as not planned;
- fabricated identity, borrowed cards, third-party accounts, credential sharing, and payment or jurisdiction circumvention are prohibited;
- Cboe public contract-level VX history is the next executable acquisition candidate under Issue #43;
- CME public delayed pages may support current reference checks, but owner-accessible 2022 historical flat-file retrieval remains unverified;
- ICE public reports may support isolated verification, while complete historical End-of-Day packages remain blocked where purchase or subscription is required;
- all provider contract identifiers remain empty and zero rows authorize price linkage or returns;
- all Actions staging remains retention-limited and is not long-term immutable ingestion;
- the CFTC PRE API identity is verified, but row-level cross-check remains pending because repeated GitHub-runner calls returned HTTP 503;
- AQR workbooks, Moreira–Muir factor artifacts, licensed traditional-futures histories, Chi et al. source data, and Binance/OKX pilot artifacts remain unavailable or un-ingested;
- no paper-level numerical replication is complete;
- all six empirical edge verdicts remain `INCONCLUSIVE`.

Public Cboe VX acquisition, parser design, terms capture, checksum/lineage work, and same-contract formula validation are authorized. CME public-access probing and isolated ICE public-report probing are authorized. Provider purchase, unavailable payment workarounds, price assignment, empirical return computation, fitting, parameter tuning, strategy tournaments, paper trading, live trading, leverage, and capital deployment remain unauthorized.

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
- Data availability time, executable prices, realistic costs, failure modes, capacity, and owner accessibility are part of the hypothesis itself.
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
- A scheduled release time is not a verified actual historical release time.
- A CFTC reporting code is not automatically a tradable instrument.
- A product root is not a provider contract-chain identity.
- A technically suitable provider that is inaccessible to the owner is not an actionable provider.
- False identity, borrowed payment instruments, third-party accounts, credential sharing, and payment or jurisdiction circumvention are prohibited.
- A provider candidate is not an accepted provider.
- A parent symbol is only a lookup key until point-in-time child resolution is verified.
- A cost endpoint is not purchase authorization.
- OHLCV is not a substitute for official settlement.
- A green gate-evaluation workflow may represent a verified blocker rather than an authenticated provider pass.
- Provider credentials must never be committed, reported, or pasted into chat; they belong only in approved secret storage.
- Missing credentials do not prove provider rejection or provider acceptance.
- Consolidated reporting aggregates must never receive a direct price series.
- Current product metadata may not be projected backward into historical observations.
- A derived-data pass is not an artifact-audit pass.
- An artifact-audit pass is not a paper-replication pass.
- A paper-replication pass is not an economic-edge pass.
- Blocked or licensed data must remain blocked or pending; a convenient substitute cannot inherit an exact verdict.
- An admitted hypothesis remains unproven until it survives genuinely new forward data and realistic execution.
- The final outcome may legitimately be to reject every candidate.

## Branch

These reports are developed on `agent/edge-research-reports` until the research package is mature enough for review and integration.
