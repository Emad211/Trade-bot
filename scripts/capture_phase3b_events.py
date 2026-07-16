from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from hybrid_trader.event_capture import capture_events, load_event_capture_spec


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

    manifest = capture_events(
        load_event_capture_spec(args.config),
        args.output,
        captured_at=_parse_time(args.captured_at),
    )
    decision_ledger = args.output / "prospective_decisions.jsonl"
    if decision_ledger.read_text(encoding="utf-8").strip():
        raise RuntimeError("Event capture unexpectedly created trading decisions")
    print(json.dumps(manifest.model_dump(mode="json"), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
