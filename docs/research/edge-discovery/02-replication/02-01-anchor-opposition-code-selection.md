# Report 2.1 — Anchor Papers, Opposing Evidence, Modern Updates, Data, and Replication-Code Selection

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Report:** 1 of 5  
**Version:** 1.0  
**Research freeze date:** 2026-07-18  
**Status:** Complete  
**Parents:** [Report 1.1](../01-edge-map/01-01-edge-definition-and-proof-standard.md), [Report 1.2](../01-edge-map/01-02-taxonomy-of-edge-mechanisms.md), [Report 1.3](../01-edge-map/01-03-market-instrument-horizon-competition-capacity-map.md), [Report 1.4](../01-edge-map/01-04-falsification-and-evidence-design.md), and [Report 1.5](../01-edge-map/01-05-edge-map-synthesis.md)  
**Machine-readable companion:** [02-01-replication-selection-manifest.yaml](02-01-replication-selection-manifest.yaml)  
**Decision type:** Binding selection of literature, data, code, and exact empirical targets for Reports 2.2–2.5

---

# Executive decision

Report 2.1 converts the six admitted economic hypotheses from Section 1 into a finite, auditable replication queue. It does **not** select whichever paper reports the highest Sharpe ratio. It selects evidence sets that maximize decision value under four constraints:

1. the economic claim must be identifiable;
2. the strongest credible challenge must be tested beside the supporting claim;
3. the data and timing contract must be reconstructable or explicitly classified as licensed;
4. the replicated output must change a continue, redesign, defer, or stop decision.

The project will use five evidence roles:

- `ANCHOR_MECHANISM`: the paper that most clearly defines the economic claim;
- `ANCHOR_EMPIRICAL`: the paper whose empirical design becomes the primary reproduction target;
- `OPPOSING_EVIDENCE`: the strongest paper capable of falsifying or materially reinterpreting the claim;
- `MODERN_UPDATE`: a later study that tests changed markets, post-publication periods, new methods, or new frictions;
- `IMPLEMENTATION_REFERENCE`: code or engineering work used to reproduce mechanics, never treated as proof of profitability.

The selected replication order is:

| Queue | Hypothesis | First decisive question | Primary replication class |
|---:|---|---|---|
| 1 | `EDGE-FUT-TREND-001` | Is strategy profitability evidence of own-return predictability, or mostly a volatility-scaled historical-mean/allocation effect? | Public factor audit + licensed raw reconstruction |
| 2 | `EDGE-RISK-POLICY-001` | Does a frozen volatility/no-trade overlay add out-of-sample utility after matched risk and costs? | Public-data exact/near-exact |
| 3 | `EDGE-FUT-CARRY-001` | Do implementable same-contract curve and carry returns survive roll, factor, and cost corrections? | Licensed exact + public constructive checks |
| 4 | `EDGE-FUT-POSITION-001` | Does public positioning add information beyond carry, trend, and market risk after the real publication delay? | Public CFTC + licensed prices |
| 5 | `EDGE-CRYPTO-BASIS-001` | Does derivatives state generalize beyond one licensed OKX sample and one bullish regime? | Licensed anchor + public multi-venue reconstruction |
| 6 | `EDGE-CRYPTO-RV-001` | Does two-leg carry remain positive after funding, financing, margin, orphan fills, venue risk, and capital lock-up? | Public exact/constructive + prospective paper execution |

No paper, repository, dataset, or result selected here authorizes paper trading, live trading, leverage, or capital deployment.

---

# 1. Research method and source coverage

## 1.1 Searches performed

The selection was built from:

- the literature and decisions already frozen in Reports 1.1–1.5;
- targeted semantic searches across peer-reviewed literature through Scholar Gateway;
- publisher pages and official institutional repositories;
- official author data pages;
- official regulator and exchange data documentation;
- public code repositories, inspected only as replication or engineering references;
- explicit searches for contradictory and null evidence rather than only supportive papers.

Scholar Gateway searches covered literature available in its corpus through May 2026. The searches separately addressed:

1. diversified futures trend and time-series momentum;
2. carry, basis, curve, hedging pressure, and speculative positioning;
3. volatility management, abstention, and no-trade policies;
4. cryptocurrency derivatives factors and two-leg relative value;
5. equity and option alternatives, to confirm the Section 1 deferral decision.

Consensus search was attempted but unavailable because the monthly search quota was exhausted. This is recorded as a source-coverage limitation, not silently replaced by an unsupported claim of comprehensive database coverage.

## 1.2 Source hierarchy

The hierarchy for this report is:

1. published peer-reviewed article and its official supplement;
2. accepted manuscript from an institutional repository;
3. official working-paper version from NBER, BIS, CEPR, or an author page;
4. official regulator or exchange data source;
5. author-supplied code and data;
6. independent replication code with transparent tests;
7. production engineering frameworks;
8. unverified notebooks, tutorials, and strategy demonstrations.

Items in levels 6–8 cannot establish the empirical truth of an anchor paper.

## 1.3 Why one paper is insufficient

A single paper often combines several claims that must be separated:

- a predictor exists;
- a portfolio earns returns;
- those returns are not a passive risk premium;
- the result is robust to data construction;
- the result is executable after costs;
- the result persists after publication;
- the result can be operated by this project.

Report 2.1 therefore selects **evidence sets**, not celebrity papers.

---

# 2. Replication classifications

Every selected item receives one of the following classifications.

## 2.1 `EXACT_PUBLIC`

The paper's exact or materially complete data and method can be obtained from public sources, and the principal published tables can be reconstructed without substituting the market, instrument, sampling rule, or return contract.

## 2.2 `EXACT_LICENSED`

The published design is reproducible only with licensed or author-permission data. The project may specify and implement the full pipeline, but it must not call a public substitute an exact replication.

## 2.3 `NEAR_EXACT_PUBLIC`

The paper supplies factor returns, processed data, or sufficient public inputs to reproduce the main statistical claim, but not every raw-data transformation.

## 2.4 `CONSTRUCTIVE_PUBLIC`

The economic hypothesis can be reconstructed using public data under a predeclared modern contract, but the output is a new replication experiment rather than an exact reproduction of the paper.

## 2.5 `THEORETICAL_REPRODUCTION`

The target is a mathematical derivation, simulation, or no-arbitrage identity rather than an empirical table.

## 2.6 `NOT_CURRENTLY_REPRODUCIBLE`

The required data or code cannot currently be obtained with sufficient fidelity. Such an item may remain contextual evidence but cannot be the sole basis of a promotion decision.

---

# 3. Selection rubric

Each paper or artifact was scored qualitatively on:

| Dimension | Question |
|---|---|
| Economic identification | Does it identify the payer, service, risk, or behavioral mechanism? |
| Empirical centrality | Does it directly test the admitted hypothesis? |
| Methodological contrast | Does it expose a failure mode missed by the anchor? |
| Timing validity | Are observation, publication, decision, and execution times recoverable? |
| Return validity | Are returns based on executable positions rather than synthetic price jumps? |
| Cost validity | Are spread, fees, financing, turnover, and market impact treated credibly? |
| Reproducibility | Are data, code, formulas, and tables available? |
| Modern relevance | Does it cover later markets, changed contract rules, or post-publication periods? |
| Decision value | Would success or failure change the research program? |

A paper may be scientifically important but receive a lower replication priority because its data are unavailable. A public-data paper may be easy to reproduce but remain secondary because it tests a weaker economic question.

---

# 4. Master evidence-selection matrix

| Hypothesis | Anchor mechanism | Anchor empirical | Strongest opposition | Modern update | Public-data route | Exactness |
|---|---|---|---|---|---|---|
| `EDGE-FUT-TREND-001` | Moskowitz, Ooi & Pedersen (2012) | MOP tables plus AQR updated factor series | Huang et al. (2020); Shang et al. (2022) for roll/spread claims | Uhl (2025); Zheng et al. (2025) | AQR factor data; independent raw-futures reconstruction | `NEAR_EXACT_PUBLIC` + `EXACT_LICENSED` |
| `EDGE-RISK-POLICY-001` | Moreira & Muir (2017) | Published factor data and vol-managed factors | Kang & Kwon (2021); OOS/cost critique | DeMiguel, Martín-Utrera & Uppal (2024) | Author factor data + public factor libraries | `NEAR_EXACT_PUBLIC` |
| `EDGE-FUT-CARRY-001` | Szymanowska et al. (2014); Boons & Prado (2019) | Same-contract spot/term-premium and basis-momentum tables | Shang et al. (2022); Yiyi et al. (2025) | Qian et al. (2025); Nakagawa & Sakemoto (2025) | Public specifications; licensed settlement curves | `EXACT_LICENSED` |
| `EDGE-FUT-POSITION-001` | Fan et al. (2020) | Speculative-pressure sorts and spanning tests | null/mixed hedging-pressure evidence; factor-beta reinterpretation | Maréchal (2023); Uhl (2025) | CFTC COT public data + licensed prices | `CONSTRUCTIVE_PUBLIC` / `EXACT_LICENSED` |
| `EDGE-CRYPTO-BASIS-001` | Chi et al. (2023) | daily cross-sectional basis portfolios | factor overlap, short sample, licensed single venue | Crypto Carry (2026); Shynkevich (2026); Ackerer et al. (2025) | OKX/Binance public historical data | `EXACT_LICENSED` + `CONSTRUCTIVE_PUBLIC` |
| `EDGE-CRYPTO-RV-001` | De Blasis & Webb (2022) | Binance quarterly/perpetual contract-design and carry tests | limited arbitrage outside dislocations; capital and venue constraints | Crypto Carry (2026); Ackerer et al. (2025) | Binance Vision; OKX historical data; prospective ledger | `EXACT_PUBLIC` / `CONSTRUCTIVE_PUBLIC` |

---

# 5. `EDGE-FUT-TREND-001` — diversified medium-frequency futures trend

## 5.1 Selected anchor mechanism

### Moskowitz, Ooi, and Pedersen — *Time Series Momentum*

- Journal: *Journal of Financial Economics* (2012)
- DOI: `10.1016/j.jfineco.2011.11.003`
- Role: `ANCHOR_MECHANISM` and `ANCHOR_EMPIRICAL`
- Official updated factor data: AQR Data Sets, “Time Series Momentum: Factors, Monthly”
- Replication class:
  - published factor-series audit: `NEAR_EXACT_PUBLIC`;
  - raw 58-instrument reconstruction: `EXACT_LICENSED` unless the exact vendor histories are acquired.

### Why selected

This paper defines the canonical hypothesis: an instrument's own past return predicts its future return, and a diversified long/short portfolio monetizes the effect. It is the correct anchor because later trend studies either extend, reinterpret, or challenge this exact claim.

### What must be replicated

1. asset-by-asset predictive regressions;
2. pooled predictive regression with and without fixed effects;
3. 12-month lookback / one-month holding strategy;
4. long and short legs separately;
5. asset-class contributions;
6. volatility scaling contribution;
7. return continuation and longer-horizon reversal;
8. performance against passive and historical-mean benchmarks;
9. crisis and non-crisis decomposition;
10. updated post-publication factor performance using AQR's maintained series.

## 5.2 Strongest opposing evidence

### Huang, Li, Wang, and Zhou — *Time Series Momentum: Is It There?*

- Journal: *Journal of Financial Economics* (2020)
- DOI: `10.1016/j.jfineco.2019.08.004`
- Role: `OPPOSING_EVIDENCE`
- Replication class: `NEAR_EXACT_PUBLIC` if the authors' processed sample is obtained; otherwise `EXACT_LICENSED` for the raw cross-section.

### Why selected

This is the most direct methodological challenge to the anchor. It argues that:

- asset-by-asset evidence is weak;
- pooled t-statistics can over-reject because of heterogeneous means, persistent predictors, and volatility scaling;
- bootstrap critical values are much larger than conventional thresholds;
- the profitable strategy may perform similarly to a historical-sample-mean strategy that requires no own-return predictability.

A trend replication that omits this benchmark cannot distinguish predictive alpha from a dynamic allocation rule.

### Binding opposing tests

1. wild-bootstrap and pairs-bootstrap critical values;
2. fixed-effects pooled regression;
3. asset-by-asset in-sample and out-of-sample predictability;
4. MOP strategy versus time-series historical-mean strategy;
5. results with and without volatility scaling;
6. results by asset class and by liquidity tier.

## 5.3 Contract-construction challenge

### Shang, Serra, and Garcia — *Ride the Trend: Is There Spread Momentum Profit in the US Commodity Markets?*

- Journal: *Journal of Agricultural Economics* (2022)
- DOI: `10.1111/1477-9552.12485`
- Role: `OPPOSING_EVIDENCE` for calendar-spread and roll-based extensions
- Replication class: `EXACT_LICENSED`

### Why selected

This paper is not a universal rejection of outright trend. It is selected because it exposes two high-impact errors:

- unrealizable roll yield embedded in continuous series;
- confounding between momentum and volatility-based asset allocation.

It becomes a required negative-control design for every futures replication.

## 5.4 Modern update

### Uhl — *Speculators and Time Series Momentum in Commodity Futures Markets*

- Journal: *Review of Financial Economics* (2025)
- DOI: `10.1002/rfe.1228`
- Role: `MODERN_UPDATE`
- Replication class: `EXACT_LICENSED`

### Why selected

The paper tests crowding rather than merely re-estimating a historical Sharpe ratio. It reports that greater alignment between speculative positions and generic TSMOM is associated with lower subsequent trend performance, though the relationship may not itself form a strong timing strategy. This is directly relevant to decay and capacity.

### Secondary modern update

Zheng, Zhang, Lien, and Yu (2025), *Evaluating Trend-Based Strategies in Chinese Commodity Futures Markets*, DOI `10.1002/fut.70033`, is retained as a cross-market update. It is not the first replication target because market access, contract rules, and data provenance differ materially from the initial listed-futures universe.

## 5.5 Code selection

### Accepted

1. **AQR maintained TSMOM factor data** — accepted as a public factor-series audit source, not raw-market replication code.
2. **Project-owned reference implementation** — required for canonical signal, same-contract returns, volatility scaling, and bootstrap tests.
3. **`joelowj/mtl-tsmom`** — accepted only as an independent model-challenger implementation for later strategy tournaments. It is not author code for MOP and does not validate the continuous-futures data.
4. **`bkelly-lab/ReplicationCrisis`** — accepted as a research-engineering reference for transparent factor replication and reporting conventions, not as TSMOM evidence.

### Rejected as primary replication code

- anonymous gists;
- QuantConnect demonstration algorithms;
- notebooks that use back-adjusted continuous prices without contract-level PnL;
- repositories that optimize Sharpe before reproducing the simple anchor;
- deep-learning trend repositories as substitutes for the canonical baseline.

## 5.6 Required reproduction outputs

```text
trend/
├── protocol.yaml
├── raw_contract_map.parquet
├── same_contract_returns.parquet
├── roll_events.parquet
├── factor_series.parquet
├── predictive_regressions.parquet
├── bootstrap_distributions.parquet
├── benchmark_comparison.parquet
├── cost_and_delay_ladder.parquet
├── crowding_analysis.parquet
└── verdict.json
```

## 5.7 Kill criteria

The hypothesis fails its initial replication gate if any of the following holds:

- profitability disappears when returns are calculated within the same contract;
- the strategy does not beat the historical-mean benchmark at matched risk;
- the pooled result fails dependence-aware bootstrap tests and there is no asset-level evidence;
- performance is attributable primarily to one asset class or one crisis;
- conservative costs and one-decision-period delay eliminate the result;
- the parameter neighborhood is unstable;
- the post-publication extension is economically null.

---

# 6. `EDGE-RISK-POLICY-001` — dependent volatility, abstention, and no-trade policy

## 6.1 Selected anchor

### Moreira and Muir — *Volatility-Managed Portfolios*

- Journal: *The Journal of Finance* (2017)
- DOI: `10.1111/jofi.12513`
- Working paper: NBER `w22208`
- Author page provides Internet Appendix and “Vol-Managed Factors Data.”
- Role: `ANCHOR_MECHANISM` and `ANCHOR_EMPIRICAL`
- Replication class: `NEAR_EXACT_PUBLIC`

### Why selected

The paper provides the canonical claim that reducing factor exposure when lagged volatility is high can expand the mean-variance opportunity set because expected returns do not rise proportionally with volatility.

### What must be replicated

1. unmanaged versus managed factor returns;
2. matched unconditional volatility;
3. spanning alpha and appraisal ratio;
4. leverage-constrained implementation;
5. transaction-cost sensitivity;
6. recession/crisis exposure;
7. utility under predeclared risk aversion;
8. sensitivity to volatility estimator and scaling cap.

## 6.2 Strongest direct opposing evidence

### Kang and Kwon — *Volatility-Managed Commodity Futures Portfolios*

- Journal: *Journal of Futures Markets* (2021)
- DOI: `10.1002/fut.22175`
- Role: `OPPOSING_EVIDENCE`
- Replication class: `EXACT_LICENSED` or author-data request

### Why selected

This paper directly tests the overlay in the project's primary asset class and finds that in-sample success may fail in real-time out-of-sample allocation. It also clarifies that a positive spanning alpha establishes value for an ex-post combination, not necessarily superiority of the managed portfolio by itself.

### Binding opposing tests

- recursive real-time estimation;
- ex-ante portfolio weights;
- managed-only versus optimal-combination performance;
- leverage and cap sensitivity;
- risk-return relation and volatility persistence diagnostics;
- no use of full-sample means or variances in the OOS policy.

## 6.3 Modern update

### DeMiguel, Martín-Utrera, and Uppal — *A Multifactor Perspective on Volatility-Managed Portfolios*

- Journal: *The Journal of Finance* (2024)
- DOI: `10.1111/jofi.13395`
- Role: `MODERN_UPDATE`
- Replication class: `NEAR_EXACT_PUBLIC`

### Why selected

The paper synthesizes the main criticism: individual-factor volatility management often weakens out of sample or after costs, while a conditional multifactor allocation can still add value. It forces the project to distinguish:

- scaling one strategy;
- combining managed and unmanaged versions;
- allocating among multiple frozen factors;
- data-mined selection of whichever overlay worked.

## 6.4 Project-specific replication design

This hypothesis is **dependent**. It may only be tested after an upstream signal and its cost model are frozen.

The initial policy family is deliberately small:

1. no overlay;
2. lagged realized-volatility target with hard leverage cap;
3. EWMA volatility target;
4. symmetric no-trade band around target exposure;
5. cost-aware abstention when expected edge is below conservative round-trip cost;
6. operational abstention for stale data, reconciliation failure, or venue-health failure.

The policy cannot jointly search over signal parameters, volatility estimator, target, cap, rebalance frequency, cost assumptions, and stop rules.

## 6.5 Accepted data and code

- Tyler Muir's official vol-managed factor data;
- Kenneth French factor returns;
- AQR BAB and other official factor datasets where required;
- project-owned recursive OOS implementation;
- DeMiguel et al. formulas and public factor sources.

No unaffiliated GitHub repository is accepted as authoritative code for Moreira–Muir.

## 6.6 Kill criteria

The overlay fails if:

- it improves Sharpe only by reducing unconditional risk;
- the gain disappears at matched volatility;
- OOS utility is nonpositive after costs;
- the result requires uncapped leverage;
- the result depends on full-sample parameter estimates;
- the overlay helps only one selected factor after searching many;
- turnover or tail exposure worsens under conservative execution;
- the no-trade rule merely delays losses rather than adding net utility.

---

# 7. `EDGE-FUT-CARRY-001` — listed-futures carry and curve premia

## 7.1 Anchor mechanism and decomposition

### Szymanowska, de Roon, Nijman, and van den Goorbergh — *An Anatomy of Commodity Futures Risk Premia*

- Journal: *The Journal of Finance* (2014)
- DOI: `10.1111/jofi.12096`
- Role: `ANCHOR_MECHANISM`
- Replication class: `EXACT_LICENSED`

### Why selected

This paper provides the most useful decomposition of:

- spot premia from underlying commodity risk;
- term premia from changes in basis;
- characteristic sorts including basis, momentum, volatility, inflation, hedging pressure, and liquidity.

It is selected to prevent the project from treating every curve-related return as one “carry” signal.

## 7.2 Anchor empirical extension

### Boons and Prado — *Basis-Momentum*

- Journal: *The Journal of Finance* (2019)
- DOI: `10.1111/jofi.12738`
- Role: `ANCHOR_EMPIRICAL`
- Replication class: `EXACT_LICENSED`

### Why selected

Basis-momentum combines information in nearby and deferred contracts and proposes an intermediary/market-clearing mechanism. It is central because it claims incremental information beyond simple basis and momentum.

### Required outputs

1. nearby holding returns;
2. calendar-spread returns;
3. basis, momentum, and basis-momentum sorts;
4. slope and curvature decomposition;
5. long and short leg contributions;
6. factor-spanning tests;
7. volatility, illiquidity, and intermediary-state conditioning;
8. cost and turnover calculation using executable calendar spreads;
9. post-1986 and post-publication subsamples.

## 7.3 Strongest contract-validity opposition

### Shang, Serra, and Garcia (2022)

- DOI: `10.1111/1477-9552.12485`
- Role: `OPPOSING_EVIDENCE`

This paper is binding because it shows how unrealizable roll yield and incorrect continuous-series returns can create apparent spread-momentum profitability.

Every carry replication must maintain separate objects for:

- signal series;
- contract-specific executable return;
- roll transaction;
- calendar-spread trade;
- collateral return;
- financing and margin.

## 7.4 Strongest interpretation challenge

### Yiyi, Cai, Zhu, and Webb — *Commodity Futures Characteristics and Asset Pricing Models*

- Journal: *Journal of Futures Markets* (2025)
- DOI: `10.1002/fut.22559`
- Role: `OPPOSING_EVIDENCE` / `MODERN_UPDATE`
- Replication class: `EXACT_LICENSED`; authors report code availability upon request but market data are licensed.

### Why selected

The paper challenges the alpha interpretation by showing that characteristic-return relations may operate through time-varying latent betas and compensation for risk rather than mispricing. The project must therefore report carry as a declared risk premium unless residual alpha survives modern factor controls.

## 7.5 Turnover and combination update

### Qian, Jiang, and Liu — *Factor Momentum in Commodity Futures Markets*

- Journal: *Journal of Futures Markets* (2025)
- DOI: `10.1002/fut.70022`
- Role: `MODERN_UPDATE`

The paper is selected not because factor momentum is automatically admitted, but because it demonstrates that a statistically attractive second layer of factor timing may lose practical value through turnover.

## 7.6 Data decision

Exact raw replication requires a licensed contract-level source with:

- settlement prices by maturity;
- contract specifications and multipliers;
- first and last trade dates;
- volume and open interest;
- exchange calendars;
- roll and delivery rules;
- bid/ask or defensible spread estimates;
- margin and fee history where available.

Public continuous futures are not acceptable as the sole source.

A public constructive pilot may test formulas and invariants, but it cannot issue the final empirical verdict.

## 7.7 Kill criteria

- any return includes price differences across different contracts as if they were cash PnL;
- basis-momentum is subsumed by simple basis after correct construction;
- net results fail conservative cost and margin treatment;
- profitability is concentrated in illiquid contracts or one sector;
- latent-factor controls reclassify the entire result as known risk without residual value;
- the parameter region is isolated;
- the modern/post-publication period is null.

---

# 8. `EDGE-FUT-POSITION-001` — hedging pressure, speculative pressure, and crowding

## 8.1 Selected anchor

### Fan, Fernandez-Perez, Fuertes, and Miffre — *Speculative Pressure*

- Journal: *Journal of Futures Markets* (2020)
- DOI: `10.1002/fut.22085`
- Role: `ANCHOR_MECHANISM` and `ANCHOR_EMPIRICAL`
- Data: CFTC public positioning plus Thomson Reuters Datastream prices
- Replication class:
  - positioning reconstruction: `EXACT_PUBLIC`;
  - complete return replication: `EXACT_LICENSED`.

### Why selected

The paper directly frames returns as compensation to speculators for accepting risk from hedgers and tests the premium across commodity, currency, equity-index, and fixed-income futures. The absence of a fixed-income result provides a useful negative cross-section.

## 8.2 Mandatory timing correction

CFTC positions generally reflect Tuesday's open interest and are released Friday. The project must distinguish:

```text
position_as_of_time != public_release_time != decision_time != execution_time
```

No signal may use Tuesday values before the actual Friday release. Historical files that label observations by report date must be joined to a release-time calendar.

## 8.3 Modern update and factor interaction

### Maréchal — *A Tale of Two Premiums Revisited*

- Journal: *Journal of Futures Markets* (2023)
- DOI: `10.1002/fut.22396`
- Role: `MODERN_UPDATE`
- Data: Refinitiv licensed
- Replication class: `EXACT_LICENSED`

### Why selected

It re-evaluates insurance and liquidity premia after adding basis, momentum, basis-momentum, open interest, and crowding factors. It is essential for testing incremental rather than standalone positioning value.

### Uhl (2025)

Uhl's crowding analysis is shared with the trend hypothesis. It tests whether the degree of speculative alignment predicts lower subsequent TSMOM performance. It is treated as an interaction study, not as independent proof of a profitable crowding-timing strategy.

## 8.4 Public data source

The official CFTC historical compressed files provide:

- Legacy futures-only data from 1986;
- Commodity Index Trader data from 2006;
- Disaggregated and Traders in Financial Futures reports from 2006/2009 onward;
- annual downloadable files;
- variable definitions and report categories.

The CFTC states that weekly reports reflect Tuesday positions and are released Friday at 3:30 p.m. Eastern time. This publication lag is a hard feature of the information contract.

## 8.5 Replication targets

1. exact COT category mapping by market and date;
2. speculative-pressure definitions and alternatives;
3. hedging-pressure definitions and alternatives;
4. crowding deviation from trailing position norms;
5. long-short sorts by asset class;
6. fixed-income negative control;
7. spanning against trend, carry, market, liquidity, and volatility;
8. release-lag stress of 0, 1, and 2 tradable sessions after publication;
9. revisions/category-break audit;
10. open-interest-only placebo.

## 8.6 Kill criteria

- signal availability is backdated to Tuesday;
- market/category mappings use future classifications;
- the result vanishes after carry and trend controls;
- the premium exists only in one category definition;
- fixed-income or placebo portfolios behave inconsistently with the declared mechanism;
- crowding predicts returns only in-sample;
- costs, turnover, or concentration eliminate the result.

---

# 9. `EDGE-CRYPTO-BASIS-001` — cross-sectional cryptocurrency derivatives state

## 9.1 Selected empirical anchor

### Chi, Hao, Hu, and Ran — *An Empirical Investigation on Risk Factors in Cryptocurrency Futures*

- Journal: *Journal of Futures Markets* (2023)
- DOI: `10.1002/fut.22425`
- Role: `ANCHOR_EMPIRICAL`
- Data: licensed GrandLine Technologies / 1Token OKEx dataset
- Sample: November 2017 through March 2021
- Replication class: `EXACT_LICENSED`

### Why selected

It is the clearest peer-reviewed cross-sectional test of cryptocurrency futures basis, momentum, and basis-momentum. It also reports that:

- basis is the strongest of the three factors;
- basis-momentum becomes insignificant after controlling for basis;
- daily results are stronger than weekly results;
- monthly results are weak;
- the strongest reported specification uses a five-day lookback and one-day holding period.

These features make it both an anchor and a high-risk overfitting target.

## 9.2 Exact replication targets

1. point-in-time universe from Table 3;
2. current-quarter futures and spot alignment;
3. basis, momentum, and basis-momentum formulas;
4. 1, 3, 5, and 7-period lookbacks, all reported rather than only the winner;
5. daily, weekly, and monthly holding periods;
6. high, medium, and low portfolio construction under varying universe size;
7. long and short legs;
8. five-basis-point cost case and a modern venue-specific cost ladder;
9. spanning regressions among the three factors;
10. controls for liquidity, volatility, skewness, dollar exposure, and market factors;
11. pre-2020, 2020–2021, and post-anchor prospective periods.

## 9.3 Strongest limitations

The anchor cannot be treated as exact-public because:

- the dataset is licensed and permission-controlled;
- only one venue is used;
- the universe is small and changes through time;
- the sample contains exceptional crypto appreciation;
- the strongest result is selected among several lookbacks;
- the reported returns are unusually large;
- monthly evidence disappears;
- contract and market rules have changed materially since the sample.

## 9.4 Mechanism and contract-design update

### Ackerer, Hugonnier, and Jermann — *Perpetual Futures Pricing*

- Journal: *Mathematical Finance* (published online 2025; volume 2026)
- DOI: `10.1111/mafi.70018`
- Role: `ANCHOR_MECHANISM` / `THEORETICAL_REPRODUCTION`

### Why selected

The paper formalizes linear, inverse, and quanto perpetual contracts and the funding specifications that anchor futures to spot. It prevents the empirical project from treating all perpetual bases as equivalent across settlement types.

### Theoretical reproduction targets

- linear perpetual pricing identity;
- inverse-contract convexity and settlement effects;
- funding specification required for zero basis;
- discrete versus continuous funding;
- effect of settlement currency and interest differential.

## 9.5 Modern market-structure update

### Shynkevich — *Trading Periodicity and Algorithmic Divide in Cryptocurrency Markets*

- Journal: *Journal of Futures Markets* (2026)
- DOI: `10.1002/fut.70089`
- Role: `MODERN_UPDATE`

The paper shows that major perpetual markets contain highly synchronized algorithmic activity at subsecond clock boundaries. This does not promote a latency strategy. It establishes that:

- five-minute directional studies may ignore substantial microstructure competition;
- execution price and observation time cannot be approximated casually;
- hourly-to-daily research remains the appropriate project horizon.

## 9.6 Public constructive replication

A modern constructive replication will use:

- OKX historical trades, candles, funding rates, mark prices, open interest, order-book data, and borrowing rates where available;
- Binance Vision public spot, perpetual, and dated-futures data;
- explicit contract metadata and funding-formula versions;
- BTC, ETH, and a predeclared liquid point-in-time universe;
- multiple venues, with no union of instruments using future liquidity.

OKX changed parts of its funding-rate formula and exposes `formulaType` in modern API responses. Historical signals must version the formula rather than assume a constant mechanism.

## 9.7 Kill criteria

- the 5-day result is not stable across neighboring lookbacks;
- the result disappears outside the original 2017–2021 sample;
- profits are primarily long-market beta;
- basis-momentum adds no value beyond basis;
- venue-specific replication fails;
- the signal requires unavailable historical constituents or formula fields;
- realistic spread, funding, and delay eliminate the result;
- one or two coins dominate the portfolio.

---

# 10. `EDGE-CRYPTO-RV-001` — delta-neutral cryptocurrency carry and dislocation convergence

## 10.1 Selected empirical anchor

### De Blasis and Webb — *Arbitrage, Contract Design, and Market Structure in Bitcoin Futures Markets*

- Journal: *Journal of Futures Markets* (2022)
- DOI: `10.1002/fut.22305`
- Role: `ANCHOR_EMPIRICAL` and `OPPOSING_EVIDENCE`
- Data: public Binance data
- Replication class: `EXACT_PUBLIC`, subject to exact data snapshot and historical contract metadata.

### Why selected

The paper is unusually valuable because it both identifies carry opportunities and limits the claim: quarterly cash-and-carry opportunities are concentrated in market dislocations. It also treats mark price, liquidation, insurance funds, stablecoin settlement, and auto-deleveraging as contract features rather than footnotes.

## 10.2 Modern structural anchor

### Schmeling, Schrimpf, and Todorov — *Crypto Carry*

- Journal: *Management Science* (online 2026)
- DOI: `10.1287/mnsc.2024.05069`
- Earlier version: BIS Working Paper 1087
- Role: `MODERN_UPDATE` and `ANCHOR_MECHANISM`
- Supplemental data: publisher data files
- Replication class: `NEAR_EXACT_PUBLIC` / supplement-dependent.

### Why selected

This paper reframes large basis as a product of:

- leveraged trend-chasing demand;
- scarcity of arbitrage capital;
- regulatory and margin frictions;
- convenience yield;
- segmentation across venues and traditional markets.

It rejects the phrase “risk-free arbitrage” unless the complete capital and failure path is modeled.

## 10.3 No-arbitrage theory

Ackerer, Hugonnier, and Jermann (`10.1111/mafi.70018`) is shared with `EDGE-CRYPTO-BASIS-001` and supplies the formal pricing identities.

## 10.4 Cross-venue limits-to-arbitrage context

Makarov and Schoar — *Trading and Arbitrage in Cryptocurrency Markets* — is retained as mechanism context for capital controls, settlement, and cross-country segmentation. It is not the direct empirical anchor for spot–perpetual carry because it studies a broader cross-exchange arbitrage problem.

## 10.5 Exact two-leg return contract

For each candidate trade, PnL must include:

```text
spot price change
+ futures/perpetual price change
+ received funding
- paid funding
- spot fee
- derivative fee
- bid/ask and slippage on both legs
- borrow or financing cost
- margin/collateral opportunity cost
- transfer and conversion cost
- settlement-currency PnL
- liquidation/ADL loss
- orphan-leg loss
- outage and rejection loss
- stablecoin and venue haircut
```

A terminal spread convergence chart is insufficient.

## 10.6 Production engineering references

### Hummingbot

Accepted as a production engineering reference for:

- spot and perpetual connectors;
- multi-venue order state;
- budget checks;
- hedging and arbitrage workflows;
- observed failure modes such as duplicate fills and stale balances.

Hummingbot issues documenting duplicate execution and delayed balance refresh are positive evidence that operational risk must be simulated; they are not evidence that a default arbitrage strategy is profitable.

### NautilusTrader

Retained as an event-driven state and backtest/live-semantics reference. It is not an empirical replication package for crypto carry.

### Exchange-native APIs

Official Binance and OKX APIs/data portals are authoritative for contract rules and public market data. A generic wrapper such as CCXT may be used behind a project-owned adapter, but raw exchange fields must be preserved.

## 10.7 Required paper-execution scenarios

1. both legs fill immediately;
2. spot fills, derivative rejects;
3. derivative fills, spot rejects;
4. partial fill on either leg;
5. funding formula changes while position is open;
6. mark price diverges from last price;
7. margin requirement increases;
8. transfer or withdrawal is suspended;
9. stablecoin depegs;
10. venue WebSocket disconnects;
11. order acknowledgement is lost;
12. auto-deleveraging closes the profitable leg;
13. basis widens before convergence;
14. forced exit under stale data;
15. restart and reconciliation with open positions.

## 10.8 Kill criteria

- positive carry requires leverage;
- conservative two-leg costs eliminate the premium;
- expected profit is smaller than orphan-fill stress loss;
- the strategy fails under a single funding reversal;
- capital lock-up makes risk-adjusted return unattractive;
- results depend on moving capital after a dislocation begins;
- venue or stablecoin haircuts eliminate net value;
- paper reconciliation fails;
- the opportunity occurs too rarely for a powered prospective test.

---

# 11. Common data-source decisions

## 11.1 Accepted official public sources

| Source | Use | Limitations |
|---|---|---|
| AQR Data Sets | updated TSMOM and selected factor returns | processed factors, not raw contract replication |
| CFTC historical COT files | public positioning and release-lag reconstruction | category changes; prices not included |
| Kenneth French Data Library | equity factor inputs for risk-policy replication | not futures data |
| Tyler Muir author page | vol-managed factor data and appendix | processed factors |
| Binance Vision | public spot, perpetual, and delivery data | historical metadata/version audit still required |
| OKX historical-data portal/API | trades, candles, funding, mark, OI, order book, borrowing | coverage begins on different dates; formulas changed |
| FRED | risk-free rates and selected macro controls | vintage rules required where revisions matter |
| Management Science supplement | Crypto Carry data files | scope and licenses must be inspected before use |

## 11.2 Licensed-source requirement

Traditional listed-futures exact replication requires a vendor or exchange-quality source. Report 2.2 must compare acquisition options before any raw-data result is called confirmatory.

Minimum required fields:

- contract identifier and maturity;
- exchange and currency;
- timestamped settlement/open/high/low/close;
- volume and open interest;
- multiplier, tick size, and price quotation;
- first/last trade and notice dates;
- margin and fee schedule where possible;
- timezone and session calendar;
- corrections and vintages.

## 11.3 Prohibited substitutions

- current continuous contract for historical contract chain;
- current instrument universe for point-in-time universe;
- current funding formula for old observations;
- close-to-close return across a roll boundary as executable PnL;
- midpoint returns without bid/ask stress;
- current COT category mapping applied backward without audit;
- public aggregate price substituted for venue-specific executable price;
- final revised macro data when real-time vintage is material.

---

# 12. Code-selection policy

## 12.1 Author code

Author-supplied code is preferred, but it must still be audited for:

- undeclared local files;
- hard-coded paths;
- non-deterministic seeds;
- silent data filtering;
- survivorship and look-ahead;
- package-version dependence;
- tables that cannot be rebuilt from raw inputs.

## 12.2 Independent audit implementation

Where author code is absent, this project will implement the published formulas independently. That implementation must:

- match hand-calculated micro examples;
- preserve raw and derived layers;
- emit content-addressed manifests;
- test all roll boundaries;
- expose every ranking and weight;
- reproduce tables before adding extensions;
- keep anchor, opposing, and modern-update experiments separate.

## 12.3 Production framework references

Production frameworks are used to learn state machines, connector behavior, and failure handling. They do not determine research truth.

Accepted references:

- Hummingbot — crypto connectors and multi-leg operational lessons;
- NautilusTrader — event-driven domain semantics and state recovery;
- Freqtrade — look-ahead analysis concepts for directional strategies;
- CCXT — optional market-access normalization, with preservation of raw exchange payloads;
- `bkelly-lab/ReplicationCrisis` — replication governance and factor-research organization;
- `joelowj/mtl-tsmom` — later model challenger, not canonical replication.

## 12.4 Rejected code categories

- code with no license;
- code with undisclosed data;
- one-notebook strategies with no tests;
- tutorials that use future-adjusted continuous prices;
- repositories that report only cumulative PnL;
- code that automatically tunes on the final test;
- “arbitrage” code without two-leg state and reconciliation;
- high-return crypto code whose result depends on extreme leverage;
- AI-generated repositories with no provenance or validation.

---

# 13. Exact tables and tests selected for Report 2.3

## 13.1 Trend family

- MOP predictive regressions and 12-month strategy;
- AQR updated factor-series extension;
- Huang pooled/fixed-effect/asset-level regressions and bootstrap critical values;
- MOP versus historical-mean benchmark;
- Shang same-contract and roll-yield correction;
- Uhl crowding interaction.

## 13.2 Carry family

- Szymanowska characteristic sorts and spot/term decomposition;
- Boons–Prado basis-momentum nearby and spreading returns;
- slope/curvature decomposition;
- transaction-cost and liquidity restrictions;
- Shang roll-validity negative control;
- Yiyi latent-beta versus alpha interpretation;
- Qian turnover erosion.

## 13.3 Positioning family

- Fan cross-asset speculative-pressure sorts;
- fixed-income negative control;
- factor-spanning tests;
- Maréchal insurance/liquidity premium after modern factor controls;
- public-release delay ladder;
- Uhl crowding interaction.

## 13.4 Risk-policy family

- Moreira–Muir matched-volatility managed factors;
- recursive OOS policy;
- Kang–Kwon managed-only and combination tests;
- DeMiguel OOS/net-cost conditional multifactor comparison;
- project no-trade and abstention extension on frozen upstream signals.

## 13.5 Crypto basis family

- Chi universe and factor sorts;
- all lookback/holding variants;
- long/short attribution;
- modern multi-venue public reconstruction;
- Ackerer contract-type identities;
- Shynkevich execution-clock stress.

## 13.6 Crypto relative-value family

- De Blasis contract-design and cash-and-carry tables;
- Crypto Carry basis distribution and explanatory tests;
- complete capital-path simulation;
- two-leg execution failure matrix;
- prospective paper ledger.

---

# 14. Replication execution order

## Stage 2.1-A — acquisition and legal/access audit

1. archive all open-access papers and supplements permitted by their licenses;
2. record DOI, version, publication date, and supplement checksum;
3. request author data/code where availability statements permit;
4. price licensed futures-data options;
5. freeze official public data endpoints and schemas;
6. create source snapshots and access logs.

## Stage 2.1-B — public-data feasibility prototypes

1. AQR TSMOM factor audit;
2. Moreira–Muir factor overlay audit;
3. CFTC release-time parser and category map;
4. Binance De Blasis-style contract reconstruction;
5. OKX/Binance funding and mark-price schema audit;
6. Crypto Carry supplement audit.

These prototypes test data feasibility, not strategy promotion.

## Stage 2.1-C — licensed exact-replication decision

Before purchasing or requesting data, Report 2.2 must establish:

- exact instruments and sample;
- vendor fields and vintages;
- licensing constraints on derived artifacts;
- expected acquisition cost;
- whether one source can support carry, trend, and positioning together;
- whether the sample contains all expired contracts and corrections.

## Stage 2.1-D — protocol freeze

Each paper receives a separate protocol hash. No combined “best of papers” strategy is allowed before all primitive replications are reported.

---

# 15. Binding decisions

1. MOP (2012) remains the canonical trend anchor, but Huang et al. (2020) is a co-equal required test, not an optional robustness check.
2. AQR's maintained TSMOM factor series is accepted for post-publication auditing but cannot replace raw contract reconstruction.
3. Every futures study must use same-contract executable returns and a separate roll ledger.
4. Szymanowska et al. and Boons–Prado jointly anchor carry because one decomposes premia and the other tests curve dynamics.
5. Shang et al. is a mandatory falsification reference for any roll- or spread-related result.
6. Characteristic returns remain declared risk premia until alpha survives modern latent-factor and state-risk controls.
7. Fan et al. anchors positioning, but CFTC publication time—not report date—governs information availability.
8. Moreira–Muir is replicated only beside Kang–Kwon and DeMiguel et al.; in-sample spanning alpha is insufficient.
9. Chi et al. is `EXACT_LICENSED`; a public OKX/Binance study is a new constructive replication.
10. De Blasis & Webb is the first exact-public crypto relative-value target.
11. Crypto Carry (2026) is the principal modern mechanism update for limits to arbitrage and capital scarcity.
12. Ackerer et al. supplies the mandatory theoretical contract model for perpetuals.
13. Hummingbot, NautilusTrader, Freqtrade, and CCXT are engineering references only.
14. Random public notebooks are not admitted as replication code.
15. No model architecture is selected in Report 2.1.
16. No hypothesis may skip its strongest opposing paper.
17. Failure to acquire exact licensed data results in `INCONCLUSIVE_EXACT_REPLICATION`, not a public-data “pass.”
18. Constructive replications receive new experiment identities.
19. All negative results remain permanent project memory.
20. Report 2.2 must now reconstruct data, timing, and information contracts before any empirical fitting begins.

---

# 16. Handoff to Report 2.2

Report 2.2 — **Data, Timing, and Information-Contract Reconstruction** must produce:

1. a paper-by-paper instrument manifest;
2. a point-in-time universe manifest;
3. a contract-chain and roll specification;
4. a source and license registry;
5. observation, release, receive, decision, and execution timestamps;
6. a raw-to-derived lineage graph;
7. a cost, financing, margin, and collateral contract;
8. source-version and formula-version handling;
9. an exact-versus-constructive replication boundary;
10. data acquisition go/no-go decisions;
11. immutable sample cutoffs;
12. adversarial data-quality tests.

No strategy result may be generated before those contracts are frozen.

---

# 17. Core reference registry

## Futures trend

1. Moskowitz, T. J., Ooi, Y. H., & Pedersen, L. H. (2012). *Time Series Momentum*. DOI: `10.1016/j.jfineco.2011.11.003`.
2. Huang, D., Li, J., Wang, L., & Zhou, G. (2020). *Time Series Momentum: Is It There?* DOI: `10.1016/j.jfineco.2019.08.004`.
3. Shang, Q., Serra, T., & Garcia, P. (2022). *Ride the Trend: Is There Spread Momentum Profit in the US Commodity Markets?* DOI: `10.1111/1477-9552.12485`.
4. Uhl, B. (2025). *Speculators and Time Series Momentum in Commodity Futures Markets*. DOI: `10.1002/rfe.1228`.
5. Zheng, Y., Zhang, X., Lien, D., & Yu, X. (2025). *Evaluating Trend-Based Strategies in Chinese Commodity Futures Markets*. DOI: `10.1002/fut.70033`.

## Futures carry and positioning

6. Szymanowska, M., de Roon, F., Nijman, T., & van den Goorbergh, R. (2014). *An Anatomy of Commodity Futures Risk Premia*. DOI: `10.1111/jofi.12096`.
7. Boons, M., & Prado, M. P. (2019). *Basis-Momentum*. DOI: `10.1111/jofi.12738`.
8. Fan, J. H., Fernandez-Perez, A., Fuertes, A.-M., & Miffre, J. (2020). *Speculative Pressure*. DOI: `10.1002/fut.22085`.
9. Maréchal, L. (2023). *A Tale of Two Premiums Revisited*. DOI: `10.1002/fut.22396`.
10. Yiyi, Q., Cai, J., Zhu, J., & Webb, R. (2025). *Commodity Futures Characteristics and Asset Pricing Models*. DOI: `10.1002/fut.22559`.
11. Qian, Y., Jiang, Y., & Liu, X. (2025). *Factor Momentum in Commodity Futures Markets*. DOI: `10.1002/fut.70022`.
12. Nakagawa, K., & Sakemoto, R. (2025). *Prices of Risk Estimation for Commodity Factors*. DOI: `10.1002/fut.70032`.

## Risk policy

13. Moreira, A., & Muir, T. (2017). *Volatility-Managed Portfolios*. DOI: `10.1111/jofi.12513`.
14. Kang, J., & Kwon, K. Y. (2021). *Volatility-Managed Commodity Futures Portfolios*. DOI: `10.1002/fut.22175`.
15. DeMiguel, V., Martín-Utrera, A., & Uppal, R. (2024). *A Multifactor Perspective on Volatility-Managed Portfolios*. DOI: `10.1111/jofi.13395`.

## Cryptocurrency derivatives

16. Chi, Y., Hao, W., Hu, J., & Ran, Z. (2023). *An Empirical Investigation on Risk Factors in Cryptocurrency Futures*. DOI: `10.1002/fut.22425`.
17. De Blasis, R., & Webb, A. (2022). *Arbitrage, Contract Design, and Market Structure in Bitcoin Futures Markets*. DOI: `10.1002/fut.22305`.
18. Schmeling, M., Schrimpf, A., & Todorov, K. (2026). *Crypto Carry*. DOI: `10.1287/mnsc.2024.05069`.
19. Ackerer, D., Hugonnier, J., & Jermann, U. (2025/2026). *Perpetual Futures Pricing*. DOI: `10.1111/mafi.70018`.
20. Shynkevich, A. (2026). *Trading Periodicity and Algorithmic Divide in Cryptocurrency Markets*. DOI: `10.1002/fut.70089`.
21. Makarov, I., & Schoar, A. (2020). *Trading and Arbitrage in Cryptocurrency Markets*. *Journal of Financial Economics*, 135(2), 293–319.

---

# Final decision

Report 2.1 is complete. The project now has a finite replication queue, explicit opposing evidence, exactness labels, official data routes, code-admission rules, table-level targets, and kill criteria.

The next permissible action is Report 2.2. The next impermissible action is to begin tuning a trading model before the data and timing contracts are reconstructed and frozen.
