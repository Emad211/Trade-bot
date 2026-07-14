"""Binary probability model contracts."""

from __future__ import annotations

from typing import Protocol

import numpy as np
from numpy.typing import NDArray

FloatMatrix = NDArray[np.float64]
FloatVector = NDArray[np.float64]
IntVector = NDArray[np.int64]


class ProbabilityModel(Protocol):
    name: str

    def fit(self, x: FloatMatrix, y: IntVector) -> ProbabilityModel: ...

    def predict_proba(self, x: FloatMatrix) -> FloatVector: ...
