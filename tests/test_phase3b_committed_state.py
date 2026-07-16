from __future__ import annotations

import hashlib
import json
from pathlib import Path

from hybrid_trader.event_capture_models import EventCaptureManifest
from hybrid_trader.event_ledger import verify_document_ledger
from hybrid_trader.semantic_extraction import verify_semantic_ledger

ROOT = Path(__file__).resolve().parents[1] / "research" / "runs" / "phase3b-events-29494760888"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_committed_phase3b_state_is_self_consistent() -> None:
    inventory: dict[str, str] = {}
    for line in (ROOT / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", maxsplit=1)
        assert name not in inventory
        inventory[name] = digest
    files = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and path != ROOT / "SHA256SUMS"
    }
    assert set(inventory) == files
    for name, digest in inventory.items():
        assert _sha256(ROOT / name) == digest

    assert (ROOT / "state" / "prospective_decisions.jsonl").read_bytes() == b""
    assert not list(ROOT.rglob("*.xml"))

    document_head, _, document_count, document_ids = verify_document_ledger(
        ROOT / "state" / "documents.jsonl"
    )
    semantic_state = verify_semantic_ledger(ROOT / "state" / "semantic_events.jsonl")
    assert document_count == 20
    assert semantic_state.count == 20
    assert semantic_state.document_ids == document_ids

    capture_dirs = sorted((ROOT / "state" / "captures").iterdir())
    assert len(capture_dirs) == 1
    manifest = EventCaptureManifest.model_validate_json(
        (capture_dirs[0] / "capture_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest.status == "success"
    assert manifest.document_count == document_count
    assert manifest.semantic_record_count == semantic_state.count
    assert manifest.document_ledger_head_sha256 == document_head
    assert manifest.semantic_ledger_head_sha256 == semantic_state.head_sha256
    assert manifest.prospective_decisions_created is False
    assert manifest.raw_payloads_committed_to_git is False

    provenance = json.loads((ROOT / "provenance.json").read_text(encoding="utf-8"))
    assert provenance["workflow_run_id"] == 29494760888
    assert provenance["capture_id"] == manifest.capture_id
    assert provenance["document_count"] == document_count
    assert provenance["semantic_record_count"] == semantic_state.count
    assert provenance["prospective_decision_count"] == 0
    assert provenance["full_feed_files_in_git"] is False
