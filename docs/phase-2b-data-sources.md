# Phase 2B public data sources

## Design rule

The data layer records what was observable, when it was observable, and which
public endpoint supplied it. Technical API availability is not legal eligibility,
safe custody, sanctions compliance, or withdrawal assurance.

## Spot OHLCV

The CCXT adapter:

- paginates forward;
- removes duplicates;
- filters event-time bounds;
- independently enforces the observation `as_of` cutoff;
- removes the forming candle;
- applies source latency;
- drops bars not observable at snapshot time.

## Funding history

Historical funding settlements are available at event timestamp plus source
latency. Predicted funding is a distinct feature and needs its own contract.

## Open-interest history

An interval value is conservatively unavailable until:

```text
event_time + timeframe + source_latency
```

## Basis history

Basis is calculated from mark and index candle closes:

```text
basis = mark_close / index_close - 1
```

Its availability is also end-of-candle plus latency. Treating the candle-open
timestamp as immediately known would leak a full bar.

## Local market premium

```text
implied_local_BTC = global_BTC_quote * local_stable_fiat
local_premium = local_BTC_fiat / implied_local_BTC - 1
```

All legs are backward as-of joined using actual availability times. Missing values
remain missing unless a bounded tolerance explicitly permits an older observation.

## Optional endpoint policy

Exchange adapters differ. Unsupported derivatives endpoints are skipped by default
and only successful sources are written to the manifest. Strict mode makes absence
of a requested feature fatal.

## Next eligible sources

Each new source must define event time, publication time, revision policy, latency,
observation cutoff and outage behavior before it is modeled. Candidates include:

- liquidation aggregates;
- exchange inflow/outflow and stablecoin flows;
- DXY, Nasdaq and gold;
- vintage macroeconomic releases;
- timestamped news and regulatory events;
- local order-book spread and depth.
