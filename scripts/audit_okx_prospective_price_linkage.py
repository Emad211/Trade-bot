from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from hybrid_trader.replication.okx_price_linkage_probe import run_pilot


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    evidence = run_pilot(args.output_dir)
    print(json.dumps(asdict(evidence), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
