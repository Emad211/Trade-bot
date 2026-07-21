from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit

from hybrid_trader.replication.okx_instrument_sources import (
    CURRENT_INSTRUMENT_URL,
    MAX_API_BYTES,
    parse_current_instrument_response,
)
from hybrid_trader.replication.okx_prospective_registry import (
    ObservationClock,
    ProspectiveFundingSourceContent,
    ProspectiveInstrumentContent,
    ProspectiveRegistryObservation,
    SourceHealthObservation,
    SourceHealthStatus,
)
from hybrid_trader.replication.okx_public_funding_probe import (
    DEFAULT_INSTRUMENT,
    DEFAULT_LIMIT,
    build_url,
    fetch_public_response,
    validate_response,
)

REGISTRY_ID = "OKX_BTC_USDT_SWAP_PROSPECTIVE_REGISTRY_V1"
MAX_ATTEMPTS = 4
TRANSIENT_HTTP_CODES = {429, 500, 502, 503, 504}


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _schema_sha256(fields: tuple[str, ...]) -> str:
    return _sha256("\x00".join(fields).encode("utf-8"))


def _fetch_current_instrument() -> tuple[bytes, int, str, str, datetime, datetime]:
    parsed = urlsplit(CURRENT_INSTRUMENT_URL)
    if parsed.scheme != "https" or parsed.hostname != "www.okx.com":
        raise RuntimeError("Current instrument URL is outside the official OKX host")
    request = urllib.request.Request(
        CURRENT_INSTRUMENT_URL,
        headers={
            "Accept": "application/json",
            "User-Agent": (
                "Emad211-Trade-bot-replication/1.0 "
                "(+https://github.com/Emad211/Trade-bot)"
            ),
        },
    )
    last_error: BaseException | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        started_at = datetime.now(tz=UTC)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read(MAX_API_BYTES + 1)
                received_at = datetime.now(tz=UTC)
                status = int(response.status)
                final_url = response.geturl()
                content_type = response.headers.get("Content-Type", "")
            if len(raw) > MAX_API_BYTES:
                raise RuntimeError("Current instrument response exceeded the byte guard")
            return raw, status, final_url, content_type, started_at, received_at
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in TRANSIENT_HTTP_CODES or attempt == MAX_ATTEMPTS:
                raise RuntimeError(
                    f"Current instrument endpoint returned HTTP {exc.code}"
                ) from exc
        except (TimeoutError, urllib.error.URLError) as exc:
            last_error = exc
            if attempt == MAX_ATTEMPTS:
                raise RuntimeError(
                    "Current instrument endpoint exhausted bounded attempts"
                ) from exc
        time.sleep(attempt * 2)
    raise RuntimeError(f"Current instrument request failed: {last_error!r}")


def _instrument_schema(raw: bytes) -> tuple[str, ...]:
    payload: Any = json.loads(raw)
    if not isinstance(payload, dict):
        raise RuntimeError("Instrument response is not an object")
    data = payload.get("data")
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        raise RuntimeError("Instrument response lacks one exact instrument object")
    instrument = cast(dict[str, Any], data[0])
    return tuple(sorted(str(key) for key in instrument))


def run(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    (
        instrument_raw,
        instrument_status,
        instrument_final_url,
        instrument_content_type,
        instrument_started_at,
        instrument_received_at,
    ) = _fetch_current_instrument()
    instrument_profile = parse_current_instrument_response(
        raw=instrument_raw,
        http_status=instrument_status,
        final_url=instrument_final_url,
        content_type=instrument_content_type,
    )
    instrument_validated_at = datetime.now(tz=UTC)
    instrument_schema = _instrument_schema(instrument_raw)
    instrument_content = ProspectiveInstrumentContent(
        source_id=instrument_profile.source_id,
        official_host=instrument_profile.final_host,
        endpoint_path=instrument_profile.final_path,
        response_byte_count=instrument_profile.byte_count,
        response_sha256=instrument_profile.response_sha256,
        schema_fields=instrument_schema,
        schema_sha256=_schema_sha256(instrument_schema),
        selected_fields=instrument_profile.selected_fields,
        provider_time_fields={
            "listTime": instrument_profile.selected_fields.get("listTime"),
            "contTdSwTime": instrument_profile.selected_fields.get("contTdSwTime"),
        },
    )

    funding_url = build_url(
        instrument_id=DEFAULT_INSTRUMENT,
        limit=DEFAULT_LIMIT,
    )
    funding_started_at = datetime.now(tz=UTC)
    funding_response = fetch_public_response(funding_url)
    funding_received_at = datetime.now(tz=UTC)
    funding_evidence = validate_response(
        funding_response,
        request_url=funding_url,
        retrieved_at=funding_received_at,
    )
    funding_validated_at = datetime.now(tz=UTC)
    funding_content = ProspectiveFundingSourceContent(
        source_id=funding_evidence.source_id,
        official_host=funding_evidence.official_host,
        endpoint_path=funding_evidence.endpoint_path,
        request_fingerprint_sha256=funding_evidence.request_fingerprint_sha256,
        response_byte_count=funding_evidence.response_byte_count,
        response_sha256=funding_evidence.response_sha256,
        schema_fields=funding_evidence.schema_fields,
        schema_sha256=funding_evidence.schema_sha256,
        row_count=funding_evidence.row_count,
        unique_provider_timestamps=funding_evidence.unique_funding_times,
        minimum_provider_timestamp_ms=funding_evidence.min_funding_time_ms,
        maximum_provider_timestamp_ms=funding_evidence.max_funding_time_ms,
        interval_seconds_counts=funding_evidence.observed_interval_seconds_counts,
    )

    committed_at = datetime.now(tz=UTC)
    instrument_clock = ObservationClock(
        request_started_at=instrument_started_at,
        response_received_at=instrument_received_at,
        provider_timestamp=None,
        research_available_at=instrument_validated_at,
        registry_committed_at=committed_at,
    )
    funding_clock = ObservationClock(
        request_started_at=funding_started_at,
        response_received_at=funding_received_at,
        provider_timestamp=None,
        research_available_at=funding_validated_at,
        registry_committed_at=committed_at,
    )

    instrument_observation = ProspectiveRegistryObservation(
        observation_clock=instrument_clock,
        content_kind="INSTRUMENT",
        content_version_id=instrument_content.content_version_id,
        source_health=SourceHealthObservation(
            status=SourceHealthStatus.SUCCESS,
            http_status=instrument_status,
            application_code="0",
            latency_milliseconds=max(
                0,
                round(
                    (instrument_received_at - instrument_started_at).total_seconds()
                    * 1000
                ),
            ),
            response_sha256=instrument_content.response_sha256,
        ),
    )
    funding_observation = ProspectiveRegistryObservation(
        observation_clock=funding_clock,
        content_kind="FUNDING_SOURCE",
        content_version_id=funding_content.content_version_id,
        source_health=SourceHealthObservation(
            status=SourceHealthStatus.SUCCESS,
            http_status=funding_evidence.http_status,
            application_code=funding_evidence.api_code,
            latency_milliseconds=max(
                0,
                round(
                    (funding_received_at - funding_started_at).total_seconds() * 1000
                ),
            ),
            response_sha256=funding_content.response_sha256,
        ),
    )

    evidence: dict[str, Any] = {
        "schema_version": "1.0",
        "registry_id": REGISTRY_ID,
        "collection_mode": "PROSPECTIVE_ONLY",
        "collection_started_at_utc": min(
            instrument_started_at,
            funding_started_at,
        ).isoformat(),
        "registry_committed_at_utc": committed_at.isoformat(),
        "instrument_content": instrument_content.model_dump(mode="json"),
        "funding_source_content": funding_content.model_dump(mode="json"),
        "observations": [
            {
                **instrument_observation.model_dump(mode="json"),
                "observation_id": instrument_observation.observation_id,
            },
            {
                **funding_observation.model_dump(mode="json"),
                "observation_id": funding_observation.observation_id,
            },
        ],
        "version_ids": {
            "instrument": instrument_content.content_version_id,
            "funding_source": funding_content.content_version_id,
        },
        "provider_timestamp_policy": {
            "instrument_response_provider_timestamp": None,
            "funding_response_provider_timestamp": None,
            "funding_settlement_times_are_provider_response_timestamps": False,
            "missing_provider_timestamp_preserved_as_null": True,
        },
        "retention_state": {
            "raw_instrument_response_retained": False,
            "raw_funding_response_retained": False,
            "funding_rate_values_retained": False,
            "ordered_timestamp_series_retained": False,
            "public_market_rows_retained": False,
        },
        "historical_state": {
            "historical_backfill": False,
            "historical_effective_time_inferred": False,
            "current_metadata_projected_backward": False,
        },
        "authorization": {
            "basis_computation": False,
            "funding_pnl_computation": False,
            "returns_computation": False,
            "empirical_fitting": False,
            "parameter_tuning": False,
            "strategy_testing": False,
            "paper_trading": False,
            "live_trading": False,
            "capital_deployment": False,
            "report_2_4_full_authorization": False,
        },
        "registry_verdict": "INITIAL_PROSPECTIVE_SNAPSHOT_ONLY",
        "issue_52_outcome": None,
        "economic_edge_verdict": "INCONCLUSIVE",
    }
    output_path = output_dir / "okx-prospective-registry-initial-snapshot.json"
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
                "registry_id": evidence["registry_id"],
                "collection_started_at_utc": evidence["collection_started_at_utc"],
                "version_ids": evidence["version_ids"],
                "observations": [
                    {
                        "content_kind": item["content_kind"],
                        "observation_id": item["observation_id"],
                        "source_health": item["source_health"],
                    }
                    for item in evidence["observations"]
                ],
                "registry_verdict": evidence["registry_verdict"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
