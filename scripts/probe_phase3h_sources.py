from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict

from hybrid_trader.event_documents import FeedSourceSpec
from hybrid_trader.source_admission import (
    SourceAdmissionPolicy,
    SourceAdmissionResult,
    probe_source,
    write_admission_report,
)


class AdmissionCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    required_for_integration: bool = False
    source: FeedSourceSpec


class AdmissionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    policy: SourceAdmissionPolicy
    candidates: tuple[AdmissionCandidate, ...]


def load_config(path: Path) -> AdmissionConfig:
    if not path.is_file():
        raise FileNotFoundError(f"Phase 3H candidate config not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        payload: Any = yaml.safe_load(handle) or {}
    config = AdmissionConfig.model_validate(payload)
    source_ids = [candidate.source.source_id for candidate in config.candidates]
    if not source_ids:
        raise ValueError("Phase 3H requires at least one candidate source")
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("Phase 3H candidate source IDs cannot contain duplicates")
    return config


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Probe candidate public feeds without modifying longitudinal state."
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    args = parser.parse_args()

    config = load_config(args.config)
    reports_root = args.output / "reports"
    raw_root = args.output / "raw"
    reports_root.mkdir(parents=True, exist_ok=True)
    raw_root.mkdir(parents=True, exist_ok=True)

    results: list[SourceAdmissionResult] = []
    required_failures: list[str] = []
    for candidate in config.candidates:
        result, payload = probe_source(
            candidate.source,
            policy=config.policy,
            timeout_seconds=args.timeout_seconds,
        )
        write_admission_report(result, reports_root)
        if payload is not None:
            raw_path = raw_root / f"{candidate.source.source_id}.xml"
            raw_path.write_bytes(payload)
            if hashlib.sha256(payload).hexdigest() != result.payload_sha256:
                raise RuntimeError("Stored Phase 3H raw payload disagrees with report")
        results.append(result)
        if candidate.required_for_integration and result.status != "accepted":
            required_failures.append(candidate.source.source_id)

    summary = {
        "schema_version": "1.0",
        "accepted_source_ids": sorted(
            result.source_id for result in results if result.status == "accepted"
        ),
        "rejected_source_ids": sorted(
            result.source_id for result in results if result.status == "rejected"
        ),
        "required_integration_failures": sorted(required_failures),
        "all_required_candidates_accepted": not required_failures,
        "longitudinal_state_modified": False,
        "results": [result.model_dump(mode="json") for result in results],
    }
    summary_path = args.output / "summary.json"
    summary_path.write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    checksum = hashlib.sha256(summary_path.read_bytes()).hexdigest()
    (args.output / "SUMMARY_SHA256SUMS").write_text(
        f"{checksum}  summary.json\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True, indent=2))
    if required_failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
