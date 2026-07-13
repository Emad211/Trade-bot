"""Typed application configuration."""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    """Base class that rejects unknown configuration keys."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class MarketConfig(StrictModel):
    symbol: str = "BTC/USD"
    timeframe: str = "4h"
    periods_per_year: int = Field(default=2190, gt=0)


class StrategyConfig(StrictModel):
    ema_fast: int = Field(default=20, ge=2)
    ema_slow: int = Field(default=100, ge=3)
    donchian_entry: int = Field(default=40, ge=2)
    donchian_exit: int = Field(default=20, ge=2)
    atr_window: int = Field(default=14, ge=2)
    volatility_window: int = Field(default=30, ge=3)
    max_annualized_volatility: float = Field(default=1.20, gt=0)

    @model_validator(mode="after")
    def validate_windows(self) -> "StrategyConfig":
        if self.ema_fast >= self.ema_slow:
            raise ValueError("ema_fast must be smaller than ema_slow")
        return self


class RiskConfig(StrictModel):
    target_annualized_volatility: float = Field(default=0.35, gt=0)
    max_exposure: float = Field(default=0.35, gt=0, le=1)
    min_exposure: float = Field(default=0.05, ge=0, le=1)

    @model_validator(mode="after")
    def validate_exposure(self) -> "RiskConfig":
        if self.min_exposure > self.max_exposure:
            raise ValueError("min_exposure cannot exceed max_exposure")
        return self


class CostConfig(StrictModel):
    fee_bps: float = Field(default=15.0, ge=0)
    slippage_bps: float = Field(default=10.0, ge=0)

    @property
    def one_way_rate(self) -> float:
        return (self.fee_bps + self.slippage_bps) / 10_000.0


class BacktestConfig(StrictModel):
    initial_cash: float = Field(default=10_000.0, gt=0)
    min_history_bars: int = Field(default=150, ge=10)


class AppConfig(StrictModel):
    market: MarketConfig = MarketConfig()
    strategy: StrategyConfig = StrategyConfig()
    risk: RiskConfig = RiskConfig()
    costs: CostConfig = CostConfig()
    backtest: BacktestConfig = BacktestConfig()


def load_config(path: str | Path) -> AppConfig:
    """Load and validate a YAML configuration file."""

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    return AppConfig.model_validate(raw)
