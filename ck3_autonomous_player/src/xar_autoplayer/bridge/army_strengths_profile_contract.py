"""Explicit Army query profiles and actual retained-journal coverage.

Coverage describes exported fields, not whether an observation is ready.
The ordinary profile retains the existing military inputs and omits only the
nine retained phase journals. Full-profile null observations remain null.
"""

from __future__ import annotations

from .army_observed_phase_contract_12004 import FAMILIES

ARMY_STRENGTHS_PROFILE_KEY = "army_strengths_profile"
ARMY_OBSERVED_PHASE_COVERAGE_KEY = "army_observed_phase_coverage"
ORDINARY_CORE_PROFILE = "ordinary_core_v1"
OBSERVED_HISTORY_FULL_PROFILE = "observed_history_full_v1"
OBSERVED_PHASE_KEYS = tuple(FAMILIES)
ARMY_STRENGTHS_CACHE_VALIDATION_SCHEMA = "army-strengths-profile-cache-v1"

_PROFILE_COVERAGE = {
    ORDINARY_CORE_PROFILE: "not_requested",
    OBSERVED_HISTORY_FULL_PROFILE: "exported_retained",
}


def require_army_strengths_profile(profile: object) -> str:
    """Reject implicit, unknown, or incorrectly typed profile requests."""
    if not isinstance(profile, str) or profile not in _PROFILE_COVERAGE:
        raise ValueError("unsupported army-strengths profile")
    return profile


def validate_army_strengths_profile_coverage(
    payload: dict[str, object], *, expected_profile: str,
) -> None:
    """Check the echoed profile against fields actually present in each row.

    Call after expanding shared wire inputs and before normalizing rows. The
    ordinary row/family validators remain responsible for values and scope.
    """
    profile = require_army_strengths_profile(expected_profile)
    if not isinstance(payload, dict):
        raise ValueError("army-strengths profile result must be an object")
    if payload.get(ARMY_STRENGTHS_PROFILE_KEY) != profile:
        raise ValueError("army-strengths result profile disagrees with request")
    if payload.get(ARMY_OBSERVED_PHASE_COVERAGE_KEY) != _PROFILE_COVERAGE[profile]:
        raise ValueError("army-strengths observed coverage disagrees with profile")
    rows = payload.get("army_strengths")
    if not isinstance(rows, list):
        raise ValueError("profiled army-strengths rows must be an array")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("profiled army-strengths row must be an object")
        present = [key in row for key in OBSERVED_PHASE_KEYS]
        if profile == ORDINARY_CORE_PROFILE and any(present):
            raise ValueError("ordinary Army profile exported a retained phase journal")
        if profile == OBSERVED_HISTORY_FULL_PROFILE and not all(present):
            raise ValueError("full Army profile omitted a retained phase journal")
