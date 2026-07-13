# Phase 2C: fixed-cutoff real-data benchmark

Phase 2C executes in GitHub Actions because the local development sandbox does
not provide reliable outbound DNS. The workflow uses a fixed observation cutoff,
not "latest" data, so a re-run requests the same historical window.

## Sources

The runner attempts three independent BTC/USD spot venues and requires at least
two successes. It then tries several public derivatives venues independently for:

- settled funding history;
- interval-close open interest;
- mark/index basis.

Daily market context is requested from FRED for Nasdaq Composite, the Federal
Reserve broad dollar index and the London morning gold price. These are explicitly
marked as latest-vintage market/reference-price series. Revisable macroeconomic
series are prohibited until an ALFRED/vintage-aware adapter is implemented.

## Model and ablation policy

The all-feature benchmark runs the full model matrix. Feature ablations rerun the
predeclared Ridge and LightGBM models plus the deterministic Trend baseline,
avoiding redundant CatBoost refits while retaining economic and nonlinear
attribution checks.

## Evidence bundle

The workflow artifact contains immutable source manifests, source failures,
missing-bar diagnostics, cross-venue checks, sealed model results, cost stress,
feature ablations, large-move analysis, fold concentration, a non-activated
prospective freeze candidate and a SHA-256 inventory.

## Safety

The workflow has no secrets or write-capable exchange API. It cannot submit
orders, withdraw funds, open short positions or enable leverage. The prospective
decision ledger must remain empty during historical automation.
