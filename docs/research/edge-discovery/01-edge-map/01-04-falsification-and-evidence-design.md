# Report 1.4 — Falsification and Evidence Design

**Program:** Edge Discovery Research Program  
**Section:** 1 — Edge Map  
**Report:** 4 of 5  
**Version:** 1.0  
**Research freeze date:** 2026-07-18  
**Status:** Complete  
**Parents:** [Report 1.1](01-01-edge-definition-and-proof-standard.md), [Report 1.2](01-02-taxonomy-of-edge-mechanisms.md), and [Report 1.3](01-03-market-instrument-horizon-competition-capacity-map.md)  
**Decision type:** Binding research-governance protocol

---

## Executive conclusion

Every trading hypothesis is treated as false until it survives a predeclared attempt to reject it.

Historical optimization is allowed to generate hypotheses. It is not allowed to certify them. A candidate can enter prospective testing only when all of the following are true:

1. the economic mechanism, payer, benchmark, information set, action rule, cost model, and failure conditions were frozen before the confirmatory evaluation;
2. the data are point-in-time and the strategy passes explicit timing and leakage controls;
3. every material research choice is recorded in a trial ledger and evaluated as part of the appropriate test family;
4. the candidate survives family-level multiple-testing control, dependence-aware uncertainty estimation, and selection-aware diagnostics;
5. the result remains economically positive under executable prices, conservative costs, delayed execution, failed or partial fills, financing, and capacity scaling;
6. performance is not concentrated in one period, asset, venue, event, or specification;
7. mechanism-specific placebo, negative-control, ablation, perturbation, and replication tests do not contradict the proposed explanation;
8. the code, configuration, data manifest, and decision policy are frozen and hashed before any new outcome is observed;
9. the candidate survives a genuinely forward-only shadow period;
10. operational reliability is established separately from economic evidence.

No single statistic—Sharpe ratio, p-value, Probabilistic Sharpe Ratio, Deflated Sharpe Ratio, Probability of Backtest Overfitting, Superior Predictive Ability, or bootstrap confidence interval—is sufficient. The project uses a **defense in depth** protocol.

A failed candidate is retained. An inconclusive candidate is not promoted. Exploratory results remain exploratory until tested under a new identity on untouched or genuinely new data.

---

## 1. Purpose

Reports 1.1–1.3 established:

- what a genuine edge is;
- the economic mechanisms that can create an edge;
- the market–instrument–horizon combinations in which an independent operator can realistically compete.

Report 1.4 defines how candidate edges must be challenged before Report 1.5 can rank them for replication.

The purpose is not to make false discovery impossible. That is unattainable. The purpose is to make every important source of false confidence visible, measurable, versioned, and capable of rejecting a candidate.

---

## 2. Threat model

The research process is assumed to be vulnerable to the following failure classes.

### 2.1 Time leakage

A feature, label, universe definition, revision, event classification, or price is used before it was actually available.

### 2.2 Selection leakage

Model, feature, horizon, venue, cost, metric, or period choices are influenced by results from the nominal test set.

### 2.3 Trial undercounting

Only the displayed finalists are counted even though many hidden variations were inspected.

### 2.4 Dependence illusion

Thousands of rows are treated as thousands of independent observations despite overlapping labels, serial correlation, common shocks, and cross-sectional dependence.

### 2.5 Benchmark weakness

A candidate is compared with no trade, a weak baseline, or an exposure-mismatched benchmark instead of the strongest feasible alternative.

### 2.6 Execution optimism

Midpoints, candle closes, simultaneous multi-leg fills, permanent maker status, zero rejection, or unlimited depth are assumed.

### 2.7 Cost omission

Spread, slippage, impact, borrow, funding, margin, transfer, conversion, settlement, and operational costs are omitted or understated.

### 2.8 Hidden risk-premium substitution

Crash, liquidity, short-volatility, leverage, stablecoin, exchange, or convergence risk is reported as alpha.

### 2.9 Nonstationarity

A relationship that existed in one market structure or regime is assumed to persist after participants, regulation, technology, liquidity, or contract design change.

### 2.10 Specification fragility

Profit exists only at one parameter, timestamp convention, vendor, start date, bar size, or random seed.

### 2.11 Test reuse

The same historical holdout is reopened until the desired result appears.

### 2.12 Narrative flexibility

The economic story is changed after observing the winning features or periods.

### 2.13 Operational substitution

A profitable simulation is treated as evidence that the runtime can safely submit, cancel, reconcile, and recover orders.

---

## 3. Research state machine

Every hypothesis must occupy exactly one state.

```text
DRAFT
  ↓
REGISTERED
  ↓
IMPLEMENTED
  ↓
EXPLORATORY_SCREENED
  ↓
HISTORICAL_CONFIRMATORY_TESTED
  ↓
PROSPECTIVE_SHADOW
  ↓
PAPER_EXECUTION
  ↓
MINIMAL_LIVE
  ↓
PROMOTED
```

Terminal or nonpromoting states:

```text
REJECTED
INCONCLUSIVE
SUPERSEDED
INVALID_DATA
INVALID_EXECUTION
PROTOCOL_DEVIATION
```

### State rules

- `DRAFT` may change without restriction.
- `REGISTERED` receives an immutable `hypothesis_id`, protocol hash, and trial-family assignment.
- Any material change after registration creates a new version.
- Historical results can promote only to `PROSPECTIVE_SHADOW`.
- Prospective predictive evidence cannot substitute for paper execution reliability.
- Paper reliability cannot substitute for predictive or economic evidence.
- Minimal live deployment is a separate controlled experiment.
- No state transition is automatic.

---

## 4. Pre-analysis plan

A candidate cannot enter confirmatory testing without a machine-readable pre-analysis plan.

### 4.1 Required identity

```yaml
schema_version: "1.0"
hypothesis_id: "HYP-YYYY-NNN"
version: 1
parent_hypothesis_ids: []
created_at: "..."
freeze_at: "..."
status: registered
primary_edge_mechanism: "..."
economic_payer: "..."
reason_for_persistence: "..."
expected_decay_mechanism: "..."
```

### 4.2 Required market contract

```yaml
market:
  asset_class: "..."
  instruments: []
  venues: []
  settlement_currencies: []
  universe_rule: "point-in-time expression"
  liquidity_rule: "..."
  shortability_rule: "..."
  trading_calendar: "..."
  target_capital: 0
  maximum_capacity_to_test: 0
```

### 4.3 Required information contract

Every input must declare:

- source;
- source version;
- event time;
- publication time;
- exchange time;
- retrieval time;
- processing completion time;
- revision policy;
- `available_at`;
- missing-data policy;
- outage policy;
- checksum or snapshot identity.

### 4.4 Required decision contract

The protocol must freeze:

- decision frequency;
- prediction or holding horizon;
- label definition;
- action space;
- threshold-selection procedure;
- position-sizing rule;
- entry and exit logic;
- rebalance policy;
- abstention rule;
- maximum exposure;
- risk override hierarchy.

### 4.5 Required execution contract

The protocol must freeze:

- decision price;
- order submission time;
- order type;
- maker/taker assumptions;
- latency model;
- depth model;
- queue or fill model;
- partial-fill behavior;
- rejection and retry behavior;
- cancellation behavior;
- multi-leg synchronization;
- liquidation or closeout behavior;
- reconciliation semantics.

### 4.6 Required evidence contract

The protocol must name:

- primary benchmark;
- secondary benchmarks;
- primary economic metric;
- secondary diagnostic metrics;
- test family;
- multiple-testing method;
- bootstrap or dependence method;
- cost tiers;
- robustness grid;
- negative controls;
- minimum detectable effect;
- minimum prospective evidence;
- hard kill conditions;
- stopping rules.

A timestamp without an explicit analysis plan is not sufficient preregistration. Detailed pre-analysis plans reduce researcher degrees of freedom more effectively than vague registration ([Chang, Gao, and Li, 2024](https://doi.org/10.1111/1475-679X.12579)).

---

## 5. Trial ledger

### 5.1 Principle

A trial is any result-informed choice that could have produced a different conclusion.

The following all count:

- market;
- asset;
- universe;
- venue;
- data provider;
- sample start or end;
- timeframe;
- feature;
- feature transformation;
- missing-data treatment;
- event filter;
- label;
- horizon;
- model family;
- architecture;
- hyperparameter;
- seed;
- threshold;
- position size;
- cost assumption;
- benchmark;
- metric;
- regime definition;
- inclusion or exclusion rule;
- LLM provider, model, prompt, schema, or retry policy;
- visual inspection that influences the next experiment.

### 5.2 Trial record

```json
{
  "trial_id": "TRL-...",
  "hypothesis_id": "HYP-...",
  "family_id": "FAM-...",
  "parent_trial_id": null,
  "created_at": "...",
  "code_commit": "...",
  "config_hash": "...",
  "data_manifest_hash": "...",
  "selection_stage": "exploratory",
  "choices": {},
  "metrics": {},
  "result_seen_by_researcher": true,
  "promoted": false,
  "failure_reasons": []
}
```

### 5.3 Family definition

Tests belong to the same family when they support substantially the same research claim using overlapping data. Splitting tests across files, agents, branches, or dates does not create independence. Reused empirical settings remain subject to family-level multiple testing even when different researchers perform the tests ([Heath et al., 2023](https://doi.org/10.1111/jofi.13250)).

### 5.4 Fail-closed accounting

- Declared trials may exceed observed trials.
- Declared trials may never be lower.
- Deleted notebooks and failed jobs still count.
- Negative and null results are permanent records.
- Unknown historical experimentation requires a conservative trial-count prior.
- A model produced by automated search inherits the full search budget, not only completed runs.
- A language model proposing many alternatives does not make those alternatives free.

---

## 6. Data and timing falsification

### 6.1 Required timestamps

The system must distinguish:

```text
event_at
published_at
exchange_at
received_at
processing_started_at
processing_completed_at
available_at
decision_at
order_submitted_at
order_acknowledged_at
filled_at
label_available_at
```

The feature-use rule is:

\[
available\_at \le decision\_at
\]

The label-use rule is:

\[
label\_available\_at \le training\_boundary
\]

### 6.2 Point-in-time universe

Historical membership must use the instruments eligible at each decision time. Present-day survivors, current index members, and current liquidity rankings cannot be backfilled.

### 6.3 Revision control

Revised macro data, corporate classifications, address labels, exchange mappings, article corrections, and vendor history must be stored as vintages. If the historical vintage cannot be recovered, the feature is either excluded or explicitly marked as a research limitation.

### 6.4 Timestamp negative controls

Every data pipeline must run:

1. **future-shift positive control** — intentionally use a future value and verify that the leak detector identifies it;
2. **availability-delay control** — delay the feature and verify that decisions change only after the delayed availability;
3. **lead/lag sweep** — genuine economic effects should not peak at impossible future leads;
4. **timezone shift test** — shift boundaries and inspect whether profitability depends on arbitrary calendar alignment;
5. **duplicate and stale-value test** — detect repeated vendor rows and forward-filled unavailable observations;
6. **cross-venue synchronization test** — account for exchange clock and receive-time differences.

The intentionally cheating control is not a candidate strategy. It is a unit test proving that the research system is capable of detecting leakage.

---

## 7. Historical validation design

### 7.1 Chronological partitions

Random row-level cross-validation is prohibited for trading confirmation.

The default hierarchy is:

```text
training
embargo
calibration
validation
embargo
sealed test
```

### 7.2 Role separation

- Training estimates model parameters.
- Calibration maps scores to probabilities or risk estimates.
- Validation selects thresholds and prespecified model variants.
- Test estimates the frozen candidate once.
- The test set cannot be used for additional feature, model, threshold, or benchmark selection.

### 7.3 Rolling or expanding windows

The protocol must predeclare either:

- expanding training, suitable when older data remain relevant;
- rolling training, suitable when structural decay is expected;
- both as separate confirmatory specifications, counted in the trial family.

### 7.4 Purging and embargo

Rows must be purged whenever their information, holding, or label intervals overlap a later partition.

The embargo must cover at least the maximum relevant interval among:

- decision-to-entry delay;
- holding horizon;
- outcome-maturity horizon;
- delayed label publication;
- overlapping portfolio state;
- known vendor revision lag.

### 7.5 Panel data

For multi-asset data:

- time must remain ordered;
- cross-sectional observations at one time are not independent bets;
- universe membership is point-in-time;
- shared market shocks require date clustering or block resampling;
- the same issuer or token across venues must not appear in conflicting partitions through aliases.

Random K-fold validation on temporal or panel data can leak future information and materially inflate fit; time-respecting cross-validation and gaps are required ([Cerqua, Letta, and Pinto, 2025](https://doi.org/10.1111/obes.70019)).

### 7.6 Historical holdout is not fresh data

A sealed historical test is stronger than ordinary model selection, but the researcher may already know broad events and market behavior. Completely fresh observations remain the strongest practical protection against hindsight and sample-selection bias. Exact published technical rules have often failed when applied to genuinely new periods ([Fang, Jacobsen, and Qin, 2013](https://doi.org/10.1016/j.rfe.2013.05.004)).

---

## 8. Multiple-testing protocol

### 8.1 Why one p-value is invalid

The distribution of the best result selected from many trials is not the distribution of a randomly selected result. With enough attempts, the maximum observed Sharpe ratio can become arbitrarily impressive even when all true Sharpes are zero. DSR adjusts for sample length, non-normality, and selection, but remains a diagnostic rather than proof ([Bailey and López de Prado, 2021](https://doi.org/10.1111/1740-9713.01588)).

### 8.2 Methods and roles

| Method | Question | Strength | Limitation | Project role |
|---|---|---|---|---|
| White Reality Check | Does any tested candidate beat the benchmark? | Family-level null | Can be conservative with poor models | Exploratory family screen |
| Superior Predictive Ability | Does the best candidate outperform while reducing poor-model influence? | Better power than basic reality check | Requires valid loss and bootstrap | Primary exploratory family test |
| Stepwise SPA / Romano–Wolf | Which candidates survive FWER control? | Controls probability of any false promotion | Lower power | Confirmatory finalist gate |
| FDR / FDP control | What share of discoveries may be false? | Useful for broad hypothesis generation | Permits some false discoveries | Exploratory ranking only |
| Model Confidence Set | Which models cannot be statistically distinguished? | Avoids forced single winner | Does not prove profitability | Candidate-set reporting |
| PSR | Is true Sharpe likely above a benchmark? | Handles skew and kurtosis | Not selection-aware by itself | Diagnostic |
| DSR | Does Sharpe survive selection adjustment? | Uses trial family and non-normality | Sensitive to trial accounting | Required diagnostic |
| PBO / CSCV | Does in-sample rank reverse out of sample? | Direct overfit diagnostic | Needs enough partitions and comparable strategies | Required when applicable |
| Block bootstrap | Is improvement robust under dependence? | Preserves local dependence | Block length uncertainty | Required uncertainty method |

### 8.3 Project policy

For broad exploratory families:

- use a family-level SPA or equivalent dependence-aware test;
- report FDR or FDP-controlled discoveries;
- report DSR and PBO when estimable;
- do not promote directly.

For confirmatory finalists:

- freeze a small candidate set;
- use stepdown FWER control at a predeclared level, normally 5%;
- use the primary economic metric only for the promotion decision;
- retain secondary metrics as diagnostics;
- require a positive lower confidence bound relative to the benchmark.

No method is allowed to rescue a candidate that fails executable net economics.

---

## 9. Negative controls and placebos

All controls must be registered and all outcomes reported. Placebos themselves are vulnerable to selective reporting ([Dreber, Johannesson, and Yang, 2024](https://doi.org/10.1111/ecin.13217)).

### 9.1 Signal controls

- block-permuted signal;
- random signal matched on exposure, turnover, and holding time;
- sign-flipped signal;
- delayed signal;
- stale signal;
- irrelevant-variable signal;
- feature values permuted within appropriate time and cross-sectional blocks.

### 9.2 Outcome controls

- impossible future horizon;
- pre-decision outcome;
- unrelated asset outcome;
- placebo event dates;
- nontradable reference price outcome.

### 9.3 Strategy controls

- no-trade;
- passive exposure;
- trend or carry baseline;
- randomized entry with matched exits;
- randomized exit with matched entries;
- same exposure with naive sizing;
- same signal with no abstention.

### 9.4 Data-source controls

- leave one provider out;
- leave one venue out;
- delayed provider arrival;
- source text without semantic transformation;
- neutral semantic baseline;
- hash-randomized document assignment.

### 9.5 Expected behavior

A valid candidate should:

- outperform matched random strategies;
- lose performance when the economically essential feature is removed;
- not gain performance from future or impossible timestamps;
- not depend on one arbitrary provider or bar boundary;
- show degradation consistent with the proposed mechanism when information is delayed.

Unexpected placebo success is a reason to investigate or reject, not a reason to invent a second story.

---

## 10. Robustness and specification analysis

### 10.1 Parameter neighborhoods

The candidate should occupy a stable region, not a single optimum.

Test:

- neighboring lookbacks;
- neighboring thresholds;
- neighboring holding periods;
- alternative but plausible rebalancing times;
- modest changes in position sizing;
- alternative random seeds;
- alternative regularization within the frozen family.

### 10.2 Specification curve

Report every plausible specification in the registered multiverse, ordered by effect size, with:

- net effect;
- uncertainty;
- costs;
- turnover;
- exposure;
- sample size;
- specification choices.

The conclusion must not depend on selectively displaying the winning specification.

### 10.3 Ablation

Perform:

- leave-one-feature-out;
- leave-one-feature-family-out;
- leave-one-source-out;
- leave-one-asset-out;
- leave-one-venue-out;
- leave-one-regime-out;
- simple-model replacement;
- no-LLM or keyword-baseline replacement where relevant.

### 10.4 Temporal robustness

Evaluate:

- nonoverlapping subperiods;
- rolling windows;
- different start dates;
- pre- and post-structural changes;
- crisis and calm periods;
- high and low liquidity;
- bull, bear, and sideways states;
- weekends and market-session differences where applicable.

### 10.5 Cross-market replication

A mechanism receives greater prior credibility when it appears in economically related markets. Failure to transfer does not automatically reject a venue-specific edge, but the mechanism must explain the boundary.

### 10.6 Researcher-choice uncertainty

Different competent analysts can produce materially different results from the same hypothesis and data. Multi-analyst evidence in finance shows sizable “nonstandard errors,” reduced but not eliminated by peer feedback ([Menkveld et al., 2024](https://doi.org/10.1111/jofi.13337)).

For major candidates, require either:

- an independent second implementation;
- a blinded internal replication;
- or a code and protocol review by an agent that did not select the candidate.

---

## 11. Economic and execution falsification

### 11.1 All-in return

\[
R^{net}
=
R^{gross}
-C_{commission}
-C_{spread}
-C_{slippage}
-C_{impact}
-C_{funding}
-C_{borrow}
-C_{margin}
-C_{transfer}
-C_{conversion}
-C_{settlement}
-C_{operational}
\]

### 11.2 Decision-price benchmark

Execution must be measured from the price available when the decision was made, not from a later convenient quote.

Implementation shortfall includes:

- explicit execution cost;
- market impact;
- information leakage;
- opportunity cost from delayed or failed trading.

This is the correct bridge between paper performance and realizable signal value ([O'Neill, Warren, and Smith, 2017](https://doi.org/10.1111/acfi.12268)).

### 11.3 Cost tiers

Every candidate must report:

```text
C0: frictionless diagnostic only
C1: observed or best-estimate deployable cost
C2: conservative stress, normally 1.5x–2x C1
C3: severe stress, normally 3x C1 plus delay and fill degradation
CBE: break-even all-in cost
```

C0 can diagnose the statistical signal but cannot support promotion.

The default historical admission rule is:

- positive net value at C1;
- nonnegative net value at C2;
- break-even cost materially above C1;
- no hidden assumption that rebates are guaranteed.

Exact multipliers must be justified and frozen per hypothesis.

### 11.4 Delay ladder

Evaluate the same decision under:

- minimum feasible latency;
- median observed latency;
- high-percentile latency;
- one additional bar or decision interval where economically relevant;
- outage recovery delay.

A candidate that disappears under a plausible delay is an infrastructure-dependent edge and must be classified accordingly.

### 11.5 Fill ladder

Evaluate:

- full immediate fill;
- depth-limited market fill;
- partial fill;
- no fill;
- maker fill conditional on queue and market movement;
- post-only rejection;
- cancel-replace;
- multi-leg orphan fill;
- exchange rejection.

Maker rebates cannot be counted unless the simulator models fill probability and adverse selection.

### 11.6 Financing and derivative costs

Depending on instrument, include:

- realized funding at each payment time;
- borrow availability and fee;
- futures roll and basis;
- initial and maintenance margin;
- liquidation and bankruptcy price;
- insurance fund and auto-deleveraging;
- option exercise, assignment, settlement, and hedging;
- stablecoin or collateral basis.

Short-sale costs can eliminate apparently persistent equity anomalies even before ordinary execution costs ([Muravyev, Pearson, and Pollet, 2025](https://doi.org/10.1111/jofi.13501)).

### 11.7 Capacity curve

Evaluate net performance as a function of deployable capital:

\[
q \mapsto Edge(q)
\]

At each size report:

- participation rate;
- days or intervals to trade;
- predicted impact;
- fill rate;
- concentration;
- required margin;
- implementation shortfall;
- opportunity cost;
- net utility.

Price impact is generally nonlinear, and ignoring it can reverse strategy or model rankings ([Brokmann et al., 2024](https://doi.org/10.1111/mafi.12449); [Detzel, Novy-Marx, and Velikov, 2023](https://doi.org/10.1111/jofi.13225)).

---

## 12. Performance and risk metrics

### 12.1 Primary decision metric

Each protocol must define one primary economic metric, such as:

- benchmark-relative net mean return;
- certainty-equivalent return;
- downside-penalized utility;
- net information ratio;
- net Calmar ratio under a risk ceiling.

The metric must match the strategy's intended use.

### 12.2 Required diagnostics

Report at least:

- gross and net return;
- annualized volatility;
- Sharpe and DSR;
- Sortino or downside deviation;
- maximum drawdown;
- Calmar;
- VaR and Expected Shortfall;
- skewness and kurtosis;
- turnover;
- total and component costs;
- exposure;
- leverage;
- hit rate;
- average win and loss;
- time under water;
- PnL by asset, fold, venue, and regime;
- concentration of positive PnL;
- effective number of independent decisions;
- capacity curve.

### 12.3 Predictive metrics

Accuracy, AUC, Brier score, log loss, calibration error, MAE, or RMSE remain secondary unless the hypothesis is explicitly a forecast-service edge. Predictive improvement does not imply economic improvement.

### 12.4 Dependence-aware uncertainty

Use:

- circular or stationary block bootstrap;
- moving block bootstrap;
- HAC estimates;
- time clustering;
- date and asset clustering for panels;
- regime-aware resampling where justified.

The block length or dependence structure must be frozen or selected by a predeclared rule.

---

## 13. Profit concentration

A candidate is fragile when most profit comes from:

- one fold;
- one asset;
- one venue;
- one event;
- one direction;
- one volatility regime;
- one parameter;
- one short crisis period.

Required diagnostics include:

- top-one positive-profit share;
- top-three positive-profit share;
- Herfindahl concentration;
- leave-one-unit-out result;
- count of profitable independent units;
- largest-loss and largest-gain contribution.

Concentration thresholds are hypothesis-specific. For diversified strategies, the protocol should normally require a majority of independent units to contribute positively and prevent one unit from determining the conclusion. A truly event-driven strategy may legitimately be sparse, but it then requires a longer prospective period and event-level replication rather than pretending dense evidence.

---

## 14. Power, failure, and inconclusiveness

### 14.1 Three possible outcomes

```text
PASS
FAIL
INCONCLUSIVE
```

### 14.2 Fail

A result is `FAIL` when:

- a hard validity gate is violated;
- the primary net effect is negative;
- the candidate fails predeclared family-level inference;
- plausible costs eliminate the effect;
- the mechanism-specific control contradicts the hypothesis;
- performance violates the risk ceiling;
- the test set was reused;
- protocol deviations make confirmation invalid.

### 14.3 Inconclusive

A result is `INCONCLUSIVE` when:

- too few independent decisions exist;
- required regimes or events did not occur;
- confidence intervals are too wide;
- data quality is insufficient;
- the prospective period ended without adequate maturity;
- operational incidents prevent fair assessment.

Inconclusive is not a partial pass.

### 14.4 Power planning

There is no universal minimum number of bars or trades.

The protocol must estimate:

- minimum economically relevant net edge;
- variance and dependence;
- effective sample size;
- event frequency;
- target Type I error;
- target power;
- maximum acceptable duration.

Elapsed time, independent decisions, and regime coverage must all be considered. Adding correlated intraday rows does not automatically create more evidence.

---

## 15. Prospective protocol

### 15.1 Freeze package

Before the first prospective decision, create:

```text
protocol.yaml
protocol.sha256
code-manifest.json
data-source-manifest.json
environment-lock.json
model-artifact-manifest.json
benchmark-manifest.json
cost-policy.yaml
risk-policy.yaml
```

### 15.2 Decision ledger

Every decision must be written before its outcome is known:

```json
{
  "decision_id": "...",
  "hypothesis_id": "...",
  "protocol_hash": "...",
  "decided_at": "...",
  "information_cutoff": "...",
  "instrument": "...",
  "venue": "...",
  "signal": {},
  "desired_position": 0,
  "benchmark_position": 0,
  "estimated_cost": 0,
  "risk_overrides": [],
  "outcome_matures_at": "..."
}
```

### 15.3 No silent adaptation

During confirmatory collection:

- model weights are frozen unless online updating was predeclared;
- thresholds are frozen;
- source inclusion rules are frozen;
- prompts and semantic schemas are frozen;
- bug fixes are documented;
- material changes create a new hypothesis version;
- old and new ledgers are never merged as one experiment.

### 15.4 Outcome maturity

Outcomes may be evaluated only after `outcome_matures_at`. Pending rows remain pending. Missing outcomes and market outages are reported, not silently removed.

### 15.5 Evaluation schedule

Use predeclared checkpoints. Continuous dashboard observation is operationally useful but must not lead to ad hoc stopping or modification.

Early termination is allowed for:

- safety;
- data invalidity;
- runtime failure;
- predeclared futility;
- predeclared risk breach.

### 15.6 Fresh data standard

Prospective evidence begins only after:

- protocol freeze;
- code freeze;
- data contract freeze;
- candidate and benchmark freeze.

Backfilling historical data after freeze remains historical evidence, not prospective evidence.

---

## 16. Shadow, paper, and live evidence

### 16.1 Shadow stage

Purpose:

- test new data;
- record decisions;
- measure expected economics;
- avoid sending orders.

It does not test actual fill or account state.

### 16.2 Paper execution stage

Purpose:

- test order state machines;
- fill assumptions;
- latency;
- partial fills;
- reconciliation;
- state recovery;
- risk controls;
- monitoring.

A paper broker must not simply fill every order at the next candle price.

### 16.3 Minimal live stage

Purpose:

- measure actual implementation shortfall and operational behavior with economically insignificant capital.

Default restrictions:

- no withdrawal permission;
- no leverage unless the instrument cannot be tested otherwise and the limit is explicit;
- no unbounded short;
- strict exposure ceiling;
- daily and total loss ceilings;
- manual kill switch;
- automated stale-data and reconciliation stops;
- isolated account;
- complete audit log.

### 16.4 Separate promotion gates

A candidate requires both:

```text
economic_evidence_passed
AND
operational_reliability_passed
```

Neither substitutes for the other.

---

## 17. Mechanism-specific falsification

### 17.1 Directional forecasting

Required:

- passive and trend baselines;
- cost-aware abstention;
- delay ladder;
- calibration;
- magnitude as well as direction;
- random signal matched on turnover;
- regime and class-balance analysis.

Kill if accuracy improves but net utility does not.

### 17.2 Carry, funding, and basis

Required:

- decomposition into carry and mark-to-market;
- realistic funding schedule;
- spot and derivative leg execution;
- collateral yield;
- margin and liquidation;
- depeg and venue failure stress;
- crowding and capacity.

Kill if profit is only compensation for unbounded tail or counterparty risk.

### 17.3 Relative value and convergence

Required:

- executable bid and ask on all legs;
- asynchronous leg risk;
- structural break and cointegration decay;
- borrowing or shortability;
- convergence horizon;
- stop and capital call;
- no-convergence scenario.

Kill if simultaneous midprice fills create most profit.

### 17.4 Cross-sectional factors

Required:

- point-in-time universe;
- delisting and survivorship;
- borrow and short fees;
- value weighting and liquidity screens;
- industry and beta controls;
- turnover-minimized implementation;
- post-publication and recent-period tests.

Kill if the result exists only in illiquid or unshortable observations.

### 17.5 Liquidity provision

Required:

- queue model;
- fill probability;
- adverse selection;
- inventory path;
- cancellation latency;
- fee/rebate schedule;
- post-fill markout;
- stress withdrawal of liquidity.

Kill if spread capture is measured without markout and inventory loss.

### 17.6 Options and volatility

Required:

- clean quotes and surface construction;
- bid–ask execution;
- delta-hedge timing and cost;
- exercise and assignment;
- margin;
- jump and volatility-of-volatility;
- tail stress;
- comparison with simpler variance exposure.

Kill if profits rely on midpoint options, continuous hedging, or hidden short-convexity risk.

### 17.7 On-chain and decentralized finance

Required:

- block and confirmation timing;
- gas;
- slippage;
- oracle;
- miner/validator or maximum-extractable-value competition;
- bridge and smart-contract risk;
- protocol governance;
- stablecoin and collateral;
- failed and reverted transactions.

Kill if the opportunity depends on winning a same-block race without matching infrastructure.

---

## 18. Current repository audit

The existing project already contains several strong components:

- chronological sealed folds with separate training, calibration, validation, and test partitions;
- label availability purging;
- next-bar execution for the simple baseline;
- explicit one-way trading costs and turnover;
- PSR and DSR;
- declared trial count;
- circular block bootstrap;
- fold-profit concentration;
- fixed 2x cost stress;
- regime summaries;
- fail-closed alignment checks;
- no automatic promotion;
- immutable evidence hashes;
- an empty prospective ledger unless a candidate passes.

The Phase 3A gate correctly rejected all candidates and treated a nominally profitable prior as insufficient after selection, dependence, fold concentration, and cost checks.

### 18.1 Strengths to retain

- typed frozen policies;
- declared thresholds;
- immutable artifacts;
- benchmark alignment;
- positive confidence-bound requirement;
- underdeclared-trial failure;
- human freeze review;
- prospective separation.

### 18.2 Gaps to close

The existing Phase 3A gate is not yet the complete program standard. It needs:

1. explicit hypothesis and family registries;
2. automated registration of all research trials;
3. SPA or equivalent family-level candidate testing;
4. FWER control for confirmatory finalists;
5. PBO when the partition structure permits;
6. mandatory negative controls and placebos;
7. specification-curve output;
8. broader execution and cost ladders;
9. capacity curves;
10. independent replication;
11. prospective protocol hashes;
12. paper fill and implementation-shortfall calibration;
13. formal `FAIL` versus `INCONCLUSIVE`;
14. mechanism-specific test profiles.

---

## 19. Engineering lessons from open-source systems

Freqtrade's `lookahead-analysis` reruns sliced signal backtests and compares indicator and decision outputs with the full baseline. This is useful because vectorized backtests can expose the entire dataframe to an indicator. Its documentation also states the limitation: untriggered signals may yield false negatives and limit-order behavior can create false positives. Therefore lookahead analysis is a required diagnostic, not proof of temporal validity.

Freqtrade's `recursive-analysis` compares indicator values under different startup-history lengths. This addresses a real research-to-live mismatch: recursive indicators calculated from a full history can differ from indicators calculated with the limited history available from a live exchange.

NautilusTrader's shared event-driven time and execution semantics across research and live environments provide the preferred architectural principle: a strategy should not be rewritten into a different model of time, order state, accounting, or fill when deployed.

### Project consequence

The final system should combine:

- vectorized research for exploration;
- event-driven replay for confirmation;
- identical decision and order semantics for paper and live;
- explicit diagnostics for lookahead and recursive instability.

---

## 20. Required artifact layout

```text
research/hypotheses/HYP-YYYY-NNN/
├── protocol.yaml
├── protocol.sha256
├── hypothesis-card.md
├── trial-ledger.jsonl
├── family-manifest.json
├── data-manifest.json
├── code-manifest.json
├── environment-lock.json
├── historical/
│   ├── exploratory-summary.json
│   ├── confirmatory-summary.json
│   ├── multiple-testing.json
│   ├── negative-controls.json
│   ├── robustness-curve.csv
│   ├── ablations.csv
│   ├── cost-ladder.csv
│   ├── delay-fill-ladder.csv
│   ├── capacity-curve.csv
│   └── verdict.json
├── prospective/
│   ├── decision-ledger.jsonl
│   ├── outcome-ledger.jsonl
│   ├── incidents.jsonl
│   ├── checkpoints/
│   └── verdict.json
├── paper/
│   ├── orders.jsonl
│   ├── fills.jsonl
│   ├── reconciliation.jsonl
│   ├── implementation-shortfall.csv
│   ├── incidents.jsonl
│   └── verdict.json
└── minimal-live/
    ├── approvals.jsonl
    ├── orders.jsonl
    ├── fills.jsonl
    ├── reconciliation.jsonl
    ├── risk-events.jsonl
    ├── incidents.jsonl
    └── verdict.json
```

---

## 21. Required schemas

### 21.1 Hypothesis protocol

```python
class HypothesisProtocol:
    hypothesis_id: str
    version: int
    primary_mechanism: str
    payer: str
    persistence_reason: str
    universe_rule: str
    information_contract: dict
    decision_contract: dict
    execution_contract: dict
    benchmark_contract: dict
    cost_contract: dict
    test_family_id: str
    primary_metric: str
    multiple_testing_method: str
    negative_controls: list[str]
    robustness_tests: list[str]
    prospective_stop_rules: dict
    hard_kill_rules: list[str]
```

### 21.2 Verdict

```json
{
  "hypothesis_id": "HYP-...",
  "protocol_hash": "...",
  "stage": "historical_confirmatory",
  "verdict": "pass|fail|inconclusive",
  "automatic_promotion_allowed": false,
  "hard_gate_results": {},
  "statistical_results": {},
  "economic_results": {},
  "risk_results": {},
  "control_results": {},
  "failed_rules": [],
  "unresolved_limitations": [],
  "next_allowed_action": "..."
}
```

---

## 22. Required commands

The future research CLI should expose:

```text
hybrid-trader hypothesis create
hybrid-trader hypothesis freeze
hybrid-trader trial record
hybrid-trader data audit
hybrid-trader leakage check
hybrid-trader recursive check
hybrid-trader family spa
hybrid-trader family fwer
hybrid-trader candidate dsr
hybrid-trader candidate pbo
hybrid-trader controls run
hybrid-trader robustness run
hybrid-trader costs run
hybrid-trader capacity run
hybrid-trader prospective start
hybrid-trader prospective mature
hybrid-trader paper reconcile
hybrid-trader verdict build
hybrid-trader evidence verify
```

Every command must be deterministic from immutable inputs and emit a content-addressed manifest.

---

## 23. Promotion and kill matrix

| Gate | Pass requirement | Fail result |
|---|---|---|
| Protocol | Complete and frozen before confirmatory outcome | Invalid experiment |
| Timing | No availability or label leakage | Reject |
| Trial ledger | Family complete and conservative | Reject or reclassify exploratory |
| Benchmark | Strong feasible benchmark | Invalid comparison |
| Multiple testing | Predeclared family-level rule passed | Reject |
| Dependence | Dependence-aware lower bound positive | Reject or inconclusive |
| Net economics | Positive at deployable base cost | Reject |
| Cost stress | Survives conservative stress | Reject |
| Delay/fill | Survives plausible execution | Reject |
| Capacity | Positive at target capital | Reject target deployment |
| Concentration | Within mechanism-specific limit | Reject or extend evidence |
| Negative controls | Behave as predeclared | Reject or investigate |
| Robustness | Stable neighborhood and specifications | Reject |
| Mechanism | Ablation and regime evidence coherent | Lower credibility or reject |
| Fresh data | Prospective protocol passed | No live promotion |
| Paper reliability | State and reconciliation gates passed | No live promotion |
| Minimal live | Risk and implementation gates passed | Stop |

---

## 24. Default policy values

These defaults are starting governance values, not universal laws. A hypothesis may override them only before outcome observation and with justification.

```yaml
confirmatory_fwer: 0.05
exploratory_fdr: 0.10
minimum_psr: 0.95
minimum_dsr: 0.95
maximum_pbo: 0.10
bootstrap_confidence: 0.95
require_positive_ci_lower_bound: true
require_positive_base_cost: true
require_nonnegative_conservative_cost: true
conservative_cost_multiplier: 2.0
severe_cost_multiplier: 3.0
automatic_promotion_allowed: false
```

The number of independent observations, fold thresholds, concentration limits, and minimum prospective duration must be selected from the hypothesis mechanism and power analysis rather than copied blindly.

---

## 25. Decision algorithm

```python
def assess_hypothesis(hypothesis):
    require_frozen_protocol(hypothesis)
    require_complete_trial_family(hypothesis)
    audit_point_in_time_data(hypothesis)
    run_leakage_and_recursive_controls(hypothesis)

    if any_hard_validity_failure():
        return FAIL

    run_nested_historical_selection()
    run_once_on_sealed_confirmatory_test()
    run_family_level_multiple_testing()
    run_selection_aware_diagnostics()
    run_negative_controls()
    run_specification_curve()
    run_ablation_and_regime_tests()
    run_cost_delay_fill_and_capacity_ladders()

    if any_predeclared_kill_rule():
        return FAIL

    if evidence_is_underpowered_or_regimes_missing():
        return INCONCLUSIVE

    freeze_code_model_and_runtime_policy()
    start_forward_only_shadow_ledger()

    if prospective_kill_rule():
        return FAIL
    if prospective_evidence_insufficient():
        return INCONCLUSIVE

    run_event_driven_paper_execution()
    if operational_reliability_fails():
        return FAIL

    authorize_minimal_live_experiment_only_after_human_review()
```

---

## 26. Inputs to Report 1.5

Report 1.5 may rank a candidate mechanism only if the candidate can be expressed as a falsifiable hypothesis card containing:

- mechanism;
- payer;
- market;
- instrument;
- horizon;
- data contract;
- execution contract;
- strongest benchmark;
- negative controls;
- trial family;
- cost and capacity plan;
- prospective duration;
- kill criteria.

Report 1.5 must not select a model architecture. It will select a small set of **economic hypotheses worthy of replication**.

---

## 27. Binding conclusions

1. Every candidate is presumed false until it survives an explicit rejection program.
2. Historical backtests can reject and prioritize; they cannot prove live edge.
3. Trial families include hidden and human-guided exploration.
4. The sealed test is single-use.
5. Fresh prospective data are mandatory.
6. Multiple-testing methods are complementary, not interchangeable decorations.
7. Net economics and execution validity dominate prediction scores.
8. Placebos and negative controls are mandatory and permanently logged.
9. A stable parameter region is required; an isolated optimum is not credible.
10. A paper broker must simulate order states and failed execution, not only prices.
11. Economic and operational evidence are separate gates.
12. `INCONCLUSIVE` never permits promotion.
13. Protocol deviations create a new experiment identity.
14. Negative evidence remains part of project memory.
15. The valid final outcome may be to reject every candidate.

---

## 28. Literature foundation

The protocol was informed by four evidence streams.

### Multiple testing and backtest selection

- Bailey and López de Prado, “How backtest overfitting in finance leads to false discoveries” ([2021](https://doi.org/10.1111/1740-9713.01588)).
- Harvey and Liu, “False (and missed) discoveries in financial economics” ([2020](https://doi.org/10.1111/jofi.12951)).
- Esposito and Cummins, dependence-aware multiple-testing applications ([2016](https://doi.org/10.1002/for.2381)).
- Dichtl, large-scale strategy evaluation with SPA controls ([2019](https://doi.org/10.1002/rfe.1078)).
- Tian et al., futures strategies that disappear after data-snooping controls ([2024](https://doi.org/10.1002/ise3.87)).

### Time-respecting and fresh validation

- Fang, Jacobsen, and Qin, true fresh-data tests of technical rules ([2013](https://doi.org/10.1016/j.rfe.2013.05.004)).
- Cerqua, Letta, and Pinto, cross-validation leakage in panel and temporal settings ([2025](https://doi.org/10.1111/obes.70019)).
- Hambuckers and Heuchenne, dependence-preserving bootstrap validation of trading parameterizations ([2015](https://doi.org/10.1002/for.2380)).
- Reschenhofer et al., review of weak economic validation in return-prediction research ([2019](https://doi.org/10.1002/for.2629)).
- Levy, look-ahead contamination in commercial language models used for historical finance tasks ([2026](https://doi.org/10.1111/1475-679x.70058)).

### Costs, execution, and capacity

- O'Neill, Warren, and Smith, capacity and implementation-shortfall methods ([2017](https://doi.org/10.1111/acfi.12268)).
- Detzel, Novy-Marx, and Velikov, model comparison with transaction costs ([2023](https://doi.org/10.1111/jofi.13225)).
- Brokmann et al., nonlinear price impact ([2024](https://doi.org/10.1111/mafi.12449)).
- Muravyev, Pearson, and Pollet, anomaly returns after borrow costs ([2025](https://doi.org/10.1111/jofi.13501)).
- Krauss, market-friction evidence in pairs trading ([2016](https://doi.org/10.1111/joes.12153)).
- Chung, execution lag and cost in apparent index arbitrage ([1991](https://doi.org/10.1111/j.1540-6261.1991.tb04644.x)).

### Preregistration, controls, and researcher discretion

- Chang, Gao, and Li, detailed pre-analysis plans and significance-threshold discretion ([2024](https://doi.org/10.1111/1475-679X.12579)).
- Heath et al., repeated use of one setting as a multiple-testing family ([2023](https://doi.org/10.1111/jofi.13250)).
- Menkveld et al., nonstandard errors across 164 research teams ([2024](https://doi.org/10.1111/jofi.13337)).
- Dreber, Johannesson, and Yang, selective reporting of placebo tests ([2024](https://doi.org/10.1111/ecin.13217)).

---

## 29. Limitations

- No statistical protocol eliminates false discovery.
- Exact dependence and effective sample size are difficult to estimate.
- Some methods, including PBO and DSR, depend materially on honest trial accounting and suitable partitions.
- Preregistration can be vague or strategically incomplete; it must be combined with code, data, and artifact transparency.
- A fresh period can differ because of genuine market evolution, not only because the original result was false.
- Strong robustness may still represent compensation for a risk not yet observed.
- Paper fills cannot reproduce all live queue, counterparty, and outage behavior.
- Small-capital live results do not automatically scale to larger capital.
- Scholar Gateway coverage is broad but not exhaustive; primary papers and replication code must be checked during Section 2.
- Consensus search was unavailable in this session because the monthly tool quota had been exhausted.
- The current report defines the protocol. It does not declare that any current or future candidate has passed it.

---

## Final decision

Report 1.4 is binding on the remaining research program.

The next report, **1.5 — Edge Map Synthesis**, will combine the definition, mechanism taxonomy, market and horizon map, and this falsification protocol. It will rank a small number of economic hypotheses for formal replication and explicitly reject or defer the rest.
