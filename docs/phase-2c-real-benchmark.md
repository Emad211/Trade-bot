# Phase 2C: fixed-cutoff real-data benchmark

Phase 2C converts the research engine into one reproducible public-data experiment.
The observation cutoff is fixed in `configs/phase2c_sources.yaml`; reruns cannot
silently move the historical endpoint forward.

## Required evidence

- at least two independent BTC/USD 4h spot snapshots;
- explicit event and availability timestamps;
- at least one successful derivative family: funding, open interest or basis;
- FRED market-context series with a conservative release lag;
- immutable raw artifacts and one combined snapshot;
- source attempts, including failures, in `source_registry.json`;
- sealed benchmark, cost stress and ablation;
- large-move and fold-concentration reports;
- inactive prospective freeze candidate and empty decision ledger.

## Important limitation

The public FRED graph CSV is not vintage-safe for revised macroeconomic releases.
It is therefore restricted here to market/reference-price series, and each series is
assigned a conservative availability lag. Revised macro data require ALFRED/vintage
records before they can enter this experiment.

## Safety

The workflow contains no secrets and cannot place orders. A successful historical
artifact is research evidence only, not permission to enable a dry-run or live venue.
