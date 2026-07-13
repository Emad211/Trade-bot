# Security policy

## Scope

Phase 1 is a research-only package. It does not accept exchange credentials and it
cannot place live orders. Public market-data downloads are optional and use CCXT
without API keys.

## Reporting a vulnerability

Do not open a public issue containing credentials, private endpoints, account data,
or an exploitable security defect. Use GitHub's private vulnerability-reporting
feature when enabled, or contact the repository owner privately.

## Operational rules for later phases

- Never commit API keys, wallet seeds, exchange cookies or KYC material.
- Trading keys must have withdrawals disabled and should use venue IP allowlists.
- Secrets must be provided at runtime by a secret manager or local environment file.
- Every order command must use an idempotent client order ID and reconciliation.
- Loss limits, stale-data guards and kill switches must remain deterministic; an LLM
  must never be able to override them.
- Residency, KYC, sanctions, custody and withdrawal eligibility must be verified
  independently for every venue before enabling live access.
