# Report 2.3M — OKX 2022 Historical Funding Delivery and Revocable-Retention Gate

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Issue:** `#50`  
**Decision date:** 2026-07-21  
**Gate outcome:** `GO_PRIVATE_REVOCABLE_2022_FUNDING_PILOT`

---

## 1. Decision

The project verified that OKX can deliver a bounded historical funding archive for the `BTC-USDT` perpetual family for March 2022 through the official historical-data service.

The project also implemented and independently tested an owner-controlled revocable-retention lifecycle.

The authorized next scope is therefore:

```text
one private bounded raw pilot
venue: OKX
instrument family: BTC-USDT
contract identity: BTC-USDT-SWAP
initial calendar scope: 2022-03 only
maximum raw retention: 30 days
purpose: personal strategy research only
```

This decision does **not** authorize:

- public raw artifacts;
- redistribution or sublicensing;
- bulk historical acquisition;
- permanent or non-revocable raw storage;
- returns, basis, or funding-PnL computation;
- empirical fitting or parameter tuning;
- paper or live trading;
- leverage or capital deployment;
- Report 2.4.

---

## 2. Official terms boundary

Frozen official references:

```text
Historical Data Terms and Conditions:
https://www.okx.com/en-gb/help/historicaldata-terms-and-conditions

OKX API Agreement:
https://www.okx.com/en-ae/help/okx-api-agreement
```

Controlling interpretation for this project:

```text
Personal possession/retention: allowed under the limited license
Development of the owner's own strategy: allowed
Redistribution: prohibited
Sublicensing: prohibited
License: limited and revocable
Deletion on revocation or expiry: required
Regional, account, KYC, payment, and technical controls: must not be circumvented
```

The project does not represent this as a permanent-data license or as a right to publish OKX market data.

The frozen machine-readable contract is:

- [OKX private revocable retention contract](02-03-okx-private-revocable-retention-contract.yaml)

---

## 3. Exact delivery contract

Static analysis of the official historical-data page bundles established the request contract used by the official UI:

```text
Method:
POST

Endpoint:
https://www.okx.com/priapi/v5/broker/public/trade-data/download-link

Funding module:
3

Instrument type:
SWAP

Instrument-family field:
instFamilyList

Date aggregation:
monthly
```

The bounded March 2022 request was:

```json
{
  "module": "3",
  "instType": "SWAP",
  "instQueryParam": {
    "instFamilyList": ["BTC-USDT"]
  },
  "dateQuery": {
    "dateAggrType": "monthly",
    "begin": "1646092800000",
    "end": "1648684800000"
  }
}
```

Authentication headers and cookies were not used.

---

## 4. Metadata-only delivery verification

Hosted run:

```text
Workflow:
OKX Historical 2022 Monthly Export Metadata Probe

Run ID:
29810652877

Conclusion:
SUCCESS
```

Safe artifact:

```text
Artifact ID:
8487263912

Artifact digest:
sha256:72e8228e6dbec9600d9538cf2b839052d135cc6834825bece7e2f658d6daaac3
```

Observed response:

```text
HTTP status: 200
Application code: 0
Details: 1
Instrument family: BTC-USDT
Instrument ID field: empty, as expected for family-level monthly selection
File count: 1
Reported size: 0.002 MB
```

Safe official file identity:

```text
Host:
static.okx.com

Path:
/cdn/okex/traderecords/swaprates/monthly/202203/BTC-USDT-SWAP-fundingrates-2022-03.zip

Filename:
BTC-USDT-SWAP-fundingrates-2022-03.zip
```

The metadata probe did not follow or download the file. Query values and reconstructable signed links were not retained.

---

## 5. Ephemeral real-file validation

Hosted run:

```text
Workflow:
OKX 2022 Funding Ephemeral File Validation

Run ID:
29811051931
```

The workflow's provider acquisition, ZIP validation, safe-evidence verification, deletion verification, and evidence upload steps succeeded.

The overall workflow conclusion was `FAILURE` because a final repository scan was initially written too broadly and flagged unrelated pre-existing CSV files in the repository. That false-positive does not alter the raw-file validation or deletion evidence. It is retained as a negative engineering finding and is not represented as a fully green workflow.

Safe evidence artifact:

```text
Artifact ID:
8487415309

Artifact digest:
sha256:806ed03e82d17be2ecc3cde7e374f16898363c1c9c1ee1fc380338c088a6d082

Evidence JSON SHA-256:
4123d7c54ae18829ac0aca2d3d3f4abb16be41fb965506f2bb9301b829c954
```

### 5.1 Raw ZIP identity

```text
Filename:
BTC-USDT-SWAP-fundingrates-2022-03.zip

Byte count:
1,403

SHA-256:
ce4fe9aaf1dfdee16e1d11cdabcbb405eb348966902950db1ca862dc86779013

HTTP status:
200

ZIP signature:
valid

CRC:
valid

Encrypted members:
0

Path traversal:
not detected
```

The ZIP was written only under `RUNNER_TEMP` in a mode-`0700` private directory and a mode-`0600` file.

### 5.2 CSV member identity and schema

```text
Member:
BTC-USDT-SWAP-fundingrates-2022-03.csv

Uncompressed byte count:
4,546

Compressed byte count:
1,235

CRC32:
01e95991

SHA-256:
508195adcc2fd9e9a1978926d8da89af4054d79de4675268cbfb2ac9539e73da
```

Exact fields:

```text
instrument_name
funding_rate
funding_time
```

Header SHA-256:

```text
9a64087a90de9be72d2b9adddc51225bd484e6a717d7a26f20d6adad7860330f
```

### 5.3 Timestamp contract

```text
Rows:
93

Unique funding timestamps:
93

Minimum timestamp:
2022-02-28T16:00:00Z

Maximum timestamp:
2022-03-31T08:00:00Z

Observed interval:
28,800,000 ms

Occurrences of observed interval:
92
```

The minimum UTC timestamp precedes March 1 because the provider's monthly file groups funding events by its own month/file convention. The project preserves the provider timestamps and does not rewrite the first observation.

Funding-rate values were parsed only to confirm numeric validity. They were not serialized, retained in evidence, aggregated, or used for returns or PnL.

### 5.4 Deletion evidence

```text
Delete method:
unlink raw file, then remove ephemeral private directory

Raw file exists after delete:
false

Private directory exists after delete:
false

Raw file uploaded:
false

Raw rows retained:
false

Secure erase claimed:
false
```

The project claims logical deletion and runner teardown, not cryptographic or physical secure erasure of the hosted runner's storage medium.

---

## 6. Private revocable-retention implementation

Implementation:

```text
src/hybrid_trader/replication/revocable_retention.py
```

Tests:

```text
tests/test_revocable_retention.py
```

Dedicated hosted workflow:

```text
Workflow:
OKX Private Revocable Retention Contract

Run ID:
29811639151

Conclusion:
SUCCESS
```

Every dedicated step passed:

- Python 3.11 environment;
- repository Ruff rules;
- strict mypy;
- eight revocable-retention lifecycle tests;
- synthetic retain operation;
- active compliance scan;
- deletion and tombstone creation;
- post-delete compliance scan;
- safe evidence upload.

Safe synthetic evidence artifact:

```text
Artifact ID:
8487687277

Artifact digest:
sha256:abe567eda91894081e3bd842b12b0cd6b0e02d13723dae45316d562abee06b0e

Evidence JSON SHA-256:
28f89edd631d7377c23ed0e63e9fe27c90a9491e0dfa2c58d1c11a59bb46c368

Retention expiry:
2026-10-19
```

The synthetic lifecycle used no provider data.

---

## 7. Enforced storage contract

Persistent private raw storage is refused unless all of the following are explicitly attested:

```text
encryption at rest
owner-only access
backup and synchronization exclusion
public artifact upload disabled
```

Additional enforced rules:

```text
storage root must be outside the repository
root/subdirectories mode: 0700
raw and lease files mode: 0600
content-addressed artifact identity: SHA-256
maximum artifact size: 20 MB
maximum retention: 30 days
no overwrite of an active identity
no reuse of a previously deleted identity
raw/lease integrity validation
orphan and overdue compliance checks
mandatory deletion on expiry/revocation
integrity mismatch must not block deletion
safe tombstone retained after deletion
secure erase is not claimed
```

Deletion triggers include:

- license revocation;
- license expiry;
- lease expiry;
- owner request;
- project cancellation;
- uncertain license scope;
- integrity failure.

---

## 8. Exact authorization consequence

```yaml
outcome: GO_PRIVATE_REVOCABLE_2022_FUNDING_PILOT
one_month_initial_scope: true
owner_controlled_private_storage_only: true
maximum_retention_days: 30
all_storage_attestations_required: true
public_raw_artifact: false
redistribution: false
bulk_download: false
permanent_raw_storage: false
returns: false
basis: false
funding_pnl: false
empirical_fitting: false
parameter_tuning: false
paper_trading: false
live_trading: false
capital_deployment: false
report_2_4_full_authorization: false
```

This gate authorizes the owner to run one bounded private raw pilot only after providing truthful storage attestations. CI success does not attest that the owner's future filesystem is encrypted or excluded from backups.

---

## 9. Remaining unresolved facts

The following are still incomplete:

1. Point-in-time instrument metadata proving the exact 2022 contract state and rule version.
2. Historical `available_at` for each archive version.
3. Provider revision/vintage history for the current downloadable file.
4. A complete multi-month acquisition and supersession ledger.
5. Raw linkage to executable prices, mark prices, and index prices under the same information clock.
6. Funding payment accounting and position-direction semantics.
7. Any return, basis, funding-PnL, capacity, or edge result.

The acquired file is a current provider vintage retrieved in 2026. Its funding timestamps are economic settlement times; they are not proof that the current downloadable archive was available at those timestamps.

All empirical crypto-edge verdicts remain `INCONCLUSIVE`.
