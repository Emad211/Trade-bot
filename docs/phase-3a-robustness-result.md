# Phase 3A robustness result

## Decision

The fixed-cutoff Phase 3A gate rejected every evaluated non-trend candidate.

```text
verdict: no_candidate_passed
recommended_action: retain_research_only
automatic_promotion_allowed: false
prospective_ledger_started: false
```

No paper-trading freeze was created and the prospective decision ledger remains empty.

## Provenance

- Historical source run: `29319905230`
- Robustness workflow run: `29488655448`
- Assessed source commit: `71dd40444eba8eae8d0806232a630aa128029785`
- Assessment ID: `96b68029c4ef00111a624f973dd263dea8d75d58e9090e33b74b8d352ee562ee`
- Compact evidence: `research/runs/phase3a-robustness-29488655448/`
- Benchmark: `trend`
- Declared/observed trial families: `40 / 40`
- Sealed observations per candidate: `4,320`

The committed `SHA256SUMS` file covers every compact evidence file. Large upstream
predictions remain in the immutable historical GitHub Actions artifact and are not
copied into Git.

## Candidate summary

| Candidate | Total return | Annualized Sharpe | PSR | DSR | Positive folds | Mean 2x-cost return | Rules passed | Result |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| prior | 5.13% | 0.294 | 0.660 | 0.000000665 | 16.7% | 0.46% | 4 / 10 | rejected |
| ridge_logistic | -17.88% | -0.816 | 0.127 | 0.000000000101 | 25.0% | -3.18% | 1 / 10 | rejected |
| catboost | -38.24% | -2.246 | 0.000927 | approximately 0 | 8.3% | -8.24% | 1 / 10 | rejected |
| lightgbm | -39.59% | -3.456 | 0.000000373 | 0 | 0.0% | -6.39% | 1 / 10 | rejected |

The `prior` candidate was nominally profitable, but its result was not statistically
or economically robust:

- PSR was below the predeclared `0.95` threshold;
- DSR was effectively zero after accounting for repeated trials;
- one-sided block-bootstrap p-value was approximately `0.331`;
- the bootstrap confidence interval crossed zero;
- only one of six folds was profitable;
- about `75.4%` of positive fold profit came from the best fold;
- the top three profitable folds accounted for all positive fold profit.

The learned candidates also failed on total return, stressed costs, fold stability and
candidate-minus-benchmark improvement.

## Interpretation

This result does not show that tree models or the existing data sources can never be
useful. It shows that the current fixed specification does not justify a forward paper
experiment after accounting for non-normal returns, serial dependence, repeated
research trials, trading costs and fold concentration.

The next experiment must use a new, predeclared identity. It may investigate better
feature availability, local-market premium, higher-quality derivatives/on-chain data,
or a different target/horizon, but it must not tune the existing sealed test until a
candidate passes the same robustness rules.
