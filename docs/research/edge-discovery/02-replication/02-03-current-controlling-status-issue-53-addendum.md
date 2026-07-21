# Report 2.3 — Controlling Status Addendum for Issue #53

**Status date:** 2026-07-21  
**Scope:** OKX prospective price-source identity and timing linkage  
**Precedence:** This addendum supersedes the Issue #53, OKX prospective price-linkage, and related authorization statements in `02-03-current-controlling-status.md` wherever they conflict. All unrelated controlling-status statements remain unchanged.

## Gate outcome

```text
Issue #53: CLOSED — GO_PROSPECTIVE_OKX_PRICE_LINKAGE_METADATA_PILOT
```

This outcome follows:

```text
Issue #51: BLOCKED_INSTRUMENT_VERSION_HISTORY
Issue #51 independent blocker: BLOCKED_ARCHIVE_AVAILABILITY_TIMING
Issue #52: GO_PROSPECTIVE_OKX_POINT_IN_TIME_REGISTRY
```

Issue #53 does not repair or supersede the historical blockers.

## Verified implementation and workflow

```text
Implementation: src/hybrid_trader/replication/okx_price_linkage_probe.py
CLI: scripts/audit_okx_prospective_price_linkage.py
Tests: tests/test_okx_price_linkage_probe.py
Workflow: .github/workflows/okx-prospective-price-linkage-metadata-pilot.yml
Read-only workflow run: 29828971655
Conclusion: SUCCESS
Formatting / lint / mypy: PASS
Adversarial tests: 12 PASS
Four official live sources: PASS
Independent safe-evidence verifier: PASS
```

```text
Artifact ID: 8494458677
Artifact digest: sha256:9442a7cab8d7bd2b400505676e73fef08fbf1ee90f5ff136b45b38ed16806dad
Evidence bytes: 9322
Evidence SHA-256: 478d6b113ef618752e3ada8ddf3cbadd3fd10cecd7ee2771c21ae6eafd2b7a6d
```

Durable evidence:

- `02-03-okx-prospective-price-linkage-metadata-evidence.json`
- `02-03-okx-prospective-price-linkage-metadata-evidence.yaml`
- `02-03-okx-prospective-price-linkage-metadata-evidence.md`
- `02-03-okx-prospective-price-linkage-metadata-gate.yaml`

## Verified source identities

```text
Spot traded instrument: BTC-USDT
Swap traded instrument: BTC-USDT-SWAP
Mark-price instrument: BTC-USDT-SWAP
Index identity: BTC-USDT
```

```text
Spot and swap ticker schema SHA-256:
a0efda49b5a0800771ceb73e426c7ea32649d12ec43296cc9a08f4864dbd2c78

Mark-price schema SHA-256:
6bf8819de4ac4a636c639c06322c30591d1834517402895b9b830916d0bbbe3f

Index-ticker schema SHA-256:
9aa78fdea927d6e3737b088b7a504f68be1b444aec4fe63acee5222d3ee7ef12
```

Name similarity is not treated as sufficient executable linkage. Each source is bound to its exact endpoint, query contract, identity fields, schema, and response fingerprint.

## Timing and cache evidence

```text
Provider timestamps monotonic in request order: false
Provider timestamp spread: 1116 ms
Provider timestamp after response: false for every source
```

Request order differed from provider-timestamp order. This is an admitted timing diagnostic consistent with independently cached market-data services. Provider timestamps are preserved per source and are not rewritten, interpolated, or forced into request order.

## Safe-retention boundary

The live responses were validated for finite numeric market fields, but the durable evidence retains no:

```text
last price
bid or ask
mark price
index price
volume
raw response body
ordered reconstructable price series
public market row
```

Retained evidence is limited to source identity, endpoint and query identity, response hashes, schema fingerprints, instrument/index identity fields, source-specific timestamps, clocks, age diagnostics, and source health.

## Admitted authorization

```yaml
okx_prospective_price_linkage_metadata_pilot: true
okx_spot_swap_mark_index_identity_monitoring: true
okx_price_source_schema_monitoring: true
okx_provider_timestamp_monitoring: true
okx_cache_behavior_monitoring: true
safe_price_source_hash_and_metadata_retention: true
```

## Explicit non-authorization

```yaml
historical_backfill: false
persistent_raw_market_values: false
raw_redistribution: false
basis_computation: false
funding_pnl_computation: false
returns_computation: false
transaction_cost_estimation: false
empirical_fitting: false
parameter_tuning: false
strategy_testing: false
paper_trading: false
live_trading: false
leverage: false
capital_deployment: false
report_2_4_authorized: false
```

## Remaining blocker after Issue #53

The source identities and current metadata contracts are now verified, but executable research remains blocked by the absence of a separately admitted contract for:

```text
bounded private retention of market values
synchronized multi-source sampling
sampling failure and partial-batch handling
provider timestamp staleness limits
revision and supersession handling
raw-value deletion and audit receipts
transaction-cost and executable-price semantics
```

The next gate may investigate these contracts. It may not compute basis, funding PnL, returns, costs, or strategy performance.
