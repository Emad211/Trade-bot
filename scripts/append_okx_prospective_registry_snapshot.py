from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, cast

from hybrid_trader.replication.okx_prospective_registry import (
    ProspectiveFundingSourceContent,
    ProspectiveInstrumentContent,
    ProspectiveRegistryObservation,
    append_observation,
    diff_safe_values,
    tail_by_content_kind,
)

REGISTRY_ID = "OKX_BTC_USDT_SWAP_PROSPECTIVE_REGISTRY_V1"
CURRENT_BUILDER = Path("scripts/build_okx_prospective_registry_snapshot.py")
CURRENT_FILENAME = "okx-prospective-registry-initial-snapshot.json"
OUTPUT_FILENAME = "okx-prospective-registry-second-snapshot.json"


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_json_object(path: Path, *, label: str) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    try:
        value: Any = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label} is not valid JSON") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} is not an object")
    return raw, cast(dict[str, Any], value)


def _parse_observation(value: Any) -> ProspectiveRegistryObservation:
    if not isinstance(value, dict):
        raise RuntimeError("registry observation is not an object")
    payload = dict(value)
    expected_id = str(payload.pop("observation_id", ""))
    observation = ProspectiveRegistryObservation.model_validate(payload)
    if observation.observation_id != expected_id:
        raise RuntimeError("registry observation identity mismatch")
    return observation


def _validate_snapshot(value: dict[str, Any], *, initial_only: bool) -> None:
    if value.get("registry_id") != REGISTRY_ID:
        raise RuntimeError("snapshot belongs to another registry")
    if value.get("collection_mode") != "PROSPECTIVE_ONLY":
        raise RuntimeError("snapshot is not prospective-only")
    if initial_only and value.get("registry_verdict") != "INITIAL_PROSPECTIVE_SNAPSHOT_ONLY":
        raise RuntimeError("fresh snapshot has an unexpected verdict")
    for section in ("retention_state", "historical_state", "authorization"):
        flags = value.get(section)
        if not isinstance(flags, dict) or any(flag is not False for flag in flags.values()):
            raise RuntimeError(f"snapshot violates safe {section} flags")
    if value.get("issue_52_outcome") is not None:
        raise RuntimeError("snapshot unexpectedly assigns the gate outcome")
    if value.get("economic_edge_verdict") != "INCONCLUSIVE":
        raise RuntimeError("snapshot unexpectedly changes the edge verdict")


def _content_and_observations(
    value: dict[str, Any],
) -> tuple[
    ProspectiveInstrumentContent,
    ProspectiveFundingSourceContent,
    tuple[ProspectiveRegistryObservation, ...],
]:
    instrument = ProspectiveInstrumentContent.model_validate(value["instrument_content"])
    funding = ProspectiveFundingSourceContent.model_validate(value["funding_source_content"])
    observations_value = value.get("observations")
    if not isinstance(observations_value, list):
        raise RuntimeError("snapshot observations are not a list")
    observations = tuple(_parse_observation(item) for item in observations_value)
    version_ids = value.get("version_ids")
    if not isinstance(version_ids, dict):
        raise RuntimeError("snapshot version_ids are not an object")
    if instrument.content_version_id != version_ids.get("instrument"):
        raise RuntimeError("instrument version identity mismatch")
    if funding.content_version_id != version_ids.get("funding_source"):
        raise RuntimeError("funding version identity mismatch")
    return instrument, funding, observations


def _fresh_snapshot() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="okx-prospective-current-") as temporary:
        root = Path(temporary)
        subprocess.run(
            [
                sys.executable,
                str(CURRENT_BUILDER),
                "--output-dir",
                str(root),
            ],
            check=True,
        )
        _, value = _load_json_object(root / CURRENT_FILENAME, label="fresh snapshot")
    _validate_snapshot(value, initial_only=True)
    return value


def _serialize(observation: ProspectiveRegistryObservation) -> dict[str, Any]:
    return {
        **observation.model_dump(mode="json"),
        "observation_id": observation.observation_id,
    }


def run(*, previous_snapshot: Path, output_dir: Path) -> dict[str, Any]:
    previous_raw, previous = _load_json_object(
        previous_snapshot,
        label="previous snapshot",
    )
    _validate_snapshot(previous, initial_only=False)
    previous_instrument, previous_funding, previous_observations = _content_and_observations(
        previous
    )
    previous_instrument_tail = tail_by_content_kind(
        previous_observations,
        content_kind="INSTRUMENT",
    )
    previous_funding_tail = tail_by_content_kind(
        previous_observations,
        content_kind="FUNDING_SOURCE",
    )

    fresh = _fresh_snapshot()
    current_instrument, current_funding, fresh_observations = _content_and_observations(fresh)
    fresh_instrument = tail_by_content_kind(
        fresh_observations,
        content_kind="INSTRUMENT",
    )
    fresh_funding = tail_by_content_kind(
        fresh_observations,
        content_kind="FUNDING_SOURCE",
    )
    if fresh["provider_timestamp_policy"] != previous["provider_timestamp_policy"]:
        raise RuntimeError("provider timestamp policy changed")

    instrument_changes = diff_safe_values(
        previous_instrument.model_dump(mode="json"),
        current_instrument.model_dump(mode="json"),
    )
    funding_changes = diff_safe_values(
        previous_funding.model_dump(mode="json"),
        current_funding.model_dump(mode="json"),
    )
    instrument_observation = ProspectiveRegistryObservation(
        **{
            **fresh_instrument.model_dump(),
            "previous_observation_id": previous_instrument_tail.observation_id,
            "changed_fields": instrument_changes,
        }
    )
    funding_observation = ProspectiveRegistryObservation(
        **{
            **fresh_funding.model_dump(),
            "previous_observation_id": previous_funding_tail.observation_id,
            "changed_fields": funding_changes,
        }
    )

    instrument_stream = tuple(
        item for item in previous_observations if item.content_kind == "INSTRUMENT"
    )
    funding_stream = tuple(
        item for item in previous_observations if item.content_kind == "FUNDING_SOURCE"
    )
    instrument_append = append_observation(instrument_stream, instrument_observation)
    funding_append = append_observation(funding_stream, funding_observation)

    output_dir.mkdir(parents=True, exist_ok=True)
    evidence: dict[str, Any] = {
        "schema_version": "1.1",
        "registry_id": REGISTRY_ID,
        "collection_mode": "PROSPECTIVE_ONLY",
        "collection_started_at_utc": previous["collection_started_at_utc"],
        "snapshot_sequence": int(previous.get("snapshot_sequence", 1)) + 1,
        "previous_snapshot_sha256": _sha256(previous_raw),
        "registry_committed_at_utc": fresh["registry_committed_at_utc"],
        "instrument_content": current_instrument.model_dump(mode="json"),
        "funding_source_content": current_funding.model_dump(mode="json"),
        "observations": [
            *previous["observations"],
            _serialize(instrument_observation),
            _serialize(funding_observation),
        ],
        "version_ids": fresh["version_ids"],
        "source_change_summary": {
            "instrument": {
                "content_version_changed": instrument_append.content_version_changed,
                "changed_fields": list(instrument_changes),
                "previous_content_version_id": previous_instrument.content_version_id,
                "current_content_version_id": current_instrument.content_version_id,
            },
            "funding_source": {
                "content_version_changed": funding_append.content_version_changed,
                "changed_fields": list(funding_changes),
                "previous_content_version_id": previous_funding.content_version_id,
                "current_content_version_id": current_funding.content_version_id,
            },
        },
        "provider_timestamp_policy": previous["provider_timestamp_policy"],
        "retention_state": previous["retention_state"],
        "historical_state": previous["historical_state"],
        "authorization": previous["authorization"],
        "registry_verdict": "PROSPECTIVE_APPEND_SNAPSHOT",
        "issue_52_outcome": None,
        "economic_edge_verdict": "INCONCLUSIVE",
    }
    output = output_dir / OUTPUT_FILENAME
    output.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous-snapshot", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    evidence = run(
        previous_snapshot=args.previous_snapshot,
        output_dir=args.output_dir,
    )
    print(
        json.dumps(
            {
                "registry_id": evidence["registry_id"],
                "snapshot_sequence": evidence["snapshot_sequence"],
                "previous_snapshot_sha256": evidence["previous_snapshot_sha256"],
                "source_change_summary": evidence["source_change_summary"],
                "new_observations": evidence["observations"][-2:],
                "registry_verdict": evidence["registry_verdict"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
