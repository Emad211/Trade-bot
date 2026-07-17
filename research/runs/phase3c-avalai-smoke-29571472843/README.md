# Phase 3C AvalAI live smoke evidence

This directory records compact, secret-free evidence from the first final live
AvalAI structured-output smoke on the clean Phase 3C branch.

## Identity

- Workflow run: `29571472843`
- Source commit: `1ed3bc52bf3cd9f35d5882d3b818a1c2d875e8c2`
- Artifact ID: `8403257104`
- Artifact digest: `sha256:a40d047652fc1b477663b237f7677fbd7b08f202d902123d080f557a0c109b03`
- Endpoint: `https://api.avalai.ir/v1/responses`
- Model and revision: `gpt-5-mini-2025-08-07`

## Verified result

The provider returned HTTP 200 in one attempt. The response model matched the
pinned model, strict structured output passed, evidence binding and trusted
source quality were preserved, and the semantic event remained neutral.

The run used 546 input tokens, 100 output tokens and 646 total tokens.

## Safety audit

- All committed file checksums match.
- `prospective_decisions.jsonl` is empty.
- No API-key-like token, Authorization field or Bearer credential was detected.
- The API key, authorization header and raw provider response are not persisted.
- This run validates transport, schema and audit plumbing only. It does not
  establish predictive value and cannot activate paper or live trading.
