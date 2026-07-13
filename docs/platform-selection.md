# Platform selection (July 2026)

## Recommended stack

| Layer | Primary choice | Why | Not used as the Phase-1 core |
|---|---|---|---|
| Research harness | This repository + pandas/NumPy | Auditable, lightweight, venue-neutral | Full platforms add assumptions before the signal contract is stable |
| Public crypto data | CCXT | MIT, broad exchange abstraction | Venue support does not imply legal availability or safe custody |
| Crypto dry-run | Freqtrade | Mature backtest, dry-run, FreqAI, lookahead analysis | Crypto-only and GPL-3.0; kept outside the core package |
| Multi-asset production | NautilusTrader | Same event-driven architecture for simulation/live; forex + crypto | More operational complexity; introduce after signal validation |
| Market making | Hummingbot | Strong CEX/DEX connector and order-book focus | Wrong fit for 4h long/flat directional Phase 1 |
| Institutional multi-market alternative | QuantConnect LEAN | Apache-2.0, event-driven, forex and crypto | Heavier C#-centric engine and data/broker integration burden |
| ML research | Qlib | Rich supervised/RL research workflows | Primarily equity-shaped data assumptions; requires adaptation for 24/7 crypto |
| RL experiments | FinRL-X / FinRL-Meta | Ready environments and DRL baselines | RL is intentionally postponed until the simulator is validated |
| Time-series FM | TimesFM 2.5, Chronos-2 | Quantile/covariate forecasts and strong zero-shot baselines | Must prove incremental net value over naive and tree baselines |

## Decision

Phase 1 is intentionally framework-light and Apache-2.0 licensed. Freqtrade will be
added as a separate dry-run adapter after the baseline and data contracts pass
walk-forward tests. NautilusTrader is the preferred production runtime because it
supports multi-asset, multi-venue event-driven execution while keeping Python as the
strategy control plane.

## Official projects

- Freqtrade: https://github.com/freqtrade/freqtrade
- NautilusTrader: https://github.com/nautechsystems/nautilus_trader
- CCXT: https://github.com/ccxt/ccxt
- TimesFM: https://github.com/google-research/timesfm
- Chronos: https://github.com/amazon-science/chronos-forecasting
- Hummingbot: https://github.com/hummingbot/hummingbot
- LEAN: https://github.com/QuantConnect/Lean
- Qlib: https://github.com/microsoft/qlib
- FinRL: https://github.com/AI4Finance-Foundation/FinRL
