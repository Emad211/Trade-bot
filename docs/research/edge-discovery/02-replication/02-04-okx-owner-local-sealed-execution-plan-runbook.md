# Owner Runbook — Sealed One-Time OKX No-Trade Execution

**Gate:** Issue #63  
**Predecessor:** Issue #61  
**Execution location:** owner local machine only  
**Real execution status:** not executed

## Why this runbook supersedes the direct Gate #61 command

Gate #61 proved the no-trade observation package. Gate #63 adds the missing
operational binding between preflight and observe:

- the actual Git head must equal the reviewed head;
- the Git worktree must be clean at both commands;
- preflight writes a short-lived HMAC-authenticated plan;
- observe must consume that exact plan;
- an atomic claim is written before any network request;
- the plan cannot be replayed, even after a failed or interrupted observation.

Do not use an older direct `observe` command that does not provide a sealed plan
and a fresh claim path.

## Non-negotiable prerequisites

1. Checkout the exact head recorded in the final Issue #63 closure receipt.
2. `git status --short` must be empty.
3. Use a dedicated IP-bound OKX key with:

```text
Read: enabled
Trade: disabled
Withdraw: disabled
```

4. Keep credentials in a local secret manager or protected shell environment.
5. Use encrypted private storage outside the repository and outside sync/backup folders.
6. Never send credential values, plan files, claim files, raw payloads, or fee snapshots through chat or GitHub.

## Local environment

```bash
export OKX_API_KEY='<owner-local-value>'
export OKX_SECRET_KEY='<owner-local-value>'
export OKX_PASSPHRASE='<owner-local-value>'
```

Avoid command-history exposure. The CLI has no credential-value arguments.

## Resolve and verify the reviewed head

Replace the placeholder with the exact immutable head from the Issue #63 closure comment:

```bash
REVIEWED_HEAD='<issue-63-exact-head>'
ACTUAL_HEAD="$(git rev-parse HEAD)"
test "$ACTUAL_HEAD" = "$REVIEWED_HEAD"
test -z "$(git status --porcelain=v1 --untracked-files=normal)"
```

The CLI repeats both checks. Supplying a valid-looking SHA does not bypass them.

## Owner-local paths

Choose absolute paths. These examples are placeholders:

```bash
PRIVATE_ROOT='/absolute/encrypted/private/okx-observation'
SAFE_ROOT='/absolute/owner-safe/okx-observation'
PLAN="$SAFE_ROOT/sealed-plan.json"
CLAIM="$SAFE_ROOT/execution-claim.json"
FEE_SNAPSHOT="$PRIVATE_ROOT/fee-snapshot.json"
BATCH_MANIFEST="$SAFE_ROOT/batch-manifest.json"
OBSERVATION_RECEIPT="$SAFE_ROOT/observation-receipt.json"
DELETION_RECEIPT="$SAFE_ROOT/deletion-receipt.json"
```

All output files must be new. The plan and claim are written `0600`. Their file contents and parent-directory entries are synchronously flushed before the operation is accepted. If the local runtime/filesystem cannot provide parent-directory `fsync`, the Gate fails closed; use a compatible owner-controlled Linux/WSL filesystem rather than weakening the durability contract.

## Step 1 — sealed preflight

Preflight performs no network request. It validates the checkout, clean worktree,
policy, paths, attestations and credential presence, then writes a ten-minute plan.

```bash
python scripts/run_okx_no_trade_observation.py preflight \
  --private-root "$PRIVATE_ROOT" \
  --repository-root "$(git rev-parse --show-toplevel)" \
  --private-fee-snapshot-output "$FEE_SNAPSHOT" \
  --safe-batch-manifest-output "$BATCH_MANIFEST" \
  --safe-observation-receipt-output "$OBSERVATION_RECEIPT" \
  --policy configs/okx_no_trade_observation_policy_v1.yaml \
  --code-head-sha "$REVIEWED_HEAD" \
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
  --attest-credentials-not-logged \
  --sealed-execution-plan-output "$PLAN" \
  --plan-claim-output "$CLAIM" \
  --safe-deletion-receipt-output "$DELETION_RECEIPT" \
  --plan-ttl-seconds 600
```

Expected claims include:

```text
preflight=PASS
actual_git_head_sha=<reviewed head>
clean_worktree=true
network_request_performed=false
credential_values_printed=false
orders_sent=false
Report_2_4_authorized=false
```

Do not edit the plan. Do not change any argument before observe.

## Step 2 — consume the plan exactly once

Run before the plan expires. Use the same values and add the sealed plan path:

```bash
python scripts/run_okx_no_trade_observation.py observe \
  --private-root "$PRIVATE_ROOT" \
  --repository-root "$(git rev-parse --show-toplevel)" \
  --private-fee-snapshot-output "$FEE_SNAPSHOT" \
  --safe-batch-manifest-output "$BATCH_MANIFEST" \
  --safe-observation-receipt-output "$OBSERVATION_RECEIPT" \
  --policy configs/okx_no_trade_observation_policy_v1.yaml \
  --code-head-sha "$REVIEWED_HEAD" \
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
  --attest-credentials-not-logged \
  --sealed-execution-plan "$PLAN" \
  --plan-claim-output "$CLAIM" \
  --safe-deletion-receipt-output "$DELETION_RECEIPT" \
  --plan-ttl-seconds 600
```

Before either public or private network access, the CLI atomically creates the
claim. If execution fails or the process is interrupted afterward, the plan is
consumed. Do not delete the claim and retry. Create a new plan with a new preflight.

## Step 3 — inspect without printing private values

```bash
stat -c '%a %n' "$PLAN" "$CLAIM" "$FEE_SNAPSHOT" "$BATCH_MANIFEST" "$OBSERVATION_RECEIPT"
git status --short
```

Do not `cat` the fee snapshot, raw payloads, plan, or claim into shared terminals or logs.

## Step 4 — deletion

Use the Gate #61 deletion command after review or before lease expiry. The deletion
receipt path must be the same path bound into the sealed plan.

```bash
python scripts/run_okx_no_trade_observation.py delete \
  --private-root "$PRIVATE_ROOT" \
  --repository-root "$(git rev-parse --show-toplevel)" \
  --private-fee-snapshot "$FEE_SNAPSHOT" \
  --safe-batch-manifest "$BATCH_MANIFEST" \
  --safe-observation-receipt "$OBSERVATION_RECEIPT" \
  --safe-deletion-receipt-output "$DELETION_RECEIPT" \
  --reason OWNER_REVIEW_COMPLETE \
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

The deletion receipt does not claim secure erase.

## Mandatory stop conditions

Stop and create a new preflight if any of these occurs:

- head mismatch or dirty worktree;
- plan expiry, authentication failure or configuration mismatch;
- a claim file already exists;
- credentials differ from preflight;
- any output path or policy changes;
- Trade or Withdraw is enabled;
- key is not IP-bound;
- any authenticated redirect occurs;
- any source is stale, incomplete, duplicated, skewed or quarantined;
- any request asks for balances, orders, fills, bills, positions or PnL.

A completed sealed observation is still only a no-trade data observation. It does
not authorize basis, funding PnL, returns, transaction costs, strategy testing,
Report 2.4, paper/live trading, leverage or capital deployment.
