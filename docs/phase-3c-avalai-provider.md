# Phase 3C — AvalAI structured semantic provider

Phase 3C connects the prospective Phase 3B event stream to AvalAI as a
**semantic-feature provider only**. The provider cannot create a trading decision,
position size, order, leverage, withdrawal, target price or stop.

## Official provider contract

The implementation follows the current official AvalAI documentation:

- API base URL: `https://api.avalai.ir/v1`;
- authentication: `Authorization: Bearer $AVALAI_API_KEY`;
- preferred new integration: `POST /v1/responses`;
- compatibility fallback: `POST /v1/chat/completions`;
- strict structured output: JSON Schema with `strict: true` and
  `additionalProperties: false`;
- stateless research calls: `store: false`;
- provider trace: response header `x-request-id`;
- client trace: `X-Client-Request-Id`, reused only for retries of the same logical
  idempotent request;
- transient retries only for 429, 500, 502, 503, 504 and network/timeout failures;
- `Retry-After`, capped exponential backoff and jitter are honored;
- 400, 401, 403, 404, 422, policy and unsupported-model errors are not blindly retried.

Official references:

- <https://docs.avalai.ir/fa/quickstart>
- <https://docs.avalai.ir/fa/api-reference/responses>
- <https://docs.avalai.ir/fa/api-reference/chat>
- <https://docs.avalai.ir/fa/guides/structured-outputs>
- <https://docs.avalai.ir/fa/guides/error-handling>
- <https://docs.avalai.ir/fa/guides/production-best-practices>
- <https://docs.avalai.ir/fa/api-reference/response-headers>

## Pinned low-cost model

A secret-free probe of `https://api.avalai.ir/public/models` on 2026-07-16
(run `29507238028`, artifact digest
`sha256:ce75419dc9926160e4ef968fb1a8c4e6baa1c7d948ccb405fab1808d8bd83a23`)
confirmed that `gpt-5-mini-2025-08-07` supports both `/v1/responses` and strict
response schemas. Its advertised input/output prices were lower than the unversioned
`gpt-5.4-mini` alias. Phase 3C therefore pins both `model` and `model_revision` to
`gpt-5-mini-2025-08-07` and rejects a mismatched `response.model`. This prevents an
alias update from silently reusing an old extraction identity.

## Credential handling

`AVALAI_API_KEY` is read only from the process environment or a CI secret. It is
never accepted in YAML, command-line arguments, source files, manifests, ledgers or
artifacts.

Use a dedicated short-lived project key with a small budget and the minimum model
access required by this workflow. Even a deliberately limited key must be injected as
a process or CI secret and must never be committed, passed as a command-line argument
or written to an artifact.

For GitHub Actions, the repository secret name is exactly:

```text
AVALAI_API_KEY
```

The smoke workflow supports manual execution and a branch-scoped review trigger. It
masks the secret before the network request and scans all produced evidence for
credential-shaped strings before upload.

Optional non-secret environment overrides:

```text
AVALAI_BASE_URL
AVALAI_MODEL
AVALAI_MODEL_REVISION
AVALAI_ROUTE
AVALAI_TIMEOUT_SECONDS
AVALAI_MAX_RETRIES
AVALAI_INITIAL_BACKOFF_SECONDS
AVALAI_MAX_BACKOFF_SECONDS
AVALAI_MAX_OUTPUT_TOKENS
AVALAI_MAX_DOCUMENT_CHARS
AVALAI_REASONING_EFFORT
```

The committed configuration remains secret-free:

```text
configs/phase3c_avalai_event_sources.yaml
```

## Trust boundary

The model is allowed to infer only:

```text
asset
event_time_utc
event_type
direction
horizon
severity
novelty
confidence
```

The following fields are injected from trusted code and cannot be supplied by the
model:

```text
source_quality
evidence_ids
document_id
source_id
document_available_at
model identity
prompt hash
input hash
inference timestamps
```

The predicted asset must be one of the document's predeclared asset tags, or
`MARKET` when no tags exist. Any schema violation, refusal, truncation, malformed
JSON, disallowed asset or provider error fails closed.

The document body is untrusted data. Instructions embedded in a feed item are never
followed, and the model is explicitly prohibited from inventing unsupported facts.

## Audit state

Each logical provider request records secret-free metadata in:

```text
state/avalai_calls.jsonl
```

Recorded fields include:

- exact pinned model ID, response model, route and HTTP status;
- endpoint;
- request and response body hashes;
- client and provider request IDs;
- attempts and timestamps;
- token usage;
- sanitized error code and message;
- extraction key;
- previous-record SHA-256.

Raw prompts, raw provider responses, authorization headers and API keys are not
persisted. Each call record has a self-verifying `call_id`, and the ledger is also
hash-chained.

Each event capture receives an immutable provider manifest under:

```text
state/avalai_runs/<capture_id>/
```

The verifier links provider calls to semantic records, links provider manifests to
Phase 3B capture manifests, validates checksums, scans compact state for credential
patterns and requires an empty `prospective_decisions.jsonl`.

## Local execution

With `AVALAI_API_KEY` available in the process environment:

```bash
python scripts/capture_phase3c_avalai_events.py \
  --config configs/phase3c_avalai_event_sources.yaml \
  --output artifacts/phase3c-avalai

python scripts/verify_phase3c_provider.py artifacts/phase3c-avalai
```

## Live validation result

The final live strict structured-output smoke succeeded on 2026-07-17 using the
repository secret and the pinned model.

- workflow run: `29571472843`;
- source commit: `1ed3bc52bf3cd9f35d5882d3b818a1c2d875e8c2`;
- artifact ID: `8403257104`;
- artifact digest:
  `sha256:a40d047652fc1b477663b237f7677fbd7b08f202d902123d080f557a0c109b03`;
- HTTP status: `200` in one attempt;
- response model: `gpt-5-mini-2025-08-07`;
- token usage: 546 input, 100 output, 646 total.

The strict schema, model identity, asset allow-list, evidence binding and trusted
source quality checks all passed. Independent artifact inspection confirmed that all
checksums matched, the prospective decision ledger was empty, and no API-key-shaped,
Authorization or Bearer credential appeared in the evidence. Compact provenance is
committed under `research/runs/phase3c-avalai-smoke-29571472843/`; trace-level details
remain only in the digest-addressed Actions artifact.

## Promotion rule

Successful API calls prove only transport and schema compliance. They do not prove
predictive value. AvalAI semantic features must later pass prospective data-quality,
calibration, ablation, economic-value and robustness gates before they may influence
a paper decision. Historical or one-off semantic results cannot activate a strategy.
