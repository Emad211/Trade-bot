# Report 1.1 — Definition of a Genuine Trading Edge and Its Proof Standard

**Program:** Edge Discovery Research Program  
**Section:** 1 — Edge Map  
**Report:** 1 of 5  
**Version:** 1.0  
**Research freeze date:** 2026-07-18  
**Status:** Complete  
**Decision type:** Foundational and binding for all later reports

---

## Executive conclusion

A trading edge is not prediction accuracy, statistical significance, a profitable chart, or the best result selected from a large model search. A genuine edge is an economically explainable, implementable, capacity-aware advantage over the strongest feasible benchmark that remains positive after all relevant costs and risks, survives correction for research selection, and is confirmed on information that did not exist when the strategy was designed.

This program will therefore use the term **candidate edge** for every historical result. The term **operationally demonstrated edge** is reserved for a strategy that has survived prospective data collection, realistic paper execution, and a controlled deployment with minimal real capital using the same decision and execution semantics.

Historical backtests can reject a hypothesis and can justify prospective testing. They cannot, by themselves, prove that a live edge exists.

---

## 1. Purpose and scope

This report answers one question:

> What is allowed to be called a trading edge, and what evidence is required to distinguish it from statistical luck, hidden risk exposure, market beta, and unrealistic execution assumptions?

This report deliberately does **not** choose:

- an asset class;
- a cryptocurrency or traditional market;
- spot, futures, options, decentralized finance, or another instrument;
- a directional, relative-value, market-making, execution, or portfolio strategy;
- a data frequency or holding horizon;
- a statistical, machine-learning, deep-learning, reinforcement-learning, or language-model architecture.

Those decisions must be made only after the proof standard is fixed. Otherwise, the standard will be unconsciously adjusted to favor whatever result is discovered.

---

## 2. Formal definition of edge

For a strategy or policy \(\pi\), benchmark \(b\), decision time \(t\), investment horizon \(H\), deployable capital \(q\), and the information set actually available at the decision time \(I_t\), define:

\[
\operatorname{Edge}_t(\pi,H,q)
=
\mathbb{E}
\left[
U\left(R^{net}_{\pi,t:t+H}\right)
-
U\left(R^{net}_{b,t:t+H}\right)
\mid I_t
\right]
\]

where:

- \(R^{net}\) is the return after realistic trading, financing, execution, and operational costs;
- \(U\) is an economic utility or value function that captures more than average return;
- \(b\) is the strongest practical alternative available to the same investor;
- \(q\) is included because many opportunities decay as capital and market impact increase;
- \(I_t\) contains only information that was truly observable and usable at time \(t\).

A candidate may be considered a genuine edge only if the lower-confidence estimate of this value is positive under the intended operating conditions.

### 2.1 Net return contract

At a minimum:

\[
R^{net}
=
R^{gross}
-C_{fee}
-C_{spread}
-C_{slippage}
-C_{impact}
-C_{funding}
-C_{borrow}
-C_{latency}
-C_{failed\ execution}
-C_{operational}
\]

Depending on the strategy, the cost and loss model may also include:

- conversion and transfer costs;
- withdrawal delays or restrictions;
- rollover and settlement effects;
- stablecoin basis and depeg risk;
- custody and counterparty losses;
- liquidation, insurance-fund, and auto-deleveraging effects;
- queue position and non-fill risk;
- stale quotes and rejected orders;
- tax and legal constraints where relevant;
- opportunity cost of locked or idle capital.

A gross anomaly is not an edge when its magnitude lies inside the realistic no-arbitrage band created by costs and risks.

---

## 3. Five levels that must not be confused

### Level 1 — Predictive relationship

A variable is statistically related to a future outcome. Examples include:

- accuracy above 50%;
- area under the receiver operating characteristic curve above 0.5;
- lower mean squared error;
- a statistically significant regression coefficient;
- Granger causality;
- correlation with future returns, volatility, volume, or liquidity.

This is a research observation, not a trading edge.

### Level 2 — Gross trading advantage

The prediction is converted into a trading rule and earns positive simulated profit before all realistic costs and execution constraints.

This remains insufficient because spread, turnover, latency, slippage, funding, non-fills, and capacity may consume the apparent advantage.

### Level 3 — Implementable net candidate edge

The strategy earns a positive net advantage over a suitable benchmark using executable prices, realistic costs, and an operationally possible trading rule.

This is the first level that may be called a **candidate edge**.

### Level 4 — Robust and capacity-aware candidate edge

The result is not dependent on a precise parameter, one asset, one venue, one favorable regime, or a handful of trades. It survives:

- parameter perturbation;
- delayed execution;
- cost stress;
- alternative start dates;
- multiple temporal folds;
- relevant market regimes;
- realistic capital and impact assumptions;
- appropriate correction for strategy search and multiple testing.

### Level 5 — Operationally demonstrated edge

The same strategy logic and execution semantics survive:

1. frozen prospective observation;
2. live-data shadow operation;
3. realistic paper trading;
4. controlled trading with minimal real capital;
5. reconciliation of every order, fill, balance, fee, and funding event.

Only this level supports a claim that the edge has been demonstrated in the target environment.

---

## 4. The economic mechanism requirement

Every edge hypothesis must answer two questions before it is tested:

1. **Who is economically paying the strategy?**
2. **Why do other participants not immediately eliminate the opportunity?**

Possible answers include:

- compensation for bearing crash, liquidity, inventory, funding, volatility, or counterparty risk;
- behavioral underreaction, overreaction, herding, attention, or forced liquidation;
- faster or better processing of public information;
- market segmentation, contract differences, capital controls, or short-sale constraints;
- convergence across related instruments or venues;
- compensation for providing liquidity or insurance;
- superior execution, order routing, abstention, sizing, or operational reliability.

A backtest discovered first and rationalized afterward receives weak prior credibility. The economic explanation must specify:

- the payer;
- the friction or risk;
- the expected horizon;
- the reason for persistence;
- the expected capacity;
- the likely decay mechanism;
- the conditions under which the edge should disappear or reverse.

This mechanism becomes part of the falsification plan. A hypothesis that cannot state what would prove it wrong is not sufficiently specified.

---

## 5. Alpha, risk premium, and hidden beta

### 5.1 Alpha

Alpha is a residual advantage after controlling for relevant systematic exposures, costs, and implementation risks.

### 5.2 Risk premium

A positive expected return may be compensation for bearing an undesirable risk. Examples include strategies that earn small profits frequently but suffer severe losses during:

- liquidity freezes;
- volatility spikes;
- crashes and gap events;
- deleveraging cascades;
- stablecoin depegs;
- exchange failures;
- correlations moving toward one;
- funding or borrow-cost shocks.

Such a strategy can still be useful, but it must not be described as free alpha.

### 5.3 Hidden beta

A strategy may appear neutral while being implicitly dependent on:

- a rising market;
- abundant leverage;
- low volatility;
- stable correlations;
- functioning short markets;
- healthy stablecoins;
- liquid exchanges;
- absence of large jumps.

The project may use the term **alpha** only after:

1. the benchmark and relevant factor exposures are declared;
2. performance is measured after all-in cost;
3. tail, liquidity, leverage, and counterparty exposures are reported;
4. the residual advantage survives independent data.

Before then, the correct term is **candidate edge**.

---

## 6. Evidence hierarchy

### E0 — Narrative

Only a story or economic intuition exists.

**Allowed status:** idea.

### E1 — Historical association

A point-in-time statistical relationship exists in historical data.

**Allowed status:** research hypothesis.

### E2 — Predefined historical backtest

The hypothesis is evaluated with:

- chronological train, validation, and test separation;
- implementable execution timing;
- a baseline cost model;
- suitable benchmarks;
- no known look-ahead violation.

**Allowed status:** experimental candidate.

### E3 — Robust historical evidence

The candidate survives:

- multiple temporal windows;
- regime analysis;
- relevant assets or venues;
- multiple-testing correction;
- cost and latency stress;
- parameter stability tests;
- ablation and negative controls;
- dependence-aware uncertainty estimation.

**Allowed status:** research-qualified candidate.

### E4 — Frozen prospective evidence

The strategy, data contract, code, thresholds, and kill criteria are frozen. Decisions are recorded before outcomes exist.

**Allowed status:** probable research edge.

### E5 — Realistic paper execution

The candidate operates on live data with real decision latency, bid and ask prices, partial fills, rejected orders, outages, recovery, and reconciliation, but without real capital.

**Allowed status:** paper-qualified edge.

### E6 — Controlled real-capital evidence

The candidate is operated with minimal capital, strict loss limits, no retrospective changes, and complete accounting of actual fills, fees, funding, incidents, and drawdowns.

**Allowed status:** operationally demonstrated edge.

### Binding rule

A historical result can reach at most E3. Cross-validation and sample splitting are necessary research tools but are not a substitute for observations that did not exist during strategy design.

---

## 7. What does not prove an edge

None of the following is sufficient alone:

| Claim | Why it is insufficient |
|---|---|
| Directional accuracy of 60% | The magnitude and cost distribution may still produce losses. |
| A high backtest Sharpe ratio | It may be the maximum selected from a large search. |
| A p-value below 0.05 | It ignores strategy selection, dependence, and economic costs. |
| Outperformance of buy-and-hold | The strategy may carry different beta, leverage, or tail risk. |
| Lower forecast error | Forecast improvement may not improve decisions or profit. |
| Feature correlation with future returns | The relation may reflect leakage, simultaneity, or one regime. |
| Profit on one exchange | It may be a venue-specific artifact or inaccessible execution. |
| Profit in a bull market | It may be disguised long-market exposure. |
| An arbitrage visible on mid-prices | The legs may not fill simultaneously or at the assumed prices. |
| Positive funding carry | It may compensate for crash, basis, depeg, or counterparty risk. |
| Multiple successful folds | The entire design may still have been chosen after observing history. |
| Publication in a journal | Peer review does not prove tradability or prospective persistence. |

The review by Reschenhofer et al. found that apparently strong financial forecasts often fail to translate into profit after realistic costs and data-snooping considerations; common weaknesses included short evaluation periods, weak benchmarks, and non-operational trading rules (DOI: 10.1002/for.2629).

---

## 8. Why backtests create false edges

### 8.1 Selection bias under multiple testing

If many zero-edge strategies are tested, the maximum observed Sharpe ratio rises with the number of trials. The best result among 100,000 variants does not have the same evidential meaning as a single strategy specified before observing the data.

Bailey and López de Prado describe backtest overfitting as the financial analogue of p-hacking: a computer search can produce impressive but false discoveries even when each individual model appears reasonable (DOI: 10.1111/1740-9713.01588).

### 8.2 A trial is more than a model hyperparameter

Every outcome-informed choice contributes to the effective research search space, including:

- market and asset selection;
- venue selection;
- sample start and end dates;
- bar frequency and aggregation;
- feature, label, and horizon choices;
- missing-value treatment;
- model, seed, and training window;
- threshold and position-size rules;
- fee and slippage assumptions;
- benchmark and evaluation metric;
- stop, take-profit, and holding rules.

If a result was observed and the design changed in response, a new trial occurred.

### 8.3 False discovery controls

The statistical toolkit may include:

- White's Reality Check;
- Hansen's Superior Predictive Ability test;
- stepwise SPA;
- familywise error control;
- false discovery rate control;
- Deflated Sharpe Ratio;
- Probability of Backtest Overfitting;
- block-bootstrap and dependence-aware confidence intervals.

No single diagnostic grants permission to trade. These methods address different failure modes and must be combined with economic and operational evidence.

### 8.4 Deflated Sharpe Ratio

A Sharpe assessment should account for:

- the number and dependence of trials;
- sample length;
- skewness;
- kurtosis;
- estimation uncertainty;
- selection of the maximum observed result.

A conventional Sharpe computed from autocorrelated, fat-tailed, negatively skewed returns can materially overstate evidence.

### 8.5 Fresh data

Fresh observations are the strongest safeguard against many forms of hindsight, sample selection, and data mining. Fang et al. applied previously published technical rules to genuinely new observations and found that the original predictability did not persist (DOI: 10.1016/j.rfe.2013.05.004).

---

## 9. Capacity and decay

Edge is a function of capital and horizon, not a constant property:

\[
\operatorname{Edge}(q_2) \leq \operatorname{Edge}(q_1),
\quad q_2 > q_1
\]

unless evidence establishes otherwise.

Sources of decay include:

- crowding and capital inflow;
- publication and imitation;
- improved connectivity;
- exchange rule changes;
- tighter spreads;
- stronger arbitrage participation;
- changes in market composition;
- disappearance of a behavioral population;
- increased adverse selection;
- reduced capacity from impact and queue competition.

Naik, Ramadorai, and Strömqvist found evidence that capital flows preceded declining alpha in several hedge-fund strategy families, consistent with capacity constraints (DOI: 10.1111/j.1468-036X.2006.00353.x).

Short-horizon opportunities generally have lower capacity because trades cannot be spread through time without losing the signal, while impact grows with deployment size. Van Binsbergen et al. formalize the trade-off between horizon-specific alpha, turnover, and price-impact cost (DOI: 10.1111/jofi.13331).

---

## 10. Cryptocurrency-specific false profitability

Cryptocurrency research introduces additional failure modes.

### 10.1 Survivorship and delisting bias

Using today's top cryptocurrencies to simulate past portfolios excludes assets that failed, became illiquid, or were delisted. The eligible universe must be reconstructed at every decision time from information available then.

A delisted asset cannot silently disappear from the simulation. The strategy must account for the actual exit mechanism, halted trading, residual value, and inability to transact.

### 10.2 Venue-selection bias

Choosing the exchange that produced the best historical result is part of the strategy search. Exchange data differ in price, liquidity, market participants, outages, contract design, and counterparty risk.

Multi-venue research also faces timestamp mismatch, nonsynchronous observations, and non-traded or stale prices. Tiniç et al. explicitly discuss these issues in cryptocurrency microstructure research (DOI: 10.1111/jfir.12317).

### 10.3 Candle aggregation ambiguity

Open-high-low-close-volume bars discard the path inside a bar. If a stop and target are both touched, the execution order cannot be known without finer data or a conservative convention.

Strategies whose profitability depends on favorable intrabar ordering must be rejected unless the path can be reconstructed.

### 10.4 Availability-time leakage

The following timestamps must be distinct where applicable:

- event time;
- exchange time;
- publication time;
- provider receipt time;
- local retrieval time;
- processing completion time;
- decision time;
- order submission time;
- acknowledgement and fill time.

A feature is usable only at its true `available_at`, not at the timestamp it describes.

### 10.5 Revised on-chain and entity data

Wallet labels, exchange identification, clustering, whale classification, and provider-cleaned histories may be revised later. Applying today's labels to historical observations can create leakage.

Historical research requires versioned vintages or explicit prospective collection.

### 10.6 Perpetual futures accounting

A realistic perpetual-futures simulation may need:

- actual funding rates and payment times;
- mark and index prices;
- maintenance margin and leverage tiers;
- liquidation logic;
- insurance-fund and auto-deleveraging behavior;
- settlement asset and stablecoin risk;
- contract-specification changes.

De Blasis and Webb show that futures contract design and market structure materially affect arbitrage opportunities, which often concentrate during dislocations when implementation risks are also elevated (DOI: 10.1002/fut.22305).

### 10.7 Reported volume is not executable liquidity

Useful liquidity measurements include:

- bid-ask spread;
- depth at relevant sizes;
- realized impact;
- fill probability;
- cancellation and queue behavior;
- cross-venue consistency.

Wash trading and non-economic volume can make volume-only filters misleading.

### 10.8 High-frequency illusion

The existence of a subsecond pattern does not imply that a normal independent trader can exploit it. Shynkevich documents deterministic subsecond algorithmic activity in major cryptocurrency spot and perpetual markets, where competition, adverse selection, and connectivity dominate outcomes (DOI: 10.1002/fut.70089).

### 10.9 Stablecoin and custody risk

A USD return and a stablecoin-denominated return are not identical when conversion, redemption, custody, or peg stability is uncertain. These risks must be modeled or the strategy must explicitly state that it cannot survive a stablecoin or exchange event.

### 10.10 Cryptocurrency lucky-factor evidence

Wei et al. tested thousands of technical rules and dozens of fundamental factors across major cryptocurrencies with data-snooping controls. Only a small subset retained both in-sample and out-of-sample profitability, challenging broad claims about the reliability of common technical and fundamental signals (DOI: 10.1002/ijfe.2863).

This supports a central policy of this project: a large number of rejected hypotheses is evidence that the research gate is functioning, not that the project has failed.

---

## 11. Mandatory edge-hypothesis dossier

No hypothesis may enter expensive replication or dedicated data engineering without the following record.

### 11.1 Identity and versioning

- `hypothesis_id`;
- version and freeze date;
- author or proposing agent;
- full change history;
- parent literature and code references.

### 11.2 Economic rationale

- target inefficiency or premium;
- economic payer;
- required risk-bearing or service;
- reason the edge can persist;
- expected decay and capacity;
- explicit disconfirming observations.

### 11.3 Tradable scope

- asset class and instrument;
- venue and settlement asset;
- point-in-time eligible universe;
- liquidity requirements;
- shorting, borrowing, and leverage constraints;
- legal and account-access constraints.

### 11.4 Information contract

For each input:

- source and schema;
- event, publication, retrieval, and availability times;
- revision policy;
- missingness and outage policy;
- immutable raw-data hash and version.

### 11.5 Decision contract

- decision frequency;
- prediction and holding horizons;
- action space, including abstention;
- position sizing and exposure limits;
- entry, rebalance, and exit logic.

### 11.6 Execution contract

- order types;
- maker or taker behavior;
- executable price source;
- latency assumptions;
- queue and partial-fill model;
- cancellation, retry, rejection, and recovery policy;
- multi-leg and basis risk;
- reconciliation requirements.

### 11.7 Benchmarks

At minimum, compare with relevant members of:

- no trade or cash;
- passive exposure;
- a simple economic baseline;
- the strongest feasible baseline;
- the same exposure with naive or random decisions;
- a volatility- or beta-matched alternative.

### 11.8 All-in cost model

- fees;
- spread;
- slippage;
- impact;
- funding and borrow;
- transfer and conversion;
- rollover and settlement;
- capital opportunity cost;
- relevant legal, tax, custody, and counterparty effects.

### 11.9 Trial ledger

Record all attempted:

- data sources;
- features and labels;
- assets and venues;
- models and seeds;
- parameter ranges;
- thresholds;
- time windows;
- benchmarks and metrics;
- positive and negative outcomes.

Deleting failed experiments is prohibited.

### 11.10 Risk register

Include market, volatility, liquidity, concentration, leverage, tail, funding, counterparty, stablecoin, custody, legal, model, data, and operational risks.

### 11.11 Evaluation metrics

Return and Sharpe are insufficient. Depending on the strategy, report:

- net return and uncertainty interval;
- downside deviation and Sortino;
- maximum drawdown and Calmar;
- expected shortfall and tail losses;
- skewness and crash exposure;
- turnover and cost-to-gross-alpha ratio;
- time under water;
- PnL concentration by trade, day, regime, asset, and venue;
- exposure and leverage;
- capacity and breakeven cost;
- probability of loss.

### 11.12 Robustness and falsification plan

- alternative costs and delayed execution;
- parameter perturbation;
- alternative start dates and folds;
- different regimes, assets, and venues where economically appropriate;
- missing data and outage simulation;
- dependence-aware bootstrap;
- ablation and negative controls;
- leave-one-period or leave-one-event-out analysis.

### 11.13 Predefined kill criteria

Specify before evaluation:

- minimum economically meaningful net edge;
- maximum acceptable drawdown and tail loss;
- maximum degradation from validation to test;
- maximum turnover and cost ratio;
- minimum number of independent decisions and regimes;
- cost-stress requirement;
- acceptable overfitting diagnostics;
- prospective stop conditions;
- real-capital shutdown conditions.

### 11.14 Prospective protocol

- code and configuration freeze;
- prospective start and end rules;
- target number of decisions and market regimes;
- append-only decision ledger;
- no retrospective threshold changes;
- incident and missing-data policy;
- completion and rejection criteria.

---

## 12. Hard rejection gates

These gates cannot be offset by a high return or score.

### Gate A — Temporal integrity

Reject immediately for:

- look-ahead or target leakage;
- revised data without vintages;
- information used before availability;
- future-informed asset universes;
- labels observable before their outcomes could exist.

### Gate B — Tradability

Reject immediately for:

- a non-tradable instrument;
- impossible fills;
- mid-price execution without spread;
- simultaneous multi-leg fills without leg-risk modeling;
- unavailable shorting, borrowing, leverage, or account access.

### Gate C — Net economics

Reject immediately when:

- the edge disappears under baseline realistic costs;
- breakeven cost is below normal trading cost;
- modest cost or latency stress changes the sign;
- most gross profit is consumed by turnover.

### Gate D — Stability

Reject immediately when:

- profit exists only in one fold, regime, venue, or asset without a mechanism that predicts this restriction;
- a small parameter change reverses the result;
- a small number of trades or events creates most profit;
- no economically coherent parameter region exists.

### Gate E — Hidden risk

Reject immediately when:

- leverage is uncontrolled;
- tail losses are omitted;
- liquidation, funding, counterparty, or stablecoin risk is ignored;
- the strategy is effectively short volatility or short liquidity but is reported as neutral alpha.

### Gate F — Reproducibility

Reject immediately when the result cannot be reconstructed from:

- immutable data;
- versioned code;
- exact configuration;
- declared random seeds;
- environment and dependency lock;
- artifact checksums.

---

## 13. Statistical policy

The following is a conservative project protocol, not a universal law.

### 13.1 Complete trial accounting

Manual notebook experiments, visual inspections that influence design, and failed runs count as research trials.

### 13.2 Multiple-testing control

Select methods according to the experimental structure. Candidate tools include Reality Check, SPA, stepwise SPA, familywise error control, false discovery rate, Deflated Sharpe Ratio, and Probability of Backtest Overfitting.

Jiang et al. examined more than 28,000 technical rules and found that fewer than 1% remained significant after data-snooping control, illustrating why isolated t-tests are inadequate for strategy searches (DOI: 10.1111/irfi.12161).

### 13.3 Time-series dependence

Independent and identically distributed assumptions must not be used blindly. Appropriate methods may include:

- heteroskedasticity and autocorrelation consistent errors;
- moving, stationary, or circular block bootstrap;
- clustered or event-aware inference;
- purging and embargo where labels overlap.

### 13.4 Lower-bound decisions

Promotion must not depend only on a point estimate. If an annual net-return estimate is 12% with an interval of -5% to 29%, a positive edge has not been established.

### 13.5 Sharpe is not sufficient

Fat tails, negative skew, autocorrelation, nonstationarity, and hidden state exposure require additional downside, tail, and stability measures.

---

## 14. Candidate scoring after hard gates

A surviving hypothesis is scored out of 100:

| Dimension | Weight |
|---|---:|
| Economic mechanism and payer | 15 |
| Data quality and temporal integrity | 15 |
| Statistical validity and trial control | 15 |
| Net economic value after cost | 20 |
| Stability across regimes and perturbations | 15 |
| Implementability and capacity | 10 |
| Prospective evidence | 10 |
| **Total** | **100** |

Suggested interpretation:

| Score | Status |
|---:|---|
| Below 50 | Reject |
| 50–64 | Research idea only |
| 65–74 | Replication candidate |
| 75–84 | Research-qualified candidate |
| 85–100 | Eligible for prospective evaluation |

A score of 100 based only on historical data still does not authorize live trading.

---

## 15. Engineering implications from production systems

Production trading systems treat temporal semantics, dry-run operation, persistence, and research-to-live parity as core architecture rather than optional utilities.

Freqtrade exposes dry-run, persistence, backtesting, look-ahead analysis, and recursive-analysis tooling as first-class features. This reflects the practical need to test both strategy logic and common leakage or indicator-instability errors before risking money.

NautilusTrader emphasizes a shared event-driven time and execution model for backtest and live deployment. This reduces the deployment gap created when a vectorized historical strategy is reimplemented in a different runtime with different order and timing semantics.

The project will not select a framework in this report. It adopts the engineering principle:

> Historical simulation, paper execution, and live execution must share explicit definitions of time, state, orders, fills, and recovery. Any remaining difference must be documented and tested.

---

## 16. Worked classification examples

### Example A — Direction classifier

- accuracy: 57%;
- 2,000 model and feature variants tested;
- no complete cost model;
- one year of test data.

**Classification:** no demonstrated edge.

### Example B — Momentum strategy

- positive net return across several folds;
- all profits occur during rising markets;
- beta and volatility exposure explain the result.

**Classification:** likely risk exposure or beta, not alpha.

### Example C — Funding carry

- long spot and short perpetual;
- positive historical funding income;
- liquidation, depeg, auto-deleveraging, and exchange failure omitted.

**Classification:** unmeasured tail-risk premium.

### Example D — Selective low-turnover strategy

- directional accuracy: 52%;
- trades in only 8% of eligible periods;
- expected move must exceed all-in cost plus an uncertainty buffer;
- robust under doubled cost and delayed execution;
- prospective behavior is similar to research estimates.

**Classification:** plausible candidate edge.

### Example E — Execution improvement

- the predictive signal is identical to the benchmark;
- improved routing and passive-order selection reduce realized slippage and fees;
- the improvement is confirmed using actual fills.

**Classification:** genuine execution edge if persistent and capacity-aware.

---

## 17. Binding decisions from Report 1.1

From this report onward:

1. Correlation, forecast accuracy, and gross backtest return will not be called edge.
2. Every hypothesis requires an economic mechanism, payer, persistence argument, and falsification condition.
3. All research trials and negative results must be retained.
4. Data availability, costs, and execution are part of the hypothesis, not post-processing adjustments.
5. Universes and features must be point-in-time.
6. Historical evidence can produce only a candidate edge.
7. Frozen prospective evidence is mandatory before paper qualification.
8. Hard gates override all scores and attractive performance statistics.
9. Rejecting every candidate is a valid and scientifically useful outcome.
10. Live capital requires separate proof of operational reliability and economic advantage.

---

## 18. Final adopted definition

> A genuine trading edge is a predefined and executable economic advantage over the strongest feasible benchmark that remains positive after all relevant costs, risks, and capacity limits; has a positive conservative lower-bound estimate; survives correction for multiple testing, parameter perturbation, regime variation, and execution delay; and is confirmed on genuinely new prospective data using the same decision and execution semantics intended for deployment.

Anything below that standard is one of the following:

- an idea;
- a statistical association;
- a promising historical backtest;
- compensation for hidden risk;
- disguised beta;
- or a selection artifact from noise.

---

## 19. Key references

1. Bailey, D. H., & López de Prado, M. (2021). *How “backtest overfitting” in finance leads to false discoveries*. Significance. DOI: [10.1111/1740-9713.01588](https://doi.org/10.1111/1740-9713.01588)
2. Bailey, D. H., Borwein, J., López de Prado, M., & Zhu, Q. *The Probability of Backtest Overfitting*. Journal of Computational Finance.
3. Fang, J., Jacobsen, B., & Qin, Y. (2014). *Predictability of the simple technical trading rules: An out-of-sample test*. Review of Financial Economics. DOI: [10.1016/j.rfe.2013.05.004](https://doi.org/10.1016/j.rfe.2013.05.004)
4. Harvey, C. R., Liu, Y., & Zhu, H. (2016). *...and the Cross-Section of Expected Returns*. Review of Financial Studies. DOI: [10.1093/rfs/hhv059](https://doi.org/10.1093/rfs/hhv059)
5. Jiang, F., Tong, G., & Song, G. (2019). *Technical Analysis Profitability Without Data Snooping Bias*. International Review of Finance. DOI: [10.1111/irfi.12161](https://doi.org/10.1111/irfi.12161)
6. McLean, R. D., & Pontiff, J. (2016). *Does Academic Research Destroy Stock Return Predictability?* Journal of Finance. DOI: [10.1111/jofi.12365](https://doi.org/10.1111/jofi.12365)
7. Naik, N. Y., Ramadorai, T., & Strömqvist, M. (2007). *Capacity Constraints and Hedge Fund Strategy Returns*. European Financial Management. DOI: [10.1111/j.1468-036X.2006.00353.x](https://doi.org/10.1111/j.1468-036X.2006.00353.x)
8. Reschenhofer, E., Mangat, M. K., Zwatz, C., & Guzmics, S. (2020). *Evaluation of current research on stock return predictability*. Journal of Forecasting. DOI: [10.1002/for.2629](https://doi.org/10.1002/for.2629)
9. Tiniç, M., Sensoy, A., Akyildirim, E., & Corbet, S. (2023). *Adverse selection in cryptocurrency markets*. Journal of Financial Research. DOI: [10.1111/jfir.12317](https://doi.org/10.1111/jfir.12317)
10. De Blasis, R., & Webb, A. (2022). *Arbitrage, contract design, and market structure in Bitcoin futures markets*. Journal of Futures Markets. DOI: [10.1002/fut.22305](https://doi.org/10.1002/fut.22305)
11. Wei, M., Kyriakou, I., Sermpinis, G., & Stasinakis, C. (2024). *Cryptocurrencies and Lucky Factors*. International Journal of Finance & Economics. DOI: [10.1002/ijfe.2863](https://doi.org/10.1002/ijfe.2863)
12. Shynkevich, A. (2026). *Trading Periodicity and Algorithmic Divide in Cryptocurrency Markets*. Journal of Futures Markets. DOI: [10.1002/fut.70089](https://doi.org/10.1002/fut.70089)
13. van Binsbergen, J., Han, J., Ruan, H., & Xing, R. (2024). *A Horizon-Based Decomposition of Mutual Fund Value Added Using Transactions*. Journal of Finance. DOI: [10.1111/jofi.13331](https://doi.org/10.1111/jofi.13331)

---

## 20. Next report

**Report 1.2 — Taxonomy of Edge Mechanisms** will separately analyze each major source of systematic trading profits, including its economic payer, persistence mechanism, decay, capacity, data requirements, implementation barriers, and falsification tests. No family will be preferred merely because it matches the repository's previous design.