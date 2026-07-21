from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from hybrid_trader.replication.okx_instrument_sources import (
    CURRENT_INSTRUMENT_URL,
    MAX_API_BYTES,
    MAX_PAGE_BYTES,
    SOURCE_CONTRACTS,
    OKXInstrumentSourceError,
    audit_official_page_bytes,
    parse_current_instrument_response,
)

AUDIT_ID = "OKX_BTC_USDT_SWAP_2022_SOURCE_IDENTITY_AUDIT_V1"
TRANSIENT_HTTP_CODES = {429, 500, 502, 503, 504}


class _OfficialRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        parsed = urlsplit(newurl)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not (
            host == "okx.com" or host == "www.okx.com" or host.endswith(".okx.com")
        ):
            raise OKXInstrumentSourceError(
                f"Official source redirected outside OKX: {newurl!r}"
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _fetch_bounded(
    url: str,
    *,
    max_bytes: int,
    accept: str,
    attempts: int = 4,
) -> tuple[bytes, int, str, str]:
    opener = urllib.request.build_opener(_OfficialRedirectHandler())
    request = urllib.request.Request(
        url,
        headers={
            "Accept": accept,
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": (
                "Emad211-Trade-bot-replication/1.0 "
                "(+https://github.com/Emad211/Trade-bot)"
            ),
        },
    )
    last_error: BaseException | None = None
    for attempt in range(1, attempts + 1):
        try:
            with opener.open(request, timeout=60) as response:
                status = int(response.status)
                final_url = response.geturl()
                content_type = response.headers.get("Content-Type", "")
                raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                raise OKXInstrumentSourceError(
                    f"{url} exceeded the {max_bytes}-byte guard"
                )
            return raw, status, final_url, content_type
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in TRANSIENT_HTTP_CODES or attempt == attempts:
                raise OKXInstrumentSourceError(
                    f"{url} returned HTTP {exc.code}"
                ) from exc
        except (TimeoutError, urllib.error.URLError) as exc:
            last_error = exc
            if attempt == attempts:
                raise OKXInstrumentSourceError(
                    f"{url} failed after {attempts} bounded attempts"
                ) from exc
        time.sleep(attempt * 2)
    raise OKXInstrumentSourceError(f"{url} failed: {last_error!r}")


def run(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    retrieved_at = datetime.now(tz=UTC)
    page_audits: list[dict[str, Any]] = []
    for contract in SOURCE_CONTRACTS:
        raw, status, final_url, content_type = _fetch_bounded(
            contract.url,
            max_bytes=MAX_PAGE_BYTES,
            accept="text/html,application/xhtml+xml,*/*;q=0.1",
        )
        audit = audit_official_page_bytes(
            contract=contract,
            raw=raw,
            http_status=status,
            final_url=final_url,
            content_type=content_type,
        )
        page_audits.append(audit.to_safe_dict())

    api_raw, api_status, api_final_url, api_content_type = _fetch_bounded(
        CURRENT_INSTRUMENT_URL,
        max_bytes=MAX_API_BYTES,
        accept="application/json,*/*;q=0.1",
    )
    current_instrument = parse_current_instrument_response(
        raw=api_raw,
        http_status=api_status,
        final_url=api_final_url,
        content_type=api_content_type,
    )

    source_ids = {source["source_id"] for source in page_audits}
    required_ids = {contract.source_id for contract in SOURCE_CONTRACTS}
    if source_ids != required_ids:
        raise OKXInstrumentSourceError("Source audit set changed unexpectedly")

    evidence: dict[str, Any] = {
        "schema_version": "1.0",
        "audit_id": AUDIT_ID,
        "retrieved_at_utc": retrieved_at.isoformat(),
        "page_source_count": len(page_audits),
        "page_sources": page_audits,
        "current_instrument_negative_control": current_instrument.to_safe_dict(),
        "availability_boundaries": {
            "historical_data_service": {
                "scope": "SERVICE",
                "available_by_utc": "2023-10-26T00:00:00+00:00",
                "source_id": "OKX_HISTORICAL_DATA_TERMS_2023_10_26",
                "specific_file_promoted": False,
            },
            "historical_batch_api": {
                "scope": "MODULE",
                "module_id": "HISTORICAL_MARKET_DATA_BATCH_API",
                "available_by_utc": "2025-09-02T00:00:00+00:00",
                "source_id": "OKX_API_CHANGELOG_2025_09_02",
                "specific_file_promoted": False,
            },
            "march_2022_funding_file": {
                "scope": "SPECIFIC_FILE",
                "historical_publication_time_verified": False,
                "available_by_utc_from_this_audit": None,
                "current_retrieval_may_be_backdated": False,
            },
        },
        "field_authorization": {
            "historical_fields_promoted_by_this_audit": [],
            "current_instrument_values_are_historical": False,
            "postponed_face_value_proposal_is_effective": False,
            "currently_revised_guide_is_a_frozen_2022_vintage": False,
        },
        "retention_state": {
            "raw_html_retained": False,
            "raw_api_response_retained": False,
            "market_rows_requested": False,
            "market_rows_retained": False,
            "funding_rate_values_retained": False,
        },
        "authorization": {
            "basis_computation": False,
            "funding_pnl_computation": False,
            "returns_computation": False,
            "empirical_fitting": False,
            "parameter_tuning": False,
            "paper_trading": False,
            "live_trading": False,
            "capital_deployment": False,
            "report_2_4_full_authorization": False,
        },
        "audit_verdict": "SOURCE_IDENTITIES_VERIFIED_NO_HISTORICAL_PROMOTION",
        "issue_51_outcome": None,
        "economic_edge_verdict": "INCONCLUSIVE",
    }
    output_path = output_dir / "okx-2022-instrument-source-audit.json"
    output_path.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    evidence = run(args.output_dir)
    print(
        json.dumps(
            {
                "audit_id": evidence["audit_id"],
                "page_source_count": evidence["page_source_count"],
                "availability_boundaries": evidence["availability_boundaries"],
                "current_instrument_selected_fields": evidence[
                    "current_instrument_negative_control"
                ]["selected_fields"],
                "audit_verdict": evidence["audit_verdict"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
