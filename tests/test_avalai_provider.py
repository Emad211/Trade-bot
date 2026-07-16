from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from hybrid_trader.avalai import (
    AvalAIHTTPResponse,
    AvalAIRequestError,
    AvalAISettings,
    AvalAIStructuredExtractor,
    append_avalai_call_records,
    verify_avalai_call_ledger,
)
from hybrid_trader.event_documents import (
    DocumentEnvelope,
    ProspectiveDocument,
    document_identity_payload,
    make_document_id,
)


class SequenceClock:
    def __init__(self, start: datetime) -> None:
        self.start = start
        self.calls = 0

    def __call__(self) -> datetime:
        value = self.start + timedelta(milliseconds=self.calls)
        self.calls += 1
        return value


class SequenceTransport:
    def __init__(self, responses: list[AvalAIHTTPResponse]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, dict[str, str], bytes, float]] = []

    def __call__(
        self,
        url: str,
        headers: Mapping[str, str],
        body: bytes,
        timeout_seconds: float,
    ) -> AvalAIHTTPResponse:
        self.calls.append((url, dict(headers), body, timeout_seconds))
        if not self.responses:
            raise AssertionError("Unexpected provider request")
        return self.responses.pop(0)


def _envelope(*, asset_tags: tuple[str, ...] = ("BTC",)) -> DocumentEnvelope:
    observed = datetime(2026, 7, 16, 12, tzinfo=UTC)
    text = "Protocol release fixes a consensus vulnerability."
    content_sha = hashlib.sha256(text.encode()).hexdigest()
    identity = document_identity_payload(
        source_id="official-feed",
        canonical_url="https://example.com/releases/1",
        title="Protocol release",
        published_at=observed - timedelta(minutes=5),
        content_sha256=content_sha,
    )
    document = ProspectiveDocument(
        document_id=make_document_id(**identity),
        source_id="official-feed",
        canonical_url="https://example.com/releases/1",
        title="Protocol release",
        published_at=observed - timedelta(minutes=5),
        retrieved_at=observed,
        available_at=observed,
        source_quality=0.93,
        asset_tags=asset_tags,
        content_sha256=content_sha,
        content_length=len(text.encode()),
        feed_payload_sha256="f" * 64,
    )
    return DocumentEnvelope(document=document, text=text)


def _semantic_payload(*, asset: str = "BTC") -> dict[str, object]:
    return {
        "asset": asset,
        "event_time_utc": "2026-07-16T11:55:00Z",
        "event_type": "protocol_security_fix",
        "direction": "neutral",
        "horizon": "1d_3d",
        "severity": 0.8,
        "novelty": 0.7,
        "confidence": 0.6,
    }


def _responses_response(
    semantic: dict[str, object] | None = None,
    *,
    status_code: int = 200,
    headers: Mapping[str, str] | None = None,
) -> AvalAIHTTPResponse:
    if status_code >= 400:
        body: dict[str, object] = {
            "error": {
                "code": "rate_limit_exceeded" if status_code == 429 else "request_failed",
                "message": f"HTTP {status_code}",
            }
        }
    else:
        body = {
            "id": "resp_test",
            "status": "completed",
            "model": "gpt-5.4-mini",
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": json.dumps(semantic or _semantic_payload()),
                        }
                    ],
                }
            ],
            "usage": {"input_tokens": 100, "output_tokens": 30, "total_tokens": 130},
        }
    return AvalAIHTTPResponse(
        status_code=status_code,
        headers=dict(headers or {"x-request-id": "provider-request-1"}),
        body=json.dumps(body).encode(),
    )


def _chat_response() -> AvalAIHTTPResponse:
    body = {
        "id": "chat_test",
        "model": "gpt-5.4-mini",
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": json.dumps(_semantic_payload())},
            }
        ],
        "usage": {"prompt_tokens": 80, "completion_tokens": 20, "total_tokens": 100},
    }
    return AvalAIHTTPResponse(
        status_code=200,
        headers={"x-request-id": "provider-chat-1"},
        body=json.dumps(body).encode(),
    )


def test_responses_route_is_strict_secret_free_and_evidence_bound() -> None:
    secret = "aa-unit-test-secret"
    transport = SequenceTransport([_responses_response()])
    extractor = AvalAIStructuredExtractor(
        AvalAISettings(max_retries=0, reasoning_effort=None),
        api_key=secret,
        transport=transport,
        clock=SequenceClock(datetime(2026, 7, 16, 12, 1, tzinfo=UTC)),
    )
    envelope = _envelope()
    record = extractor.extract(envelope)

    assert record.signal.source_quality == envelope.document.source_quality
    assert record.signal.evidence_ids == (envelope.document.document_id,)
    assert record.signal.asset == "BTC"
    assert record.model_id == "avalai/gpt-5.4-mini"
    assert len(extractor.call_records) == 1
    call_record = extractor.call_records[0]
    assert call_record.status == "success"
    assert call_record.provider_request_id == "provider-request-1"
    assert call_record.input_tokens == 100
    assert call_record.output_tokens == 30
    assert call_record.total_tokens == 130

    url, headers, body, timeout = transport.calls[0]
    request = json.loads(body)
    assert url == "https://api.avalai.ir/v1/responses"
    assert timeout == 60
    assert headers["Authorization"] == f"Bearer {secret}"
    assert headers["X-Client-Request-Id"].startswith("ht-")
    assert secret.encode() not in body
    assert request["store"] is False
    assert request["text"]["format"]["type"] == "json_schema"
    assert request["text"]["format"]["strict"] is True
    schema_properties = request["text"]["format"]["schema"]["properties"]
    assert "source_quality" not in schema_properties
    assert "evidence_ids" not in schema_properties
    assert secret not in call_record.model_dump_json()


def test_chat_route_uses_json_schema_and_max_completion_tokens() -> None:
    transport = SequenceTransport([_chat_response()])
    extractor = AvalAIStructuredExtractor(
        AvalAISettings(route="chat_completions", max_retries=0),
        api_key="unit-test-secret",
        transport=transport,
        clock=SequenceClock(datetime(2026, 7, 16, 12, 1, tzinfo=UTC)),
    )
    record = extractor.extract(_envelope())
    request = json.loads(transport.calls[0][2])
    assert record.signal.event_type == "protocol_security_fix"
    assert transport.calls[0][0].endswith("/chat/completions")
    assert request["store"] is False
    assert request["max_completion_tokens"] == 700
    assert request["response_format"]["type"] == "json_schema"
    assert request["response_format"]["json_schema"]["strict"] is True


def test_retry_honors_retry_after_and_reuses_logical_request_id() -> None:
    transport = SequenceTransport(
        [
            _responses_response(status_code=429, headers={"retry-after": "2"}),
            _responses_response(),
        ]
    )
    sleeps: list[float] = []
    extractor = AvalAIStructuredExtractor(
        AvalAISettings(
            max_retries=2,
            initial_backoff_seconds=0.1,
            max_backoff_seconds=5,
            reasoning_effort=None,
        ),
        api_key="unit-test-secret",
        transport=transport,
        clock=SequenceClock(datetime(2026, 7, 16, 12, 1, tzinfo=UTC)),
        sleep=sleeps.append,
        jitter=lambda low, high: 0.0,
    )
    extractor.extract(_envelope())
    assert len(transport.calls) == 2
    assert sleeps == [2.0]
    request_ids = [call[1]["X-Client-Request-Id"] for call in transport.calls]
    assert request_ids[0] == request_ids[1]
    assert extractor.call_records[0].attempts == 2


def test_authentication_error_is_not_retried_and_secret_is_redacted() -> None:
    secret = "aa-redaction-test-secret"
    response = AvalAIHTTPResponse(
        status_code=401,
        headers={"x-request-id": "provider-auth-1"},
        body=json.dumps(
            {"error": {"code": "invalid_api_key", "message": f"invalid {secret}"}}
        ).encode(),
    )
    transport = SequenceTransport([response])
    extractor = AvalAIStructuredExtractor(
        AvalAISettings(max_retries=4, reasoning_effort=None),
        api_key=secret,
        transport=transport,
        clock=SequenceClock(datetime(2026, 7, 16, 12, 1, tzinfo=UTC)),
        sleep=lambda seconds: pytest.fail(f"Unexpected retry sleep: {seconds}"),
    )
    with pytest.raises(AvalAIRequestError) as caught:
        extractor.extract(_envelope())
    assert len(transport.calls) == 1
    assert caught.value.call_record.status == "failed"
    assert caught.value.call_record.error_code == "invalid_api_key"
    serialized = caught.value.call_record.model_dump_json()
    assert secret not in serialized
    assert "REDACTED_API_KEY" in serialized


def test_provider_rejects_untrusted_assets_and_oversized_documents() -> None:
    transport = SequenceTransport([_responses_response(_semantic_payload(asset="ETH"))])
    extractor = AvalAIStructuredExtractor(
        AvalAISettings(max_retries=0, reasoning_effort=None),
        api_key="unit-test-secret",
        transport=transport,
        clock=SequenceClock(datetime(2026, 7, 16, 12, 1, tzinfo=UTC)),
    )
    with pytest.raises(ValueError, match="not allowed"):
        extractor.extract(_envelope(asset_tags=("BTC",)))

    tiny = AvalAIStructuredExtractor(
        AvalAISettings(max_document_chars=1_000, max_retries=0, reasoning_effort=None),
        api_key="unit-test-secret",
        transport=SequenceTransport([]),
    )
    envelope = _envelope().model_copy(update={"text": "x" * 1_001})
    with pytest.raises(ValueError, match="input limit"):
        tiny.extract(envelope)


def test_settings_and_key_contracts_fail_closed() -> None:
    with pytest.raises(ValidationError, match="base_url"):
        AvalAISettings(base_url="https://evil.example/v1")
    with pytest.raises(ValueError, match="AVALAI_API_KEY"):
        AvalAIStructuredExtractor(AvalAISettings(), api_key="")
    with pytest.raises(ValueError, match="whitespace"):
        AvalAIStructuredExtractor(AvalAISettings(), api_key="invalid key")


def test_call_ledger_is_hash_chained_and_deduplicated(tmp_path: Path) -> None:
    extractor = AvalAIStructuredExtractor(
        AvalAISettings(max_retries=0, reasoning_effort=None),
        api_key="unit-test-secret",
        transport=SequenceTransport([_responses_response()]),
        clock=SequenceClock(datetime(2026, 7, 16, 12, 1, tzinfo=UTC)),
    )
    extractor.extract(_envelope())
    ledger = tmp_path / "avalai_calls.jsonl"
    state = append_avalai_call_records(ledger, extractor.call_records)
    assert state.count == 1
    duplicate = append_avalai_call_records(ledger, extractor.call_records)
    assert duplicate.count == 1
    raw = ledger.read_bytes()
    ledger.write_bytes(raw.replace(b'"status":"success"', b'"status":"failed"', 1))
    with pytest.raises(ValueError, match="Invalid AvalAI|hash chain|call_id"):
        verify_avalai_call_ledger(ledger)
