# Phase 2C workflow authority

Phase 2C was developed through progressively stricter workflows. They are retained
in the draft branch so methodological corrections remain visible, but only the
following chain is authoritative:

```text
phase2c-real-benchmark-authoritative
                    ↓
          phase2c-foundation-final
```

## Historical data authority

`phase2c-real-benchmark-authoritative` uses:

- `configs/phase2c_sources_authoritative.yaml`;
- a fixed 2023-01-01 through 2026-07-12 event window;
- a fixed 2026-07-13 00:15 UTC observation cutoff;
- page size 100 to remain compatible with venues whose public endpoints cap a
  page at 100 records;
- at least two independent spot venues with >=95% window coverage;
- a cross-venue overlap/correlation gate;
- at least one sufficiently long and current derivative family;
- required Nasdaq, broad-dollar and gold context;
- integrity, coverage and macro-context verifiers.

## Foundation-model authority

`phase2c-foundation-final` accepts only an artifact from the authoritative historical
workflow. It re-runs all three verifiers before resolving immutable TimesFM and
Chronos revisions and generating challenger features.

## Non-authoritative workflows

Workflows containing `fixed`, `strict`, or `gate` in their names document the
sequence of corrections and can help diagnose a source failure. Their successful
completion alone does not satisfy the release gate.

No workflow in this phase can activate trading. Historical success produces only
non-activated evidence for human review and a future prospective paper period.
