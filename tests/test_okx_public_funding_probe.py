from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from hybrid_trader.replication.okx_public_funding_probe import (
    HTTPResponse,
    OKXFundingProbeError,
    build_url,
    validate_response,
)


def _row(timestamp: int, *, inst_id: str = "BTC-USDT-SWAP") -> dict[str, str]:
    return {
        "formulaType": "noRate",
        "fundingRate": "0.0001",
        "fundingTime": str(timestamp),
        "instId": inst_id,
        "instType": "SWAP",
        "method": "current_period",
        "realizedRate": "0.00009",
    }


def _response(rows: list[dict[str, str]]) -> HTTPResponse:
    body = json.dumps({"code": "0", "msg": "", "data": rows}).encode()
    return HTTPResponse(
        body=body,
        status_code=200,
        content_type="application/json",
        final_url=build_url(),
    )


def test_build_url_is_bounded_and_official() -> None:
    url = build_url(limit=100)
    assert url.startswith("https://www.okx.com/api/v5/public/funding-rate-history?")
    assert "instId=BTC-USDT-SWAP" in url
    assert "limit=100" in url
    with pytest.raises(ValueError, match="between 1 and 100"):
        build_url(limit=101)


def test_validate_records_only_safe_metadata() -> None:
    timestamps = [1703059200000, 1703030400000, 1703001600000]
    evidence = validate_response(
        _response([_row(value) for value in timestamps]),
        request_url=build_url(),
        retrieved_at=datetime(2026, 7, 20, tzinfo=UTC),
    )
    assert evidence.row_count == 3
    assert evidence.unique_funding_times == 3
    assert evidence.timestamp_order == "DESCENDING"
    assert evidence.observed_interval_seconds_counts == ((28800, 2),)
    assert evidence.raw_rows_persisted is False
    assert evidence.raw_rows_published is False
    assert evidence.returns_computed is False
    assert evidence.economic_edge_verdict == "INCONCLUSIVE"
    assert "fundingRate" in evidence.schema_fields
    assert not hasattr(evidence, "funding_rates")


def test_validate_accepts_variable_intervals_without_fixed_assumption() -> None:
    timestamps = [1703059200000, 1703037600000, 1703030400000]
    evidence = validate_response(
        _response([_row(value) for value in timestamps]),
        request_url=build_url(),
    )
    assert evidence.observed_interval_seconds_counts == ((7200, 1), (21600, 1))


def test_validate_rejects_wrong_instrument_and_duplicate_time() -> None:
    with pytest.raises(OKXFundingProbeError, match="unexpected instrument identity"):
        validate_response(
            _response([_row(1703059200000, inst_id="ETH-USDT-SWAP")]),
            request_url=build_url(),
        )
    duplicate = [_row(1703059200000), _row(1703059200000)]
    with pytest.raises(OKXFundingProbeError, match="Duplicate"):
        validate_response(_response(duplicate), request_url=build_url())


def test_validate_rejects_bad_api_status_and_unordered_time() -> None:
    rejected = HTTPResponse(
        body=json.dumps({"code": "50000", "msg": "error", "data": []}).encode(),
        status_code=200,
        content_type="application/json",
        final_url=build_url(),
    )
    with pytest.raises(OKXFundingProbeError, match="rejected request"):
        validate_response(rejected, request_url=build_url())
    unordered = [_row(1703030400000), _row(1703059200000), _row(1703040000000)]
    with pytest.raises(OKXFundingProbeError, match="not deterministically ordered"):
        validate_response(_response(unordered), request_url=build_url())


def test_validate_rejects_non_finite_rate_and_bad_timestamp() -> None:
    invalid_rate = _row(1703059200000)
    invalid_rate["realizedRate"] = str(Decimal("NaN"))
    with pytest.raises(OKXFundingProbeError, match="non-finite"):
        validate_response(_response([invalid_rate]), request_url=build_url())
    invalid_time = _row(123)
    with pytest.raises(OKXFundingProbeError, match="not milliseconds"):
        validate_response(_response([invalid_time]), request_url=build_url())
