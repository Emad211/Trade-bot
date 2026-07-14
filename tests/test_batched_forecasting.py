import numpy as np
import pandas as pd

from hybrid_trader.forecasting.base import ForecastOutput
from hybrid_trader.forecasting.batched import BatchRollingSpec, rolling_batched_features


class FakeBatchForecaster:
    def __init__(self) -> None:
        self.calls = 0

    def predict_batch(self, histories, horizon):
        self.calls += 1
        outputs = []
        for history in histories:
            base = float(history[-1])
            point = base + np.arange(1, horizon + 1, dtype=float)
            outputs.append(
                ForecastOutput(
                    point=point,
                    quantiles={0.1: point - 1.0, 0.9: point + 1.0},
                )
            )
        return outputs


def test_batched_rolling_uses_correct_horizon_step() -> None:
    index = pd.date_range("2026-01-01", periods=20, freq="4h", tz="UTC")
    series = pd.Series(np.arange(20, dtype=float), index=index)
    availability = pd.Series(index + pd.Timedelta(hours=4), index=index)
    model = FakeBatchForecaster()
    features = rolling_batched_features(
        series,
        model,
        BatchRollingSpec(
            context_length=4,
            min_history=4,
            horizon=3,
            stride=3,
            batch_size=2,
            prefix="fake",
            inference_latency_seconds=10,
        ),
        availability=availability,
    )
    assert len(features) == 17
    assert model.calls == 3
    # Origin is index 3, whose last value is 3. Steps are 4, 5, 6.
    assert features.loc[index[3], "fake_point_1"] == 4
    assert features.loc[index[4], "fake_point_1"] == 5
    assert features.loc[index[5], "fake_point_1"] == 6
    assert features.loc[index[5], "fake_forecast_age_bars"] == 2
    assert features.loc[index[3], "available_at"] == index[3] + pd.Timedelta(hours=4, seconds=10)
