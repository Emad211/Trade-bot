# Report 2.3 — Risk-Policy Controlling Addendum

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Hypothesis:** `EDGE-RISK-POLICY-001`  
**Status date:** 2026-07-19  
**Status:** `OFFICIAL_TARGET_CONTRACT_VERIFIED; RECURSIVE_REAL_TIME_REPLICATION_NOT_STARTED`

This document is the controlling status for the volatility-managed-factor path. It supplements the broader Report 2.3 status and supersedes earlier wording that treated the Moreira-Muir author artifact as unavailable.

Detailed evidence:

- [Official factor snapshot and scaling-contract evidence](02-03-moreira-muir-official-factor-contract-evidence.md)
- [Machine-readable factor-contract evidence](02-03-moreira-muir-official-factor-contract-evidence.yaml)
- `src/hybrid_trader/replication/moreira_muir.py`
- `tests/test_moreira_muir.py`
- `.github/workflows/moreira-muir-official-factor-contract-audit.yml`

## Controlling decision

```text
Official Tyler Muir factor CSV: ACQUIRED_AND_IDENTIFIED
Exact snapshot parser: VERIFIED
Published managed/unmanaged factor pairs: VERIFIED_6
Published unconditional-volatility scaling contract: PASS_6_OF_6
Safe evidence deterministic across runners: YES
Recursive real-time policy: NOT CONSTRUCTED
Paper replication: NOT COMPLETE
Economic edge: NOT ESTABLISHED
```

The official author file is a published target artifact. It must not be confused with a real-time investable policy.

## Why the current pass is limited

The author page states that each volatility-managed factor is scaled by the inverse of prior-month realized variance and then rescaled to have the same unconditional standard deviation as the original factor.

The current audit confirms the latter property in the distributed file with extremely small numerical error. It does not establish:

- when the unconditional scaling constant became available;
- whether a full-sample normalization was used;
- how an investor would have estimated the constant recursively;
- whether the series survive leverage caps and transaction costs;
- whether managed-only exposure is superior to combining managed and unmanaged exposure;
- whether alpha survives opposing recursive real-time evidence;
- whether the effect persists prospectively.

Consequently, the author-provided series may be used as a published replication target, but not as an automatically authorized live strategy.

## Verified identity

```text
Snapshot:
MOREIRA_MUIR_VOL_MANAGED_FACTORS_2026_01_V1

Rows / columns:
1189 / 14

Date range:
1927-01 through 2026-01

Unit:
PERCENT

Source SHA-256:
e9d92955e6ef2154aa55d05eed7b9237a313b987aad9afb0fdffd2103a81a6ba
```

All six managed/unmanaged pairs satisfy the predeclared 2.5% relative standard-deviation tolerance. The maximum observed relative error is `0.000000515518`.

## Hosted evidence

Two clean-head runs passed:

```text
29698955657
29698976996
```

The three safe JSON outputs were byte-identical across the runs:

```text
safe-factor-contract-evidence.json
a254600f17ec665cede4a30a6dabb91d7664c3c420d7a338e0455d2765559ec6

safe-factor-contract-summary.json
5c967101beca0066d7fb964dee945f88a48ee85983cff45d9c5308bc6affe8cf

safe-scaling-gate.json
0f28fe871f757286fb2f774c70fd977da33b54a92466cd67bb0feefa5da3cce9
```

No author CSV, HTML page, or row-level return data is retained in the safe artifacts.

## Current authorization

```yaml
official_snapshot_monitoring: true
exact_parser_maintenance: true
safe_contract_audit: true
synthetic_adversarial_testing: true
recursive_replication_contract_design: true
public_unmanaged_source_acquisition_design: true

raw_publication: false
raw_immutable_retention: false
annualized_performance_analysis: false
sharpe_analysis: false
alpha_analysis: false
optimal_combination_analysis: false
empirical_fitting: false
parameter_tuning: false
strategy_tournament: false
paper_trading: false
live_trading: false
leverage: false
capital_deployment: false
report_2_4_full_authorization: false
```

## Next controlling gate

```text
RECURSIVE_REAL_TIME_VOLATILITY_MANAGED_FACTOR_REPLICATION_CONTRACT
```

Before calculating performance, the project must freeze:

1. exact public unmanaged factor sources and vintages;
2. daily factor observations used for prior-month variance;
3. observation and publication timing;
4. recursive scale estimation with no full-sample leakage;
5. initial burn-in and missing-data rules;
6. leverage caps;
7. turnover and cost assumptions;
8. managed-only and optimal-combination benchmarks;
9. fixed estimator and cap sensitivity families;
10. crisis, utility, alpha, and appraisal-ratio targets;
11. strongest opposing evidence;
12. trial accounting and kill criteria.

No metric may be selected because it makes the managed strategy look better.

## Final controlling verdict

```text
OFFICIAL TARGET SERIES: CONFIRMED
EXACT SNAPSHOT AND UNIT CONTRACT: CONFIRMED
UNCONDITIONAL VOLATILITY MATCH: PASS_6_OF_6
SAFE OUTPUT DETERMINISM: PASS
REAL-TIME IMPLEMENTABILITY: NOT ESTABLISHED
RECURSIVE REPLICATION: NOT STARTED
PAPER REPLICATION: NOT COMPLETE
ECONOMIC EDGE: NOT ESTABLISHED
EDGE-RISK-POLICY-001: INCONCLUSIVE
REPORT 2.4: BLOCKED
```
