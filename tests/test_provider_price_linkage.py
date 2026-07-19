from __future__ import annotations

import base64
import csv
import gzip
import io
from pathlib import Path

import pytest

from hybrid_trader.replication.provider_price_linkage import (
    EXPECTED_REGISTRY_SHA256,
    PILOT_ROOTS,
    authenticated_probe_request,
    build_provider_candidate_rows,
    load_verified_registry_b64,
    provider_plan_profile,
    render_candidate_csv,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = (
    ROOT
    / "docs/research/edge-discovery/02-replication/"
    "02-03-cftc-tff-2022-instrument-registry.csv.gz.b64"
)


def _rows() -> list[dict[str, str]]:
    return build_provider_candidate_rows(load_verified_registry_b64(REGISTRY))


def test_candidate_coverage_is_exact_and_fail_closed() -> None:
    rows = _rows()
    profile = provider_plan_profile(rows)
    assert profile.row_count == 54
    assert profile.ordinary_candidate_rows == 47
    assert profile.glbx_candidate_rows == 43
    assert profile.ifus_candidate_rows == 3
    assert profile.xcbf_candidate_rows == 1
    assert profile.aggregate_rows == 3
    assert profile.later_delisted_rows == 2
    assert profile.nonstandard_rows == 1
    assert profile.technical_symbol_pending_rows == 1
    assert profile.price_linkage_authorized_rows == 0
    assert profile.provider_contract_id_rows == 0
    assert profile.purchase_authorized is False
    assert profile.authenticated_probe_executed is False


def test_aggregates_have_no_provider_or_parent_symbol() -> None:
    aggregates = [
        row
        for row in _rows()
        if row["mapping_class"] == "NON_TRADABLE_CONSOLIDATED_AGGREGATE"
    ]
    assert {row["cftc_contract_market_code"] for row in aggregates} == {
        "12460+",
        "13874+",
        "20974+",
    }
    assert all(not row["provider_candidate"] for row in aggregates)
    assert all(not row["dataset_id_candidate"] for row in aggregates)
    assert all(not row["parent_symbol_candidate"] for row in aggregates)


def test_dataset_assignment_matches_exchange_coverage() -> None:
    rows = _rows()
    datasets = {row["exchange_product_code"]: row["dataset_id_candidate"] for row in rows}
    assert datasets["ZN"] == "GLBX.MDP3"
    assert datasets["ES"] == "GLBX.MDP3"
    assert datasets["NIY"] == "GLBX.MDP3"
    assert datasets["DX"] == "IFUS.IMPACT"
    assert datasets["VX"] == "XCBF.PITCH"


def test_special_cases_remain_blocked() -> None:
    rows = {row["cftc_contract_market_code"]: row for row in _rows()}
    assert "EXPIRED_HISTORY" in rows["132741"]["candidate_status"]
    assert "2022_VINTAGE" in rows["157741"]["candidate_status"]
    assert "NONSTANDARD_EXECUTION" in rows["13874W"]["candidate_status"]
    assert "TECHNICAL_SYMBOL" in rows["04360Y"]["candidate_status"]
    assert all(row["price_linkage_authorized"] == "false" for row in rows.values())
    assert all(row["returns_authorized"] == "false" for row in rows.values())


def test_authenticated_probe_is_representative_and_non_purchasing() -> None:
    probe = authenticated_probe_request(_rows())
    assert tuple(item["root"] for item in probe["probes"]) == PILOT_ROOTS
    assert {item["dataset"] for item in probe["probes"]} == {
        "GLBX.MDP3",
        "IFUS.IMPACT",
        "XCBF.PITCH",
    }
    assert probe["max_cost_usd"] == 0.0
    assert probe["purchase_authorized"] is False
    assert probe["price_linkage_authorized"] is False
    assert probe["settlement_contract"]["allow_ohlcv_as_settlement_substitute"] is False


def test_candidate_csv_is_deterministic() -> None:
    first = render_candidate_csv(_rows())
    second = render_candidate_csv(_rows())
    assert first == second
    parsed = list(csv.DictReader(io.StringIO(first.decode("utf-8"))))
    assert [row["cftc_contract_market_code"] for row in parsed] == sorted(
        row["cftc_contract_market_code"] for row in parsed
    )


def test_changed_registry_is_rejected(tmp_path: Path) -> None:
    encoded = REGISTRY.read_text(encoding="ascii").strip()
    raw = gzip.decompress(base64.b64decode(encoded))
    assert __import__("hashlib").sha256(raw).hexdigest() == EXPECTED_REGISTRY_SHA256
    changed = raw + b"\n"
    path = tmp_path / "changed.b64"
    path.write_text(
        base64.b64encode(gzip.compress(changed, mtime=0)).decode(),
        encoding="ascii",
    )
    with pytest.raises(ValueError, match="SHA-256 changed"):
        load_verified_registry_b64(path)
