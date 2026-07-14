import numpy as np
import pytest

from hybrid_trader.models import CatBoostProbabilityModel, LightGBMProbabilityModel

pytestmark = pytest.mark.optional_ml


@pytest.mark.parametrize("factory", [LightGBMProbabilityModel, CatBoostProbabilityModel])
def test_optional_tree_model_contract(factory) -> None:
    rng = np.random.default_rng(2)
    x = rng.normal(size=(100, 4))
    x[:5, 0] = np.nan
    y = (x[:, 1] + rng.normal(scale=0.2, size=100) > 0).astype(np.int64)
    model = factory(random_seed=3).fit(x, y)
    probabilities = model.predict_proba(x[:10])
    assert probabilities.shape == (10,)
    assert np.isfinite(probabilities).all()
    assert ((probabilities >= 0) & (probabilities <= 1)).all()
