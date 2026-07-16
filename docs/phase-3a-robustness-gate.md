# Phase 3A — statistical robustness gate

## Purpose

Phase 3A sits between historical model screening and any prospective paper ledger.
A candidate that looks profitable in one sealed backtest is not enough: repeated
experimentation, serial dependence, unstable folds and concentrated profits can all
create false confidence.

This gate is research-only. Passing it creates a **human freeze-review candidate**;
it never activates paper or live trading.

## Predeclared checks

The authoritative policy is `configs/phase3a_robustness.yaml`. Each non-benchmark
model is evaluated against the trend baseline using:

1. positive total sealed net return;
2. Probabilistic Sharpe Ratio (PSR);
3. Deflated Sharpe Ratio (DSR), with a declared trial-family count;
4. one-sided circular block-bootstrap significance for candidate-minus-benchmark
   mean returns, including a positive 95% confidence-interval lower bound;
5. at least half of sealed folds profitable;
6. bounded concentration of positive profit in the best one and best three folds;
7. positive mean net return at twice the declared trading costs;
8. descriptive results under fixed volatility/trend regimes.

The trial count covers the wider model/ablation research family, not only the final
all-features table. Lowering it after observing results is prohibited.

## Inputs

The assessment consumes immutable outputs from a successful fixed-cutoff historical
run:

- `benchmark/all_features/predictions.csv.gz`;
- `benchmark/all_features/cost_stress.csv`;
- `ablation_fold_metrics.csv`.

Predictions must be unique and fully aligned by model, fold and timestamp. The script
fails closed on missing 2x-cost rows, underdeclared trials, non-finite returns or
misaligned benchmark histories.

## Outputs

```text
phase3a-robustness/
├── robustness_summary.csv
├── regime_summary.csv
├── robustness_assessment.json
└── prospective_decisions.jsonl
```

`prospective_decisions.jsonl` is deliberately created empty. Even when a candidate
passes every rule, the output status is `candidate_requires_human_freeze_review` and
`automatic_promotion_allowed` remains `false`.

## Command

```bash
python scripts/assess_phase3a_robustness.py \
  --predictions artifacts/phase2c-historical/benchmark/all_features/predictions.csv.gz \
  --cost-stress artifacts/phase2c-historical/benchmark/all_features/cost_stress.csv \
  --trial-metrics artifacts/phase2c-historical/ablation_fold_metrics.csv \
  --policy configs/phase3a_robustness.yaml \
  --output artifacts/phase3a-robustness
```

## Interpretation

PSR asks whether the true Sharpe is likely positive after accounting for skewness and
kurtosis. DSR raises the benchmark further to reflect repeated trials. The block
bootstrap preserves short-range dependence rather than pretending four-hour returns
are independent. Fold concentration prevents one exceptional period from carrying
the entire conclusion.

These diagnostics do not prove future profitability. They are a stricter rejection
filter before a separately frozen, forward-only paper period.
