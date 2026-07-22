"""Effective-dated crypto derivatives and two-leg accounting audits."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContractLinearity(StrEnum):
    LINEAR = "LINEAR"
    INVERSE = "INVERSE"
    QUANTO = "QUANTO"
    NA = "NA"


class InstrumentVersion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    venue_id: str
    instrument_id: str
    effective_from: datetime
    effective_to: datetime | None = None
    instrument_type: str
    base_currency: str
    quote_currency: str
    settlement_currency: str | None = None
    contract_multiplier: float | None = None
    linearity: ContractLinearity = ContractLinearity.NA
    tick_size: float = Field(gt=0)
    lot_size: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_interval(self) -> InstrumentVersion:
        if self.effective_to is not None and self.effective_to <= self.effective_from:
            raise ValueError("effective_to must follow effective_from")
        return self


def resolve_instrument_version(
    versions: list[InstrumentVersion],
    *,
    venue_id: str,
    instrument_id: str,
    timestamp: datetime,
) -> InstrumentVersion:
    candidates = [
        version
        for version in versions
        if version.venue_id == venue_id
        and version.instrument_id == instrument_id
        and version.effective_from <= timestamp
        and (version.effective_to is None or timestamp < version.effective_to)
    ]
    if len(candidates) != 1:
        raise ValueError(f"Expected one effective instrument version, found {len(candidates)}")
    return candidates[0]


def mark_index_basis(mark_price: pd.Series, index_price: pd.Series) -> pd.Series:
    mark = pd.to_numeric(mark_price, errors="raise").astype(float)
    index = pd.to_numeric(index_price, errors="raise").astype(float)
    values = np.column_stack([mark.to_numpy(), index.to_numpy()])
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("Mark and index prices must be finite and positive")
    return mark / index - 1.0


class LinearTwoLegInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spot_entry: float = Field(gt=0)
    spot_exit: float = Field(gt=0)
    spot_quantity: float = Field(gt=0)
    derivative_entry: float = Field(gt=0)
    derivative_exit: float = Field(gt=0)
    derivative_quantity: float = Field(gt=0)
    derivative_multiplier: float = Field(gt=0)
    derivative_side: int = -1
    funding_cashflow: float = 0.0
    trading_fees: float = Field(default=0.0, ge=0)
    spread_cost: float = Field(default=0.0, ge=0)
    slippage_cost: float = Field(default=0.0, ge=0)
    financing_cost: float = Field(default=0.0, ge=0)
    collateral_opportunity_cost: float = Field(default=0.0, ge=0)
    transfer_cost: float = Field(default=0.0, ge=0)
    orphan_leg_loss: float = Field(default=0.0, ge=0)
    stablecoin_haircut: float = Field(default=0.0, ge=0)
    venue_haircut: float = Field(default=0.0, ge=0)

    @model_validator(mode="after")
    def validate_side(self) -> LinearTwoLegInput:
        if self.derivative_side not in {-1, 1}:
            raise ValueError("derivative_side must be -1 or 1")
        return self


def linear_two_leg_pnl(inputs: LinearTwoLegInput) -> dict[str, float]:
    spot_pnl = inputs.spot_quantity * (inputs.spot_exit - inputs.spot_entry)
    derivative_pnl = (
        inputs.derivative_side
        * inputs.derivative_quantity
        * inputs.derivative_multiplier
        * (inputs.derivative_exit - inputs.derivative_entry)
    )
    total_cost = sum(
        [
            inputs.trading_fees,
            inputs.spread_cost,
            inputs.slippage_cost,
            inputs.financing_cost,
            inputs.collateral_opportunity_cost,
            inputs.transfer_cost,
            inputs.orphan_leg_loss,
            inputs.stablecoin_haircut,
            inputs.venue_haircut,
        ]
    )
    net = spot_pnl + derivative_pnl + inputs.funding_cashflow - total_cost
    return {
        "spot_pnl": float(spot_pnl),
        "derivative_pnl": float(derivative_pnl),
        "funding_cashflow": float(inputs.funding_cashflow),
        "total_cost": float(total_cost),
        "net_pnl": float(net),
    }
