# Hybrid Trader

A leakage-aware, venue-neutral research foundation for a conservative **BTC Spot
Long/Flat** trading system. The project starts with an auditable baseline and adds
ML, time-series foundation models and LLM-derived event features only when each
component proves incremental out-of-sample value after costs.

> **Status:** Phase 1 research scaffold. It does not place live orders and is not
> financial advice.

## فارسی

این مخزن فاز اول بات هیبریدی BTC Spot است: اعتبارسنجی داده، استراتژی پایه روندی،
اندازه موقعیت بر اساس نوسان، هزینه معامله، بک‌تست بدون نگاه به آینده و ارزیابی
walk-forward. اتصال TimesFM آماده شده ولی مدل مستقیماً سفارش صادر نمی‌کند.

## Phase 1 deliverables

- strict UTC OHLCV schema and impossible-bar checks;
- optional public candle download through CCXT, without credentials;
- EMA + Donchian trend baseline with volatility targeting;
- next-bar execution rule to prevent close-to-close look-ahead;
- fees, slippage, turnover and buy-and-hold comparison;
- expanding-window walk-forward evaluation with an embargo gap;
- optional TimesFM 2.5 forecasting adapter and a mandatory naive baseline;
- constrained schema for future LLM/RAG event extraction;
- tests, type checking, linting and GitHub Actions.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'

hybrid-trader generate-sample --output data/sample_btc_4h.csv --bars 1200
hybrid-trader validate-data --input data/sample_btc_4h.csv
hybrid-trader backtest \
  --input data/sample_btc_4h.csv \
  --config configs/btc_spot_4h.yaml \
  --output artifacts/baseline.csv
hybrid-trader walk-forward \
  --input data/sample_btc_4h.csv \
  --config configs/btc_spot_4h.yaml \
  --initial-train 600 --test-size 120 --gap 1
```

Run quality checks:

```bash
make check
```

## Optional market data

CCXT is optional and the command uses public endpoints only:

```bash
python -m pip install -e '.[exchange]'
hybrid-trader download-ohlcv \
  --exchange kraken --symbol BTC/USD --timeframe 4h \
  --output data/btc_usd_4h.csv
```

Exchange API availability is not permission to use that venue. Residency, KYC,
sanctions, custody and withdrawal rules must be independently verified before any
live integration.

## Optional TimesFM

```bash
python -m pip install -e '.[forecast]'
```

The adapter follows the official TimesFM 2.5 PyTorch API. In Phase 2 it will be
benchmarked on **log returns, realized volatility, funding and local premium**. It
will not be accepted unless it beats naive and tree-model baselines on sealed
walk-forward windows after trading costs.

## Research rules

1. No random train/test split for market time series.
2. No signal earns a return on the bar that created it.
3. Every model is compared after fees and slippage.
4. Test windows are sealed; prompt/model/threshold changes require a new test period.
5. Real-money execution stays disabled until dry-run reconciliation and kill-switch tests pass.

## Roadmap

- **Phase 1 — completed in this scaffold:** data contract, baseline, costs, walk-forward, CI.
- **Phase 2:** point-in-time real dataset, LightGBM/CatBoost classifier, probability calibration, TimesFM/Chronos benchmark and ablations.
- **Phase 3:** timestamped news/on-chain pipeline, local multilingual LLM event encoder, source provenance and confidence calibration.
- **Phase 4:** Freqtrade dry-run adapter, order reconciliation, health checks and paper-trading report.
- **Phase 5:** NautilusTrader execution adapter, local-venue adapter, portfolio/risk service, observability and controlled release gates.

See [`docs/platform-selection.md`](docs/platform-selection.md) and
[`docs/architecture.md`](docs/architecture.md).

## License

Apache License 2.0. Third-party runtimes retain their own licenses; notably,
Freqtrade is GPL-3.0 and is therefore planned as an external adapter rather than
vendored code.
