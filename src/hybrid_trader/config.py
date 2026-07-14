"""Typed application configuration."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hybrid_trader.data.timeframe import timeframe_to_timedelta


class StrictModel(BaseModel):
    """Base class that rejects unknown configuration keys."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class MarketConfig(StrictModel):
    symbol: str = "BTC/USD"
    timeframe: str = "4h"
    periods_per_year: int = Field(default=2190, gt=0)

    @field_validator("timeframe")
    @classmethod
    def validate_timeframe(cls, value: str) -> str:
        timeframe_to_timedelta(value)
        return value.strip()


class DataConfig(StrictModel):
    source_latency_seconds: float = Field(default=30.0, ge=0)
    require_regular_bars: bool = True
    drop_incomplete_last_bar: bool = True


class StrategyConfig(StrictModel):
    ema_fast: int = Field(default=20, ge=2)
    ema_slow: int = Field(default=100, ge=3)
    donchian_entry: int = Field(default=40, ge=2)
    donchian_exit: int = Field(default=20, ge=2)
    atr_window: int = Field(default=14, ge=2)
    volatility_window: int = Field(default=30, ge=3)
    max_annualized_volatility: float = Field(default=1.20, gt=0)

    @model_validator(mode="after")
    def validate_windows(self) -> StrategyConfig:
        if self.ema_fast >= self.ema_slow:
            raise ValueError("ema_fast must be smaller than ema_slow")
        return self


class FeatureConfig(StrictModel):
    return_windows: tuple[int, ...] = (1, 2, 6, 24)
    volatility_windows: tuple[int, ...] = (6, 24, 42)
    volume_window: int = Field(default=30, ge=3)

    @model_validator(mode="after")
    def validate_feature_windows(self) -> FeatureConfig:
        if not self.return_windows or not self.volatility_windows:
            raise ValueError("Feature windows cannot be empty")
        for name, windows in {
            "return_windows": self.return_windows,
            "volatility_windows": self.volatility_windows,
        }.items():
            if any(window <= 0 for window in windows):
                raise ValueError("Feature windows must be positive")
            if len(set(windows)) != len(windows):
                raise ValueError(f"{name} cannot contain duplicates")
            if tuple(sorted(windows)) != windows:
                raise ValueError(f"{name} must be sorted")
        return self


class LabelConfig(StrictModel):
    execution_delay_bars: int = Field(default=1, ge=0)
    holding_period_bars: int = Field(default=1, ge=1)
    positive_threshold_bps: float = 0.0


class EvaluationConfig(StrictModel):
    initial_train: int = Field(default=800, ge=100)
    calibration_size: int = Field(default=120, ge=20)
    validation_size: int = Field(default=120, ge=20)
    test_size: int = Field(default=120, ge=20)
    step_size: int = Field(default=120, ge=1)
    embargo: int = Field(default=1, ge=0)
    thresholds: tuple[float, ...] = (0.50, 0.55, 0.60, 0.65)
    min_entries: int = Field(default=3, ge=0)
    drawdown_penalty: float = Field(default=0.5, ge=0)
    cost_multipliers: tuple[float, ...] = (1.0, 1.5, 2.0)

    @model_validator(mode="after")
    def validate_evaluation(self) -> EvaluationConfig:
        if not self.thresholds:
            raise ValueError("At least one threshold is required")
        if any(not 0 < threshold < 1 for threshold in self.thresholds):
            raise ValueError("Thresholds must be strictly between zero and one")
        if len(set(self.thresholds)) != len(self.thresholds):
            raise ValueError("Thresholds cannot contain duplicates")
        if tuple(sorted(self.thresholds)) != self.thresholds:
            raise ValueError("Thresholds must be sorted")
        if not self.cost_multipliers:
            raise ValueError("At least one cost multiplier is required")
        if any(multiplier <= 0 for multiplier in self.cost_multipliers):
            raise ValueError("Cost multipliers must be positive")
        if len(set(self.cost_multipliers)) != len(self.cost_multipliers):
            raise ValueError("Cost multipliers cannot contain duplicates")
        if tuple(sorted(self.cost_multipliers)) != self.cost_multipliers:
            raise ValueError("Cost multipliers must be sorted")
        return self


class MLConfig(StrictModel):
    models: tuple[str, ...] = ("prior", "ridge_logistic", "lightgbm", "catboost")
    random_seed: int = 42
    ridge_c: float = Field(default=1.0, gt=0)

    @model_validator(mode="after")
    def validate_models(self) -> MLConfig:
        if not self.models:
            raise ValueError("At least one model is required")
        if len(set(self.models)) != len(self.models):
            raise ValueError("Model names cannot contain duplicates")
        return self


class RiskConfig(StrictModel):
    target_annualized_volatility: float = Field(default=0.35, gt=0)
    max_exposure: float = Field(default=0.35, gt=0, le=1)
    min_exposure: float = Field(default=0.05, ge=0, le=1)

    @model_validator(mode="after")
    def validate_exposure(self) -> RiskConfig:
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
    data: DataConfig = DataConfig()
    strategy: StrategyConfig = StrategyConfig()
    features: FeatureConfig = FeatureConfig()
    labels: LabelConfig = LabelConfig()
    evaluation: EvaluationConfig = EvaluationConfig()
    ml: MLConfig = MLConfig()
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
