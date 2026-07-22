# Verified Disabled-by-Default Owner-Side OKX One-Batch Runner

**Issue:** #55  
**Runner outcome:** `GO_OWNER_SIDE_OKX_ONE_BATCH_RUNNER_READY`  
**Real execution status:** `NOT_EXECUTED_REQUIRES_OWNER_PRIVATE_STORAGE_AND_KEYS`  
**Validation mode:** `SYNTHETIC_INJECTED`

## 1. What is ready

The project now contains an owner-side CLI that can retain exactly one four-source OKX batch only after explicit activation, path separation, retention bounds, terms, scale, redistribution, encryption, access, backup/sync, public-upload, private-storage, encryption-key, and owner-confirmation controls pass.

Commands:

```text
python scripts/run_okx_owner_private_sampling.py retain ...
python scripts/run_okx_owner_private_sampling.py delete ...
```

The CLI is disabled by default. A real retain operation requires the exact confirmation phrase:

```text
I_CONFIRM_OWNER_CONTROLLED_PRIVATE_OKX_RAW_SAMPLING
```

Deletion requires the independent phrase:

```text
I_CONFIRM_DELETE_OWNER_CONTROLLED_OKX_RAW_BATCH
```

## 2. Verified workflow

```text
Workflow: OKX Owner-Side One-Batch Runner
Run ID: 29832572073
Triggering head: 16c245f05cb5f173185aaed0fb49ef4c0af0e14d
Permissions: contents read-only
Conclusion: SUCCESS
Official network fetcher used: false
```

```text
Formatting: PASS
Lint: PASS
Mypy: PASS
Combined tests: 28 PASS
CLI help: PASS
Synthetic retain/delete lifecycle: PASS
Independent safe-evidence verifier: PASS
```

Normalization:

```text
Exact Ruff bot commit: 43c82fe69cc05e910cd4a5a42a05740cc9e2ae28
Clock guard: research_available_at = max(now, response_received_at)
One-shot normalization workflow removed: true
```

Artifact:

```text
Artifact ID: 8495921479
Artifact digest: sha256:e9179034da965c270ebfe5c40e966aceb5f6822c0a09c1888a4739c7f4b50670
Evidence bytes: 8770
Evidence SHA-256: e5757753519bf0f8ff15311e1090095a5af24b4868c6ec788f0519211e4ccc30
```

## 3. Frozen source order

The synthetic validator requested exactly:

```text
https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT
https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT-SWAP
https://www.okx.com/api/v5/public/mark-price?instType=SWAP&instId=BTC-USDT-SWAP
https://www.okx.com/api/v5/market/index-tickers?instId=BTC-USDT
```

Synthetic mode cannot use the official network fetcher. The public real-execution function does not expose an injectable fetcher.

## 4. Fail-before-retain behavior

The runner fetches and validates all four responses before constructing the private store or retaining any raw artifact.

Verified behavior:

```text
Fetch failure on source three: no private raw directory created
Wrong confirmation: rejected
Missing real-network enable flag: rejected
Missing owner storage/key attestations: rejected
Safe manifest inside private raw tree: rejected
Existing safe manifest output: rejected
Synthetic mode with official fetcher: rejected
Real executor with synthetic configuration: rejected
```

## 5. Retain and rollback behavior

Successful synthetic execution produced:

```text
Private artifacts before delete: 4
Leases before delete: 4
Safe manifest mode: 0600
Safe manifest bytes: 4909
Safe manifest SHA-256: 4c201942468115f31591f77f7c561b03c04bfc575df82339ae70cba3a2dced2a
```

A forced safe-manifest write failure caused all four retained artifacts to be deleted through the normal rollback path. No raw or lease file remained.

## 6. Independent delete command

The delete command loaded the safe manifest, recovered the content-addressed batch identity, deleted every raw artifact and lease, and wrote a separate safe receipt.

```text
Raw artifacts after delete: 0
Leases after delete: 0
All raw deleted: true
All leases deleted: true
Integrity matched before deletion: true for every source
Secure erase claimed: false
```

## 7. Public evidence boundary

Neither the safe manifest, deletion receipt, CI evidence, nor console summary contains injected fake market values.

Retained safe fields include:

```text
batch ID
artifact IDs
source IDs
raw SHA-256 identities
byte counts
source object-key hashes
request / response / provider / research clocks
lease creation and expiry times
policy and license snapshot IDs
safe manifest path and SHA-256
```

No last, bid, ask, mark, index, volume, raw response body, or reconstructable ordered price series is published.

## 8. Real execution inputs still missing

The code is ready, but this environment has not supplied:

```text
owner-controlled private storage path
owner-controlled encryption keys
encryption-at-rest attestation
owner-only access attestation
backup/sync exclusion
public-upload disablement
explicit owner confirmation
```

Therefore:

```text
Real OKX request performed: false
Real raw sampling executed: false
```

## 9. Explicit non-authorization

```text
Historical backfill: false
Public raw artifact: false
Basis computation: false
Funding PnL: false
Returns: false
Transaction-cost estimation: false
Empirical fitting: false
Parameter tuning: false
Strategy testing: false
Paper/live trading: false
Leverage: false
Capital deployment: false
Report 2.4: blocked
Economic edge: not established
```
