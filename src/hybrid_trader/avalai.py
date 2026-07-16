"""AvalAI structured-output provider with bounded retries and tamper-evident audit logs."""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import time
import urllib.error
import urllib.request
import uuid
from collections.abc import Callable, Mapping
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, Protocol, Self, cast
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hybrid_trader.event_documents import DocumentEnvelope
from hybrid_trader.events import EventSignal
from hybrid_trader.semantic_extraction import (
    SemanticEventRecord,
    make_extraction_key,
    make_semantic_record,
)

AvalAIRoute = Literal["responses", "chat_completions"]
AvalAIStatus = Literal["success", "failed"]
Clock = Callable[[], datetime]
Sleeper = Callable[[float], None]
Jitter = Callable[[float, float], float]

_RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
_SECRET_PATTERN = re.compile(r"(?i)\b(?:aa|sk)-[A-Za-z0-9_-]{6,}\b")
_MAX_RESPONSE_BYTES = 2_000_000
_SCHEMA_NAME = "hybrid_trader_semantic_event_v1"

AVALAI_SEMANTIC_PROMPT = """hybrid-trader semantic extraction v1
You extract a semantic market-event feature from one public document.
Return only JSON that satisfies the supplied schema.

Rules:
- This is research metadata, not trading advice or an execution instruction.
- Never emit an order, position size, exposure, leverage, target price, stop loss,
  take profit, exchange, wallet, withdrawal, or portfolio action.
- direction is the likely semantic market effect of the event, never an instruction.
- asset must be exactly one allowed asset tag from the document metadata, or MARKET
  when the allowed tag list is empty.
- event_type must be concise snake_case.
- event_time_utc must be ISO-8601 with a timezone. Prefer the stated event/publication
  time when reliable; otherwise use the retrieval time supplied in metadata.
- severity, novelty and confidence are numbers in [0, 1].
- Be conservative when evidence is ambiguous and use neutral direction when needed.
"""


class AvalAISettings(BaseModel):
    """Non-secret provider configuration suitable for manifests and Git."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    base_url: str = "https://api.avalai.ir/v1"
    model: str = "gpt-5.4-mini"
    model_revision: str = "provider-managed"
    route: AvalAIRoute = "responses"
    timeout_seconds: float = Field(default=60.0, gt=0, le=300)
    max_retries: int = Field(default=3, ge=0, le=8)
    initial_backoff_seconds: float = Field(default=1.0, ge=0, le=60)
    max_backoff_seconds: float = Field(default=20.0, gt=0, le=300)
    max_output_tokens: int = Field(default=700, ge=128, le=8_192)
    max_document_chars: int = Field(default=30_000, ge=1_000, le=500_000)
    reasoning_effort: Literal["none", "minimal", "low", "medium", "high", "xhigh"] | None = "low"

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        normalized = value.rstrip("/")
        parsed = urlsplit(normalized)
        if (
            parsed.scheme != "https"
            or parsed.hostname != "api.avalai.ir"
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or parsed.path.rstrip("/") != "/v1"
        ):
            raise ValueError("AvalAI base_url must be exactly https://api.avalai.ir/v1")
        return normalized

    @field_validator("model", "model_revision")
    @classmethod
    def validate_model_identity(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized or len(normalized) > 200:
            raise ValueError("AvalAI model identity must be a non-empty short string")
        return normalized

    @model_validator(mode="after")
    def validate_backoff(self) -> AvalAISettings:
        if self.max_backoff_seconds < self.initial_backoff_seconds:
            raise ValueError("max_backoff_seconds cannot be smaller than initial_backoff_seconds")
        return self

    @classmethod
    def from_env(cls) -> Self:
        """Load optional non-secret overrides; the API key is loaded separately."""

        values: dict[str, object] = {}
        string_fields = {
            "base_url": "AVALAI_BASE_URL",
            "model": "AVALAI_MODEL",
            "model_revision": "AVALAI_MODEL_REVISION",
            "route": "AVALAI_ROUTE",
            "reasoning_effort": "AVALAI_REASONING_EFFORT",
        }
        for field, variable in string_fields.items():
            if value := os.environ.get(variable):
                values[field] = value
        integer_fields = {
            "max_retries": "AVALAI_MAX_RETRIES",
            "max_output_tokens": "AVALAI_MAX_OUTPUT_TOKENS",
            "max_document_chars": "AVALAI_MAX_DOCUMENT_CHARS",
        }
        for field, variable in integer_fields.items():
            if value := os.environ.get(variable):
                values[field] = int(value)
        float_fields = {
            "timeout_seconds": "AVALAI_TIMEOUT_SECONDS",
            "initial_backoff_seconds": "AVALAI_INITIAL_BACKOFF_SECONDS",
            "max_backoff_seconds": "AVALAI_MAX_BACKOFF_SECONDS",
        }
        for field, variable in float_fields.items():
            if value := os.environ.get(variable):
                values[field] = float(value)
        return cls.model_validate(values)

    @property
    def endpoint(self) -> str:
        suffix = "responses" if self.route == "responses" else "chat/completions"
        return f"{self.base_url}/{suffix}"


class AvalAISemanticPayload(BaseModel):
    """Only model-inferred fields; trusted evidence fields are injected by code."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    asset: str = Field(min_length=1, max_length=32)
    event_time_utc: datetime
    event_type: str = Field(min_length=1, max_length=100)
    direction: Literal["bullish", "bearish", "neutral"]
    horizon: Literal["intraday", "1d_3d", "1w_plus"]
    severity: float = Field(ge=0, le=1)
    novelty: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)

    @field_validator("asset")
    @classmethod
    def normalize_asset(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("event_type")
    @classmethod
    def normalize_event_type(cls, value: str) -> str:
        normalized = value.strip().lower().replace(" ", "_")
        if not normalized:
            raise ValueError("event_type cannot be empty")
        return normalized

    @field_validator("event_time_utc")
    @classmethod
    def normalize_event_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("event_time_utc must be timezone-aware")
        return value.astimezone(UTC)

    def to_event_signal(self, envelope: DocumentEnvelope) -> EventSignal:
        allowed_assets = envelope.document.asset_tags
        expected_asset = self.asset
        if allowed_assets:
            if expected_asset not in allowed_assets:
                raise ValueError("AvalAI semantic asset is not allowed by document metadata")
        elif expected_asset != "MARKET":
            raise ValueError("Documents without asset tags must use the MARKET asset")
        return EventSignal(
            asset=expected_asset,
            event_time_utc=self.event_time_utc,
            event_type=self.event_type,
            direction=self.direction,
            horizon=self.horizon,
            severity=self.severity,
            novelty=self.novelty,
            source_quality=envelope.document.source_quality,
            confidence=self.confidence,
            evidence_ids=(envelope.document.document_id,),
        )


@dataclass(frozen=True)
class AvalAIHTTPResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes


class AvalAITransport(Protocol):
    def __call__(
        self,
        url: str,
        headers: Mapping[str, str],
        body: bytes,
        timeout_seconds: float,
    ) -> AvalAIHTTPResponse: ...


class AvalAICallRecord(BaseModel):
    """Secret-free metadata for one logical provider call, including retries."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    call_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    extraction_key: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: AvalAIStatus
    route: AvalAIRoute
    endpoint: str
    model: str
    model_revision: str
    client_request_id: str
    provider_request_id: str | None = None
    response_id: str | None = None
    response_model: str | None = None
    request_body_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    response_body_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    attempts: int = Field(ge=1)
    started_at: datetime
    completed_at: datetime
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    error_code: str | None = None
    error_message: str | None = None
    previous_record_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @field_validator("started_at", "completed_at")
    @classmethod
    def normalize_call_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("AvalAI call timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_call(self) -> AvalAICallRecord:
        if self.completed_at < self.started_at:
            raise ValueError("AvalAI call completion cannot precede its start")
        if self.status == "success" and (self.error_code or self.error_message):
            raise ValueError("Successful AvalAI calls cannot contain error metadata")
        if self.status == "failed" and not self.error_code:
            raise ValueError("Failed AvalAI calls must contain an error_code")
        expected_call_id = _call_id(
            self.model_dump(
                mode="json",
                exclude={"call_id", "previous_record_sha256"},
            )
        )
        if self.call_id != expected_call_id:
            raise ValueError("AvalAI call_id does not match call metadata")
        return self


class AvalAIRequestError(RuntimeError):
    def __init__(self, message: str, *, call_record: AvalAICallRecord) -> None:
        super().__init__(message)
        self.call_record = call_record


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _redact(value: str, api_key: str) -> str:
    redacted = value.replace(api_key, "[REDACTED_API_KEY]") if api_key else value
    return _SECRET_PATTERN.sub("[REDACTED_API_KEY]", redacted)[:1_000]


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")


def _identity_value(value: Any) -> Any:
    if isinstance(value, datetime):
        normalized = value.astimezone(UTC).isoformat()
        return normalized.replace("+00:00", "Z")
    if isinstance(value, Mapping):
        return {str(key): _identity_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_identity_value(item) for item in value]
    return value


def _call_id(payload: Mapping[str, Any]) -> str:
    identity = {
        key: _identity_value(value)
        for key, value in payload.items()
        if key not in {"call_id", "previous_record_sha256"}
    }
    return hashlib.sha256(_canonical_json_bytes(identity)).hexdigest()


def _failed_call_record(
    record: AvalAICallRecord,
    *,
    error_code: str,
    error_message: str,
) -> AvalAICallRecord:
    payload = record.model_dump(
        mode="python",
        exclude={"call_id", "previous_record_sha256"},
    )
    payload.update(
        status="failed",
        error_code=error_code,
        error_message=error_message,
    )
    return AvalAICallRecord(call_id=_call_id(payload), **payload)


def _default_transport(
    url: str,
    headers: Mapping[str, str],
    body: bytes,
    timeout_seconds: float,
) -> AvalAIHTTPResponse:
    request = urllib.request.Request(
        url,
        data=body,
        headers=dict(headers),
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            payload = bytes(response.read(_MAX_RESPONSE_BYTES + 1))
            response_headers = {key.lower(): value for key, value in response.headers.items()}
            status_code = int(response.status)
    except urllib.error.HTTPError as exc:
        payload = bytes(exc.read(_MAX_RESPONSE_BYTES + 1))
        response_headers = (
            {key.lower(): value for key, value in exc.headers.items()} if exc.headers else {}
        )
        status_code = int(exc.code)
    if len(payload) > _MAX_RESPONSE_BYTES:
        raise ValueError("AvalAI response exceeds the configured safety limit")
    return AvalAIHTTPResponse(status_code=status_code, headers=response_headers, body=payload)


def _json_object(payload: bytes) -> dict[str, Any]:
    try:
        parsed: object = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("AvalAI returned a non-JSON response") from exc
    if not isinstance(parsed, dict):
        raise ValueError("AvalAI response root must be a JSON object")
    return cast(dict[str, Any], parsed)


def _usage(
    payload: Mapping[str, Any], *, route: AvalAIRoute
) -> tuple[int | None, int | None, int | None]:
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return None, None, None
    if route == "responses":
        input_value = usage.get("input_tokens")
        output_value = usage.get("output_tokens")
    else:
        input_value = usage.get("prompt_tokens")
        output_value = usage.get("completion_tokens")
    total_value = usage.get("total_tokens")
    return (
        int(input_value) if isinstance(input_value, int) else None,
        int(output_value) if isinstance(output_value, int) else None,
        int(total_value) if isinstance(total_value, int) else None,
    )


def _responses_text(payload: Mapping[str, Any]) -> str:
    status = payload.get("status")
    if status not in {None, "completed"}:
        raise ValueError(f"AvalAI Responses request did not complete: {status}")
    output = payload.get("output")
    if not isinstance(output, list):
        raise ValueError("AvalAI Responses payload is missing output items")
    text_parts: list[str] = []
    refusals: list[str] = []
    for item in output:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict):
                continue
            part_type = part.get("type")
            if part_type == "output_text" and isinstance(part.get("text"), str):
                text_parts.append(cast(str, part["text"]))
            elif part_type == "refusal":
                refusal = part.get("refusal") or part.get("text")
                if isinstance(refusal, str):
                    refusals.append(refusal)
    if refusals:
        raise ValueError(f"AvalAI model refusal: {' '.join(refusals)}")
    text = "".join(text_parts).strip()
    if not text:
        raise ValueError("AvalAI Responses payload contains no output text")
    return text


def _chat_text(payload: Mapping[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise ValueError("AvalAI Chat payload is missing choices")
    first = cast(dict[str, Any], choices[0])
    if first.get("finish_reason") == "length":
        raise ValueError("AvalAI Chat output was truncated")
    message = first.get("message")
    if not isinstance(message, dict):
        raise ValueError("AvalAI Chat payload is missing the assistant message")
    refusal = message.get("refusal")
    if isinstance(refusal, str) and refusal.strip():
        raise ValueError(f"AvalAI model refusal: {refusal}")
    content = message.get("content")
    if isinstance(content, str):
        text = content.strip()
    elif isinstance(content, list):
        text = "".join(
            str(part.get("text", "")) for part in content if isinstance(part, dict)
        ).strip()
    else:
        text = ""
    if not text:
        raise ValueError("AvalAI Chat payload contains no assistant text")
    return text


class AvalAIClient:
    def __init__(
        self,
        settings: AvalAISettings,
        *,
        api_key: str | None = None,
        transport: AvalAITransport = _default_transport,
        clock: Clock = _utc_now,
        sleep: Sleeper = time.sleep,
        jitter: Jitter = random.uniform,
    ) -> None:
        secret = api_key or os.environ.get("AVALAI_API_KEY", "")
        if not secret:
            raise ValueError("AVALAI_API_KEY is required")
        if any(character.isspace() for character in secret):
            raise ValueError("AVALAI_API_KEY cannot contain whitespace")
        self.settings = settings
        self._api_key = secret
        self._transport = transport
        self._clock = clock
        self._sleep = sleep
        self._jitter = jitter

    def _request_body(self, *, prompt: str, input_text: str) -> dict[str, Any]:
        schema = AvalAISemanticPayload.model_json_schema()
        schema["additionalProperties"] = False
        if self.settings.route == "responses":
            payload: dict[str, Any] = {
                "model": self.settings.model,
                "instructions": prompt,
                "input": input_text,
                "store": False,
                "max_output_tokens": self.settings.max_output_tokens,
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": _SCHEMA_NAME,
                        "strict": True,
                        "schema": schema,
                    }
                },
            }
            if self.settings.reasoning_effort is not None:
                payload["reasoning"] = {"effort": self.settings.reasoning_effort}
            return payload
        return {
            "model": self.settings.model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": input_text},
            ],
            "store": False,
            "max_completion_tokens": self.settings.max_output_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": _SCHEMA_NAME,
                    "strict": True,
                    "schema": schema,
                },
            },
        }

    def _call_record(
        self,
        *,
        extraction_key: str,
        status: AvalAIStatus,
        client_request_id: str,
        request_sha256: str,
        attempts: int,
        started_at: datetime,
        completed_at: datetime,
        response: AvalAIHTTPResponse | None,
        response_payload: Mapping[str, Any] | None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> AvalAICallRecord:
        response_sha = hashlib.sha256(response.body).hexdigest() if response is not None else None
        input_tokens, output_tokens, total_tokens = (
            _usage(response_payload, route=self.settings.route)
            if response_payload is not None
            else (None, None, None)
        )
        response_id = response_payload.get("id") if response_payload is not None else None
        response_model = response_payload.get("model") if response_payload is not None else None
        provider_request_id = response.headers.get("x-request-id") if response is not None else None
        record_payload: dict[str, Any] = {
            "schema_version": "1.0",
            "extraction_key": extraction_key,
            "status": status,
            "route": self.settings.route,
            "endpoint": self.settings.endpoint,
            "model": self.settings.model,
            "model_revision": self.settings.model_revision,
            "client_request_id": client_request_id,
            "provider_request_id": provider_request_id,
            "response_id": response_id if isinstance(response_id, str) else None,
            "response_model": response_model if isinstance(response_model, str) else None,
            "request_body_sha256": request_sha256,
            "response_body_sha256": response_sha,
            "attempts": attempts,
            "started_at": started_at,
            "completed_at": completed_at,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "error_code": error_code,
            "error_message": error_message,
        }
        return AvalAICallRecord(call_id=_call_id(record_payload), **record_payload)

    def generate(
        self,
        envelope: DocumentEnvelope,
        *,
        prompt: str,
        extraction_key: str,
    ) -> tuple[AvalAISemanticPayload, AvalAICallRecord]:
        if len(envelope.text) > self.settings.max_document_chars:
            raise ValueError("Document text exceeds the configured AvalAI input limit")
        input_payload = {
            "document_id": envelope.document.document_id,
            "source_id": envelope.document.source_id,
            "allowed_asset_tags": list(envelope.document.asset_tags),
            "published_at": (
                envelope.document.published_at.isoformat()
                if envelope.document.published_at is not None
                else None
            ),
            "retrieved_at": envelope.document.retrieved_at.isoformat(),
            "document_text": envelope.text,
        }
        input_text = json.dumps(input_payload, sort_keys=True, ensure_ascii=False)
        request_payload = self._request_body(prompt=prompt, input_text=input_text)
        request_body = _canonical_json_bytes(request_payload)
        request_sha = hashlib.sha256(request_body).hexdigest()
        client_request_id = f"ht-{uuid.uuid4()}"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Client-Request-Id": client_request_id,
        }
        started_at = self._clock().astimezone(UTC)
        response: AvalAIHTTPResponse | None = None
        parsed_response: dict[str, Any] | None = None
        last_code = "connection_error"
        last_message = "AvalAI request failed"
        attempts = 0

        for attempt in range(self.settings.max_retries + 1):
            attempts = attempt + 1
            try:
                response = self._transport(
                    self.settings.endpoint,
                    headers,
                    request_body,
                    self.settings.timeout_seconds,
                )
                parsed_response = _json_object(response.body)
                if 200 <= response.status_code < 300:
                    try:
                        text = (
                            _responses_text(parsed_response)
                            if self.settings.route == "responses"
                            else _chat_text(parsed_response)
                        )
                        result = AvalAISemanticPayload.model_validate_json(text)
                    except Exception as exc:
                        completed_at = self._clock().astimezone(UTC)
                        record = self._call_record(
                            extraction_key=extraction_key,
                            status="failed",
                            client_request_id=client_request_id,
                            request_sha256=request_sha,
                            attempts=attempts,
                            started_at=started_at,
                            completed_at=completed_at,
                            response=response,
                            response_payload=parsed_response,
                            error_code="invalid_structured_output",
                            error_message=_redact(str(exc), self._api_key),
                        )
                        raise AvalAIRequestError(str(exc), call_record=record) from exc
                    completed_at = self._clock().astimezone(UTC)
                    record = self._call_record(
                        extraction_key=extraction_key,
                        status="success",
                        client_request_id=client_request_id,
                        request_sha256=request_sha,
                        attempts=attempts,
                        started_at=started_at,
                        completed_at=completed_at,
                        response=response,
                        response_payload=parsed_response,
                    )
                    return result, record

                error = parsed_response.get("error")
                error_mapping = error if isinstance(error, dict) else {}
                raw_code = error_mapping.get("code") or error_mapping.get("type")
                raw_message = error_mapping.get("message") or f"HTTP {response.status_code}"
                last_code = str(raw_code) if raw_code else f"http_{response.status_code}"
                last_message = _redact(str(raw_message), self._api_key)
                if response.status_code not in _RETRYABLE_STATUS_CODES:
                    break
                retry_after = response.headers.get("retry-after")
            except AvalAIRequestError:
                raise
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                response = None
                parsed_response = None
                last_code = "connection_error"
                last_message = _redact(str(exc), self._api_key)
                retry_after = None

            if attempt >= self.settings.max_retries:
                break
            base_delay = min(
                self.settings.max_backoff_seconds,
                self.settings.initial_backoff_seconds * (2**attempt),
            )
            if retry_after is not None:
                with suppress(ValueError):
                    base_delay = max(base_delay, float(retry_after))
            delay = min(
                self.settings.max_backoff_seconds,
                base_delay + self._jitter(0.0, max(0.001, base_delay * 0.25)),
            )
            self._sleep(delay)

        completed_at = self._clock().astimezone(UTC)
        record = self._call_record(
            extraction_key=extraction_key,
            status="failed",
            client_request_id=client_request_id,
            request_sha256=request_sha,
            attempts=attempts,
            started_at=started_at,
            completed_at=completed_at,
            response=response,
            response_payload=parsed_response,
            error_code=last_code,
            error_message=last_message,
        )
        raise AvalAIRequestError(last_message, call_record=record)


class AvalAIStructuredExtractor:
    """Semantic extractor using AvalAI without granting execution authority."""

    def __init__(
        self,
        settings: AvalAISettings,
        *,
        api_key: str | None = None,
        prompt: str = AVALAI_SEMANTIC_PROMPT,
        transport: AvalAITransport = _default_transport,
        clock: Clock = _utc_now,
        sleep: Sleeper = time.sleep,
        jitter: Jitter = random.uniform,
    ) -> None:
        self.settings = settings
        self.model_id = f"avalai/{settings.model}"
        self.model_revision = settings.model_revision
        self.prompt = prompt
        self._client = AvalAIClient(
            settings,
            api_key=api_key,
            transport=transport,
            clock=clock,
            sleep=sleep,
            jitter=jitter,
        )
        self.call_records: list[AvalAICallRecord] = []

    @property
    def prompt_sha256(self) -> str:
        return hashlib.sha256(self.prompt.encode("utf-8")).hexdigest()

    def extraction_key(self, envelope: DocumentEnvelope) -> str:
        return make_extraction_key(
            document_id=envelope.document.document_id,
            model_id=self.model_id,
            model_revision=self.model_revision,
            prompt_sha256=self.prompt_sha256,
            input_sha256=envelope.document.content_sha256,
        )

    def extract(
        self,
        envelope: DocumentEnvelope,
        *,
        inference_started_at: datetime | None = None,
        inference_completed_at: datetime | None = None,
    ) -> SemanticEventRecord:
        if inference_started_at is not None or inference_completed_at is not None:
            raise ValueError("AvalAI extraction cannot use synthetic inference timestamps")
        extraction_key = self.extraction_key(envelope)
        try:
            payload, call_record = self._client.generate(
                envelope,
                prompt=self.prompt,
                extraction_key=extraction_key,
            )
        except AvalAIRequestError as exc:
            self.call_records.append(exc.call_record)
            raise
        try:
            signal = payload.to_event_signal(envelope)
        except Exception as exc:
            failed_record = _failed_call_record(
                call_record,
                error_code="semantic_contract_violation",
                error_message=_redact(str(exc), self._client._api_key),
            )
            self.call_records.append(failed_record)
            raise AvalAIRequestError(str(exc), call_record=failed_record) from exc
        self.call_records.append(call_record)
        return make_semantic_record(
            envelope,
            signal,
            model_id=self.model_id,
            model_revision=self.model_revision,
            prompt=self.prompt,
            inference_started_at=call_record.started_at,
            inference_completed_at=call_record.completed_at,
        )


def _canonical_call_line(record: AvalAICallRecord) -> bytes:
    payload = json.dumps(
        record.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )
    return (payload + "\n").encode("utf-8")


def avalai_call_record_sha256(record: AvalAICallRecord) -> str:
    return hashlib.sha256(_canonical_call_line(record)).hexdigest()


@dataclass(frozen=True)
class AvalAICallLedgerState:
    head_sha256: str | None
    previous_record: AvalAICallRecord | None
    count: int
    call_ids: frozenset[str]


def verify_avalai_call_ledger(path: str | Path) -> AvalAICallLedgerState:
    ledger = Path(path)
    if not ledger.exists():
        return AvalAICallLedgerState(None, None, 0, frozenset())
    previous_sha: str | None = None
    previous: AvalAICallRecord | None = None
    call_ids: set[str] = set()
    count = 0
    with ledger.open("rb") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if not raw.endswith(b"\n"):
                raise ValueError(f"AvalAI call ledger line {line_number} is not newline-terminated")
            try:
                record = AvalAICallRecord.model_validate_json(raw)
            except Exception as exc:
                raise ValueError(f"Invalid AvalAI call ledger line {line_number}") from exc
            expected_call_id = _call_id(
                record.model_dump(
                    mode="json",
                    exclude={"call_id", "previous_record_sha256"},
                )
            )
            if record.call_id != expected_call_id:
                raise ValueError(f"AvalAI call_id mismatch at line {line_number}")
            if record.previous_record_sha256 != previous_sha:
                raise ValueError(f"AvalAI call ledger hash chain breaks at line {line_number}")
            if record.call_id in call_ids:
                raise ValueError(f"Duplicate AvalAI call ID at line {line_number}")
            if previous is not None and (record.started_at, record.call_id) <= (
                previous.started_at,
                previous.call_id,
            ):
                raise ValueError("AvalAI call records must be strictly ordered")
            previous_sha = avalai_call_record_sha256(record)
            previous = record
            call_ids.add(record.call_id)
            count += 1
    return AvalAICallLedgerState(previous_sha, previous, count, frozenset(call_ids))


def append_avalai_call_records(
    path: str | Path,
    records: tuple[AvalAICallRecord, ...] | list[AvalAICallRecord],
) -> AvalAICallLedgerState:
    ledger = Path(path)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    state = verify_avalai_call_ledger(ledger)
    pending = [record for record in records if record.call_id not in state.call_ids]
    pending.sort(key=lambda item: (item.started_at, item.call_id))
    if not pending:
        return state
    previous_sha = state.head_sha256
    previous = state.previous_record
    payloads: list[bytes] = []
    for record in pending:
        if previous is not None and (record.started_at, record.call_id) <= (
            previous.started_at,
            previous.call_id,
        ):
            raise ValueError("New AvalAI call records are not strictly ordered")
        chained = record.model_copy(update={"previous_record_sha256": previous_sha})
        payload = _canonical_call_line(chained)
        payloads.append(payload)
        previous_sha = hashlib.sha256(payload).hexdigest()
        previous = chained
    descriptor = os.open(ledger, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        for payload in payloads:
            os.write(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return verify_avalai_call_ledger(ledger)
