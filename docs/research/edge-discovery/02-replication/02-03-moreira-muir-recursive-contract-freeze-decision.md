# Report 2.3 — Moreira–Muir Recursive Contract Freeze Decision

**Issue:** #46  
**Status date:** 2026-07-21  
**Outcome:** `GO_RECURSIVE_CONTRACT_FROZEN_EMPIRICAL_EXECUTION_BLOCKED`

## Decision

The completion criterion of Issue #46 is satisfied: the official current daily source contract and the recursive policy are frozen in machine-readable form. The separate current monthly source contract and daily/monthly reconciliation are also verified.

This closes the contract-design issue. It does not authorize performance calculation.

## Common-head evidence

```text
Head: c01ca4176a25cf0f150e20b6934a55fd9dff10fd

Daily source run / artifact:
29846542945 / 8501572703
sha256:c5931bda933faaac96ea39a15dfe7cfcfc45b3b8a902debdf19621727ce9ddab

Monthly source run / artifact:
29846543065 / 8501596170
sha256:45487ce75cb69b69d7fc8b1a55f7cfe3d240fd0ce1ac483e8c54c62fd7a8579f

Current-source reconciliation run / artifact:
29846542979 / 8501593770
sha256:c2939f3ced96e8dfb1f13f327f969ac7b22771d557e92a80d40eaab2471f0f95
```

All three workflows completed successfully and retained only safe evidence. Raw and row-level source data were deleted before artifact upload.

## Frozen contract

The contract predeclares source mappings, percent units, lagged month-t variance to month-t+1 returns, three variance definitions, expanding recursive normalization, a 60-month primary burn-in, fixed burn-in and leverage-cap sensitivity families, fixed cost scenarios, trial accounting, opposing evidence, and kill criteria.

## Remaining empirical blockers

The exact paper vintages and historical publication clocks are not verified. Variance-definition mechanical identification, recursive reconstruction, inference, optimal-combination analysis, cost results, and opposing-evidence replication remain unexecuted.

```text
Performance: NOT AUTHORIZED
Sharpe / alpha / utility: NOT AUTHORIZED
Paper replication: NOT COMPLETE
Economic edge: INCONCLUSIVE
Report 2.4: BLOCKED
```
