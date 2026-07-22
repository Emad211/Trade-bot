from __future__ import annotations

import base64
import csv
import gzip
import io
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from hybrid_trader.replication import databento_metadata_probe as probe


class FakeMetadata:
    def __init__(
        self, *, missing_dataset: str | None = None, fail_secret: str | None = None
    ) -> None:
        self.missing_dataset = missing_dataset
        self.fail_secret = fail_secret
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def list_datasets(
        self, *, start_date: str | None = None, end_date: str | None = None
    ) -> list[str]:
        self.calls.append(("list_datasets", {"start_date": start_date, "end_date": end_date}))
        if self.fail_secret:
            raise RuntimeError(f"authentication failed for {self.fail_secret}")
        return [dataset for dataset in probe.DATASETS if dataset != self.missing_dataset]

    def list_schemas(self, *, dataset: str) -> list[str]:
        self.calls.append(("list_schemas", {"dataset": dataset}))
        return ["trades", "definition", "statistics"]

    def list_fields(self, *, schema: str, encoding: str) -> list[dict[str, str]]:
        self.calls.append(("list_fields", {"schema": schema, "encoding": encoding}))
        if schema == "definition":
            return [
                {"name": "instrument_id", "type": "uint32_t"},
                {"name": "raw_symbol", "type": "char[71]"},
                {"name": "expiration", "type": "uint64_t"},
            ]
        return [
            {"name": "instrument_id", "type": "uint32_t"},
            {"name": "stat_type", "type": "uint16_t"},
            {"name": "stat_flags", "type": "uint8_t"},
        ]

    def list_unit_prices(self, *, dataset: str) -> list[dict[str, Any]]:
        self.calls.append(("list_unit_prices", {"dataset": dataset}))
        return [{"mode": "historical-streaming", "unit_prices": {"definition": 1.0}}]

    def get_dataset_range(self, *, dataset: str) -> dict[str, Any]:
        self.calls.append(("get_dataset_range", {"dataset": dataset}))
        return {
            "start": "2010-01-01T00:00:00Z",
            "end": "2026-01-01T00:00:00Z",
            "schema": {
                "definition": {
                    "start": "2010-01-01T00:00:00Z",
                    "end": "2026-01-01T00:00:00Z",
                },
                "statistics": {
                    "start": "2010-01-01T00:00:00Z",
                    "end": "2026-01-01T00:00:00Z",
                },
            },
        }

    def get_dataset_condition(
        self,
        *,
        dataset: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, Any]]:
        self.calls.append(
            (
                "get_dataset_condition",
                {"dataset": dataset, "start_date": start_date, "end_date": end_date},
            )
        )
        return [
            {"date": "2022-09-01", "condition": "available", "last_modified_date": "2024-01-01"},
            {"date": "2022-09-02", "condition": "available", "last_modified_date": "2024-01-01"},
            {"date": "2022-09-03", "condition": "missing", "last_modified_date": None},
            {"date": "2022-09-04", "condition": "missing", "last_modified_date": None},
            {"date": "2022-09-05", "condition": "available", "last_modified_date": "2024-01-01"},
        ]

    def get_cost(
        self,
        *,
        dataset: str,
        start: str,
        end: str | None = None,
        symbols: list[str] | str | None = None,
        schema: str = "trades",
        stype_in: str = "raw_symbol",
        limit: int | None = None,
    ) -> float:
        self.calls.append(
            (
                "get_cost",
                {
                    "dataset": dataset,
                    "start": start,
                    "end": end,
                    "symbols": symbols,
                    "schema": schema,
                    "stype_in": stype_in,
                    "limit": limit,
                },
            )
        )
        return 0.125 if schema == "definition" else 0.05


class FakeSymbology:
    def __init__(self, *, partial_parent: str | None = None) -> None:
        self.partial_parent = partial_parent
        self.calls: list[dict[str, Any]] = []

    def resolve(
        self,
        *,
        dataset: str,
        symbols: list[str] | str,
        stype_in: str,
        stype_out: str,
        start_date: str,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        parent = symbols[0] if isinstance(symbols, list) else symbols
        self.calls.append(
            {
                "dataset": dataset,
                "symbols": symbols,
                "stype_in": stype_in,
                "stype_out": stype_out,
                "start_date": start_date,
                "end_date": end_date,
            }
        )
        partial = [parent] if parent == self.partial_parent else []
        return {
            "result": {parent: [{"d0": start_date, "d1": end_date, "s": "123"}]},
            "symbols": [parent],
            "stype_in": stype_in,
            "stype_out": stype_out,
            "start_date": start_date,
            "end_date": end_date,
            "partial": partial,
            "not_found": [],
            "message": "Partially resolved" if partial else "OK",
            "status": 1 if partial else 0,
        }


class FakeClient:
    def __init__(
        self,
        *,
        missing_dataset: str | None = None,
        partial_parent: str | None = None,
        fail_secret: str | None = None,
    ) -> None:
        self.metadata = FakeMetadata(missing_dataset=missing_dataset, fail_secret=fail_secret)
        self.symbology = FakeSymbology(partial_parent=partial_parent)


@pytest.fixture
def plan_rows() -> list[dict[str, str]]:
    roots = {
        "ZN": ("043602", "GLBX.MDP3", "ZN.FUT"),
        "ES": ("13874A", "GLBX.MDP3", "ES.FUT"),
        "NIY": ("240743", "GLBX.MDP3", "NIY.FUT"),
        "DX": ("098662", "IFUS.IMPACT", "DX.FUT"),
        "VX": ("1170E1", "XCBF.PITCH", "VX.FUT"),
    }
    rows: list[dict[str, str]] = []
    for index in range(probe.PLAN_ROWS):
        root = f"R{index:02d}"
        code = f"{index:06d}"
        dataset = "GLBX.MDP3"
        parent = f"{root}.FUT"
        if index < len(roots):
            root, (code, dataset, parent) = list(roots.items())[index]
        rows.append(
            {
                "plan_version": probe.PLAN_VERSION,
                "cftc_contract_market_code": code,
                "exchange_product_code": root,
                "dataset_id_candidate": dataset,
                "parent_symbol_candidate": parent,
            }
        )
    return sorted(rows, key=lambda row: row["cftc_contract_market_code"])


def test_probe_request_has_exact_representative_roots(plan_rows: list[dict[str, str]]) -> None:
    request = probe.build_request(plan_rows)
    assert [item["root"] for item in request["probes"]] == list(probe.ROOTS)
    assert request["metadata_only"] is True
    assert request["purchase_authorized"] is False
    assert request["max_authorized_cost_usd"] == 0.0


def test_successful_fake_probe_remains_fail_closed(plan_rows: list[dict[str, str]]) -> None:
    request = probe.build_request(plan_rows)
    client = FakeClient()
    evidence = probe.run_probe(
        client,
        request,
        key="db-secret-value-that-must-not-leak",
        version=probe.CLIENT_VERSION,
        at=datetime(2026, 7, 19, tzinfo=UTC),
    )
    assert evidence["profile"]["authenticated"] is True
    assert evidence["profile"]["metadata_gate_passed_count"] == 5
    assert evidence["metadata_gate_all_representative_roots_passed"] is True
    assert evidence["next_gate"] == "EXPLICIT_MINIMAL_DEFINITION_AND_SETTLEMENT_COST_APPROVAL"
    assert evidence["provider_accepted"] is False
    assert evidence["purchase_authorized"] is False
    assert evidence["global_price_linkage_authorized"] is False
    assert evidence["returns_authorized"] is False
    assert evidence["definition_records_acquired"] is False
    assert evidence["settlement_records_acquired"] is False
    assert all(item["definition_cost_usd"] == 0.125 for item in evidence["representative_probes"])
    assert all(item["statistics_cost_usd"] == 0.05 for item in evidence["representative_probes"])
    assert not hasattr(client, "timeseries")


def test_partial_resolution_fails_that_probe_gate(plan_rows: list[dict[str, str]]) -> None:
    request = probe.build_request(plan_rows)
    evidence = probe.run_probe(
        FakeClient(partial_parent="VX.FUT"),
        request,
        key="db-safe-test-key",
        version=probe.CLIENT_VERSION,
        at=datetime(2026, 7, 19, tzinfo=UTC),
    )
    by_root = {item["root"]: item for item in evidence["representative_probes"]}
    assert by_root["VX"]["parent_resolution_passed"] is False
    assert by_root["VX"]["metadata_gate_passed"] is False
    assert evidence["next_gate"] == "REJECT_OR_REMEDIATE_PROVIDER_CANDIDATE"


def test_missing_dataset_is_recorded_not_inferred(plan_rows: list[dict[str, str]]) -> None:
    request = probe.build_request(plan_rows)
    evidence = probe.run_probe(
        FakeClient(missing_dataset="IFUS.IMPACT"),
        request,
        key="db-safe-test-key",
        version=probe.CLIENT_VERSION,
        at=datetime(2026, 7, 19, tzinfo=UTC),
    )
    assert evidence["datasets"]["IFUS.IMPACT"]["entitled"] is False
    by_root = {item["root"]: item for item in evidence["representative_probes"]}
    assert by_root["DX"]["dataset_entitled"] is False
    assert by_root["DX"]["metadata_gate_passed"] is False


def test_authentication_failure_redacts_secret(plan_rows: list[dict[str, str]]) -> None:
    secret = "db-super-secret-api-key"
    request = probe.build_request(plan_rows)
    evidence = probe.run_probe(
        FakeClient(fail_secret=secret),
        request,
        key=secret,
        version=probe.CLIENT_VERSION,
        at=datetime(2026, 7, 19, tzinfo=UTC),
    )
    serialized = json.dumps(evidence, sort_keys=True)
    assert secret not in serialized
    assert "[REDACTED]" in serialized
    assert evidence["profile"]["execution_status"] == "AUTHENTICATION_OR_LIST_DATASETS_FAILURE"


def test_blocked_missing_secret_bundle_is_valid(
    tmp_path: Path, plan_rows: list[dict[str, str]]
) -> None:
    request = probe.build_request(plan_rows)
    evidence = probe.blocked(
        request,
        datetime(2026, 7, 19, tzinfo=UTC),
        "BLOCKED_MISSING_DATABENTO_API_KEY",
    )
    manifest = probe.write_bundle(tmp_path, request, evidence)
    assert manifest["purchase_authorized"] is False
    assert manifest["time_series_download_executed"] is False
    assert manifest["price_linkage_authorized_rows"] == 0
    for filename, identity in manifest["files"].items():
        content = (tmp_path / filename).read_bytes()
        assert len(content) == identity["byte_count"]
        assert probe.sha(content) == identity["sha256"]


def test_candidate_plan_loader_checks_hash_and_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rows = [
        {
            "plan_version": "TEST_PLAN",
            "cftc_contract_market_code": f"{index:03d}",
        }
        for index in range(3)
    ]
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    raw = output.getvalue().encode()
    path = tmp_path / "plan.csv.gz.b64"
    path.write_text(base64.b64encode(gzip.compress(raw, mtime=0)).decode(), encoding="ascii")
    monkeypatch.setattr(probe, "PLAN_SHA", probe.sha(raw))
    monkeypatch.setattr(probe, "PLAN_ROWS", 3)
    monkeypatch.setattr(probe, "PLAN_VERSION", "TEST_PLAN")
    assert probe.load_plan(path) == rows
