"""Prospective-only safe metadata probe for OKX price-linkage source identities."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from pathlib import Path
from typing import Any, cast
from urllib.parse import parse_qsl, urlencode, urlsplit
from urllib.request import Request, urlopen

OFFICIAL_HOST = "www.okx.com"
MAX_RESPONSE_BYTES = 1_000_000
USER_AGENT = "Emad211-Trade-bot-replication/2.0"


class OKXPriceLinkageProbeError(RuntimeError):
    """Raised when a source violates the prospective metadata contract."""


class PriceSourceKind(StrEnum):
    SPOT_TICKER = "SPOT_TICKER"
    SWAP_TICKER = "SWAP_TICKER"
    MARK_PRICE = "MARK_PRICE"
    INDEX_TICKER = "INDEX_TICKER"


@dataclass(frozen=True)
class EndpointContract:
    source_id: str
    source_kind: PriceSourceKind
    endpoint_path: str
    query: tuple[tuple[str, str], ...]
    required_fields: frozenset[str]
    market_value_fields: frozenset[str]
    expected_identity: tuple[tuple[str, str], ...]
    provider_timestamp_field: str = "ts"

    @property
    def expected_identity_map(self) -> dict[str, str]:
        return dict(self.expected_identity)


TICKER_REQUIRED_FIELDS = frozenset(
    {
        "instType",
        "instId",
        "last",
        "lastSz",
        "askPx",
        "askSz",
        "bidPx",
        "bidSz",
        "open24h",
        "high24h",
        "low24h",
        "volCcy24h",
        "vol24h",
        "sodUtc0",
        "sodUtc8",
        "ts",
    }
)
TICKER_MARKET_VALUE_FIELDS = TICKER_REQUIRED_FIELDS - {"instType", "instId", "ts"}
MARK_REQUIRED_FIELDS = frozenset({"instType", "instId", "markPx", "ts"})
INDEX_REQUIRED_FIELDS = frozenset(
    {"instId", "idxPx", "high24h", "open24h", "low24h", "sodUtc0", "sodUtc8", "ts"}
)

SOURCE_CONTRACTS = (
    EndpointContract(
        source_id="OKX_SPOT_BTC_USDT_TICKER",
        source_kind=PriceSourceKind.SPOT_TICKER,
        endpoint_path="/api/v5/market/ticker",
        query=(("instId", "BTC-USDT"),),
        required_fields=TICKER_REQUIRED_FIELDS,
        market_value_fields=TICKER_MARKET_VALUE_FIELDS,
        expected_identity=(("instType", "SPOT"), ("instId", "BTC-USDT")),
    ),
    EndpointContract(
        source_id="OKX_SWAP_BTC_USDT_SWAP_TICKER",
        source_kind=PriceSourceKind.SWAP_TICKER,
        endpoint_path="/api/v5/market/ticker",
        query=(("instId", "BTC-USDT-SWAP"),),
        required_fields=TICKER_REQUIRED_FIELDS,
        market_value_fields=TICKER_MARKET_VALUE_FIELDS,
        expected_identity=(("instType", "SWAP"), ("instId", "BTC-USDT-SWAP")),
    ),
    EndpointContract(
        source_id="OKX_SWAP_BTC_USDT_SWAP_MARK_PRICE",
        source_kind=PriceSourceKind.MARK_PRICE,
        endpoint_path="/api/v5/public/mark-price",
        query=(("instType", "SWAP"), ("instId", "BTC-USDT-SWAP")),
        required_fields=MARK_REQUIRED_FIELDS,
        market_value_fields=frozenset({"markPx"}),
        expected_identity=(("instType", "SWAP"), ("instId", "BTC-USDT-SWAP")),
    ),
    EndpointContract(
        source_id="OKX_BTC_USDT_INDEX_TICKER",
        source_kind=PriceSourceKind.INDEX_TICKER,
        endpoint_path="/api/v5/market/index-tickers",
        query=(("instId", "BTC-USDT"),),
        required_fields=INDEX_REQUIRED_FIELDS,
        market_value_fields=frozenset(
            {"idxPx", "high24h", "open24h", "low24h", "sodUtc0", "sodUtc8"}
        ),
        expected_identity=(("instId", "BTC-USDT"),),
    ),
)


@dataclass(frozen=True)
class HTTPResponse:
    body: bytes
    status_code: int
    content_type: str
    final_url: str


@dataclass(frozen=True)
class SourceObservation:
    source_id: str
    source_kind: str
    official_host: str
    endpoint_path: str
    query_parameter_names: tuple[str, ...]
    request_fingerprint_sha256: str
    request_started_at: str
    response_received_at: str
    research_available_at: str
    provider_timestamp_ms: int
    provider_timestamp_utc: str
    provider_timestamp_age_ms_at_response: int
    provider_timestamp_after_response: bool
    http_status: int
    application_code: str
    content_type: str
    response_byte_count: int
    response_sha256: str
    row_count: int
    schema_fields: tuple[str, ...]
    schema_sha256: str
    identity_fields: dict[str, str]
    market_value_fields_validated: tuple[str, ...]
    source_health: str
    raw_response_retained: bool
    market_values_retained: bool
    ordered_price_series_retained: bool
    historical_backfill: bool


@dataclass(frozen=True)
class PriceLinkagePilotEvidence:
    schema_version: str
    pilot_id: str
    collection_mode: str
    provider_cache_contract: dict[str, bool]
    sources: tuple[SourceObservation, ...]
    source_count: int
    request_order_source_ids: tuple[str, ...]
    provider_timestamp_order_source_ids: tuple[str, ...]
    provider_timestamps_monotonic_in_request_order: bool
    provider_timestamp_spread_ms: int
    identity_linkage: dict[str, str]
    retention_state: dict[str, bool]
    authorization: dict[str, bool]
    pilot_verdict: str
    issue_53_outcome: str | None
    economic_edge_verdict: str


@dataclass(frozen=True)
class TimedHTTPResponse:
    response: HTTPResponse
    request_started_at: datetime
    response_received_at: datetime


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def build_url(contract: EndpointContract) -> str:
    query = urlencode(contract.query)
    return f"https://{OFFICIAL_HOST}{contract.endpoint_path}?{query}"


def safe_url_metadata(value: str) -> tuple[str, str, str, tuple[str, ...]]:
    parsed = urlsplit(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host != OFFICIAL_HOST:
        raise OKXPriceLinkageProbeError("Response resolved outside the frozen OKX HTTPS host")
    query_names = tuple(sorted({key for key, _ in parse_qsl(parsed.query, keep_blank_values=True)}))
    return parsed.scheme, host, parsed.path, query_names


def fetch_public_response(url: str, *, timeout_seconds: float = 30.0) -> TimedHTTPResponse:
    scheme, host, path, _ = safe_url_metadata(url)
    if scheme != "https" or host != OFFICIAL_HOST:
        raise OKXPriceLinkageProbeError("Request URL is outside the official OKX host")
    if path not in {contract.endpoint_path for contract in SOURCE_CONTRACTS}:
        raise OKXPriceLinkageProbeError("Request URL is outside the frozen endpoint set")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")

    request_started_at = datetime.now(UTC)
    request = Request(
        url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        body = response.read(MAX_RESPONSE_BYTES + 1)
        status_code = int(response.status)
        content_type = response.headers.get("Content-Type", "")
        final_url = response.geturl()
    response_received_at = datetime.now(UTC)

    if len(body) > MAX_RESPONSE_BYTES:
        raise OKXPriceLinkageProbeError("Response exceeded the bounded byte limit")
    return TimedHTTPResponse(
        response=HTTPResponse(body, status_code, content_type, final_url),
        request_started_at=request_started_at,
        response_received_at=response_received_at,
    )


def _require_aware_utc(value: datetime, *, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value.astimezone(UTC)


def _validate_decimal(value: object, *, field: str) -> None:
    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise OKXPriceLinkageProbeError(f"Invalid decimal in {field}: {value!r}") from exc
    if not decimal.is_finite():
        raise OKXPriceLinkageProbeError(f"Non-finite decimal in {field}")


def _validate_timestamp_ms(value: object) -> int:
    try:
        timestamp = int(str(value))
    except ValueError as exc:
        raise OKXPriceLinkageProbeError(f"Invalid provider timestamp: {value!r}") from exc
    if timestamp < 10**12 or timestamp >= 10**14:
        raise OKXPriceLinkageProbeError("Provider timestamp is not milliseconds")
    return timestamp


def validate_source_response(
    *,
    contract: EndpointContract,
    response: HTTPResponse,
    request_url: str,
    request_started_at: datetime,
    response_received_at: datetime,
    research_available_at: datetime | None = None,
) -> SourceObservation:
    request_time = _require_aware_utc(request_started_at, field="request_started_at")
    response_time = _require_aware_utc(response_received_at, field="response_received_at")
    available_time = _require_aware_utc(
        research_available_at or datetime.now(UTC), field="research_available_at"
    )
    if not request_time <= response_time <= available_time:
        raise ValueError("clocks must satisfy request <= response <= research available")

    if response.status_code != 200:
        raise OKXPriceLinkageProbeError(
            f"{contract.source_id} returned HTTP {response.status_code}"
        )
    if not response.body or len(response.body) > MAX_RESPONSE_BYTES:
        raise OKXPriceLinkageProbeError("Response is empty or exceeds the byte guard")
    if "json" not in response.content_type.casefold():
        raise OKXPriceLinkageProbeError("Response content type is not JSON")

    _, host, path, query_names = safe_url_metadata(response.final_url)
    if path != contract.endpoint_path:
        raise OKXPriceLinkageProbeError("Final response path differs from the frozen endpoint")
    expected_query_names = tuple(sorted(key for key, _ in contract.query))
    if query_names != expected_query_names:
        raise OKXPriceLinkageProbeError("Final response query contract changed")

    try:
        decoded: Any = json.loads(response.body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OKXPriceLinkageProbeError("Response is not valid UTF-8 JSON") from exc
    if not isinstance(decoded, dict):
        raise OKXPriceLinkageProbeError("Expected a top-level JSON object")
    payload = cast(Mapping[str, Any], decoded)
    if str(payload.get("code")) != "0" or str(payload.get("msg")) != "":
        raise OKXPriceLinkageProbeError("OKX returned an unsuccessful application response")
    data = payload.get("data")
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        raise OKXPriceLinkageProbeError("Expected exactly one source row")
    row = cast(Mapping[str, Any], data[0])

    missing = contract.required_fields - set(row)
    if missing:
        raise OKXPriceLinkageProbeError(f"Response lacks required fields: {sorted(missing)}")
    identity_fields: dict[str, str] = {}
    for field, expected in contract.expected_identity:
        observed = str(row.get(field, ""))
        if observed != expected:
            raise OKXPriceLinkageProbeError(
                f"Identity mismatch for {field}: expected {expected!r}, got {observed!r}"
            )
        identity_fields[field] = observed

    for field in contract.market_value_fields:
        _validate_decimal(row[field], field=field)
    provider_timestamp_ms = _validate_timestamp_ms(row[contract.provider_timestamp_field])
    provider_timestamp = datetime.fromtimestamp(provider_timestamp_ms / 1000, tz=UTC)
    response_timestamp_ms = int(response_time.timestamp() * 1000)
    provider_age_ms = response_timestamp_ms - provider_timestamp_ms

    schema_fields = tuple(sorted(str(key) for key in row))
    schema_sha256 = sha256_bytes("\x00".join(schema_fields).encode("utf-8"))
    request_fingerprint = sha256_bytes(request_url.encode("utf-8"))

    return SourceObservation(
        source_id=contract.source_id,
        source_kind=contract.source_kind.value,
        official_host=host,
        endpoint_path=path,
        query_parameter_names=query_names,
        request_fingerprint_sha256=request_fingerprint,
        request_started_at=request_time.isoformat().replace("+00:00", "Z"),
        response_received_at=response_time.isoformat().replace("+00:00", "Z"),
        research_available_at=available_time.isoformat().replace("+00:00", "Z"),
        provider_timestamp_ms=provider_timestamp_ms,
        provider_timestamp_utc=provider_timestamp.isoformat().replace("+00:00", "Z"),
        provider_timestamp_age_ms_at_response=provider_age_ms,
        provider_timestamp_after_response=provider_age_ms < 0,
        http_status=response.status_code,
        application_code="0",
        content_type=response.content_type,
        response_byte_count=len(response.body),
        response_sha256=sha256_bytes(response.body),
        row_count=1,
        schema_fields=schema_fields,
        schema_sha256=schema_sha256,
        identity_fields=identity_fields,
        market_value_fields_validated=tuple(sorted(contract.market_value_fields)),
        source_health="SUCCESS",
        raw_response_retained=False,
        market_values_retained=False,
        ordered_price_series_retained=False,
        historical_backfill=False,
    )


def build_pilot_evidence(
    observations: Sequence[SourceObservation],
) -> PriceLinkagePilotEvidence:
    expected_ids = tuple(contract.source_id for contract in SOURCE_CONTRACTS)
    observed_ids = tuple(observation.source_id for observation in observations)
    if observed_ids != expected_ids:
        raise OKXPriceLinkageProbeError(
            "Source set or order differs from the frozen pilot contract"
        )
    if len({observation.source_id for observation in observations}) != len(observations):
        raise OKXPriceLinkageProbeError("Duplicate source identities detected")
    if any(
        observation.raw_response_retained
        or observation.market_values_retained
        or observation.ordered_price_series_retained
        or observation.historical_backfill
        for observation in observations
    ):
        raise OKXPriceLinkageProbeError("Unsafe retention or historical promotion detected")

    request_order = tuple(
        observation.source_id
        for observation in sorted(observations, key=lambda item: item.request_started_at)
    )
    provider_order = tuple(
        observation.source_id
        for observation in sorted(observations, key=lambda item: item.provider_timestamp_ms)
    )
    request_order_observations = sorted(observations, key=lambda item: item.request_started_at)
    provider_values = [item.provider_timestamp_ms for item in request_order_observations]
    monotonic = provider_values == sorted(provider_values)

    return PriceLinkagePilotEvidence(
        schema_version="1.0",
        pilot_id="OKX_BTC_USDT_PROSPECTIVE_PRICE_LINKAGE_METADATA_V1",
        collection_mode="PROSPECTIVE_ONLY",
        provider_cache_contract={
            "multiple_independent_cache_services": True,
            "later_request_may_return_earlier_provider_timestamp": True,
            "cross_source_timestamp_monotonicity_required": False,
            "request_order_is_provider_time_order": False,
        },
        sources=tuple(observations),
        source_count=len(observations),
        request_order_source_ids=request_order,
        provider_timestamp_order_source_ids=provider_order,
        provider_timestamps_monotonic_in_request_order=monotonic,
        provider_timestamp_spread_ms=max(provider_values) - min(provider_values),
        identity_linkage={
            "spot_traded_instrument": "BTC-USDT",
            "swap_traded_instrument": "BTC-USDT-SWAP",
            "mark_price_instrument": "BTC-USDT-SWAP",
            "index_identity": "BTC-USDT",
            "name_similarity_is_sufficient_linkage": "false",
            "calculation_authorized": "false",
        },
        retention_state={
            "raw_responses_retained": False,
            "price_values_retained": False,
            "bid_ask_values_retained": False,
            "mark_values_retained": False,
            "index_values_retained": False,
            "volume_values_retained": False,
            "ordered_price_series_retained": False,
            "public_market_rows_retained": False,
        },
        authorization={
            "historical_backfill": False,
            "basis_computation": False,
            "funding_pnl_computation": False,
            "returns_computation": False,
            "transaction_cost_estimation": False,
            "empirical_fitting": False,
            "parameter_tuning": False,
            "strategy_testing": False,
            "paper_trading": False,
            "live_trading": False,
            "leverage": False,
            "capital_deployment": False,
            "report_2_4_full_authorization": False,
        },
        pilot_verdict="PROSPECTIVE_PRICE_LINKAGE_METADATA_PROFILE",
        issue_53_outcome=None,
        economic_edge_verdict="INCONCLUSIVE",
    )


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def run_pilot(output_dir: str | Path) -> PriceLinkagePilotEvidence:
    observations: list[SourceObservation] = []
    for contract in SOURCE_CONTRACTS:
        request_url = build_url(contract)
        timed = fetch_public_response(request_url)
        observations.append(
            validate_source_response(
                contract=contract,
                response=timed.response,
                request_url=request_url,
                request_started_at=timed.request_started_at,
                response_received_at=timed.response_received_at,
            )
        )
    evidence = build_pilot_evidence(observations)
    output = Path(output_dir) / "okx-prospective-price-linkage-metadata-evidence.json"
    _atomic_write(
        output,
        (json.dumps(asdict(evidence), indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return evidence
