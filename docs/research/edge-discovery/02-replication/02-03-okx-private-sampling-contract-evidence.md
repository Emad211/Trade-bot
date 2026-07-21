# Verified Owner-Controlled Private OKX Sampling Contract

**Issue:** #54  
**Contract outcome:** `GO_OWNER_CONTROLLED_PRIVATE_OKX_SAMPLING_CONTRACT`  
**Real execution status:** `NOT_EXECUTED_REQUIRES_OWNER_PRIVATE_STORAGE_AND_KEYS`  
**Validation mode:** `SYNTHETIC_VALIDATION`

## 1. What this gate proves

The gate proves that a four-source OKX sampling batch can be handled by the existing content-addressed revocable store under a bounded, owner-only contract with:

- exact four-source membership;
- source-specific request, response, provider, and research clocks;
- private storage outside the repository;
- `0700` storage directories and `0600` raw/lease files;
- per-source and total-batch byte guards;
- a maximum seven-day sampling lease;
- deterministic batch identity;
- rollback after a simulated mid-batch failure;
- compliance snapshots;
- full-batch deletion and safe receipts;
- zero raw-value leakage into public evidence.

It does not prove that a real OKX raw-value batch has been retained.

## 2. Verified workflow

```text
Workflow: OKX Private Synchronized Sampling Contract
Run ID: 29830415024
Triggering head: c0514d688dcd87ed1a6c17a90ef3e386f39670c7
Permissions: contents read-only
Conclusion: SUCCESS
Real OKX request performed: false
```

```text
Formatting: PASS
Lint: PASS
Mypy: PASS
Private batch tests: 10 PASS
Existing revocable-retention tests: PASS
Synthetic retain/delete lifecycle: PASS
Independent safe-evidence verifier: PASS
```

Artifact:

```text
Artifact ID: 8495050218
Artifact digest: sha256:a0af175026ebf1f3e0ca3574b0432062616023e99b6abb42dea362ce78cefd95
Evidence bytes: 7852
Evidence SHA-256: 44a96f43fb903a941a5a961b66011e6a4d4690801c5bfea381e8cee09b088523
```

## 3. Synthetic batch evidence

```text
Contract ID: OKX_PRIVATE_SYNCHRONIZED_PRICE_SAMPLING_V1
Batch ID: sha256-ff6aaf21ac9a18d2b15c138fba361d54203dba852cdcc9baa4e19da291bd1598
Source count: 4
Total synthetic bytes: 431
Requested lease: 2 days
```

Source order:

```text
OKX_SPOT_BTC_USDT_TICKER
OKX_SWAP_BTC_USDT_SWAP_TICKER
OKX_SWAP_BTC_USDT_SWAP_MARK_PRICE
OKX_BTC_USDT_INDEX_TICKER
```

The synthetic provider timestamps were intentionally non-monotonic. The contract retained their exact source-specific values and did not force them into request order.

## 4. Atomicity and rollback

The contract rejects missing, unknown, empty, oversized, excessive-retention, and future-skew inputs before admitting a complete batch.

A simulated failure on the third retain operation caused the first two retained artifacts to be deleted through the normal deletion path. No raw or lease record remained after rollback; safe tombstones remained for audit.

## 5. Retention and deletion proof

Before deletion:

```text
Active artifacts: 4
Compliance: true
```

After deletion:

```text
Raw artifacts remaining: 0
Lease records remaining: 0
Active artifacts: 0
Compliance: true
Integrity matched before deletion: true for all four sources
Secure erase claimed: false
```

The public evidence retained only hashes, byte counts, source IDs, artifact IDs, clocks, policy IDs, lease timestamps, and deletion status. It contains no raw response or synthetic market value.

## 6. Terms interpretation

The API agreement is treated as applicable to public Market Data even without authentication. The admitted purpose is owner-internal, personal, non-commercial research; redistribution, publication, high-scale extraction, and rate-limit circumvention remain prohibited.

The project uses a short revocable lease and deletion receipts as conservative internal controls. It does not claim that the historical-data deletion clause is automatically an explicit legal obligation for every live public API response.

## 7. Exact authorization boundary

The GO authorizes:

```text
owner-controlled private sampling contract implementation
synthetic lifecycle validation in CI
one-batch owner-side execution capability after explicit owner attestations
safe non-market manifest and deletion receipts
```

The following remain false:

```text
Real raw sampling executed in this environment
GitHub Actions raw sampling
Public raw artifacts
Historical backfill
Basis computation
Funding PnL
Returns
Transaction-cost estimation
Empirical fitting or tuning
Strategy testing
Paper/live trading
Leverage
Capital deployment
Report 2.4
```

## 8. Remaining execution blocker

A real one-batch run requires all of the following outside the repository and outside public CI:

```text
owner-controlled private storage path
owner-controlled encryption keys
encryption-at-rest attestation
owner-only access attestation
backup and sync exclusion
public upload disabled
explicit owner confirmation for real execution
```

Until these conditions are supplied and a separate owner-side run is explicitly performed, the execution state remains:

```text
NOT_EXECUTED_REQUIRES_OWNER_PRIVATE_STORAGE_AND_KEYS
```
