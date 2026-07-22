from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from hybrid_trader.replication.okx_fee_accounting import (
    AccountFeeRateSnapshot,
    AccountingAmountReference,
    AggregationLevel,
    FeeRateQuery,
    FillRecord,
    FundingBillDirection,
    FundingBillRecord,
    FundingFormulaApplicability,
    FundingFormulaVersion,
    InstrumentType,
    LiquidityRole,
    OKXFeeAccountingError,
    OwnerAccountAccessBoundary,
    PositionAccountingAggregate,
    build_safe_accounting_contract_evidence,
    safe_evidence_json,
    sum_same_aggregation_level,
)

TS = 1784635200000


def _spot_fee_snapshot() -> AccountFeeRateSnapshot:
    return AccountFeeRateSnapshot(
        query=FeeRateQuery(InstrumentType.SPOT, instrument_id="BTC-USDT"),
        level="Lv1",
        rule_type="normal",
        response_timestamp_ms=TS,
        maker=Decimal("-0.0008"),
        taker=Decimal("-0.001"),
        maker_u=None,
        taker_u=None,
    )


def _swap_fee_snapshot() -> AccountFeeRateSnapshot:
    return AccountFeeRateSnapshot(
        query=FeeRateQuery(InstrumentType.SWAP, instrument_family="BTC-USDT"),
        level="Lv1",
        rule_type="normal",
        response_timestamp_ms=TS,
        maker=Decimal("-0.0002"),
        taker=Decimal("-0.0005"),
        maker_u=Decimal("-0.0002"),
        taker_u=Decimal("-0.0005"),
    )


def _spot_fill(*, fill_time: int = TS, record_ts: int = TS + 1) -> FillRecord:
    return FillRecord(
        instrument_type=InstrumentType.SPOT,
        instrument_id="BTC-USDT",
        trade_id=f"spot-{fill_time}",
        order_id="order-spot",
        bill_id="bill-spot",
        fill_time_ms=fill_time,
        record_timestamp_ms=record_ts,
        liquidity_role=LiquidityRole.TAKER,
        fee=Decimal("-0.000001"),
        fee_currency="BTC",
        fee_rate=Decimal("-0.001"),
        fill_price=Decimal("60000"),
        fill_size=Decimal("0.001"),
        fill_index_price=None,
        fill_mark_price=None,
        fill_pnl=Decimal("0"),
        trade_quote_currency="USDT",
        side="buy",
        position_side="net",
        subtype="1",
    )


def _swap_fill() -> FillRecord:
    return FillRecord(
        instrument_type=InstrumentType.SWAP,
        instrument_id="BTC-USDT-SWAP",
        trade_id="swap-1",
        order_id="order-swap",
        bill_id="bill-swap",
        fill_time_ms=TS,
        record_timestamp_ms=TS + 1,
        liquidity_role=LiquidityRole.MAKER,
        fee=Decimal("0.01"),
        fee_currency="USDT",
        fee_rate=None,
        fill_price=Decimal("60000"),
        fill_size=Decimal("10"),
        fill_index_price=Decimal("59995"),
        fill_mark_price=Decimal("60001"),
        fill_pnl=Decimal("0"),
        trade_quote_currency="USDT",
        side="sell",
        position_side="short",
        subtype="4",
    )


def test_fee_queries_are_instrument_specific() -> None:
    spot = FeeRateQuery(InstrumentType.SPOT, instrument_id="BTC-USDT")
    swap = FeeRateQuery(InstrumentType.SWAP, instrument_family="BTC-USDT")
    assert spot.query_parameter_names == ("instId", "instType")
    assert swap.query_parameter_names == ("instFamily", "instType")

    with pytest.raises(OKXFeeAccountingError, match="SPOT fee query"):
        FeeRateQuery(InstrumentType.SPOT, instrument_family="BTC-USDT").validate()
    with pytest.raises(OKXFeeAccountingError, match="SWAP fee query"):
        FeeRateQuery(InstrumentType.SWAP, instrument_id="BTC-USDT-SWAP").validate()


def test_account_fee_snapshots_preserve_product_fields_and_zero_fee_caveat() -> None:
    _spot_fee_snapshot().validate()
    _swap_fee_snapshot().validate()

    base = _spot_fee_snapshot()
    with pytest.raises(OKXFeeAccountingError, match="zero-fee-pair"):
        AccountFeeRateSnapshot(
            **{**base.__dict__, "open_api_reflects_zero_fee_exceptions": True}
        ).validate()


def test_fill_fee_sign_and_currency_are_explicit() -> None:
    spot = _spot_fill()
    swap = _swap_fill()
    assert spot.fee_semantics == "COMMISSION_CHARGE"
    assert swap.fee_semantics == "REBATE"
    assert spot.fee_currency == "BTC"
    assert spot.trade_quote_currency == "USDT"

    with pytest.raises(OKXFeeAccountingError, match="feeCcy"):
        FillRecord(**{**spot.__dict__, "fee_currency": ""}).validate()


def test_spot_and_swap_fill_field_contracts_are_distinct() -> None:
    _spot_fill().validate()
    _swap_fill().validate()

    with pytest.raises(OKXFeeAccountingError, match="SWAP fills do not admit"):
        FillRecord(**{**_swap_fill().__dict__, "fee_rate": Decimal("-0.0005")}).validate()
    with pytest.raises(OKXFeeAccountingError, match="SPOT fill requires"):
        FillRecord(**{**_spot_fill().__dict__, "fee_rate": None}).validate()


def test_fill_chronology_uses_fill_time_not_record_generation_time() -> None:
    earlier_trade_later_record = _spot_fill(fill_time=TS, record_ts=TS + 5000)
    later_trade_earlier_record = _spot_fill(fill_time=TS + 1000, record_ts=TS + 1001)
    ordered = sorted(
        (later_trade_earlier_record, earlier_trade_later_record),
        key=lambda item: item.chronology_key,
    )
    assert ordered == [earlier_trade_later_record, later_trade_earlier_record]


def test_funding_bill_expense_and_income_remain_distinct() -> None:
    expense = FundingBillRecord("bill-173", "BTC-USDT-SWAP", 173, "USDT", Decimal("-1"), TS)
    income = FundingBillRecord("bill-174", "BTC-USDT-SWAP", 174, "USDT", Decimal("1"), TS)
    assert expense.direction == FundingBillDirection.EXPENSE
    assert income.direction == FundingBillDirection.INCOME

    with pytest.raises(OKXFeeAccountingError, match="173 or 174"):
        FundingBillRecord("bad", "BTC-USDT-SWAP", 175, "USDT", Decimal("0"), TS).validate()


def test_position_realized_pnl_reconciles_exactly_once() -> None:
    position = PositionAccountingAggregate(
        instrument_id="BTC-USDT-SWAP",
        position_side="net",
        realized_pnl=Decimal("7"),
        pnl=Decimal("10"),
        fee=Decimal("-1"),
        funding_fee=Decimal("-2"),
        liquidation_penalty=Decimal("0"),
        settled_pnl=Decimal("0"),
        provider_timestamp_ms=TS,
    )
    position.validate()

    with pytest.raises(OKXFeeAccountingError, match="does not reconcile"):
        PositionAccountingAggregate(
            **{**position.__dict__, "realized_pnl": Decimal("6")}
        ).validate()


def test_aggregation_rejects_mixed_levels_currencies_and_duplicate_keys() -> None:
    fills = (
        AccountingAmountReference(AggregationLevel.PER_FILL, "trade-1", "USDT", Decimal("-1")),
        AccountingAmountReference(AggregationLevel.PER_FILL, "trade-2", "USDT", Decimal("2")),
    )
    assert sum_same_aggregation_level(fills) == Decimal("1")

    with pytest.raises(OKXFeeAccountingError, match="Mixed aggregation levels"):
        sum_same_aggregation_level(
            (
                fills[0],
                AccountingAmountReference(
                    AggregationLevel.POSITION_AGGREGATE, "position-1", "USDT", Decimal("1")
                ),
            )
        )
    with pytest.raises(OKXFeeAccountingError, match="Mixed currencies"):
        sum_same_aggregation_level(
            (
                fills[0],
                AccountingAmountReference(
                    AggregationLevel.PER_FILL, "trade-2", "BTC", Decimal("1")
                ),
            )
        )
    with pytest.raises(OKXFeeAccountingError, match="Duplicate reconciliation"):
        sum_same_aggregation_level((fills[0], fills[0]))


def test_current_funding_formula_is_versioned_and_not_backdated() -> None:
    formula = FundingFormulaVersion()
    assert (
        formula.applicability(datetime(2022, 3, 1, tzinfo=UTC))
        == FundingFormulaApplicability.NOT_APPLICABLE
    )
    assert (
        formula.applicability(datetime(2026, 6, 2, tzinfo=UTC))
        == FundingFormulaApplicability.AMBIGUOUS_MIGRATION_WINDOW
    )
    assert (
        formula.applicability(
            datetime(2026, 6, 2, tzinfo=UTC), provider_formula_type=formula.formula_id
        )
        == FundingFormulaApplicability.PROVIDER_CONFIRMED_MIGRATION_WINDOW
    )
    assert (
        formula.applicability(datetime(2026, 6, 4, tzinfo=UTC))
        == FundingFormulaApplicability.APPLICABLE
    )
    assert formula.interval_divisor(1) == Decimal("8")
    assert formula.interval_divisor(8) == Decimal("1")


def test_real_account_snapshot_requires_every_owner_boundary() -> None:
    blocked = OwnerAccountAccessBoundary(False, True, True, True, True, True)
    with pytest.raises(OKXFeeAccountingError, match="read_only_credentials_present"):
        blocked.validate_real_snapshot()

    OwnerAccountAccessBoundary(True, True, True, True, True, True).validate_real_snapshot()


def test_safe_public_evidence_contains_contract_only() -> None:
    evidence = build_safe_accounting_contract_evidence()
    payload = safe_evidence_json(evidence)
    assert evidence.real_account_request_performed is False
    assert evidence.owner_account_fee_snapshot_status == "BLOCKED_OWNER_READ_ONLY_CREDENTIALS"
    assert evidence.public_evidence_contains_account_values is False
    assert evidence.public_evidence_contains_credentials is False
    assert all(value is False for value in evidence.authorizations.values())
    assert "-0.0008" not in payload
    assert "order-spot" not in payload
    assert "bill-173" not in payload
    assert "API_KEY" not in payload
