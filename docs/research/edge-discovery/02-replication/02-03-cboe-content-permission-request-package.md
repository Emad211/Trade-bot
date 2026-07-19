# Cboe Content Permission Request Package

**Project:** Edge Discovery Research Program  
**Status:** `PREPARED_NOT_SENT`  
**Prepared:** 2026-07-19

This package is a reusable request for written permission. It must not be represented as submitted, approved, or licensed until a real response and executed agreement exist.

## Official submission routes

Primary permission instructions:

```text
https://www.cboe.com/en/use-of-content/
```

The request should be sent to the contact address displayed on the official Use of Cboe Content page.

Market-data licensing contact and documentation:

```text
marketdata@cboe.com
https://www.cboe.com/market_data_services/document_library/
https://www.cboe.com/market_data_services/onboarding
```

Do not send credentials, financial account details, raw Cboe files, or unrelated personal data with the initial request.

## Suggested subject

```text
Permission request — private non-commercial research use of historical CFE VX contract data
```

## Request body

```text
Dear Cboe Content / Market Data Licensing Team,

I am requesting written permission for a limited, private, non-commercial research use of historical Cboe Futures Exchange VIX futures data.

Requester

Name: [FULL LEGAL NAME]
Title / role: Independent researcher and software developer
Organization: Independent non-commercial research project
Email: [EMAIL]
Country of residence: [COUNTRY]
Complete contact information: [POSTAL ADDRESS AND TELEPHONE, IF REQUIRED]

Project purpose

The project studies whether public CFTC Traders in Financial Futures positioning observations contain incremental information after their real publication delay. The work is methodological and research-oriented. It is not a brokerage service, data-vending service, index product, advisory product, trading signal subscription, or public market-data display.

Requested Cboe content

Initial bounded scope:

- CFE VX historical contract file expiring 2022-09-21;
- CFE VX historical contract file expiring 2022-10-19;
- associated contract metadata, settlement fields, volume, open interest, and lifecycle dates;
- current and historical documentation needed to interpret the files.

A later extension to additional standard monthly VX contract files would be requested separately or included only if Cboe expressly approves it.

Requested uses

I request permission to:

1. download exact historical contract files from official Cboe locations;
2. retain one private electronic research copy of each approved file;
3. store the approved files in encrypted, access-controlled, content-addressed private storage;
4. calculate SHA-256 hashes, byte counts, schema fingerprints, and provenance metadata;
5. parse the files for internal research;
6. combine approved Cboe observations with public CFTC positioning observations;
7. create private derived research fields and contract-specific return calculations;
8. retain private derived datasets required for reproducibility;
9. publish open-source parser and validation code that contains no Cboe price rows;
10. publish only aggregate statistical findings, methodology, source citations, hashes, and non-sensitive lineage metadata;
11. retain the approved private research materials for [REQUESTED RETENTION PERIOD, E.G. TEN YEARS].

Distribution and display

No raw or row-level Cboe data would be:

- committed to a public Git repository;
- displayed on a public website;
- distributed to third parties;
- sold, sublicensed, or included in a commercial product;
- used to create a public index or market-data service.

The public repository would contain only source code, synthetic test fixtures, documentation, source URLs, hashes, byte counts, schema descriptions, and aggregate research conclusions, subject to any additional restrictions required by Cboe.

Security and access

Access to retained Cboe content would be limited to the requester unless Cboe separately approves additional named researchers. Storage would use encryption, least-privilege access, immutable object identity, a deletion policy, and an audit log.

Exact research timing

The research distinguishes:

- CFTC report-as-of time;
- CFTC public release time;
- CFE settlement calculation time;
- Cboe publication time;
- data retrieval time;
- strategy decision and execution time.

No historical observation would be treated as available before documented publication. No continuous or back-adjusted futures series would be substituted for contract-level data.

Commercial status

The current project has no paying users, subscribers, commercial data redistribution, managed accounts, live trading authorization, or capital deployment. If that status changes, I would seek a new or amended permission before expanding use.

Requested clarification

Please confirm whether Cboe can grant permission for the uses above and identify:

- the applicable agreement or license;
- any fees;
- geographic or eligibility restrictions;
- permitted private retention period;
- restrictions on internal derived datasets;
- restrictions on publication of aggregate statistical results;
- required attribution language;
- audit, reporting, or deletion obligations;
- whether the historical contract files were publicly available contemporaneously or are later archives;
- any official source for historical publication timestamps.

I understand that submitting this request does not grant permission and that use beyond the existing website terms may begin only after written approval and execution of any required agreement by both parties.

Sincerely,

[FULL LEGAL NAME]
[EMAIL]
[CONTACT INFORMATION]
```

## Attachments or links to include

The official request instructions ask for samples or links showing intended use when applicable. The following project links may be provided after review:

```text
Public repository:
https://github.com/Emad211/Trade-bot

Draft research PR:
https://github.com/Emad211/Trade-bot/pull/41
```

Recommended accompanying explanation:

- raw and derived Cboe price rows are not published;
- the permanent workflow deletes restricted content before artifact upload;
- only hash and schema evidence is retained publicly;
- price linkage and returns remain disabled pending permission.

Do not attach the raw Cboe CSV files unless Cboe explicitly requests them through an approved secure channel.

## Required internal record after submission

Create a new evidence record containing:

```yaml
submitted_at: null
submission_channel: null
recipient_identity: null
request_sha256: null
provider_response_received_at: null
provider_response_sha256: null
approval_status: NOT_SUBMITTED
license_agreement_id: null
license_effective_at: null
license_expiration_at: null
permitted_uses: []
prohibited_uses: []
fees: null
```

No status may be upgraded from `PREPARED_NOT_SENT` without independently retained submission and response evidence.
