# TimesFM and Chronos feature protocol

## Role

TimesFM and Chronos are challenger feature generators. They cannot select position
size or call an exchange. Forecasts are cached, hashed and evaluated through the
same sealed model pipeline as every other feature.

## TimesFM 2.5

The adapter follows the official PyTorch API and validates:

- non-empty finite one-dimensional history;
- context no greater than 16,384;
- horizon no greater than 1,000;
- point shape `(horizon,)`;
- continuous quantile shape `(horizon, 10)`;
- finite output values.

The official quantile matrix is interpreted as mean followed by q10 through q90.

## Chronos-2

The adapter uses `Chronos2Pipeline.predict_quantiles` and validates:

- positive context and horizon;
- unique sorted quantile levels inside `(0, 1)`;
- quantile shape `(1, horizon, n_quantiles)`;
- mean shape `(1, horizon)`;
- finite outputs.

## Target alignment

The default trading label earns the Open[t+2] to Open[t+3] return. When a model is
fed one-bar log returns observed at the close of bar `t`, the first alignment to test
is therefore a three-step forecast. The cache stores:

- first step;
- last requested step;
- sum across the requested horizon;
- the same three representations for every quantile.

Alignment is still an empirical hypothesis; it must be ablated against market-only
features and a naive zero-return forecast.

## Rolling origin and latency

At each origin, only history ending at that origin is supplied. The cache records:

- dataset SHA-256;
- model ID and pinned revision;
- context, horizon, stride and minimum history;
- inference latency;
- feature SHA-256;
- exact rows and columns.

Feature availability is:

```text
underlying_data_available_at + inference_latency
```

Existing cache directories are immutable. A dataset mismatch, payload mismatch,
identity mismatch, invalid availability or structural mismatch fails closed.

## Acceptance rule

A foundation feature is accepted only when it:

1. improves sealed final-test results over market-only baselines;
2. survives leave-one-group-out ablation;
3. remains economically positive under stressed costs;
4. preserves acceptable calibration;
5. is not concentrated in one fold or event;
6. survives a prospective paper period.
