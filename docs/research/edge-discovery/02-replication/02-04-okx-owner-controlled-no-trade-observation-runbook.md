# Owner Runbook — One OKX No-Trade Observation

**Gate:** Issue #61  
**Execution location:** the owner's local machine only  
**Current state:** package preparation and synthetic verification; no real execution has occurred.

## Purpose

This runbook performs exactly one owner-confirmed observation consisting of:

1. two account-specific fee snapshots from `GET /api/v5/account/trade-fee`;
2. four public OKX source responses;
3. health and exact batch-admission checks;
4. owner-private retention with safe manifests and receipts;
5. no order, cancel, amendment, transfer, withdrawal or account-setting change.

It does not calculate basis, funding PnL, returns or transaction costs.

## API-key requirements

Create an OKX API key yourself in the OKX interface. Do not send the key, secret or passphrase through chat, email, GitHub, CI, issue comments or logs.

Required configuration:

```text
Read: enabled
Trade: disabled
Withdraw: disabled
IP allowlist: enabled
```

Delete and recreate the key if Trade or Withdraw is enabled. Use a separate key for this observation; do not reuse a trading key.

## Private storage requirements

Choose an encrypted owner-controlled directory outside the repository and outside cloud-sync or backup folders. The run refuses a private root inside the repository.

Expected permissions:

```text
private directories: 0700
private files: 0600
retention: 1–7 days
```

Safe manifests still must remain outside the repository because they identify the owner's run lifecycle.

## Local credential environment

Enter these values only in the owner's local shell or local secret manager:

```bash
export OKX_API_KEY='<owner-local-value>'
export OKX_SECRET_KEY='<owner-local-value>'
export OKX_PASSPHRASE='<owner-local-value>'
```

Do not put them in `.env` inside the repository. Avoid shell-history exposure by using a local secret manager or a protected interactive prompt mechanism.

## Preflight

Resolve the exact code head before running:

```bash
HEAD_SHA="$(git rev-parse HEAD)"
```

Run the command below with owner-selected absolute paths. It validates policy, paths, permissions, attestations and local credential presence, but performs no network request:

```bash
python scripts/run_okx_no_trade_observation.py preflight \
  --private-root '/absolute/encrypted/private/okx-observation' \
  --repository-root "$(git rev-parse --show-toplevel)" \
  --private-fee-snapshot-output '/absolute/encrypted/private/okx-observation/fee-snapshot.json' \
  --safe-batch-manifest-output '/absolute/private-safe/okx-batch-manifest.json' \
  --safe-observation-receipt-output '/absolute/private-safe/okx-observation-receipt.json' \
  --policy configs/okx_no_trade_observation_policy_v1.yaml \
  --code-head-sha "$HEAD_SHA" \
  --api-domain www.okx.com \
  --retention-days 2 \
  --confirm I_CONFIRM_OWNER_CONTROLLED_OKX_NO_TRADE_OBSERVATION \
  --enable-public-network-fetch \
  --enable-private-network-fetch \
  --attest-terms-reviewed \
  --attest-personal-noncommercial-use \
  --attest-reasonable-rate-and-scale \
  --attest-redistribution-disabled \
  --attest-encryption-at-rest \
  --attest-owner-only-access \
  --attest-backup-and-sync-excluded \
  --attest-public-artifact-upload-disabled \
  --attest-owner-controlled-private-storage \
  --attest-owner-controlled-encryption-keys \
  --attest-real-execution-owner-confirmed \
  --attest-read-permission-enabled \
  --attest-trade-permission-disabled \
  --attest-withdraw-permission-disabled \
  --attest-ip-allowlist-enabled \
  --attest-credentials-outside-repository \
  --attest-credentials-outside-ci \
  --attest-credentials-not-logged
```

Expected preflight claims:

```text
network_request_performed=false
orders_sent=false
trade_permission_used=false
withdraw_permission_used=false
credential_values_printed=false
```

## Observation

Only after preflight passes, change `preflight` to `observe` without changing any other argument. The package will:

- issue two exact read-only fee requests;
- collect the four public source responses;
- reject unhealthy or incomplete batches before private raw retention;
- write private fee/raw content only under the owner-controlled root;
- write safe hash/state receipts at the selected private-safe paths.

No order-capable endpoint exists in the package allowlist. Authenticated private requests also reject every HTTP redirect before credentials can be replayed to a second URL.

## Immediate inspection

Check file modes and ensure no output path is in the repository:

```bash
stat -c '%a %n' \
  '/absolute/encrypted/private/okx-observation/fee-snapshot.json' \
  '/absolute/private-safe/okx-batch-manifest.json' \
  '/absolute/private-safe/okx-observation-receipt.json'

git status --short
```

Do not print the private fee snapshot or raw response files to the terminal.

## Deletion

Delete the observation at the end of the bounded review or before its lease expires:

```bash
python scripts/run_okx_no_trade_observation.py delete \
  --private-root '/absolute/encrypted/private/okx-observation' \
  --repository-root "$(git rev-parse --show-toplevel)" \
  --private-fee-snapshot '/absolute/encrypted/private/okx-observation/fee-snapshot.json' \
  --safe-batch-manifest '/absolute/private-safe/okx-batch-manifest.json' \
  --safe-observation-receipt '/absolute/private-safe/okx-observation-receipt.json' \
  --safe-deletion-receipt-output '/absolute/private-safe/okx-deletion-receipt.json' \
  --reason 'OWNER_REVIEW_COMPLETE' \
  --confirm I_CONFIRM_DELETE_OWNER_CONTROLLED_OKX_NO_TRADE_OBSERVATION \
  --attest-terms-reviewed \
  --attest-personal-noncommercial-use \
  --attest-reasonable-rate-and-scale \
  --attest-redistribution-disabled \
  --attest-encryption-at-rest \
  --attest-owner-only-access \
  --attest-backup-and-sync-excluded \
  --attest-public-artifact-upload-disabled
```

The deletion receipt explicitly does not claim secure erase.

## Stop conditions

Do not proceed if any of these is true:

- Trade or Withdraw permission is enabled;
- the API key is not IP-bound;
- private storage is inside the repository or a sync folder;
- preflight fails;
- any source is stale, partial, duplicated, skewed or quarantined;
- any output already exists;
- the code head differs from the reviewed Gate #61 head;
- a request or output asks for balance, fills, bills, positions, orders or PnL;
- the provider responds with any redirect for the authenticated fee request.

A successful owner run is still only a no-trade observation. It is not a basis, PnL, return, transaction-cost, strategy or Report 2.4 authorization.
