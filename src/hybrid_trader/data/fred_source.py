"""Conservative public FRED CSV reader for market-price context series.

The graph CSV endpoint does not expose historical vintages. This adapter is
therefore restricted to market/reference-price series. Revisable macro series
must use an ALFRED or otherwise vintage-aware source.
"""

from __future__ import annotations

import hashlib
import io
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Final
from urllib.parse import quote
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

_ALLOWED_REVISION_POLICY: Final = "market_price_latest_vintage"


@dataclass(frozen=True)
class FredFetchResult:
    frame: pd.DataFrame
    url: str
    payload_sha256: str
    retrieved_at: datetime
    revision_policy: str


def _download(url: str, *, timeout_seconds: float) -> bytes:
    request = Request(
        url,
        headers={"User-Agent": "hybrid-trader/0.3 (+https://github.com/Emad211/Trade-bot)"},
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        return bytes(response.read())


@dataclass(frozen=True)
class FredCsvSource:
    """Fetch one daily FRED market-price series without an API key."""

    series_id: str
    feature_name: str
    release_lag: timedelta = timedelta(days=1)
    source_latency: timedelta = timedelta(minutes=5)
    revision_policy: str = _ALLOWED_REVISION_POLICY
    timeout_seconds: float = 60.0

    def __post_init__(self) -> None:
        if not self.series_id or not self.feature_name:
            raise ValueError("series_id and feature_name are required")
        if self.release_lag < timedelta(0) or self.source_latency < timedelta(0):
            raise ValueError("FRED lag and latency cannot be negative")
        if self.revision_policy != _ALLOWED_REVISION_POLICY:
            raise ValueError(
                "The public graph endpoint is allowed only for non-revisable market-price series"
            )
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

    @property
    def url(self) -> str:
        return f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={quote(self.series_id)}"

    def fetch(
        self,
        *,
        start: pd.Timestamp,
        end: pd.Timestamp,
        as_of: pd.Timestamp,
        downloader: Callable[[str], bytes] | None = None,
        retrieved_at: datetime | None = None,
    ) -> FredFetchResult:
        """Return values observable by ``as_of`` with conservative availability."""

        start_utc = _utc(start)
        end_utc = _utc(end)
        as_of_utc = _utc(as_of)
        if not start_utc <= end_utc <= as_of_utc:
            raise ValueError("FRED request requires start <= end <= as_of")
        payload = (
            downloader(self.url)
            if downloader is not None
            else _download(self.url, timeout_seconds=self.timeout_seconds)
        )
        digest = hashlib.sha256(payload).hexdigest()
        raw = pd.read_csv(io.BytesIO(payload))
        date_column = next(
            (column for column in ("observation_date", "DATE", "date") if column in raw.columns),
            None,
        )
        if date_column is None or self.series_id not in raw.columns:
            raise ValueError(
                f"Unexpected FRED columns for {self.series_id}: {sorted(raw.columns)}"
            )
        event_time = pd.to_datetime(raw[date_column], utc=True, errors="coerce")
        values = pd.to_numeric(raw[self.series_id].replace(".", np.nan), errors="coerce")
        frame = pd.DataFrame({"event_time": event_time, self.feature_name: values}).dropna()
        frame = frame.loc[
            (frame["event_time"] >= start_utc) & (frame["event_time"] <= end_utc)
        ].copy()
        frame["available_at"] = (
            frame["event_time"] + pd.Timedelta(self.release_lag) + pd.Timedelta(self.source_latency)
        )
        frame = frame.loc[frame["available_at"] <= as_of_utc]
        frame = frame.sort_values("event_time").drop_duplicates("event_time", keep="last")
        if frame.empty:
            raise RuntimeError(f"FRED returned no observable rows for {self.series_id}")
        numeric = frame[self.feature_name].to_numpy(dtype=float)
        if not np.isfinite(numeric).all():
            raise ValueError(f"FRED series {self.series_id} contains non-finite values")
        timestamp = retrieved_at or datetime.now(UTC)
        timestamp = (
            timestamp.replace(tzinfo=UTC)
            if timestamp.tzinfo is None
            else timestamp.astimezone(UTC)
        )
        return FredFetchResult(
            frame=frame.reset_index(drop=True),
            url=self.url,
            payload_sha256=digest,
            retrieved_at=timestamp,
            revision_policy=self.revision_policy,
        )


def _utc(value: pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    return timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp.tz_convert("UTC")
