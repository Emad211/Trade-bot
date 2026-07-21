from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from hybrid_trader.replication.okx_instrument_version import (
    AvailabilityClaim,
    AvailabilityScope,
    EvidenceClass,
    GateOutcome,
    HistoricalFieldClaim,
    OKXInstrumentVersionError,
    earliest_verified_availability,
    evaluate_point_in_time_gate,
    resolve_historical_field,
)

SOURCE_SHA = "a" * 64
FILE_SHA = "b" * 64
POINT_IN_TIME = datetime(2022, 3, 15, tzinfo=UTC)
RETRIEVED_AT = datetime(2026, 7, 21, tzinfo=UTC)


def _effective_claim(
    field_name: str,
    value: str,
    *,
    source_id: str | None = None,
) -> HistoricalFieldClaim:
    return HistoricalFieldClaim(
        source_id=source_id or f"SOURCE_{field_name}",
        field_name=field_name,
        value=value,
        evidence_class=EvidenceClass.OFFICIAL_DATED_EFFECTIVE_NOTICE,
        published_at=datetime(2020, 3, 4, tzinfo=UTC),
        retrieved_at=RETRIEVED_AT,
        source_sha256=SOURCE_SHA,
        effective_from=datetime(2020, 3, 20, 8, tzinfo=UTC),
        historical_use_authorized=True,
    )


def _specific_file_availability(available_by: datetime) -> AvailabilityClaim:
    return AvailabilityClaim(
        source_id="OKX_MARCH_2022_FILE",
        evidence_class=EvidenceClass.VERIFIED_PROVIDER_ARTIFACT,
        scope=AvailabilityScope.SPECIFIC_FILE,
        available_by=available_by,
        retrieved_at=RETRIEVED_AT,
        source_sha256=SOURCE_SHA,
        verified=True,
        module_id="FUNDING_RATES",
        file_sha256=FILE_SHA,
        file_path=(
            "/cdn/okex/traderecords/swaprates/monthly/202203/"
            "BTC-USDT-SWAP-fundingrates-2022-03.zip"
        ),
    )


@pytest.mark.parametrize(
    "evidence_class",
    [
        EvidenceClass.OFFICIAL_DATED_POSTPONEMENT,
        EvidenceClass.OFFICIAL_DATED_GUIDE_CURRENTLY_REVISED,
        EvidenceClass.OFFICIAL_DATED_SERVICE_TERMS,
        EvidenceClass.OFFICIAL_DATED_CHANGELOG,
        EvidenceClass.OFFICIAL_CURRENT_API_NEGATIVE_CONTROL,
        EvidenceClass.OFFICIAL_CURRENT_PAGE,
    ],
)
def test_non_historical_evidence_cannot_authorize_historical_values(
    evidence_class: EvidenceClass,
) -> None:
    with pytest.raises(ValidationError, match="cannot authorize a historical field"):
        HistoricalFieldClaim(
            source_id="NON_HISTORICAL",
            field_name="contract_size",
            value="0.01 BTC",
            evidence_class=evidence_class,
            published_at=datetime(2022, 6, 20, tzinfo=UTC),
            retrieved_at=RETRIEVED_AT,
            source_sha256=SOURCE_SHA,
            effective_from=datetime(2022, 3, 1, tzinfo=UTC),
            historical_use_authorized=True,
        )


def test_authorized_historical_claim_requires_effective_date_and_source_hash() -> None:
    with pytest.raises(ValidationError, match="require effective_from"):
        HistoricalFieldClaim(
            source_id="MISSING_EFFECTIVE_DATE",
            field_name="contract_size",
            value="0.01 BTC",
            evidence_class=EvidenceClass.OFFICIAL_DATED_EFFECTIVE_NOTICE,
            published_at=datetime(2020, 3, 4, tzinfo=UTC),
            retrieved_at=RETRIEVED_AT,
            source_sha256=SOURCE_SHA,
            historical_use_authorized=True,
        )

    with pytest.raises(ValidationError, match="frozen source SHA-256"):
        HistoricalFieldClaim(
            source_id="MISSING_SOURCE_HASH",
            field_name="contract_size",
            value="0.01 BTC",
            evidence_class=EvidenceClass.OFFICIAL_DATED_EFFECTIVE_NOTICE,
            published_at=datetime(2020, 3, 4, tzinfo=UTC),
            retrieved_at=RETRIEVED_AT,
            effective_from=datetime(2020, 3, 20, tzinfo=UTC),
            historical_use_authorized=True,
        )


def test_resolve_historical_field_requires_exactly_one_effective_claim() -> None:
    claim = _effective_claim("contract_size", "0.01 BTC")

    assert (
        resolve_historical_field(
            [claim],
            field_name="contract_size",
            point_in_time=POINT_IN_TIME,
        )
        == claim
    )

    with pytest.raises(OKXInstrumentVersionError, match="No authorized"):
        resolve_historical_field(
            [claim],
            field_name="tick_size",
            point_in_time=POINT_IN_TIME,
        )

    conflicting = _effective_claim(
        "contract_size",
        "0.001 BTC",
        source_id="CONFLICTING_SOURCE",
    )
    with pytest.raises(OKXInstrumentVersionError, match="Ambiguous"):
        resolve_historical_field(
            [claim, conflicting],
            field_name="contract_size",
            point_in_time=POINT_IN_TIME,
        )


def test_service_availability_never_promotes_to_specific_file_availability() -> None:
    service = AvailabilityClaim(
        source_id="OKX_HISTORICAL_TERMS_2023",
        evidence_class=EvidenceClass.OFFICIAL_DATED_SERVICE_TERMS,
        scope=AvailabilityScope.SERVICE,
        available_by=datetime(2023, 10, 26, tzinfo=UTC),
        retrieved_at=RETRIEVED_AT,
        source_sha256=SOURCE_SHA,
        verified=True,
    )

    assert earliest_verified_availability(
        [service],
        scope=AvailabilityScope.SERVICE,
    ) == datetime(2023, 10, 26, tzinfo=UTC)
    assert (
        earliest_verified_availability(
            [service],
            scope=AvailabilityScope.SPECIFIC_FILE,
            module_id="FUNDING_RATES",
            file_sha256=FILE_SHA,
        )
        is None
    )


def test_module_availability_never_promotes_to_specific_file_availability() -> None:
    module = AvailabilityClaim(
        source_id="OKX_HISTORICAL_API_CHANGELOG_2025",
        evidence_class=EvidenceClass.OFFICIAL_DATED_CHANGELOG,
        scope=AvailabilityScope.MODULE,
        available_by=datetime(2025, 9, 2, tzinfo=UTC),
        retrieved_at=RETRIEVED_AT,
        source_sha256=SOURCE_SHA,
        verified=True,
        module_id="HISTORICAL_FUNDING_API",
    )

    assert earliest_verified_availability(
        [module],
        scope=AvailabilityScope.MODULE,
        module_id="HISTORICAL_FUNDING_API",
    ) == datetime(2025, 9, 2, tzinfo=UTC)
    assert (
        earliest_verified_availability(
            [module],
            scope=AvailabilityScope.SPECIFIC_FILE,
            module_id="FUNDING_RATES",
            file_sha256=FILE_SHA,
        )
        is None
    )


def test_gate_blocks_on_incomplete_instrument_history_before_archive_timing() -> None:
    result = evaluate_point_in_time_gate(
        historical_claims=[_effective_claim("contract_size", "0.01 BTC")],
        availability_claims=[_specific_file_availability(RETRIEVED_AT)],
        required_fields=["contract_size", "tick_size"],
        as_of=POINT_IN_TIME,
        module_id="FUNDING_RATES",
        file_sha256=FILE_SHA,
        latest_acceptable_file_availability=datetime(2022, 4, 1, tzinfo=UTC),
    )

    assert result.outcome == GateOutcome.BLOCKED_INSTRUMENT_VERSION
    assert result.resolved_fields == {"contract_size": "0.01 BTC"}
    assert result.unresolved_fields == ("tick_size",)


def test_gate_blocks_when_specific_file_was_verified_only_after_cutoff() -> None:
    result = evaluate_point_in_time_gate(
        historical_claims=[
            _effective_claim("contract_size", "0.01 BTC"),
            _effective_claim("tick_size", "0.1 USDT"),
        ],
        availability_claims=[_specific_file_availability(RETRIEVED_AT)],
        required_fields=["contract_size", "tick_size"],
        as_of=POINT_IN_TIME,
        module_id="FUNDING_RATES",
        file_sha256=FILE_SHA,
        latest_acceptable_file_availability=datetime(2022, 4, 1, tzinfo=UTC),
    )

    assert result.outcome == GateOutcome.BLOCKED_ARCHIVE_TIMING
    assert result.specific_file_available_by == RETRIEVED_AT


def test_gate_go_requires_complete_fields_and_timely_specific_file_evidence() -> None:
    file_available_by = datetime(2022, 4, 1, tzinfo=UTC)
    result = evaluate_point_in_time_gate(
        historical_claims=[
            _effective_claim("contract_size", "0.01 BTC"),
            _effective_claim("tick_size", "0.1 USDT"),
        ],
        availability_claims=[_specific_file_availability(file_available_by)],
        required_fields=["contract_size", "tick_size"],
        as_of=POINT_IN_TIME,
        module_id="FUNDING_RATES",
        file_sha256=FILE_SHA,
        latest_acceptable_file_availability=file_available_by,
    )

    assert result.outcome == GateOutcome.GO
    assert result.unresolved_fields == ()
    assert result.basis_computation_authorized is False
    assert result.funding_pnl_computation_authorized is False
    assert result.returns_computation_authorized is False
    assert result.empirical_fitting_authorized is False
    assert result.paper_or_live_trading_authorized is False


def test_naive_timestamps_are_rejected() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        AvailabilityClaim(
            source_id="NAIVE_TIME",
            evidence_class=EvidenceClass.OFFICIAL_DATED_SERVICE_TERMS,
            scope=AvailabilityScope.SERVICE,
            available_by=datetime(2023, 10, 26),
            retrieved_at=RETRIEVED_AT,
            source_sha256=SOURCE_SHA,
            verified=True,
        )
