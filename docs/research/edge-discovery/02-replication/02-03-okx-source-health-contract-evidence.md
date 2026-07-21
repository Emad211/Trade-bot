# Report 2.3 — Verified OKX Source-Health and Sampling-Abort Contract

**Status date:** 2026-07-21  
**Issue:** #58  
**Outcome:** `GO_OKX_SOURCE_HEALTH_AND_SAMPLING_ABORT_CONTRACT`

## Decision

The project now has a fail-closed source-health state machine for prospective OKX REST and WebSocket observations. The outcome authorizes only the tested metadata, sequence, incident, and batch-abort contract. It does not authorize real raw sampling, numerical transaction costs, basis, funding PnL, returns, strategy testing, or trading.

## Verified workflow

```text
Workflow: OKX Source Health and Sampling Abort Contract
Run ID: 29845596573
Triggering head: bfcf8ca98e44c2b05ea79f00dbaf28d4a53fda28
Permissions: contents read-only
Conclusion: SUCCESS
Ruff: PASS
Mypy: PASS
Scoped tests: 16 PASS
Independent verifier: PASS
```

## Artifact

```text
Artifact ID: 8501219123
Artifact digest: sha256:0abe10d937837032e3ca1a03506bd724e6bb17c10bfa7c24c46e54c335c603f8
Evidence bytes: 3981
Evidence SHA-256: cbb91b6d4dd02704495f477a0cae1a8d0694836a4aff3a085d03b3facb8bf0a3
```

The artifact contains one safe JSON document with source-health identities, policy identities, provider-code identities, sequence rules, and authorization flags only. It contains no real prices, sizes, order books, fills, fees, account values, credentials, PnL, or returns.

## Frozen operational rules

- All staleness, future-skew, response-to-research delay, WebSocket silence, and cross-source-skew thresholds are explicit versioned policy inputs.
- Provider code `50011` is a rate-limit failure and aborts admission.
- Provider notice `64008` enters service-upgrade drain/reconnect state.
- From the admitted 2026-06-23 boundary, checksum is not an integrity signal for `books`, `books-l2-tbt`, or `books50-l2-tbt`; `seqId/prevSeqId` is authoritative.
- A snapshot starts with `prevSeqId=-1`.
- An empty unchanged-sequence book message is a heartbeat, never a new market observation.
- Schema or identity drift quarantines the observation.
- Partial or duplicate source sets, sequence gaps/regressions, stale/future clocks, silence, and excessive cross-source skew abort the batch.
- Failed observations are never converted into market nulls, carried forward, interpolated, or retained publicly.

## Explicit non-authorization

```text
Real market request: false
Real order request: false
Private trading endpoint: false
Hidden thresholds: false
Carry-forward / interpolation: false
Numerical transaction-cost estimation: false
Basis / funding PnL / returns: false
Report 2.4: blocked
Economic edge: INCONCLUSIVE
```
