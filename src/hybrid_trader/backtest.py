"""Small, auditable close-to-close backtester for the trend baseline."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from hybrid_trader.config import AppConfig


@dataclass(frozen=True)
class BacktestResult:
    frame: pd.DataFrame
    metrics: dict[str, float]


def _max_drawdown(equity: pd.Series) -> float:
    running_max = equity.cummax()
    drawdown = equity / running_max - 1.0
    return float(drawdown.min())


def calculate_metrics(
    net_returns: pd.Series,
    exposure: pd.Series,
    turnover: pd.Series,
    close: pd.Series,
    periods_per_year: int,
) -> dict[str, float]:
    clean_returns = net_returns.fillna(0.0)
    equity = (1.0 + clean_returns).cumprod()
    observations = len(clean_returns)
    years = observations / periods_per_year if periods_per_year else 0.0
    total_return = float(equity.iloc[-1] - 1.0) if observations else 0.0
    annualized_return = (
        float((1.0 + total_return) ** (1.0 / years) - 1.0)
        if years > 0 and total_return > -1.0
        else 0.0
    )
    annualized_vol = float(clean_returns.std(ddof=0) * np.sqrt(periods_per_year))
    sharpe = (
        float(clean_returns.mean() / clean_returns.std(ddof=0) * np.sqrt(periods_per_year))
        if clean_returns.std(ddof=0) > 0
        else 0.0
    )
    entries = ((exposure > 0) & (exposure.shift(1).fillna(0) == 0)).sum()
    buy_hold = float(close.iloc[-1] / close.iloc[0] - 1.0) if observations > 1 else 0.0

    return {
        "total_return": total_return,
        "annualized_return": annualized_return,
        "annualized_volatility": annualized_vol,
        "sharpe": sharpe,
        "max_drawdown": _max_drawdown(equity) if observations else 0.0,
        "buy_hold_return": buy_hold,
        "average_exposure": float(exposure.mean()) if observations else 0.0,
        "turnover": float(turnover.sum()),
        "entries": float(entries),
        "observations": float(observations),
    }


def run_backtest(signal_frame: pd.DataFrame, config: AppConfig) -> BacktestResult:
    """Execute desired close decisions on the next bar and charge one-way costs."""

    if "desired_exposure" not in signal_frame:
        raise ValueError("signal_frame must contain desired_exposure")
    if len(signal_frame) < config.backtest.min_history_bars:
        raise ValueError(
            f"Need at least {config.backtest.min_history_bars} bars; got {len(signal_frame)}"
        )

    frame = signal_frame.copy()
    frame["asset_return"] = frame["close"].pct_change().fillna(0.0)
    frame["executed_exposure"] = frame["desired_exposure"].shift(1).fillna(0.0)
    frame["gross_strategy_return"] = frame["executed_exposure"] * frame["asset_return"]
    frame["turnover"] = (
        frame["executed_exposure"].diff().abs().fillna(frame["executed_exposure"].abs())
    )
    frame["trading_cost"] = frame["turnover"] * config.costs.one_way_rate
    frame["net_strategy_return"] = frame["gross_strategy_return"] - frame["trading_cost"]
    frame["equity"] = config.backtest.initial_cash * (1.0 + frame["net_strategy_return"]).cumprod()

    metrics = calculate_metrics(
        frame["net_strategy_return"],
        frame["executed_exposure"],
        frame["turnover"],
        frame["close"],
        config.market.periods_per_year,
    )
    metrics["final_equity"] = float(frame["equity"].iloc[-1])
    return BacktestResult(frame=frame, metrics=metrics)
