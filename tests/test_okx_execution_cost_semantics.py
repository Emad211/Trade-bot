from __future__ import annotations

from decimal import Decimal

import pytest

from hybrid_trader.replication.okx_execution_cost_semantics import (
    AggregationLevel,
    BookSnapshot,
    CostAggregationContext,
    CostComponent,
    CostComponentKind,
    ExecutionSemanticsError,
    Fill,
    LiquidityRole,
    OrderExecution,
    OrderState,
    OrderTimeline,
    OrderType,
    PriceIdentity,
    PriceObservation,
    Side,
    aggregate_synthetic_costs,
    directional_slippage,
    provider_cache_diagnostics,
)

BASE_MS = 1_784_635_200_000
BASE_US = BASE_MS * 1000


def _price(identity: PriceIdentity, value: str, *, offset_ms: int = 0) -> PriceObservation:
    return PriceObservation(
        identity=identity,
        value=Decimal(value),
        observed_at_ms=BASE_MS + offset_ms,
        source_id=f"SYNTHETIC_{identity.value}",
    )


def _book() -> BookSnapshot:
    return BookSnapshot(
        source_id="SYNTHETIC_BOOK",
        version_id="book-version-1",
        best_bid=_price(PriceIdentity.BEST_BID, "99"),
        best_ask=_price(PriceIdentity.BEST_ASK, "101"),
        provider_timestamp_ms=BASE_MS,
        research_available_at_ms=BASE_MS + 2,
        depth=5,
        aggregation_mode="books5",
        tick_size=Decimal("0.1"),
    )


def _fill(
    fill_id: str,
    price: str,
    quantity: str,
    *,
    offset_ms: int,
    role: LiquidityRole = LiquidityRole.TAKER,
) -> Fill:
    return Fill(
        fill_id=fill_id,
        trade_id=f"trade-{fill_id}",
        price=Decimal(price),
        quantity=Decimal(quantity),
        fill_time_ms=BASE_MS + offset_ms,
        liquidity_role=role,
    )


def _component(
    component_id: str,
    kind: CostComponentKind,
    amount: str,
    *,
    currency: str = "USDT",
    level: AggregationLevel = AggregationLevel.PER_FILL,
    horizon: str = "horizon-1",
) -> CostComponent:
    return CostComponent(
        component_id=component_id,
        kind=kind,
        amount=Decimal(amount),
        currency=currency,
        aggregation_level=level,
        horizon_id=horizon,
        reconciliation_key=f"key-{component_id}",
    )


def _context(**overrides: object) -> CostAggregationContext:
    values: dict[str, object] = {
        "currency": "USDT",
        "horizon_id": "horizon-1",
        "quantity_convention": "BASE_QUANTITY",
        "instrument_version_id": "instrument-version-1",
    }
    values.update(overrides)
    return CostAggregationContext(**values)  # type: ignore[arg-type]


def test_buy_uses_ask_sell_uses_bid_and_midpoint_is_reference_only() -> None:
    book = _book()

    assert book.executable_quote(side=Side.BUY).identity == PriceIdentity.BEST_ASK
    assert book.executable_quote(side=Side.SELL).identity == PriceIdentity.BEST_BID
    assert book.full_spread() == Decimal("2")
    assert book.half_spread() == Decimal("1")

    midpoint = book.midpoint_reference()
    assert midpoint.identity == PriceIdentity.MIDPOINT
    assert midpoint.value == Decimal("100")
    with pytest.raises(ExecutionSemanticsError, match="not the executable quote identity"):
        midpoint.require_executable(side=Side.BUY)


@pytest.mark.parametrize(
    "identity",
    [
        PriceIdentity.DECISION_REFERENCE,
        PriceIdentity.MIDPOINT,
        PriceIdentity.LAST_TRADED,
        PriceIdentity.ORDER_LIMIT,
        PriceIdentity.MARK,
        PriceIdentity.INDEX,
        PriceIdentity.POSITION_ACCOUNTING,
    ],
)
def test_non_executable_identities_fail_closed(identity: PriceIdentity) -> None:
    with pytest.raises(ExecutionSemanticsError, match="not the executable quote identity"):
        _price(identity, "100").require_executable(side=Side.BUY)


def test_limit_price_is_constraint_not_fill_price() -> None:
    execution = OrderExecution(
        order_id="order-1",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        requested_quantity=Decimal("2"),
        limit_price=Decimal("101"),
        final_state=OrderState.FILLED,
        fills=(
            _fill("1", "100.5", "1", offset_ms=10),
            _fill("2", "100.8", "1", offset_ms=11),
        ),
        acknowledgement_accepted=True,
    )

    assert execution.limit_price == Decimal("101")
    assert execution.weighted_average_fill_price == Decimal("100.65")
    assert execution.weighted_average_fill_price != execution.limit_price


def test_acknowledgement_and_cancel_ack_are_not_execution_or_final_cancellation() -> None:
    live = OrderExecution(
        order_id="order-live",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        requested_quantity=Decimal("1"),
        final_state=OrderState.LIVE,
        fills=(),
        acknowledgement_accepted=True,
        cancellation_acknowledged=True,
        cancellation_confirmed=False,
    )

    assert live.execution_confirmed is False
    assert live.acknowledgement_is_execution is False
    assert live.cancellation_ack_is_final_state is False

    with pytest.raises(ExecutionSemanticsError, match="requires confirmation"):
        OrderExecution(
            order_id="bad-cancel",
            side=Side.SELL,
            order_type=OrderType.MARKET,
            requested_quantity=Decimal("1"),
            final_state=OrderState.CANCELED,
            fills=(),
            cancellation_acknowledged=True,
            cancellation_confirmed=False,
        )


def test_partial_fills_use_quantity_weighting_and_preserve_residual() -> None:
    execution = OrderExecution(
        order_id="partial",
        side=Side.SELL,
        order_type=OrderType.IOC,
        requested_quantity=Decimal("5"),
        limit_price=Decimal("99"),
        final_state=OrderState.PARTIALLY_FILLED,
        fills=(
            _fill("1", "100", "1", offset_ms=10),
            _fill("2", "98", "2", offset_ms=11),
        ),
        acknowledgement_accepted=True,
    )

    assert execution.filled_quantity == Decimal("3")
    assert execution.residual_quantity == Decimal("2")
    assert execution.weighted_average_fill_price == Decimal("98.66666666666666666666666667")


def test_unfilled_quantity_never_receives_a_fabricated_price() -> None:
    execution = OrderExecution(
        order_id="unfilled",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        requested_quantity=Decimal("3"),
        final_state=OrderState.LIVE,
        fills=(),
        acknowledgement_accepted=True,
    )

    assert execution.filled_quantity == 0
    assert execution.residual_quantity == Decimal("3")
    assert execution.weighted_average_fill_price is None


def test_liquidity_role_comes_from_fills_not_order_type() -> None:
    taker_limit = OrderExecution(
        order_id="limit-taker",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        requested_quantity=Decimal("1"),
        limit_price=Decimal("101"),
        final_state=OrderState.FILLED,
        fills=(_fill("1", "100", "1", offset_ms=1, role=LiquidityRole.TAKER),),
    )
    synthetic_maker_market = OrderExecution(
        order_id="market-role-contract",
        side=Side.SELL,
        order_type=OrderType.MARKET,
        requested_quantity=Decimal("1"),
        final_state=OrderState.FILLED,
        fills=(_fill("2", "99", "1", offset_ms=2, role=LiquidityRole.MAKER),),
    )

    assert taker_limit.liquidity_roles() == (LiquidityRole.TAKER,)
    assert synthetic_maker_market.liquidity_roles() == (LiquidityRole.MAKER,)


def test_latency_decomposition_preserves_units_and_non_overlapping_clocks() -> None:
    timeline = OrderTimeline(
        client_decision_us=BASE_US,
        client_submit_us=BASE_US + 100,
        gateway_in_us=BASE_US + 200,
        gateway_out_us=BASE_US + 500,
        client_receive_us=BASE_US + 700,
        order_create_ms=BASE_MS + 1,
        order_update_ms=BASE_MS + 5,
        fill_times_ms=(BASE_MS + 3, BASE_MS + 4),
    )

    assert timeline.latency_components_us() == {
        "client_decision_to_submit": 100,
        "client_submit_to_gateway_in": 100,
        "gateway_processing": 300,
        "gateway_out_to_client_receive": 200,
        "client_decision_to_first_fill": 3000,
        "client_decision_to_last_fill": 4000,
        "order_live_duration": 4000,
    }


def test_negative_reordered_or_wrong_unit_clocks_fail_closed() -> None:
    with pytest.raises(ExecutionSemanticsError, match="reordered"):
        OrderTimeline(
            client_decision_us=BASE_US,
            client_submit_us=BASE_US + 200,
            gateway_in_us=BASE_US + 100,
            gateway_out_us=BASE_US + 500,
            client_receive_us=BASE_US + 700,
            order_create_ms=BASE_MS + 1,
            order_update_ms=BASE_MS + 2,
        )

    with pytest.raises(ExecutionSemanticsError, match="microseconds"):
        OrderTimeline(
            client_decision_us=BASE_MS,
            client_submit_us=BASE_MS + 1,
            gateway_in_us=BASE_MS + 2,
            gateway_out_us=BASE_MS + 3,
            client_receive_us=BASE_MS + 4,
            order_create_ms=BASE_MS + 1,
            order_update_ms=BASE_MS + 2,
        )


def test_directional_slippage_is_adverse_positive_for_buys_and_sells() -> None:
    reference = _price(PriceIdentity.DECISION_REFERENCE, "100", offset_ms=0)
    buy_fill = _price(PriceIdentity.WEIGHTED_AVERAGE_FILL, "101", offset_ms=10)
    sell_fill = _price(PriceIdentity.WEIGHTED_AVERAGE_FILL, "99", offset_ms=10)

    assert directional_slippage(side=Side.BUY, reference=reference, execution=buy_fill) == 1
    assert directional_slippage(side=Side.SELL, reference=reference, execution=sell_fill) == 1

    favorable_buy = _price(PriceIdentity.INDIVIDUAL_FILL, "99", offset_ms=11)
    assert (
        directional_slippage(
            side=Side.BUY,
            reference=reference,
            execution=favorable_buy,
        )
        == -1
    )


def test_slippage_requires_fill_identity_and_reference_time_order() -> None:
    reference = _price(PriceIdentity.MIDPOINT, "100", offset_ms=10)
    non_fill = _price(PriceIdentity.BEST_ASK, "101", offset_ms=11)
    with pytest.raises(ExecutionSemanticsError, match="fill identity"):
        directional_slippage(side=Side.BUY, reference=reference, execution=non_fill)

    early_fill = _price(PriceIdentity.INDIVIDUAL_FILL, "101", offset_ms=5)
    with pytest.raises(ExecutionSemanticsError, match="precede"):
        directional_slippage(side=Side.BUY, reference=reference, execution=early_fill)


def test_cache_nonmonotonicity_is_diagnostic_not_rewritten() -> None:
    diagnostics = provider_cache_diagnostics((BASE_MS + 100, BASE_MS + 50, BASE_MS + 120))

    assert diagnostics == {
        "monotonic_in_request_order": False,
        "request_order_rewritten": False,
        "later_response_may_have_earlier_provider_time": True,
        "spread_ms": 70,
    }


def test_cost_components_reject_double_counting() -> None:
    context = _context()
    shortfall = _component(
        "shortfall",
        CostComponentKind.IMPLEMENTATION_SHORTFALL,
        "1.5",
    )
    impact = _component("impact", CostComponentKind.MARKET_IMPACT, "0.5")

    with pytest.raises(ExecutionSemanticsError, match="decomposed components"):
        aggregate_synthetic_costs(context=context, components=(shortfall, impact))

    full = _component("full", CostComponentKind.QUOTED_FULL_SPREAD, "2")
    half = _component("half", CostComponentKind.QUOTED_HALF_SPREAD, "1")
    with pytest.raises(ExecutionSemanticsError, match="both be counted"):
        aggregate_synthetic_costs(context=context, components=(full, half))


def test_cost_aggregation_requires_currency_level_and_owner_inputs() -> None:
    fee = _component("fee", CostComponentKind.TRADING_FEE, "0.1")
    with pytest.raises(ExecutionSemanticsError, match="owner-account fee snapshot"):
        aggregate_synthetic_costs(context=_context(), components=(fee,))

    funding = _component(
        "funding",
        CostComponentKind.FUNDING_CASHFLOW,
        "0.2",
        level=AggregationLevel.PER_BILL,
    )
    with pytest.raises(ExecutionSemanticsError, match="formula-version"):
        aggregate_synthetic_costs(context=_context(), components=(funding,))

    mixed_currency = (
        _component("a", CostComponentKind.ARRIVAL_SLIPPAGE, "1"),
        _component(
            "b",
            CostComponentKind.MARKET_IMPACT,
            "2",
            currency="BTC",
        ),
    )
    with pytest.raises(ExecutionSemanticsError, match="Mixed currencies"):
        aggregate_synthetic_costs(context=_context(), components=mixed_currency)

    mixed_levels = (
        _component("c", CostComponentKind.ARRIVAL_SLIPPAGE, "1"),
        _component(
            "d",
            CostComponentKind.OPPORTUNITY_COST,
            "2",
            level=AggregationLevel.PER_ORDER,
        ),
    )
    with pytest.raises(ExecutionSemanticsError, match="Mixed aggregation levels"):
        aggregate_synthetic_costs(context=_context(), components=mixed_levels)


def test_position_aggregate_cannot_readd_fee_or_funding() -> None:
    position = _component(
        "position",
        CostComponentKind.POSITION_REALIZED_PNL,
        "10",
        level=AggregationLevel.POSITION_AGGREGATE,
    )
    fee = _component(
        "fee",
        CostComponentKind.TRADING_FEE,
        "-1",
        level=AggregationLevel.PER_FILL,
    )
    context = _context(
        owner_fee_snapshot_id="fee-snapshot-1",
        reconciliation_transform_id="transform-1",
    )

    with pytest.raises(ExecutionSemanticsError, match="again"):
        aggregate_synthetic_costs(context=context, components=(position, fee))


def test_elp_and_book_constraints_are_explicit() -> None:
    with pytest.raises(ExecutionSemanticsError, match="ELP taker access"):
        BookSnapshot(
            source_id="book",
            version_id="version",
            best_bid=_price(PriceIdentity.BEST_BID, "99"),
            best_ask=_price(PriceIdentity.BEST_ASK, "101"),
            provider_timestamp_ms=BASE_MS,
            research_available_at_ms=BASE_MS + 1,
            depth=5,
            aggregation_mode="books5",
            elp_liquidity_included=False,
            elp_taker_access=True,
        )

    with pytest.raises(ExecutionSemanticsError, match="stale_threshold"):
        BookSnapshot(
            source_id="book",
            version_id="version",
            best_bid=_price(PriceIdentity.BEST_BID, "99"),
            best_ask=_price(PriceIdentity.BEST_ASK, "101"),
            provider_timestamp_ms=BASE_MS,
            research_available_at_ms=BASE_MS + 1,
            depth=5,
            aggregation_mode="books5",
            stale_threshold_ms=0,
        )
