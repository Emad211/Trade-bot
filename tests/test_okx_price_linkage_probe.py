from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta

import pytest

from hybrid_trader.replication.okx_price_linkage_probe import (
    HTTPResponse,
    SOURCE_CONTRACTS,
    OKXPriceLinkageProbeError,
    build_pilot_evidence,
    build_url,
    safe_url_metadata,
    validate_source_response,
)

BASE = datetime(2026, 7, 21, 12, 0, tzinfo=UTC)


def _row_for(source_id: str, timestamp_ms: int = 1784635200000) -> dict[str, str]:
    if source_id == "OKX_SPOT_BTC_USDT_TICKER":
        identity = {"instType": "SPOT", "instId": "BTC-USDT"}
        values = {
            "last": "118000.1",
            "lastSz": "0.1",
            "askPx": "118000.2",
            "askSz": "0.2",
            "bidPx": "118000.0",
            "bidSz": "0.3",
            "open24h": "117000",
            "high24h": "119000",
            "low24h": "116000",
            "volCcy24h": "1000000",
            "vol24h": "10",
            "sodUtc0": "117500",
            "sodUtc8": "117600",
        }
    elif source_id == "OKX_SWAP_BTC_USDT_SWAP_TICKER":
        identity = {"instType": "SWAP", "instId": "BTC-USDT-SWAP"}
        values = {
            "last": "118010.1",
            "lastSz": "1",
            "askPx": "118010.2",
            "askSz": "2",
            "bidPx": "118010.0",
            "bidSz": "3",
            "open24h": "117010",
            "high24h": "119010",
            "low24h": "116010",
            "volCcy24h": "1000001",
            "vol24h": "11",
            "sodUtc0": "117510",
            "sodUtc8": "117610",
        }
    elif source_id == "OKX_SWAP_BTC_USDT_SWAP_MARK_PRICE":
        return {
            "instType": "SWAP",
            "instId": "BTC-USDT-SWAP",
            "markPx": "118005.5",
            "ts": str(timestamp_ms),
        }
    elif source_id == "OKX_BTC_USDT_INDEX_TICKER":
        return {
            "instId": "BTC-USDT",
            "idxPx": "118002.5",
            "high24h": "119002",
            "open24h": "117002",
            "low24h": "116002",
            "sodUtc0": "117502",
            "sodUtc8": "117602",
            "ts": str(timestamp_ms),
        }
    else:
        raise AssertionError(source_id)
    return {**identity, **values, "ts": str(timestamp_ms)}


def _response(
    contract_index: int,
    timestamp_ms: int = 1784635200000,
) -> tuple[str, HTTPResponse]:
    contract = SOURCE_CONTRACTS[contract_index]
    url = build_url(contract)
    body = json.dumps(
        {
            "code": "0",
            "msg": "",
            "data": [_row_for(contract.source_id, timestamp_ms)],
        }
    ).encode()
    return url, HTTPResponse(body, 200, "application/json", url)


def _observation(
    contract_index: int,
    timestamp_ms: int = 1784635200000,
    offset: int = 0,
):
    contract = SOURCE_CONTRACTS[contract_index]
    url, response = _response(contract_index, timestamp_ms)
    return validate_source_response(
        contract=contract,
        response=response,
        request_url=url,
        request_started_at=BASE + timedelta(seconds=offset),
        response_received_at=BASE + timedelta(seconds=offset + 1),
        research_available_at=BASE + timedelta(seconds=offset + 2),
    )


def test_build_urls_are_deterministic_and_bounded() -> None:
    assert build_url(SOURCE_CONTRACTS[0]).endswith(
        "/api/v5/market/ticker?instId=BTC-USDT"
    )
    assert build_url(SOURCE_CONTRACTS[2]).endswith(
        "/api/v5/public/mark-price?instType=SWAP&instId=BTC-USDT-SWAP"
    )
    assert build_url(SOURCE_CONTRACTS[3]).endswith(
        "/api/v5/market/index-tickers?instId=BTC-USDT"
    )


def test_safe_url_rejects_non_okx_or_http() -> None:
    with pytest.raises(OKXPriceLinkageProbeError, match="frozen OKX HTTPS"):
        safe_url_metadata("https://example.com/api/v5/market/ticker?instId=BTC-USDT")
    with pytest.raises(OKXPriceLinkageProbeError, match="frozen OKX HTTPS"):
        safe_url_metadata("http://www.okx.com/api/v5/market/ticker?instId=BTC-USDT")


@pytest.mark.parametrize("contract_index", range(4))
def test_each_contract_validates_identity_schema_decimal_and_timestamp(
    contract_index: int,
) -> None:
    observation = _observation(contract_index)
    contract = SOURCE_CONTRACTS[contract_index]
    assert observation.source_id == contract.source_id
    assert observation.source_kind == contract.source_kind.value
    assert observation.identity_fields == contract.expected_identity_map
    assert observation.market_value_fields_validated == tuple(
        sorted(contract.market_value_fields)
    )
    assert observation.provider_timestamp_ms == 1784635200000
    assert observation.raw_response_retained is False
    assert observation.market_values_retained is False
    assert observation.ordered_price_series_retained is False
    assert observation.historical_backfill is False
    payload = asdict(observation)
    for forbidden in ("last", "bidPx", "askPx", "markPx", "idxPx", "vol24h"):
        assert forbidden not in payload


def test_identity_mismatch_fails_closed() -> None:
    contract = SOURCE_CONTRACTS[0]
    url, response = _response(0)
    decoded = json.loads(response.body)
    decoded["data"][0]["instId"] = "ETH-USDT"
    bad = HTTPResponse(json.dumps(decoded).encode(), 200, "application/json", url)
    with pytest.raises(OKXPriceLinkageProbeError, match="Identity mismatch"):
        validate_source_response(
            contract=contract,
            response=bad,
            request_url=url,
            request_started_at=BASE,
            response_received_at=BASE + timedelta(seconds=1),
            research_available_at=BASE + timedelta(seconds=2),
        )


def test_missing_field_invalid_decimal_and_invalid_timestamp_fail_closed() -> None:
    contract = SOURCE_CONTRACTS[2]
    url, response = _response(2)
    decoded = json.loads(response.body)
    del decoded["data"][0]["markPx"]
    with pytest.raises(OKXPriceLinkageProbeError, match="required fields"):
        validate_source_response(
            contract=contract,
            response=HTTPResponse(
                json.dumps(decoded).encode(), 200, "application/json", url
            ),
            request_url=url,
            request_started_at=BASE,
            response_received_at=BASE + timedelta(seconds=1),
            research_available_at=BASE + timedelta(seconds=2),
        )

    decoded = json.loads(response.body)
    decoded["data"][0]["markPx"] = "NaN"
    with pytest.raises(OKXPriceLinkageProbeError, match="Non-finite"):
        validate_source_response(
            contract=contract,
            response=HTTPResponse(
                json.dumps(decoded).encode(), 200, "application/json", url
            ),
            request_url=url,
            request_started_at=BASE,
            response_received_at=BASE + timedelta(seconds=1),
            research_available_at=BASE + timedelta(seconds=2),
        )

    decoded = json.loads(response.body)
    decoded["data"][0]["ts"] = "123"
    with pytest.raises(OKXPriceLinkageProbeError, match="not milliseconds"):
        validate_source_response(
            contract=contract,
            response=HTTPResponse(
                json.dumps(decoded).encode(), 200, "application/json", url
            ),
            request_url=url,
            request_started_at=BASE,
            response_received_at=BASE + timedelta(seconds=1),
            research_available_at=BASE + timedelta(seconds=2),
        )


def test_wrong_final_path_or_query_contract_fails_closed() -> None:
    contract = SOURCE_CONTRACTS[0]
    url, response = _response(0)
    wrong_path = HTTPResponse(
        response.body,
        200,
        "application/json",
        url.replace("/ticker", "/tickers"),
    )
    with pytest.raises(OKXPriceLinkageProbeError, match="path differs"):
        validate_source_response(
            contract=contract,
            response=wrong_path,
            request_url=url,
            request_started_at=BASE,
            response_received_at=BASE + timedelta(seconds=1),
            research_available_at=BASE + timedelta(seconds=2),
        )
    wrong_query = HTTPResponse(response.body, 200, "application/json", url + "&extra=1")
    with pytest.raises(OKXPriceLinkageProbeError, match="query contract"):
        validate_source_response(
            contract=contract,
            response=wrong_query,
            request_url=url,
            request_started_at=BASE,
            response_received_at=BASE + timedelta(seconds=1),
            research_available_at=BASE + timedelta(seconds=2),
        )


def test_nonmonotonic_provider_timestamps_are_accepted_and_diagnosed() -> None:
    observations = (
        _observation(0, 1784635200000, 0),
        _observation(1, 1784635199000, 3),
        _observation(2, 1784635201000, 6),
        _observation(3, 1784635198000, 9),
    )
    evidence = build_pilot_evidence(observations)
    assert evidence.provider_timestamps_monotonic_in_request_order is False
    assert evidence.provider_cache_contract[
        "later_request_may_return_earlier_provider_timestamp"
    ]
    assert (
        evidence.provider_cache_contract["cross_source_timestamp_monotonicity_required"]
        is False
    )
    assert evidence.provider_timestamp_spread_ms == 3000
    assert all(value is False for value in evidence.retention_state.values())
    assert all(value is False for value in evidence.authorization.values())
    assert evidence.issue_53_outcome is None


def test_source_order_duplicates_and_unsafe_flags_are_rejected() -> None:
    observations = tuple(_observation(index, offset=index * 3) for index in range(4))
    with pytest.raises(OKXPriceLinkageProbeError, match="Source set or order"):
        build_pilot_evidence(tuple(reversed(observations)))


def test_clock_order_is_fail_closed() -> None:
    contract = SOURCE_CONTRACTS[0]
    url, response = _response(0)
    with pytest.raises(ValueError, match="request <= response"):
        validate_source_response(
            contract=contract,
            response=response,
            request_url=url,
            request_started_at=BASE + timedelta(seconds=2),
            response_received_at=BASE + timedelta(seconds=1),
        )
