from __future__ import annotations

import argparse
from collections.abc import Sequence

from hybrid_trader.replication.moreira_muir_reconciliation import (
    write_safe_reconciliation_evidence,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reconcile Moreira-Muir unmanaged factors to current official sources."
    )
    parser.add_argument("--author-csv", required=True)
    parser.add_argument("--author-page", required=True)
    parser.add_argument("--data-library", required=True)
    parser.add_argument("--ff3", required=True)
    parser.add_argument("--ff5", required=True)
    parser.add_argument("--mom", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    write_safe_reconciliation_evidence(
        author_csv_path=args.author_csv,
        author_page_path=args.author_page,
        data_library_path=args.data_library,
        monthly_zip_paths={
            "ff3_monthly": args.ff3,
            "ff5_monthly": args.ff5,
            "momentum_monthly": args.mom,
        },
        output_dir=args.output_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
