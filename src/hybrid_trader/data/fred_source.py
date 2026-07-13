"""Conservative public FRED CSV reader for market/reference-price series."""

from __future__ import annotations

import hashlib
import io
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import quote
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

REVISION_POLICY = "market_price_latest_vintage"


@dataclass(frozen=True)
class FredFetchResult:
    frame: pd.DataFrame
    url: str
    payload_sha256: str
    retrieved_at: datetime
    revision_policy: str


def _download(url: str, timeout_seconds: float) -> bytes:
    request = Request(
        url,
        headers={"User-Agent": "hybrid-trader/0.3 (+https://github.com/Emad211/Trade-bot)"},
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        return bytes(response.read())


@dataclass(frozen=True)
class FredCsvSource:
    series_id: str
    feature_name: str
    release_lag: timedelta = timedelta(days=1)
    source_latency: timedelta = timedelta(minutes=5)
    revision_policy: str = REVISION_POLICY
    timeout_seconds: float = 60.0

    def __post_init__(self) -> None:
        if not self.series_id or not self.feature_name:
            raise ValueError("series_id and feature_name are required")
        if self.release_lag < timedelta(0) or self.source_latency < timedelta(0):
            raise ValueError("FRED lag and latency cannot be negative")
        if self.revision_policy != REVISION_POLICY:
            raise ValueError(
                "Public FRED graph CSV is restricted to market/reference-price series"
            )
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

    @property
    def url(self) -> str:
        return (
            "https://fred.stlouisfed.org/graph/fredgraph.csv?id="
            f"{quote(self.series_id)}"
        )

    def fetch(
        self,
        *,
        start: pd.Timestamp,
        end: pd.Timestamp,
        as_of: pd.Timestamp,
        downloader: Callable[[str], bytes] | None = None,
        retrieved_at: datetime | None = None,
    ) -> FredFetchResult:
        start_utc, end_utc, as_of_utc = map(_utc, (start, end, as_of))
        if not start_utc <= end_utc <= as_of_utc:
            raise ValueError("FRED request requires start <= end <= as_of")
        payload = (
            downloader(self.url)
            if downloader
            else _download(self.url, self.timeout_seconds)
        )
        raw = pd.read_csv(io.BytesIO(payload))
        date_col = next(
            (column for column in ("observation_date", "DATE", "date") if column in raw),
            None,
        )
        if date_col is None or self.series_id not in raw:
            raise ValueError(f"Unexpected FRED columns: {sorted(raw.columns)}")
        event = pd.to_datetime(raw[date_col], utc=True, errors="coerce")
        values = pd.to_numeric(
            raw[self.series_id].replace(".", np.nan), errors="coerce"
        )
        frame = pd.DataFrame(
            {"event_time": event, self.feature_name: values}
        ).dropna()
        frame = frame.loc[
            (frame.event_time >= start_utc) & (frame.event_time <= end_utc)
        ].copy()
        frame["available_at"] = (
            frame.event_time
            + pd.Timedelta(self.release_lag)
            + pd.Timedelta(self.source_latency)
        )
        frame = frame.loc[frame.available_at <= as_of_utc].sort_values("event_time")
        frame = frame.drop_duplicates("event_time", keep="last")
        if frame.empty:
            raise RuntimeError(f"FRED returned no observable rows for {self.series_id}")
        if not np.isfinite(frame[self.feature_name].to_numpy(dtype=float)).all():
            raise ValueError("FRED series contains non-finite values")
        stamp = retrieved_at or datetime.now(UTC)
        stamp = (
            stamp.replace(tzinfo=UTC)
            if stamp.tzinfo is None
            else stamp.astimezone(UTC)
        )
        return FredFetchResult(
            frame=frame.reset_index(drop=True),
            url=self.url,
            payload_sha256=hashlib.sha256(payload).hexdigest(),
            retrieved_at=stamp,
            revision_policy=self.revision_policy,
        )


def _utc(value: pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    return (
        timestamp.tz_localize("UTC")
        if timestamp.tzinfo is None
        else timestamp.tz_convert("UTC")
    )
