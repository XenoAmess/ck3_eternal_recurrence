"""Recognize the verified vanilla .4 profile for bounded combat research only.

The normalizer's explicit mod-absence contract is distinct from xar_off.
This predicate grants no contact action, forecast fidelity or win probability.
"""
from __future__ import annotations

from collections.abc import Mapping

ACTUAL4_EXE_SHA256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
VERIFIED_XAR_ABSENT = "absent_by_verified_xar_mod_not_loaded"


def is_verified_vanilla_research_profile_v1(
    snapshot: object, *, expected_environment_sha256: str | None = None,
) -> bool:
    """Accept only an existing canonical ordinary/verified-absent binding.

    Its upstream prepared-environment validation owns actual profile/log proof.
    An optional caller-held environment pin narrows this to one frozen profile;
    a missing field or arbitrary null xar_enabled is never enough.
    """
    from .bridge.succession_transition_contract import (
        ORDINARY_CAMPAIGN_SUCCESSION, normalize_succession_lifecycle_binding_v1,
    )

    if not isinstance(snapshot, Mapping):
        return False
    diagnostics = snapshot.get("diagnostics")
    hello = diagnostics.get("hello") if isinstance(diagnostics, Mapping) else None
    if (not isinstance(hello, Mapping) or hello.get("ck3_build_match") is not True
            or hello.get("expected_ck3_version") != "1.20.0.4"
            or not isinstance(hello.get("expected_ck3_sha256"), str)
            or hello["expected_ck3_sha256"].upper() != ACTUAL4_EXE_SHA256):
        return False
    try:
        binding = normalize_succession_lifecycle_binding_v1(snapshot.get("succession_lifecycle"))
    except (TypeError, ValueError):
        return False
    if (binding["lifecycle"] != ORDINARY_CAMPAIGN_SUCCESSION
            or binding["xar_enabled"] is not None
            or binding["pact_contract"] != VERIFIED_XAR_ABSENT
            or binding["source"] != VERIFIED_XAR_ABSENT):
        return False
    if expected_environment_sha256 is not None:
        if (not isinstance(expected_environment_sha256, str)
                or len(expected_environment_sha256) != 64
                or any(ch not in "0123456789abcdef" for ch in expected_environment_sha256)
                or binding["environment_sha256"] != expected_environment_sha256):
            return False
    return True
