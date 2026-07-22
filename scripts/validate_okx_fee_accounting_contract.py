from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from hybrid_trader.replication.okx_fee_accounting import (
    AccountFeeRateSnapshot,
    AccountingAmountReference,
    AggregationLevel,
    FeeRateQuery,
    FillRecord,
    FundingBillRecord,
    FundingFormulaApplicability,
    FundingFormulaVersion,
    InstrumentType,
    LiquidityRole,
    PositionAccountingAggregate,
    build_safe_accounting_contract_evidence,
    safe_evidence_json,
    sum_same_aggregation_level,
)

TS = 1784635200000


def _exercise_contract() -> None:
    spot_query = FeeRateQuery(InstrumentType.SPOT, instrument_id="BTC-USDT")
    swap_query = FeeRateQuery(InstrumentType.SWAP, instrument_family="BTC-USDT")
    AccountFeeRateSnapshot(
        spot_query,
        "Lv1",
        "normal",
        TS,
        Decimal("-0.0008"),
        Decimal("-0.001"),
        None,
        None,
    ).validate()
    AccountFeeRateSnapshot(
        swap_query,
        "Lv1",
        "normal",
        TS,
        Decimal("-0.0002"),
        Decimal("-0.0005"),
        Decimal("-0.0002"),
        Decimal("-0.0005"),
    ).validate()

    fill = FillRecord(
        InstrumentType.SPOT,
        "BTC-USDT",
        "synthetic-trade",
        "synthetic-order",
        "synthetic-bill",
        TS,
        TS + 1,
        LiquidityRole.TAKER,
        Decimal("-0.000001"),
        "BTC",
        Decimal("-0.001"),
        Decimal("60000"),
        Decimal("0.001"),
        None,
        None,
        Decimal("0"),
        "USDT",
        "buy",
        "net",
        "1",
    )
    fill.validate()
    assert fill.fee_semantics == "COMMISSION_CHARGE"

    expense = FundingBillRecord(
        "synthetic-funding-expense", "BTC-USDT-SWAP", 173, "USDT", Decimal("-1"), TS
    )
    income = FundingBillRecord(
        "synthetic-funding-income", "BTC-USDT-SWAP", 174, "USDT", Decimal("1"), TS
    )
    assert expense.direction.value == "FUNDING_EXPENSE"
    assert income.direction.value == "FUNDING_INCOME"

    position = PositionAccountingAggregate(
        "BTC-USDT-SWAP",
        "net",
        Decimal("7"),
        Decimal("10"),
        Decimal("-1"),
        Decimal("-2"),
        Decimal("0"),
        Decimal("0"),
        TS,
    )
    position.validate()

    assert sum_same_aggregation_level(
        (
            AccountingAmountReference(
                AggregationLevel.PER_FILL, "synthetic-fill-1", "USDT", Decimal("-1")
            ),
            AccountingAmountReference(
                AggregationLevel.PER_FILL, "synthetic-fill-2", "USDT", Decimal("2")
            ),
        )
    ) == Decimal("1")

    formula = FundingFormulaVersion()
    assert (
        formula.applicability(datetime(2022, 3, 1, tzinfo=UTC))
        == FundingFormulaApplicability.NOT_APPLICABLE
    )
    assert (
        formula.applicability(datetime(2026, 6, 4, tzinfo=UTC))
        == FundingFormulaApplicability.APPLICABLE
    )


def run(output_dir: str | Path) -> Path:
    _exercise_contract()
    evidence = build_safe_accounting_contract_evidence()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    path = output / "okx-fee-accounting-contract-safe-evidence.json"
    path.write_text(safe_evidence_json(evidence), encoding="utf-8")
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    path = run(args.output_dir)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
