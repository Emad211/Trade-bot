from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import urllib.error
import urllib.request
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from hybrid_trader.replication.okx_historical_export import (
    MAX_ARCHIVE_BYTES,
    inspect_funding_archive_bytes,
)

EXPORT_ENDPOINT = "https://www.okx.com/priapi/v5/broker/public/trade-data/download-link"
HISTORICAL_DATA_PAGE = "https://www.okx.com/en-gb/historical-data"
HISTORICAL_DATA_TERMS = "https://www.okx.com/en-gb/help/historicaldata-terms-and-conditions"
EXPECTED_ARCHIVE_PATH = (
    "/cdn/okex/traderecords/swaprates/monthly/202203/BTC-USDT-SWAP-fundingrates-2022-03.zip"
)
EXPORT_REQUEST: dict[str, Any] = {
    "module": "3",
    "instType": "SWAP",
    "instQueryParam": {"instFamilyList": ["BTC-USDT"]},
    "dateQuery": {
        "dateAggrType": "monthly",
        "begin": "1646092800000",
        "end": "1648684800000",
    },
}


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _official_url_metadata(value: str) -> dict[str, Any]:
    parsed = urlsplit(value)
    if parsed.scheme != "https" or parsed.hostname != "static.okx.com":
        raise RuntimeError(f"Archive link is outside the official host: {value!r}")
    if parsed.path != EXPECTED_ARCHIVE_PATH:
        raise RuntimeError(f"Unexpected OKX archive path: {parsed.path!r}")
    return {
        "scheme": parsed.scheme,
        "host": parsed.hostname,
        "path": parsed.path,
        "query_parameter_names": sorted(
            {key for key, _ in parse_qsl(parsed.query, keep_blank_values=True)}
        ),
        "full_url_sha256": _sha256(value.encode("utf-8")),
    }


def _find_archive_links(value: Any) -> list[str]:
    matches: list[str] = []

    def walk(item: Any) -> None:
        if isinstance(item, Mapping):
            for child in item.values():
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)
        elif isinstance(item, str):
            parsed = urlsplit(item)
            if parsed.path == EXPECTED_ARCHIVE_PATH:
                matches.append(item)

    walk(value)
    return sorted(set(matches))


def _request_export_link() -> tuple[str, dict[str, Any]]:
    request_bytes = json.dumps(
        EXPORT_REQUEST,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    request = urllib.request.Request(
        EXPORT_ENDPOINT,
        data=request_bytes,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": "https://www.okx.com",
            "Referer": HISTORICAL_DATA_PAGE,
            "User-Agent": (
                "Emad211-Trade-bot-replication/1.0 (+https://github.com/Emad211/Trade-bot)"
            ),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            status = int(response.status)
            final_url = response.geturl()
            content_type = response.headers.get("Content-Type", "")
            raw = response.read(2_000_001)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"OKX export endpoint returned HTTP {exc.code}") from exc
    if status != 200 or len(raw) > 2_000_000:
        raise RuntimeError("OKX export metadata response violated the bounded contract")
    final = urlsplit(final_url)
    if final.scheme != "https" or final.hostname != "www.okx.com":
        raise RuntimeError(f"Export endpoint resolved off the official host: {final_url}")
    if "json" not in content_type.lower():
        raise RuntimeError(f"Export endpoint did not return JSON: {content_type!r}")
    payload: Any = json.loads(raw)
    if not isinstance(payload, Mapping) or str(payload.get("code")) != "0":
        raise RuntimeError("OKX export endpoint did not return a successful contract")
    links = _find_archive_links(payload)
    if len(links) != 1:
        raise RuntimeError(f"Expected one March 2022 funding archive link, found {len(links)}")
    link = links[0]
    metadata = {
        "endpoint": EXPORT_ENDPOINT,
        "request_method": "POST",
        "request_body": EXPORT_REQUEST,
        "request_body_sha256": _sha256(request_bytes),
        "response_status": status,
        "response_byte_count": len(raw),
        "response_sha256": _sha256(raw),
        "archive_link": _official_url_metadata(link),
        "raw_metadata_response_retained": False,
    }
    return link, metadata


class _RecordingRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self) -> None:
        super().__init__()
        self.chain: list[dict[str, Any]] = []

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        self.chain.append(
            {
                "status": int(code),
                "from_host": urlsplit(req.full_url).hostname or "",
                "to": _official_url_metadata(newurl),
            }
        )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _download_ephemeral(link: str, destination: Path) -> dict[str, Any]:
    redirect_handler = _RecordingRedirectHandler()
    opener = urllib.request.build_opener(redirect_handler)
    request = urllib.request.Request(
        link,
        method="GET",
        headers={
            "Accept": "application/zip,application/octet-stream,*/*;q=0.1",
            "Referer": HISTORICAL_DATA_PAGE,
            "User-Agent": (
                "Emad211-Trade-bot-replication/1.0 (+https://github.com/Emad211/Trade-bot)"
            ),
        },
    )
    try:
        with opener.open(request, timeout=90) as response, destination.open("wb") as handle:
            status = int(response.status)
            final_url = response.geturl()
            headers = {key.lower(): value for key, value in response.headers.items()}
            if status not in {200, 206}:
                raise RuntimeError(f"OKX archive returned HTTP {status}")
            final_metadata = _official_url_metadata(final_url)
            declared_length = headers.get("content-length")
            if declared_length is not None and int(declared_length) > MAX_ARCHIVE_BYTES:
                raise RuntimeError("OKX archive exceeds the pre-download byte guard")
            byte_count = 0
            while True:
                chunk = response.read(64 * 1024)
                if not chunk:
                    break
                byte_count += len(chunk)
                if byte_count > MAX_ARCHIVE_BYTES:
                    raise RuntimeError("OKX archive exceeded the streaming byte guard")
                handle.write(chunk)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"OKX archive returned HTTP {exc.code}") from exc

    return {
        "request_method": "GET",
        "status": status,
        "final_url": final_metadata,
        "redirect_chain": redirect_handler.chain,
        "selected_headers": {
            key: headers[key]
            for key in (
                "content-type",
                "content-length",
                "etag",
                "last-modified",
                "accept-ranges",
                "content-disposition",
                "cache-control",
                "x-amz-version-id",
                "x-oss-hash-crc64ecma",
            )
            if key in headers
        },
        "downloaded_byte_count": byte_count,
    }


def run(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    temporary_root = Path(tempfile.mkdtemp(prefix="okx-2022-funding-"))
    archive_path = temporary_root / "funding.zip"
    evidence: dict[str, Any] | None = None
    try:
        link, export_metadata = _request_export_link()
        delivery_metadata = _download_ephemeral(link, archive_path)
        archive_bytes = archive_path.read_bytes()
        profile = inspect_funding_archive_bytes(archive_bytes)
        evidence = {
            "schema_version": "1.0",
            "pilot_id": "OKX_BTC_USDT_SWAP_FUNDING_2022_03_EPHEMERAL_V1",
            "retrieved_at": datetime.now(tz=UTC).isoformat(),
            "historical_data_page": HISTORICAL_DATA_PAGE,
            "historical_data_terms": HISTORICAL_DATA_TERMS,
            "license_contract": {
                "personal_strategy_development_allowed": True,
                "license_revocable": True,
                "delete_all_copies_on_revocation_or_expiry": True,
                "public_redistribution_allowed": False,
            },
            "export_metadata": export_metadata,
            "delivery_metadata": delivery_metadata,
            "archive_profile": profile.to_safe_dict(),
            "storage_mode": "EPHEMERAL_RUNNER_ONLY",
            "raw_archive_uploaded": False,
            "raw_archive_retained": False,
            "raw_rows_retained": False,
            "ordered_timestamp_series_retained": False,
            "funding_rate_values_retained": False,
            "basis_computed": False,
            "funding_pnl_computed": False,
            "returns_computed": False,
            "empirical_fitting_executed": False,
            "paper_or_live_trading_authorized": False,
            "raw_archive_deleted_verified": False,
            "gate_verdict": "PRIVATE_REVOCABLE_PILOT_TECHNICALLY_VERIFIED",
        }
    finally:
        if archive_path.exists():
            archive_path.unlink()
        shutil.rmtree(temporary_root, ignore_errors=False)

    if evidence is None:
        raise RuntimeError("OKX funding evidence was not produced")
    evidence["raw_archive_deleted_verified"] = not temporary_root.exists()
    if evidence["raw_archive_deleted_verified"] is not True:
        raise RuntimeError("Ephemeral OKX archive deletion could not be verified")
    evidence_bytes = (json.dumps(evidence, indent=2, sort_keys=True) + "\n").encode("utf-8")
    evidence["evidence_sha256_without_self_hash"] = _sha256(evidence_bytes)
    output = output_dir / "evidence.json"
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    evidence = run(args.output)
    profile = evidence["archive_profile"]
    print(
        json.dumps(
            {
                "pilot_id": evidence["pilot_id"],
                "archive_sha256": profile["archive_sha256"],
                "archive_byte_count": profile["archive_byte_count"],
                "member": profile["member"],
                "raw_archive_deleted_verified": evidence["raw_archive_deleted_verified"],
                "gate_verdict": evidence["gate_verdict"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
