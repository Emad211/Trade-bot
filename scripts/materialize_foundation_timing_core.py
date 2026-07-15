from __future__ import annotations

from pathlib import Path


def replace_once(text: str, before: str, after: str, *, label: str) -> str:
    if text.count(before) != 1:
        raise RuntimeError(f"Expected one {label} anchor, found {text.count(before)}")
    return text.replace(before, after, 1)


def patch_rolling() -> None:
    path = Path("src/hybrid_trader/forecasting/rolling.py")
    text = path.read_text("utf-8")
    text = replace_once(
        text,
        '    schema_version: str = "1.2"',
        '    schema_version: str = "1.3"',
        label="manifest schema",
    )
    text = replace_once(
        text,
        '''        row: dict[str, float | pd.Timestamp] = {
            "timestamp": pd.Timestamp(series.index[origin]),
            f"{spec.prefix}_point_1": float(point[0]),
            f"{spec.prefix}_point_last": float(point[-1]),
            f"{spec.prefix}_point_sum": float(point.sum()),
        }
        if observed_availability is not None:
            row["available_at"] = pd.Timestamp(observed_availability.iloc[origin]) + latency
''',
        '''        origin_at = pd.Timestamp(series.index[origin])
        row: dict[str, float | pd.Timestamp] = {
            "timestamp": origin_at,
            f"{spec.prefix}_point_1": float(point[0]),
            f"{spec.prefix}_point_last": float(point[-1]),
            f"{spec.prefix}_point_sum": float(point.sum()),
        }
        if observed_availability is not None:
            origin_available_at = pd.Timestamp(observed_availability.iloc[origin])
            row["forecast_origin_at"] = origin_at
            row["forecast_origin_available_at"] = origin_available_at
            row["available_at"] = origin_available_at + latency
            row["forecast_step"] = 1.0
''',
        label="rolling forecast row",
    )
    text = replace_once(
        text,
        '''    columns: tuple[str, ...],
) -> dict[str, object]:
    return {
        "schema_version": "1.2",
''',
        '''    columns: tuple[str, ...],
    schema_version: str = "1.3",
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
''',
        label="cache identity schema",
    )
    text = replace_once(
        text,
        '''def cache_rolling_features(
    frame: pd.DataFrame,
    output_dir: str | Path,
    *,
    dataset_sha256: str,
    model_id: str,
    model_revision: str | None,
    spec: RollingForecastSpec,
) -> str:
    if frame.empty:
        raise ValueError("Feature cache cannot be empty")
    if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise ValueError("Feature cache index must be unique and sorted")
    if frame.columns.duplicated().any():
        raise ValueError("Feature cache columns must be unique")
    if "available_at" in frame:
        available = pd.to_datetime(frame["available_at"], utc=True, errors="coerce")
        origins = pd.to_datetime(frame.index, utc=True, errors="coerce")
        if available.isna().any() or np.asarray(pd.isna(origins), dtype=bool).any():
            raise ValueError("Feature cache contains invalid timestamps")
        if (available.to_numpy() < origins.to_numpy()).any():
            raise ValueError("Forecast features cannot be available before their origin")

''',
        '''FORECAST_TIMESTAMP_COLUMNS = (
    "available_at",
    "forecast_origin_at",
    "forecast_origin_available_at",
)
FORECAST_METADATA_COLUMNS = (*FORECAST_TIMESTAMP_COLUMNS, "forecast_step")


def _validate_forecast_timing(
    frame: pd.DataFrame, *, horizon: int | None = None
) -> pd.DataFrame:
    """Validate forecast provenance while distinguishing rows from origins."""

    result = frame.copy()
    present = set(FORECAST_TIMESTAMP_COLUMNS).intersection(result.columns)
    if not present:
        return result
    missing = set(FORECAST_TIMESTAMP_COLUMNS).difference(result.columns)
    if missing:
        raise ValueError(
            f"Feature cache missing forecast timing columns: {sorted(missing)}"
        )
    if "forecast_step" not in result.columns:
        raise ValueError("Feature cache missing forecast_step")

    row_times = pd.DatetimeIndex(
        pd.to_datetime(result.index, utc=True, errors="coerce")
    )
    if row_times.isna().any():
        raise ValueError("Feature cache index contains invalid timestamps")
    for column in FORECAST_TIMESTAMP_COLUMNS:
        values = pd.to_datetime(result[column], utc=True, errors="coerce")
        if values.isna().any():
            raise ValueError(
                f"Feature cache contains invalid {column} timestamps"
            )
        result[column] = values

    origin_at = pd.DatetimeIndex(result["forecast_origin_at"])
    origin_available = pd.DatetimeIndex(result["forecast_origin_available_at"])
    available = pd.DatetimeIndex(result["available_at"])
    if (origin_at > row_times).any():
        raise ValueError("Forecast origin cannot be after its decision row")
    if (origin_available < origin_at).any():
        raise ValueError(
            "Forecast origin cannot be available before its origin timestamp"
        )
    if (available < origin_available).any():
        raise ValueError("Forecast output cannot be available before origin inputs")

    steps = pd.to_numeric(result["forecast_step"], errors="coerce").to_numpy(
        dtype=float
    )
    if (
        not np.isfinite(steps).all()
        or (steps < 1).any()
        or not np.equal(steps, np.floor(steps)).all()
    ):
        raise ValueError("forecast_step must contain positive integers")
    if horizon is not None and (steps > horizon).any():
        raise ValueError("forecast_step cannot exceed the configured horizon")
    result["forecast_step"] = steps
    return result


def cache_rolling_features(
    frame: pd.DataFrame,
    output_dir: str | Path,
    *,
    dataset_sha256: str,
    model_id: str,
    model_revision: str | None,
    spec: RollingForecastSpec,
) -> str:
    if frame.empty:
        raise ValueError("Feature cache cannot be empty")
    if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise ValueError("Feature cache index must be unique and sorted")
    if frame.columns.duplicated().any():
        raise ValueError("Feature cache columns must be unique")
    frame = _validate_forecast_timing(frame, horizon=spec.horizon)

''',
        label="forecast timing validator",
    )
    text = replace_once(
        text,
        '''    frame = pd.read_csv(io.BytesIO(payload), index_col=0, parse_dates=True)
    frame.index = pd.to_datetime(frame.index, utc=True)
    if "available_at" in frame:
        frame["available_at"] = pd.to_datetime(frame["available_at"], utc=True)
    for column in frame.columns:
        if column != "available_at":
            frame[column] = pd.to_numeric(frame[column], errors="raise").astype(float)
''',
        '''    frame = pd.read_csv(io.BytesIO(payload), index_col=0, parse_dates=True)
    frame.index = pd.to_datetime(frame.index, utc=True)
    for column in FORECAST_TIMESTAMP_COLUMNS:
        if column in frame:
            frame[column] = pd.to_datetime(
                frame[column], utc=True, errors="raise"
            )
    for column in frame.columns:
        if column not in FORECAST_TIMESTAMP_COLUMNS:
            frame[column] = pd.to_numeric(
                frame[column], errors="raise"
            ).astype(float)
''',
        label="cache timestamp parsing",
    )
    text = replace_once(
        text,
        '''        row_count=manifest.row_count,
        columns=manifest.columns,
    )
    if canonical_json_sha256(identity_payload) != manifest.cache_id:
''',
        '''        row_count=manifest.row_count,
        columns=manifest.columns,
        schema_version=manifest.schema_version,
    )
    if canonical_json_sha256(identity_payload) != manifest.cache_id:
''',
        label="manifest identity version",
    )
    text = replace_once(
        text,
        '''    if (
        "available_at" in frame
        and (
            pd.to_datetime(frame["available_at"], utc=True).to_numpy()
            < pd.to_datetime(frame.index, utc=True).to_numpy()
        ).any()
    ):
        raise ValueError("Feature cache contains availability before forecast origin")
    return frame, manifest
''',
        '''    if manifest.schema_version == "1.2":
        if "available_at" in frame and (
            pd.to_datetime(frame["available_at"], utc=True).to_numpy()
            < pd.to_datetime(frame.index, utc=True).to_numpy()
        ).any():
            raise ValueError(
                "Legacy feature cache contains availability before forecast origin"
            )
    elif manifest.schema_version == "1.3":
        frame = _validate_forecast_timing(
            frame,
            horizon=int(manifest.spec.get("horizon", 0)) or None,
        )
    else:
        raise ValueError(
            f"Unsupported rolling feature schema: {manifest.schema_version}"
        )
    return frame, manifest
''',
        label="schema-aware cache validation",
    )
    path.write_text(text, encoding="utf-8")


def patch_cli() -> None:
    path = Path("src/hybrid_trader/cli.py")
    text = path.read_text("utf-8")
    text = replace_once(
        text,
        '''from hybrid_trader.forecasting.rolling import (
    RollingForecastSpec,
''',
        '''from hybrid_trader.forecasting.rolling import (
    FORECAST_METADATA_COLUMNS,
    RollingForecastSpec,
''',
        label="CLI metadata import",
    )
    text = replace_once(
        text,
        '''        if "available_at" in feature_frame:
            feature_availability.append(
                pd.to_datetime(feature_frame.pop("available_at"), utc=True).rename(
                    f"feature_available_at_{cache_index}"
                )
            )
        overlap = set(data.columns).intersection(feature_frame.columns)
''',
        '''        if "available_at" in feature_frame:
            feature_availability.append(
                pd.to_datetime(feature_frame.pop("available_at"), utc=True).rename(
                    f"feature_available_at_{cache_index}"
                )
            )
        for metadata_column in FORECAST_METADATA_COLUMNS:
            if (
                metadata_column != "available_at"
                and metadata_column in feature_frame
            ):
                feature_frame.pop(metadata_column)
        overlap = set(data.columns).intersection(feature_frame.columns)
''',
        label="CLI metadata removal",
    )
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_rolling()
    patch_cli()
