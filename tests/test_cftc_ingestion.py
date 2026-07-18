from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from hybrid_trader.replication import cftc_ingestion
from hybrid_trader.replication.cftc_ingestion import (
    CFTCPilotError,
    HTTPArtifact,
    build_query_url,
    parse_and_validate,
    write_pilot_bundle,
)


def _row(identifier: str = "220913020601F") -> dict[str, str]:
    return {
        "id": identifier,
        "market_and_exchange_names": "UST BOND - CHICAGO BOARD OF TRADE",
        "report_date_as_yyyy_mm_dd": "2022-09-13T00:00:00.000",
        "cftc_contract_market_code": "020601",
        "commodity_name": "T-BONDS",
        "open_interest_all": "100",
        "tot_rept_positions_long_all": "80",
        "tot_rept_positions_short": "70",
        "nonrept_positions_long_all": "20",
        "nonrept_positions_short_all": "30",
        "futonly_or_combined": "FutOnly",
    }


def _raw(rows: list[dict[str, str]]) -> bytes:
    return json.dumps(rows, separators=(",", ":"), sort_keys=True).encode()


def test_build_query_url_is_narrow_and_does_not_server_sort() -> None:
    url = build_query_url(report_date=date(2022, 9, 13), limit=5000)
    assert "gpe5-46if.json" in url
    assert "%24select=" in url
    assert "report_date_as_yyyy_mm_dd=2022-09-13T00%3A00%3A00.000" in url
    assert "%24order" not in url


def test_validate_accepts_unordered_rows_and_records_inversions() -> None:
    first = _row("220913020604F")
    second = _row("220913020601F")
    result = parse_and_validate(_raw([first, second]))
    assert result.row_count == 2
    assert result.unique_id_count == 2
    assert result.accounting_identity_rows_checked == 2
    assert result.raw_order_inversion_count == 1
    assert result.canonical_sort_key == "id"


def test_validate_rejects_duplicate_ids() -> None:
    row = _row()
    with pytest.raises(CFTCPilotError, match="Duplicate"):
        parse_and_validate(_raw([row, row]))


def test_validate_rejects_wrong_date_and_accounting() -> None:
    wrong_date = _row()
    wrong_date["report_date_as_yyyy_mm_dd"] = "2022-09-20T00:00:00.000"
    with pytest.raises(CFTCPilotError, match="unexpected report date"):
        parse_and_validate(_raw([wrong_date]))

    wrong_accounting = _row()
    wrong_accounting["nonrept_positions_long_all"] = "19"
    with pytest.raises(CFTCPilotError, match="Long-side accounting"):
        parse_and_validate(_raw([wrong_accounting]))


def test_bundle_preserves_raw_and_creates_canonical_hash(tmp_path: Path) -> None:
    raw = _raw([_row("220913020604F"), _row("220913020601F")])
    validation = parse_and_validate(raw)
    artifact = HTTPArtifact(raw, 200, "application/json; charset=utf-8", '"etag"', None)
    manifest = write_pilot_bundle(
        tmp_path,
        artifact=artifact,
        validation=validation,
        source_url="https://publicreporting.cftc.gov/resource/gpe5-46if.json?frozen=1",
        retrieved_at=datetime(2026, 7, 18, tzinfo=UTC),
    )
    stored = (tmp_path / "tff_futures_only_2022-09-13.raw.json").read_bytes()
    canonical = (tmp_path / "tff_futures_only_2022-09-13.canonical.json").read_bytes()
    canonical_rows = json.loads(canonical)
    assert stored == raw
    assert [row["id"] for row in canonical_rows] == ["220913020601F", "220913020604F"]
    assert manifest["raw_sha256"] == hashlib.sha256(raw).hexdigest()
    assert manifest["raw_byte_count"] == len(raw)
    assert manifest["canonical_sha256"] == hashlib.sha256(canonical).hexdigest()
    assert manifest["canonical_byte_count"] == len(canonical)
    assert manifest["artifact_audit_pass"] is False
    assert manifest["source_access_state"] == "RAW_ARTIFACT_ACQUIRED_NOT_YET_ACTIONS_STAGED"


def test_ingest_quarantines_downloaded_bytes_when_validation_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    invalid_row = _row()
    invalid_row["nonrept_positions_long_all"] = "19"
    raw = _raw([invalid_row])
    artifact = HTTPArtifact(raw, 200, "application/json; charset=utf-8", '"etag"', None)
    monkeypatch.setattr(cftc_ingestion, "fetch_official_bytes", lambda *args, **kwargs: artifact)

    with pytest.raises(CFTCPilotError, match="Long-side accounting"):
        cftc_ingestion.ingest_pilot(tmp_path)

    stored = (tmp_path / "tff_futures_only_2022-09-13.raw.json").read_bytes()
    failure = json.loads(
        (tmp_path / "validation-failure-manifest.json").read_text(encoding="utf-8")
    )
    assert stored == raw
    assert failure["raw_sha256"] == hashlib.sha256(raw).hexdigest()
    assert failure["validation_status"] == "FAILED_QUARANTINED"
    assert failure["artifact_audit_pass"] is False
    assert failure["source_access_state"] == (
        "RAW_ARTIFACT_ACQUIRED_VALIDATION_FAILED_QUARANTINED"
    )
