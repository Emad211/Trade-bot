# Foundation-model screening verdict

## Decision

**Verdict: `no_candidate_passed`.**

**Action: retain TimesFM 2.5 and Chronos-2 as research-only challengers. Do not promote either model, or their combination, into paper-trading or execution logic.**

This verdict is based on the pinned, fixed-cutoff Phase 2C foundation run with:

- repository commit: `494e5af03b7957cac6e3f654ea92fbfda4ac1b8f`;
- successful foundation workflow run: `29412736808`;
- artifact ID: `8342048388`;
- artifact digest: `sha256:0e01fc2c0179000c83c7cb2d56665356fb8e42dd7f4a1d2711ce1d80b6766335`;
- fixed historical dataset: 2023-01-01 00:00 UTC through 2026-07-12 20:00 UTC;
- observation cutoff: 2026-07-13 00:15 UTC;
- TimesFM revision: `1d952420fba87f3c6dee4f240de0f1a0fbc790e3`;
- Chronos revision: `29ec3766d36d6f73f0696f85560a422f50e8498c`;
- context 256, horizon 6, stride 6, batch size 16 and declared inference latency 120 seconds.

The compact, reviewable outputs are committed under
`research/runs/phase2c-foundation-29412736808/`. Large immutable feature caches,
predictions and model-run artifacts remain in GitHub Actions and are identified by
the run, artifact ID and SHA-256 digest above. They are not copied into the Git
history as opaque ZIP files.

## Screening policy

A candidate had to satisfy all of the following:

1. net return above the matching non-foundation baseline;
2. net return above the matching naive zero-return challenger;
3. Sharpe ratio above the non-foundation baseline;
4. Brier score not worse than the non-foundation baseline;
5. at least half of sealed test folds positive;
6. positive mean net return at two times the declared trading costs.

None of the 15 scenario/model combinations passed all six checks.

## Most favorable partial results

These are observations, not promotion evidence:

- `timesfm_chronos + lightgbm` improved mean net return by approximately `+0.010799` and Sharpe by `+0.951846` over its market-only baseline, and exceeded its naive scenario by approximately `+0.013113`; however, only `25%` of folds were positive, Brier score worsened by about `+0.001665`, and mean net return at 2x costs was approximately `-0.055565`.
- `chronos + catboost` improved mean net return by approximately `+0.006629` and Sharpe by `+1.381694`, and exceeded its naive scenario by approximately `+0.016981`; however, it had `0%` positive folds, a worse Brier score, and mean net return at 2x costs near `-0.061219`.
- `timesfm + catboost` improved mean net return by approximately `+0.003442` over its market-only baseline and approximately `+0.013794` over its naive scenario, but Sharpe and calibration worsened, only `8.33%` of folds were positive, and 2x-cost net return was approximately `-0.071706`.

The prior model remained slightly positive under 2x costs, but the foundation features made no meaningful improvement over the prior or naive baseline; this is not evidence that either foundation model adds alpha.

## Interpretation

The experiment demonstrates that the TimesFM and Chronos integration, timing contracts, immutable caches, pinned revisions, sealed evaluation, ablation and cost-stress pipelines work correctly. It does **not** demonstrate economically reliable predictive value.

The current evidence indicates:

- improvements are model-specific and unstable across folds;
- cost robustness is absent for the learned candidates;
- probability calibration frequently degrades;
- combining TimesFM and Chronos does not reliably dominate either model alone;
- there is no basis for paper-trading promotion from this experiment.

## Next research direction

Further work should focus on stronger causal and market-microstructure features rather than adding more foundation-model complexity:

- derivatives-regime features and bounded publication delays;
- volatility and liquidity forecasting as separate targets;
- regime-conditional models;
- stronger non-foundation baselines;
- multiple-comparison control and deflated Sharpe analysis;
- a new, predeclared experiment identity for any changed target, horizon, stride, model revision or feature set.

The prospective ledger must remain empty for these foundation scenarios. Any future promotion requires a new frozen experiment and an independent paper-trading period.
