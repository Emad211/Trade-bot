from __future__ import annotations

import argparse
import json
from pathlib import Path

from hybrid_trader.avalai_capture import verify_phase3c_avalai_root


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify Phase 3C provider provenance and the non-activation boundary."
    )
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    result = verify_phase3c_avalai_root(args.root)
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
