"""Typed policy for the Phase 3A statistical robustness gate."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class RobustnessPolicy(BaseModel):
    """Predeclared acceptance thresholds; never an automatic trading approval."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    benchmark_model: str = "trend"
    periods_per_year: int = Field(default=2190, gt=0)
    declared_trials: int = Field(default=40, ge=2)
    bootstrap_samples: int = Field(default=5000, ge=500)
    bootstrap_block_length: int = Field(default=6, ge=1)
    random_seed: int = 42
    minimum_observations: int = Field(default=500, ge=30)
    minimum_psr: float = Field(default=0.95, gt=0.5, lt=1)
    minimum_dsr: float = Field(default=0.95, gt=0.5, lt=1)
    maximum_bootstrap_pvalue: float = Field(default=0.05, gt=0, lt=0.5)
    minimum_positive_fold_ratio: float = Field(default=0.5, ge=0, le=1)
    maximum_top_fold_profit_share: float = Field(default=0.5, gt=0, le=1)
    maximum_top_three_fold_profit_share: float = Field(default=0.8, gt=0, le=1)
    require_positive_total_return: bool = True
    require_positive_two_x_cost_return: bool = True
    low_volatility_threshold: float = Field(default=0.45, gt=0)
    high_volatility_threshold: float = Field(default=0.90, gt=0)
    trend_band: float = Field(default=0.0, ge=0)

    @model_validator(mode="after")
    def validate_thresholds(self) -> RobustnessPolicy:
        if self.low_volatility_threshold >= self.high_volatility_threshold:
            raise ValueError("low_volatility_threshold must be below high_volatility_threshold")
        if self.maximum_top_fold_profit_share > self.maximum_top_three_fold_profit_share:
            raise ValueError(
                "maximum_top_fold_profit_share cannot exceed the top-three threshold"
            )
        return self


def load_robustness_policy(path: str | Path) -> RobustnessPolicy:
    policy_path = Path(path)
    if not policy_path.exists():
        raise FileNotFoundError(f"Robustness policy not found: {policy_path}")
    with policy_path.open("r", encoding="utf-8") as handle:
        payload: Any = yaml.safe_load(handle) or {}
    return RobustnessPolicy.model_validate(payload)
