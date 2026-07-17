# Phase 3F point-in-time semantic dataset evidence

This directory records compact, independently verified evidence from the first fixed
Phase 3F semantic-dataset build.

## Identity

- Workflow run: `29576654860`
- Artifact ID: `8405288031`
- Artifact digest:
  `sha256:a78c1d880a42854614428b902479e6d9bf8ae545584c0ef71a11f64a73c07d0b`
- Artifact source commit: `33ad4c0c368ca576ff5b5c62206810e8df7f77be`
- Final validated implementation commit: `c1248daadb0313261c565c88291a77bb5b1926d6`
- Final CI run: `29585998799`

The artifact was generated before the final Ruff/index round-trip cleanup. The final
implementation was subsequently validated by the complete CI matrix. The cleanup did
not change the point-in-time inclusion, maturity, content-addressing or no-backfill
contracts; it normalized the in-memory index expectation used by the round-trip test.

## Dataset result

- Dataset ID: `semantic-157007b0519c`
- Dataset content SHA-256:
  `157007b0519c122d4a2851c5d4164e5dbcc3d828a5bfcd8067a3a840e7d6d3f6`
- Market snapshot SHA-256:
  `fa8c7f3ddc75baa7fccc8b835b47c4bb75ca3e8dbdc208a27428d513da40f144`
- Semantic ledger head:
  `91cc8de3811bbf70e37c99b3d7de087d3562966333b65bbb58fc3c698a969b99`
- Candidate and matured rows: `7,632`
- Positive/negative labels: `3,915 / 3,717`
- Relevant prospective semantic records: `8`
- Semantic availability dates: `1`
- Active decision rows: `0`
- Semantic event-count sum across all market rows: `0`

The market snapshot ends before the prospective events became available. A zero event
sum therefore confirms that publication/event timestamps were not used to backfill
semantic information into historical market rows.

## Maturity verdict

```text
status = insufficient_prospective_sample
research_model_fitting_allowed = false
paper_or_live_trading_allowed = false
```

Failure reasons:

- insufficient semantic records;
- insufficient unique availability dates;
- insufficient active decision rows;
- insufficient source diversity.

The labeled market sample is large enough, and both target classes exist, but the
prospective semantic sample is intentionally immature. No model was fitted, no
threshold was selected, and no prospective decision was created.

## Verification

The downloaded ZIP digest matched the GitHub artifact digest exactly. Every entry in
the six-file checksum inventory was independently recomputed and matched. All 42
semantic feature columns were finite, and both the latest decision time and label
availability preceded the declared `as_of` cutoff.
