"""Conservative public Stooq CSV reader for daily market-reference series."""

from __future__ import annotations

import hashlib
import io
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

REVISION_POLICY = "market_price_latest_vintage"


@dataclass(frozen=True)
class StooqFetchResult:
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


def _utc(value: pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    return timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp.tz_convert("UTC")


@dataclass(frozen=True)
class StooqCsvSource:
    """Fetch a daily close series from Stooq's public historical CSV endpoint.

    Stooq rows are date-indexed. To avoid assuming an exact exchange close time,
    the default contract makes each observation usable one full day after its
    date, plus explicit source latency.
    """

    symbol: str
    feature_name: str
    release_lag: timedelta = timedelta(days=1)
    source_latency: timedelta = timedelta(minutes=5)
    revision_policy: str = REVISION_POLICY
    timeout_seconds: float = 60.0

    def __post_init__(self) -> None:
        if not self.symbol or not self.feature_name:
            raise ValueError("symbol and feature_name are required")
        if self.release_lag < timedelta(0) or self.source_latency < timedelta(0):
            raise ValueError("Stooq lag and latency cannot be negative")
        if self.revision_policy != REVISION_POLICY:
            raise ValueError("Stooq is restricted to market/reference-price series")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

    def url_for(self, start: pd.Timestamp, end: pd.Timestamp) -> str:
        query = urlencode(
            {
                "s": self.symbol.lower(),
                "i": "d",
                "d1": _utc(start).strftime("%Y%m%d"),
                "d2": _utc(end).strftime("%Y%m%d"),
            }
        )
        return f"https://stooq.com/q/d/l/?{query}"

    def fetch(
        self,
        *,
        start: pd.Timestamp,
        end: pd.Timestamp,
        as_of: pd.Timestamp,
        downloader: Callable[[str], bytes] | None = None,
        retrieved_at: datetime | None = None,
    ) -> StooqFetchResult:
        start_utc, end_utc, as_of_utc = map(_utc, (start, end, as_of))
        if not start_utc <= end_utc <= as_of_utc:
            raise ValueError("Stooq request requires start <= end <= as_of")
        url = self.url_for(start_utc, end_utc)
        payload = downloader(url) if downloader else _download(url, self.timeout_seconds)
        raw = pd.read_csv(io.BytesIO(payload))
        normalized_columns = {str(column).strip().lower(): column for column in raw.columns}
        date_column = normalized_columns.get("date")
        close_column = normalized_columns.get("close")
        if date_column is None or close_column is None:
            raise ValueError(f"Unexpected Stooq columns: {sorted(map(str, raw.columns))}")
        event = pd.to_datetime(raw[date_column], utc=True, errors="coerce")
        values = pd.to_numeric(raw[close_column], errors="coerce")
        frame = pd.DataFrame({"event_time": event, self.feature_name: values}).dropna()
        frame = frame.loc[(frame.event_time >= start_utc) & (frame.event_time <= end_utc)].copy()
        frame["available_at"] = (
            frame.event_time + pd.Timedelta(self.release_lag) + pd.Timedelta(self.source_latency)
        )
        frame = frame.loc[frame.available_at <= as_of_utc].sort_values("event_time")
        frame = frame.drop_duplicates("event_time", keep="last")
        if frame.empty:
            raise RuntimeError(f"Stooq returned no observable rows for {self.symbol}")
        if not np.isfinite(frame[self.feature_name].to_numpy(dtype=float)).all():
            raise ValueError("Stooq series contains non-finite values")
        if (frame[self.feature_name] <= 0).any():
            raise ValueError("Stooq reference prices must be positive")
        stamp = retrieved_at or datetime.now(UTC)
        stamp = stamp.replace(tzinfo=UTC) if stamp.tzinfo is None else stamp.astimezone(UTC)
        return StooqFetchResult(
            frame=frame.reset_index(drop=True),
            url=url,
            payload_sha256=hashlib.sha256(payload).hexdigest(),
            retrieved_at=stamp,
            revision_policy=self.revision_policy,
        )
