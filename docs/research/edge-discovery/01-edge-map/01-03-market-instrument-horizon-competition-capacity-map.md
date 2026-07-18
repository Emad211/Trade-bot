# Report 1.3 — Market, Instrument, Horizon, Competition, and Capacity Map

**Research program:** Edge Discovery Research Program  
**Section:** 1 — Edge Map  
**Report:** 1.3 of 1.5  
**Version:** 1.0  
**Date:** 2026-07-18  
**Status:** Complete  
**Depends on:** Report 1.1 and Report 1.2  
**Purpose:** Identify the market–instrument–horizon combinations in which a small independent systematic operator can realistically search for, validate, and operate a trading edge.

---

## 1. Executive decision

No market is globally “best.” A market is suitable only when its economic edge mechanism, data, execution model, competition, operational risk, capital requirements, and research horizon fit the operator.

For the operator profile defined in this report, the initial ranking is:

1. **Diversified liquid listed futures at daily-to-weekly horizons** are the strongest scientific research environment.
2. **Liquid cryptocurrency spot and perpetual markets at hourly-to-daily horizons** are the most accessible environment for building and validating a first event-driven live runtime, but have materially greater venue, stablecoin, liquidation, and 24/7 operational risk.
3. **Liquid equities and exchange-traded funds at daily-to-monthly horizons** provide the broadest cross-section and the richest factor and event data, but require careful point-in-time universe construction, corporate-action processing, and borrow modeling.
4. **Listed options at daily-to-monthly horizons** are a high-potential second-stage research domain, not the preferred first live market, because surface construction, spreads, margin, exercise, Greeks, and hedging semantics greatly increase the number of ways to create false profitability.
5. **Decentralized-finance relative value at multi-hour-to-multi-week horizons** may contain genuine structural opportunities, especially staking, lending, and basis dislocations, but protocol, bridge, oracle, smart-contract, gas, maximum-extractable-value, and stablecoin risks are part of the return source.
6. **Retail over-the-counter foreign exchange, contracts for difference, illiquid altcoins, subsecond cryptocurrency trading, news-release races, and generalized high-frequency market making** are not recommended as initial research or deployment domains.

The most important distinction is:

> The best market for discovering a robust economic edge is not necessarily the best market for building the first operational robot.

Therefore this report separates:

- **research priority**, where the evidence base and contract structure are strongest;
- **operational pilot priority**, where accessible APIs and data make live engineering possible;
- **eventual expansion priority**, where attractive mechanisms exist but complexity is high.

No final strategy is selected in Report 1.3. Final hypothesis admission occurs only after Reports 1.4 and 1.5.

---

## 2. Operator profile

All rankings are conditional on the following operator. Changing these assumptions can materially change the ranking.

### 2.1 Resources

The operator is assumed to have:

- strong software engineering and applied machine-learning capability;
- access to normal cloud or dedicated servers;
- no exchange colocation;
- no microwave or specialized low-latency network;
- no privileged broker or market-maker order flow;
- no proprietary bank, dealer, or hedge-fund position data;
- no exclusive news feed;
- limited but nontrivial research capital;
- capacity to maintain an always-on system;
- willingness to collect prospective data for months before meaningful capital deployment.

### 2.2 Capital profile

The target system is intended for small-to-moderate capital, not institutional scale. This has two opposite implications:

- the operator cannot exploit opportunities requiring large balance sheets or prime-broker relationships;
- the operator can exploit low-capacity opportunities that would be economically irrelevant to a large fund.

### 2.3 Risk constraints

The initial live system is assumed to require:

- no or minimal leverage;
- no dependence on continuous refinancing;
- no unlimited-loss option positions;
- no strategy whose apparent return comes primarily from rare liquidation or default exposure;
- bounded venue and stablecoin exposure;
- independent kill switches and reconciliation;
- a paper and shadow phase before real capital.

### 2.4 Geographic and account-access condition

Broker, exchange, instrument, tax, sanctions, residency, and know-your-customer eligibility are not assumed. Before implementation, every candidate venue must pass a separate live-access and legal-operability review.

A paper that demonstrates an opportunity on a market the operator cannot legally or reliably access does not create an implementable edge.

---

## 3. Research question

The report answers five linked questions:

1. **Where can an economic edge plausibly exist?**
2. **At what horizon can a non-colocated independent operator compete?**
3. **Which instruments express the mechanism with the least execution ambiguity?**
4. **How much data, capital, infrastructure, and operational complexity are required?**
5. **How rapidly should the opportunity decay as capital and competition enter?**

---

## 4. Evidence searches

### 4.1 Cross-market opportunity search

Scholar Gateway · For a small independent systematic trader without colocation, privileged order flow, or proprietary data, how does the peer-reviewed literature compare the realistic opportunity set across major liquid markets: equities, equity index futures, commodity futures, foreign exchange, government bond futures, listed options, cryptocurrency spot and perpetual futures, decentralized finance, and prediction markets? · 20 passages · 16 articles · 2015-05-12–2026-04-27

### 4.2 Medium-frequency strategy search

Scholar Gateway · Across liquid equities, equity-index futures, government-bond futures, commodity futures, and foreign-exchange markets, what peer-reviewed evidence identifies which systematic strategies remain economically meaningful for non-colocated traders at horizons from one hour to one month? · 20 passages · 16 articles · 2012-01-01–2026-03-09

### 4.3 Options and volatility search

Scholar Gateway · For a small independent systematic trader, what peer-reviewed evidence compares feasible edge opportunities in listed equity-index options, single-stock options, volatility futures, and cryptocurrency options? · 20 passages · 12 articles · 1987-07-01–2025-07-07

### 4.4 Cryptocurrency and decentralized-finance search

Scholar Gateway · For an independent systematic trader, what peer-reviewed evidence identifies feasible and infeasible edge opportunities in cryptocurrency spot, perpetual futures, dated futures, options, decentralized exchanges, automated market makers, lending protocols, liquid staking, and on-chain markets? · 20 passages · 12 articles · 2020-10-08–2026-02-18

The literature is uneven. Equities and traditional futures have long histories and mature data conventions. Cryptocurrency and decentralized-finance evidence is younger, more venue-specific, and more exposed to structural breaks. A larger number of papers does not necessarily imply a larger live opportunity.

---

## 5. Selection dimensions

A market–instrument–horizon combination is evaluated on ten dimensions.

| Dimension | Weight | Question |
|---|---:|---|
| Economic mechanism quality | 15 | Is there a defensible payer and persistence mechanism? |
| Independent evidence | 12 | Is the evidence replicated across samples, markets, or authors? |
| Point-in-time data feasibility | 10 | Can the historical information set be reconstructed honestly? |
| Execution observability | 10 | Can executable prices, fills, costs, and order states be modeled? |
| Low-speed feasibility | 13 | Can the edge survive without colocation or privileged feeds? |
| Cost and turnover tolerance | 10 | Is gross edge large enough relative to all-in costs? |
| Diversification opportunity | 8 | Can the mechanism be spread across independent bets? |
| Operational safety | 8 | Are custody, settlement, margin, and venue risks bounded? |
| Capital and capacity fit | 7 | Is the opportunity suitable for small-to-moderate capital? |
| Engineering ecosystem | 7 | Are reliable APIs, adapters, data formats, and runtime patterns available? |
| **Total** | **100** | |

The scores in this report are decision aids, not statistical estimates. They must not be interpreted as probabilities of profitability.

---

## 6. Horizon taxonomy

The same market can be attractive at one horizon and impossible at another.

### H0 — Subsecond

**Range:** microseconds to less than one second  
**Dominant edge:** latency, queue position, stale-quote detection, direct-feed interpretation, market making  
**Required infrastructure:** colocation, exchange-native feeds, kernel/network tuning, highly optimized execution, detailed order-book replay

**Independent-operator verdict:** Reject as an initial domain.

At these horizons, economic research is inseparable from physical infrastructure. A signal observed in public historical trades is not necessarily accessible before professional competitors act.

### H1 — Seconds to one minute

**Dominant edge:** order-flow prediction, liquidity state, short-term price discovery, news parsing, routing

**Independent-operator verdict:** Usually reject. Allow only as an execution-control layer, not the primary alpha thesis.

The operator may use second-level data to avoid toxic execution, but should not assume the ability to win a race against specialized participants.

### H2 — One minute to one hour

**Dominant edge:** intraday regime, order-flow persistence, short-lived relative value, event digestion, liquidity timing

**Independent-operator verdict:** Conditional.

This horizon may be feasible on less efficient or structurally fragmented venues, but requires high-quality trades, quotes, funding, and order-book data. Bar-only research is generally insufficient.

### H3 — One hour to one day

**Dominant edge:** derivatives state, funding and basis, cross-market spillover, volatility regime, selective momentum, liquidation state, execution-aware direction

**Independent-operator verdict:** Strong candidate, especially for liquid cryptocurrency markets and selected futures.

This is the shortest preferred alpha horizon for the initial system.

### H4 — One day to one month

**Dominant edge:** carry, trend, cross-sectional momentum, value, basis, hedging pressure, option surface, portfolio construction, risk timing

**Independent-operator verdict:** Highest general feasibility.

Costs are easier to absorb, the physical speed advantage is weaker, and cross-sectional diversification becomes practical.

### H5 — More than one month

**Dominant edge:** slow factors, structural carry, valuation, long-horizon option and macro signals

**Independent-operator verdict:** Feasible but statistically slow.

The main limitation is the number of independent observations. A ten-year backtest may contain only approximately 120 monthly decisions per asset, and far fewer independent regimes.

---

## 7. Universal horizon rule

For an independent operator:

> Prefer the slowest horizon that preserves the proposed economic mechanism and still produces enough independent decisions for validation.

Faster is not automatically better. A faster horizon creates:

- greater turnover;
- stronger dependence on exact timestamps;
- higher sensitivity to spread and latency;
- greater queue and partial-fill uncertainty;
- more correlated observations;
- greater infrastructure inequality;
- more opportunities for data leakage.

Moving from daily to minute data multiplies rows, but does not necessarily multiply independent economic information.

---

# 8. Market analysis

## 8.1 Diversified listed futures

### 8.1.1 Instruments

This family includes:

- equity-index futures;
- government-bond and interest-rate futures;
- commodity futures;
- currency futures;
- selected volatility futures.

### 8.1.2 Why futures are structurally attractive

Futures provide:

- standardized contracts;
- explicit expiry and settlement rules;
- relatively symmetric long and short implementation;
- central clearing in regulated markets;
- transparent margin schedules;
- liquid front contracts in major markets;
- natural cross-asset diversification;
- term structures that encode basis, carry, inventory, hedging, and funding information.

These properties make it easier to express the mechanisms identified in Report 1.2 without relying on hard-to-model stock borrow or custody of many underlying assets.

### 8.1.3 Documented mechanisms

The most credible candidate mechanisms are:

- time-series momentum and diversified trend;
- carry and term-structure information;
- basis momentum;
- hedging and speculative pressure;
- cross-sectional value and momentum;
- risk-management overlays;
- multi-market relative value.

Value and momentum have been documented across equities, stock indexes, currencies, government bonds, and commodities, with evidence of common risk and funding-liquidity exposure ([Asness, Moskowitz, and Pedersen, 2013](https://doi.org/10.1111/jofi.12021)). This supports a multi-asset portfolio thesis more than a claim that one indicator can predict one contract.

Speculative-pressure portfolios have shown lower turnover than momentum and carry in several futures classes and relatively high break-even transaction costs, although the premium is heterogeneous across asset classes and regimes ([Fan et al., 2019](https://doi.org/10.1002/fut.22085)).

Basis momentum has stronger evidence in commodities and currencies than in stock and bond indexes and appears connected to intermediary and liquidity constraints ([Boons and Prado, 2018](https://doi.org/10.1111/jofi.12738)).

### 8.1.4 Important negative evidence

The evidence is not uniformly favorable:

- simple single-market technical trend rules can decay after publication or structural change;
- volatility management that looks successful in sample may fail in real-time out-of-sample tests;
- factor momentum can be driven by a small subset of factors;
- high-turnover conditional strategies can lose their gross advantage to costs;
- trend-following can become crowded.

Individual-stock trend profitability largely disappeared after 2007 in one major study, while diversified futures evidence was more favorable ([Szakmary and Lancaster, 2015](https://doi.org/10.1111/fire.12065)).

Real-time commodity volatility management failed to reproduce its in-sample gains ([Kang and Kwon, 2020](https://doi.org/10.1002/fut.22175)).

Commodity factor momentum has recent international support, but transaction costs materially erode its practical value because of turnover ([Qian, Jiang, and Liu, 2025](https://doi.org/10.1002/fut.70022)).

### 8.1.5 Best horizon

- primary: daily to weekly;
- secondary: four-hour to daily for liquid contracts;
- avoid: subminute directional competition.

### 8.1.6 Data requirements

A serious futures dataset requires:

- individual contract histories, not only vendor continuous series;
- point-in-time contract specifications;
- roll and expiry calendars;
- settlement and last-trade rules;
- tick size and multiplier history;
- volume and open interest;
- bid/ask or quote data for realistic costs;
- margin schedules;
- session calendars and holidays;
- limit-up and limit-down rules;
- correct treatment of negative prices and exceptional settlements;
- currency conversion for cross-market portfolios.

### 8.1.7 Competition and capacity

Competition is high in front contracts, but medium-frequency risk premia are not purely speed races. Capacity is generally good for small capital, especially when diversified. The main risk is not immediate market impact; it is crowding, factor drawdown, leverage, and correlated deleveraging.

### 8.1.8 Independent-operator assessment

| Attribute | Assessment |
|---|---|
| Research quality | Very high |
| Data cost | Medium to high |
| Live access complexity | Medium |
| Short implementation | Strong |
| Speed dependence | Low at daily/weekly horizons |
| Operational risk | Medium |
| Diversification | Very high |
| First-live suitability | Medium |
| Long-term research priority | **Highest** |

### 8.1.9 Score

**84/100 — Tier A research market**

---

## 8.2 Liquid equity indexes and exchange-traded funds

### 8.2.1 Structural advantages

Liquid indexes and exchange-traded funds provide:

- clean directional exposure;
- high-quality regulated market data;
- straightforward cash positions;
- broad macro and factor representation;
- highly liquid instruments for risk overlays;
- transparent corporate index methodologies.

They are easier than individual equities but provide less cross-sectional information.

### 8.2.2 Candidate mechanisms

- medium-term trend and momentum;
- volatility and risk targeting;
- cross-index relative strength;
- macro-regime allocation;
- ETF versus futures relative value;
- execution and portfolio hedging.

### 8.2.3 Limitations

Major index products are highly efficient. Pure direction forecasting from past prices is a weak thesis. A better use is as:

- a portfolio benchmark;
- a liquid risk-control instrument;
- a component of cross-asset allocation;
- a hedge for other strategies.

### 8.2.4 Best horizon

Daily to monthly. Intraday macro announcements are dominated by speed and spread expansion.

### 8.2.5 Score

**71/100 — Tier B primary instrument and benchmark**

---

## 8.3 Individual equities

### 8.3.1 Structural advantages

Individual equities offer the richest cross-section:

- thousands of instruments;
- accounting and corporate-event data;
- analyst and ownership information;
- options-derived information;
- sector and supply-chain relationships;
- persistent heterogeneity in attention, liquidity, and constraints.

A cross-sectional question is often statistically easier than predicting the sign of one index:

> Which securities should outperform peers under a fixed market exposure?

### 8.3.2 Candidate mechanisms

- value, quality, investment, profitability, momentum, and low-risk factors;
- post-event drift and slow information diffusion;
- cross-sectional option-implied information;
- supply-chain and network lead-lag effects;
- short-term reversal in liquid names;
- portfolio and tax-aware execution.

### 8.3.3 Data hazards

Equity research is highly vulnerable to:

- survivorship bias;
- delisting bias;
- point-in-time constituent errors;
- revised fundamentals;
- announcement-date versus period-end confusion;
- stock splits and dividends;
- merger and spin-off treatment;
- stale securities;
- historical borrow availability;
- short-sale fees and recalls;
- opening and closing auction assumptions.

A clean equity dataset is substantially harder than downloading adjusted closing prices.

### 8.3.4 Competition and capacity

Cross-sectional factors are crowded and widely published. However, small capital can operate in narrower capacity niches. The danger is mistaking small-cap illiquidity and unmodeled borrow costs for alpha.

### 8.3.5 Best horizon

- daily to monthly for factors and event drift;
- avoid subminute competition;
- use the most liquid point-in-time universe for initial replication.

### 8.3.6 Score

**74/100 — Tier A/B research market**

This score assumes access to point-in-time data and realistic borrow information. Without those, the score falls materially.

---

## 8.4 Foreign exchange

Foreign exchange must be divided into two distinct environments.

### 8.4.1 Currency futures and institutional forwards

Candidate mechanisms include:

- carry;
- value;
- momentum;
- basis and funding effects;
- macro and risk-regime behavior;
- cross-sectional currency portfolios.

The evidence base is broad, and futures provide central execution and standardized contracts.

**Preferred horizon:** daily to monthly.  
**Assessment:** attractive as part of a diversified futures program.

### 8.4.2 Retail spot foreign exchange and contracts for difference

The retail environment is materially less attractive because:

- execution is broker-specific;
- the market is decentralized;
- there is no single complete tape;
- spreads and financing differ by broker and account;
- the broker may be principal or internalizer;
- historical bid/ask data may not match live execution;
- rollover and financing can dominate small edges;
- legal and account access vary substantially.

A backtest on an aggregated mid-price feed cannot prove an edge at a specific retail broker.

### 8.4.3 Scores

- **Currency futures / robust institutional-style feed: 75/100**
- **Retail spot FX / CFD: 48/100**

The project should not start with retail OTC execution unless venue-specific data and fills are available prospectively.

---

## 8.5 Government-bond and interest-rate futures

### 8.5.1 Candidate mechanisms

- macro regime and yield-curve dynamics;
- carry and roll-down;
- cross-maturity relative value;
- trend;
- event and policy response;
- hedging pressure and intermediary constraints.

### 8.5.2 Strengths

- deep institutional markets;
- standardized central clearing;
- strong macroeconomic interpretation;
- useful diversification versus equities and commodities.

### 8.5.3 Barriers

- high efficiency;
- contract and cheapest-to-deliver mechanics;
- delivery-option complexity;
- sensitivity to scheduled announcements;
- institutional competition in curve and basis trades;
- substantial leverage embedded in duration exposure.

### 8.5.4 Best horizon

Daily to monthly for independent research. Subsecond and announcement-release trading are rejected.

### 8.5.5 Score

**70/100 — Tier B diversification market**

The market is valuable in a multi-asset portfolio, but it is not the easiest first standalone edge domain.

---

## 8.6 Commodity futures

### 8.6.1 Why commodities are distinct

Commodity futures represent physical-production and inventory economics. Their term structures can reflect:

- inventory scarcity;
- convenience yield;
- storage and financing;
- producer hedging;
- consumer hedging;
- speculative capital;
- seasonal supply and demand;
- weather and geopolitical shocks.

This creates stronger economic mechanisms than a price-only thesis.

### 8.6.2 Candidate mechanisms

- carry and basis;
- basis momentum;
- cross-sectional momentum;
- hedging and speculative pressure;
- seasonality with point-in-time safeguards;
- curve-relative value;
- risk-control overlays.

### 8.6.3 Important cautions

- continuous futures construction can manufacture returns;
- delivery and roll details matter;
- liquidity is concentrated by maturity;
- some contracts have seasonal or “zombie” maturities;
- fundamental inventory data can be revised or delayed;
- single-commodity signals have low statistical power;
- event information is incorporated rapidly;
- crowding can weaken trend returns.

Recent work shows that liquidity-aware maturity selection is essential when researching curve momentum, and that results do not automatically transfer between countries with different participant and liquidity structures ([Zheng et al., 2026](https://doi.org/10.1002/fut.70093)).

### 8.6.4 Best horizon

Daily to monthly, implemented as a diversified portfolio rather than a single commodity bot.

### 8.6.5 Score

**82/100 — Tier A research market**

---

## 8.7 Listed options and volatility products

### 8.7.1 Why options are attractive

Options reveal and transfer risks not directly visible in the underlying:

- expected volatility;
- variance risk premium;
- skew and crash insurance;
- term structure;
- investor demand for leverage and protection;
- informed trading;
- event uncertainty.

### 8.7.2 Candidate mechanisms

- volatility risk premium;
- option momentum;
- implied-versus-realized volatility;
- term-structure and surface relative value;
- cross-sectional implied-volatility mispricing;
- dispersion;
- event volatility;
- option-to-stock information transmission.

Option momentum has been documented at horizons of months rather than milliseconds, including robustness to delta hedging and alternative option sets ([Heston et al., 2023](https://doi.org/10.1111/jofi.13279)). Long-term implied-volatility surface components may contain information about subsequent stock returns ([Kim, Kim, and Park, 2019](https://doi.org/10.1002/fut.22070)).

### 8.7.3 Why options are dangerous for naive research

Option prices are extremely noisy. Research must account for:

- large relative bid/ask spreads;
- stale and crossed quotes;
- zero bids;
- discrete strikes and maturities;
- early exercise for American options;
- dividends and borrow;
- assignment;
- settlement style;
- volatility-surface interpolation;
- delta and vega hedging;
- discrete hedging error;
- jump risk;
- portfolio margin;
- short-option tail losses;
- liquidity selection bias.

Bias-corrected option research can materially change conclusions about volatility risk premia ([Duarte, Jones, and Wang, 2024](https://doi.org/10.1111/jofi.13365)). Midpoint returns are not sufficient evidence.

### 8.7.4 Competition and capacity

Market-making and intraday volatility arbitrage are institutionally competitive. Cross-sectional and monthly strategies may be feasible for small capital, but require broad data and many simultaneous positions.

### 8.7.5 Best horizon

- daily to monthly;
- avoid intraday market making as the first system;
- use defined-risk structures in early live testing;
- treat systematic short volatility as a risk premium, not unexplained alpha.

### 8.7.6 Score

**64/100 — Tier B research expansion, Tier C first-live market**

Options should enter only after the base data, execution, risk, and portfolio systems are mature.

---

## 8.8 Cryptocurrency spot markets

### 8.8.1 Advantages

- programmatic exchange APIs;
- 24/7 operation;
- free or low-cost public data;
- fractional sizing;
- transparent balances on many venues;
- high volatility and regime variation;
- multi-venue fragmentation;
- direct path from research to paper and live systems.

Bitcoin has demonstrated investable spreads and depth at major venues, but liquidity and resilience vary by exchange and asset ([Aleti and Mizrach, 2020](https://doi.org/10.1002/fut.22163)).

### 8.8.2 Candidate mechanisms

- cross-sectional factor and relative-strength portfolios;
- medium-frequency trend and reversal;
- volatility and liquidity regimes;
- spot–derivatives state;
- cross-venue price and liquidity information;
- on-chain and exchange-flow state;
- execution and venue selection.

### 8.8.3 Risks

- exchange default and custody;
- fragmented prices;
- stablecoin denomination;
- wash trading and volume quality;
- API outages and rate limits;
- 24/7 operational burden;
- deposit and withdrawal interruptions;
- inconsistent symbol and contract histories;
- forks and token migrations;
- delistings;
- regulation and account eligibility.

### 8.8.4 Competition

The most liquid assets are increasingly efficient. Very short horizons are dominated by algorithmic participants. Less liquid assets appear more predictable but have higher manipulation, delisting, spread, and impact risk.

### 8.8.5 Best horizon

One hour to several days. Four-hour and daily bars may be useful for an initial system, but bars must be augmented by real quote, fee, funding, and latency observations before live promotion.

### 8.8.6 Score

**73/100 — Tier A/B operational pilot market**

---

## 8.9 Cryptocurrency perpetual futures

### 8.9.1 Structural advantages

Perpetual futures provide:

- simple long and short access;
- no expiry roll;
- high liquidity in major assets;
- explicit funding payments;
- direct observation of leverage demand;
- mark and index prices;
- open interest and liquidation state.

### 8.9.2 Candidate mechanisms

- funding and basis risk premia;
- cross-venue funding dispersion;
- spot–perpetual relative value;
- open-interest and liquidation regimes;
- cross-sectional carry and momentum;
- volatility and crowding filters;
- event-risk abstention.

### 8.9.3 Critical risks

The apparent simplicity hides major risks:

- leverage and liquidation;
- mark-price rules;
- maintenance-margin tiers;
- insurance-fund sufficiency;
- auto-deleveraging;
- funding sign and interval changes;
- stablecoin settlement;
- exchange counterparty risk;
- index composition and nontraded settlement inputs;
- forced closures and venue-specific rules.

Perpetual contracts transfer some extreme losses from exchanges to traders through insurance and auto-deleveraging mechanisms. These must be modeled as contract risk, not treated as rare operational noise.

### 8.9.4 Speed boundary

Subsecond perpetual price discovery is strongly algorithmic. Recent evidence identifies deterministic subsecond trade clustering and major price discovery during proprietary-algorithm activity ([Shynkevich, 2026](https://doi.org/10.1002/fut.70089)). This makes subsecond strategies inappropriate for the target operator.

### 8.9.5 Best horizon

One hour to several days. Funding-interval and daily horizons are especially relevant. The first live version should use no or minimal leverage.

### 8.9.6 Score

**78/100 — Tier A operational research market, conditional on venue safety**

This is the highest operational-pilot score, not the strongest proof that a profitable edge exists.

---

## 8.10 Dated cryptocurrency futures and crypto carry

### 8.10.1 Candidate mechanisms

- cash-and-carry;
- term-structure carry;
- basis convergence;
- calendar spreads;
- dislocation during funding stress.

### 8.10.2 Advantages

The convergence date creates a clearer terminal relation than a perpetual contract. Relative-value hypotheses are economically interpretable.

### 8.10.3 Risks

- capital tied in spot and futures legs;
- exchange and custody risk;
- legging risk;
- transfer delays;
- margin calls before convergence;
- settlement-index risk;
- basis widening during stress;
- short availability and collateral denomination.

### 8.10.4 Best horizon

Days to months.

### 8.10.5 Score

**72/100 — Tier B relative-value market**

---

## 8.11 Cryptocurrency options

Crypto options add:

- volatility and skew information;
- event and crash-risk pricing;
- term-structure strategies;
- portfolio hedging;
- defined-risk directional trades.

But the market is concentrated, products may be inverse or stablecoin-settled, and settlement relies on fragmented indexes. These features create market incompleteness and basis risk ([Alexander, Chen, and Imeraj, 2023](https://doi.org/10.1111/mafi.12410)).

### Best horizon

Daily to monthly.

### Score

**56/100 — Tier C initial market, possible later expansion**

The evidence and engineering ecosystem are less mature than traditional listed options.

---

## 8.12 Decentralized exchanges and automated market makers

### 8.12.1 Candidate mechanisms

- CEX–DEX price convergence;
- pool rebalancing and arbitrage;
- concentrated-liquidity management;
- fee-tier selection;
- stable-pair dislocation;
- liquidity provision conditioned on volatility and flow;
- on-chain event and flow information.

### 8.12.2 Why apparent yield is not edge

Liquidity providers earn fees but may lose through:

- adverse selection;
- impermanent loss or loss-versus-rebalancing;
- toxic flow;
- gas costs;
- maximum extractable value;
- oracle manipulation;
- smart-contract failure;
- bridge failure;
- token and stablecoin collapse.

The yield is often compensation for these risks.

### 8.12.3 Market efficiency

Uniswap v3 has improved price discovery relative to earlier automated-market-maker designs, but informed participants may migrate to centralized exchanges during volatility and cross-venue arbitrage becomes more important ([Alexander et al., 2025](https://doi.org/10.1002/fut.22593)).

### 8.12.4 Competition

On-chain arbitrage at the block and transaction-ordering level is dominated by specialized searchers, builders, validators, private order flow, and sophisticated transaction simulation. A normal public transaction is structurally disadvantaged in maximum-extractable-value competition.

### 8.12.5 Best horizon

Hours to weeks for slow liquidity allocation and protocol-relative value. Reject transaction-level or same-block arbitrage for the initial system.

### 8.12.6 Score

**48/100 — Tier C experimental research market**

---

## 8.13 Liquid staking, lending, and protocol-relative value

### 8.13.1 Candidate mechanisms

- liquid-staking-token versus underlying basis;
- staking-yield differentials;
- lending-rate dispersion;
- collateral demand;
- protocol incentives;
- redemption and withdrawal constraints;
- risk-adjusted yield allocation.

Liquid-staking bases vary with reward differences, concentration risk, liquidity, forced liquidations, attention, and sentiment ([Scharnowski and Jahanshahloo, 2024](https://doi.org/10.1002/fut.22556)). This is an economically meaningful hypothesis family.

### 8.13.2 Risks

- validator and slashing risk;
- protocol concentration;
- delayed redemption;
- smart contracts;
- oracle risk;
- governance attack;
- collateral liquidation;
- stablecoin and bridge risk;
- uncertain tax and legal treatment.

Stablecoin systems can enter endogenous deleveraging spirals in which collateral losses and the stablecoin price reinforce each other ([Klages-Mundt and Minca, 2022](https://doi.org/10.1111/mafi.12357)).

### 8.13.3 Best horizon

Days to months.

### 8.13.4 Score

**57/100 — Tier B/C specialized relative-value research**

Potentially valuable for small capital, but only after protocol-risk modeling and wallet-security architecture exist.

---

## 8.14 Prediction and betting markets

Prediction markets can offer:

- bounded payouts;
- event-specific information aggregation;
- cross-market probability comparison;
- semantic and polling information;
- potentially low-capacity niches.

However:

- legal access is jurisdiction-specific;
- market resolution and oracle rules are central;
- liquidity can be thin;
- events are heterogeneous and nonstationary;
- historical datasets are short;
- the outcome definition can dominate model quality;
- capacity is often low.

The existence of production adapters, such as a Polymarket integration in general-purpose trading engines, proves engineering feasibility, not the existence of an edge.

### Best horizon

Hours to months, dependent on event structure.

### Score

**45/100 — Watchlist only**

It should not displace the more mature initial research domains.

---

# 9. Competition map

## 9.1 Competition types

Competition is not one variable. It has at least six forms:

1. **speed competition** — who observes and acts first;
2. **data competition** — who has cleaner, deeper, or earlier data;
3. **model competition** — who extracts a more accurate conditional distribution;
4. **capital competition** — who can finance and hold convergence trades;
5. **execution competition** — who obtains better queues, routing, fees, and fills;
6. **governance and operational competition** — who survives outages, legal constraints, and extreme states.

### 9.1.1 Independent comparative advantages

An independent operator may have advantages in:

- willingness to pursue small-capacity ideas;
- lower organizational latency;
- narrow specialization;
- ability to abstain for long periods;
- no need to deploy large capital;
- flexible research and engineering stack;
- tolerance for modest absolute profits.

The operator does not have a plausible advantage in:

- direct-feed latency;
- colocation;
- generalized market making in the most liquid instruments;
- prime-broker financing;
- privileged retail or institutional flow;
- same-block maximum-extractable-value search;
- large multi-leg options books requiring institutional margin.

---

# 10. Capacity map

## 10.1 Capacity is mechanism-specific

A strategy's capacity depends on:

- average daily volume;
- spread and depth;
- holding horizon;
- turnover;
- concentration;
- participation rate;
- number of independent instruments;
- crowding by similar strategies;
- funding and margin requirements.

### 10.1.1 Low-capacity opportunities

Potentially suitable for small operators:

- niche cross-sectional crypto portfolios;
- selected slow cross-venue dislocations;
- specialized protocol-relative value;
- small options portfolios in liquid contracts;
- less-followed futures contracts with adequate liquidity;
- execution savings on the operator's own orders.

### 10.1.2 High-capacity opportunities

- major index futures trend and allocation;
- major currency futures;
- broad liquid equity factors;
- diversified commodity futures;
- major crypto spot/perpetual portfolios.

These are accessible but heavily researched and competitive.

### 10.1.3 False capacity

Reported volume is not capacity when:

- volume is wash trading;
- depth disappears under stress;
- fills occur only at a small quote size;
- the strategy requires simultaneous legs;
- collateral cannot be transferred in time;
- borrow disappears;
- the venue rejects or rate-limits orders;
- the strategy is crowded and participants exit together.

---

# 11. Market × edge-mechanism matrix

Legend: **H** high relevance, **M** medium, **L** low, **X** generally unsuitable for the target operator.

| Market | Risk premia / carry | Behavioral | Information | Relative value | Liquidity provision | Execution | Risk / abstention |
|---|---:|---:|---:|---:|---:|---:|---:|
| Diversified listed futures | H | M | M | H | M | H | H |
| Equity indexes / ETFs | M | L | M | M | L | H | H |
| Individual equities | H | H | H | M | M | H | H |
| Currency futures | H | M | M | H | M | H | H |
| Retail spot FX / CFD | M | L | L | L | X | M | M |
| Government-bond futures | H | L | H | H | M | H | H |
| Commodity futures | H | H | H | H | M | H | H |
| Listed options | H | H | H | H | M | H | H |
| Crypto spot | M | H | H | H | M | H | H |
| Crypto perpetuals | H | H | H | H | M | H | H |
| Dated crypto futures | H | M | M | H | L | H | H |
| Crypto options | H | H | H | H | L | H | H |
| DEX / AMM | H | M | H | H | H | H | H |
| Liquid staking / lending | H | M | H | H | L | M | H |
| Prediction markets | M | H | H | M | L | M | H |

This table maps research relevance, not expected profitability.

---

# 12. Market × horizon matrix

| Market | <1s | 1s–1m | 1m–1h | 1h–1d | 1d–1m | >1m |
|---|---:|---:|---:|---:|---:|---:|
| Listed futures | X | X | M | H | H | M |
| Equities / ETFs | X | X | M | M | H | H |
| Retail spot FX | X | X | L | M | M | M |
| Listed options | X | X | L | M | H | H |
| Crypto spot | X | L | M | H | H | M |
| Crypto perpetuals | X | L | M | H | H | M |
| DEX / AMM | X | X | L | M | H | H |
| Staking / lending | X | X | X | L | H | H |
| Prediction markets | X | X | L | M | H | H |

**Primary independent-operator sweet spot:** H3 and H4.

---

# 13. Engineering ecosystem review

Open-source systems demonstrate that multi-market research and live execution are technically possible, but framework support is not evidence of profitability.

## 13.1 Event-driven multi-asset engines

NautilusTrader describes a common event-driven architecture for research, deterministic simulation, and live execution, with identical time and execution semantics. It supports modular adapters for cryptocurrency exchanges, traditional foreign exchange, equities, futures, options, decentralized exchanges, and selected prediction or betting markets.

The relevant engineering principle is:

> Market choice should not force a different definition of time, order state, fill, accounting, or risk between research and live execution.

## 13.2 Crypto-specific bot frameworks

Freqtrade demonstrates that retail-accessible cryptocurrency spot and futures connectivity, persistence, dry run, backtesting, look-ahead analysis, and operational controls can be packaged into a usable system.

The relevant lesson is not to adopt all framework assumptions. It is that the initial live cryptocurrency pilot has a mature engineering ecosystem, which raises its operational-pilot ranking.

## 13.3 Broad brokerage engines

Broad engines such as LEAN demonstrate that one research and runtime abstraction can cover equities, options, futures, foreign exchange, and cryptocurrency. The project should preserve multi-asset domain models even if the first adapter supports only one venue.

## 13.4 Architectural consequence

The future runtime should model at least:

- `InstrumentId` independent of symbol text;
- venue and account as explicit dimensions;
- cash, spot, future, perpetual, option, and tokenized claims as different instrument types;
- contract multiplier, tick size, lot size, settlement currency, margin, and expiry;
- market calendars and 24/7 venues;
- normalized quotes, trades, bars, order books, funding, and corporate or protocol events;
- a common order and fill state machine;
- venue-specific risk overlays;
- portfolio-level exposure across venues and currencies.

Choosing cryptocurrency first must not hard-code the entire system as a single-symbol candle bot.

---

# 14. Scored ranking

| Rank | Market–instrument–horizon | Score | Research role | Operational role |
|---:|---|---:|---|---|
| 1 | Diversified listed futures, daily–weekly | 84 | Primary | Later live expansion |
| 2 | Commodity futures portfolio, daily–monthly | 82 | Primary structural-premia laboratory | Later live expansion |
| 3 | Liquid crypto perpetuals, hourly–daily | 78 | Primary accessible derivatives laboratory | First pilot candidate |
| 4 | Currency futures, daily–monthly | 75 | Multi-asset component | Later live expansion |
| 5 | Liquid individual equities, daily–monthly | 74 | Primary cross-sectional laboratory | Possible second adapter |
| 6 | Liquid crypto spot, hourly–daily | 73 | Accessible baseline and cross-section | First pilot candidate |
| 7 | Dated crypto futures, days–months | 72 | Relative-value candidate | Controlled later pilot |
| 8 | Equity indexes / ETFs, daily–monthly | 71 | Baseline, hedge, allocation | Strong risk-control instrument |
| 9 | Government-bond futures, daily–monthly | 70 | Diversifier and macro laboratory | Later expansion |
| 10 | Listed options, daily–monthly | 64 | High-potential advanced research | Not first live market |
| 11 | Liquid staking / lending, days–months | 57 | Specialized structural research | Experimental only |
| 12 | Crypto options, daily–monthly | 56 | Advanced crypto research | Experimental only |
| 13 | Retail spot FX / CFD, hourly–monthly | 48 | Venue-specific only | Generally avoid |
| 14 | DEX / AMM, hours–weeks | 48 | Specialized protocol research | Not first runtime |
| 15 | Prediction markets, hours–months | 45 | Watchlist | No initial deployment |
| 16 | Illiquid altcoins, any short horizon | 28 | Bias and manipulation risk | Reject initially |
| 17 | Generalized HFT / latency arbitrage | 18 | Infrastructure study only | Reject |
| 18 | Same-block DEX arbitrage / MEV race | 12 | Specialized institutional domain | Reject |

---

# 15. Recommended research architecture

The evidence supports a two-track architecture.

## Track A — Generalizable economic-edge research

Build hypotheses that can be tested across:

- liquid traditional futures;
- liquid cryptocurrency spot and perpetuals;
- later, equities and options.

Prioritize mechanisms that transfer across markets:

- carry and basis;
- trend and momentum;
- volatility and liquidity regime;
- crowding and positioning;
- selective abstention;
- execution and cost control.

A mechanism that works only on one exchange and one period receives lower prior credibility than one that appears across economically related markets.

## Track B — Operational runtime development

Use one highly accessible liquid cryptocurrency spot or perpetual venue to build:

- market-data ingestion;
- event-time and receive-time handling;
- order management;
- paper fills;
- reconciliation;
- state recovery;
- risk limits;
- monitoring;
- kill switches.

The runtime pilot does not imply that cryptocurrency direction is the final alpha thesis.

---

# 16. Provisional admission decisions

These are inputs to Reports 1.4 and 1.5, not final promotions.

## Admit for deeper falsification design

1. Multi-asset futures trend, carry, basis, and positioning mechanisms.
2. Medium-frequency crypto funding, basis, open-interest, liquidation, and cross-sectional mechanisms.
3. Volatility and risk-regime forecasting as an exposure and abstention layer.
4. Cost-aware portfolio construction and no-trade regions.
5. Equity cross-sectional and event-information mechanisms using point-in-time liquid universes.
6. Monthly option momentum and volatility-surface mechanisms after a full options data audit.
7. Slow protocol-relative-value hypotheses such as liquid-staking basis, only with explicit smart-contract and liquidity risk.

## Place on watchlist

1. Prediction-market semantic information.
2. DEX liquidity allocation.
3. Crypto option sentiment and skew.
4. macro-announcement strategies at non-racing horizons.
5. less-followed but adequately liquid commodity contracts.

## Reject as initial domains

1. Subsecond and generalized high-frequency trading.
2. News-release latency races.
3. Same-block decentralized-finance arbitrage.
4. Retail contracts-for-difference strategies using generic aggregated prices.
5. Illiquid-altcoin technical trading.
6. Naked short-option income strategies.
7. Any strategy requiring unmodeled leverage or continuous refinancing.

---

# 17. Falsification requirements created by market choice

Each admitted market imposes additional tests.

## 17.1 Listed futures

- reconstruct actual contracts and rolls;
- test multiple roll rules;
- use delayed execution;
- include margin and currency conversion;
- exclude illiquid maturities point in time;
- test cross-market diversification and crowding.

## 17.2 Equities

- include delisted securities;
- use announcement and filing availability dates;
- model borrow and recalls;
- reconstruct point-in-time universes;
- use corporate actions and executable auctions.

## 17.3 Cryptocurrency centralized exchanges

- use venue-specific trades and quotes;
- preserve receive timestamps;
- model outages, rate limits, and rejected orders;
- stress stablecoin and venue failure;
- use real funding, mark, and liquidation rules;
- test cross-venue transfer and withdrawal constraints.

## 17.4 Options

- use bid and ask, not only midpoint;
- construct valid surfaces without future information;
- include exercise, assignment, dividends, and hedging;
- stress jumps and volatility-of-volatility;
- calculate portfolio margin and tail loss;
- reject results dependent on zero-bid or stale contracts.

## 17.5 Decentralized finance

- simulate gas and failed transactions;
- model block inclusion and transaction ordering;
- include smart-contract, oracle, bridge, and governance failure;
- compare liquidity-provider returns with passive rebalancing;
- include loss-versus-rebalancing and adverse selection;
- separate token incentives from sustainable economic yield.

---

# 18. Implementation consequences

Report 1.3 establishes the following design requirements for the future codebase:

1. **The domain model must remain multi-asset and multi-venue.**
2. **The first live adapter may be cryptocurrency-specific, but strategy interfaces must not be.**
3. **Market data must support both 24/7 and session-based venues.**
4. **Instrument metadata must be time-varying and versioned.**
5. **Spot, perpetual, dated future, and option accounting must be distinct.**
6. **Portfolio risk must be expressed in a common base currency.**
7. **The simulator must support latency, bid/ask, partial fills, rejected orders, and funding.**
8. **Traditional futures research requires a contract-chain and roll subsystem.**
9. **Equity research requires a point-in-time security master.**
10. **Options research requires a surface and Greeks subsystem.**
11. **DeFi research requires block, transaction, gas, and protocol-state semantics.**
12. **No single market adapter is allowed to determine the core architecture.**

---

# 19. What this report does not conclude

This report does not claim that:

- listed futures are currently profitable;
- cryptocurrency markets necessarily contain a usable edge;
- an hourly strategy is better than a daily one;
- options are too difficult forever;
- decentralized finance is inherently unsafe;
- a high-scoring market should automatically be traded.

The scores estimate research and implementation suitability under the stated operator profile. Actual edge must still pass the proof standard in Report 1.1.

---

# 20. Final conclusion

The central conclusion is:

> The target operator should not compete on speed. It should compete on mechanism selection, data integrity, portfolio construction, abstention, execution discipline, and the ability to operate small-capacity ideas that are too small or inconvenient for large institutions.

The highest-quality long-run research path is a **diversified, medium-frequency, multi-asset program**, especially listed futures, with explicit carry, basis, positioning, trend, volatility, and risk-control hypotheses.

The most practical first runtime path is a **liquid cryptocurrency spot/perpetual pilot at hourly-to-daily horizons**, using minimal leverage and treating venue, funding, stablecoin, liquidation, and 24/7 operations as first-class risks.

Options and decentralized-finance mechanisms remain valuable expansion domains, but they should not be allowed to multiply complexity before the basic research, execution, accounting, and risk infrastructure is proven.

---

# 21. Reference anchors

- Alexander, C., Chen, D., and Imeraj, A. (2023). Crypto quanto and inverse options. *Mathematical Finance*. https://doi.org/10.1111/mafi.12410
- Alexander, C., Chen, X., Deng, J., and Fu, Q. (2025). Price discovery and efficiency in Uniswap liquidity pools. *Journal of Futures Markets*. https://doi.org/10.1002/fut.22593
- Aleti, S., and Mizrach, B. (2020). Bitcoin spot and futures market microstructure. *Journal of Futures Markets*. https://doi.org/10.1002/fut.22163
- Asness, C. S., Moskowitz, T. J., and Pedersen, L. H. (2013). Value and momentum everywhere. *Journal of Finance*. https://doi.org/10.1111/jofi.12021
- Boons, M., and Prado, M. P. (2018). Basis-momentum. *Journal of Finance*. https://doi.org/10.1111/jofi.12738
- Duarte, J., Jones, C. S., and Wang, J. L. (2024). Very noisy option prices and inference regarding the volatility risk premium. *Journal of Finance*. https://doi.org/10.1111/jofi.13365
- Fan, J. H., Fernandez-Perez, A., Fuertes, A., and Miffre, J. (2019). Speculative pressure. *Journal of Futures Markets*. https://doi.org/10.1002/fut.22085
- Heston, S. L., Jones, C. S., Khorram, M., Li, S., and Mo, H. (2023). Option momentum. *Journal of Finance*. https://doi.org/10.1111/jofi.13279
- Kang, J., and Kwon, K. Y. (2020). Volatility-managed commodity futures portfolios. *Journal of Futures Markets*. https://doi.org/10.1002/fut.22175
- Kim, B., Kim, D., and Park, H. (2019). Informed options trading on the implied volatility surface. *Journal of Futures Markets*. https://doi.org/10.1002/fut.22070
- Klages-Mundt, A., and Minca, A. (2022). While stability lasts: A stochastic model of noncustodial stablecoins. *Mathematical Finance*. https://doi.org/10.1111/mafi.12357
- Qian, Y., Jiang, Y., and Liu, X. (2025). Factor momentum in commodity futures markets. *Journal of Futures Markets*. https://doi.org/10.1002/fut.70022
- Scharnowski, S., and Jahanshahloo, H. (2024). The economics of liquid staking derivatives. *Journal of Futures Markets*. https://doi.org/10.1002/fut.22556
- Shynkevich, A. (2026). Trading periodicity and algorithmic divide in cryptocurrency markets. *Journal of Futures Markets*. https://doi.org/10.1002/fut.70089
- Szakmary, A. C., and Lancaster, M. C. (2015). Trend-following trading strategies in U.S. stocks: A revisit. *Financial Review*. https://doi.org/10.1111/fire.12065
- Zheng, Z., Liu, Y., Wu, Y., and Chen, R. (2026). Curve momentum in China. *Journal of Futures Markets*. https://doi.org/10.1002/fut.70093

---

Results retrieved by Scholar Gateway. AI-assisted synthesis must be verified against the source papers during Report 2 replication. Corpus freshness: May 2026.
