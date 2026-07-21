"""Fail-closed executable-price, order-lifecycle, latency, and cost semantics.

This module is intentionally suitable for synthetic validation only.  It does not
place orders, call private endpoints, infer owner fee rates, or authorize economic
calculations from real market or account data.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from itertools import pairwise


class ExecutionSemanticsError(RuntimeError):
    """Raised when an execution or cost contract would become ambiguous."""


class Side(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class PriceIdentity(StrEnum):
    DECISION_REFERENCE = "DECISION_REFERENCE"
    BEST_BID = "BEST_BID"
    BEST_ASK = "BEST_ASK"
    MIDPOINT = "MIDPOINT"
    LAST_TRADED = "LAST_TRADED"
    ORDER_LIMIT = "ORDER_LIMIT"
    MARK = "MARK"
    INDEX = "INDEX"
    INDIVIDUAL_FILL = "INDIVIDUAL_FILL"
    WEIGHTED_AVERAGE_FILL = "WEIGHTED_AVERAGE_FILL"
    POSITION_ACCOUNTING = "POSITION_ACCOUNTING"


class OrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"
    POST_ONLY = "post_only"
    IOC = "ioc"
    FOK = "fok"
    OPTIMAL_LIMIT_IOC = "optimal_limit_ioc"


class LiquidityRole(StrEnum):
    MAKER = "M"
    TAKER = "T"


class OrderState(StrEnum):
    LIVE = "live"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"


class AggregationLevel(StrEnum):
    PER_FILL = "PER_FILL"
    PER_ORDER = "PER_ORDER"
    PER_BILL = "PER_BILL"
    POSITION_AGGREGATE = "POSITION_AGGREGATE"
    HORIZON_AGGREGATE = "HORIZON_AGGREGATE"


class CostComponentKind(StrEnum):
    QUOTED_HALF_SPREAD = "QUOTED_HALF_SPREAD"
    QUOTED_FULL_SPREAD = "QUOTED_FULL_SPREAD"
    ARRIVAL_SLIPPAGE = "ARRIVAL_SLIPPAGE"
    IMPLEMENTATION_SHORTFALL = "IMPLEMENTATION_SHORTFALL"
    MARKET_IMPACT = "MARKET_IMPACT"
    ADVERSE_SELECTION = "ADVERSE_SELECTION"
    LATENCY_DELAY = "LATENCY_DELAY"
    OPPORTUNITY_COST = "OPPORTUNITY_COST"
    TRADING_FEE = "TRADING_FEE"
    FUNDING_CASHFLOW = "FUNDING_CASHFLOW"
    LIQUIDATION_CASHFLOW = "LIQUIDATION_CASHFLOW"
    SETTLEMENT_CASHFLOW = "SETTLEMENT_CASHFLOW"
    POSITION_REALIZED_PNL = "POSITION_REALIZED_PNL"


EXECUTABLE_QUOTE_IDENTITIES: Mapping[Side, PriceIdentity] = {
    Side.BUY: PriceIdentity.BEST_ASK,
    Side.SELL: PriceIdentity.BEST_BID,
}

NON_EXECUTABLE_IDENTITIES = frozenset(
    {
        PriceIdentity.DECISION_REFERENCE,
        PriceIdentity.MIDPOINT,
        PriceIdentity.LAST_TRADED,
        PriceIdentity.ORDER_LIMIT,
        PriceIdentity.MARK,
        PriceIdentity.INDEX,
        PriceIdentity.POSITION_ACCOUNTING,
    }
)


@dataclass(frozen=True)
class PriceObservation:
    identity: PriceIdentity
    value: Decimal
    observed_at_ms: int
    source_id: str

    def __post_init__(self) -> None:
        if not self.value.is_finite() or self.value <= 0:
            raise ExecutionSemanticsError("Price values must be finite and positive")
        if self.observed_at_ms < 10**12 or self.observed_at_ms >= 10**14:
            raise ExecutionSemanticsError("observed_at_ms must be a millisecond timestamp")
        if not self.source_id.strip():
            raise ExecutionSemanticsError("source_id cannot be empty")

    def require_executable(self, *, side: Side) -> PriceObservation:
        expected = EXECUTABLE_QUOTE_IDENTITIES[side]
        if self.identity != expected:
            raise ExecutionSemanticsError(
                f"{self.identity.value} is not the executable quote identity for {side.value}"
            )
        return self


@dataclass(frozen=True)
class BookSnapshot:
    source_id: str
    version_id: str
    best_bid: PriceObservation
    best_ask: PriceObservation
    provider_timestamp_ms: int
    research_available_at_ms: int
    depth: int
    aggregation_mode: str
    checksum: str | None = None
    sequence_id: str | None = None
    elp_liquidity_included: bool = False
    elp_taker_access: bool = False
    speed_bump_applies: bool = False
    tick_size: Decimal | None = None
    stale_threshold_ms: int | None = None

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.version_id.strip():
            raise ExecutionSemanticsError("Book source and version identities are required")
        if self.best_bid.identity != PriceIdentity.BEST_BID:
            raise ExecutionSemanticsError("best_bid must have BEST_BID identity")
        if self.best_ask.identity != PriceIdentity.BEST_ASK:
            raise ExecutionSemanticsError("best_ask must have BEST_ASK identity")
        if self.best_bid.value >= self.best_ask.value:
            raise ExecutionSemanticsError("Crossed or locked synthetic books fail closed")
        if self.provider_timestamp_ms < 10**12:
            raise ExecutionSemanticsError("provider_timestamp_ms must be milliseconds")
        if self.research_available_at_ms < self.provider_timestamp_ms:
            raise ExecutionSemanticsError("research availability cannot precede provider time")
        if self.depth <= 0:
            raise ExecutionSemanticsError("Book depth must be positive")
        if not self.aggregation_mode.strip():
            raise ExecutionSemanticsError("Book aggregation mode is required")
        if self.tick_size is not None and (not self.tick_size.is_finite() or self.tick_size <= 0):
            raise ExecutionSemanticsError("tick_size must be finite and positive")
        if self.stale_threshold_ms is not None and self.stale_threshold_ms <= 0:
            raise ExecutionSemanticsError("stale_threshold_ms must be positive when supplied")
        if self.elp_taker_access and not self.elp_liquidity_included:
            raise ExecutionSemanticsError("ELP taker access requires an ELP-inclusive book")
        if self.speed_bump_applies and not self.elp_taker_access:
            raise ExecutionSemanticsError("A speed-bump flag requires ELP taker access")

    def executable_quote(self, *, side: Side) -> PriceObservation:
        observation = self.best_ask if side == Side.BUY else self.best_bid
        return observation.require_executable(side=side)

    def midpoint_reference(self) -> PriceObservation:
        return PriceObservation(
            identity=PriceIdentity.MIDPOINT,
            value=(self.best_bid.value + self.best_ask.value) / Decimal("2"),
            observed_at_ms=max(
                self.best_bid.observed_at_ms,
                self.best_ask.observed_at_ms,
            ),
            source_id=self.source_id,
        )

    def full_spread(self) -> Decimal:
        return self.best_ask.value - self.best_bid.value

    def half_spread(self) -> Decimal:
        return self.full_spread() / Decimal("2")


@dataclass(frozen=True)
class Fill:
    fill_id: str
    trade_id: str
    price: Decimal
    quantity: Decimal
    fill_time_ms: int
    liquidity_role: LiquidityRole

    def __post_init__(self) -> None:
        if not self.fill_id.strip() or not self.trade_id.strip():
            raise ExecutionSemanticsError("Fill and trade identities are required")
        if not self.price.is_finite() or self.price <= 0:
            raise ExecutionSemanticsError("Fill price must be finite and positive")
        if not self.quantity.is_finite() or self.quantity <= 0:
            raise ExecutionSemanticsError("Fill quantity must be finite and positive")
        if self.fill_time_ms < 10**12 or self.fill_time_ms >= 10**14:
            raise ExecutionSemanticsError("fill_time_ms must be milliseconds")


@dataclass(frozen=True)
class OrderExecution:
    order_id: str
    side: Side
    order_type: OrderType
    requested_quantity: Decimal
    final_state: OrderState
    fills: tuple[Fill, ...]
    limit_price: Decimal | None = None
    acknowledgement_accepted: bool = False
    cancellation_acknowledged: bool = False
    cancellation_confirmed: bool = False

    def __post_init__(self) -> None:
        if not self.order_id.strip():
            raise ExecutionSemanticsError("order_id cannot be empty")
        if not self.requested_quantity.is_finite() or self.requested_quantity <= 0:
            raise ExecutionSemanticsError("requested_quantity must be finite and positive")
        if self.order_type in {OrderType.LIMIT, OrderType.POST_ONLY, OrderType.IOC, OrderType.FOK}:
            if self.limit_price is None:
                raise ExecutionSemanticsError(f"{self.order_type.value} requires a limit price")
        elif self.limit_price is not None:
            raise ExecutionSemanticsError(
                f"{self.order_type.value} must not silently carry a limit price"
            )
        if self.limit_price is not None and (
            not self.limit_price.is_finite() or self.limit_price <= 0
        ):
            raise ExecutionSemanticsError("limit_price must be finite and positive")
        fill_ids = [fill.fill_id for fill in self.fills]
        trade_ids = [fill.trade_id for fill in self.fills]
        if len(fill_ids) != len(set(fill_ids)) or len(trade_ids) != len(set(trade_ids)):
            raise ExecutionSemanticsError("Fill and trade identities must be unique")
        fill_times = [fill.fill_time_ms for fill in self.fills]
        if fill_times != sorted(fill_times):
            raise ExecutionSemanticsError("Fills must be ordered by fillTime")
        if self.filled_quantity > self.requested_quantity:
            raise ExecutionSemanticsError("Filled quantity cannot exceed requested quantity")
        if self.final_state == OrderState.FILLED and self.residual_quantity != 0:
            raise ExecutionSemanticsError("A filled order cannot retain residual quantity")
        if self.final_state == OrderState.PARTIALLY_FILLED and not (
            0 < self.filled_quantity < self.requested_quantity
        ):
            raise ExecutionSemanticsError("Partially filled state requires a partial quantity")
        if self.final_state == OrderState.REJECTED and self.fills:
            raise ExecutionSemanticsError("A rejected order cannot contain fills")
        if self.cancellation_confirmed and self.final_state != OrderState.CANCELED:
            raise ExecutionSemanticsError("Cancellation confirmation requires canceled final state")
        if self.final_state == OrderState.CANCELED and not self.cancellation_confirmed:
            raise ExecutionSemanticsError("Canceled final state requires confirmation")
        if self.cancellation_confirmed and not self.cancellation_acknowledged:
            raise ExecutionSemanticsError("Cancellation confirmation requires acknowledgement")

    @property
    def filled_quantity(self) -> Decimal:
        return sum((fill.quantity for fill in self.fills), Decimal("0"))

    @property
    def residual_quantity(self) -> Decimal:
        return self.requested_quantity - self.filled_quantity

    @property
    def weighted_average_fill_price(self) -> Decimal | None:
        if not self.fills:
            return None
        notional = sum((fill.price * fill.quantity for fill in self.fills), Decimal("0"))
        return notional / self.filled_quantity

    @property
    def execution_confirmed(self) -> bool:
        return bool(self.fills)

    @property
    def acknowledgement_is_execution(self) -> bool:
        return False

    @property
    def cancellation_ack_is_final_state(self) -> bool:
        return False

    def liquidity_roles(self) -> tuple[LiquidityRole, ...]:
        return tuple(fill.liquidity_role for fill in self.fills)


@dataclass(frozen=True)
class OrderTimeline:
    client_decision_us: int
    client_submit_us: int
    gateway_in_us: int
    gateway_out_us: int
    client_receive_us: int
    order_create_ms: int
    order_update_ms: int
    fill_times_ms: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        microsecond_fields = (
            self.client_decision_us,
            self.client_submit_us,
            self.gateway_in_us,
            self.gateway_out_us,
            self.client_receive_us,
        )
        if any(value < 10**15 or value >= 10**17 for value in microsecond_fields):
            raise ExecutionSemanticsError("Client and gateway clocks must be microseconds")
        if list(microsecond_fields) != sorted(microsecond_fields):
            raise ExecutionSemanticsError("Client and gateway clocks are reordered")
        if not (10**12 <= self.order_create_ms < 10**14):
            raise ExecutionSemanticsError("order_create_ms must be milliseconds")
        if not (10**12 <= self.order_update_ms < 10**14):
            raise ExecutionSemanticsError("order_update_ms must be milliseconds")
        if self.order_update_ms < self.order_create_ms:
            raise ExecutionSemanticsError("Order update cannot precede order creation")
        if self.order_create_ms * 1000 < self.gateway_in_us:
            raise ExecutionSemanticsError("Order creation cannot precede gateway receipt")
        if tuple(sorted(self.fill_times_ms)) != self.fill_times_ms:
            raise ExecutionSemanticsError("fillTime values must be ordered")
        for fill_time in self.fill_times_ms:
            if not (self.order_create_ms <= fill_time <= self.order_update_ms):
                raise ExecutionSemanticsError(
                    "Every fillTime must be between order creation and last update"
                )

    def latency_components_us(self) -> Mapping[str, int | None]:
        first_fill = self.fill_times_ms[0] * 1000 if self.fill_times_ms else None
        last_fill = self.fill_times_ms[-1] * 1000 if self.fill_times_ms else None
        return {
            "client_decision_to_submit": self.client_submit_us - self.client_decision_us,
            "client_submit_to_gateway_in": self.gateway_in_us - self.client_submit_us,
            "gateway_processing": self.gateway_out_us - self.gateway_in_us,
            "gateway_out_to_client_receive": self.client_receive_us - self.gateway_out_us,
            "client_decision_to_first_fill": (
                first_fill - self.client_decision_us if first_fill is not None else None
            ),
            "client_decision_to_last_fill": (
                last_fill - self.client_decision_us if last_fill is not None else None
            ),
            "order_live_duration": (self.order_update_ms - self.order_create_ms) * 1000,
        }


@dataclass(frozen=True)
class CostComponent:
    component_id: str
    kind: CostComponentKind
    amount: Decimal
    currency: str
    aggregation_level: AggregationLevel
    horizon_id: str
    reconciliation_key: str
    parent_aggregate_id: str | None = None

    def __post_init__(self) -> None:
        if not self.component_id.strip() or not self.reconciliation_key.strip():
            raise ExecutionSemanticsError("Cost component identities are required")
        if not self.amount.is_finite():
            raise ExecutionSemanticsError("Cost amount must be finite")
        if not self.currency.strip() or not self.horizon_id.strip():
            raise ExecutionSemanticsError("Currency and horizon identities are required")


@dataclass(frozen=True)
class CostAggregationContext:
    currency: str
    horizon_id: str
    quantity_convention: str
    instrument_version_id: str
    owner_fee_snapshot_id: str | None = None
    funding_formula_version_id: str | None = None
    conversion_contract_id: str | None = None
    reconciliation_transform_id: str | None = None

    def __post_init__(self) -> None:
        required = (
            self.currency,
            self.horizon_id,
            self.quantity_convention,
            self.instrument_version_id,
        )
        if any(not value.strip() for value in required):
            raise ExecutionSemanticsError("Cost aggregation context is incomplete")


def directional_slippage(
    *,
    side: Side,
    reference: PriceObservation,
    execution: PriceObservation,
) -> Decimal:
    if execution.identity not in {
        PriceIdentity.INDIVIDUAL_FILL,
        PriceIdentity.WEIGHTED_AVERAGE_FILL,
    }:
        raise ExecutionSemanticsError("Slippage execution must use a fill identity")
    if reference.identity in {
        PriceIdentity.INDIVIDUAL_FILL,
        PriceIdentity.WEIGHTED_AVERAGE_FILL,
        PriceIdentity.POSITION_ACCOUNTING,
    }:
        raise ExecutionSemanticsError("Slippage reference must be an explicit non-fill reference")
    if execution.observed_at_ms < reference.observed_at_ms:
        raise ExecutionSemanticsError("Execution cannot precede the admitted reference time")
    return (
        execution.value - reference.value if side == Side.BUY else reference.value - execution.value
    )


def provider_cache_diagnostics(
    provider_timestamps_ms_in_request_order: Sequence[int],
) -> Mapping[str, object]:
    if not provider_timestamps_ms_in_request_order:
        raise ExecutionSemanticsError("At least one provider timestamp is required")
    if any(value < 10**12 or value >= 10**14 for value in provider_timestamps_ms_in_request_order):
        raise ExecutionSemanticsError("Provider timestamps must be milliseconds")
    monotonic = all(
        current >= previous
        for previous, current in pairwise(provider_timestamps_ms_in_request_order)
    )
    return {
        "monotonic_in_request_order": monotonic,
        "request_order_rewritten": False,
        "later_response_may_have_earlier_provider_time": True,
        "spread_ms": max(provider_timestamps_ms_in_request_order)
        - min(provider_timestamps_ms_in_request_order),
    }


def aggregate_synthetic_costs(
    *,
    context: CostAggregationContext,
    components: Iterable[CostComponent],
) -> Decimal:
    items = tuple(components)
    if not items:
        raise ExecutionSemanticsError("At least one cost component is required")
    component_ids = [item.component_id for item in items]
    reconciliation_keys = [item.reconciliation_key for item in items]
    if len(component_ids) != len(set(component_ids)):
        raise ExecutionSemanticsError("Duplicate cost component identity")
    if len(reconciliation_keys) != len(set(reconciliation_keys)):
        raise ExecutionSemanticsError("Duplicate reconciliation key")
    if any(item.horizon_id != context.horizon_id for item in items):
        raise ExecutionSemanticsError("Mixed accounting horizons require a transform")
    currencies = {item.currency for item in items}
    if currencies != {context.currency} and context.conversion_contract_id is None:
        raise ExecutionSemanticsError("Mixed currencies require an admitted conversion contract")
    levels = {item.aggregation_level for item in items}
    if len(levels) > 1 and context.reconciliation_transform_id is None:
        raise ExecutionSemanticsError("Mixed aggregation levels require a reconciliation transform")
    kinds = {item.kind for item in items}
    if CostComponentKind.TRADING_FEE in kinds and context.owner_fee_snapshot_id is None:
        raise ExecutionSemanticsError("Trading fees require an owner-account fee snapshot")
    if CostComponentKind.FUNDING_CASHFLOW in kinds and context.funding_formula_version_id is None:
        raise ExecutionSemanticsError("Funding requires a formula-version identity")
    if CostComponentKind.POSITION_REALIZED_PNL in kinds and kinds.intersection(
        {CostComponentKind.TRADING_FEE, CostComponentKind.FUNDING_CASHFLOW}
    ):
        raise ExecutionSemanticsError(
            "Position realized PnL cannot be combined with fee or funding components again"
        )
    if CostComponentKind.IMPLEMENTATION_SHORTFALL in kinds and kinds.intersection(
        {
            CostComponentKind.ARRIVAL_SLIPPAGE,
            CostComponentKind.MARKET_IMPACT,
            CostComponentKind.LATENCY_DELAY,
            CostComponentKind.OPPORTUNITY_COST,
        }
    ):
        raise ExecutionSemanticsError(
            "Implementation shortfall cannot coexist with its decomposed components"
        )
    if (
        CostComponentKind.QUOTED_FULL_SPREAD in kinds
        and CostComponentKind.QUOTED_HALF_SPREAD in kinds
    ):
        raise ExecutionSemanticsError("Full and half spread cannot both be counted")
    return sum((item.amount for item in items), Decimal("0"))
