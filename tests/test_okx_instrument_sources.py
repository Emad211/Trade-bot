from __future__ import annotations

import json

import pytest

from hybrid_trader.replication.okx_instrument_sources import (
    CURRENT_INSTRUMENT_FIELDS,
    OKXInstrumentSourceError,
    OfficialPageContract,
    audit_official_page_bytes,
    normalize_document_text,
    parse_current_instrument_response,
    safe_url_metadata,
)


def _contract() -> OfficialPageContract:
    return OfficialPageContract(
        source_id="TEST_OFFICIAL_PAGE",
        url="https://www.okx.com/help/test",
        evidence_class="OFFICIAL_DATED_EFFECTIVE_NOTICE",
        published_date="2022-03-01",
        expected_markers=("BTCUSDT Perpetual", "0.01 BTC", "March 2022"),
        historical_role="SYNTHETIC_TEST",
    )


def _instrument_payload(**overrides: str) -> bytes:
    instrument = {
        "instId": "BTC-USDT-SWAP",
        "instFamily": "BTC-USDT",
        "instType": "SWAP",
        "ctType": "linear",
        "ctVal": "0.01",
        "ctValCcy": "BTC",
        "ctMult": "1",
        "settleCcy": "USDT",
        "tickSz": "0.1",
        "lotSz": "0.01",
        "minSz": "0.01",
        "listTime": "1573557408000",
        "contTdSwTime": "1611916860000",
        "state": "live",
        "extraCurrentField": "not-retained-as-a-value",
    }
    instrument.update(overrides)
    return json.dumps({"code": "0", "data": [instrument], "msg": ""}).encode()


def test_normalize_document_text_unescapes_and_collapses_markup() -> None:
    raw = b"<html><body>BTCUSDT&nbsp; Perpetual\n <b>0.01 BTC</b></body></html>"

    assert normalize_document_text(raw) == "BTCUSDT Perpetual 0.01 BTC"


def test_safe_url_metadata_rejects_non_okx_hosts() -> None:
    with pytest.raises(OKXInstrumentSourceError, match="outside the OKX"):
        safe_url_metadata("https://example.com/help/test")

    assert safe_url_metadata("https://static.okx.com/path/file.zip?v=1&token=redacted") == (
        "https",
        "static.okx.com",
        "/path/file.zip",
        ("token", "v"),
    )


def test_page_audit_retains_only_hash_marker_and_transport_metadata() -> None:
    raw = b"<html><body>BTCUSDT Perpetual <b>0.01 BTC</b> <span>March 2022</span></body></html>"

    audit = audit_official_page_bytes(
        contract=_contract(),
        raw=raw,
        http_status=200,
        final_url="https://www.okx.com/help/test?locale=en",
        content_type="text/html; charset=utf-8",
    )
    safe = audit.to_safe_dict()

    assert audit.markers_all_present is True
    assert audit.marker_counts == {
        "BTCUSDT Perpetual": 1,
        "0.01 BTC": 1,
        "March 2022": 1,
    }
    assert audit.raw_body_retained is False
    assert audit.historical_use_authorized_by_audit is False
    assert safe["byte_count"] == len(raw)
    assert len(safe["sha256"]) == 64
    assert "<html>" not in json.dumps(safe)


def test_page_audit_fails_closed_when_a_marker_disappears() -> None:
    with pytest.raises(OKXInstrumentSourceError, match="lacks expected markers"):
        audit_official_page_bytes(
            contract=_contract(),
            raw=b"BTCUSDT Perpetual 0.01 BTC",
            http_status=200,
            final_url="https://www.okx.com/help/test",
            content_type="text/html",
        )


def test_current_instrument_profile_is_current_only_negative_control() -> None:
    raw = _instrument_payload()

    profile = parse_current_instrument_response(
        raw=raw,
        http_status=200,
        final_url=(
            "https://www.okx.com/api/v5/public/instruments?instType=SWAP&instId=BTC-USDT-SWAP"
        ),
        content_type="application/json",
    )

    assert tuple(profile.selected_fields) == CURRENT_INSTRUMENT_FIELDS
    assert profile.selected_fields["instId"] == "BTC-USDT-SWAP"
    assert profile.selected_fields["ctType"] == "linear"
    assert profile.selected_fields["ctVal"] == "0.01"
    assert profile.selected_fields["settleCcy"] == "USDT"
    assert profile.raw_response_retained is False
    assert profile.historical_use_authorized is False
    assert "extraCurrentField" not in profile.selected_fields


def test_current_instrument_profile_rejects_wrong_or_incomplete_identity() -> None:
    with pytest.raises(OKXInstrumentSourceError, match="identity changed"):
        parse_current_instrument_response(
            raw=_instrument_payload(instId="ETH-USDT-SWAP"),
            http_status=200,
            final_url="https://www.okx.com/api/v5/public/instruments",
            content_type="application/json",
        )

    with pytest.raises(OKXInstrumentSourceError, match="lacks required fields"):
        parse_current_instrument_response(
            raw=_instrument_payload(tickSz=""),
            http_status=200,
            final_url="https://www.okx.com/api/v5/public/instruments",
            content_type="application/json",
        )


def test_current_instrument_profile_rejects_multiple_rows() -> None:
    row = json.loads(_instrument_payload())["data"][0]
    raw = json.dumps({"code": "0", "data": [row, row], "msg": ""}).encode()

    with pytest.raises(OKXInstrumentSourceError, match="exactly one instrument"):
        parse_current_instrument_response(
            raw=raw,
            http_status=200,
            final_url="https://www.okx.com/api/v5/public/instruments",
            content_type="application/json",
        )
