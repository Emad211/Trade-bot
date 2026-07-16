from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from hybrid_trader.event_capture_models import EventCaptureManifest
from hybrid_trader.event_ledger import verify_document_ledger
from hybrid_trader.semantic_extraction import verify_semantic_ledger


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_phase3b_root(root: Path) -> dict[str, object]:
    state = root / "state"
    decisions = state / "prospective_decisions.jsonl"
    if not decisions.exists() or decisions.read_text(encoding="utf-8").strip():
        raise RuntimeError("Prospective decision ledger must exist and remain empty")
    document_head, _, document_count, document_ids = verify_document_ledger(
        state / "documents.jsonl"
    )
    semantic_state = verify_semantic_ledger(state / "semantic_events.jsonl")
    if not semantic_state.document_ids.issubset(document_ids):
        raise RuntimeError("Semantic ledger references an unknown document")

    manifests: list[EventCaptureManifest] = []
    for capture_dir in sorted((state / "captures").iterdir()):
        if not capture_dir.is_dir():
            continue
        manifest = EventCaptureManifest.model_validate_json(
            (capture_dir / "capture_manifest.json").read_text(encoding="utf-8")
        )
        if manifest.capture_id != capture_dir.name:
            raise RuntimeError("Capture directory and manifest identity disagree")
        inventory: dict[str, str] = {}
        for line in (capture_dir / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
            digest, name = line.split("  ", maxsplit=1)
            inventory[name] = digest
        expected = {"capture_manifest.json", "raw_payloads.json", "source_attempts.json"}
        if set(inventory) != expected:
            raise RuntimeError("Unexpected compact capture checksum inventory")
        for name, digest in inventory.items():
            if _sha256(capture_dir / name) != digest:
                raise RuntimeError(f"Compact capture checksum mismatch: {name}")
        for record in manifest.raw_payloads:
            raw_path = root / record.relative_path
            if not raw_path.is_file():
                raise FileNotFoundError(f"Raw capture payload missing: {raw_path}")
            if raw_path.stat().st_size != record.size_bytes or _sha256(raw_path) != record.sha256:
                raise RuntimeError(f"Raw capture payload mismatch: {raw_path}")
        manifests.append(manifest)

    if not manifests:
        raise RuntimeError("No Phase 3B capture manifests were found")
    latest = max(manifests, key=lambda item: (item.capture_completed_at, item.capture_id))
    if latest.document_ledger_head_sha256 != document_head:
        raise RuntimeError("Latest document ledger head does not match")
    if latest.semantic_ledger_head_sha256 != semantic_state.head_sha256:
        raise RuntimeError("Latest semantic ledger head does not match")
    if latest.document_count != document_count or latest.semantic_record_count != semantic_state.count:
        raise RuntimeError("Latest capture counts do not match current ledgers")
    return {
        "capture_count": len(manifests),
        "document_count": document_count,
        "semantic_record_count": semantic_state.count,
        "document_ledger_head_sha256": document_head,
        "semantic_ledger_head_sha256": semantic_state.head_sha256,
        "prospective_decision_count": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify a Phase 3B event capture root.")
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify_phase3b_root(args.root), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
