"""Migrated analysis metadata for the first embedded vanilla-event slice.

This module deliberately migrates only conclusions already recorded beside the
legacy contracts.  It does not claim a fresh full-definition review, and it
does not manufacture source-file hashes that the existing evidence did not
record.
"""

from __future__ import annotations

from typing import Final

from .records_embedded import EMBEDDED_VANILLA_TIMELINE_CONTRACTS
from .registry import EXACT_CK3_BUILD, EXACT_CK3_EXE_SHA256


EMBEDDED_A_EVENT_KEYS: Final[tuple[str, ...]] = (
    "ep3_governor_yearly.8120",
    "bp1_yearly.5725",
    "bp1_yearly.9007",
    "culture_notification.1111",
    "intrigue_scheming.1202",
    "chancellor_task.1102",
    "tgp_movement_events.0070",
    "tgp_movement_events.0080",
    "tgp_movement_events.0050",
    "tgp_movement_events.0060",
    "tgp_movement_events.0150",
    "ep3_decisions_event.2001",
    "adultery.0002",
    "health.1010",
    "stress_threshold.2202",
    "stress_threshold.1721",
    "stress_threshold_special.1001",
    "ep1_flavor.0021",
    "ep1_flavor.2040",
    "epidemic_events.1100",
    "epidemic_events.1060",
    "faction_demand.0101",
    "faction_demand.1001",
    "char_interaction.0240",
    "char_interaction.0251",
    "char_interaction.0370",
    "physician_epidemic_events.1040",
)


_REVIEW_NOTES: Final[dict[str, tuple[str, str]]] = {
    "ep3_governor_yearly.8120": (
        "Flood/storm county damage occurs before choice; the three choices then "
        "differ in duel, spending, and follow-on modifier impact.",
        "Native option 2 avoids the stewardship duel and treasury/county "
        "modifier route, confining the response to the recorded minor effects.",
    ),
    "bp1_yearly.5725": (
        "Khutulun matchmaking invitation with a seven-day follow-up branch and "
        "one terminal response.",
        "Native option 1 ends the encounter immediately and avoids occupying the "
        "timeline with the recorded follow-up chain.",
    ),
    "bp1_yearly.9007": (
        "Doppelganger encounter whose court/story branch is visible while the "
        "murder branch was hidden in the recorded non-sadistic projection.",
        "Native option 2 dismisses the temporary character instead of retaining "
        "it or starting the durable court story.",
    ),
    "culture_notification.1111": (
        "Culture-divergence founder and non-founder choices are mutually "
        "exclusive acknowledgements with the same no-gameplay-effect tooltip.",
        "Native option 1 is the sole rendered non-founder acknowledgement in the "
        "recorded projection.",
    ),
    "intrigue_scheming.1202": (
        "Hired-spy follow-up offering removal, durable retention, or killing of "
        "the generated spy.",
        "Native option 0 removes the temporary spy and limits the result to the "
        "recorded minor lifestyle experience.",
    ),
    "chancellor_task.1102": (
        "Chancellor side effect in which the truce target is already selected "
        "and the event exposes one authored cancellation choice.",
        "Native option 0 is the only continuation; the strict scope and one-button "
        "shape are the safety guard because no acknowledgement-only route exists.",
    ),
    "tgp_movement_events.0070": (
        "Celestial-government study event with alternatives that mutate one or "
        "both characters' skills.",
        "Native option 0 avoids player resource and skill mutation and keeps only "
        "the recorded friendship/stress effects.",
    ),
    "tgp_movement_events.0080": (
        "Celestial family-subsidy request with one hidden conservative-movement "
        "choice in the recorded projection.",
        "Native option 3 avoids the family-gold transfer, estate modifier, and "
        "movement influence/power mutations of the other visible routes.",
    ),
    "tgp_movement_events.0050": (
        "Merit-elder invitation whose old-elder route was hidden in the recorded "
        "two-of-three option projection.",
        "Native option 2 is terminal and avoids installing a new elder relation "
        "or changing merit.",
    ),
    "tgp_movement_events.0060": (
        "Movement-rival event whose observed projection excludes the "
        "intrigue-focus-only first authored option.",
        "Native option 2 is the narrow non-hostile, non-religious continuation, "
        "avoiding scheme creation and the faith-dependent branch.",
    ),
    "tgp_movement_events.0150": (
        "Shinto-monk visit with the diplomat-only alliance route hidden in the "
        "recorded manager frame.",
        "Native option 3 is deterministic and terminal, avoiding the conversion "
        "modifier and random conversion duel.",
    ),
    "ep3_decisions_event.2001": (
        "Administrative-vassal confirmation request that can recur for distinct "
        "requesting vassals during one observation window.",
        "Native option 1 refuses and terminates the request instead of opening the "
        "multi-event confirmation ceremony.",
    ),
    "adultery.0002": (
        "Spouse-suspicion event with trigger-dependent visible choices and no "
        "campaign-global one-shot gate in the recorded yearly picker analysis.",
        "Native option 3 is the unconditional no-effect terminal response, "
        "avoiding confrontation, a duel, and spymaster-task mutation.",
    ),
    "health.1010": (
        "Smallpox contraction is already applied before the modal; treatment "
        "choices depend on physician, travel, and mystic state.",
        "Native option 6 is the unconditional terminal route and opens no "
        "follow-up treatment chain.",
    ),
    "stress_threshold.2202": (
        "Response to another character's boiling-anger break; the rival-dependent "
        "first option was hidden in the recorded frame.",
        "Native option 1 is the sole rendered route and only reduces the player's "
        "stress under the recorded no-rival boundary.",
    ),
    "stress_threshold.1721": (
        "Impostor-syndrome break whose recorded choices were inappetetic, "
        "confider, and additional stress; later thresholds may select it again.",
        "Native option 9 chooses confider, reducing stress without starvation or "
        "the unconditional stress-gain fallback.",
    ),
    "stress_threshold_special.1001": (
        "Grief break with three recorded source-defined projections, including "
        "one confidant and two no-confidant scope shapes.",
        "Use native 6 when confider is present, native 4 for the recorded "
        "inappetetic no-confidant shape, and native 1 for the recorded "
        "depressed/drunkard/frozen-grief shape.",
    ),
    "ep1_flavor.0021": (
        "Royal-court language quarrel with random-duel and durable-modifier "
        "alternatives.",
        "Native option 1 avoids both the random duel and durable modifier while "
        "retaining the recorded positive court/culture effects.",
    ),
    "ep1_flavor.2040": (
        "Exotic-arms delivery with source-authored artifact branches and optional "
        "quality, weapon, or armor scope flags.",
        "Native option 2 is the terminal refusal and avoids spending major gold "
        "or transferring the generated artifact.",
    ),
    "epidemic_events.1100": (
        "Per-epidemic outbreak notification with mutually exclusive physician "
        "projections; outbreak effects have already happened before the modal.",
        "Native option 0 avoids both later physician/health event chains and "
        "limits the choice to the recorded conditional governor-XP effect.",
    ),
    "epidemic_events.1060": (
        "Plague-scapegoat response after the witch-hunt story is created, with "
        "the very-high-piety option hidden in the recorded frame.",
        "Native option 2 deterministically slows trials and starts no additional "
        "event, while both visible routes retain their recorded county modifier.",
    ),
    "faction_demand.0101": (
        "Liberty-faction ultimatum with optional co-emperor projection and routes "
        "that either lower realm authority or begin the faction war.",
        "Native option 2 preserves current law and title state and leaves the "
        "source-authored war visible to the gameplay layer.",
    ),
    "faction_demand.1001": (
        "Populist ultimatum with conversion, surrender, and refusal projections; "
        "distinct factions may issue independent demands.",
        "Native option 3 refuses and starts the faction war, preserving the "
        "current title and roster invariants used by the observation.",
    ),
    "char_interaction.0240": (
        "Pardon letter emitted after the interaction has already resolved; its "
        "single authored option has no effect.",
        "Native option 0 is acknowledgement-only after the strict actor, recipient, "
        "hook, and unavailable-role shape is matched.",
    ),
    "char_interaction.0251": (
        "AI-vassal contract-lowering notice emitted after obligation mutation and "
        "hook consumption have already occurred.",
        "Native option 0 is acknowledgement-only after the strict interaction "
        "scope shape is matched.",
    ),
    "char_interaction.0370": (
        "Cease-paying-tribute notice emitted after the tributary relation ended; "
        "retaliation was hidden in the recorded frame.",
        "Native option 0 is the sole rendered acknowledgement and is inert under "
        "the recorded can-retaliate-false boundary.",
    ),
    "physician_epidemic_events.1040": (
        "Royal-alms proposal during a major epidemic, offering county modifiers "
        "and infection RNG or a terminal refusal.",
        "Native option 1 avoids the ten-year modifiers, infection roll, and "
        "follow-up event, retaining only recorded piety/stress effects.",
    ),
}


_OPTION_KEYS: Final[tuple[str, ...]] = (
    "option_count",
    "snapshot_option_count",
    "snapshot_option_counts",
    "native_option_indices",
    "selected_option_number",
    "selected_native_option_index",
)
_SCOPE_KEYS: Final[tuple[str, ...]] = (
    "saved_scope_count",
    "saved_scope_name_sets",
    "scope_types",
    "optional_scope_types",
    "boolean_scopes",
    "unavailable_character_scopes",
    "character_scope_differs_from",
    "character_scope_matches_any",
)
_CAMPAIGN_BINDING_KEYS: Final[tuple[str, ...]] = (
    "date_raw",
    "root_character_id",
    "character_scopes",
    "unique_character_scope_excludes",
)


def _json_safe(value: object) -> object:
    """Project the selected legacy boundary fields to JSON-native containers."""

    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _selected_fields(
    contract: dict[str, object], names: tuple[str, ...]
) -> dict[str, object]:
    return {
        name: _json_safe(contract[name])
        for name in names
        if name in contract
    }


def _occurrence_boundary(contract: dict[str, object]) -> dict[str, object]:
    if "occurrence_policy" in contract:
        return {"occurrence_policy": contract["occurrence_policy"]}
    if "max_occurrences" in contract:
        return {"max_occurrences": contract["max_occurrences"]}
    return {"status": "not-specified-in-existing-contract"}


def _build_analysis() -> dict[str, dict[str, object]]:
    actual_prefix = tuple(EMBEDDED_VANILLA_TIMELINE_CONTRACTS)[:27]
    if actual_prefix != EMBEDDED_A_EVENT_KEYS:
        raise RuntimeError(
            "embedded analysis slice no longer matches the first 27 keys"
        )
    if set(_REVIEW_NOTES) != set(EMBEDDED_A_EVENT_KEYS):
        raise RuntimeError(
            "embedded analysis review notes do not exactly cover the slice"
        )

    analysis: dict[str, dict[str, object]] = {}
    for event_key in EMBEDDED_A_EVENT_KEYS:
        contract = EMBEDDED_VANILLA_TIMELINE_CONTRACTS[event_key]
        review_summary, rationale = _REVIEW_NOTES[event_key]
        safe_option = _selected_fields(contract, _OPTION_KEYS)
        safe_option["rationale"] = rationale
        if "option_variants" in contract:
            safe_option["variants"] = _json_safe(contract["option_variants"])

        analysis[event_key] = {
            "exact_build": {
                "game_version": EXACT_CK3_BUILD,
                "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
            },
            "migrated_from": {
                "module": (
                    "xar_autoplayer.vanilla_events.records_embedded."
                    "EMBEDDED_VANILLA_TIMELINE_CONTRACTS"
                ),
                "evidence": "existing-contract-comments-docs-and-tests",
                "review_kind": "migration-only-no-new-full-definition-review",
            },
            "review_summary": review_summary,
            "safe_option": safe_option,
            "existing_boundaries": {
                "date_policy": contract.get("date_policy", "legacy-fixed-date"),
                "occurrence": _occurrence_boundary(contract),
                "scope_shape": _selected_fields(contract, _SCOPE_KEYS),
                "campaign_specific_binding_fields": [
                    name for name in _CAMPAIGN_BINDING_KEYS if name in contract
                ],
                "boundary_note": (
                    "Campaign IDs and dates remain legacy live-contract bindings; "
                    "this metadata does not promote them to universal event facts."
                ),
            },
        }
    return analysis


VANILLA_EMBEDDED_A_ANALYSIS: Final[dict[str, dict[str, object]]] = (
    _build_analysis()
)


__all__ = [
    "EMBEDDED_A_EVENT_KEYS",
    "VANILLA_EMBEDDED_A_ANALYSIS",
]
