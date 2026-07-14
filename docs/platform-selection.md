# Platform selection (July 2026)

| Layer | Primary choice | Reason | Why not the core yet |
|---|---|---|---|
| Research | This repository + pandas/NumPy | Auditable and venue-neutral | Full platforms impose assumptions before signal validation |
| Public crypto data | CCXT | Broad unified API, MIT | Connector support is not jurisdictional eligibility |
| Crypto dry-run | Freqtrade | Mature backtest, dry-run and diagnostics | Crypto-oriented and GPL; keep behind an adapter |
| Multi-asset production | NautilusTrader | Event-driven simulation/live architecture | Introduce only after prospective validation |
| Market making | Hummingbot | Strong CEX/DEX and order-book tooling | Wrong fit for 4h directional Long/Flat |
| Multi-market alternative | QuantConnect LEAN | Event-driven forex and crypto support | Heavier ecosystem and C# orientation |
| ML research | Qlib | Rich supervised and portfolio workflows | Equity-shaped assumptions need 24/7 adaptation |
| RL research | FinRL | Ready DRL environments | Postponed until simulator fidelity is proven |
| Time-series FM | TimesFM 2.5 + Chronos-2 | Strong zero-shot challengers | Must beat naive/tree baselines after costs |

The project remains framework-light through Phase 2B. Freqtrade is the likely first
dry-run adapter. NautilusTrader is the preferred later runtime for multi-venue,
multi-asset event-driven execution.

Official projects:

- https://github.com/ccxt/ccxt
- https://github.com/freqtrade/freqtrade
- https://github.com/nautechsystems/nautilus_trader
- https://github.com/google-research/timesfm
- https://github.com/amazon-science/chronos-forecasting
- https://github.com/hummingbot/hummingbot
- https://github.com/QuantConnect/Lean
- https://github.com/microsoft/qlib
- https://github.com/AI4Finance-Foundation/FinRL
