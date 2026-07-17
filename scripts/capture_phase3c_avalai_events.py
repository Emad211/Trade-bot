from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from hybrid_trader.avalai_capture import (
    capture_avalai_events,
    load_phase3c_avalai_config,
    verify_phase3c_avalai_root,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Capture public event feeds and extract semantic features through AvalAI."
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not os.environ.get("AVALAI_API_KEY"):
        raise RuntimeError("AVALAI_API_KEY must be provided through the environment")
    result = capture_avalai_events(
        load_phase3c_avalai_config(args.config),
        args.output,
    )
    verification = verify_phase3c_avalai_root(args.output)
    if verification["prospective_decision_count"] != 0:
        raise RuntimeError("AvalAI capture unexpectedly created a trading decision")
    print(
        json.dumps(
            {
                "capture": result.capture.model_dump(mode="json"),
                "provider": result.provider.model_dump(mode="json"),
                "verification": verification,
            },
            sort_keys=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
