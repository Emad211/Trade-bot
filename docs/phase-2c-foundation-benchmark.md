# Phase 2C foundation-model challenger protocol

This stage starts only from a previously verified fixed-cutoff Phase 2C artifact.
It does not download a different market sample for each model.

## Pinned models

The workflow resolves immutable Hugging Face commit SHAs for:

- `google/timesfm-2.5-200m-pytorch`;
- `amazon/chronos-2`.

Model ID, revision, package version, device, context, horizon, stride, batch size,
inference latency, runtime, dataset SHA, cache ID and feature SHA are retained.

## Forecast alignment

The experiment uses BTC log returns with:

- context: 256 four-hour bars;
- forecast horizon: 6 bars;
- refresh stride: 6 bars;
- CPU batch size: 16;
- declared inference latency: 120 seconds.

A forecast generated at origin `t` supplies forecast step 1 at row `t`, step 2 at
`t+1`, and so on. The first-step forecast is never forward-filled as if it were a
new one-step forecast on every bar.

The daily refresh is a predeclared CPU feasibility experiment. A stride-1 GPU run
must be recorded as a separate experiment and cannot replace this result after its
test set is observed.

## Scenario matrix

1. zero-return naive features;
2. TimesFM features;
3. Chronos features;
4. TimesFM and Chronos together.

Every scenario uses the same sealed train/calibration/validation/test folds, model
matrix and cost assumptions. The combined run also executes feature-group ablation
for base features, TimesFM and Chronos.

## Promotion rule

A foundation model is not promoted merely because it improves RMSE. It must add
net economic value over the baseline and zero-return scenario, survive stressed
costs and multiple folds, improve or preserve probability calibration, and retain
value when the other foundation model is removed.

The historical workflow writes `historical_challenger_not_activated` and an empty
prospective decision file. It cannot activate a dry-run or live strategy.
