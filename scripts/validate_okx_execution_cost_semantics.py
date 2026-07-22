from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path

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


def _price(identity: PriceIdentity, value: str, offset_ms: int = 0) -> PriceObservation:
    return PriceObservation(
        identity=identity,
        value=Decimal(value),
        observed_at_ms=BASE_MS + offset_ms,
        source_id=f"SYNTHETIC_{identity.value}",
    )


def _component(
    component_id: str,
    kind: CostComponentKind,
    amount: str,
    *,
    level: AggregationLevel = AggregationLevel.PER_FILL,
) -> CostComponent:
    return CostComponent(
        component_id=component_id,
        kind=kind,
        amount=Decimal(amount),
        currency="SYNTHETIC_CCY",
        aggregation_level=level,
        horizon_id="SYNTHETIC_HORIZON",
        reconciliation_key=f"key-{component_id}",
    )


def _expect_rejection(callable_: object, *, label: str) -> bool:
    try:
        callable_()  # type: ignore[operator]
    except ExecutionSemanticsError:
        return True
    raise RuntimeError(f"Synthetic rejection did not occur: {label}")


def build_safe_evidence() -> dict[str, object]:
    book = BookSnapshot(
        source_id="SYNTHETIC_BOOK",
        version_id="synthetic-version",
        best_bid=_price(PriceIdentity.BEST_BID, "99"),
        best_ask=_price(PriceIdentity.BEST_ASK, "101"),
        provider_timestamp_ms=BASE_MS,
        research_available_at_ms=BASE_MS + 2,
        depth=5,
        aggregation_mode="SYNTHETIC_DEPTH",
        tick_size=Decimal("0.1"),
    )
    partial = OrderExecution(
        order_id="synthetic-order",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        requested_quantity=Decimal("5"),
        limit_price=Decimal("101"),
        final_state=OrderState.PARTIALLY_FILLED,
        fills=(
            Fill(
                fill_id="synthetic-fill-1",
                trade_id="synthetic-trade-1",
                price=Decimal("100"),
                quantity=Decimal("1"),
                fill_time_ms=BASE_MS + 3,
                liquidity_role=LiquidityRole.TAKER,
            ),
            Fill(
                fill_id="synthetic-fill-2",
                trade_id="synthetic-trade-2",
                price=Decimal("101"),
                quantity=Decimal("2"),
                fill_time_ms=BASE_MS + 4,
                liquidity_role=LiquidityRole.MAKER,
            ),
        ),
        acknowledgement_accepted=True,
    )
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
    latency = timeline.latency_components_us()
    reference = _price(PriceIdentity.DECISION_REFERENCE, "100")
    buy_execution = _price(PriceIdentity.WEIGHTED_AVERAGE_FILL, "101", 10)
    sell_execution = _price(PriceIdentity.WEIGHTED_AVERAGE_FILL, "99", 10)

    base_context = CostAggregationContext(
        currency="SYNTHETIC_CCY",
        horizon_id="SYNTHETIC_HORIZON",
        quantity_convention="BASE_QUANTITY",
        instrument_version_id="synthetic-instrument-version",
    )
    cache = provider_cache_diagnostics((BASE_MS + 100, BASE_MS + 50, BASE_MS + 120))

    safe = {
        "schema_version": "1.0",
        "gate_id": "OKX_EXECUTABLE_PRICE_AND_COST_SEMANTICS_CONTRACT_V1",
        "issue_number": 57,
        "validation_mode": "SYNTHETIC_EXECUTION_RESPONSES_ONLY",
        "real_order_request_performed": False,
        "real_private_endpoint_called": False,
        "owner_fee_snapshot_status": "BLOCKED_OWNER_READ_ONLY_CREDENTIALS",
        "real_execution_inputs_status": "NOT_ADMITTED",
        "price_identity_rules": {
            "buy_executable_quote": PriceIdentity.BEST_ASK.value,
            "sell_executable_quote": PriceIdentity.BEST_BID.value,
            "midpoint_is_executable": False,
            "last_is_executable": False,
            "mark_is_executable": False,
            "index_is_executable": False,
            "limit_price_is_fill_price": False,
            "unfilled_quantity_receives_price": False,
        },
        "order_contract": {
            "supported_types": [value.value for value in OrderType],
            "maker_taker_from_actual_fill": True,
            "order_type_hardcodes_liquidity_role": False,
            "acknowledgement_is_execution": partial.acknowledgement_is_execution,
            "cancel_ack_is_final_cancellation": partial.cancellation_ack_is_final_state,
            "partial_fill_weighted_by_quantity": partial.weighted_average_fill_price is not None,
            "residual_quantity_preserved": partial.residual_quantity > 0,
        },
        "timing_contract": {
            "client_gateway_unit": "MICROSECONDS",
            "provider_order_fill_unit": "MILLISECONDS",
            "gateway_in_field": "inTime",
            "gateway_out_field": "outTime",
            "order_creation_field": "cTime",
            "order_update_field": "uTime",
            "fill_matching_field": "fillTime",
            "acknowledgement_time_used_as_fill_time": False,
            "all_synthetic_components_non_negative": all(
                value is None or value >= 0 for value in latency.values()
            ),
        },
        "slippage_contract": {
            "buy_adverse_direction": "EXECUTION_MINUS_REFERENCE",
            "sell_adverse_direction": "REFERENCE_MINUS_EXECUTION",
            "reference_identity_required": True,
            "reference_time_required": True,
            "buy_adverse_synthetic_check": directional_slippage(
                side=Side.BUY,
                reference=reference,
                execution=buy_execution,
            )
            > 0,
            "sell_adverse_synthetic_check": directional_slippage(
                side=Side.SELL,
                reference=reference,
                execution=sell_execution,
            )
            > 0,
        },
        "book_contract": {
            "source_version_required": True,
            "depth_required": True,
            "aggregation_mode_required": True,
            "provider_timestamp_required": True,
            "research_available_at_required": True,
            "stale_threshold_hidden_constant_allowed": False,
            "elp_eligibility_explicit": True,
            "speed_bump_flag_explicit": True,
            "tick_size_explicit": book.tick_size is not None,
            "buy_uses_ask": book.executable_quote(side=Side.BUY).identity == PriceIdentity.BEST_ASK,
            "sell_uses_bid": book.executable_quote(side=Side.SELL).identity
            == PriceIdentity.BEST_BID,
        },
        "provider_cache_contract": cache,
        "cost_component_contract": {
            "components": [value.value for value in CostComponentKind],
            "full_and_half_spread_both_counted": False,
            "implementation_shortfall_and_decomposition_both_counted": False,
            "position_aggregate_readds_fill_fee_or_funding": False,
            "mixed_currency_without_conversion": "REJECT",
            "mixed_level_without_transform": "REJECT",
            "duplicate_reconciliation_keys": "REJECT",
            "trading_fee_requires_owner_snapshot": True,
            "funding_requires_formula_version": True,
        },
        "synthetic_rejections": {
            "midpoint_as_executable": _expect_rejection(
                lambda: book.midpoint_reference().require_executable(side=Side.BUY),
                label="midpoint executable",
            ),
            "implementation_shortfall_double_count": _expect_rejection(
                lambda: aggregate_synthetic_costs(
                    context=base_context,
                    components=(
                        _component(
                            "shortfall",
                            CostComponentKind.IMPLEMENTATION_SHORTFALL,
                            "1",
                        ),
                        _component("impact", CostComponentKind.MARKET_IMPACT, "1"),
                    ),
                ),
                label="shortfall double count",
            ),
            "fee_without_owner_snapshot": _expect_rejection(
                lambda: aggregate_synthetic_costs(
                    context=base_context,
                    components=(_component("fee", CostComponentKind.TRADING_FEE, "1"),),
                ),
                label="fee snapshot",
            ),
            "funding_without_formula_version": _expect_rejection(
                lambda: aggregate_synthetic_costs(
                    context=base_context,
                    components=(
                        _component(
                            "funding",
                            CostComponentKind.FUNDING_CASHFLOW,
                            "1",
                            level=AggregationLevel.PER_BILL,
                        ),
                    ),
                ),
                label="funding formula",
            ),
        },
        "public_evidence_contains_real_prices": False,
        "public_evidence_contains_real_sizes": False,
        "public_evidence_contains_real_fills": False,
        "public_evidence_contains_real_costs": False,
        "public_evidence_contains_account_values": False,
        "public_evidence_contains_credentials": False,
        "authorizations": {
            "owner_fee_snapshot": False,
            "real_execution_input": False,
            "basis_computation": False,
            "funding_pnl_computation": False,
            "returns_computation": False,
            "transaction_cost_estimation": False,
            "empirical_fitting": False,
            "strategy_testing": False,
            "paper_trading": False,
            "live_trading": False,
            "capital_deployment": False,
            "report_2_4": False,
        },
        "economic_edge_verdict": "INCONCLUSIVE",
    }
    return safe


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    output = Path(args.output_dir) / "okx-execution-cost-semantics-safe-evidence.json"
    payload = build_safe_evidence()
    _atomic_write(
        output,
        (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
