from __future__ import annotations

import argparse
from collections.abc import Sequence

from hybrid_trader.replication.kenneth_french_daily import (
    write_safe_contract_evidence,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit frozen Kenneth French current daily factor snapshots."
    )
    parser.add_argument("--data-library", required=True)
    parser.add_argument("--ff3", required=True)
    parser.add_argument("--ff5", required=True)
    parser.add_argument("--mom", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    write_safe_contract_evidence(
        page_path=args.data_library,
        zip_paths={"ff3": args.ff3, "ff5": args.ff5, "mom": args.mom},
        output_dir=args.output_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
