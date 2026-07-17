# Phase 3D bounded AvalAI pilot evidence

This directory records compact, secret-free evidence from the first bounded
prospective Phase 3D pilot.

## Identity

- Workflow run: `29572947781`
- Source commit: `0f9a035f0aff8699cee350762d70b1c305bf0515`
- Artifact ID: `8403844430`
- Artifact digest: `sha256:541a2390427af6917214a5053747f7d64a284a1ba02ab71a730e58bd796bdb3f`
- Assessment ID: `26c5d094b8184051b3fd518455b676c15c941a1c193be3fe2feb3bce6fae1a7b`

## Result

The pilot passed every predeclared budget, source, retry, deduplication, credential
and non-activation rule.

- Two required public feeds succeeded.
- One document per source was processed.
- The first capture made two AvalAI calls.
- The repeated capture made zero additional provider calls.
- Both calls succeeded on their first attempt.
- Total token use was 2,435, below the 4,000-token ceiling.
- Mean provider latency was 3.49 seconds; maximum latency was 4.42 seconds.
- Two semantic records were produced: one neutral BTC event and one bullish ETH event.
- The prospective decision ledger remained empty.
- No credential-shaped material was detected.

All top-level and nested checksum inventories were independently verified after the
artifact was downloaded. Raw RSS/Atom payloads and provider trace records remain in
the digest-addressed Actions artifact rather than Git history.

## Interpretation

The result permits continued prospective semantic-data collection only. It does not
demonstrate predictive value, alpha or economic usefulness and cannot activate paper
or live trading. Any predictive experiment must receive a new predeclared identity
and pass data-quality, calibration, ablation, economic-value and Phase 3A robustness
gates.
