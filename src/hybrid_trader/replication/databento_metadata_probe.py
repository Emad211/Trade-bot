"""Fail-closed, authenticated, zero-purchase Databento metadata probe."""

from __future__ import annotations

import argparse
import base64
import csv
import gzip
import hashlib
import importlib
import importlib.metadata
import io
import json
import os
import platform
import tempfile
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, date, datetime
from functools import partial
from pathlib import Path
from typing import Any, cast

PLAN_SHA = "cd2430c7fdd0b3a68a1093925d755c242081372fbe41668cc53436893c274062"
PLAN_VERSION = "CFTC_TFF_2022_09_13_DATABENTO_CANDIDATE_PLAN_V1"
PLAN_ROWS = 54
PROBE_ID = "DATABENTO_CFTC_TFF_2022_09_13_ZERO_PURCHASE_METADATA_PROBE_V1"
CLIENT_VERSION = "0.81.0"
API_KEY_ENV = "DATABENTO_API_KEY"
DATASETS = ("GLBX.MDP3", "IFUS.IMPACT", "XCBF.PITCH")
SCHEMAS = ("definition", "statistics")
ROOTS = ("ZN", "ES", "NIY", "DX", "VX")
START, END = "2022-09-01", "2022-10-01"
STAT_START, STAT_END = "2022-09-16", "2022-09-17"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [jsonable(v) for v in value]
    item = getattr(value, "item", None)
    if callable(item):
        try:
            return jsonable(item())
        except (TypeError, ValueError):
            pass
    to_dict = getattr(value, "to_dict", None)
    return jsonable(to_dict()) if callable(to_dict) else str(value)


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        tmp.replace(path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def load_plan(path: str | Path) -> list[dict[str, str]]:
    encoded = Path(path).read_text(encoding="ascii").strip()
    try:
        raw = gzip.decompress(base64.b64decode(encoded, validate=True))
    except (ValueError, OSError) as exc:
        raise ValueError("Candidate plan is not valid gzip-compressed Base64") from exc
    if sha(raw) != PLAN_SHA:
        raise ValueError(f"Candidate-plan SHA-256 changed: {sha(raw)}")
    rows = list(csv.DictReader(io.StringIO(raw.decode(), newline="")))
    codes = [row["cftc_contract_market_code"] for row in rows]
    if len(rows) != PLAN_ROWS or {row["plan_version"] for row in rows} != {PLAN_VERSION}:
        raise ValueError("Unexpected candidate-plan row count or version")
    if codes != sorted(codes) or len(codes) != len(set(codes)):
        raise ValueError("Candidate plan has duplicate or nondeterministic CFTC codes")
    return rows


def build_request(rows: Sequence[Mapping[str, str]]) -> dict[str, Any]:
    by_root = {row["exchange_product_code"]: row for row in rows}
    if missing := [root for root in ROOTS if root not in by_root]:
        raise ValueError(f"Representative roots missing: {missing}")
    probes = []
    for root in ROOTS:
        row = by_root[root]
        probes.append(
            {
                "cftc_contract_market_code": row["cftc_contract_market_code"],
                "root": root,
                "dataset": row["dataset_id_candidate"],
                "parent_symbol": row["parent_symbol_candidate"],
                "definition_start": START,
                "definition_end": END,
                "statistics_start": STAT_START,
                "statistics_end": STAT_END,
            }
        )
    return {
        "schema_version": "1.0",
        "probe_id": PROBE_ID,
        "provider": "DATABENTO",
        "candidate_plan_sha256": PLAN_SHA,
        "client_version_required": CLIENT_VERSION,
        "authentication_secret_name": API_KEY_ENV,
        "datasets": list(DATASETS),
        "required_schemas": list(SCHEMAS),
        "metadata_only": True,
        "time_series_download_authorized": False,
        "batch_download_authorized": False,
        "purchase_authorized": False,
        "max_authorized_cost_usd": 0.0,
        "probes": probes,
    }


def operation(name: str, request: dict[str, Any], call: Callable[[], Any], secret: str) -> dict[str, Any]:
    request = cast(dict[str, Any], jsonable(request))
    try:
        response = jsonable(call())
        return {
            "operation": name,
            "request": request,
            "request_sha256": sha(canonical(request)),
            "response": response,
            "response_sha256": sha(canonical(response)),
            "success": True,
            "error_type": None,
            "error_message": None,
        }
    except Exception as exc:
        return {
            "operation": name,
            "request": request,
            "request_sha256": sha(canonical(request)),
            "response": None,
            "response_sha256": None,
            "success": False,
            "error_type": type(exc).__name__,
            "error_message": str(exc).replace(secret, "[REDACTED]"),
        }


def parse_ts(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return (result if result.tzinfo else result.replace(tzinfo=UTC)).astimezone(UTC)


def range_pass(response: Any) -> bool:
    if not isinstance(response, Mapping) or not isinstance(response.get("schema"), Mapping):
        return False
    for schema in SCHEMAS:
        item = response["schema"].get(schema)
        if not isinstance(item, Mapping):
            return False
        start, end = item.get("start"), item.get("end")
        if not isinstance(start, str) or not isinstance(end, str):
            return False
        if parse_ts(start) > parse_ts(f"{START}T00:00:00Z") or parse_ts(end) < parse_ts(
            f"{END}T00:00:00Z"
        ):
            return False
    return True


def condition_pass(response: Any) -> tuple[bool, dict[str, int]]:
    if not isinstance(response, list):
        return False, {}
    counts: dict[str, int] = {}
    ok = bool(response)
    for item in response:
        if not isinstance(item, Mapping):
            ok = False
            continue
        condition, day = str(item.get("condition", "unknown")), str(item.get("date", ""))
        counts[condition] = counts.get(condition, 0) + 1
        if condition == "available":
            continue
        try:
            if condition == "missing" and date.fromisoformat(day).weekday() >= 5:
                continue
        except ValueError:
            pass
        ok = False
    return ok, dict(sorted(counts.items()))


def resolution_pass(response: Any, parent: str) -> tuple[bool, int]:
    if not isinstance(response, Mapping) or not isinstance(response.get("result"), Mapping):
        return False, 0
    mappings = response["result"].get(parent)
    count = len(mappings) if isinstance(mappings, list) else 0
    return (
        response.get("status") == 0
        and response.get("partial") == []
        and response.get("not_found") == []
        and count > 0,
        count,
    )


def cost_value(op: Mapping[str, Any]) -> float | None:
    if not op.get("success") or op.get("response") is None:
        return None
    try:
        return float(op["response"])
    except (TypeError, ValueError):
        return None


def blocked(request: Mapping[str, Any], requested_at: datetime, status: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "profile": {
            "probe_id": PROBE_ID,
            "provider": "DATABENTO",
            "execution_status": status,
            "authenticated": False,
            "candidate_plan_sha256": PLAN_SHA,
            "candidate_plan_rows": PLAN_ROWS,
            "required_dataset_count": len(DATASETS),
            "entitled_dataset_count": 0,
            "representative_probe_count": len(ROOTS),
            "metadata_gate_passed_count": 0,
            "provider_contract_id_count": 0,
            "price_linkage_authorized_rows": 0,
            "purchase_authorized": False,
            "max_authorized_cost_usd": 0.0,
            "time_series_download_executed": False,
            "batch_download_submitted": False,
        },
        "requested_at": requested_at.astimezone(UTC).isoformat(),
        "request": jsonable(request),
        "client": None,
        "operations": [],
        "datasets": {},
        "representative_probes": [],
        "provider_accepted": False,
        "authenticated_metadata_probe_executed": False,
        "cost_quote_acquired": False,
        "license_snapshot_acquired": False,
        "definition_records_acquired": False,
        "settlement_records_acquired": False,
        "purchase_authorized": False,
        "global_price_linkage_authorized": False,
        "returns_authorized": False,
        "paper_replication_pass": False,
        "economic_edge_verdict": "INCONCLUSIVE",
    }


def run_probe(client: Any, request: Mapping[str, Any], key: str, version: str, at: datetime) -> dict[str, Any]:
    ops: list[dict[str, Any]] = []
    list_op = operation(
        "metadata.list_datasets",
        {"start_date": START, "end_date": END},
        partial(client.metadata.list_datasets, start_date=START, end_date=END),
        key,
    )
    ops.append(list_op)
    if not list_op["success"] or not isinstance(list_op["response"], list):
        evidence = blocked(request, at, "AUTHENTICATION_OR_LIST_DATASETS_FAILURE")
        evidence["client"] = {"package": "databento", "version": version, "python": platform.python_version()}
        evidence["operations"] = ops
        return evidence
    entitled = {str(item) for item in list_op["response"]}
    fields: dict[str, dict[str, Any]] = {}
    for schema in SCHEMAS:
        fields[schema] = operation(
            f"metadata.list_fields:{schema}",
            {"schema": schema, "encoding": "json"},
            partial(client.metadata.list_fields, schema=schema, encoding="json"),
            key,
        )
        ops.append(fields[schema])

    dataset_results: dict[str, Any] = {}
    for dataset in DATASETS:
        if dataset not in entitled:
            dataset_results[dataset] = {"entitled": False, "operations": []}
            continue
        dataset_ops = [
            operation(
                f"metadata.list_schemas:{dataset}",
                {"dataset": dataset},
                partial(client.metadata.list_schemas, dataset=dataset),
                key,
            ),
            operation(
                f"metadata.get_dataset_range:{dataset}",
                {"dataset": dataset},
                partial(client.metadata.get_dataset_range, dataset=dataset),
                key,
            ),
            operation(
                f"metadata.get_dataset_condition:{dataset}",
                {"dataset": dataset, "start_date": START, "end_date": END},
                partial(
                    client.metadata.get_dataset_condition,
                    dataset=dataset,
                    start_date=START,
                    end_date=END,
                ),
                key,
            ),
            operation(
                f"metadata.list_unit_prices:{dataset}",
                {"dataset": dataset},
                partial(client.metadata.list_unit_prices, dataset=dataset),
                key,
            ),
        ]
        ops.extend(dataset_ops)
        schemas = set(dataset_ops[0]["response"]) if dataset_ops[0]["success"] else set()
        condition_ok, condition_counts = condition_pass(dataset_ops[2]["response"])
        dataset_results[dataset] = {
            "entitled": True,
            "required_schemas_available": set(SCHEMAS).issubset(schemas),
            "range_covers_probe": dataset_ops[1]["success"] and range_pass(dataset_ops[1]["response"]),
            "condition_gate_passed": dataset_ops[2]["success"] and condition_ok,
            "condition_counts": condition_counts,
            "definition_fields_available": fields["definition"]["success"],
            "statistics_fields_available": fields["statistics"]["success"],
            "unit_prices_acquired": dataset_ops[3]["success"],
            "operations": dataset_ops,
        }

    probe_results: list[dict[str, Any]] = []
    for item in cast(Sequence[Mapping[str, str]], request["probes"]):
        dataset, parent = item["dataset"], item["parent_symbol"]
        if dataset not in entitled:
            probe_results.append(
                {
                    **dict(item),
                    "dataset_entitled": False,
                    "parent_resolution_passed": False,
                    "resolved_mapping_count": 0,
                    "definition_cost_usd": None,
                    "statistics_cost_usd": None,
                    "metadata_gate_passed": False,
                    "operations": [],
                }
            )
            continue
        resolve = operation(
            f"symbology.resolve:{parent}",
            {
                "dataset": dataset,
                "symbols": [parent],
                "stype_in": "parent",
                "stype_out": "instrument_id",
                "start_date": START,
                "end_date": END,
            },
            partial(
                client.symbology.resolve,
                dataset=dataset,
                symbols=[parent],
                stype_in="parent",
                stype_out="instrument_id",
                start_date=START,
                end_date=END,
            ),
            key,
        )
        def_cost = operation(
            f"metadata.get_cost:definition:{parent}",
            {"dataset": dataset, "symbols": [parent], "schema": "definition", "stype_in": "parent", "start": START, "end": END},
            partial(client.metadata.get_cost, dataset=dataset, symbols=[parent], schema="definition", stype_in="parent", start=START, end=END),
            key,
        )
        stat_cost = operation(
            f"metadata.get_cost:statistics:{parent}",
            {"dataset": dataset, "symbols": [parent], "schema": "statistics", "stype_in": "parent", "start": STAT_START, "end": STAT_END},
            partial(client.metadata.get_cost, dataset=dataset, symbols=[parent], schema="statistics", stype_in="parent", start=STAT_START, end=STAT_END),
            key,
        )
        probe_ops = [resolve, def_cost, stat_cost]
        ops.extend(probe_ops)
        resolved, count = resolution_pass(resolve["response"], parent)
        definition_cost, statistics_cost = cost_value(def_cost), cost_value(stat_cost)
        gate = dataset_results.get(dataset, {})
        passed = bool(
            gate.get("entitled")
            and gate.get("required_schemas_available")
            and gate.get("range_covers_probe")
            and gate.get("condition_gate_passed")
            and resolved
            and definition_cost is not None
            and statistics_cost is not None
        )
        probe_results.append(
            {
                **dict(item),
                "dataset_entitled": True,
                "parent_resolution_passed": resolved,
                "resolved_mapping_count": count,
                "definition_cost_usd": definition_cost,
                "statistics_cost_usd": statistics_cost,
                "metadata_gate_passed": passed,
                "operations": probe_ops,
            }
        )

    passed_count = sum(bool(item["metadata_gate_passed"]) for item in probe_results)
    all_passed = passed_count == len(ROOTS)
    return {
        "schema_version": "1.0",
        "profile": {
            "probe_id": PROBE_ID,
            "provider": "DATABENTO",
            "execution_status": "AUTHENTICATED_ZERO_PURCHASE_METADATA_PROBE_COMPLETED",
            "authenticated": True,
            "candidate_plan_sha256": PLAN_SHA,
            "candidate_plan_rows": PLAN_ROWS,
            "required_dataset_count": len(DATASETS),
            "entitled_dataset_count": sum(dataset in entitled for dataset in DATASETS),
            "representative_probe_count": len(ROOTS),
            "metadata_gate_passed_count": passed_count,
            "provider_contract_id_count": 0,
            "price_linkage_authorized_rows": 0,
            "purchase_authorized": False,
            "max_authorized_cost_usd": 0.0,
            "time_series_download_executed": False,
            "batch_download_submitted": False,
        },
        "requested_at": at.astimezone(UTC).isoformat(),
        "request": jsonable(request),
        "client": {"package": "databento", "version": version, "python": platform.python_version()},
        "operations": ops,
        "datasets": dataset_results,
        "representative_probes": probe_results,
        "provider_accepted": False,
        "authenticated_metadata_probe_executed": True,
        "metadata_gate_all_representative_roots_passed": all_passed,
        "next_gate": "EXPLICIT_MINIMAL_DEFINITION_AND_SETTLEMENT_COST_APPROVAL" if all_passed else "REJECT_OR_REMEDIATE_PROVIDER_CANDIDATE",
        "cost_quote_acquired": all(item["definition_cost_usd"] is not None and item["statistics_cost_usd"] is not None for item in probe_results),
        "license_snapshot_acquired": False,
        "definition_records_acquired": False,
        "settlement_records_acquired": False,
        "purchase_authorized": False,
        "global_price_linkage_authorized": False,
        "returns_authorized": False,
        "paper_replication_pass": False,
        "economic_edge_verdict": "INCONCLUSIVE",
    }


def write_bundle(output_dir: str | Path, request: Mapping[str, Any], evidence: Mapping[str, Any]) -> dict[str, Any]:
    root = Path(output_dir)
    files = {
        "probe-request.json": canonical(jsonable(request)),
        "probe-evidence.json": canonical(jsonable(evidence)),
        "probe-summary.json": canonical(
            {
                "probe_id": PROBE_ID,
                "execution_status": evidence["profile"]["execution_status"],
                "authenticated": evidence["profile"]["authenticated"],
                "provider_accepted": False,
                "purchase_authorized": False,
                "price_linkage_authorized_rows": 0,
                "provider_contract_id_count": 0,
                "time_series_download_executed": False,
                "batch_download_submitted": False,
                "returns_authorized": False,
                "economic_edge_verdict": "INCONCLUSIVE",
            }
        ),
    }
    for name, content in files.items():
        atomic_write(root / name, content)
    manifest = {
        "schema_version": "1.0",
        "probe_id": PROBE_ID,
        "files": {name: {"byte_count": len(content), "sha256": sha(content)} for name, content in sorted(files.items())},
        "provider_accepted": False,
        "purchase_authorized": False,
        "time_series_download_executed": False,
        "batch_download_submitted": False,
        "price_linkage_authorized_rows": 0,
        "returns_authorized": False,
        "paper_replication_pass": False,
        "economic_edge_verdict": "INCONCLUSIVE",
    }
    atomic_write(root / "probe-manifest.json", canonical(manifest))
    return manifest


def load_client(key: str) -> tuple[Any, str]:
    version = importlib.metadata.version("databento")
    if version != CLIENT_VERSION:
        raise RuntimeError(f"Expected databento {CLIENT_VERSION}, found {version}")
    module = importlib.import_module("databento")
    return module.Historical(key), version


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-plan-b64", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    request = build_request(load_plan(args.candidate_plan_b64))
    at = datetime.now(UTC)
    key = os.getenv(API_KEY_ENV, "").strip()
    if not key:
        evidence = blocked(request, at, "BLOCKED_MISSING_DATABENTO_API_KEY")
    elif not key.startswith("db-"):
        evidence = blocked(request, at, "BLOCKED_INVALID_API_KEY_FORMAT")
    else:
        try:
            client, version = load_client(key)
            evidence = run_probe(client, request, key, version, at)
        except Exception as exc:
            evidence = blocked(request, at, "PROBE_CLIENT_INITIALIZATION_FAILURE")
            evidence["sanitized_error"] = {
                "type": type(exc).__name__,
                "message": str(exc).replace(key, "[REDACTED]"),
            }
    write_bundle(args.output_dir, request, evidence)
    print(
        json.dumps(
            {
                "probe_id": PROBE_ID,
                "execution_status": evidence["profile"]["execution_status"],
                "authenticated": evidence["profile"]["authenticated"],
                "provider_accepted": False,
                "purchase_authorized": False,
                "price_linkage_authorized_rows": 0,
                "returns_authorized": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
