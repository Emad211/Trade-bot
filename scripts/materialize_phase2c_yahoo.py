from __future__ import annotations

from pathlib import Path

PATH = Path("src/hybrid_trader/phase2c_runner.py")


def replace_once(text: str, before: str, after: str) -> str:
    if after in text:
        return text
    if text.count(before) != 1:
        raise RuntimeError(f"Expected exactly one runner anchor, found {text.count(before)}")
    return text.replace(before, after, 1)


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "from hybrid_trader.data.stooq_source import StooqCsvSource, StooqFetchResult\n",
        "from hybrid_trader.data.stooq_source import StooqCsvSource, StooqFetchResult\n"
        "from hybrid_trader.data.yahoo_source import YahooChartSource, YahooFetchResult\n",
    )
    text = replace_once(
        text,
        "    StooqSeriesSpec,\n    load_phase2c_spec,\n",
        "    StooqSeriesSpec,\n    YahooSeriesSpec,\n    load_phase2c_spec,\n",
    )
    text = replace_once(
        text,
        "StooqFactory = Callable[[StooqSeriesSpec], StooqCsvSource]\n",
        "StooqFactory = Callable[[StooqSeriesSpec], StooqCsvSource]\n"
        "YahooFactory = Callable[[YahooSeriesSpec], YahooChartSource]\n",
    )
    text = replace_once(
        text,
        "def run_phase2c(\n",
        "def _yahoo_factory(spec: YahooSeriesSpec) -> YahooChartSource:\n"
        "    return YahooChartSource(\n"
        "        spec.symbol,\n"
        "        spec.feature_name,\n"
        "        release_lag=timedelta(hours=spec.release_lag_hours),\n"
        "        source_latency=timedelta(seconds=spec.source_latency_seconds),\n"
        "    )\n\n\n"
        "def run_phase2c(\n",
    )
    text = replace_once(
        text,
        "    stooq_factory: StooqFactory = _stooq_factory,\n"
        "    feature_caches: tuple[Path, ...] = (),\n",
        "    stooq_factory: StooqFactory = _stooq_factory,\n"
        "    yahoo_factory: YahooFactory = _yahoo_factory,\n"
        "    feature_caches: tuple[Path, ...] = (),\n",
    )
    yahoo_loop = '''
    for yahoo_item in spec.yahoo_series:
        source_id = f"yahoo:{yahoo_item.symbol}"
        try:
            yahoo_result: YahooFetchResult = yahoo_factory(yahoo_item).fetch(
                start=start, end=end, as_of=as_of
            )
            macro_manifest = write_tabular_artifact(
                yahoo_result.frame,
                root / "sources" / "yahoo" / _safe(yahoo_item.symbol),
                source_id=source_id,
                source_type="market_context",
                instrument=yahoo_item.symbol,
                availability_policy=(
                    f"event_plus_{yahoo_item.release_lag_hours:g}h_plus_latency"
                ),
                revision_policy=yahoo_result.revision_policy,
                created_at=spec.as_of,
                notes=yahoo_result.url,
            )
            combined = merge_asof_features(
                combined,
                yahoo_result.frame,
                feature_columns=[yahoo_item.feature_name],
                provenance_column=f"{yahoo_item.feature_name}__available_at",
                tolerance=pd.Timedelta(days=yahoo_item.tolerance_days),
            )
            extra.append(yahoo_item.feature_name)
            macro_successes.append(yahoo_item.feature_name)
            attempts.append(
                _attempt_artifact(
                    source_id,
                    "market_context",
                    "yahoo",
                    yahoo_item.symbol,
                    yahoo_item.required,
                    spec,
                    macro_manifest,
                    yahoo_item.source_latency_seconds,
                    yahoo_result.retrieved_at,
                    yahoo_result.payload_sha256,
                )
            )
        except Exception as exc:
            attempts.append(
                _attempt_failure(
                    source_id,
                    "market_context",
                    "yahoo",
                    yahoo_item.symbol,
                    yahoo_item.required,
                    spec,
                    "event_plus_release_lag",
                    yahoo_item.revision_policy,
                    yahoo_item.source_latency_seconds,
                    retrieved,
                    exc,
                )
            )
            if yahoo_item.required:
                raise

'''
    text = replace_once(
        text,
        '    successful_ids = [item.source_id for item in attempts if item.status == "success"]\n',
        yahoo_loop
        + '    successful_ids = [item.source_id for item in attempts if item.status == "success"]\n',
    )
    PATH.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
