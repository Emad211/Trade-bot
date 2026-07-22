from __future__ import annotations

import csv
import hashlib
import io
from dataclasses import replace
from decimal import Decimal

import pytest

from hybrid_trader.replication.cboe_vx_public import (
    CONTRACT_SPECS,
    EXPECTED_HEADER,
    PILOT_VERSION,
    ParsedContract,
    build_manifest,
    derive_pilot_rows,
    parse_contract_bytes,
    render_pilot_csv,
)


def _raw(identity: str, expiry: str, *, duplicate: bool = False, bad_change: bool = False) -> bytes:
    rows = [
        [
            "2022-09-15",
            identity,
            "20.0000",
            "21.0000",
            "19.0000",
            "20.5000",
            "20.6",
            "0",
            "100",
            "0",
            "200",
        ],
        [
            "2022-09-16",
            identity,
            "20.5000",
            "22.0000",
            "20.0000",
            "21.0000",
            "21.2",
            "0.5" if bad_change else "0.6",
            "110",
            "1",
            "210",
        ],
        [
            expiry,
            identity,
            "21.0000",
            "22.5000",
            "20.5000",
            "21.5000",
            "21.7",
            "0.5",
            "120",
            "0",
            "220",
        ],
    ]
    if duplicate:
        rows.insert(2, list(rows[1]))
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(EXPECTED_HEADER)
    writer.writerows(rows)
    return stream.getvalue().encode()


def _contract(
    index: int = 0,
    *,
    duplicate: bool = False,
    bad_change: bool = False,
) -> ParsedContract:
    base = CONTRACT_SPECS[index]
    raw = _raw(
        base.expected_identity,
        base.expiry,
        duplicate=duplicate,
        bad_change=bad_change,
    )
    spec = replace(
        base,
        expected_sha256=hashlib.sha256(raw).hexdigest(),
        expected_byte_count=len(raw),
    )
    return parse_contract_bytes(raw, spec)


def test_parses_exact_contract_and_preserves_settlement() -> None:
    parsed = _contract()
    assert parsed.last_trade_date == CONTRACT_SPECS[0].expiry
    assert parsed.settlement_close_difference_count == 3
    assert Decimal(parsed.rows[1]["Settle"]) == Decimal("21.2")
    assert Decimal(parsed.rows[1]["Close"]) == Decimal("21.0000")


def test_changed_hash_is_rejected() -> None:
    spec = replace(CONTRACT_SPECS[0], expected_byte_count=3, expected_sha256="0" * 64)
    with pytest.raises(ValueError, match="SHA-256 changed"):
        parse_contract_bytes(b"abc", spec)


def test_duplicate_dates_are_rejected() -> None:
    base = CONTRACT_SPECS[0]
    raw = _raw(base.expected_identity, base.expiry, duplicate=True)
    spec = replace(
        base,
        expected_sha256=hashlib.sha256(raw).hexdigest(),
        expected_byte_count=len(raw),
    )
    with pytest.raises(ValueError, match="Duplicate Cboe trade dates"):
        parse_contract_bytes(raw, spec)


def test_settlement_change_mismatch_is_rejected() -> None:
    base = CONTRACT_SPECS[0]
    raw = _raw(base.expected_identity, base.expiry, bad_change=True)
    spec = replace(
        base,
        expected_sha256=hashlib.sha256(raw).hexdigest(),
        expected_byte_count=len(raw),
    )
    with pytest.raises(ValueError, match="Settlement change mismatch"):
        parse_contract_bytes(raw, spec)


def test_pilot_is_contract_level_and_deterministic() -> None:
    contracts = [_contract(0), _contract(1)]
    rows = derive_pilot_rows(contracts)
    assert all(row["pilot_version"] == PILOT_VERSION for row in rows)
    assert all(row["continuous_series"] == "false" for row in rows)
    assert all(row["back_adjusted"] == "false" for row in rows)
    assert all(row["returns_authorized"] == "false" for row in rows)
    assert render_pilot_csv(rows) == render_pilot_csv(rows)


def test_manifest_keeps_license_and_return_gates_closed() -> None:
    contracts = [_contract(0), _contract(1)]
    rows = derive_pilot_rows(contracts)
    manifest = build_manifest(contracts, rows, render_pilot_csv(rows))
    assert manifest["license_state"]["raw_redistribution_authorized"] is False
    assert manifest["license_state"]["public_redisplay_authorized"] is False
    assert manifest["returns_computed"] is False
    assert manifest["economic_edge_verdict"] == "INCONCLUSIVE"


def test_wrong_contract_identity_is_rejected() -> None:
    base = CONTRACT_SPECS[0]
    raw = _raw("V (Oct 2022)", base.expiry)
    spec = replace(
        base,
        expected_sha256=hashlib.sha256(raw).hexdigest(),
        expected_byte_count=len(raw),
    )
    with pytest.raises(ValueError, match="Unexpected Cboe futures identity"):
        parse_contract_bytes(raw, spec)


def test_html_response_is_rejected() -> None:
    raw = b"<html><body>not csv</body></html>"
    spec = replace(
        CONTRACT_SPECS[0],
        expected_sha256=hashlib.sha256(raw).hexdigest(),
        expected_byte_count=len(raw),
    )
    with pytest.raises(ValueError, match="returned HTML"):
        parse_contract_bytes(raw, spec)
