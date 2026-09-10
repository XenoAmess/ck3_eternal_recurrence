"""Reusable analysis metadata for embedded vanilla-event slice 54-79.

This module migrates only evidence already recorded in the legacy timeline
contracts, their comments, regression tests, and project reports.  Exact-build
source hashes make that knowledge portable without claiming an exhaustive
review of every definition or caller.
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


_SOURCE_FILE_BY_EVENT: Final[dict[str, tuple[str, str]]] = {
    "tgp_dynastic_cycle_events.0040": (
        "events/dlc/tgp/tgp_dynastic_cycle_flavor_events.txt",
        "2260A2AC3F568B3135588E12E4C817846A03AA4BDB16A71C4828490D45F696F3",
    ),
    "tgp_china_yearly.0010": (
        "events/dlc/tgp/tgp_china_yearly_events.txt",
        "4E722C41EE880085BD81E4793BADE40CC75B32933E7DC9AE6ED860C9879CB227",
    ),
    "tgp_china_yearly.0005": (
        "events/dlc/tgp/tgp_china_yearly_events.txt",
        "4E722C41EE880085BD81E4793BADE40CC75B32933E7DC9AE6ED860C9879CB227",
    ),
    "tgp_china_yearly.0015": (
        "events/dlc/tgp/tgp_china_yearly_events.txt",
        "4E722C41EE880085BD81E4793BADE40CC75B32933E7DC9AE6ED860C9879CB227",
    ),
    "tgp_china_yearly.0020": (
        "events/dlc/tgp/tgp_china_yearly_events.txt",
        "4E722C41EE880085BD81E4793BADE40CC75B32933E7DC9AE6ED860C9879CB227",
    ),
    "ep3_emperor_yearly.2200": (
        "events/dlc/ep3/ep3_emperor_yearly_2.txt",
        "5B59252EF885BB605529B1AE76964A03BA447255DB77951CDBF2CB2AE267BDCD",
    ),
    "ep3_emperor_yearly.2240": (
        "events/dlc/ep3/ep3_emperor_yearly_2.txt",
        "5B59252EF885BB605529B1AE76964A03BA447255DB77951CDBF2CB2AE267BDCD",
    ),
    "ep1_flavor.1200": (
        "events/dlc/ep1/ep1_flavor_events.txt",
        "CC4CD67B77F9FA7B83E3B7A5534045F0DBFC1E724C53182E19ED7884BAD10924",
    ),
    "ep3_governor_yearly.3060": (
        "events/dlc/ep3/ep3_governor_yearly_3.txt",
        "2D4291E8293079D009A5F983CE074246D7B9B6CEB6B6569F336A118AF50BAB0F",
    ),
    "ep3_governor_yearly.8130": (
        "events/dlc/ep3/ep3_governor_yearly_8.txt",
        "DA8B840BD0A71705421ABE2FB1C743C451253156917BAB1DC0F6165074194789",
    ),
    "ep3_governor_yearly.8160": (
        "events/dlc/ep3/ep3_governor_yearly_8.txt",
        "DA8B840BD0A71705421ABE2FB1C743C451253156917BAB1DC0F6165074194789",
    ),
    "ep3_governor_yearly.8170": (
        "events/dlc/ep3/ep3_governor_yearly_8.txt",
        "DA8B840BD0A71705421ABE2FB1C743C451253156917BAB1DC0F6165074194789",
    ),
    "chancellor_task.1104": (
        "events/councillor_task_events/chancellor_task_events.txt",
        "EAF95612E4AEC6BF0CEDBC1ACA1C66C8087DD280BC42A60296F824437A5A46EB",
    ),
    "bp1_yearly.9006": (
        "events/yearly_events/bp1_yearly_james.txt",
        "013A6B602C8C344D27944D99020D1DA11E088C00354A542A97C0AE96FED0401B",
    ),
    "yearly.5050": (
        "events/yearly_events/yearly_events_5.txt",
        "BA47BA01C55CF9C7E73F469F9FC1C5F1F439B86AC33EF7C31292B821197F3CC5",
    ),
    "yearly.1040": (
        "events/yearly_events/yearly_events_2.txt",
        "64B778B7B3DFE1056EB0151A7ED3AA7CFB3E6E738E68144006BAF97E93E0A3E8",
    ),
    "yearly.1041": (
        "events/yearly_events/yearly_events_2.txt",
        "64B778B7B3DFE1056EB0151A7ED3AA7CFB3E6E738E68144006BAF97E93E0A3E8",
    ),
    "ep3_governor_yearly.8080": (
        "events/dlc/ep3/ep3_governor_yearly_8.txt",
        "DA8B840BD0A71705421ABE2FB1C743C451253156917BAB1DC0F6165074194789",
    ),
    "sway_ongoing.1002": (
        "events/scheme_events/sway_scheme/sway_ongoing_events.txt",
        "F646FAE510A66A87A01B464140F7206921B141E6F3D3D06CE20570C18C7B9759",
    ),
    "sway_ongoing.5011": (
        "events/scheme_events/sway_scheme/sway_ongoing_events.txt",
        "F646FAE510A66A87A01B464140F7206921B141E6F3D3D06CE20570C18C7B9759",
    ),
    "sway_outcome.1001": (
        "events/scheme_events/sway_scheme/sway_outcome_events.txt",
        "44AA74F211D47F225BA5AF3CE7E6A23D6BC08B8691856BC14975A7D37DFC39BC",
    ),
    "tgp_interaction_event.0016": (
        "events/dlc/tgp/tgp_interaction_events.txt",
        "C845EBEB53A7D80E5155AF1D6FC42D03A86931C7088613CFA39A19B0DF468C75",
    ),
    "tgp_interaction_event.0030": (
        "events/dlc/tgp/tgp_interaction_events.txt",
        "C845EBEB53A7D80E5155AF1D6FC42D03A86931C7088613CFA39A19B0DF468C75",
    ),
    "scheme_critical_moments.1134": (
        "events/scheme_events/scheme_critical_moments_events.txt",
        "A51C5D0ED3CE9B475A25B7857829B098A4D5A38B4D89044C68C4813CC32EEA26",
    ),
    "realm_maintenance.2001": (
        "events/realm_maintenance_events.txt",
        "A4ED406F9ADFB9AE6A49C3299198F5D19DAA683535E43BF76FDEA0348E32659D",
    ),
    "sway_outcome.2001": (
        "events/scheme_events/sway_scheme/sway_outcome_events.txt",
        "44AA74F211D47F225BA5AF3CE7E6A23D6BC08B8691856BC14975A7D37DFC39BC",
    ),
}


_REVIEW_SUMMARIES: Final[dict[str, str]] = {
    "tgp_dynastic_cycle_events.0040": (
        "Silk Road investment prompt; exact source and R406 live evidence bind "
        "both the advancement-only full projection and ordinary two-choice "
        "projection to the same bounded opt-out."
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
    source_path, source_sha256 = _SOURCE_FILE_BY_EVENT[event_key]
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
        "source_sha256": {source_path: source_sha256},
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
