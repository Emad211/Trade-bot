# Report 1.2 — Taxonomy of Trading Edge Mechanisms

**Program:** Edge Discovery Research Program  
**Section:** 1 — Edge Map  
**Report:** 2 of 5  
**Version:** 1.0  
**Research freeze date:** 2026-07-18  
**Status:** Complete  
**Parent:** [Report 1.1 — Definition of a Genuine Trading Edge and Its Proof Standard](01-01-edge-definition-and-proof-standard.md)

---

## Executive conclusion

A trading model, indicator, dataset, or neural architecture is not a source of edge. It is a tool that may detect, express, or execute an underlying economic mechanism.

The literature supports seven economically distinct primary families of candidate edge:

1. **Risk transfer, insurance, carry, and funding premia.**
2. **Behavioral mispricing and slow price adjustment.**
3. **Information acquisition and superior information processing.**
4. **Relative value, segmentation, and convergence.**
5. **Liquidity provision and market making.**
6. **Execution, routing, and operational advantage.**
7. **Portfolio construction, selective participation, and risk-control advantage.**

These families can interact, but they must not be double-counted. A momentum return may simultaneously reflect slow information diffusion, liquidity risk, and crash exposure. A futures basis may reflect insurance demand, funding constraints, or contract-specific segmentation. A spread-capture strategy may earn compensation for inventory and adverse-selection risk rather than free alpha.

The most important conclusion is therefore methodological:

> Every future strategy must be classified by its economic payer and persistence mechanism before it is classified by model type, asset, or signal.

This report does not select a market, asset class, horizon, or strategy. It creates the mechanism map that Report 1.3 will use to determine where an independent operator can realistically compete.

---

## 1. Purpose

Report 1.1 established what qualifies as a genuine edge and what evidence is required. Report 1.2 answers the next question:

> What economically distinct mechanisms can produce systematic trading profits, who pays them, why can they persist, and how must each mechanism be falsified?

The purpose is not to create a catalogue of popular strategies. The purpose is to prevent category errors such as:

- treating a risk premium as unexplained alpha;
- treating a forecast model as the source of profit;
- treating spread capture as riskless income;
- treating reduced drawdown as directional prediction;
- treating a law-of-one-price deviation as executable arbitrage;
- treating faster data processing as durable without measuring latency decay;
- treating a backtest improvement as independent when it is only another expression of the same underlying exposure.

---

## 2. Mechanism, signal, model, policy, and implementation are different layers

A complete trading hypothesis has at least five layers:

```text
Economic mechanism
        ↓
Observable state or signal
        ↓
Statistical model or rule
        ↓
Decision and portfolio policy
        ↓
Execution and operational implementation
```

### 2.1 Economic mechanism

The reason a transfer of wealth can occur. Examples:

- hedgers pay for insurance;
- impatient traders pay for immediacy;
- constrained arbitrageurs leave relative mispricing uncorrected;
- inattentive investors process information slowly;
- poor routing pays excessive spread and fees;
- a volatility-sensitive portfolio avoids exposure when risk is least compensated.

### 2.2 Observable state or signal

A measurable proxy for the mechanism. Examples:

- basis, funding, open interest, dealer positions;
- order-flow imbalance, spread, depth, queue state;
- attention, news arrival, disagreement, search activity;
- volatility, correlation, tail dependence, liquidity state;
- cross-venue or cross-instrument price deviation.

### 2.3 Statistical model or rule

The method that maps observations to estimates. Examples:

- linear regression;
- state-space or regime-switching models;
- tree ensembles;
- neural networks;
- language models;
- deterministic rules.

A more complex model does not create a new mechanism. It may only estimate an existing mechanism more or less effectively.

### 2.4 Decision and portfolio policy

The conversion of estimates into actions:

- trade or abstain;
- direction and instrument;
- sizing;
- hedging;
- rebalancing;
- risk budget;
- exit and shutdown conditions.

### 2.5 Execution and operation

The realized implementation:

- venue and order type;
- queue and fill behavior;
- routing;
- latency;
- partial fills and leg risk;
- reconciliation and recovery;
- counterparty and custody controls.

A strategy can have a valid economic mechanism and still lose because the implementation is inferior. Conversely, execution can create an advantage even when the predictive signal is identical to a benchmark.

---

## 3. Summary taxonomy

| ID | Primary mechanism | Economic payer | Typical horizons | Main persistence barrier | Dominant hidden risk | Typical capacity |
|---|---|---|---|---|---|---|
| EM-1 | Risk transfer, insurance, carry, funding | Hedgers, leverage demanders, protection buyers, impatient capital users | Days to years; sometimes funding intervals | Limited risk-bearing capital and costly insurance | Crash, liquidity, funding, correlation, counterparty | Medium to high, state dependent |
| EM-2 | Behavioral mispricing and slow adjustment | Inattentive, overconfident, extrapolative, constrained, or forced traders | Minutes to years, mechanism dependent | Cognitive bias, attention limits, slow diffusion, limits to arbitrage | Hidden beta, distress, liquidity, publication decay | Low to medium |
| EM-3 | Information acquisition and processing | Slower or less informed traders | Microseconds to months | Data cost, expertise, complexity, delayed diffusion | Latency decay, false causality, legal/data revision risk | Often low; can be medium at slower horizons |
| EM-4 | Relative value, segmentation, convergence | End users facing segmentation, contract or funding frictions | Seconds to contract maturity | Funding, margin, settlement, specialization, short constraints | Divergence, leg risk, margin calls, counterparty | Low to medium; occasionally high |
| EM-5 | Liquidity provision and market making | Traders demanding immediacy | Microseconds to days | Inventory and adverse-selection risk; technology | Toxic flow, jumps, inventory liquidation | Low per market; scalable across markets with infrastructure |
| EM-6 | Execution, routing, and operational advantage | Avoided fees, impact, stale routing, and system failures | Milliseconds to execution horizon | Better measurement, routing, reliability, venue access | Modelled fills differing from actual fills | Strategy-size dependent |
| EM-7 | Portfolio, abstention, and risk-control advantage | Avoided uncompensated risk and unnecessary trading cost | Bars to years | Predictable risk, nonlinear costs, diversification, no-trade regions | De-risking after losses, missed rebounds, model risk | Often high for modest capital |

The table describes broad priors, not universal properties. Each concrete hypothesis must state its own horizon, capacity, payer, and failure mechanism.

---

# Part I — Primary mechanism families

## 4. EM-1 — Risk transfer, insurance, carry, and funding premia

### 4.1 Definition

This family earns expected return by accepting a risk or financing burden that another participant wishes to transfer. The strategy is paid for providing:

- price insurance;
- leverage or balance-sheet capacity;
- duration or maturity transformation;
- volatility or tail-risk absorption;
- funding or inventory capital;
- hedging capacity;
- immediacy over longer horizons.

Common expressions include:

- futures carry and basis;
- hedging-pressure strategies;
- currency carry;
- volatility risk premia;
- funding-rate capture;
- lending, borrow, or staking spreads;
- insurance selling;
- dealer or intermediary balance-sheet premia.

### 4.2 Who pays?

Potential payers include:

- producers or consumers hedging future prices;
- investors buying downside protection;
- leveraged traders paying funding;
- asset owners paying borrow fees;
- institutions constrained by mandate, margin, or accounting treatment;
- participants requiring immediate balance-sheet use;
- investors avoiding operational or custody complexity.

The payer is not necessarily irrational. Paying a premium can be optimal because the buyer values reduced uncertainty, balance-sheet relief, or regulatory compliance.

### 4.3 Why can it persist?

Persistence can arise because:

- risk-bearing capital is limited;
- the premium performs poorly in states where marginal utility is high;
- institutional mandates prevent natural counterparties from entering;
- funding and collateral are scarce;
- the strategy has negative skew or rare catastrophic loss;
- intermediary balance sheets contract during stress;
- implementation requires specialized infrastructure or legal access.

Kang, Rouwenhorst, and Tang distinguish a longer-term insurance channel from a shorter-term liquidity channel in futures markets: speculators may receive compensation for absorbing hedging demand but pay or receive short-term premia depending on immediacy and position pressure (DOI: [10.1111/jofi.12845](https://doi.org/10.1111/jofi.12845)).

Boons and Prado show that basis momentum is related to supply-demand imbalances and intermediary constraints, which is consistent with compensation for providing capital when liquidity and volatility conditions are adverse (DOI: [10.1111/jofi.12738](https://doi.org/10.1111/jofi.12738)).

### 4.4 Expected fingerprints

A valid risk-premium hypothesis should predict:

- returns strengthen when demand for insurance or balance sheet increases;
- apparent Sharpe may fall sharply during stress;
- losses cluster in states of low liquidity or high volatility;
- premium magnitude varies with dealer capital, leverage, margin, or hedging pressure;
- capacity expands and contracts with market depth and financing conditions;
- a factor exposure or state variable explains at least part of the return.

### 4.5 Primary risks

- rare crash losses;
- negative skewness;
- basis widening before convergence;
- funding-rate reversal;
- correlation convergence during crisis;
- margin calls and forced liquidation;
- counterparty, settlement, stablecoin, or custody risk;
- apparent diversification disappearing in the left tail.

### 4.6 Data requirements

Depending on the market:

- futures curves, spot prices, and contract specifications;
- funding payments and timestamps;
- open interest and trader-position data;
- option surfaces and realized volatility;
- margin, liquidation, and collateral rules;
- borrow availability and rates;
- balance-sheet or funding-condition proxies;
- stress-period and failure-event histories.

### 4.7 Falsification tests

Reject or reclassify when:

- returns vanish after controlling the relevant risk state;
- the premium exists only because liquidation and failure states were omitted;
- compensation is below the expected tail loss or capital charge;
- the strategy cannot survive historical or synthetic funding stress;
- a change in collateral or settlement asset reverses the economics;
- return concentration occurs entirely in a small number of unrepeatable episodes;
- the supposed alpha is simply leverage applied to a known premium.

### 4.8 Independent-operator prior

This family can be accessible at medium horizons and modest capital, but a small operator must avoid assuming that a market-neutral position is risk-neutral. The strongest advantage may be operational simplicity, low overhead, or willingness to hold capital through conditions in which constrained institutions cannot. The main danger is underestimating rare losses and exchange or collateral risk.

---

## 5. EM-2 — Behavioral mispricing and slow price adjustment

### 5.1 Definition

This family attempts to profit when prices do not immediately incorporate information or when participants systematically extrapolate, overreact, underreact, herd, or trade for non-informational reasons.

Submechanisms include:

- gradual information diffusion;
- limited attention;
- conservatism in belief updating;
- overconfidence and biased self-attribution;
- extrapolation and trend chasing;
- disposition effects;
- herding;
- lottery preference;
- forced liquidation or mandate-driven flow;
- delayed reaction across economically linked assets.

### 5.2 Who pays?

Potential counterparties include:

- inattentive or slow-processing investors;
- overconfident traders;
- trend chasers entering late;
- investors forced to trade by liquidation, flows, tax, mandate, or risk limits;
- constrained informed institutions unable to correct mispricing;
- participants who use simplified models for hard-to-value assets.

### 5.3 Why can it persist?

Behavioral patterns can persist when:

- new participants repeatedly enter the market;
- feedback about true value is delayed or ambiguous;
- fundamentals are difficult to estimate;
- shorting or arbitrage is costly;
- attention and sophistication are unevenly distributed;
- institutional constraints bind at the same time behavioral demand increases;
- the bias is generated by market design rather than a fixed population.

Hirshleifer's survey emphasizes that expected returns may reflect both risk and misvaluation, particularly under uncertainty and weak feedback (DOI: [10.1111/0022-1082.00379](https://doi.org/10.1111/0022-1082.00379)).

Hong and Stein model gradual information diffusion followed by momentum trading and possible long-horizon overreaction (DOI: [10.1111/0022-1082.00184](https://doi.org/10.1111/0022-1082.00184)). Daniel, Hirshleifer, and Subrahmanyam connect overconfidence and biased attribution to short-run continuation and later reversal (DOI: [10.1111/0022-1082.00077](https://doi.org/10.1111/0022-1082.00077)).

### 5.4 Horizon fingerprints

Mechanisms should imply different return paths:

- **Underreaction / slow diffusion:** continuation followed by gradual decay, not necessarily reversal.
- **Overreaction / extrapolation:** initial continuation or pressure followed by sign reversal.
- **Temporary liquidity shock:** short-horizon reversal as transitory pressure unwinds.
- **Forced liquidation:** price concession followed by recovery conditional on solvency and market depth.
- **Fundamental information:** continuation without full reversal if cash-flow expectations genuinely change.

A hypothesis that claims both underreaction and overreaction after seeing the result is not falsifiable. The expected impulse response must be specified before testing.

### 5.5 Evidence and disagreement

Detzel et al. provide a rational-learning explanation for price drift in assets with hard-to-value fundamentals and report moving-average predictability for Bitcoin and relevant stock groups (DOI: [10.1111/fima.12310](https://doi.org/10.1111/fima.12310)). This illustrates that price continuation need not imply irrationality.

Chen et al. identify attention spillovers that create short-run pressure and later reversal (DOI: [10.1111/jofi.13281](https://doi.org/10.1111/jofi.13281)). Della Vedova et al. show momentum can strengthen when the normal relationship between household liquidity provision and institutionally informed trading breaks down (DOI: [10.1111/eufm.70023](https://doi.org/10.1111/eufm.70023)).

However, Szakmary and Lancaster find that trend-following profitability in U.S. stocks disappeared after 2007, demonstrating that behavioral or diffusion-based opportunities can decay without a simple explanation from market-state changes (DOI: [10.1111/fire.12065](https://doi.org/10.1111/fire.12065)).

### 5.6 Data requirements

- event timestamps and publication times;
- investor-type or order-flow data where available;
- attention and participation proxies;
- cross-asset economic links;
- short-sale, leverage, and arbitrage constraints;
- fundamental outcomes for separating information from sentiment;
- sufficient post-event horizon for continuation and reversal tests.

### 5.7 Falsification tests

- predefine the expected horizon and reversal pattern;
- separate public-information events from non-information shocks;
- use placebo assets, unrelated events, or participant groups;
- test whether results concentrate in illiquid or distressed assets and disappear after liquidity adjustment;
- test whether a risk factor, beta, or option-like payoff explains the return;
- measure post-publication and recent-sample decay;
- test whether realistic transaction costs consume the short-horizon pattern;
- require prospective event capture to eliminate revised timestamps and hindsight classification.

### 5.8 Independent-operator prior

Slower behavioral or forced-flow mechanisms may be accessible without low-latency infrastructure. Their weakness is severe research-selection risk: thousands of technical patterns can be rationalized after discovery. Strong candidates require identifiable participants, events, or constraints—not only price shapes.

---

## 6. EM-3 — Information acquisition and superior information processing

### 6.1 Definition

This family profits from observing useful information earlier, more accurately, more completely, or in a more actionable form than competing participants.

It includes:

- direct information-speed advantage;
- superior parsing of public disclosures or news;
- alternative data;
- on-chain or network data;
- entity resolution;
- cross-language processing;
- cross-market information transmission;
- better estimation of hidden state from order flow;
- improved signal-to-decision compression.

The source is not the machine-learning model itself. The source is the information gap that the model helps exploit.

### 6.2 Who pays?

- slower participants;
- participants with incomplete data coverage;
- investors unable to process complex or unstructured information;
- liquidity providers quoting stale prices;
- traders relying on delayed or aggregated feeds;
- participants unable to connect information across related markets.

### 6.3 Why can it persist?

- data acquisition is costly;
- interpretation requires domain expertise;
- information is fragmented across languages, venues, or formats;
- processing latency matters;
- entity resolution is difficult;
- institutional systems change slowly;
- the information is valuable only when combined with position, liquidity, or regime context.

Persistence generally declines as:

- vendors commoditize the dataset;
- a signal becomes widely published;
- exchanges improve dissemination;
- participants adopt similar models;
- the market horizon shrinks below the operator's latency.

### 6.4 Information edge subtypes

#### 6.4.1 Speed edge

The same information is observed earlier. Typical horizon: microseconds to minutes. This is highly sensitive to:

- physical location;
- feed type;
- parsing time;
- network and exchange latency;
- order-entry priority.

#### 6.4.2 Breadth edge

The operator integrates more sources or markets than competitors. Typical horizon: minutes to days.

#### 6.4.3 Interpretation edge

The operator maps information to economic consequences more accurately. Language models may be useful here, but their revision, hallucination, and latency must be measured.

#### 6.4.4 State-estimation edge

The operator infers unobserved inventory, toxicity, liquidation pressure, or regime from public market data.

#### 6.4.5 Data-quality edge

The advantage comes from cleaner timestamps, correct vintages, reliable entity histories, or better handling of outages and revisions.

### 6.5 Main risks

- timestamp or revision leakage;
- using a modern entity label in historical data;
- confusing correlation with causality;
- data-provider survivorship or silent backfill;
- illegal, restricted, or contractually prohibited information use;
- speed advantage that disappears before deployment;
- model output not available early enough to trade;
- high false-positive cost during major events.

### 6.6 Falsification tests

- record publication, receipt, processing-start, processing-end, decision, and order times;
- measure performance as artificial delays are added;
- compare against the cheapest publicly available delayed feed;
- use source ablation and leave-one-source-out analysis;
- verify that information predicts outcomes beyond price and order-flow controls;
- evaluate event classifications prospectively;
- test alternative entity and topic mappings;
- verify legal and contractual usability;
- test whether value survives full processing and execution latency.

### 6.7 Independent-operator prior

A small technical team is unlikely to win pure speed races against colocated firms. It may compete at slower horizons through domain expertise, source integration, multilingual processing, data quality, and targeted alternative data. The best opportunity is often information that is public but operationally difficult to structure, rather than information that is merely fast.

---

## 7. EM-4 — Relative value, segmentation, and convergence

### 7.1 Definition

This family trades two or more economically linked prices when their relationship deviates from a justified range. Examples include:

- spot-futures basis;
- calendar spreads;
- cross-listed assets;
- option parity;
- exchange-traded fund versus net asset value;
- cross-venue price differences;
- pairs and baskets;
- stablecoin or wrapped-asset parity;
- index and constituent discrepancies;
- yield or funding-curve relationships.

### 7.2 Who pays?

The apparent payer may be:

- end users with urgent hedging or inventory demand;
- participants trapped by venue, jurisdiction, custody, or mandate;
- intermediaries facing funding or balance-sheet constraints;
- traders unable to short or transfer an asset;
- markets that update asynchronously;
- participants accepting contract-specific settlement or collateral terms.

### 7.3 Why can it persist?

Real-world law-of-one-price relationships are bounded by:

- trading and transfer costs;
- funding and collateral requirements;
- short-sale and borrow constraints;
- position limits;
- settlement delays;
- market fragmentation;
- capital controls;
- taxes and jurisdiction;
- counterparty and custody risk;
- specialist balance sheets;
- uncertain convergence time.

Siriwardane, Sunderam, and Wallen find that arbitrage is segmented by funding source and intermediary specialization; different spreads respond to localized funding and balance-sheet shocks rather than a single universal arbitrage-capital factor (DOI: [10.1111/jofi.13469](https://doi.org/10.1111/jofi.13469)).

Bhanot and Guo show that funding and asset-specific liquidity affect both the magnitude and path of convergence, including margin-call risk (DOI: [10.1002/fut.20518](https://doi.org/10.1002/fut.20518)).

### 7.4 Convergence is not riskless

Kondor demonstrates that dynamic convergence trading can experience losses and negative skew even when the underlying opportunity appears fundamentally riskless (DOI: [10.1111/j.1540-6261.2009.01445.x](https://doi.org/10.1111/j.1540-6261.2009.01445.x)).

Chen et al. identify nonlinear limits to arbitrage: moderate mispricing attracts capital, but extreme mispricing can coincide with tighter funding constraints and less arbitrage activity (DOI: [10.1002/fut.22320](https://doi.org/10.1002/fut.22320)). Therefore:

> A larger spread is not automatically a better trade. It may indicate that convergence capital is impaired or that the relationship has structurally changed.

### 7.5 Primary risks

- divergence before convergence;
- uncertain or absent convergence;
- partial execution and leg risk;
- transfer or settlement delay;
- borrow recall;
- margin calls;
- contract redesign;
- liquidation or auto-deleveraging;
- depeg and counterparty risk;
- modelled cointegration breaking permanently;
- stale quotes creating fictitious spreads.

### 7.6 Data requirements

- synchronized executable quotes for every leg;
- depth and size-sensitive prices;
- funding, borrow, margin, and transfer conditions;
- contract specifications and historical changes;
- settlement calendars and failure history;
- venue health and counterparty state;
- capital usage through the full holding path;
- timestamps precise enough for the intended horizon.

### 7.7 Falsification tests

- enter using executable bid and ask, never simultaneous mid-prices;
- model asymmetric fill probability and residual exposure;
- apply random and stress delays between legs;
- simulate basis widening and collateral calls before convergence;
- test structural breaks and relationship re-estimation rules;
- test independent venues and alternative quote sources;
- include transfer, borrow, settlement, and funding costs;
- test whether the spread remains after using synchronous observations;
- evaluate capital return, not only return on nominal exposure;
- require live shadow quotes and prospective multi-leg paper execution.

### 7.8 Independent-operator prior

Structural relative-value opportunities may suit modest capital because capacity can be too small for large institutions. However, venue access, account restrictions, transfer reliability, and counterparty diversification are often the true bottlenecks. A small operator may have flexibility but weaker balance sheet and legal protection.

---

## 8. EM-5 — Liquidity provision and market making

### 8.1 Definition

A liquidity provider posts executable interest and receives compensation for supplying immediacy. Potential revenue includes:

- quoted or realized spread;
- maker rebate;
- temporary price-pressure reversal;
- inventory mean reversion;
- privileged or low-toxicity order flow.

### 8.2 Who pays?

- impatient traders;
- large traders prioritizing completion;
- informed traders whose adverse-selection cost is priced into spreads;
- exchanges subsidizing displayed liquidity;
- participants paying for certainty of execution.

### 8.3 Why can it persist?

Liquidity provision is a service with real costs:

- inventory risk;
- adverse selection;
- order-processing and infrastructure cost;
- capital and margin consumption;
- queue uncertainty;
- jump risk while quotes are resting;
- continuous monitoring and cancellation requirements.

Zaharudin, Young, and Hsu summarize market-making revenue as spread capture with compensation for inventory and adverse-selection risk, often dependent on very fast quote updates and fee structure (DOI: [10.1111/joes.12434](https://doi.org/10.1111/joes.12434)).

Kelley and Tetlock distinguish aggressive order information from passive liquidity provision and show how realized spread represents only the temporary component that a liquidity provider may retain (DOI: [10.1111/jofi.12028](https://doi.org/10.1111/jofi.12028)).

### 8.4 Why quoted spread is not profit

A filled passive order is selected, not random. It may fill precisely when:

- price is about to move through the quote;
- informed flow arrives;
- other liquidity providers cancel;
- inventory is most costly;
- volatility rises.

Expected market-making value must therefore be measured as:

\[
\text{Realized spread}
+
\text{rebates}
-
\text{adverse selection}
-
\text{inventory loss}
-
\text{hedging and impact cost}
-
\text{operational cost}
\]

### 8.5 Technology and horizon

At highly liquid markets, competitive market making may require:

- low-latency market data;
- rapid cancellation;
- reliable queue estimates;
- colocated or geographically close infrastructure;
- precise fee and order-type knowledge;
- real-time inventory and toxicity controls.

At slower or less competitive markets, latency may be less demanding but counterparty, liquidity, and jump risks can be much larger.

### 8.6 Data requirements

- full-depth or relevant limit-order-book data;
- trades, quotes, and sequence information;
- own-order acknowledgements and fills;
- queue estimates;
- cancellation and reject logs;
- maker/taker fee histories;
- realized spread and mark-out horizons;
- inventory and hedge transactions;
- venue outages and latency distributions.

### 8.7 Falsification tests

- evaluate realized spread at several post-fill mark-out horizons;
- condition fills on subsequent price moves;
- compare actual and simulated fill rates;
- use conservative queue assumptions;
- measure PnL before and after rebates separately;
- test inventory shocks and quote withdrawal conditions;
- evaluate toxic versus non-toxic order-flow regimes;
- include hedging cost and residual inventory;
- paper trade with actual submitted orders or a venue-supported sandbox where possible.

Dixon's trade-information-matrix approach is relevant because it maps prediction error to profit under fill probability and position constraints rather than treating classification accuracy as sufficient (DOI: [10.1002/hf2.10016](https://doi.org/10.1002/hf2.10016)).

### 8.8 Independent-operator prior

Competing in top-tier subsecond market making is generally a weak prior for a small remote operator. Niche instruments or slower horizons may be feasible, but the project must prove that larger spreads are not simply compensation for unmanageable adverse selection, counterparty risk, or nonexistent depth.

---

## 9. EM-6 — Execution, routing, and operational advantage

### 9.1 Definition

An execution edge improves realized outcomes without necessarily improving return forecasts. It may reduce:

- spread paid;
- market impact;
- missed fills;
- adverse selection;
- fees;
- opportunity cost;
- stale-order loss;
- duplicate orders;
- outages and recovery loss;
- capital trapped by failed or unmatched legs.

### 9.2 Who pays or what is avoided?

Unlike a directional edge, much of this value is an avoided transfer:

- exchanges receive lower fees;
- market makers receive less spread;
- other traders receive less impact advantage;
- the system avoids losses from poor timing, routing, or reliability;
- the strategy retains more of an upstream gross signal.

Execution alpha must be measured relative to an explicit parent-order benchmark, not as an unexplained component of total PnL.

### 9.3 Submechanisms

#### 9.3.1 Order-type selection

Choosing passive, aggressive, post-only, immediate-or-cancel, or other instructions based on urgency, toxicity, and fill probability.

#### 9.3.2 Smart routing

Choosing venues based on:

- net executable price;
- depth;
- fee and rebate;
- fill probability;
- adverse selection;
- hidden liquidity;
- reliability and latency.

Battalio, Corwin, and Jennings show that routing to maximize maker rebates can reduce execution quality; rebates cannot be optimized independently of fill and adverse-selection outcomes (DOI: [10.1111/jofi.12422](https://doi.org/10.1111/jofi.12422)).

#### 9.3.3 Scheduling and impact control

Determining how quickly to execute based on order imbalance, volatility, liquidity, signal decay, and urgency. Easley, López de Prado, and O'Hara formulate an optimal execution horizon that depends on whether the order leans with or against prevailing flow (DOI: [10.1111/mafi.12045](https://doi.org/10.1111/mafi.12045)).

#### 9.3.4 Reliability advantage

- idempotent client order IDs;
- restart-safe state;
- duplicate prevention;
- reconciliation;
- stale-data shutdown;
- deterministic retry and cancel policy;
- venue failover;
- accurate fee and funding accounting.

Operational reliability may not create gross alpha, but it determines whether a research edge survives production.

### 9.4 Data requirements

- parent decisions and desired positions;
- every order message and acknowledgement;
- fills and partial fills;
- full fee and rebate records;
- contemporaneous market state;
- implementation shortfall benchmark;
- venue latency and error distributions;
- opportunity cost of missed or delayed execution;
- reconciliation and incident logs.

### 9.5 Falsification tests

- replay identical parent orders through competing policies;
- use randomized or alternating routing where safe;
- compare implementation shortfall with matched market state;
- report conditional results by size, urgency, volatility, and venue;
- separate fee improvement from price and fill deterioration;
- test restart, duplicate, cancel, stale-data, and reconciliation failures;
- require live-fill evidence because historical queue simulation is insufficient.

### 9.6 Independent-operator prior

This is one of the most credible sources of practical advantage for a strong software team. It does not require forecasting the market better than every competitor; it requires losing less of whatever gross edge exists. Its value is bounded by the upstream strategy's trading volume and gross opportunity.

---

## 10. EM-7 — Portfolio construction, selective participation, and risk-control advantage

### 10.1 Definition

This family improves economic utility through decisions about **when not to trade**, how much risk to take, and how to combine exposures. It includes:

- abstention and no-trade regions;
- transaction-cost-aware thresholds;
- volatility targeting;
- tail-risk scaling;
- regime-conditioned exposure;
- diversification and covariance management;
- drawdown and capital-preservation policies;
- uncertainty-aware position sizing;
- exposure netting across strategies;
- risk budgeting.

This family may generate value even when expected-return forecasts are weak.

### 10.2 Who pays or what loss is avoided?

The value often comes from avoiding:

- trading when gross opportunity is below all-in cost;
- overexposure when volatility is high and risk compensation is low;
- concentrated or redundant bets;
- forced liquidation caused by excessive leverage;
- repeated rebalancing inside a no-trade band;
- tail losses that permanently impair capital;
- model actions under high uncertainty.

There may be no direct behavioral counterparty. The advantage can arise from a better objective function and better use of scarce risk capital.

### 10.3 Economic basis

With fixed and proportional transaction costs, optimal policies naturally contain no-trade regions rather than continuous rebalancing. Liu shows that transaction costs can materially reduce the economic importance of apparent return predictability and lead to threshold-based trading policies (DOI: [10.1111/j.1540-6261.2004.00634.x](https://doi.org/10.1111/j.1540-6261.2004.00634.x)).

Risk targeting adjusts exposure using conditional risk estimates. Happersberger, Lohre, and Nolte show that dynamic risk and portfolio-insurance strategies can improve downside protection, while also demonstrating dependence on the quality of tail-risk forecasts (DOI: [10.1111/eufm.12256](https://doi.org/10.1111/eufm.12256)).

The literature is not uniformly positive. DeMiguel, Martín-Utrera, and Uppal note that several volatility-managed strategies fail out of sample or after transaction costs, then identify a conditional multifactor implementation that performs better under stricter evaluation (DOI: [10.1111/jofi.13395](https://doi.org/10.1111/jofi.13395)). This disagreement is important: risk management must be evaluated economically, not accepted because it lowers historical volatility.

### 10.4 Risk forecast versus trading objective

A statistically accurate volatility forecast is not automatically economically optimal. Taylor shows that variance forecasts optimized for mean squared error may have insignificant trading value, while forecasts aligned with the investor's loss function can produce different outcomes (DOI: [10.1002/for.70063](https://doi.org/10.1002/for.70063)).

Therefore, every risk model must be evaluated through the action it controls:

- exposure;
- margin;
- hedge;
- abstention;
- rebalancing;
- capital reserve.

### 10.5 Primary risks

- reducing exposure after losses and missing rebounds;
- procyclical deleveraging;
- inaccurate covariance during crisis;
- diversification disappearing in the left tail;
- excessive turnover from unstable weights;
- hidden return timing introduced by the risk model;
- backtest benefit caused by one crash;
- overfitting risk thresholds or regime definitions.

### 10.6 Data requirements

- return, volatility, liquidity, and dependence measures;
- realistic costs as a function of turnover and size;
- tail-event and crisis data;
- state-dependent correlation;
- uncertainty estimates;
- portfolio-level exposure and capital use;
- benchmark policies with matched average risk.

### 10.7 Falsification tests

- compare at matched average volatility, beta, leverage, and capital;
- separate return improvement from volatility reduction;
- test whether results rely on a single crisis;
- apply delayed risk estimates and noisy forecasts;
- include transaction costs and weight turnover;
- evaluate alternative regime definitions;
- test tail dependence and correlation breakdown;
- compare with simple no-trade bands, equal weight, inverse volatility, and fixed exposure;
- use prospective action logs, not only risk-forecast scores.

### 10.8 Independent-operator prior

This is a high-priority engineering and research family because it can add value across many upstream signals, is often less latency-sensitive, and directly supports survival. It should not be used to manufacture a positive Sharpe from an unprofitable signal. The benchmark must isolate incremental decision-policy value.

---

# Part II — Cross-cutting classification axes

## 11. A strategy requires both a primary mechanism and overlays

Every future hypothesis must declare exactly one **primary economic mechanism** and may declare secondary overlays.

Example:

```yaml
primary_mechanism: EM-4_relative_value
secondary_mechanisms:
  - EM-1_funding_risk_premium
  - EM-6_execution_advantage
risk_overlay:
  - EM-7_volatility_and_tail_scaling
```

The primary mechanism answers who pays and why. Secondary mechanisms explain important conditional behavior but cannot each claim the same PnL.

---

## 12. Directionality axis

| Type | Description |
|---|---|
| Directional | Depends materially on asset price direction. |
| Relative directional | Selects winners versus losers but retains factor or market exposure. |
| Market neutral | Attempts to remove first-order market direction. |
| Delta or beta hedged | Neutral only to declared first-order exposures. |
| Pure execution | Improves realized cost for a fixed desired trade. |
| Risk overlay | Changes exposure rather than forecasting direction. |

Market-neutral does not mean risk-neutral. Basis, correlation, volatility, liquidity, and counterparty risks can remain dominant.

---

## 13. Horizon and latency axis

| Horizon | Likely dominant mechanisms | Main challenge |
|---|---|---|
| Microseconds–seconds | Information speed, stale quotes, queue, market making | Colocation, feeds, queue, adverse selection |
| Seconds–minutes | Order flow, event response, cross-market transmission | Fill realism, decay, spread and impact |
| Minutes–days | Slow diffusion, forced flow, derivatives state, risk timing | Regime instability, event timestamps, cost |
| Days–months | Carry, hedging pressure, cross-sectional factors, relative value | Funding, capacity, structural changes |
| Months–years | Risk premia, value, insurance, structural segmentation | Few independent observations, tail risk |

A high-frequency dataset does not imply a high-frequency edge. The trading horizon must follow the mechanism's decay, not the available sampling rate.

---

## 14. Capacity axis

Capacity is driven by:

- market depth;
- signal horizon;
- number of independent instruments;
- turnover;
- ability to spread execution;
- funding and margin;
- crowding;
- transfer and settlement capacity;
- short and borrow supply.

Short-lived alpha often has lower capacity because execution cannot be distributed through time. Risk premia can have higher nominal capacity but can collapse when all holders seek to exit simultaneously.

---

## 15. Technology and access axis

| Requirement | Low | Medium | High |
|---|---|---|---|
| Market-data granularity | Daily or bars | Trades and quotes | Full-depth, sequence-level, direct feed |
| Latency | Minutes or more | Seconds | Submillisecond to milliseconds |
| Venue integration | One venue | Several APIs | Colocation, direct market access |
| Capital | Modest | Multi-leg collateral | Large inventory and balance sheet |
| Operational burden | Scheduled batch | Continuous service | Fault-tolerant real-time infrastructure |
| Legal/data access | Public | Licensed data | Restricted or institutional access |

Report 1.3 will use this axis to eliminate mechanisms that are theoretically valid but operationally inaccessible.

---

## 16. Return-shape axis

Mechanisms should be classified by expected distribution:

- frequent small gains / rare large losses;
- infrequent event gains;
- positive skew;
- negative skew;
- long-duration convergence;
- inventory-dependent returns;
- regime-localized returns;
- crisis-sensitive or crisis-protective returns.

A strategy's average return cannot be interpreted without its state-contingent loss profile.

---

# Part III — Mechanism interactions and double-counting controls

## 17. Momentum is not one mechanism

Observed continuation may reflect:

- slow information diffusion;
- overconfidence and feedback trading;
- rational learning about hard-to-value fundamentals;
- time-varying risk premia;
- forced flow;
- liquidity and market-friction exposure.

Required tests include horizon response, reversal, event linkage, factor controls, participant behavior, and liquidity conditioning.

---

## 18. Carry is not one mechanism

Carry may reflect:

- insurance demand;
- crash or volatility risk;
- funding scarcity;
- intermediary balance sheet;
- convenience yield;
- contract design;
- segmentation.

A high carry signal cannot be treated as alpha until the relevant loss states and collateral path are included.

---

## 19. Order flow is not one mechanism

Order flow may contain:

- private information;
- forced or liquidity-motivated demand;
- inventory rebalancing;
- execution scheduling;
- mechanical liquidation;
- manipulation or wash trading.

Its expected return signature depends on source. Informed flow tends to have persistent impact; liquidity pressure may reverse; liquidation may continue before reverting.

---

## 20. Volatility management is not automatically an edge

Reducing exposure in high volatility can:

- improve utility if risk is poorly compensated;
- reduce leverage and drawdown;
- or merely reduce both risk and return while adding turnover.

It must be evaluated at matched risk and after cost. A lower drawdown alone is not evidence of economic superiority.

---

## 21. Information and execution can be inseparable

A faster signal is worthless if:

- it arrives after the price moves;
- orders queue behind competitors;
- fills occur only when the prediction is wrong;
- the required processing creates excessive delay;
- spread and impact exceed the predicted move.

For short-horizon hypotheses, information, decision, and execution must be evaluated as one end-to-end system.

---

# Part IV — Research priorities implied by the taxonomy

## 22. Preliminary mechanism priors

These are research priors, not final strategy selections.

### 22.1 Structurally durable but risk-bearing

- risk transfer and insurance;
- funding and balance-sheet premia;
- structurally segmented relative value.

These have strong economic reasons to persist but can hide severe tail and funding risk.

### 22.2 Potentially true alpha but high decay

- behavioral mispricing;
- superior public-information processing;
- cross-market diffusion.

These can produce residual alpha but are highly exposed to selection, publication, and competition.

### 22.3 Operationally credible and broadly useful

- execution quality;
- cost-aware abstention;
- portfolio and risk policy;
- reliability and reconciliation.

These may preserve rather than originate gross alpha, but they are necessary for any live system and can create measurable incremental value.

### 22.4 Weak prior for a remote independent operator

- top-tier subsecond latency arbitrage;
- highly competitive market making in the deepest instruments;
- strategies requiring proprietary institutional flow or balance-sheet access.

These mechanisms can be real while remaining inaccessible to this project.

---

## 23. Required classification record for every future hypothesis

```yaml
hypothesis_id: EDGE-XXXX
primary_mechanism: EM-1_to_EM-7
secondary_mechanisms: []
economic_payer: ""
service_or_risk_provided: ""
reason_for_persistence: ""
expected_horizon: ""
expected_return_shape: ""
expected_capacity: ""
required_data: []
required_market_access: []
latency_budget: ""
main_hidden_risks: []
expected_decay_mechanism: []
mechanism_specific_falsification_tests: []
benchmark_that_isolates_incremental_value: ""
```

A hypothesis that cannot complete these fields is not ready for implementation.

---

## 24. Engineering examples are not empirical proof

Open-source systems illustrate operational requirements but do not prove profitability:

- **Hummingbot** exposes market-making and spot-perpetual arbitrage components, demonstrating the need for multi-leg state, budget checks, slippage buffers, and opening/closing transitions.
- **NautilusTrader** emphasizes shared event-driven semantics across research and live execution, useful for reducing simulation-to-production divergence.
- **Freqtrade** exposes dry-run and look-ahead analysis, useful for directional strategy testing and leakage diagnostics.

These projects are implementation references. Their existence does not validate any default strategy or parameter.

---

# Part V — Binding outputs

## 25. Decisions adopted by Report 1.2

1. Every candidate must declare one primary economic mechanism.
2. Models and indicators are never classified as mechanisms.
3. PnL cannot be attributed independently to overlapping mechanisms without decomposition.
4. Risk-premium returns must be reported as compensation for declared states until residual alpha is established.
5. Relative-value research must model the full capital and convergence path, not only terminal spread closure.
6. Market-making research must use fill-conditioned mark-outs and inventory accounting, not quoted spread.
7. Information-edge research must measure complete publication-to-fill latency.
8. Execution and risk-policy value must be tested incrementally against the same upstream decisions.
9. A mechanism may be economically real but rejected because the project lacks data, access, technology, legal permission, or capital.
10. Report 1.3 will evaluate markets and horizons against these mechanism requirements without inheriting the repository's previous choices.

---

## 26. What remains unresolved

This report has not yet determined:

- which asset class offers the best opportunity;
- whether cryptocurrency should remain the target;
- whether the system should be directional or relative-value;
- which horizons are compatible with available infrastructure;
- which datasets can be collected point in time;
- which mechanisms are legally and operationally accessible;
- which candidates deserve replication.

These are the subjects of Reports 1.3 through 1.5.

---

## 27. Next report

**Report 1.3 — Market, Instrument, Horizon, Competition, and Capacity Map** will evaluate where each mechanism can realistically be implemented. It will compare markets using:

- structural source of edge;
- data availability and integrity;
- competition and latency;
- market depth and capacity;
- account and legal access;
- shorting, leverage, and settlement;
- infrastructure cost;
- tail and counterparty risk;
- suitability for a technically capable independent operator.

No market will be retained merely because the current repository already supports it.

---

## 28. Key references

### Risk transfer, carry, and intermediary constraints

1. Kang, W., Rouwenhorst, K. G., & Tang, K. *A Tale of Two Premiums*. Journal of Finance. DOI: [10.1111/jofi.12845](https://doi.org/10.1111/jofi.12845)
2. Boons, M., & Prado, M. P. *Basis-Momentum*. Journal of Finance. DOI: [10.1111/jofi.12738](https://doi.org/10.1111/jofi.12738)
3. Fontaine, J.-S., Garcia, R., & Gungor, S. *Intermediary Leverage Shocks and Funding Conditions*. Journal of Finance. DOI: [10.1111/jofi.13407](https://doi.org/10.1111/jofi.13407)
4. Fan, J. H., Fernandez-Perez, A., Fuertes, A., & Miffre, J. *Speculative Pressure*. Journal of Futures Markets. DOI: [10.1002/fut.22085](https://doi.org/10.1002/fut.22085)

### Behavioral and information mechanisms

5. Hirshleifer, D. *Investor Psychology and Asset Pricing*. Journal of Finance. DOI: [10.1111/0022-1082.00379](https://doi.org/10.1111/0022-1082.00379)
6. Daniel, K., Hirshleifer, D., & Subrahmanyam, A. *Investor Psychology and Security Market Under- and Overreactions*. Journal of Finance. DOI: [10.1111/0022-1082.00077](https://doi.org/10.1111/0022-1082.00077)
7. Hong, H., & Stein, J. C. *A Unified Theory of Underreaction, Momentum Trading, and Overreaction*. Journal of Finance. DOI: [10.1111/0022-1082.00184](https://doi.org/10.1111/0022-1082.00184)
8. Detzel, A., Liu, H., Strauss, J., Zhou, G., & Zhu, Y. *Learning and Predictability via Technical Analysis*. Financial Management. DOI: [10.1111/fima.12310](https://doi.org/10.1111/fima.12310)
9. Chen, X., An, L., Wang, Z., & Yu, J. *Attention Spillover in Asset Pricing*. Journal of Finance. DOI: [10.1111/jofi.13281](https://doi.org/10.1111/jofi.13281)
10. Della Vedova, J., Grant, A., & Westerholm, P. J. *Who Drives Momentum Returns?* European Financial Management. DOI: [10.1111/eufm.70023](https://doi.org/10.1111/eufm.70023)

### Relative value and arbitrage

11. Siriwardane, E. N., Sunderam, A., & Wallen, J. *Segmented Arbitrage*. Journal of Finance. DOI: [10.1111/jofi.13469](https://doi.org/10.1111/jofi.13469)
12. Bhanot, K., & Guo, L. *Types of Liquidity and Limits to Arbitrage*. Journal of Futures Markets. DOI: [10.1002/fut.20518](https://doi.org/10.1002/fut.20518)
13. Kondor, P. *Risk in Dynamic Arbitrage*. Journal of Finance. DOI: [10.1111/j.1540-6261.2009.01445.x](https://doi.org/10.1111/j.1540-6261.2009.01445.x)
14. Gromb, D., & Vayanos, D. *The Dynamics of Financially Constrained Arbitrage*. Journal of Finance. DOI: [10.1111/jofi.12689](https://doi.org/10.1111/jofi.12689)
15. Chen, J., Cai, C. X., Faff, R., & Shin, Y. *Nonlinear Limits to Arbitrage*. Journal of Futures Markets. DOI: [10.1002/fut.22320](https://doi.org/10.1002/fut.22320)
16. Figlewski, S. *Derivatives Valuation Based on Arbitrage: The Trade Is Crucial*. Journal of Futures Markets. DOI: [10.1002/fut.21806](https://doi.org/10.1002/fut.21806)

### Liquidity provision and execution

17. Zaharudin, K. Z., Young, M. R., & Hsu, W. *High-Frequency Trading: Definition, Implications, and Controversies*. Journal of Economic Surveys. DOI: [10.1111/joes.12434](https://doi.org/10.1111/joes.12434)
18. Kelley, E. K., & Tetlock, P. C. *How Wise Are Crowds?* Journal of Finance. DOI: [10.1111/jofi.12028](https://doi.org/10.1111/jofi.12028)
19. Battalio, R., Corwin, S. A., & Jennings, R. *Can Brokers Have It All?* Journal of Finance. DOI: [10.1111/jofi.12422](https://doi.org/10.1111/jofi.12422)
20. Dixon, M. *A High-Frequency Trade Execution Model for Supervised Learning*. High Frequency. DOI: [10.1002/hf2.10016](https://doi.org/10.1002/hf2.10016)
21. Easley, D., López de Prado, M., & O'Hara, M. *Optimal Execution Horizon*. Mathematical Finance. DOI: [10.1111/mafi.12045](https://doi.org/10.1111/mafi.12045)
22. Muravyev, D. *Order Flow and Expected Option Returns*. Journal of Finance. DOI: [10.1111/jofi.12380](https://doi.org/10.1111/jofi.12380)

### Portfolio and risk-policy value

23. Liu, H. *Optimal Consumption and Investment with Transaction Costs and Multiple Risky Assets*. Journal of Finance. DOI: [10.1111/j.1540-6261.2004.00634.x](https://doi.org/10.1111/j.1540-6261.2004.00634.x)
24. Happersberger, D., Lohre, H., & Nolte, I. *Estimating Portfolio Risk for Tail Risk Protection Strategies*. European Financial Management. DOI: [10.1111/eufm.12256](https://doi.org/10.1111/eufm.12256)
25. DeMiguel, V., Martín-Utrera, A., & Uppal, R. *A Multifactor Perspective on Volatility-Managed Portfolios*. Journal of Finance. DOI: [10.1111/jofi.13395](https://doi.org/10.1111/jofi.13395)
26. Taylor, N. *Optimal Variance Forecasting in a Trading Context*. Journal of Forecasting. DOI: [10.1002/for.70063](https://doi.org/10.1002/for.70063)
