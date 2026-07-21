"""Fail-closed point-in-time contracts for historical OKX instrument evidence."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

SHA256_PATTERN = r"^[0-9a-f]{64}$"


class OKXInstrumentVersionError(RuntimeError):
    """Raised when historical instrument or availability evidence is ambiguous."""


class EvidenceClass(StrEnum):
    """Evidence classes with deliberately different historical permissions."""

    OFFICIAL_DATED_EFFECTIVE_NOTICE = "OFFICIAL_DATED_EFFECTIVE_NOTICE"
    OFFICIAL_DATED_POSTPONEMENT = "OFFICIAL_DATED_POSTPONEMENT"
    OFFICIAL_DATED_GUIDE_FROZEN = "OFFICIAL_DATED_GUIDE_FROZEN"
    OFFICIAL_DATED_GUIDE_CURRENTLY_REVISED = (
        "OFFICIAL_DATED_GUIDE_CURRENTLY_REVISED"
    )
    OFFICIAL_DATED_SERVICE_TERMS = "OFFICIAL_DATED_SERVICE_TERMS"
    OFFICIAL_DATED_CHANGELOG = "OFFICIAL_DATED_CHANGELOG"
    OFFICIAL_CURRENT_API_NEGATIVE_CONTROL = (
        "OFFICIAL_CURRENT_API_NEGATIVE_CONTROL"
    )
    OFFICIAL_CURRENT_PAGE = "OFFICIAL_CURRENT_PAGE"
    VERIFIED_PROVIDER_ARTIFACT = "VERIFIED_PROVIDER_ARTIFACT"


class AvailabilityScope(StrEnum):
    """The object whose availability is actually supported by a source."""

    SERVICE = "SERVICE"
    MODULE = "MODULE"
    SPECIFIC_FILE = "SPECIFIC_FILE"


class GateOutcome(StrEnum):
    """Only outcomes admitted by Issue #51."""

    GO = "GO_OKX_2022_POINT_IN_TIME_INSTRUMENT_CONTRACT"
    BLOCKED_INSTRUMENT_VERSION = "BLOCKED_INSTRUMENT_VERSION_HISTORY"
    BLOCKED_ARCHIVE_TIMING = "BLOCKED_ARCHIVE_AVAILABILITY_TIMING"


_HISTORICALLY_AUTHORIZING_EVIDENCE = {
    EvidenceClass.OFFICIAL_DATED_EFFECTIVE_NOTICE,
    EvidenceClass.OFFICIAL_DATED_GUIDE_FROZEN,
    EvidenceClass.VERIFIED_PROVIDER_ARTIFACT,
}


_NON_HISTORICAL_EVIDENCE = {
    EvidenceClass.OFFICIAL_DATED_POSTPONEMENT,
    EvidenceClass.OFFICIAL_DATED_GUIDE_CURRENTLY_REVISED,
    EvidenceClass.OFFICIAL_DATED_SERVICE_TERMS,
    EvidenceClass.OFFICIAL_DATED_CHANGELOG,
    EvidenceClass.OFFICIAL_CURRENT_API_NEGATIVE_CONTROL,
    EvidenceClass.OFFICIAL_CURRENT_PAGE,
}


def _require_aware_utc(value: datetime, *, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


class HistoricalFieldClaim(BaseModel):
    """One source-bound claim about a historically effective instrument field."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str = Field(min_length=1)
    field_name: str = Field(min_length=1)
    value: str = Field(min_length=1)
    evidence_class: EvidenceClass
    published_at: datetime
    retrieved_at: datetime
    source_sha256: str | None = Field(default=None, pattern=SHA256_PATTERN)
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    historical_use_authorized: bool = False

    @model_validator(mode="after")
    def validate_historical_permission(self) -> HistoricalFieldClaim:
        published_at = _require_aware_utc(
            self.published_at,
            field_name="published_at",
        )
        retrieved_at = _require_aware_utc(
            self.retrieved_at,
            field_name="retrieved_at",
        )
        if retrieved_at < published_at:
            raise ValueError("retrieved_at cannot precede published_at")

        effective_from = None
        effective_to = None
        if self.effective_from is not None:
            effective_from = _require_aware_utc(
                self.effective_from,
                field_name="effective_from",
            )
        if self.effective_to is not None:
            effective_to = _require_aware_utc(
                self.effective_to,
                field_name="effective_to",
            )
            if effective_from is None:
                raise ValueError("effective_to requires effective_from")
            if effective_to <= effective_from:
                raise ValueError("effective_to must follow effective_from")

        if self.historical_use_authorized:
            if self.evidence_class not in _HISTORICALLY_AUTHORIZING_EVIDENCE:
                raise ValueError(
                    f"{self.evidence_class} cannot authorize a historical field"
                )
            if effective_from is None:
                raise ValueError(
                    "historically authorized claims require effective_from"
                )
            if self.source_sha256 is None:
                raise ValueError(
                    "historically authorized claims require a frozen source SHA-256"
                )
        elif self.evidence_class in _NON_HISTORICAL_EVIDENCE:
            return self

        return self

    def applies_at(self, point_in_time: datetime) -> bool:
        """Return whether this exact authorized claim covers ``point_in_time``."""

        point = _require_aware_utc(point_in_time, field_name="point_in_time")
        if not self.historical_use_authorized or self.effective_from is None:
            return False
        start = self.effective_from.astimezone(UTC)
        if point < start:
            return False
        if self.effective_to is None:
            return True
        return point < self.effective_to.astimezone(UTC)


class AvailabilityClaim(BaseModel):
    """A source-bound availability claim at an exact scope."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str = Field(min_length=1)
    evidence_class: EvidenceClass
    scope: AvailabilityScope
    available_by: datetime
    retrieved_at: datetime
    source_sha256: str | None = Field(default=None, pattern=SHA256_PATTERN)
    verified: bool = False
    module_id: str | None = None
    file_sha256: str | None = Field(default=None, pattern=SHA256_PATTERN)
    file_path: str | None = None

    @model_validator(mode="after")
    def validate_scope(self) -> AvailabilityClaim:
        available_by = _require_aware_utc(
            self.available_by,
            field_name="available_by",
        )
        retrieved_at = _require_aware_utc(
            self.retrieved_at,
            field_name="retrieved_at",
        )
        if available_by > retrieved_at:
            raise ValueError("available_by cannot follow retrieved_at")
        if self.verified and self.source_sha256 is None:
            raise ValueError("verified availability requires a frozen source SHA-256")

        if self.scope == AvailabilityScope.SERVICE:
            if self.module_id is not None or self.file_sha256 is not None:
                raise ValueError("service availability cannot identify a module or file")
            if self.file_path is not None:
                raise ValueError("service availability cannot identify a file path")
        elif self.scope == AvailabilityScope.MODULE:
            if not self.module_id:
                raise ValueError("module availability requires module_id")
            if self.file_sha256 is not None or self.file_path is not None:
                raise ValueError("module availability cannot identify a specific file")
        elif self.scope == AvailabilityScope.SPECIFIC_FILE:
            if not self.module_id:
                raise ValueError("specific-file availability requires module_id")
            if self.file_sha256 is None or not self.file_path:
                raise ValueError(
                    "specific-file availability requires file_sha256 and file_path"
                )
        return self


class PointInTimeGateResult(BaseModel):
    """Deterministic Issue #51 evaluation without any trading authorization."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    as_of: datetime
    latest_acceptable_file_availability: datetime
    required_fields: tuple[str, ...]
    resolved_fields: dict[str, str]
    unresolved_fields: tuple[str, ...]
    specific_file_available_by: datetime | None
    outcome: GateOutcome
    basis_computation_authorized: bool = False
    funding_pnl_computation_authorized: bool = False
    returns_computation_authorized: bool = False
    empirical_fitting_authorized: bool = False
    paper_or_live_trading_authorized: bool = False

    @model_validator(mode="after")
    def validate_non_authorization(self) -> PointInTimeGateResult:
        forbidden = (
            self.basis_computation_authorized,
            self.funding_pnl_computation_authorized,
            self.returns_computation_authorized,
            self.empirical_fitting_authorized,
            self.paper_or_live_trading_authorized,
        )
        if any(forbidden):
            raise ValueError("Issue #51 cannot authorize calculations or trading")
        return self


def resolve_historical_field(
    claims: Iterable[HistoricalFieldClaim],
    *,
    field_name: str,
    point_in_time: datetime,
) -> HistoricalFieldClaim:
    """Resolve exactly one effective claim, failing on absence or ambiguity."""

    candidates = [
        claim
        for claim in claims
        if claim.field_name == field_name and claim.applies_at(point_in_time)
    ]
    if not candidates:
        raise OKXInstrumentVersionError(
            f"No authorized historical claim for {field_name!r}"
        )
    if len(candidates) != 1:
        source_ids = sorted(claim.source_id for claim in candidates)
        raise OKXInstrumentVersionError(
            f"Ambiguous historical claims for {field_name!r}: {source_ids}"
        )
    return candidates[0]


def earliest_verified_availability(
    claims: Iterable[AvailabilityClaim],
    *,
    scope: AvailabilityScope,
    module_id: str | None = None,
    file_sha256: str | None = None,
) -> datetime | None:
    """Return availability only from claims at the requested exact scope."""

    matches: list[AvailabilityClaim] = []
    for claim in claims:
        if not claim.verified or claim.scope != scope:
            continue
        if scope in {AvailabilityScope.MODULE, AvailabilityScope.SPECIFIC_FILE}:
            if claim.module_id != module_id:
                continue
        if scope == AvailabilityScope.SPECIFIC_FILE:
            if claim.file_sha256 != file_sha256:
                continue
        matches.append(claim)
    if not matches:
        return None
    return min(claim.available_by.astimezone(UTC) for claim in matches)


def evaluate_point_in_time_gate(
    *,
    historical_claims: Sequence[HistoricalFieldClaim],
    availability_claims: Sequence[AvailabilityClaim],
    required_fields: Sequence[str],
    as_of: datetime,
    module_id: str,
    file_sha256: str,
    latest_acceptable_file_availability: datetime,
) -> PointInTimeGateResult:
    """Evaluate Issue #51 while preserving every downstream prohibition."""

    point = _require_aware_utc(as_of, field_name="as_of")
    availability_cutoff = _require_aware_utc(
        latest_acceptable_file_availability,
        field_name="latest_acceptable_file_availability",
    )
    resolved: dict[str, str] = {}
    unresolved: list[str] = []
    for field_name in required_fields:
        try:
            claim = resolve_historical_field(
                historical_claims,
                field_name=field_name,
                point_in_time=point,
            )
        except OKXInstrumentVersionError:
            unresolved.append(field_name)
        else:
            resolved[field_name] = claim.value

    specific_file_available_by = earliest_verified_availability(
        availability_claims,
        scope=AvailabilityScope.SPECIFIC_FILE,
        module_id=module_id,
        file_sha256=file_sha256,
    )
    if unresolved:
        outcome = GateOutcome.BLOCKED_INSTRUMENT_VERSION
    elif (
        specific_file_available_by is None
        or specific_file_available_by > availability_cutoff
    ):
        outcome = GateOutcome.BLOCKED_ARCHIVE_TIMING
    else:
        outcome = GateOutcome.GO

    return PointInTimeGateResult(
        as_of=point,
        latest_acceptable_file_availability=availability_cutoff,
        required_fields=tuple(required_fields),
        resolved_fields=resolved,
        unresolved_fields=tuple(unresolved),
        specific_file_available_by=specific_file_available_by,
        outcome=outcome,
    )
