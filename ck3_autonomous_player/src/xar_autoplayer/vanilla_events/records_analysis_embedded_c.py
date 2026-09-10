"""Reusable analysis metadata for embedded vanilla-event slice 54-79.

This module migrates only evidence already recorded in the legacy timeline
contracts, their comments, regression tests, and project reports.  It does not
claim a new exhaustive review of the corresponding vanilla definitions.
"""

from __future__ import annotations

from typing import Final

from .records_embedded_c import EMBEDDED_C_VANILLA_TIMELINE_CONTRACTS
from .registry import EXACT_CK3_BUILD, EXACT_CK3_EXE_SHA256


EMBEDDED_C_EVENT_KEYS: Final[tuple[str, ...]] = (
    "tgp_dynastic_cycle_events.0040",
    "tgp_china_yearly.0010",
    "tgp_china_yearly.0005",
    "tgp_china_yearly.0015",
    "tgp_china_yearly.0020",
    "ep3_emperor_yearly.2200",
    "ep3_emperor_yearly.2240",
    "ep1_flavor.1200",
    "ep3_governor_yearly.3060",
    "ep3_governor_yearly.8130",
    "ep3_governor_yearly.8160",
    "ep3_governor_yearly.8170",
    "chancellor_task.1104",
    "bp1_yearly.9006",
    "yearly.5050",
    "yearly.1040",
    "yearly.1041",
    "ep3_governor_yearly.8080",
    "sway_ongoing.1002",
    "sway_ongoing.5011",
    "sway_outcome.1001",
    "tgp_interaction_event.0016",
    "tgp_interaction_event.0030",
    "scheme_critical_moments.1134",
    "realm_maintenance.2001",
    "sway_outcome.2001",
)


_REVIEW_SUMMARIES: Final[dict[str, str]] = {
    "tgp_dynastic_cycle_events.0040": (
        "Silk Road investment prompt; the existing review distinguishes the "
        "treasury/modifier and fascination branches from the bounded opt-out."
    ),
    "tgp_china_yearly.0010": (
        "Charlatan-poet prompt with one hidden authored option; the existing "
        "review freezes a three-of-four rendered projection and a temporary role."
    ),
    "tgp_china_yearly.0005": (
        "Grieving-child prompt whose six generated or selected character roles "
        "are constrained by role relationships rather than allocator IDs."
    ),
    "tgp_china_yearly.0015": (
        "Merchant dispute with two distinct event-created merchants and one "
        "hidden authored option in the observed three-of-four projection."
    ),
    "tgp_china_yearly.0020": (
        "Unpaid-tax prompt with dynamic liege/councillor roles and a typed county; "
        "both choices mutate state, so the existing review selects the bounded one."
    ),
    "ep3_emperor_yearly.2200": (
        "Embezzlement offer; the accepted branch carries durable governance and "
        "character-state effects while refusal is the bounded alternative."
    ),
    "ep3_emperor_yearly.2240": (
        "Scholar encounter; the first two branches introduce duel or resource "
        "effects and the third is the existing explicit opt-out."
    ),
    "ep1_flavor.1200": (
        "Learned-eunuch encounter; three branches buy durable player modifiers "
        "and the fourth confines effects to the event character and stress."
    ),
    "ep3_governor_yearly.3060": (
        "Imperial succession notice with one hidden authored option; the existing "
        "contract binds title/government scope shape across a finite date window."
    ),
    "ep3_governor_yearly.8130": (
        "Arbitrary-tax prompt; the fourth branch avoids the modifier, treasury, "
        "influence, and governance mutations identified by the existing review."
    ),
    "ep3_governor_yearly.8160": (
        "Equitable-access prompt with an event-created administrator; the existing "
        "review uses relationship constraints and the empty dismissal branch."
    ),
    "ep3_governor_yearly.8170": (
        "Local-defense prompt; the first three branches have broader resource, "
        "duel, modifier, or truce effects and refusal is the bounded route."
    ),
    "chancellor_task.1104": (
        "One-option foreign-affairs continuation; role aliases bind the active "
        "chancellor and the distinct neighboring ruler before acknowledgement."
    ),
    "bp1_yearly.9006": (
        "Sinful-courtier encounter; the frozen non-craven frame has one dynamic "
        "courtier and the second option avoids friendship mutation."
    ),
    "yearly.5050": (
        "Slighted-spouse encounter; option two terminates without removing the "
        "courtier, entering a duel, or scheduling the reviewed follow-ups."
    ),
    "yearly.1040": (
        "Suspicious-letter opening; the existing good-surprise frame binds one "
        "third-party character and two flags and chooses the shortest continuation."
    ),
    "yearly.1041": (
        "Immediate one-option disclosure reached from yearly.1040 option one; it "
        "reuses the already-bound character and flag frame."
    ),
    "ep3_governor_yearly.8080": (
        "Annual magistrate prompt with one event-created role; option one avoids "
        "the kill, recruitment, and embezzlement effects of the alternatives."
    ),
    "sway_ongoing.1002": (
        "Compliment letter whose first three rendered choices are randomized from "
        "twelve authored choices; the fixed thirteenth option is effect-free."
    ),
    "sway_ongoing.5011": (
        "Sway visit opening; the first option starts a delayed event chain while "
        "the second terminates with only bounded stress relief."
    ),
    "sway_outcome.1001": (
        "Successful sway outcome; option two applies the deterministic smaller "
        "opinion result and ends the scheme without a duel."
    ),
    "tgp_interaction_event.0016": (
        "Military-aid completion letter; the interaction mutation precedes the "
        "window and the sole event option is an empty acknowledgement."
    ),
    "tgp_interaction_event.0030": (
        "Elder-break notice observed through two exact payload name sets; the "
        "relationship changes before rendering and the sole option is empty."
    ),
    "scheme_critical_moments.1134": (
        "Slander reaction notice; the state change occurs in immediate and the "
        "single option only acknowledges one of two frozen boolean-scope shapes."
    ),
    "realm_maintenance.2001": (
        "Title-inheritance notice delivered after transfer; the existing contract "
        "preserves its title/government and character-role shape."
    ),
    "sway_outcome.2001": (
        "Failed-sway misunderstanding with one unavoidable acknowledgement after "
        "the typed target opinion loss and scheme-ending outcome."
    ),
}


_SAFE_OPTION_RATIONALES: Final[dict[str, str]] = {
    "tgp_dynastic_cycle_events.0040": "avoids gold spending and durable investment effects",
    "tgp_china_yearly.0010": "avoids merit/dread changes and retaining the generated character",
    "tgp_china_yearly.0005": "avoids court/guardian changes and promotion-relevant merit gain",
    "tgp_china_yearly.0015": "avoids merit and treasury changes before temporary-role cleanup",
    "tgp_china_yearly.0020": "avoids the long county modifier and major influence cost",
    "ep3_emperor_yearly.2200": "refuses the durable embezzlement and governance mutations",
    "ep3_emperor_yearly.2240": "uses the explicit opt-out instead of duel or resource mutations",
    "ep1_flavor.1200": "avoids buying a fifteen-year player modifier",
    "ep3_governor_yearly.3060": "selects the rendered no-effect acknowledgement",
    "ep3_governor_yearly.8130": "avoids modifier, treasury, influence, and governance mutations",
    "ep3_governor_yearly.8160": "uses the empty dismissal and lets common cleanup dispose of the administrator",
    "ep3_governor_yearly.8170": "avoids treasury, governance, duel, modifier, truce, and influence changes",
    "chancellor_task.1104": "acknowledges the only authored continuation",
    "bp1_yearly.9006": "avoids creating or advancing a friendship",
    "yearly.5050": "terminates without removal, duel, or delayed follow-up",
    "yearly.1040": "takes the shorter deterministic disclosure continuation",
    "yearly.1041": "acknowledges the only authored continuation",
    "ep3_governor_yearly.8080": "avoids killing, recruiting, or taking gold from the magistrate",
    "sway_ongoing.1002": "uses the fixed effect-free fallback after randomized compliments",
    "sway_ongoing.5011": "ends the branch instead of starting a delayed exploration chain",
    "sway_outcome.1001": "avoids a duel and applies the deterministic smaller outcome",
    "tgp_interaction_event.0016": "acknowledges the sole effect-free option",
    "tgp_interaction_event.0030": "acknowledges the sole empty option after the prior relationship change",
    "scheme_critical_moments.1134": "acknowledges the sole empty option after immediate effects",
    "realm_maintenance.2001": "acknowledges the only option after the title transfer",
    "sway_outcome.2001": "acknowledges the unavoidable failed-sway outcome",
}


def _scope_names(contract: dict[str, object]) -> list[str]:
    """Return only established scope names, never historical numeric identities."""

    names: set[str] = set()
    for field in (
        "character_scopes",
        "unique_character_scope_excludes",
        "character_scope_matches_any",
        "character_scope_differs_from",
        "scope_types",
    ):
        value = contract.get(field, {})
        if isinstance(value, dict):
            names.update(str(name) for name in value)
    for field in ("unavailable_character_scopes", "boolean_scopes"):
        value = contract.get(field, ())
        if isinstance(value, (list, tuple)):
            names.update(str(name) for name in value)
    return sorted(names)


def _sequence_as_json(value: object) -> list[object] | None:
    if not isinstance(value, (list, tuple)):
        return None
    result: list[object] = []
    for item in value:
        if isinstance(item, (list, tuple)):
            result.append(list(item))
        else:
            result.append(item)
    return result


def _existing_boundaries(contract: dict[str, object]) -> dict[str, object]:
    """Project the already-established shape limits without inventing evidence."""

    result: dict[str, object] = {
        "evidence_class": "migrated-existing-review",
        "date_policy": contract.get("date_policy", "legacy-exact-date"),
        "scope_names": _scope_names(contract),
        "saved_scope_count": contract.get("saved_scope_count"),
        "option_count": contract["option_count"],
        "snapshot_option_count": contract.get(
            "snapshot_option_count", contract["option_count"]
        ),
        "campaign_identity_values_promoted_to_universal_facts": False,
        "exhaustive_variant_review_claimed": False,
    }
    for source, target in (
        ("saved_scope_name_sets", "saved_scope_name_sets"),
        ("boolean_scope_name_sets", "boolean_scope_name_sets"),
        ("native_option_indices", "native_option_indices"),
        ("native_option_suffix", "native_option_suffix"),
        ("native_option_prefix_range", "native_option_prefix_range"),
    ):
        projected = _sequence_as_json(contract.get(source))
        if projected is not None:
            result[target] = projected
    if "max_occurrences" in contract:
        result["max_occurrences"] = contract["max_occurrences"]
    if "occurrence_policy" in contract:
        result["occurrence_policy"] = contract["occurrence_policy"]
    return result


def _record(event_key: str, order: int) -> dict[str, object]:
    contract = EMBEDDED_C_VANILLA_TIMELINE_CONTRACTS[event_key]
    return {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        },
        "migrated_from": {
            "module": "xar_autoplayer.vanilla_events.records_embedded",
            "symbol": "EMBEDDED_VANILLA_TIMELINE_CONTRACTS",
            "default_order_1_based": order,
            "evidence": "existing contract comments, tests, and project reports",
        },
        "review_summary": _REVIEW_SUMMARIES[event_key],
        "safe_option": {
            "selected_option_number": contract["selected_option_number"],
            "selected_native_option_index": contract[
                "selected_native_option_index"
            ],
            "rationale": _SAFE_OPTION_RATIONALES[event_key],
        },
        "existing_boundaries": _existing_boundaries(contract),
    }


VANILLA_EMBEDDED_C_ANALYSIS: Final[dict[str, dict[str, object]]] = {
    event_key: _record(event_key, order)
    for order, event_key in enumerate(EMBEDDED_C_EVENT_KEYS, start=54)
}


__all__ = [
    "EMBEDDED_C_EVENT_KEYS",
    "VANILLA_EMBEDDED_C_ANALYSIS",
]
