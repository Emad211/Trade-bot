"""Safe, bounded probe of the official OKX public funding-rate-history endpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from itertools import pairwise
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

OFFICIAL_HOST = "www.okx.com"
API_PATH = "/api/v5/public/funding-rate-history"
DEFAULT_INSTRUMENT = "BTC-USDT-SWAP"
DEFAULT_LIMIT = 100
MAX_LIMIT = 100
REQUIRED_FIELDS = frozenset(
    {
        "instType",
        "instId",
        "formulaType",
        "fundingRate",
        "realizedRate",
        "fundingTime",
        "method",
    }
)


class OKXFundingProbeError(RuntimeError):
    """Raised when the bounded OKX probe violates its frozen contract."""


@dataclass(frozen=True)
class HTTPResponse:
    body: bytes
    status_code: int
    content_type: str
    final_url: str


@dataclass(frozen=True)
class FundingProbeEvidence:
    schema_version: str
    source_id: str
    official_host: str
    endpoint_path: str
    instrument_id: str
    requested_limit: int
    request_fingerprint_sha256: str
    retrieved_at: str
    http_status: int
    content_type: str
    response_byte_count: int
    response_sha256: str
    api_code: str
    row_count: int
    schema_fields: tuple[str, ...]
    schema_sha256: str
    min_funding_time_ms: int
    max_funding_time_ms: int
    unique_funding_times: int
    timestamp_order: str
    observed_interval_seconds_counts: tuple[tuple[int, int], ...]
    raw_rows_persisted: bool
    raw_rows_published: bool
    returns_computed: bool
    economic_edge_verdict: str


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_url(*, instrument_id: str = DEFAULT_INSTRUMENT, limit: int = DEFAULT_LIMIT) -> str:
    if not instrument_id or instrument_id != instrument_id.strip():
        raise ValueError("instrument_id must be non-empty and stripped")
    if limit <= 0 or limit > MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_LIMIT}")
    query = urlencode({"instId": instrument_id, "limit": str(limit)})
    return f"https://{OFFICIAL_HOST}{API_PATH}?{query}"


def fetch_public_response(url: str, *, timeout_seconds: float = 30.0) -> HTTPResponse:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != OFFICIAL_HOST or parsed.path != API_PATH:
        raise OKXFundingProbeError("Request URL is outside the frozen official OKX endpoint")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Emad211-Trade-bot-replication/1.0",
        },
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        body = response.read()
        status = int(response.status)
        content_type = response.headers.get("Content-Type", "")
        final_url = response.geturl()
    final = urlparse(final_url)
    if final.scheme != "https" or final.hostname != OFFICIAL_HOST:
        raise OKXFundingProbeError("OKX response redirected outside the official host")
    if status != 200:
        raise OKXFundingProbeError(f"Official endpoint returned HTTP {status}")
    if not body:
        raise OKXFundingProbeError("Official endpoint returned an empty body")
    if "json" not in content_type.lower():
        raise OKXFundingProbeError(f"Unexpected content type: {content_type!r}")
    return HTTPResponse(body, status, content_type, final_url)


def _decimal(value: object, *, field: str, row_index: int) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise OKXFundingProbeError(
            f"Row {row_index}: invalid decimal in {field}: {value!r}"
        ) from exc
    if not result.is_finite():
        raise OKXFundingProbeError(f"Row {row_index}: non-finite decimal in {field}")
    return result


def _timestamp(value: object, *, row_index: int) -> int:
    try:
        result = int(str(value))
    except ValueError as exc:
        raise OKXFundingProbeError(f"Row {row_index}: invalid fundingTime {value!r}") from exc
    if result <= 0 or result < 10**12 or result >= 10**14:
        raise OKXFundingProbeError(f"Row {row_index}: fundingTime is not milliseconds")
    return result


def validate_response(
    response: HTTPResponse,
    *,
    request_url: str,
    instrument_id: str = DEFAULT_INSTRUMENT,
    requested_limit: int = DEFAULT_LIMIT,
    retrieved_at: datetime | None = None,
) -> FundingProbeEvidence:
    try:
        decoded = json.loads(response.body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OKXFundingProbeError("Response is not valid UTF-8 JSON") from exc
    if not isinstance(decoded, dict):
        raise OKXFundingProbeError("Expected a top-level JSON object")
    payload = cast(Mapping[str, Any], decoded)
    if set(("code", "msg", "data")) - set(payload):
        raise OKXFundingProbeError("Response lacks required top-level fields")
    if str(payload["code"]) != "0" or str(payload["msg"]) != "":
        raise OKXFundingProbeError(
            f"OKX API rejected request: code={payload['code']!r}, msg={payload['msg']!r}"
        )
    raw_rows = payload["data"]
    if not isinstance(raw_rows, list) or not raw_rows:
        raise OKXFundingProbeError("Expected a non-empty data array")
    if len(raw_rows) > requested_limit:
        raise OKXFundingProbeError("Response exceeded the requested row bound")

    timestamps: list[int] = []
    schema: set[str] = set()
    for index, value in enumerate(raw_rows):
        if not isinstance(value, dict):
            raise OKXFundingProbeError(f"Row {index} is not an object")
        row = cast(Mapping[str, Any], value)
        missing = REQUIRED_FIELDS - set(row)
        if missing:
            raise OKXFundingProbeError(f"Row {index} lacks fields: {sorted(missing)}")
        if str(row["instId"]) != instrument_id or str(row["instType"]) != "SWAP":
            raise OKXFundingProbeError(f"Row {index} has unexpected instrument identity")
        _decimal(row["fundingRate"], field="fundingRate", row_index=index)
        _decimal(row["realizedRate"], field="realizedRate", row_index=index)
        timestamps.append(_timestamp(row["fundingTime"], row_index=index))
        schema.update(str(key) for key in row)

    if len(timestamps) != len(set(timestamps)):
        raise OKXFundingProbeError("Duplicate fundingTime values detected")
    descending = timestamps == sorted(timestamps, reverse=True)
    ascending = timestamps == sorted(timestamps)
    if not descending and not ascending:
        raise OKXFundingProbeError("Funding timestamps are not deterministically ordered")
    chronological = sorted(timestamps)
    intervals = Counter(
        (current - previous) // 1000 for previous, current in pairwise(chronological)
    )
    schema_fields = tuple(sorted(schema))
    schema_bytes = "\x00".join(schema_fields).encode("utf-8")
    retrieval = retrieved_at or datetime.now(UTC)
    if retrieval.tzinfo is None:
        raise ValueError("retrieved_at must be timezone-aware")
    request_fingerprint = _sha256(request_url.encode("utf-8"))
    return FundingProbeEvidence(
        schema_version="1.0",
        source_id="OKX_PUBLIC_FUNDING_RATE_HISTORY",
        official_host=OFFICIAL_HOST,
        endpoint_path=API_PATH,
        instrument_id=instrument_id,
        requested_limit=requested_limit,
        request_fingerprint_sha256=request_fingerprint,
        retrieved_at=retrieval.astimezone(UTC).isoformat(),
        http_status=response.status_code,
        content_type=response.content_type,
        response_byte_count=len(response.body),
        response_sha256=_sha256(response.body),
        api_code="0",
        row_count=len(raw_rows),
        schema_fields=schema_fields,
        schema_sha256=_sha256(schema_bytes),
        min_funding_time_ms=min(timestamps),
        max_funding_time_ms=max(timestamps),
        unique_funding_times=len(set(timestamps)),
        timestamp_order="DESCENDING" if descending else "ASCENDING",
        observed_interval_seconds_counts=tuple(sorted(intervals.items())),
        raw_rows_persisted=False,
        raw_rows_published=False,
        returns_computed=False,
        economic_edge_verdict="INCONCLUSIVE",
    )


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def run_probe(output_dir: str | Path) -> FundingProbeEvidence:
    url = build_url()
    response = fetch_public_response(url)
    evidence = validate_response(response, request_url=url)
    payload = asdict(evidence)
    _atomic_write(
        Path(output_dir) / "okx-funding-probe-evidence.json",
        (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return evidence


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    evidence = run_probe(args.output_dir)
    print(json.dumps(asdict(evidence), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
