# Security policy

## Current safety boundary

This repository is a research system. It does not accept exchange credentials and
cannot place, cancel or withdraw an order.

Never commit:

- API keys or secrets;
- exchange session cookies;
- wallet seed phrases or private keys;
- identity or KYC documents;
- proprietary market-data credentials;
- real account balances or order exports containing personal data.

## Future exchange adapters

Any future dry-run or live adapter must use:

- a key with withdrawal disabled;
- venue-supported IP restrictions where available;
- an external secret manager;
- idempotent client order IDs;
- independent order/fill/balance reconciliation;
- stale-data and connection-loss kill switches;
- explicit venue and jurisdiction eligibility review.

Report security issues privately to the repository owner rather than opening a
public issue containing secrets or exploitable details.
