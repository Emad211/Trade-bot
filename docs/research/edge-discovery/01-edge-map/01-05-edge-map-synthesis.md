# Report 1.5 — Edge Map Synthesis and Replication Admissions

**Program:** Edge Discovery Research Program  
**Section:** 1 — Edge Map  
**Report:** 5 of 5  
**Version:** 1.0  
**Research freeze date:** 2026-07-18  
**Status:** Complete  
**Parents:** [Report 1.1](01-01-edge-definition-and-proof-standard.md), [Report 1.2](01-02-taxonomy-of-edge-mechanisms.md), [Report 1.3](01-03-market-instrument-horizon-competition-capacity-map.md), and [Report 1.4](01-04-falsification-and-evidence-design.md)  
**Decision type:** Section-level synthesis and admission decision for formal replication  
**Machine-readable companion:** [01-05-replication-admission-manifest.yaml](01-05-replication-admission-manifest.yaml)

---

# Executive decision

Section 1 does **not** identify a proven trading edge. It identifies a deliberately small set of economic hypotheses that are sufficiently coherent, falsifiable, data-feasible, and implementable to justify formal replication.

The future trading system should not be organized around a model family such as a transformer, gradient-boosted tree, large language model, or foundation time-series model. It should be organized around economic mechanisms and portfolio functions:

1. **structural risk transfer and futures-curve premia;**
2. **medium-frequency trend and slow price adjustment across diversified markets;**
3. **positioning, crowding, and intermediary constraints as separately tested information;**
4. **cryptocurrency derivatives structure as both a research domain and the first accessible runtime laboratory;**
5. **cost-aware abstention, no-trade regions, and volatility/risk policy as dependent overlays rather than stand-alone alpha claims;**
6. **execution and operational reliability as a separate source of retained value, never confused with predictive alpha.**

The section admits five confirmatory hypotheses and one conditional secondary hypothesis:

| Rank | Hypothesis ID | Short name | Admission |
|---:|---|---|---|
| 1 | `EDGE-FUT-CARRY-001` | Diversified futures carry and curve premia | `ADMITTED_FOR_REPLICATION` |
| 2 | `EDGE-FUT-TREND-001` | Diversified medium-frequency futures trend | `ADMITTED_FOR_REPLICATION` |
| 3 | `EDGE-CRYPTO-BASIS-001` | Cross-sectional cryptocurrency derivatives state | `ADMITTED_FOR_REPLICATION` |
| 4 | `EDGE-FUT-POSITION-001` | Futures positioning and crowding | `ADMITTED_FOR_REPLICATION` |
| 5 | `EDGE-RISK-POLICY-001` | Incremental cost-aware risk and abstention policy | `ADMITTED_AS_DEPENDENT_REPLICATION` |
| 6 | `EDGE-CRYPTO-RV-001` | Delta-neutral cryptocurrency basis dislocations | `CONDITIONAL_SECONDARY_REPLICATION` |

These admissions authorize **research replication only**. They do not authorize paper trading, live trading, strategy promotion, leverage, or capital deployment.

The primary research environment is diversified liquid listed futures at daily-to-weekly horizons. The first operational runtime laboratory may be liquid cryptocurrency spot and perpetual markets at hourly-to-daily horizons because APIs and market data are more accessible. This distinction is binding:

> Cryptocurrency may be the first market in which the runtime is exercised, while diversified listed futures remain the stronger scientific environment for evaluating generalizable economic mechanisms.

---

# 1. Purpose

Reports 1.1 through 1.4 answered four foundational questions:

1. What qualifies as a genuine trading edge?
2. Through which economic mechanisms can an edge arise?
3. In which market–instrument–horizon combinations can an independent operator plausibly compete?
4. What falsification protocol must every candidate survive?

Report 1.5 answers the final question in Section 1:

> Which small set of economic hypotheses deserves scarce replication, data-engineering, and implementation resources, and which attractive alternatives must be rejected or deferred?

The output is intentionally narrower than the preceding reports. Broad exploration is useful for constructing the map. Formal replication requires concentration.

---

# 2. Binding conclusions inherited from Reports 1.1–1.4

## 2.1 Historical evidence does not prove a live edge

A backtest can:

- reject a hypothesis;
- expose leakage;
- estimate sensitivity;
- compare a candidate with a benchmark;
- justify collecting genuinely new data.

A backtest cannot prove that a live edge exists.

Every hypothesis admitted here remains a **candidate edge** until it survives:

- exact literature and code replication;
- point-in-time dataset reconstruction;
- sealed confirmatory evaluation;
- genuinely forward-only shadow observation;
- realistic event-driven paper execution;
- controlled minimal-capital live evaluation.

## 2.2 The economic mechanism precedes the model

A feature, model, prompt, neural architecture, or data provider is not an economic mechanism.

For example:

- funding rate is a measurement, not an edge;
- open interest is a measurement, not an edge;
- TimesFM is a forecasting tool, not an edge;
- a large language model is an information-processing tool, not an edge;
- order-book imbalance is a signal candidate, not an edge;
- volatility targeting is a policy candidate, not automatically an edge.

Each admitted hypothesis must identify:

- the economic payer;
- the reason the opportunity may persist;
- the risks transferred or absorbed;
- the conditions under which the effect should disappear;
- the executable action through which the effect could be captured.

## 2.3 Costs and execution are part of the hypothesis

The project will not begin with a frictionless signal and append costs at the end.

The hypothesis includes:

- when information becomes available;
- when a decision can be calculated;
- when an order can be sent;
- which price is executable;
- whether the order is filled;
- how much is filled;
- financing, funding, margin, borrow, and settlement;
- what happens during outages, liquidations, or contract rolls;
- how performance changes with capital.

## 2.4 Independent evidence must include disagreement

A hypothesis is not admitted because one highly cited paper reports a large Sharpe ratio.

Admission considers:

- positive evidence;
- failed replications;
- post-publication performance;
- methodology-sensitive findings;
- evidence that a return is risk compensation rather than alpha;
- evidence that costs or contract construction create the appearance of profitability.

## 2.5 The project prefers slower, diversified mechanisms

For an independent operator without colocation or privileged feeds, the preferred horizon is the slowest horizon that:

- preserves the proposed mechanism;
- produces enough independent decisions;
- leaves sufficient gross edge after costs;
- does not require winning a physical latency race.

The preferred alpha research bands remain:

- one hour to one day for liquid cryptocurrency derivatives;
- one day to one month for diversified futures and later-stage equity or option research.

## 2.6 No single statistic is a promotion gate

Sharpe ratio, p-value, Probabilistic Sharpe Ratio, Deflated Sharpe Ratio, Probability of Backtest Overfitting, Superior Predictive Ability, and bootstrap confidence intervals are diagnostics.

The project requires defense in depth:

- protocol freeze;
- temporal audit;
- full trial accounting;
- family-level testing;
- negative controls;
- cost and execution stress;
- specification and regime stability;
- fresh prospective evidence.

---

# 3. Operator assumptions

The decisions in this report are conditional on an operator with:

- strong software-engineering capability;
- applied statistics and machine-learning capability;
- access to ordinary cloud or dedicated servers;
- no exchange colocation;
- no proprietary dealer flow;
- no exclusive news feed;
- no institutional prime-broker infrastructure at the start;
- small-to-moderate research capital;
- willingness to collect forward data for months;
- willingness to accept that every candidate may fail.

A different operator profile could produce a different ranking.

---

# 4. Decision principles

## 4.1 Scientific value is not the same as operational accessibility

A market can be attractive for research but difficult to access live.

A market can be easy to connect to but weak as a source of generalizable evidence.

The project therefore scores two separate questions:

1. Is the hypothesis scientifically worth replicating?
2. Is the market suitable for the first operational runtime?

## 4.2 Admission is based on mechanisms, not strategy names

The report does not admit a generic “momentum strategy” or “carry strategy.”

It admits specific hypothesis identities with:

- a defined market;
- a defined instrument family;
- a defined horizon;
- a defined economic payer;
- a limited family of specifications;
- predeclared null and rejection conditions.

## 4.3 Closely related ideas remain separate hypotheses

The following are not merged merely because they use the same dataset:

- futures carry;
- trend following;
- basis momentum;
- speculative pressure;
- volatility management;
- cryptocurrency funding;
- cryptocurrency cash-and-carry.

Combining them before the primitive effects are replicated would obscure:

- which mechanism produces the return;
- how many research trials occurred;
- which risk is being absorbed;
- which component fails after costs.

## 4.4 Complexity carries an evidentiary burden

A complex model must beat a simple, economically aligned benchmark after:

- all costs;
- identical information;
- identical exposure;
- identical risk;
- identical execution timing;
- trial-selection adjustment.

Complexity is not a source of prior credibility.

---

# 5. Pre-replication admission rubric

This rubric determines whether a hypothesis deserves formal replication. It is not the proof score from Report 1.1 and is not a probability of profitability.

| Dimension | Weight | Question |
|---|---:|---|
| Economic mechanism clarity | 15 | Is the payer and persistence mechanism explicit? |
| Independent supporting and opposing evidence | 15 | Is there enough evidence to justify a confirmatory test and enough disagreement to make the test informative? |
| Falsifiability and benchmark quality | 10 | Can a clear null, strongest feasible benchmark, and kill condition be frozen? |
| Point-in-time data feasibility | 15 | Can the historical information set be reconstructed without revision leakage? |
| Execution and cost observability | 15 | Can executable prices, financing, fills, rolls, and failures be modeled? |
| Cross-market or cross-venue replication | 10 | Can the mechanism be tested beyond one asset, venue, or episode? |
| Independent-operator speed fit | 10 | Can the mechanism survive without privileged latency? |
| Capacity and operational fit | 10 | Is it suitable for small-to-moderate capital with bounded operational risk? |
| **Total** | **100** | |

## 5.1 Admission bands

| Score | Admission meaning |
|---:|---|
| 85–100 | Primary formal replication |
| 75–84 | Formal replication with explicit constraints |
| 65–74 | Conditional or secondary replication |
| 50–64 | Watchlist or exploratory-only |
| below 50 | Reject for the current program |

A hard failure overrides the score.

## 5.2 Hard failures

A candidate is rejected regardless of score when it requires:

- known look-ahead information;
- an unreconstructable historical universe;
- an impossible fill assumption;
- unmodeled leverage or liquidation;
- speed unavailable to the operator;
- a narrative created only after observing the result;
- a benchmark intentionally weaker than the candidate;
- a test family that cannot be honestly enumerated;
- a market that the operator cannot legally or operationally access;
- a strategy whose downside cannot be bounded before live use.

---

# 6. Candidate universe considered

The synthesis considered the following broad families:

1. diversified futures trend;
2. futures carry and term structure;
3. futures basis momentum and curve structure;
4. hedging pressure, speculative pressure, crowding, and open interest;
5. cryptocurrency funding, basis, open interest, liquidations, and crowding;
6. cryptocurrency delta-neutral cash-and-carry;
7. volatility management;
8. selective participation and no-trade regions;
9. equity cross-sectional factors;
10. equity event-driven information;
11. listed options and volatility-surface strategies;
12. decentralized-finance relative value;
13. liquidity provision and market making;
14. news and language-model signals;
15. general machine-learning direction prediction;
16. high-frequency and latency arbitrage.

The purpose was not to find the highest reported historical Sharpe ratio. It was to identify the hypotheses for which a failed replication would be informative and a successful replication would be actionable.

---

# 7. Admission scores and decisions

| Rank | Hypothesis | Mechanism | Evidence | Falsifiability | Data | Execution | Replication | Speed fit | Capacity | Total | Decision |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `EDGE-FUT-CARRY-001` | 15 | 14 | 9 | 14 | 14 | 10 | 10 | 9 | **95** | Primary replication |
| 2 | `EDGE-FUT-TREND-001` | 13 | 14 | 10 | 15 | 14 | 10 | 10 | 9 | **95** | Primary replication |
| 3 | `EDGE-CRYPTO-BASIS-001` | 14 | 11 | 9 | 12 | 11 | 8 | 9 | 8 | **82** | Constrained replication |
| 4 | `EDGE-FUT-POSITION-001` | 14 | 12 | 9 | 11 | 13 | 8 | 10 | 9 | **86** | Primary replication, lower execution order |
| 5 | `EDGE-RISK-POLICY-001` | 13 | 12 | 10 | 14 | 14 | 10 | 10 | 10 | **93** | Dependent replication only |
| 6 | `EDGE-CRYPTO-RV-001` | 15 | 10 | 9 | 10 | 8 | 7 | 8 | 6 | **73** | Conditional secondary replication |
| — | Equity cross-sectional factors | 13 | 14 | 9 | 8 | 7 | 10 | 10 | 8 | **79** | Deferred by prerequisite |
| — | Listed option factors | 13 | 13 | 8 | 5 | 5 | 8 | 9 | 6 | **67** | Deferred |
| — | DeFi structural relative value | 14 | 7 | 7 | 8 | 5 | 6 | 7 | 5 | **59** | Watchlist |
| — | LLM/news semantic signals | 8 | 6 | 7 | 7 | 9 | 6 | 8 | 8 | **59** | Shadow/exploratory only |
| — | Generic single-asset ML direction | 4 | 6 | 6 | 12 | 11 | 5 | 9 | 9 | **62** | Rejected as primary thesis |
| — | Subsecond HFT/latency arbitrage | 13 | 12 | 8 | 5 | 3 | 7 | 0 | 2 | **50** | Hard reject |
| — | Illiquid altcoins, any short horizon | 5 | 5 | 5 | 7 | 3 | 4 | 7 | 2 | **38** | Reject |
| — | Same-block decentralized arbitrage/MEV | 14 | 9 | 7 | 5 | 2 | 5 | 0 | 2 | **44** | Hard reject |
| — | Unhedged short-volatility income | 14 | 11 | 8 | 7 | 5 | 8 | 9 | 4 | **66** | Hard reject for initial system |

The table contains two distinct concepts:

- **scientific score**, reflecting whether formal research could be valuable;
- **program decision**, reflecting current prerequisites and operational constraints.

For example, equity factors score well scientifically but are deferred because point-in-time membership, delistings, corporate actions, and borrow data would create a large parallel data program before the project has completed a simpler multi-asset futures foundation.

---

# 8. Workstream architecture

## Workstream A — Diversified listed-futures economic research

Purpose:

- establish a rigorous, generalizable multi-asset research foundation;
- compare slow economic mechanisms under standardized contracts;
- avoid dependence on one cryptocurrency, one exchange, or one market regime.

Admitted hypotheses:

- `EDGE-FUT-CARRY-001`;
- `EDGE-FUT-TREND-001`;
- `EDGE-FUT-POSITION-001`.

Preferred initial universe:

- major equity-index futures;
- government-bond and interest-rate futures;
- currency futures;
- liquid commodity futures.

Preferred horizons:

- daily signals;
- weekly or monthly portfolio updates where appropriate;
- no intraday alpha requirement.

## Workstream B — Cryptocurrency derivatives research and runtime bridge

Purpose:

- test whether derivatives state contains cross-sectional or relative-value information;
- build the first event-driven runtime using accessible APIs;
- measure real operational frictions before the final alpha domain is known.

Admitted hypotheses:

- `EDGE-CRYPTO-BASIS-001`;
- `EDGE-CRYPTO-RV-001` as secondary.

Preferred initial universe:

- BTC;
- ETH;
- a limited point-in-time universe of the most liquid perpetual and spot instruments;
- dated futures only where historical contract data and execution are reliable.

Preferred horizons:

- hourly to daily;
- no subsecond or five-minute directional HFT;
- no reliance on illiquid tokens.

## Workstream C — Dependent risk and participation policy

Purpose:

- determine whether a simple, frozen risk policy increases net utility;
- reduce turnover and catastrophic exposure without claiming independent directional skill.

Admitted hypothesis:

- `EDGE-RISK-POLICY-001`.

This workstream begins only after an upstream signal is frozen. It must never search jointly over:

- signal;
- volatility model;
- threshold;
- risk target;
- rebalance frequency;
- cost assumptions.

Joint search would make the overlay inseparable from strategy overfitting.

---

# 9. Hypothesis card — EDGE-FUT-CARRY-001

## 9.1 Identity

```yaml
hypothesis_id: EDGE-FUT-CARRY-001
title: Diversified listed-futures carry and curve premia
status: ADMITTED_FOR_REPLICATION
primary_mechanism: risk_transfer_and_structural_curve_premia
secondary_mechanisms:
  - inventory_and_storage_constraints
  - intermediary_balance_sheet_constraints
  - hedging_demand
  - funding_and_liquidity_risk
market: diversified_liquid_listed_futures
horizon: daily_to_monthly
```

## 9.2 Economic proposition

The shape of a futures curve contains information about expected returns because market participants demand or supply risk transfer under:

- inventory and storage conditions;
- producer and consumer hedging demand;
- funding constraints;
- intermediary capital constraints;
- convenience yield;
- market segmentation.

The expected return may be compensation for risk rather than mispricing. That does not make it economically irrelevant, but it changes the correct benchmark and interpretation.

## 9.3 Economic payer

Potential payers include:

- commercial hedgers willing to pay for predictable cash flows;
- inventory holders and users transferring price risk;
- leveraged participants facing funding constraints;
- intermediaries with limited balance-sheet capacity;
- investors demanding specific maturity exposure.

## 9.4 Persistence mechanism

The effect can persist because the underlying participants are not all return-maximizers. Hedging, inventory, regulation, and balance-sheet constraints can create persistent demand.

The effect should weaken when:

- arbitrage capital becomes abundant;
- storage or funding constraints change;
- financialization alters the participant mix;
- curve trades become crowded;
- the measured basis is an artifact of continuous-contract construction.

## 9.5 Evidence supporting replication

The commodity-futures literature documents economically meaningful spot and term premia associated with basis and related characteristics. Szymanowska et al. distinguish spot premia from term premia and find that basis factors explain important cross-sectional variation ([2013](https://doi.org/10.1111/jofi.12096)).

Boons and Prado propose basis momentum, related to changes in slope and curvature, and interpret the effect through impaired market-clearing capacity of speculators and intermediaries ([2018](https://doi.org/10.1111/jofi.12738)).

Maréchal reports that basis, momentum, basis momentum, and crowding remain relevant when revisiting liquidity and insurance premia, while some variables such as open-interest growth perform poorly in the evaluated specification ([2023](https://doi.org/10.1002/fut.22396)).

## 9.6 Evidence challenging replication

The literature is not uniform on:

- whether observed characteristics represent alpha or latent risk exposure;
- whether return calculations include unrealisable roll yield;
- whether results survive modern costs;
- whether complex combinations add value beyond simple factors.

Yiyi et al. report that relationships between commodity characteristics and returns are driven primarily by time-varying latent-factor betas rather than characteristic-linked alpha ([2025](https://doi.org/10.1002/fut.22559)).

Shang, Serra, and Garcia show that incorrect treatment of roll yield can create an illusion of profitable spread momentum ([2022](https://doi.org/10.1111/1477-9552.12485)).

Qian, Jiang, and Liu find strong gross factor-momentum patterns but report substantial erosion from turnover and transaction costs ([2025](https://doi.org/10.1002/fut.70022)).

## 9.7 Exact hypothesis to replicate

Primary confirmatory statement:

> A predeclared, diversified portfolio formed from point-in-time futures-curve information produces positive net utility relative to equal-risk passive, equal-weighted futures, and simple curve benchmarks after correct same-contract return construction, explicit roll execution, fees, spreads, and conservative implementation costs.

The first experiment will not combine every known curve factor.

Primitive signals must be replicated separately:

1. normalized carry or basis;
2. basis momentum or curve change;
3. optional simple equal-weight combination only after primitive results are reported.

## 9.8 Required data

For every contract:

- raw contract identifier;
- venue;
- underlying;
- expiry;
- first notice and last trade dates where applicable;
- settlement price;
- executable bid/ask where available;
- volume;
- open interest;
- contract multiplier;
- tick size;
- currency;
- trading calendar;
- roll eligibility and liquidity.

Continuous prices may be used for diagnostics only. Realized strategy returns must be formed from actual held contracts and explicit roll trades.

## 9.9 Strongest benchmarks

At minimum:

- equal-risk passive futures exposure where economically meaningful;
- equal-weighted universe;
- long-only commodity index for commodity-only subsets;
- simple nearby basis sort;
- no-signal volatility-scaled portfolio;
- randomized ranks preserving turnover and cross-sectional exposure.

## 9.10 Main null

> After correct contract construction and realistic implementation, no member of the predeclared carry/curve family has positive expected net utility relative to the strongest feasible benchmark.

## 9.11 Mandatory negative controls

- random cross-sectional ranks;
- sign-reversed basis;
- stale basis delayed by one rebalance;
- continuous-series return versus same-contract return comparison;
- synthetic roll-yield contamination test;
- random maturity pairing;
- matched-turnover null portfolios.

## 9.12 Kill criteria

Reject the candidate when any of the following is true:

- profitability depends on cross-contract price jumps that cannot be realized;
- the conservative lower confidence bound is nonpositive;
- break-even cost is below realistic all-in cost;
- one commodity sector or one crisis carries most positive performance;
- the effect vanishes outside the original publication period;
- the effect is dominated by passive exposure or leverage;
- small changes in roll policy reverse the conclusion;
- the effect requires unavailable maturity-specific information.

## 9.13 Admission decision

**Admitted as the first formal replication priority.**

Reason:

- clear economic payer;
- multi-asset diversification;
- slow horizon;
- standardized contracts;
- strong positive and opposing literature;
- falsifiable contract-construction questions;
- direct relevance to future portfolio architecture.

---

# 10. Hypothesis card — EDGE-FUT-TREND-001

## 10.1 Identity

```yaml
hypothesis_id: EDGE-FUT-TREND-001
title: Diversified medium-frequency futures trend
status: ADMITTED_FOR_REPLICATION
primary_mechanism: slow_price_adjustment_and_behavioral_trend
secondary_mechanisms:
  - gradual_information_diffusion
  - institutional_hedging_flows
  - crisis_convexity
  - risk_transfer
market: diversified_liquid_listed_futures
horizon: daily_to_weekly
```

## 10.2 Economic proposition

Past price direction may contain information about future returns because:

- information diffuses gradually;
- investors underreact or herd;
- institutional positions adjust slowly;
- hedging and policy flows are persistent;
- trends emerge after structural shocks.

A diversified strategy may be more credible than a single-market trend rule because weak, imperfectly correlated effects can aggregate.

## 10.3 Economic payer

Potential payers include:

- participants who adjust positions slowly;
- hedgers prioritizing risk transfer over expected return;
- investors who underreact and later chase trends;
- participants forced to deleverage after adverse moves.

## 10.4 Persistence mechanism

The effect can persist if its return compensates trend followers for:

- whipsaw losses in range-bound markets;
- prolonged periods of underperformance;
- liquidity demand during reversals;
- crowding and momentum crashes.

It should decay when:

- many similar strategies trade the same markets;
- transaction costs and turnover dominate;
- return persistence disappears;
- volatility scaling rather than direction generates the historical result.

## 10.5 Evidence supporting replication

Trend and time-series momentum have been documented across futures markets and CTA returns. Bollen, Hutchinson, and O’Brien find that CTA conformity is associated with time-series momentum exposure, while noting the gap between idealized factor returns and realized manager performance after frictions ([2021](https://doi.org/10.1002/fut.22199)).

Han and Kong report a commodity trend factor robust to alternative moving-average signals, second-nearby contracts, active-contract rolls, and a transaction-cost exercise ([2021](https://doi.org/10.1002/fut.22291)).

Recent evidence in Chinese commodity futures also reports robust trend performance across a broad modern sample, though market-specific structure remains important ([Zheng et al., 2025](https://doi.org/10.1002/fut.70033)).

## 10.6 Evidence challenging replication

Trend evidence is sensitive to:

- benchmark choice;
- volatility scaling;
- contract rolling;
- selected parameter windows;
- sample period;
- crowding;
- transaction costs.

Zoicas-Ienciu reports fading, nonpersistent, and methodology-sensitive excess returns for generic trend reactions ([2020](https://doi.org/10.1002/ijfe.1833)).

Szakmary and Lancaster find that individual-stock trend profitability vanishes after 2007 ([2015](https://doi.org/10.1111/fire.12065)).

Shang, Serra, and Garcia show that apparent spread momentum can be generated by unrealisable roll yield and biased regression design ([2022](https://doi.org/10.1111/1477-9552.12485)).

Uhl finds that stronger alignment between speculator positions and generic trend can be associated with weaker subsequent trend performance, consistent with crowding decay ([2025](https://doi.org/10.1002/rfe.1228)).

## 10.7 Exact hypothesis to replicate

> A small, predeclared ensemble of simple trend specifications across diversified liquid futures produces positive net utility relative to equal-risk passive and random-direction benchmarks, after decomposing direction, volatility scaling, asset allocation, contract rolls, and costs.

The project will not search thousands of moving-average combinations.

The initial family will contain a small, justified grid such as:

- medium and slow return-sign trend;
- moving-average or breakout equivalents with similar effective horizon;
- equal-volatility portfolio;
- one unscaled version to separate signal from sizing.

## 10.8 Required decomposition

Reported performance must be decomposed into:

1. raw directional effect;
2. volatility-scaling effect;
3. cross-asset allocation effect;
4. long and short legs;
5. contract-roll effect;
6. crisis and noncrisis performance;
7. market-sector contribution;
8. cost and turnover.

## 10.9 Strongest benchmarks

- equal-risk long-only portfolio;
- equal-weighted futures portfolio;
- random sign with identical exposure and turnover;
- constant-volatility no-signal exposure;
- simple 12-month sign benchmark;
- carry-controlled trend and trend-controlled carry.

## 10.10 Main null

> After correct contract construction, risk matching, selection adjustment, and all-in costs, the predeclared trend family does not outperform the strongest feasible benchmark.

## 10.11 Mandatory negative controls

- shuffled trend signs in dependence-preserving blocks;
- sign reversal;
- one-period signal delay;
- random lookback selected before test;
- continuous-contract versus actual-contract return comparison;
- volatility scaling with random direction;
- trend direction with constant sizing.

## 10.12 Kill criteria

Reject when:

- the directional component is nonpositive after separating volatility scaling;
- performance depends on one lookback parameter;
- performance vanishes under actual roll execution;
- most profits arise from one crisis or one asset sector;
- post-publication periods are materially negative without an economic explanation;
- crowding-adjusted or delayed results collapse below cost;
- the candidate fails family-level multiple-testing correction.

## 10.13 Admission decision

**Admitted as the second formal replication priority and the primary benchmark family.**

Trend is admitted because it is:

- simple;
- economically interpretable;
- widely documented;
- widely criticized;
- easy to falsify;
- useful as a benchmark even if ultimately rejected.

---

# 11. Hypothesis card — EDGE-CRYPTO-BASIS-001

## 11.1 Identity

```yaml
hypothesis_id: EDGE-CRYPTO-BASIS-001
title: Cross-sectional cryptocurrency derivatives state
status: ADMITTED_FOR_REPLICATION
primary_mechanism: leverage_demand_and_derivatives_market_segmentation
secondary_mechanisms:
  - intermediary_constraints
  - crowding
  - forced_liquidation
  - slow_cross_market_adjustment
market: liquid_crypto_spot_perpetual_and_dated_futures
horizon: hourly_to_daily
```

## 11.2 Economic proposition

The joint state of:

- perpetual funding;
- perpetual–spot basis;
- dated-futures basis;
- open-interest change;
- liquidation state;
- price momentum;
- liquidity;

may reveal:

- leveraged demand;
- crowded positioning;
- limits to arbitrage;
- future risk transfer;
- differential expected returns across liquid cryptocurrency assets.

The claim is cross-sectional and state-dependent. It is not a claim that funding alone predicts Bitcoin direction.

## 11.3 Economic payer

Potential payers include:

- leveraged speculators paying funding;
- traders forced to liquidate;
- participants unable or unwilling to move collateral across venues;
- hedgers demanding short or long exposure;
- investors accepting inferior relative prices for leverage or immediacy.

## 11.4 Persistence mechanism

The effect can persist because cryptocurrency markets remain:

- fragmented;
- collateral-constrained;
- exposed to exchange-specific margin rules;
- settled in different currencies and stablecoins;
- subject to 24/7 liquidation;
- costly to arbitrage across venues.

It should weaken as:

- institutional arbitrage capital increases;
- venue fragmentation decreases;
- contract design converges;
- funding and basis data become crowded;
- access restrictions prevent execution.

## 11.5 Evidence supporting replication

Chi et al. examine 12 major cryptocurrencies and report that futures basis is the strongest cross-sectional predictor among their evaluated characteristics, with stronger effects at daily than longer horizons ([2023](https://doi.org/10.1002/fut.22425)).

The broader crypto-derivatives literature documents significant price discovery in futures and perpetual markets and persistent differences caused by market structure, arbitrage capital, and leverage demand.

## 11.6 Evidence challenging replication

The evidence base is shorter and more venue-specific than traditional futures.

Risks include:

- survivorship-biased token universes;
- changing contract specifications;
- funding-history revisions or gaps;
- exchange outages;
- stablecoin exposure;
- liquidation and auto-deleveraging;
- unmodeled mark/index prices;
- transfer and withdrawal constraints;
- regulatory access;
- extreme claims based on weak backtests.

De Blasis and Webb show that apparent cash-and-carry opportunities are concentrated in dislocations and require realistic treatment of execution, margin, and contract-specific risks ([2022](https://doi.org/10.1002/fut.22305)).

Aleti and Mizrach document professional price discovery and microstructure competition across Bitcoin spot and futures markets ([2020](https://doi.org/10.1002/fut.22163)).

Shynkevich finds that subsecond price discovery is strongly associated with proprietary algorithmic activity, reinforcing the decision to avoid latency competition ([2026](https://doi.org/10.1002/fut.70089)).

## 11.7 Exact hypothesis to replicate

> A predeclared cross-sectional policy based on normalized derivatives state produces incremental net utility over liquidity-matched momentum, equal-weighted, and random-rank benchmarks across a point-in-time universe of liquid cryptocurrency instruments.

Primitive effects must be evaluated separately:

1. basis;
2. funding;
3. open-interest change;
4. liquidation/crowding state;
5. simple, predeclared combination.

The first confirmatory test will not include a large machine-learning feature zoo.

## 11.8 Initial universe policy

The universe must be rebuilt point in time using:

- instrument listing and delisting dates;
- minimum trailing dollar volume;
- minimum order-book depth where available;
- maximum spread;
- minimum history;
- spot and derivative availability;
- contract and settlement-currency consistency.

Using today’s largest tokens in the historical sample is prohibited.

## 11.9 Required data

- trades and quotes or defensible executable bars;
- spot price;
- perpetual price;
- mark price;
- index price;
- actual funding rate and payment time;
- dated-futures prices where available;
- open interest;
- liquidation records with availability time;
- contract metadata;
- fee tiers;
- margin and liquidation schedules;
- venue status and outages;
- stablecoin conversion state.

## 11.10 Strongest benchmarks

- liquidity-matched momentum;
- equal-weighted liquid crypto portfolio;
- BTC/ETH passive exposure;
- random cross-sectional ranks;
- funding-only;
- basis-only;
- no-derivatives feature model;
- same signal delayed by one funding interval.

## 11.11 Main null

> Derivatives-state features do not provide incremental net economic value beyond simple price, liquidity, and momentum benchmarks after point-in-time universe construction, venue-realistic costs, and family-level selection adjustment.

## 11.12 Mandatory negative controls

- randomized funding across assets within timestamp;
- one-interval delayed derivatives state;
- sign-reversed basis;
- pseudo-funding generated from unrelated assets;
- no-open-interest ablation;
- no-liquidation ablation;
- venue holdout;
- asset holdout;
- stablecoin-regime exclusion.

## 11.13 Kill criteria

Reject when:

- the effect exists only on one exchange;
- the effect is driven by illiquid or delisted tokens;
- a one-interval delay removes all value;
- funding payments and fees consume the gross result;
- the effect depends on leverage;
- conservative mark-price or liquidation assumptions make the result negative;
- post-2021 or post-publication evidence is absent;
- the strategy cannot be executed in the operator’s accessible venues.

## 11.14 Admission decision

**Admitted as a constrained replication and the bridge to runtime engineering.**

It ranks below traditional futures because the evidence is narrower and operational risk is higher. It remains valuable because it can test a structural mechanism while exercising a real event-driven system.

---

# 12. Hypothesis card — EDGE-FUT-POSITION-001

## 12.1 Identity

```yaml
hypothesis_id: EDGE-FUT-POSITION-001
title: Futures positioning and crowding
status: ADMITTED_FOR_REPLICATION
primary_mechanism: hedger_speculator_risk_transfer_and_crowding
secondary_mechanisms:
  - intermediary_capacity
  - slow_position_adjustment
  - liquidity_risk
market: diversified_liquid_listed_futures
horizon: weekly_to_monthly
```

## 12.2 Economic proposition

Public positioning data may contain incremental information about expected futures returns because:

- commercial hedgers transfer risk;
- speculators absorb that risk;
- crowded speculative positions may reduce future compensation;
- position changes can reveal slow-moving capital and intermediary constraints.

This hypothesis is separate from carry and trend even though the signals may correlate.

## 12.3 Economic payer

- commercial hedgers seeking insurance;
- participants demanding immediacy;
- crowded speculators entering or exiting similar positions;
- intermediaries with limited balance-sheet capacity.

## 12.4 Evidence supporting replication

Fan et al. report significant speculative-pressure premia in commodity, currency, and equity-index futures, but not fixed income, and interpret the results as hedger-to-speculator risk transfer ([2019](https://doi.org/10.1002/fut.22085)).

Maréchal reports that crowding contributes to an optimal commodity factor set and that insurance and liquidity premia remain after broader adjustment, although their economic and statistical magnitude attenuates ([2023](https://doi.org/10.1002/fut.22396)).

## 12.5 Evidence challenging replication

Positioning data are:

- aggregated;
- delayed;
- revised or reclassified;
- weekly rather than daily;
- not maturity-specific in many public datasets;
- potentially endogenous to recent returns.

Clements and Todorova find that after controlling for news flow, net trader positions play only a minor role in explaining realized volatility for gold and crude oil ([2015](https://doi.org/10.1002/fut.21724)).

Uhl’s evidence suggests that stronger alignment with generic trend positions can predict weaker future trend performance, but reports limited ability to exploit that relation dynamically ([2025](https://doi.org/10.1002/rfe.1228)).

## 12.6 Exact hypothesis to replicate

> Point-in-time public positioning and crowding variables provide incremental net utility beyond carry and trend when evaluated at their true publication time and with a predeclared weekly or monthly policy.

Primitive tests:

1. hedging pressure;
2. speculative pressure;
3. crowding relative to trailing history;
4. open-interest growth as a negative or low-prior comparator.

## 12.7 Publication-time contract

A Tuesday observation released later in the week cannot be used as though available on Tuesday.

For each report:

- observation date;
- publication date;
- retrieval time;
- revision policy;
- earliest executable decision time

must be stored separately.

## 12.8 Strongest benchmarks

- carry;
- trend;
- carry plus trend;
- lagged return and volatility;
- random position ranks;
- stale position data;
- equal-weighted universe.

## 12.9 Main null

> Public positioning and crowding data provide no incremental economic value over frozen carry, trend, and liquidity benchmarks after true publication-time alignment.

## 12.10 Kill criteria

Reject when:

- apparent performance disappears under publication delay;
- open-interest growth is the only surviving result;
- the effect is confined to one commodity category;
- the result is subsumed by trend or carry;
- revisions materially change historical signals;
- the effect cannot survive conservative weekly execution costs;
- the incremental lower confidence bound is nonpositive.

## 12.11 Admission decision

**Admitted for formal replication, but sequenced after the carry and trend data foundation.**

The lower implementation order reflects data-publication complexity, not a weak economic mechanism.

---

# 13. Hypothesis card — EDGE-RISK-POLICY-001

## 13.1 Identity

```yaml
hypothesis_id: EDGE-RISK-POLICY-001
title: Incremental cost-aware risk and abstention policy
status: ADMITTED_AS_DEPENDENT_REPLICATION
primary_mechanism: selective_participation_and_turnover_control
secondary_mechanisms:
  - volatility_timing
  - no_trade_region
  - drawdown_control
  - operational_risk_reduction
market: applies_to_frozen_upstream_strategy
horizon: same_or_slower_than_upstream
```

## 13.2 Economic proposition

A strategy may retain more value by:

- scaling exposure when forecast risk changes;
- refusing trades whose expected benefit does not exceed all-in cost and uncertainty;
- using no-trade regions;
- reducing unnecessary rebalancing;
- lowering exposure during liquidity or operational stress.

The policy does not need better directional accuracy. It must improve net economic utility.

## 13.3 Why it is not an independent alpha thesis

A policy that reduces volatility can create a higher Sharpe ratio while lowering expected return.

A policy can also appear beneficial because it was optimized jointly with the signal.

Therefore:

- the upstream signal must be frozen first;
- overlay research receives a separate trial family;
- the benchmark must be risk matched;
- both return and risk must be reported;
- leverage and cash exposure must be transparent.

## 13.4 Evidence supporting replication

Moreira and Muir document benefits from volatility-managed portfolios in multiple factor settings ([2017](https://doi.org/10.1111/jofi.12513)).

Gârleanu and Pedersen show that optimal dynamic trading under costs naturally creates gradual adjustment and no-trade behavior rather than immediate movement to a frictionless target ([2013](https://doi.org/10.1111/jofi.12080)).

## 13.5 Evidence challenging replication

DeMiguel et al. report that many volatility-managed strategies are less compelling out of sample and after transaction costs than in headline historical results ([2024](https://doi.org/10.1111/jofi.13395)).

Romero and Opschoor find that a simple EWMA volatility model remains difficult to beat after transaction costs, including against sophisticated high-frequency covariance models ([2026](https://doi.org/10.1002/jae.70053)).

The evidence supports testing simple policies before complex regime models.

## 13.6 Exact hypothesis to replicate

> A predeclared, simple risk and abstention policy applied to a frozen upstream strategy improves conservative net utility relative to the same strategy under constant-risk and no-overlay execution.

Primitive policies:

1. constant target risk;
2. simple EWMA or realized-volatility scaling;
3. cost-and-uncertainty abstention;
4. no-trade band;
5. operational stress shutdown rule evaluated separately.

## 13.7 Strongest benchmarks

- upstream strategy with fixed exposure;
- upstream strategy with constant ex ante volatility;
- cash-scaled benchmark with matched realized volatility;
- equal-turnover randomized abstention;
- simple EWMA versus every more complex volatility model.

## 13.8 Main null

> The risk policy provides no incremental net utility after matching exposure, volatility, turnover, and cash allocation.

## 13.9 Mandatory controls

- random abstention with identical trade count;
- delayed volatility estimate;
- fixed-risk scaling;
- equal-turnover smoothing;
- risk policy on a random upstream signal;
- stress-rule ablation;
- leverage-disabled analysis.

## 13.10 Kill criteria

Reject when:

- utility improvement disappears under risk matching;
- the overlay merely reduces exposure;
- the result depends on one volatility window;
- turnover reduction rather than risk information explains the result and a simpler no-trade band performs as well;
- complex volatility models fail to beat EWMA;
- drawdown improvement is offset by unacceptable loss of expected return;
- the policy was jointly optimized with the upstream signal.

## 13.11 Admission decision

**Admitted only as a dependent replication.**

It cannot begin until at least one upstream hypothesis has a frozen implementation and immutable historical outputs.

---

# 14. Hypothesis card — EDGE-CRYPTO-RV-001

## 14.1 Identity

```yaml
hypothesis_id: EDGE-CRYPTO-RV-001
title: Delta-neutral cryptocurrency basis dislocations
status: CONDITIONAL_SECONDARY_REPLICATION
primary_mechanism: market_segmentation_and_limits_to_arbitrage
secondary_mechanisms:
  - leverage_demand
  - collateral_constraints
  - transfer_friction
  - settlement_and_stablecoin_risk
market: liquid_crypto_spot_perpetual_and_dated_futures
horizon: multi_hour_to_multi_week
```

## 14.2 Economic proposition

Large net carry or basis dislocations may compensate capital providers that can hold offsetting spot and derivative positions.

The candidate is not risk free.

Returns may compensate:

- exchange credit risk;
- stablecoin risk;
- funding reversal;
- basis widening;
- liquidation;
- transfer constraints;
- operational complexity;
- inability to exit both legs simultaneously.

## 14.3 Exact hypothesis to replicate

> A fully collateralized, delta-neutral policy entering only predeclared large dislocations produces positive net return after both-leg execution, funding, financing, transfer, margin, liquidation, and venue-risk charges.

## 14.4 Why secondary

The economic mechanism is strong, but historical simulation is difficult because:

- order-level two-leg execution is required;
- collateral and margin are path dependent;
- funding can reverse;
- venue risk is endogenous to dislocations;
- historical account and transfer constraints are difficult to reconstruct;
- apparent arbitrage may be compensation for catastrophic venue or stablecoin risk.

## 14.5 Mandatory controls

- no-transfer assumption versus explicit transfer delay;
- same-venue versus cross-venue implementation;
- one-leg fill stress;
- funding reversal;
- stablecoin depeg;
- mark-price shock;
- auto-deleveraging;
- withdrawal suspension;
- full collateral versus leverage;
- venue default haircut.

## 14.6 Kill criteria

Reject when:

- positive return requires leverage;
- one-leg execution cannot be bounded;
- return disappears under conservative transfer and settlement assumptions;
- break-even venue-loss probability is implausibly small;
- the result is driven entirely by periods in which capital could not actually be moved;
- no accessible venue permits the required operation.

## 14.7 Admission decision

**Conditional secondary replication.**

It should not delay the primary futures and cross-sectional crypto workstreams.

---

# 15. Deferred domains

## 15.1 Cross-sectional equities

### Scientific merits

- broad cross-section;
- extensive factor literature;
- corporate and event information;
- deep regulated markets;
- clear connection to portfolio construction.

### Deferral reasons

- point-in-time index and listing membership;
- delistings;
- splits, dividends, mergers, and corporate actions;
- historical borrow availability and fees;
- survivorship-free fundamentals;
- earnings and filing publication timestamps;
- exchange calendars and auction behavior.

Recent evidence shows that short-sale costs can remove the abnormal return of many long–short anomaly portfolios ([Muravyev, Pearson, and Pollet, 2025](https://doi.org/10.1111/jofi.13501)).

### Re-entry conditions

Equity research may enter Section 2 after:

- the multi-asset instrument model exists;
- point-in-time universe infrastructure is complete;
- borrow data can be sourced;
- corporate-action accounting is tested;
- futures replication has established the experiment registry.

## 15.2 Listed options

### Scientific merits

- variance risk premium;
- skew and term-structure information;
- option momentum;
- relative-value and mispricing research;
- rich risk-transfer mechanisms.

### Deferral reasons

- noisy and asynchronous quotes;
- surface interpolation;
- dividend and rate assumptions;
- stale quotes;
- wide spreads;
- margin;
- exercise and assignment;
- delta, gamma, vega, and jump hedging;
- path-dependent execution.

Wallmeier documents material implied-volatility data distortions caused by timestamp mismatch and dividend information errors ([2024](https://doi.org/10.1002/fut.22495)).

Do, Foster, and Gray show that apparently large volatility-spread profits can be heavily reduced by bid–ask spreads and margin treatment ([2015](https://doi.org/10.1002/fut.21729)).

Option momentum is scientifically promising, but credible implementation requires substantially more market-state and execution detail than the first program stage ([Heston et al., 2023](https://doi.org/10.1111/jofi.13279)).

### Re-entry conditions

- synchronized option and underlying quotes;
- validated surface construction;
- assignment and margin simulator;
- multi-leg order model;
- realistic hedge execution;
- option-specific data-quality audit.

## 15.3 Decentralized finance

### Scientific merits

- transparent on-chain state;
- staking and lending basis;
- protocol-level segmentation;
- structural liquidity provision;
- novel relative-value relationships.

### Deferral reasons

- smart-contract risk;
- oracle risk;
- bridge risk;
- governance risk;
- gas and failed transactions;
- maximum-extractable-value competition;
- block-level ordering;
- protocol upgrades;
- stablecoin and collateral cascades;
- chain reorganizations.

### Re-entry conditions

- protocol-state replay;
- deterministic transaction simulator;
- smart-contract and oracle risk model;
- gas and block-inclusion model;
- explicit catastrophic-loss prior.

## 15.4 News, language models, and semantic signals

These remain shadow research tools, not primary edge theses.

Potential roles:

- classify known events;
- map entities;
- detect policy or protocol changes;
- enrich risk-state monitoring;
- generate hypotheses.

They are not admitted as primary directional strategies because:

- historical model training may contain future information;
- document availability is difficult to reconstruct;
- prompts and providers change;
- semantic relevance does not imply price impact;
- latency and publication-time competition matter;
- model outputs are difficult to reproduce across versions.

A language model may enter a future hypothesis only after:

- raw source capture is prospective;
- model revision and prompt are frozen;
- inference completion time defines availability;
- keyword and non-LLM baselines are strong;
- the effect is incremental to market-state variables.

---

# 16. Rejected domains

## 16.1 Generic single-asset direction prediction

Rejected as the primary project thesis.

Examples include:

- predict the next Bitcoin candle from OHLCV;
- optimize a deep model on one asset;
- use a foundation time-series model as a direct buy/sell engine;
- search technical indicators until one works.

Reason:

- weak economic payer;
- high trial freedom;
- limited diversification;
- easy benchmark manipulation;
- high sensitivity to costs;
- previous project results already failed stricter robustness gates.

This does not prohibit using price models as components or baselines.

## 16.2 Subsecond and low-latency trading

Hard rejected for the initial program.

Reason:

- physical infrastructure is part of the edge;
- public historical data do not prove the signal was accessible first;
- queue position and feed latency dominate;
- the operator lacks colocation and privileged market data.

Short-horizon data may still be used to control execution.

## 16.3 Illiquid altcoin strategies

Rejected because:

- manipulated volume;
- large spread;
- weak depth;
- delisting and survivorship bias;
- venue concentration;
- capacity collapse;
- unreliable short availability.

## 16.4 Same-block arbitrage and MEV

Hard rejected because:

- specialized infrastructure;
- block-builder and validator relationships;
- adversarial transaction ordering;
- gas auction;
- smart-contract and reversion risk;
- speed competition outside the operator profile.

## 16.5 Naked short-volatility income

Hard rejected for the first system.

A smooth historical premium is not sufficient when one unobserved tail event can dominate years of returns.

Any future short-volatility work requires:

- bounded-loss construction;
- catastrophe stress;
- margin and assignment simulation;
- liquidity and gap risk;
- explicit insurance-premium interpretation.

---

# 17. Decision dependencies

The replication sequence is not identical to the score ranking.

```text
Instrument and contract data foundation
    ├── EDGE-FUT-CARRY-001
    ├── EDGE-FUT-TREND-001
    └── EDGE-FUT-POSITION-001
          └── cross-signal incremental tests

Crypto event-driven market-data foundation
    ├── EDGE-CRYPTO-BASIS-001
    └── EDGE-CRYPTO-RV-001 [secondary]

Frozen upstream strategy
    └── EDGE-RISK-POLICY-001
```

## 17.1 Recommended implementation order

1. Select literature and code for `EDGE-FUT-CARRY-001`.
2. Select literature and code for `EDGE-FUT-TREND-001`.
3. Define the shared listed-futures contract and roll data model.
4. Select literature for `EDGE-CRYPTO-BASIS-001`.
5. Design the general multi-venue runtime domain model.
6. Add `EDGE-FUT-POSITION-001` after publication-time data can be represented.
7. Test `EDGE-RISK-POLICY-001` only on frozen upstream outputs.
8. Attempt `EDGE-CRYPTO-RV-001` only after two-leg paper execution exists.

---

# 18. Section 2 handoff

Report 2.1 must select:

- anchor papers;
- opposing papers;
- replication papers;
- available codebases;
- exact tables and figures to reproduce;
- data sources and licensing constraints.

## 18.1 Required paper roles

For each admitted hypothesis, Report 2.1 must identify:

1. **Anchor paper** — strongest clear formulation.
2. **Opposing or skeptical paper** — strongest methodological or empirical challenge.
3. **Modern update** — evidence from a recent period.
4. **Implementation paper** — cost, execution, or capacity treatment.
5. **Replication asset** — code or data description sufficient to rebuild the result.

## 18.2 Minimum initial dossiers

### EDGE-FUT-CARRY-001

Candidate anchors:

- Szymanowska et al., *An Anatomy of Commodity Futures Risk Premia* ([2013](https://doi.org/10.1111/jofi.12096)).
- Boons and Prado, *Basis-Momentum* ([2018](https://doi.org/10.1111/jofi.12738)).

Candidate opposing/update papers:

- Shang, Serra, and Garcia ([2022](https://doi.org/10.1111/1477-9552.12485)).
- Yiyi et al. ([2025](https://doi.org/10.1002/fut.22559)).
- Qian, Jiang, and Liu ([2025](https://doi.org/10.1002/fut.70022)).

### EDGE-FUT-TREND-001

Candidate anchors:

- a canonical diversified futures time-series momentum formulation;
- Han and Kong’s trend factor ([2021](https://doi.org/10.1002/fut.22291)).

Candidate opposing/update papers:

- Zoicas-Ienciu ([2020](https://doi.org/10.1002/ijfe.1833));
- Shang, Serra, and Garcia ([2022](https://doi.org/10.1111/1477-9552.12485));
- Uhl ([2025](https://doi.org/10.1002/rfe.1228));
- Zheng et al. ([2025](https://doi.org/10.1002/fut.70033)).

### EDGE-CRYPTO-BASIS-001

Candidate anchor:

- Chi et al. ([2023](https://doi.org/10.1002/fut.22425)).

Candidate skeptical and implementation papers:

- De Blasis and Webb ([2022](https://doi.org/10.1002/fut.22305));
- Aleti and Mizrach ([2020](https://doi.org/10.1002/fut.22163));
- Shynkevich ([2026](https://doi.org/10.1002/fut.70089)).

### EDGE-FUT-POSITION-001

Candidate anchors:

- Fan et al. ([2019](https://doi.org/10.1002/fut.22085));
- Maréchal ([2023](https://doi.org/10.1002/fut.22396)).

Candidate opposing or limiting papers:

- Clements and Todorova ([2015](https://doi.org/10.1002/fut.21724));
- Uhl ([2025](https://doi.org/10.1002/rfe.1228)).

### EDGE-RISK-POLICY-001

Candidate anchors:

- Moreira and Muir ([2017](https://doi.org/10.1111/jofi.12513));
- Gârleanu and Pedersen ([2013](https://doi.org/10.1111/jofi.12080)).

Candidate opposing/update papers:

- DeMiguel et al. ([2024](https://doi.org/10.1111/jofi.13395));
- Romero and Opschoor ([2026](https://doi.org/10.1002/jae.70053)).

---

# 19. Dataset implications

Section 3 must not inherit the repository’s current single-BTC candle schema as the general research model.

The data model must support:

## 19.1 Instrument identity

- asset class;
- venue;
- underlying;
- contract;
- expiry;
- settlement currency;
- multiplier;
- tick and lot size;
- margin class;
- trading calendar.

## 19.2 Multiple clocks

- event time;
- exchange time;
- publication time;
- receive time;
- processing completion time;
- decision time;
- order-submission time;
- acknowledgment time;
- fill time.

## 19.3 Futures curves

- multiple maturities;
- actual contract prices;
- roll eligibility;
- explicit roll transactions;
- notice and expiry rules;
- same-contract returns;
- continuous-series diagnostics kept separate.

## 19.4 Positioning data

- observation date;
- release date;
- vintage;
- classification;
- revision;
- source hash.

## 19.5 Cryptocurrency derivatives

- spot;
- perpetual;
- dated future;
- mark and index;
- funding;
- open interest;
- liquidation;
- margin tiers;
- venue outages;
- settlement currency;
- stablecoin state.

## 19.6 Trial and protocol records

- hypothesis identity;
- parent identity;
- confirmatory or exploratory status;
- config hash;
- code commit;
- data snapshot;
- benchmark;
- metrics;
- full negative results;
- deviation log.

---

# 20. Runtime implications

The live architecture should be multi-asset and multi-venue even if the first adapter is cryptocurrency-only.

It must model:

- `InstrumentId`;
- `VenueId`;
- `AccountId`;
- cash and settlement balances;
- spot, future, perpetual, and later option instruments;
- order state;
- fill state;
- position state;
- margin state;
- funding and financing;
- contract expiry and roll;
- portfolio-level risk;
- multi-currency valuation;
- reconciliation;
- persistence and restart recovery;
- kill switches.

Research and live systems must use compatible definitions of:

- time;
- instrument;
- order;
- fill;
- cost;
- portfolio state;
- risk.

A future architecture may use an existing engine or an internal implementation. Framework choice remains outside Section 1.

---

# 21. Relationship to the current repository

The existing repository contains valuable research safeguards:

- chronological sealed folds;
- label availability purging;
- explicit embargo;
- cost-aware evaluation;
- Probabilistic and Deflated Sharpe diagnostics;
- dependence-aware block bootstrap;
- fold-concentration checks;
- doubled-cost stress;
- automatic-promotion prohibition.

The prior robustness gate rejected every evaluated nontrend model. That negative result is retained.

However, the current implementation remains centered on:

- BTC;
- four-hour bars;
- long/flat exposure;
- one-bar holding periods;
- simple proportional cost;
- historical model screening.

Section 1 does not discard the safeguards. It discards the assumption that the existing market, model, target, or horizon is the final thesis.

Required generalizations include:

- multi-asset portfolio accounting;
- futures contracts and rolls;
- cross-sectional decisions;
- short exposure where instrument rules permit;
- funding and margin;
- multi-period positions;
- event-driven fills;
- trial registry;
- negative-control registry;
- prospective shadow protocol.

TimesFM, Chronos, LightGBM, CatBoost, Ridge, and prior semantic experiments remain historical evidence about attempted tools. None is an admitted edge mechanism.

---

# 22. Universal prohibitions for Section 2 and later

The following actions are prohibited:

1. selecting papers only because they report high performance;
2. omitting skeptical or failed-replication papers;
3. tuning the hypothesis after opening the final test;
4. using continuous futures jumps as realizable returns;
5. using today’s crypto or equity universe historically;
6. using report dates before publication;
7. treating funding as risk-free yield;
8. ignoring margin, liquidation, or auto-deleveraging;
9. combining primitive signals before separate reporting;
10. using a complex model without a simple matched benchmark;
11. reusing sealed test outcomes for model selection;
12. deleting negative experiments;
13. calling a risk premium “alpha” without factor and tail analysis;
14. starting paper trading automatically;
15. deploying live capital from historical evidence alone.

---

# 23. Criteria for revising the admission list

The admission list can change only through a versioned amendment.

A new hypothesis may enter when:

- strong new peer-reviewed evidence appears;
- a credible code and data replication asset becomes available;
- a missing data prerequisite is solved;
- operator access changes;
- an existing hypothesis is rejected and resources become available.

An admitted hypothesis may be removed when:

- its anchor result cannot be reproduced;
- the data cannot be reconstructed honestly;
- execution is infeasible;
- the effect is a contract-construction artifact;
- costs or capacity eliminate the result;
- a stronger benchmark subsumes it;
- the operator cannot access the market.

Every amendment must preserve the original report and create a new version.

---

# 24. Final Section 1 thesis

The most defensible direction for the future bot is:

> A multi-asset, event-driven portfolio system that researches slow structural futures premia and diversified trend, tests positioning and cryptocurrency derivatives state as separate incremental hypotheses, applies simple cost-aware abstention and risk policies only after upstream signals are frozen, and preserves value through rigorous execution, reconciliation, and operational risk control.

This thesis intentionally rejects the idea that the project’s edge will come from one magical forecasting model.

The likely final source of value, if the program succeeds, is an ensemble of modest and independently validated components:

\[
\text{Net system value}
=
\text{structural premia}
+
\text{slow predictive effects}
+
\text{portfolio diversification}
+
\text{selective participation}
+
\text{execution quality}
-
\text{costs}
-
\text{operational failures}
-
\text{tail losses}.
\]

Each term must be measured separately before the combined system is evaluated.

---

# 25. Section 1 completion decision

Section 1 is complete.

The following are now fixed:

- definition of edge;
- economic mechanism taxonomy;
- market and horizon map;
- falsification protocol;
- replication admission list;
- deferred and rejected domains;
- section-to-section dependencies.

The next report is:

> **Report 2.1 — Anchor Papers, Opposing Evidence, and Replication Code Selection**

Report 2.1 must not reopen the Section 1 conclusions merely because a paper or repository is convenient. Any proposed deviation requires an explicit amendment.

---

# 26. Search provenance

The synthesis used focused peer-reviewed searches through Scholar Gateway under one research interaction identity.

## 26.1 Diversified futures trend

**Search scope:** supporting and opposing evidence for daily-to-weekly diversified trend, including out-of-sample evidence, rolls, costs, crowding, volatility scaling, and simple-versus-complex comparisons.  
**Coverage returned:** 20 passages, 16 unique articles, 2008-10-14 through 2026-04-03.

## 26.2 Futures carry, curve, and positioning

**Search scope:** carry, basis, basis momentum, hedging pressure, speculative pressure, crowding, turnover, downside risk, and post-publication robustness.  
**Coverage returned:** 20 passages, 11 unique articles, 2013-08-22 through 2026-04-03.

## 26.3 Cryptocurrency derivatives

**Search scope:** funding, basis, open interest, liquidations, cross-sectional returns, cash-and-carry, execution, leverage, stablecoin, venue risk, and latency competition.  
**Coverage returned:** 20 passages, 12 unique articles, 2020-10-08 through 2026-02-18.

## 26.4 Risk and abstention policy

**Search scope:** volatility management, liquidity regimes, no-trade regions, abstention, costs, turnover, matched-risk comparisons, and simple-versus-complex risk models.  
**Coverage returned:** 20 passages, 14 unique articles, 2016-03-18 through 2026-02-16.

## 26.5 Equity and option deferral

**Search scope:** point-in-time equity data, borrow, options quote quality, surface construction, spreads, hedging, margin, and execution.  
**Coverage returned:** 20 passages, 11 unique articles, 2002-03-16 through 2025-09-30.

Scholar Gateway coverage is broad but not exhaustive. Section 2 must verify primary papers, supplementary materials, code, and data directly.

---

# 27. Limitations

- Admission scores are structured judgments, not statistical estimates.
- Peer-reviewed evidence can still contain data errors, selection bias, and weak execution assumptions.
- Futures data quality and licensing may constrain exact replication.
- Cryptocurrency venue history is short and institutionally unstable.
- Public positioning data are delayed and aggregated.
- Risk-policy evidence may not transfer across upstream signals.
- A mechanism can be real but unavailable to this operator.
- A successful historical replication may fail in fresh data.
- A candidate may survive because an unobserved tail event has not occurred.
- The final valid outcome of the program may still be to reject every admitted hypothesis.

---

# Final decision

Five hypotheses are admitted for formal or dependent replication, and one is admitted conditionally as a secondary workstream.

No strategy is promoted.

No paper ledger is started.

No live trading is authorized.

The next action is to build Report 2.1 around the admitted hypothesis identities and select the exact papers, opposing evidence, codebases, tables, and data contracts to reproduce.
