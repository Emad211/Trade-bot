"""Bounded source-identity audits for the OKX 2022 instrument-version gate."""

from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import parse_qsl, urlsplit

MAX_PAGE_BYTES = 5_000_000
MAX_API_BYTES = 1_000_000
ALLOWED_OKX_HOSTS = {"okx.com", "www.okx.com"}


class OKXInstrumentSourceError(RuntimeError):
    """Raised when an official source violates its frozen audit contract."""


@dataclass(frozen=True)
class OfficialPageContract:
    source_id: str
    url: str
    evidence_class: str
    published_date: str | None
    expected_markers: tuple[str, ...]
    historical_role: str


@dataclass(frozen=True)
class OfficialPageAudit:
    source_id: str
    official_locator: str
    evidence_class: str
    published_date: str | None
    historical_role: str
    http_status: int
    final_scheme: str
    final_host: str
    final_path: str
    final_query_parameter_names: tuple[str, ...]
    content_type: str
    byte_count: int
    sha256: str
    marker_counts: dict[str, int]
    markers_all_present: bool
    raw_body_retained: bool
    historical_use_authorized_by_audit: bool

    def to_safe_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CurrentInstrumentProfile:
    source_id: str
    official_locator: str
    http_status: int
    final_scheme: str
    final_host: str
    final_path: str
    final_query_parameter_names: tuple[str, ...]
    content_type: str
    byte_count: int
    response_sha256: str
    selected_fields: dict[str, str]
    field_count: int
    raw_response_retained: bool
    historical_use_authorized: bool

    def to_safe_dict(self) -> dict[str, Any]:
        return asdict(self)


SOURCE_CONTRACTS = (
    OfficialPageContract(
        source_id="OKX_BTCUSDT_SWAP_LAUNCH_2019_12_16",
        url="https://www.okx.com/en-us/help/usdt-margined-perpetual-swap-now-available",
        evidence_class="OFFICIAL_DATED_EFFECTIVE_NOTICE",
        published_date="2019-12-16",
        expected_markers=(
            "BTCUSDT Perpetual Swap trading is officially live",
            "0.0001BTC",
            "Tick Size",
            "06:00 Dec 16, 2019",
        ),
        historical_role="ORIGINAL_LISTING_AND_INITIAL_SPECIFICATION",
    ),
    OfficialPageContract(
        source_id="OKX_BTCUSDT_FACE_VALUE_2020_03_04",
        url=(
            "https://www.okx.com/en-gb/help/adjustment-of-face-value-for-"
            "usdt-margined-perpetual-swap-futures-trading"
        ),
        evidence_class="OFFICIAL_DATED_EFFECTIVE_NOTICE",
        published_date="2020-03-04",
        expected_markers=(
            "BTCUSDT Perpetual Swap",
            "0.0001 BTC",
            "0.01 BTC",
            "Mar 20",
        ),
        historical_role="CONTRACT_FACE_VALUE_EFFECTIVE_CHANGE",
    ),
    OfficialPageContract(
        source_id="OKX_BTC_FUNDING_RULES_2020_10_14",
        url=(
            "https://www.okx.com/en-us/help/adjustment-of-price-limit-rules-for-"
            "futures-perpetual-swap-and-funding-rate-rules-for-perpetual-swap"
        ),
        evidence_class="OFFICIAL_DATED_EFFECTIVE_NOTICE",
        published_date="2020-10-14",
        expected_markers=(
            "Funding Rate Rules",
            "Interest is currently zero",
            "-0.375%",
            "0.375%",
        ),
        historical_role="FUNDING_FORMULA_AND_BTC_CLAMP_EFFECTIVE_CHANGE",
    ),
    OfficialPageContract(
        source_id="OKX_FACE_VALUE_POSTPONEMENT_2021_05_08",
        url="https://www.okx.com/help/postponement-of-face-value-adjustment",
        evidence_class="OFFICIAL_DATED_POSTPONEMENT",
        published_date="2021-05-08",
        expected_markers=(
            "has been postponed",
            "BTCUSDT",
            "0.01",
            "0.001",
        ),
        historical_role="PROPOSED_CHANGE_NOT_EFFECTIVE_FROM_THIS_SOURCE",
    ),
    OfficialPageContract(
        source_id="OKX_PERPETUAL_GUIDE_2022_06_20_CURRENTLY_REVISED",
        url="https://www.okx.com/en-gb/help/i-perpetual-swaps",
        evidence_class="OFFICIAL_DATED_GUIDE_CURRENTLY_REVISED",
        published_date="2022-06-20",
        expected_markers=(
            "Published on 20 Jun 2022",
            "BTCUSDT Perpetual",
            "0.01 BTC",
            "Tick size",
        ),
        historical_role="NEARBY_LATER_STATE_NEGATIVE_CONTROL",
    ),
    OfficialPageContract(
        source_id="OKX_HISTORICAL_DATA_TERMS_2023_10_26",
        url="https://www.okx.com/en-us/help/historicaldata-terms-and-conditions",
        evidence_class="OFFICIAL_DATED_SERVICE_TERMS",
        published_date="2023-10-26",
        expected_markers=(
            "Published on Oct 26, 2023",
            "historical data",
            "personal use",
            "historical-data",
        ),
        historical_role="SERVICE_EXISTENCE_AND_LICENSE_BOUNDARY",
    ),
    OfficialPageContract(
        source_id="OKX_HISTORICAL_DATA_CATALOG_CURRENT",
        url="https://www.okx.com/historical-data",
        evidence_class="OFFICIAL_CURRENT_PAGE",
        published_date=None,
        expected_markers=(
            "Historical market data",
            "Funding rate",
            "March 2022 onwards",
        ),
        historical_role="CURRENT_CATALOG_LOWER_BOUND_LABEL_ONLY",
    ),
    OfficialPageContract(
        source_id="OKX_API_CHANGELOG_2025_09_02",
        url="https://www.okx.com/docs-v5/log_en/",
        evidence_class="OFFICIAL_DATED_CHANGELOG",
        published_date="2025-09-02",
        expected_markers=(
            "2025-09-02",
            "Historical market data query endpoint",
            "funding rate",
            "daily and monthly data aggregation options",
        ),
        historical_role="SEPARATE_BATCH_API_AVAILABILITY_BOUNDARY",
    ),
)

CURRENT_INSTRUMENT_URL = (
    "https://www.okx.com/api/v5/public/instruments?"
    "instType=SWAP&instId=BTC-USDT-SWAP"
)
CURRENT_INSTRUMENT_FIELDS = (
    "instId",
    "instFamily",
    "instType",
    "ctType",
    "ctVal",
    "ctValCcy",
    "ctMult",
    "settleCcy",
    "tickSz",
    "lotSz",
    "minSz",
    "listTime",
    "contTdSwTime",
    "state",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _is_allowed_okx_host(host: str) -> bool:
    normalized = host.lower()
    return normalized in ALLOWED_OKX_HOSTS or normalized.endswith(".okx.com")


def safe_url_metadata(value: str) -> tuple[str, str, str, tuple[str, ...]]:
    parsed = urlsplit(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not _is_allowed_okx_host(host):
        raise OKXInstrumentSourceError(
            f"Official source resolved outside the OKX HTTPS allow-list: {value!r}"
        )
    query_names = tuple(
        sorted({key for key, _ in parse_qsl(parsed.query, keep_blank_values=True)})
    )
    return parsed.scheme, host, parsed.path, query_names


def normalize_document_text(raw: bytes) -> str:
    """Normalize HTML/JSON source text without retaining a rendered document."""

    try:
        decoded = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise OKXInstrumentSourceError("Official source is not valid UTF-8") from exc
    unescaped = html.unescape(decoded)
    without_tags = re.sub(r"<[^>]+>", " ", unescaped)
    return re.sub(r"\s+", " ", without_tags).strip()


def audit_official_page_bytes(
    *,
    contract: OfficialPageContract,
    raw: bytes,
    http_status: int,
    final_url: str,
    content_type: str,
    max_bytes: int = MAX_PAGE_BYTES,
) -> OfficialPageAudit:
    if http_status != 200:
        raise OKXInstrumentSourceError(
            f"{contract.source_id} returned HTTP {http_status}"
        )
    if not raw or len(raw) > max_bytes:
        raise OKXInstrumentSourceError(
            f"{contract.source_id} violated the {max_bytes}-byte source guard"
        )
    scheme, host, path, query_names = safe_url_metadata(final_url)
    normalized = normalize_document_text(raw).casefold()
    marker_counts = {
        marker: normalized.count(marker.casefold())
        for marker in contract.expected_markers
    }
    if not all(count > 0 for count in marker_counts.values()):
        missing = sorted(marker for marker, count in marker_counts.items() if count == 0)
        raise OKXInstrumentSourceError(
            f"{contract.source_id} lacks expected markers: {missing}"
        )
    return OfficialPageAudit(
        source_id=contract.source_id,
        official_locator=contract.url,
        evidence_class=contract.evidence_class,
        published_date=contract.published_date,
        historical_role=contract.historical_role,
        http_status=http_status,
        final_scheme=scheme,
        final_host=host,
        final_path=path,
        final_query_parameter_names=query_names,
        content_type=content_type,
        byte_count=len(raw),
        sha256=sha256_bytes(raw),
        marker_counts=marker_counts,
        markers_all_present=True,
        raw_body_retained=False,
        historical_use_authorized_by_audit=False,
    )


def parse_current_instrument_response(
    *,
    raw: bytes,
    http_status: int,
    final_url: str,
    content_type: str,
    max_bytes: int = MAX_API_BYTES,
) -> CurrentInstrumentProfile:
    """Profile the current instrument response strictly as a negative control."""

    if http_status != 200:
        raise OKXInstrumentSourceError(
            f"Current instrument endpoint returned HTTP {http_status}"
        )
    if not raw or len(raw) > max_bytes:
        raise OKXInstrumentSourceError(
            f"Current instrument response violated the {max_bytes}-byte guard"
        )
    scheme, host, path, query_names = safe_url_metadata(final_url)
    try:
        payload: Any = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OKXInstrumentSourceError(
            "Current instrument endpoint did not return valid JSON"
        ) from exc
    if not isinstance(payload, dict) or str(payload.get("code")) != "0":
        raise OKXInstrumentSourceError(
            "Current instrument endpoint returned an unsuccessful application code"
        )
    data = payload.get("data")
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        raise OKXInstrumentSourceError(
            "Current instrument endpoint did not return exactly one instrument"
        )
    instrument = data[0]
    if instrument.get("instId") != "BTC-USDT-SWAP":
        raise OKXInstrumentSourceError("Current instrument identity changed")
    selected_fields = {
        field: str(instrument.get(field, "")) for field in CURRENT_INSTRUMENT_FIELDS
    }
    if any(value == "" for value in selected_fields.values()):
        missing = sorted(field for field, value in selected_fields.items() if value == "")
        raise OKXInstrumentSourceError(
            f"Current instrument response lacks required fields: {missing}"
        )
    return CurrentInstrumentProfile(
        source_id="OKX_CURRENT_BTC_USDT_SWAP_INSTRUMENT_API",
        official_locator=CURRENT_INSTRUMENT_URL,
        http_status=http_status,
        final_scheme=scheme,
        final_host=host,
        final_path=path,
        final_query_parameter_names=query_names,
        content_type=content_type,
        byte_count=len(raw),
        response_sha256=sha256_bytes(raw),
        selected_fields=selected_fields,
        field_count=len(instrument),
        raw_response_retained=False,
        historical_use_authorized=False,
    )
