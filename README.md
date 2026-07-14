# Hybrid Trader

A leakage-aware, venue-neutral research system for a conservative **BTC Spot
Long/Flat** strategy. The repository deliberately separates point-in-time data,
model research, risk, and eventual execution so every added component must prove
incremental out-of-sample value after realistic costs.

> **Status: Phase 2C fixed-cutoff research candidate.** No live orders, exchange credentials,
> leverage, shorting, or withdrawal permissions are implemented. Nothing in this
> repository is financial advice.

## فارسی

این مخزن زیرساخت پژوهشی Phase 2C بات هیبریدی BTC Spot است. داده‌ها به‌صورت
point-in-time و دارای زمان واقعی دسترس‌پذیری ذخیره می‌شوند؛ مدل‌ها در ساختار
Train / Calibration / Validation / Test جداگانه ارزیابی می‌شوند؛ هزینه، اسلیپیج،
خروج اجباری پایان هر fold و دفتر forward-test ثبت می‌شوند. TimesFM و Chronos فقط
feature تولید می‌کنند و اجازه ارسال سفارش ندارند.

## Implemented

- strict UTC OHLCV and impossible-bar validation;
- separate `open_available_at` and full-bar `available_at` timestamps;
- immutable gzip snapshots with SHA-256 manifests;
- backward availability-time joins for funding, open interest, basis and local premium;
- public CCXT adapters without credentials;
- execution-aligned Open-to-Open labels with label-availability purging;
- sealed expanding walk-forward folds:
  - train;
  - embargo;
  - probability calibration;
  - threshold validation;
  - embargo;
  - untouched test;
- prior, ridge logistic, LightGBM, CatBoost and deterministic trend baselines;
- Platt calibration and validation-only threshold selection;
- fee, slippage, turnover, terminal liquidation and cost stress tests;
- TimesFM 2.5 and Chronos-2 adapters behind optional dependencies;
- rolling-origin foundation feature caches bound to dataset/model/revision hashes;
- incremental and leave-one-group-out ablations;
- content-addressed experiment artifacts;
- tamper-evident prospective paper-decision ledger;
- lint, strict typing, tests, wheel smoke test and GitHub Actions.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Optional capabilities:

```bash
python -m pip install -e '.[exchange]'  # CCXT public data
python -m pip install -e '.[ml]'        # LightGBM + CatBoost
python -m pip install -e '.[forecast]'  # TimesFM + Chronos
```

## Reproducible smoke workflow

```bash
# 1. Generate deterministic synthetic data. It is only a pipeline test.
hybrid-trader generate-sample \
  --output data/sample_btc_4h.csv \
  --bars 1800

# 2. Validate and freeze a point-in-time snapshot.
hybrid-trader create-snapshot \
  --input data/sample_btc_4h.csv \
  --config configs/btc_spot_4h_smoke.yaml \
  --output data/snapshots/sample \
  --source synthetic-smoke

# 3. Generate a naive foundation-feature cache.
hybrid-trader foundation-features \
  --snapshot data/snapshots/sample \
  --output data/features/naive \
  --model naive \
  --target log_return \
  --context-length 64 \
  --min-history 32 \
  --horizon 3

# 4. Run a sealed benchmark.
hybrid-trader benchmark \
  --snapshot data/snapshots/sample \
  --config configs/btc_spot_4h_smoke.yaml \
  --feature-cache data/features/naive \
  --output artifacts/smoke
```

The benchmark writes:

```text
fold_metrics.csv
predictions.csv.gz
summary.csv
cost_stress.csv
experiment.json
experiment.sha256
```

Experiment output directories are immutable: use a new directory for a new run.

## Public market-data snapshot

No private keys are required:

```bash
hybrid-trader download-real-snapshot \
  --config configs/btc_spot_4h.yaml \
  --output data/snapshots/btc-global \
  --global-exchange kraken \
  --global-symbol BTC/USD \
  --since 2022-01-01T00:00:00Z \
  --as-of 2026-07-13T00:00:00Z
```

Optional derivatives data can be requested from a venue that supports the required
CCXT unified endpoints:

```bash
hybrid-trader download-real-snapshot \
  --config configs/btc_spot_4h.yaml \
  --output data/snapshots/btc-with-derivatives \
  --global-exchange kraken \
  --global-symbol BTC/USD \
  --derivative-exchange binanceusdm \
  --derivative-symbol BTC/USDT:USDT \
  --strict-optional-sources
```

A connector being technically available does **not** establish legal eligibility,
safe custody, sanctions compliance, or withdrawal reliability for a resident of any
jurisdiction.

## TimesFM and Chronos

Both models are challengers, not trading agents. For the default label contract
(`execution_delay_bars=1`, `holding_period_bars=1`), a three-step return forecast is
the first sensible alignment experiment:

```bash
hybrid-trader foundation-features \
  --snapshot data/snapshots/btc-global \
  --output data/features/timesfm \
  --model timesfm \
  --target log_return \
  --horizon 3 \
  --context-length 1024 \
  --min-history 256 \
  --revision '<PINNED_MODEL_REVISION>' \
  --inference-latency-seconds 2.0
```

Use a pinned revision for a publishable result. The cache stores point step 1,
point last step, horizon sum, quantile step 1, quantile last step, and quantile sum.

## Ablation

Feature groups must be mutually exclusive:

```bash
hybrid-trader ablation \
  --snapshot data/snapshots/btc-global \
  --config configs/btc_spot_4h.yaml \
  --groups configs/feature_groups.example.json \
  --feature-cache data/features/timesfm \
  --feature-cache data/features/chronos \
  --output artifacts/ablation-001
```

## Prospective paper ledger

After freezing an experiment, record future decisions before their outcomes:

```bash
hybrid-trader forward-record \
  --ledger artifacts/forward/decisions.jsonl \
  --decision-time '2026-07-13T12:00:00+04:00' \
  --dataset-sha256 '<64_HEX_DATASET_SHA>' \
  --experiment-id '<64_HEX_EXPERIMENT_ID>' \
  --probability 0.68 \
  --threshold 0.60 \
  --desired-exposure 0.20 \
  --reason-code calibrated-model

hybrid-trader forward-verify \
  --ledger artifacts/forward/decisions.jsonl
```

## Fixed-cutoff Phase 2C

The authoritative historical workflow uses `configs/phase2c_sources_authoritative.yaml`
and keeps the 2023-01-01 through 2026-07-12 20:00 UTC window fixed. It requires
two independent spot histories, derivative coverage, Nasdaq, a broad USD index,
and gold futures, then runs sealed tree-model benchmarks, cost stress and ablation.

```bash
python -m hybrid_trader.phase2c   --spec configs/phase2c_sources_authoritative.yaml   --config configs/phase2c_btc_4h.yaml   --output artifacts/phase2c-historical

python scripts/verify_phase2c_artifacts.py artifacts/phase2c-historical
python scripts/verify_phase2c_artifacts_strict.py   artifacts/phase2c-historical   --spec configs/phase2c_sources_authoritative.yaml
python scripts/verify_phase2c_macro_gate.py   artifacts/phase2c-historical   --spec configs/phase2c_sources_authoritative.yaml
```

Historical success never activates a strategy. The foundation-model workflow remains
a pinned, non-activating challenger assessment requiring independent human review.

## Safety boundary

The repository currently cannot:

- send or cancel an order;
- accept an exchange API secret;
- withdraw funds;
- use leverage;
- open a short position;
- let an LLM determine position size;
- promote a model based on a historical test alone.

See [`docs/release-gates.md`](docs/release-gates.md) before adding dry-run or live
execution.

## Documentation

- [Reference architecture](docs/architecture.md)
- [Phase 2 methodology](docs/phase-2-methodology.md)
- [Public data contracts](docs/phase-2b-data-sources.md)
- [TimesFM and Chronos protocol](docs/foundation-models.md)
- [Forward-test ledger](docs/forward-test.md)
- [Platform selection](docs/platform-selection.md)
- [Release gates](docs/release-gates.md)


Phase 2C details:

- [Fixed-cutoff historical benchmark](docs/phase-2c-real-benchmark.md)
- [Foundation challenger benchmark](docs/phase-2c-foundation-benchmark.md)
- [Authority and non-activation rules](docs/phase-2c-authority.md)
