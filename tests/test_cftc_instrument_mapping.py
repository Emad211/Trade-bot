from __future__ import annotations

import base64
import csv
import gzip
import io
import json
import tempfile
from pathlib import Path

import pytest

from hybrid_trader.replication.cftc_instrument_mapping import (
    EXPECTED_ROWS,
    build_registry_rows,
    load_mapping_contract,
    load_source_registry,
    load_verified_pilot,
    render_registry_csv,
)

ROOT = Path(__file__).resolve().parents[1]
MAP_CONTRACT_B64 = (
    ROOT
    / "docs/research/edge-discovery/02-replication/02-03-cftc-tff-2022-instrument-map-contract.csv.gz.b64"
)
SOURCE_REGISTRY = (
    ROOT
    / "docs/research/edge-discovery/02-replication/02-03-cftc-tff-instrument-mapping-sources.json"
)


def _mapping_contract_path() -> Path:
    destination = Path(tempfile.gettempdir()) / "cftc-instrument-map-contract.csv"
    destination.write_bytes(gzip.decompress(base64.b64decode(MAP_CONTRACT_B64.read_text().strip())))
    return destination


def _synthetic_pilot_rows(mapping_by_code: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "CFTC_Contract_Market_Code": code,
            "Market_and_Exchange_Names": f"{row['expected_name_contains']} - TEST EXCHANGE",
            "CFTC_Market_Code": "TST",
            "CFTC_Region_Code": "00",
            "CFTC_Commodity_Code": code[:3],
            "Contract_Units": "TEST CONTRACT UNITS",
        }
        for code, row in sorted(mapping_by_code.items())
    ]


def _rows() -> list[dict[str, str]]:
    mapping = load_mapping_contract(_mapping_contract_path())
    sources = load_source_registry(SOURCE_REGISTRY)
    return build_registry_rows(_synthetic_pilot_rows(mapping), mapping, sources)


def test_complete_mapping_coverage() -> None:
    rows = _rows()
    assert len(rows) == EXPECTED_ROWS == 54
    assert len({row["cftc_contract_market_code"] for row in rows}) == 54


def test_aggregates_never_receive_price_roots() -> None:
    aggregates = [row for row in _rows() if row["cftc_contract_market_code"].endswith("+")]
    assert {row["cftc_contract_market_code"] for row in aggregates} == {
        "12460+",
        "13874+",
        "20974+",
    }
    assert all(row["mapping_class"] == "NON_TRADABLE_CONSOLIDATED_AGGREGATE" for row in aggregates)
    assert all(not row["exchange_product_code"] for row in aggregates)


def test_special_historical_and_nonstandard_products_are_gated() -> None:
    rows = {row["cftc_contract_market_code"]: row for row in _rows()}
    assert rows["132741"]["exchange_product_code"] == "GE"
    assert "LATER_DELISTED" in rows["132741"]["mapping_class"]
    assert rows["157741"]["exchange_product_code"] == "BSB"
    assert rows["157741"]["exchange_order_entry_symbol"] == "BW"
    assert rows["13874W"]["exchange_product_code"] == "ASR"
    assert rows["13874W"]["exchange_security_group"] == "0B"
    assert rows["240743"]["exchange_product_code"] == "NIY"
    assert rows["04360Y"]["mapping_class"] == "PRODUCT_IDENTITY_VERIFIED_TECHNICAL_SYMBOL_PENDING"


def test_no_row_authorizes_price_linkage_or_returns() -> None:
    rows = _rows()
    assert all(row["price_linkage_authorized"] == "false" for row in rows)
    assert all(not row["provider_contract_id"] for row in rows)
    assert all(row["source_ids"] for row in rows)


def test_registry_csv_is_deterministic() -> None:
    first = render_registry_csv(_rows())
    second = render_registry_csv(_rows())
    assert first == second
    parsed = list(csv.DictReader(io.StringIO(first.decode("utf-8"))))
    assert [row["cftc_contract_market_code"] for row in parsed] == sorted(
        row["cftc_contract_market_code"] for row in parsed
    )


def test_changed_contract_or_source_registry_is_rejected(tmp_path: Path) -> None:
    changed_contract = tmp_path / "contract.csv"
    changed_contract.write_bytes(_mapping_contract_path().read_bytes() + b"\n")
    with pytest.raises(ValueError, match="SHA-256 changed"):
        load_mapping_contract(changed_contract)
    decoded = json.loads(SOURCE_REGISTRY.read_text(encoding="utf-8"))
    decoded["EXTRA"] = {"authority": "x", "url": "x", "role": "x"}
    changed_sources = tmp_path / "sources.json"
    changed_sources.write_text(json.dumps(decoded), encoding="utf-8")
    with pytest.raises(ValueError, match="Source-registry SHA-256 changed"):
        load_source_registry(changed_sources)


def test_wrong_pilot_hash_is_rejected(tmp_path: Path) -> None:
    changed = tmp_path / "changed.csv"
    changed.write_text("not,the,official,pilot\n", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256 changed"):
        load_verified_pilot(changed)
