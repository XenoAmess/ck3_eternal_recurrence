"""Reusable analysis metadata for the reviewed manager-A event contracts.

This module migrates only conclusions already recorded beside the contracts.  It
does not claim a fresh original-definition audit, and deliberately omits source
hashes and campaign-specific character identities.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

from .records_manager_a import MANAGER_VANILLA_TIMELINE_CONTRACTS_A
from .registry import EXACT_CK3_BUILD, EXACT_CK3_EXE_SHA256


_EXCLUDED_EVENTS: Final = frozenset({
    "epidemic_events.0110",
    "great_holy_war.0011",
    "health.1006",
    "health.2202",
    "health.3001",
    "health.3101",
    "health.3102",
    "health.3103",
})


def _json_safe(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"manager-A analysis value is not JSON-safe: {value!r}")


def _option_projection(contract: Mapping[str, object]) -> dict[str, object]:
    option_count = int(contract["option_count"])
    native_indices = contract.get("native_option_indices", tuple(range(option_count)))
    projection: dict[str, object] = {
        "rendered_option_count": option_count,
        "rendered_native_option_indices": _json_safe(native_indices),
        "selected_authored_option_number": contract["selected_option_number"],
        "selected_native_option_index": contract["selected_native_option_index"],
    }
    for key in ("snapshot_option_count", "snapshot_option_counts"):
        if key in contract:
            projection[key] = _json_safe(contract[key])
    return projection


def _scope_projection(contract: Mapping[str, object]) -> dict[str, object]:
    if "saved_scope_names" in contract:
        saved_scope_name_sets: object = [contract["saved_scope_names"]]
    else:
        saved_scope_name_sets = contract.get("saved_scope_name_sets", ())
    return {
        "saved_scope_name_sets": _json_safe(saved_scope_name_sets),
        "saved_scope_count": contract.get("saved_scope_count", 0),
        "scope_types": _json_safe(contract.get("scope_types", {})),
        "boolean_scope_names": _json_safe(contract.get("boolean_scopes", ())),
        "fixed_identity_scope_names": sorted(
            str(name) for name in dict(contract.get("character_scopes", {}))
        ),
        "distinct_from_fixed_root_scope_names": sorted(
            str(name)
            for name in dict(contract.get("unique_character_scope_excludes", {}))
        ),
        "same_as_any": _json_safe(contract.get("character_scope_matches_any", {})),
        "different_from": _json_safe(
            contract.get("character_scope_differs_from", {})
        ),
        "unavailable_character_scope_names": _json_safe(
            contract.get("unavailable_character_scopes", ())
        ),
    }


_MIGRATED_FROM_BY_EVENT: Final[dict[str, str]] = {}


def _register_origin(source_name: str, event_keys: tuple[str, ...]) -> None:
    origin = f"tools/zg361_phase2_promotion_manager_{source_name}_contracts.py"
    for event_key in event_keys:
        if event_key in _MIGRATED_FROM_BY_EVENT:
            raise ValueError(f"duplicate manager-A analysis origin: {event_key}")
        _MIGRATED_FROM_BY_EVENT[event_key] = origin


_register_origin("befriend", ("befriend_outcome.0002",))
_register_origin("birth", ("birth.3035", "birth.3032", "birth.1003", "birth.1010"))
_register_origin("chancellor", ("chancellor_task.1002",))
_register_origin("council_claim", ("court_chaplain_task.0313",))
_register_origin(
    "court", ("major_decisions.2011", "court_yearly.6030", "court_yearly.6040")
)
_register_origin(
    "death",
    ("death_management.1000", "death_management.1001", "death_management.1008"),
)
_register_origin("debate", ("debate_event.5110",))
_register_origin("health_aging", ("health.7000", "health.7200", "health.7400", "health.7500"))
_register_origin(
    "health",
    (
        "health.7100",
        "health.2201",
        "health.1110",
        "health.1112",
        "health.1001",
        "health.1015",
        "health.3104",
        "health.1101",
        "epidemic_events.5001",
        "epidemic_events.1020",
        "epidemic_events.1050",
    ),
)


_REVIEW_SUMMARY_BY_EVENT: Final[dict[str, str]] = {
    "befriend_outcome.0002": (
        "Success and failure projections were both reviewed; native 2 is the "
        "terminal gentle rejection that avoids friendship and the harsher rejection."
    ),
    "birth.3035": (
        "The sickly-child recovery is already applied before the notice; its only "
        "option is an inert acknowledgement."
    ),
    "birth.3032": (
        "The sickly state is already assigned before this father-side notice; its "
        "only option is an inert acknowledgement."
    ),
    "birth.1003": (
        "Birth and the default name predate the notice; the visible non-twin option "
        "is inert for the contracted player boundary."
    ),
    "birth.1010": (
        "Birth and naming already exist; the sole acknowledgement is inert across "
        "the complete and secret-birth scope projections."
    ),
    "chancellor_task.1002": (
        "The sole unavoidable option cancels the target's one-way truce after the "
        "councillor and truce-holder frame has already been selected."
    ),
    "court_chaplain_task.0313": (
        "Claim fabrication and payment are already complete; the only option applies "
        "the fixed holder opinion result and has no follow-up."
    ),
    "major_decisions.2011": (
        "The courtier is already created and employed; native 1 returns them to the "
        "pool and terminates without a follow-up."
    ),
    "court_yearly.6030": (
        "Only authored option F renders for the reviewed root and it schedules no "
        "follow-up, so the branch is unavoidable."
    ),
    "court_yearly.6040": (
        "Native 2 is the terminal no-follow-up route; native 1 spends gold and "
        "schedules the 6041 continuation."
    ),
    "death_management.1000": (
        "The mutually exclusive spouse-opinion projections each expose one terminal "
        "memory and stress response; the contract selects that rendered response."
    ),
    "death_management.1001": (
        "Adult and minor child-death projections expose one unavoidable response; "
        "each records the deceased child and applies the authored stress effect."
    ),
    "death_management.1008": (
        "The death-of-heir's-spouse notice has one acknowledgement-only option and no "
        "option effect."
    ),
    "debate_event.5110": (
        "Native 1 confirms the already calculated debate winner; native 0 overturns "
        "the result and costs legitimacy."
    ),
    "health.7000": (
        "The onset-of-infirmity frame has one unavoidable acknowledgement and no "
        "alternative branch to optimize."
    ),
    "health.7200": (
        "The withering-mind onset has one mandatory acknowledgement whose sole effect "
        "adds the indicated trait."
    ),
    "health.7400": (
        "The faltering-heart onset has one mandatory acknowledgement whose sole effect "
        "adds the indicated trait."
    ),
    "health.7500": (
        "The fragile-bones onset has one mandatory acknowledgement whose sole effect "
        "adds the indicated trait."
    ),
    "health.7100": (
        "The infirm-health pulse has one enabled acknowledgement and no alternative "
        "to the authored depressed trait effect."
    ),
    "health.2201": (
        "Without a physician, native 6 avoids a hiring follow-up; with a physician, "
        "the reviewed variant selects native 0 safe treatment."
    ),
    "health.1110": (
        "Recovery, immunity and treatment cleanup precede the modal; its only option "
        "is an acknowledgement."
    ),
    "health.1112": (
        "Measles recovery and immunity precede the modal; the only option cannot avoid "
        "the event's unconditional closing blindness roll."
    ),
    "health.1001": (
        "With a physician, native 3 is safe treatment; without one, native 0 starts "
        "the reviewed physician-search path instead of declining treatment."
    ),
    "health.1015": (
        "Disease and immunity are already applied; native 3 is the conservative "
        "treatment route into the reviewed result contracts."
    ),
    "health.3104": (
        "Treatment failure is already applied; native 0 is the acknowledgement that "
        "does not imprison or execute the physician."
    ),
    "health.1101": (
        "Illness and treatment state are removed before the modal; the sole option "
        "acknowledges the completed recovery."
    ),
    "epidemic_events.5001": (
        "Native 0 is the terminal relief route, spending minor gold for supplies, "
        "legitimacy and a positive county modifier."
    ),
    "epidemic_events.1020": (
        "Native 0 is the deterministic positive route: minor treasury cost, legitimacy "
        "gain and the positive county modifier."
    ),
    "epidemic_events.1050": (
        "Native 0 deterministically suppresses the cult and reduces travel danger; "
        "the other routes can or will create the cult modifier."
    ),
}


def _build_analysis() -> dict[str, dict[str, object]]:
    contracts = {
        key: value
        for key, value in MANAGER_VANILLA_TIMELINE_CONTRACTS_A.items()
        if key not in _EXCLUDED_EVENTS
    }
    if set(contracts) != set(_MIGRATED_FROM_BY_EVENT):
        raise ValueError("manager-A analysis origins do not match migrated contracts")
    if set(contracts) != set(_REVIEW_SUMMARY_BY_EVENT):
        raise ValueError("manager-A review summaries do not match migrated contracts")

    result: dict[str, dict[str, object]] = {}
    for event_key, contract in contracts.items():
        option_variants = []
        for variant in contract.get("option_variants", ()):
            effective = {**contract, **dict(variant)}
            option_variants.append(_option_projection(effective))

        scope_variants = []
        for variant in contract.get("scope_variants", ()):
            effective = {**contract, **dict(variant)}
            scope_variants.append(_scope_projection(effective))

        default_option = _option_projection(contract)
        result[event_key] = {
            "exact_build": {
                "game_version": EXACT_CK3_BUILD,
                "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
            },
            "migrated_from": _MIGRATED_FROM_BY_EVENT[event_key],
            "review_summary": _REVIEW_SUMMARY_BY_EVENT[event_key],
            "safe_option": {
                "basis": "existing-reviewed-contract",
                "default": {
                    "selected_authored_option_number": default_option[
                        "selected_authored_option_number"
                    ],
                    "selected_native_option_index": default_option[
                        "selected_native_option_index"
                    ],
                },
                "variants": [
                    {
                        "selected_authored_option_number": projection[
                            "selected_authored_option_number"
                        ],
                        "selected_native_option_index": projection[
                            "selected_native_option_index"
                        ],
                    }
                    for projection in option_variants
                ],
            },
            "option_boundary": {
                "default": default_option,
                "variants": option_variants,
            },
            "scope_boundary": {
                "default": _scope_projection(contract),
                "variants": scope_variants,
                "identity_policy": (
                    "role-and-relation-only; campaign-specific numeric identities omitted"
                ),
            },
            "evidence_boundary": (
                "migrated from existing contract comments/tests; no new original-source "
                "definition review or source hash asserted"
            ),
        }
    return result


MANAGER_A_VANILLA_EVENT_ANALYSIS: Final[dict[str, dict[str, object]]] = (
    _build_analysis()
)


__all__ = ["MANAGER_A_VANILLA_EVENT_ANALYSIS"]
