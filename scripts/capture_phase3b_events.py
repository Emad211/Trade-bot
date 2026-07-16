from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from hybrid_trader.event_capture import (
    EventCaptureFailure,
    capture_events,
    load_event_capture_spec,
)
from hybrid_trader.event_ledger import verify_document_ledger
from hybrid_trader.semantic_extraction import verify_semantic_ledger


def _parse_time(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("--captured-at must include a timezone")
    return parsed.astimezone(UTC)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Capture public event feeds without producing trading decisions."
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--captured-at")
    args = parser.parse_args()

    try:
        manifest = capture_events(
            load_event_capture_spec(args.config),
            args.output,
            captured_at=_parse_time(args.captured_at),
        )
    except EventCaptureFailure as exc:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "error": str(exc),
                    "manifest_path": str(exc.manifest_path),
                },
                sort_keys=True,
                indent=2,
            )
        )
        raise SystemExit(1) from exc

    state_root = args.output / "state"
    decision_ledger = state_root / "prospective_decisions.jsonl"
    if decision_ledger.read_text(encoding="utf-8").strip():
        raise RuntimeError("Event capture unexpectedly created trading decisions")
    document_head, _, document_count, _ = verify_document_ledger(state_root / "documents.jsonl")
    semantic_state = verify_semantic_ledger(state_root / "semantic_events.jsonl")
    if (
        document_head != manifest.document_ledger_head_sha256
        or document_count != manifest.document_count
    ):
        raise RuntimeError("Document ledger does not match the capture manifest")
    if (
        semantic_state.head_sha256 != manifest.semantic_ledger_head_sha256
        or semantic_state.count != manifest.semantic_record_count
    ):
        raise RuntimeError("Semantic ledger does not match the capture manifest")
    print(json.dumps(manifest.model_dump(mode="json"), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
