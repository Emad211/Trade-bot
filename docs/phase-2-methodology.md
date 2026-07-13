# Phase 2 methodology: sealed point-in-time evaluation

## Objective

The pipeline asks whether a candidate feature or model adds economic value beyond
simple baselines when evaluated exactly as information would have arrived in real
time. It is designed to reject attractive but contaminated results.

## Information times

For a candle whose index is its opening time:

```text
open_available_at = open_time + source_latency
available_at      = open_time + timeframe + source_latency
```

External data are joined with a backward as-of operation using publication or
availability timestamps—not the economic period they describe.

## Trading label

For decision row `t`, with execution delay `d` and holding period `h`:

```text
entry = Open[t + 1 + d]
exit  = Open[t + 1 + d + h]
target_return = exit / entry - 1
```

The default `d=1`, `h=1` means:

```text
bar t closes
one complete delay bar passes
entry at Open[t+2]
exit at Open[t+3]
```

The label becomes known only when the exit open is observable. Labels crossing a
partition boundary are purged before fitting that partition.

## Sealed fold

```text
expanding train
embargo
calibration
validation
embargo
untouched test
```

- Training fits model parameters.
- Calibration fits Platt scaling.
- Validation selects the probability threshold.
- Test is evaluated once.

Changing a feature, model, prompt, threshold grid, source latency or cost model
after seeing final-test results requires a new sealed test or prospective period.

## Economic mapping

A calibrated probability above the selected threshold creates a Long exposure.
Position size is volatility-targeted and capped. The system is always Long/Flat.

Costs include fee and slippage on every exposure change. Every fold is forcibly
liquidated, and that liquidation is included in turnover and cost. The passive
comparator is charged one entry and one exit.

The vectorized evaluator supports a one-bar holding period only. Multi-bar labels
create overlapping lots and require a portfolio-book simulator with explicit
capital reservation and fill timing.

Threshold utility is:

```text
net_return - drawdown_penalty * abs(max_drawdown)
```

When utility ties, the higher, more conservative threshold wins.

## Required comparisons

- prior probability;
- regularized logistic regression;
- deterministic trend baseline;
- passive buy-and-hold comparator;
- tree/foundation/hybrid candidate;
- 1.0x, 1.5x and 2.0x cost stress;
- incremental and leave-one-group-out ablations.

## Metrics

Probability quality:

- accuracy;
- Brier score;
- log loss;
- ROC AUC;
- expected calibration error;
- predicted and realized positive rate.

Economic quality:

- net and passive return;
- gross passive return;
- annualized volatility;
- Sharpe ratio;
- maximum drawdown;
- turnover and total cost;
- average exposure;
- number of entries.

No model is promoted from accuracy, RMSE, one fold, or one market regime alone.
