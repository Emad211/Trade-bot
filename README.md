# Hybrid Trader

A leakage-aware, venue-neutral research system for a conservative **BTC Spot
Long/Flat** strategy. The repository deliberately separates point-in-time data,
model research, risk, and eventual execution so every added component must prove
incremental out-of-sample value after realistic costs.

> **Status: Phase 3B prospective event research.** The Phase 3A robustness gate
> rejected every current trading candidate. No live orders, exchange credentials,
> leverage, shorting, or withdrawal permissions are implemented. Nothing in this
> repository is financial advice.

## فارسی

این مخزن زیرساخت پژوهشی بات هیبریدی BTC Spot است. داده‌های بازار و رویدادها
با زمان واقعی دسترس‌پذیری ذخیره می‌شوند؛ مدل‌ها در ساختار جداگانه و sealed ارزیابی
می‌شوند و Phase 3A همه نامزدهای فعلی را رد کرده است. Phase 3B فقط اسناد عمومی و
featureهای معنایی آینده‌نگر را ثبت می‌کند. هیچ LLM، مدل سری زمانی یا مدل درختی
اجازه تعیین اندازه موقعیت یا ارسال سفارش ندارد.

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
- Phase 3A PSR/DSR, block-bootstrap, fold-concentration and 2x-cost rejection gate;
- prospective RSS/Atom capture with retrieval-time availability semantics;
- hash-chained document and semantic-event ledgers with deterministic retry identities;
- lint, strict typing, tests, wheel smoke test and GitHub Actions.

## Current research verdict

The real pinned TimesFM 2.5 and Chronos-2 experiment completed successfully, but
**no foundation scenario/model candidate passed every screening rule**. A candidate
must beat both its market-only baseline and the matching naive zero-return
challenger, preserve calibration, be positive in at least half of sealed folds and
remain profitable at twice the declared costs. Therefore TimesFM, Chronos and their
combination remain research-only and cannot enter the prospective ledger.

- [Human-readable verdict](docs/foundation-screening-verdict.md)
- [Machine-readable verdict](research/foundation-screening-verdict.json)
- [Compact committed run evidence](research/runs/phase2c-foundation-29412736808/README.md)

Large immutable feature caches and prediction matrices remain in GitHub Actions
under the artifact ID and SHA-256 digest recorded in the committed evidence; they
are not checked into Git as opaque binary archives.

## Phase 3A robustness verdict

The stricter PSR/DSR, circular block-bootstrap, fold-stability, profit-concentration
and doubled-cost gate screened the prior, ridge logistic, CatBoost and LightGBM
candidates. **Zero of four candidates passed all predeclared rules.** No paper
experiment was started and the prospective decision ledger remains empty.

- [Phase 3A result](docs/phase-3a-robustness-result.md)
- [Phase 3A method](docs/phase-3a-robustness-gate.md)
- [Committed Phase 3A evidence](research/runs/phase3a-robustness-29488655448/)

## Phase 3B prospective event evidence

A credential-free public capture recorded 20 Bitcoin Core and Geth release
documents plus 20 neutral baseline semantic records. Document availability is the
actual retrieval time; semantic availability is inference completion. The raw XML
remains in a digest-addressed GitHub Actions artifact, while compact hash-chained
ledgers and checksums are committed to Git. This validates the data pipeline only;
it is not evidence of predictive value.

```bash
python scripts/capture_phase3b_events.py \
  --config configs/phase3b_event_sources.yaml \
  --output artifacts/phase3b-events
python scripts/verify_phase3b_events.py artifacts/phase3b-events
```

- [Phase 3B design and safety contract](docs/phase-3b-prospective-events.md)
- [Committed Phase 3B evidence](research/runs/phase3b-events-29494760888/)

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

The current foundation scenarios are not eligible for this ledger. A new candidate
must have a separate predeclared identity and pass every historical screening gate.

## Fixed-cutoff Phase 2C

The authoritative historical workflow uses `configs/phase2c_sources_authoritative.yaml`
and keeps the 2023-01-01 through 2026-07-12 20:00 UTC window fixed. It requires
two independent spot histories, derivative coverage, Nasdaq, a broad USD index,
and gold futures, then runs sealed tree-model benchmarks, cost stress and ablation.

```bash
python -m hybrid_trader.phase2c \
  --spec configs/phase2c_sources_authoritative.yaml \
  --config configs/phase2c_btc_4h.yaml \
  --output artifacts/phase2c-historical

python scripts/verify_phase2c_artifacts.py artifacts/phase2c-historical
python scripts/verify_phase2c_artifacts_strict.py \
  artifacts/phase2c-historical \
  --spec configs/phase2c_sources_authoritative.yaml
python scripts/verify_phase2c_macro_gate.py \
  artifacts/phase2c-historical \
  --spec configs/phase2c_sources_authoritative.yaml
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
- [Foundation screening verdict](docs/foundation-screening-verdict.md)
- [Phase 3A robustness gate](docs/phase-3a-robustness-gate.md)
- [Phase 3A real-data result](docs/phase-3a-robustness-result.md)
- [Phase 3B prospective event stream](docs/phase-3b-prospective-events.md)
- [Forward-test ledger](docs/forward-test.md)
- [Platform selection](docs/platform-selection.md)
- [Release gates](docs/release-gates.md)

Phase 2C details:

- [Fixed-cutoff historical benchmark](docs/phase-2c-real-benchmark.md)
- [Foundation challenger benchmark](docs/phase-2c-foundation-benchmark.md)
- [Authority and non-activation rules](docs/phase-2c-authority.md)
