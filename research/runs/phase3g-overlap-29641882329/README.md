# Phase 3G prospective market/semantic overlap evidence

This directory records compact, independently reviewed evidence from the first real
Phase 3G market/semantic overlap run.

## Identity

- Workflow run: `29641882329`
- Source commit: `d67c49b7e2937add0d1b33f00d81b28ed626d846`
- Artifact ID: `8428867389`
- Artifact digest: `sha256:47ffbb2a4656c0a59945c673586f2e0fc06181036c663a06e23facf6c7d74cd6`
- Observation cutoff: `2026-07-18T11:03:21Z`
- Overlap ID: `fe9b0103aaaac0b9b5385904ac9fd3c4563d41c2eafc3ce2b77783c08aa1ffd2`
- Market snapshot SHA-256: `3b18b21bb886d0b756abc365e80cde458c11a661c4a4905d1f215cdc7c1ef274`
- Semantic dataset ID: `semantic-ace403ed7733`
- Dataset content SHA-256: `ace403ed7733eff07da9303af672586f2bb358dd6d6e6270af6194d75a48e5c6`
- Trajectory entry ID: `a867afcbe8747844dc68393a57385bdf28904f332ee075de1aec3b23885df243`

## Public market evidence

Bitstamp BTC/USD and OKX BTC/USDT each supplied 719 fully available 4-hour bars from
2026-03-20 12:00 UTC through 2026-07-18 04:00 UTC.

- missing bars: zero on both venues;
- irregular gaps: zero;
- common rows: 719;
- overlap ratio: 1.0;
- return correlation: 0.9996495643;
- median absolute spread: 6.65 basis points;
- 95th percentile absolute spread: 16.08 basis points;
- maximum absolute spread: 20.91 basis points.

No exchange account, credential, order, position or trading decision was used.

## Prospective overlap result

The verified Phase 3E semantic artifact from workflow run `29575275480` was restored
and bound to the current market snapshot.

- prospective semantic records: 8;
- matured labeled market rows: 677;
- positive/negative targets: 331 / 346;
- active semantic decision rows: 3;
- first semantic availability: 2026-07-17 10:57:13.300850 UTC;
- rows before first semantic availability: 674;
- semantic event-count sum before first availability: exactly 0;
- rows on or after first semantic availability: 3;
- semantic event-count sum on or after first availability: 56.

The event-count sum covers overlapping 4h, 24h and 72h windows and therefore is not
a unique-event count. The important leakage invariant is that all 674 earlier rows
remain exactly zero.

## Maturity verdict

The trajectory recorded one immutable entry, but the prospective sample remains too
small for model fitting:

- semantic records: 8 of 100 required;
- unique semantic availability dates: 1 of 30;
- active decision rows: 3 of 50;
- relevant source diversity: 1 of 2;
- matured labeled rows: 677 of 500 required;
- both target classes are present.

The resulting status is `insufficient_prospective_sample` with
`research_model_fitting_allowed = false` and
`paper_or_live_trading_allowed = false`.

## Independent audit

All 20 artifact checksum entries matched. The two source snapshot hashes, combined
snapshot hash, dataset canonical content hash and trajectory self-hash were
independently recomputed and matched their manifests. The prospective decision ledger
remained empty.

The full market snapshots and deterministic dataset remain in the digest-addressed
GitHub Actions artifact. Git stores only this compact reviewed evidence.
