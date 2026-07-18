from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from hybrid_trader.avalai_capture import load_phase3c_avalai_config
from hybrid_trader.event_relevance import evaluate_relevance, relevance_decisions_sha256
from hybrid_trader.feed_source import PublicFeedSource


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Probe Phase 3H public feeds without semantic-provider calls."
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-source", action="append", default=[])
    args = parser.parse_args()

    root = args.output
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"Probe output directory is not empty: {root}")
    raw_root = root / "raw"
    raw_root.mkdir(parents=True)
    config = load_phase3c_avalai_config(args.config)
    observed_at = datetime.now(UTC)
    records: list[dict[str, object]] = []
    successful: set[str] = set()

    for source in config.capture.sources:
        try:
            result = PublicFeedSource(
                source,
                timeout_seconds=config.capture.timeout_seconds,
            ).fetch(retrieved_at=observed_at)
            raw_path = raw_root / f"{source.source_id}.xml"
            raw_path.write_bytes(result.payload)
            decisions = tuple(
                evaluate_relevance(envelope, source.relevance)
                for envelope in result.parse_result.documents
            )
            accepted = sum(decision.accepted for decision in decisions)
            successful.add(source.source_id)
            records.append(
                {
                    "source_id": source.source_id,
                    "feed_url": source.feed_url,
                    "status": "success",
                    "required": source.required,
                    "retrieved_at": result.retrieved_at,
                    "payload_sha256": result.payload_sha256,
                    "payload_bytes": len(result.payload),
                    "parsed_documents": len(result.parse_result.documents),
                    "accepted_documents": accepted,
                    "rejected_documents": len(decisions) - accepted,
                    "relevance_decisions_sha256": relevance_decisions_sha256(decisions),
                    "warnings": result.parse_result.warnings,
                    "error_type": None,
                    "error_message": None,
                }
            )
        except Exception as error:
            records.append(
                {
                    "source_id": source.source_id,
                    "feed_url": source.feed_url,
                    "status": "failed",
                    "required": source.required,
                    "retrieved_at": observed_at,
                    "payload_sha256": None,
                    "payload_bytes": 0,
                    "parsed_documents": 0,
                    "accepted_documents": 0,
                    "rejected_documents": 0,
                    "relevance_decisions_sha256": None,
                    "warnings": [],
                    "error_type": type(error).__name__,
                    "error_message": str(error)[:1_000],
                }
            )

    required = {
        source.source_id for source in config.capture.sources if source.required
    }.union(args.require_source)
    missing = sorted(required.difference(successful))
    if len(successful) < config.capture.minimum_successful_sources:
        missing.append(
            "minimum_successful_sources:"
            f"{len(successful)}/{config.capture.minimum_successful_sources}"
        )

    report = {
        "schema_version": "1.0",
        "config_sha256": hashlib.sha256(args.config.read_bytes()).hexdigest(),
        "observed_at": observed_at,
        "provider_calls_created": 0,
        "prospective_decisions_created": 0,
        "successful_sources": sorted(successful),
        "failed_sources": sorted(
            record["source_id"]
            for record in records
            if record["status"] == "failed"
        ),
        "required_probe_sources": sorted(required),
        "missing_required_probe_sources": missing,
        "sources": records,
    }
    _write_json(root / "feed_probe.json", report)
    checksum_lines = []
    for path in sorted(path for path in root.rglob("*") if path.is_file()):
        if path.name == "SHA256SUMS":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        checksum_lines.append(f"{digest}  {path.relative_to(root).as_posix()}")
    (root / "SHA256SUMS").write_text(
        "\n".join(checksum_lines) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True, indent=2, default=str))
    if missing:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
