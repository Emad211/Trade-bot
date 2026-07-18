# Phase 3F point-in-time semantic dataset evidence

This directory records compact, secret-free evidence from the final fixed Phase 3F
run on source commit `c1248daadb0313261c565c88291a77bb5b1926d6`.

## Identity

- Workflow run: `29586581122`
- Artifact ID: `8409259039`
- Artifact digest: `sha256:d1d4ba1b34370667aeab95e9c3ba0dd5f58d2085550963a93843863537a00f6b`
- Dataset ID: `semantic-157007b0519c`
- Dataset content SHA-256: `157007b0519c122d4a2851c5d4164e5dbcc3d828a5bfcd8067a3a840e7d6d3f6`
- Maturity assessment ID: `ab74a228d570318b59f9c748d336d53f318bc58672e66709541ccabe3472d6a6`

## Independent verification

The downloaded artifact passed all independent checks:

- all six top-level checksum entries matched their files;
- the decompressed canonical CSV matched the manifest content SHA-256;
- manifest and maturity records agreed exactly;
- row count was 7,632;
- all decision and label-availability timestamps were no later than `as_of`;
- the sum of all semantic event-count features was exactly zero;
- no model fitting was executed;
- no prospective paper or live-trading decision was created.

The zero event sum is the expected leakage test result: the market snapshot ends on
2026-07-13 while the prospective semantic records were observed on 2026-07-17. Any
nonzero semantic value in those historical market rows would have proved backfill.

## Maturity verdict

The prospective sample remains intentionally immature:

- relevant semantic records: 8 of the 100-record minimum;
- unique semantic availability dates: 1 of 30;
- active decision rows: 0 of 50;
- relevant source diversity: 1 of 2;
- matured labeled rows: 7,632;
- both market target classes are present.

The resulting status is `insufficient_prospective_sample` with
`research_model_fitting_allowed = false` and
`paper_or_live_trading_allowed = false`.

The full deterministic dataset remains in the digest-addressed GitHub Actions
artifact. Git stores only reviewed provenance and the compact verdict.
