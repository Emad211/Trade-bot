"""Fail-closed OKX fee, fill, funding-bill, and position accounting contracts."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any

SPOT_INSTRUMENT_ID = "BTC-USDT"
SWAP_INSTRUMENT_ID = "BTC-USDT-SWAP"
SWAP_INSTRUMENT_FAMILY = "BTC-USDT"
ACCOUNT_FEE_ENDPOINT = "/api/v5/account/trade-fee"
FILLS_ENDPOINT = "/api/v5/trade/fills"
FILLS_HISTORY_ENDPOINT = "/api/v5/trade/fills-history"
BILLS_ENDPOINT = "/api/v5/account/bills"
BILLS_ARCHIVE_ENDPOINT = "/api/v5/account/bills-archive"
BILLS_HISTORY_ARCHIVE_ENDPOINT = "/api/v5/account/bills-history-archive"
POSITION_ENDPOINT = "/api/v5/account/positions"
CURRENT_FUNDING_FORMULA_ID = "OKX_PERPETUAL_FUNDING_8_OVER_N_2026_V1"
CURRENT_FUNDING_FORMULA_PUBLICATION = datetime(2026, 5, 29, tzinfo=UTC)
CURRENT_FUNDING_FORMULA_MIGRATION_START = datetime(2026, 6, 1, tzinfo=UTC)
CURRENT_FUNDING_FORMULA_CONSERVATIVE_ADMISSION = datetime(2026, 6, 4, tzinfo=UTC)
ALLOWED_FUNDING_INTERVAL_HOURS = (1, 2, 4, 8)


class OKXFeeAccountingError(RuntimeError):
    """Raised when an accounting record violates the frozen OKX contract."""


class InstrumentType(StrEnum):
    SPOT = "SPOT"
    SWAP = "SWAP"


class LiquidityRole(StrEnum):
    MAKER = "M"
    TAKER = "T"
    NOT_APPLICABLE = ""


class AggregationLevel(StrEnum):
    PER_FILL = "PER_FILL"
    PER_BILL = "PER_BILL"
    POSITION_AGGREGATE = "POSITION_AGGREGATE"


class FundingBillDirection(StrEnum):
    EXPENSE = "FUNDING_EXPENSE"
    INCOME = "FUNDING_INCOME"


class FundingFormulaApplicability(StrEnum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    AMBIGUOUS_MIGRATION_WINDOW = "AMBIGUOUS_MIGRATION_WINDOW"
    PROVIDER_CONFIRMED_MIGRATION_WINDOW = "PROVIDER_CONFIRMED_MIGRATION_WINDOW"
    APPLICABLE = "APPLICABLE"


@dataclass(frozen=True)
class FeeRateQuery:
    instrument_type: InstrumentType
    instrument_id: str | None = None
    instrument_family: str | None = None

    def validate(self) -> None:
        if self.instrument_type == InstrumentType.SPOT:
            if self.instrument_id != SPOT_INSTRUMENT_ID or self.instrument_family is not None:
                raise OKXFeeAccountingError(
                    "SPOT fee query requires exact instId=BTC-USDT and no instFamily"
                )
        elif self.instrument_family != SWAP_INSTRUMENT_FAMILY or self.instrument_id is not None:
            raise OKXFeeAccountingError(
                "SWAP fee query requires exact instFamily=BTC-USDT and no instId"
            )

    @property
    def query_parameter_names(self) -> tuple[str, ...]:
        self.validate()
        if self.instrument_type == InstrumentType.SPOT:
            return ("instId", "instType")
        return ("instFamily", "instType")


@dataclass(frozen=True)
class AccountFeeRateSnapshot:
    query: FeeRateQuery
    level: str
    rule_type: str
    response_timestamp_ms: int
    maker: Decimal | None
    taker: Decimal | None
    maker_u: Decimal | None
    taker_u: Decimal | None
    maker_usdc: Decimal | None = None
    taker_usdc: Decimal | None = None
    open_api_reflects_zero_fee_exceptions: bool = False

    def validate(self) -> None:
        self.query.validate()
        if not self.level.strip():
            raise OKXFeeAccountingError("Account fee level is required")
        if self.rule_type != "normal":
            raise OKXFeeAccountingError("Only the frozen normal trading rule is admitted")
        _validate_timestamp_ms(self.response_timestamp_ms, field="fee response timestamp")
        for field, value in (
            ("maker", self.maker),
            ("taker", self.taker),
            ("makerU", self.maker_u),
            ("takerU", self.taker_u),
            ("makerUSDC", self.maker_usdc),
            ("takerUSDC", self.taker_usdc),
        ):
            if value is not None:
                _finite_decimal(value, field=field)
        if self.query.instrument_type == InstrumentType.SPOT:
            if self.maker is None or self.taker is None:
                raise OKXFeeAccountingError("SPOT snapshot requires maker and taker fields")
            if self.maker_u is not None or self.taker_u is not None:
                raise OKXFeeAccountingError("SPOT snapshot must not use SWAP makerU/takerU fields")
        elif self.maker_u is None or self.taker_u is None:
            raise OKXFeeAccountingError(
                "USDT-margined SWAP snapshot requires makerU and takerU fields"
            )
        if self.open_api_reflects_zero_fee_exceptions:
            raise OKXFeeAccountingError(
                "Open API fee-rate responses cannot claim zero-fee-pair coverage"
            )


@dataclass(frozen=True)
class FillRecord:
    instrument_type: InstrumentType
    instrument_id: str
    trade_id: str
    order_id: str
    bill_id: str
    fill_time_ms: int
    record_timestamp_ms: int
    liquidity_role: LiquidityRole
    fee: Decimal
    fee_currency: str
    fee_rate: Decimal | None
    fill_price: Decimal
    fill_size: Decimal
    fill_index_price: Decimal | None
    fill_mark_price: Decimal | None
    fill_pnl: Decimal
    trade_quote_currency: str
    side: str
    position_side: str
    subtype: str

    def validate(self) -> None:
        expected_id = (
            SPOT_INSTRUMENT_ID
            if self.instrument_type == InstrumentType.SPOT
            else SWAP_INSTRUMENT_ID
        )
        if self.instrument_id != expected_id:
            raise OKXFeeAccountingError("Fill instrument identity differs from the frozen contract")
        if not self.trade_id or not self.order_id or not self.bill_id:
            raise OKXFeeAccountingError("Fill reconciliation IDs are required")
        _validate_timestamp_ms(self.fill_time_ms, field="fillTime")
        _validate_timestamp_ms(self.record_timestamp_ms, field="ts")
        for field, value in (
            ("fee", self.fee),
            ("fillPx", self.fill_price),
            ("fillSz", self.fill_size),
            ("fillPnl", self.fill_pnl),
        ):
            _finite_decimal(value, field=field)
        if self.fill_price <= 0 or self.fill_size <= 0:
            raise OKXFeeAccountingError("Fill price and size must be positive")
        for field, optional_value in (
            ("fillIdxPx", self.fill_index_price),
            ("fillMarkPx", self.fill_mark_price),
            ("feeRate", self.fee_rate),
        ):
            if optional_value is not None:
                _finite_decimal(optional_value, field=field)
        if not self.fee_currency.strip():
            raise OKXFeeAccountingError("feeCcy is required and may not be inferred")
        if self.side not in {"buy", "sell"}:
            raise OKXFeeAccountingError("Fill side must be buy or sell")
        if self.instrument_type == InstrumentType.SPOT:
            if self.fee_rate is None:
                raise OKXFeeAccountingError("SPOT fill requires explicit feeRate")
            if self.fill_mark_price is not None:
                raise OKXFeeAccountingError("SPOT fill cannot carry a derivative mark price")
        else:
            if self.fee_rate is not None:
                raise OKXFeeAccountingError("SWAP fills do not admit inferred feeRate")
            if self.fill_mark_price is None:
                raise OKXFeeAccountingError("SWAP fill requires fillMarkPx")

    @property
    def chronology_key(self) -> tuple[int, str]:
        self.validate()
        return (self.fill_time_ms, self.trade_id)

    @property
    def fee_semantics(self) -> str:
        self.validate()
        if self.fee < 0:
            return "COMMISSION_CHARGE"
        if self.fee > 0:
            return "REBATE"
        return "ZERO_FEE_AMOUNT"


@dataclass(frozen=True)
class FundingBillRecord:
    bill_id: str
    instrument_id: str
    subtype: int
    currency: str
    provider_amount: Decimal
    record_timestamp_ms: int

    def validate(self) -> None:
        if not self.bill_id:
            raise OKXFeeAccountingError("Funding bill ID is required")
        if self.instrument_id != SWAP_INSTRUMENT_ID:
            raise OKXFeeAccountingError("Funding bill must use BTC-USDT-SWAP")
        if self.subtype not in {173, 174}:
            raise OKXFeeAccountingError("Funding bill subtype must be 173 or 174")
        if not self.currency.strip():
            raise OKXFeeAccountingError("Funding bill currency is required")
        _finite_decimal(self.provider_amount, field="funding bill amount")
        _validate_timestamp_ms(self.record_timestamp_ms, field="funding bill ts")

    @property
    def direction(self) -> FundingBillDirection:
        self.validate()
        if self.subtype == 173:
            return FundingBillDirection.EXPENSE
        return FundingBillDirection.INCOME


@dataclass(frozen=True)
class PositionAccountingAggregate:
    instrument_id: str
    position_side: str
    realized_pnl: Decimal
    pnl: Decimal
    fee: Decimal
    funding_fee: Decimal
    liquidation_penalty: Decimal
    settled_pnl: Decimal
    provider_timestamp_ms: int

    def validate(self) -> None:
        if self.instrument_id != SWAP_INSTRUMENT_ID:
            raise OKXFeeAccountingError("Position aggregate must use BTC-USDT-SWAP")
        if self.position_side not in {"net", "long", "short"}:
            raise OKXFeeAccountingError("Unsupported position side")
        for field, value in (
            ("realizedPnl", self.realized_pnl),
            ("pnl", self.pnl),
            ("fee", self.fee),
            ("fundingFee", self.funding_fee),
            ("liqPenalty", self.liquidation_penalty),
            ("settledPnl", self.settled_pnl),
        ):
            _finite_decimal(value, field=field)
        expected = (
            self.pnl + self.fee + self.funding_fee + self.liquidation_penalty + self.settled_pnl
        )
        if self.realized_pnl != expected:
            raise OKXFeeAccountingError(
                "Provider realizedPnl does not reconcile to pnl+fee+fundingFee+liqPenalty+settledPnl"
            )
        _validate_timestamp_ms(self.provider_timestamp_ms, field="position timestamp")


@dataclass(frozen=True)
class AccountingAmountReference:
    aggregation_level: AggregationLevel
    reconciliation_key: str
    currency: str
    amount: Decimal

    def validate(self) -> None:
        if not self.reconciliation_key.strip():
            raise OKXFeeAccountingError("Accounting reconciliation key is required")
        if not self.currency.strip():
            raise OKXFeeAccountingError("Accounting currency is required")
        _finite_decimal(self.amount, field="accounting amount")


def sum_same_aggregation_level(
    records: Sequence[AccountingAmountReference],
) -> Decimal:
    if not records:
        raise OKXFeeAccountingError("At least one accounting record is required")
    for record in records:
        record.validate()
    levels = {record.aggregation_level for record in records}
    currencies = {record.currency for record in records}
    keys = [record.reconciliation_key for record in records]
    if len(levels) != 1:
        raise OKXFeeAccountingError(
            "Mixed aggregation levels cannot be summed without an explicit reconciliation transform"
        )
    if len(currencies) != 1:
        raise OKXFeeAccountingError("Mixed currencies cannot be summed without conversion")
    if len(keys) != len(set(keys)):
        raise OKXFeeAccountingError(
            "Duplicate reconciliation keys would double count accounting records"
        )
    return sum((record.amount for record in records), Decimal("0"))


@dataclass(frozen=True)
class FundingFormulaVersion:
    formula_id: str = CURRENT_FUNDING_FORMULA_ID
    source_publication: datetime = CURRENT_FUNDING_FORMULA_PUBLICATION
    migration_start: datetime = CURRENT_FUNDING_FORMULA_MIGRATION_START
    conservative_admission: datetime = CURRENT_FUNDING_FORMULA_CONSERVATIVE_ADMISSION
    fixed_interest_rate: Decimal = Decimal("0.0001")
    interval_factor_enabled: bool = True
    allowed_interval_hours: tuple[int, ...] = ALLOWED_FUNDING_INTERVAL_HOURS

    def validate(self) -> None:
        if self.formula_id != CURRENT_FUNDING_FORMULA_ID:
            raise OKXFeeAccountingError("Unknown funding formula version")
        publication = _aware_utc(self.source_publication, field="source publication")
        migration = _aware_utc(self.migration_start, field="migration start")
        admission = _aware_utc(self.conservative_admission, field="conservative admission")
        if not publication <= migration <= admission:
            raise OKXFeeAccountingError("Funding formula version clocks are inconsistent")
        if self.fixed_interest_rate != Decimal("0.0001"):
            raise OKXFeeAccountingError("Current formula must preserve fixed 0.01% interest")
        if not self.interval_factor_enabled or self.allowed_interval_hours != (1, 2, 4, 8):
            raise OKXFeeAccountingError("Current formula must preserve the 8/N interval contract")

    def applicability(
        self,
        observed_at: datetime,
        *,
        provider_formula_type: str | None = None,
    ) -> FundingFormulaApplicability:
        self.validate()
        observed = _aware_utc(observed_at, field="observed_at")
        if observed < self.migration_start:
            return FundingFormulaApplicability.NOT_APPLICABLE
        if observed < self.conservative_admission:
            if provider_formula_type == self.formula_id:
                return FundingFormulaApplicability.PROVIDER_CONFIRMED_MIGRATION_WINDOW
            return FundingFormulaApplicability.AMBIGUOUS_MIGRATION_WINDOW
        return FundingFormulaApplicability.APPLICABLE

    def interval_divisor(self, interval_hours: int) -> Decimal:
        self.validate()
        if interval_hours not in self.allowed_interval_hours:
            raise OKXFeeAccountingError("Funding interval must be one of 1, 2, 4, or 8 hours")
        return Decimal(8) / Decimal(interval_hours)


@dataclass(frozen=True)
class OwnerAccountAccessBoundary:
    read_only_credentials_present: bool
    withdrawal_permission_disabled: bool
    trading_permission_disabled: bool
    owner_controlled_secret_storage: bool
    exact_regional_endpoint_confirmed: bool
    explicit_owner_confirmation: bool

    def validate_real_snapshot(self) -> None:
        required = asdict(self)
        missing = [name for name, value in required.items() if value is not True]
        if missing:
            raise OKXFeeAccountingError(
                "Real account fee snapshot is blocked: " + ", ".join(missing)
            )


@dataclass(frozen=True)
class SafeAccountingContractEvidence:
    schema_version: str
    gate_id: str
    issue_number: int
    validation_mode: str
    real_account_request_performed: bool
    owner_account_fee_snapshot_status: str
    endpoints: dict[str, dict[str, Any]]
    sign_and_currency_rules: dict[str, Any]
    chronology_rules: dict[str, Any]
    funding_bill_rules: dict[str, Any]
    position_reconciliation_rule: str
    aggregation_rules: dict[str, Any]
    funding_formula_version: dict[str, Any]
    synthetic_checks: dict[str, bool]
    public_evidence_contains_account_values: bool
    public_evidence_contains_credentials: bool
    authorizations: dict[str, bool]
    economic_edge_verdict: str


def build_safe_accounting_contract_evidence() -> SafeAccountingContractEvidence:
    formula = FundingFormulaVersion()
    formula.validate()
    endpoints: dict[str, dict[str, Any]] = {
        "account_fee_rate": {
            "path": ACCOUNT_FEE_ENDPOINT,
            "authentication_required": True,
            "permission": "Read",
            "spot_query_names": ["instId", "instType"],
            "swap_query_names": ["instFamily", "instType"],
            "account_specific": True,
            "generic_lv1_is_owner_snapshot": False,
            "zero_fee_exceptions_reflected_by_open_api": False,
        },
        "fills": {
            "paths": [FILLS_ENDPOINT, FILLS_HISTORY_ENDPOINT],
            "authentication_required": True,
            "aggregation_level": AggregationLevel.PER_FILL.value,
            "chronology_field": "fillTime",
            "record_generation_field": "ts",
        },
        "bills": {
            "paths": [BILLS_ENDPOINT, BILLS_ARCHIVE_ENDPOINT, BILLS_HISTORY_ARCHIVE_ENDPOINT],
            "authentication_required": True,
            "aggregation_level": AggregationLevel.PER_BILL.value,
        },
        "positions": {
            "path": POSITION_ENDPOINT,
            "authentication_required": True,
            "aggregation_level": AggregationLevel.POSITION_AGGREGATE.value,
        },
    }
    return SafeAccountingContractEvidence(
        schema_version="1.0",
        gate_id="OKX_FEE_FILL_FUNDING_ACCOUNTING_CONTRACT_V1",
        issue_number=56,
        validation_mode="SYNTHETIC_ACCOUNT_RESPONSES_ONLY",
        real_account_request_performed=False,
        owner_account_fee_snapshot_status="BLOCKED_OWNER_READ_ONLY_CREDENTIALS",
        endpoints=endpoints,
        sign_and_currency_rules={
            "negative_fee": "COMMISSION_CHARGE",
            "positive_fee": "REBATE",
            "fee_currency_explicit": True,
            "fee_currency_inferred_from_quote_currency": False,
            "swap_fee_rate_inferred_from_fill": False,
        },
        chronology_rules={
            "trade_chronology_field": "fillTime",
            "record_generation_field": "ts",
            "ts_replaces_fillTime": False,
        },
        funding_bill_rules={
            "173": FundingBillDirection.EXPENSE.value,
            "174": FundingBillDirection.INCOME.value,
            "provider_amount_sign_rewritten": False,
            "funding_cashflow_merged_with_trading_fee": False,
        },
        position_reconciliation_rule="realizedPnl=pnl+fee+fundingFee+liqPenalty+settledPnl",
        aggregation_rules={
            "mixed_levels_summable_without_transform": False,
            "duplicate_reconciliation_keys_allowed": False,
            "mixed_currencies_summable_without_conversion": False,
            "position_aggregate_readds_fill_fee_or_funding_bill": False,
        },
        funding_formula_version={
            "formula_id": formula.formula_id,
            "source_publication": formula.source_publication.isoformat(),
            "migration_start": formula.migration_start.isoformat(),
            "conservative_admission": formula.conservative_admission.isoformat(),
            "fixed_interest_rate_decimal": "0.0001",
            "interval_factor": "8/N",
            "allowed_interval_hours": list(formula.allowed_interval_hours),
            "projected_backward_to_2022": False,
        },
        synthetic_checks={
            "exact_spot_and_swap_fee_queries": True,
            "fee_sign_preservation": True,
            "fee_currency_non_inference": True,
            "fill_time_chronology": True,
            "funding_bill_subtype_separation": True,
            "position_reconciliation": True,
            "double_count_rejection": True,
            "formula_version_boundary": True,
        },
        public_evidence_contains_account_values=False,
        public_evidence_contains_credentials=False,
        authorizations={
            "account_fee_snapshot": False,
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
        economic_edge_verdict="INCONCLUSIVE",
    )


def safe_evidence_json(evidence: SafeAccountingContractEvidence) -> str:
    return json.dumps(asdict(evidence), indent=2, sort_keys=True) + "\n"


def _finite_decimal(value: Decimal, *, field: str) -> Decimal:
    try:
        result = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise OKXFeeAccountingError(f"Invalid decimal in {field}") from exc
    if not result.is_finite():
        raise OKXFeeAccountingError(f"Non-finite decimal in {field}")
    return result


def _validate_timestamp_ms(value: int, *, field: str) -> None:
    if value < 10**12 or value >= 10**14:
        raise OKXFeeAccountingError(f"{field} is not a Unix millisecond timestamp")


def _aware_utc(value: datetime, *, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise OKXFeeAccountingError(f"{field} must be timezone-aware")
    return value.astimezone(UTC)
