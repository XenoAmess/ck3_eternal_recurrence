"""Migrated analysis metadata for the first embedded vanilla-event slice.

This module deliberately migrates only conclusions already recorded beside the
legacy contracts.  It does not claim a fresh full-definition review, and it
does not manufacture source-file hashes that the existing evidence did not
record.
"""

from __future__ import annotations

from typing import Final

from .records_embedded_a import (
    EMBEDDED_A_VANILLA_OBSERVATIONS as _LEGACY_MIGRATION_OBSERVATIONS,
    EMBEDDED_A_VANILLA_TIMELINE_CONTRACTS,
)
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
    "stress_threshold.1011",
    "trait_specific_interactions.0011",
    "travel_completion_event.1000",
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
        "Impostor-syndrome break with three source-reviewed live projections; "
        "later stress thresholds may select it again.",
        "Use native 9 when confider is rendered. In the recorded no-confidant "
        "projection, native 10 lowers stress and avoids both advancing the "
        "already-owned inappetetic starvation chain and native 12 stress gain.",
    ),
    "stress_threshold.1011": (
        "Wanton-desires mental break with the rakish, reclusive, and endure "
        "routes rendered in the R498 player projection.",
        "Native option 5 changes only the played character's stress and avoids "
        "the coping-trait, brothel, relationship, and faith mutations of the "
        "other authored routes.",
    ),
    "trait_specific_interactions.0011": (
        "Mourning-poem response sent by a distinct actor to the played recipient; "
        "the R500 projection rendered duel, accept, and reject routes.",
        "Native option 1 deterministically accepts the poem, avoiding both the "
        "random diplomacy duel and the rejection route's opinion loss and "
        "possible rivalry.",
    ),
    "travel_completion_event.1000": (
        "Generic travel completion with mutually exclusive already-home and "
        "return-home options; R502 rendered only the already-home route.",
        "Native option 0 is the sole legal live response and has no explicit "
        "action beyond a possible trait-conditioned stress decrease.",
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
    "scope_variants",
)
_CAMPAIGN_BINDING_KEYS: Final[tuple[str, ...]] = (
    "date_raw",
    "date_raw_range",
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


def _contains_numeric_campaign_identity(value: object) -> bool:
    if type(value) is int:
        return True
    if isinstance(value, dict):
        return any(
            _contains_numeric_campaign_identity(item)
            for item in value.values()
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_numeric_campaign_identity(item) for item in value)
    return False


def _occurrence_boundary(contract: dict[str, object]) -> dict[str, object]:
    if "occurrence_policy" in contract:
        return {"occurrence_policy": contract["occurrence_policy"]}
    if "max_occurrences" in contract:
        return {"max_occurrences": contract["max_occurrences"]}
    return {"status": "not-specified-in-existing-contract"}


def _build_analysis() -> dict[str, dict[str, object]]:
    actual_prefix = tuple(EMBEDDED_A_VANILLA_TIMELINE_CONTRACTS)
    if actual_prefix != EMBEDDED_A_EVENT_KEYS:
        raise RuntimeError(
            "embedded analysis slice no longer matches the first 28 keys"
        )
    if set(_REVIEW_NOTES) != set(EMBEDDED_A_EVENT_KEYS):
        raise RuntimeError(
            "embedded analysis review notes do not exactly cover the slice"
        )

    analysis: dict[str, dict[str, object]] = {}
    for event_key in EMBEDDED_A_EVENT_KEYS:
        contract = EMBEDDED_A_VANILLA_TIMELINE_CONTRACTS[event_key]
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
                    name
                    for name in _CAMPAIGN_BINDING_KEYS
                    if name in contract
                    and _contains_numeric_campaign_identity(contract[name])
                ],
                "boundary_note": (
                    "The reusable contract binds player identity through $player "
                    "and otherwise relies on typed roles and scope relations. "
                    "Campaign dates and numeric identities remain migration-only "
                    "observations, not universal event facts."
                ),
            },
        }

    movement_rival_analysis = analysis["tgp_movement_events.0060"]
    movement_rival_analysis["migrated_from"]["review_kind"] = (
        "exact-build-original-definition-and-live-repeat-review"
    )
    movement_rival_analysis.update({
        "source_sha256": {
            "events/dlc/tgp/tgp_movement_events.txt": (
                "D9B172FC6C9F81216BE580C1B65DA7720CAA6EF21F049AB316361E17D3710BC6"
            ),
            "common/on_action/dlc/tgp/tgp_china_yearly_on_actions.txt": (
                "4D6F5379E40304B56C5C1A914E8A0EE3998E8023174DC52F7E5072F7CFA40454"
            ),
            "common/on_action/mandate_on_actions.txt": (
                "C129A3C09A32BE3F2D55686099AB3FC97DBC286E18D75968B8C2553349AD731D"
            ),
            "common/on_action/yearly_on_actions.txt": (
                "0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA"
            ),
        },
        "definition_lines": "1165-1412",
        "caller_semantics": (
            "the TGP yearly pool includes the event at weight 100, the general "
            "yearly pool at weight 200, and the placate-movements mandate pool "
            "at weight 100; none is one-shot and the event has a ten-year cooldown"
        ),
        "trigger_boundary": (
            "available adult celestial-government ruler with TGP enabled, a "
            "decided dynastic-cycle movement, and at least one valid ruler in a "
            "different movement"
        ),
        "immediate_effect": (
            "saves the player's movement and selects a valid rival ruler plus "
            "that ruler's different movement, favoring potential or actual rivals "
            "and movement leaders"
        ),
        "option_semantics": {
            "0": (
                "intrigue-focus-only route that increases the player's movement "
                "power, reduces the rival movement, adds intrigue XP, and applies "
                "trait-dependent stress"
            ),
            "1": (
                "starts or strengthens a hostile challenge-status scheme against "
                "the rival, reduces rival movement power, and applies stress"
            ),
            "2": (
                "increases only the player's movement power by the medium value "
                "and applies trait-dependent stress"
            ),
            "3": (
                "grants piety plus court-chaplain opinion when the faith treats "
                "calm or compassionate as a virtue, otherwise minor prestige; "
                "also applies trait-dependent stress"
            ),
        },
        "after_effect": None,
        "safe_option_rationale": (
            "native2 avoids a hostile scheme, avoids reducing another movement, "
            "and does not inspect faith; its bounded effect is a medium power gain "
            "for the player's existing movement plus possible personality stress"
        ),
        "frequency_boundary": (
            "R422 observed instances 1115 and 1122 for the same played manager "
            "7,810 in-game days apart; the source cooldown is ten years and all "
            "three candidate callers permit later recurrence"
        ),
    })
    movement_rival_analysis["existing_boundaries"]["occurrence"] = {
        "occurrence_policy": "repeatable-within-product-observation-window"
    }

    movement_study_analysis = analysis["tgp_movement_events.0070"]
    movement_study_analysis["migrated_from"]["review_kind"] = (
        "exact-build-original-definition-and-live-repeat-review"
    )
    movement_study_analysis.update({
        "source_sha256": {
            "events/dlc/tgp/tgp_movement_events.txt": (
                "D9B172FC6C9F81216BE580C1B65DA7720CAA6EF21F049AB316361E17D3710BC6"
            ),
            "common/on_action/dlc/tgp/tgp_china_yearly_on_actions.txt": (
                "4D6F5379E40304B56C5C1A914E8A0EE3998E8023174DC52F7E5072F7CFA40454"
            ),
            "common/on_action/yearly_on_actions.txt": (
                "0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA"
            ),
        },
        "definition_lines": "1426-1598",
        "caller_semantics": (
            "the TGP yearly pool includes the event at weight 100 and the "
            "general yearly pool at weight 200; the event itself has a ten-year "
            "cooldown, so a later yearly selection is legal"
        ),
        "trigger_boundary": (
            "available adult celestial-government ruler with TGP enabled and at "
            "least one healthy adult AI councillor who shares the ruler's highest "
            "skill and has at least ten opinion of the ruler"
        ),
        "immediate_effect": (
            "optionally saves the dynastic-cycle top participant group and "
            "selects a valid councillor, favoring an existing potential friend"
        ),
        "option_semantics": {
            "0": (
                "progresses toward friendship with the councillor and applies "
                "trait-dependent stress"
            ),
            "1": (
                "adds two points to the spouse's highest skill or to the "
                "councillor's relevant council skill, plus trait-dependent stress"
            ),
            "2": (
                "adds one highest-skill point to both the ruler and councillor, "
                "plus trait-dependent stress"
            ),
        },
        "after_effect": None,
        "safe_option_rationale": (
            "native0 avoids direct skill mutation of the player and councillor; "
            "its friendship progress and possible personality stress remain "
            "explicit bounded costs"
        ),
        "frequency_boundary": (
            "R418 observed two legal instances about eleven in-game years apart; "
            "the source cooldown is ten years and neither yearly caller is one-shot"
        ),
    })
    movement_study_analysis["existing_boundaries"]["occurrence"] = {
        "occurrence_policy": "repeatable-within-product-observation-window"
    }

    culture_divergence_analysis = analysis["culture_notification.1111"]
    culture_divergence_analysis["migrated_from"]["review_kind"] = (
        "exact-build-original-definition-and-live-repeat-review"
    )
    culture_divergence_analysis.update({
        "source_sha256": {
            "events/culture_events/culture_notification_events.txt": (
                "875A91E2E308DCFB15AD8DD99D267F721985798FB6B6AD0E605011FE1AB9AC8F"
            ),
            "common/on_action/culture_on_actions.txt": (
                "68E4ECC075A7D3D91FB2FD46A9A1C0C3FEE12D07E018E6E2A01E533013F6C91F"
            ),
        },
        "definition_lines": "161-262",
        "caller_semantics": (
            "each culture-divergence action schedules this event at day zero "
            "for every player whose culture is the new culture or one of its "
            "parents; neither caller nor event is one-shot"
        ),
        "trigger_boundary": (
            "the player culture matches the newly diverged culture or one of "
            "that culture's parent cultures"
        ),
        "immediate_effect": (
            "saves the new ethos flag only when it differs from parent_1"
        ),
        "option_semantics": {
            "0": "founder-only acknowledgement with the culture notification tooltip",
            "1": "non-founder acknowledgement with the same tooltip",
        },
        "after_effect": None,
        "repeatability_evidence": (
            "R420 observed instances 1111 and 1113 for the same played manager "
            "at dates 54225528 and 54251808 in one process and product window"
        ),
    })
    culture_divergence_analysis["existing_boundaries"]["occurrence"] = {
        "occurrence_policy": "repeatable-within-product-observation-window"
    }

    stress_analysis = analysis["stress_threshold.1721"]
    stress_analysis["migrated_from"]["review_kind"] = (
        "exact-build-original-definition-and-live-variant-review"
    )
    stress_analysis.update({
        "source_sha256": {
            "events/stress_events/stress_threshold_events.txt": (
                "66538A8FE8C894A52D8EC89B2FC4A45B85B8D1B9464802263E45D582CE1CA42B"
            ),
            "common/on_action/stress_on_actions.txt": (
                "35A9B8FC8FE6CDE91EAAD06F9C90AD6FCD41BEEFD317BFF77D3A68430E5DD839"
            ),
            "common/scripted_effects/00_stress_effects.txt": (
                "3CD9F4F5F800E8C94D31F1841C93EB70F430B00064AFAE61D7C388F50BD7E612"
            ),
            "common/scripted_triggers/00_stress_triggers.txt": (
                "2AA4F3F637BF5A824B14FD74C9B6F30507C76C6BE9D26CFE40E493C84DAE775C"
            ),
            "common/traits/00_traits.txt": (
                "079F0AB5C4224C505AB9F25BCA80D8DF296E5899BFAB26049CE5FE794DC0B042"
            ),
            "common/script_values/00_stress_values.txt": (
                "104A7EF94EE9DA1092F23AEB2FD9DC971B08C695415F3B7EBFB628F381D26395"
            ),
        },
        "definition_lines": "6315-7479",
        "caller_semantics": (
            "stress-level on_actions schedule stress_threshold.0001 after three "
            "days; that manager can call the level-one tombola, whose weighted "
            "event list includes .1721 at weight 100"
        ),
        "trigger_boundary": (
            "playable county-tier-or-higher character with one supported "
            "personality trait and at least two eligible or already-owned "
            "stress-coping traits"
        ),
        "immediate_effect": (
            "saves root as stress_character, chooses two coping-option flags "
            "from existing traits before new eligible traits, and records the "
            "current stress-level cooldown band"
        ),
        "option_semantics": {
            "7": (
                "medium stress loss and inappetetic, then advances the cumulative "
                "starvation effect; hunger stage 3 can make that advance fatal"
            ),
            "9": (
                "medium stress loss and confider; may mark or strengthen a "
                "selected friend relationship"
            ),
            "10": (
                "minor stress loss and drunkard; adds the trait when new or a "
                "three-year drinking binge when already owned"
            ),
            "12": "unconditional medium stress gain",
        },
        "after_effect": (
            "runs shared threshold cleanup/cooldown effects and rotates the "
            "matching personality-description flag for ten years"
        ),
        "live_variant_boundary": (
            "native (7,9,12) is legal both with and without the unrelated "
            "retained confidant scope; the confider option is enabled by the "
            "event-local flag and its friend relation is optional. Native "
            "(7,10,12) is the other observed two-scope projection, where the "
            "live indicator proves drunkard would be newly added while "
            "native7 carries no add-trait indicator"
        ),
        "safe_routes_by_live_projection": [{
            "saved_scope_names": [
                "stress_character",
                "deceased_character",
                "confidant",
            ],
            "rendered_native_option_indices": [7, 9, 12],
            "selected_authored_option_number": 10,
            "selected_native_option_index": 9,
        }, {
            "saved_scope_names": [
                "stress_character",
                "deceased_character",
            ],
            "rendered_native_option_indices": [7, 10, 12],
            "selected_authored_option_number": 11,
            "selected_native_option_index": 10,
        }, {
            "saved_scope_names": [
                "stress_character",
                "deceased_character",
            ],
            "rendered_native_option_indices": [7, 9, 12],
            "selected_authored_option_number": 10,
            "selected_native_option_index": 9,
        }],
    })
    stress_analysis["existing_boundaries"][
        "campaign_specific_binding_fields"
    ] = []
    stress_analysis["existing_boundaries"]["boundary_note"] = (
        "The reusable contract binds the root and stress_character through "
        "$player, keeps campaign dates and numeric identities in observations "
        "only, and couples each reviewed saved-scope shape to its exact option "
        "projection."
    )

    desires_analysis = analysis["stress_threshold.1011"]
    desires_analysis["migrated_from"]["review_kind"] = (
        "exact-build-original-definition-and-live-projection-review"
    )
    desires_analysis.update({
        "source_sha256": {
            "events/stress_events/stress_threshold_events.txt": (
                "66538A8FE8C894A52D8EC89B2FC4A45B85B8D1B9464802263E45D582CE1CA42B"
            ),
            "common/on_action/stress_on_actions.txt": (
                "35A9B8FC8FE6CDE91EAAD06F9C90AD6FCD41BEEFD317BFF77D3A68430E5DD839"
            ),
        },
        "definition_lines": "882-1281",
        "caller_semantics": (
            "stress_threshold.0001 dispatches an uncooldowned level-one mental "
            "break through stress_threshold_level_1_event, whose random event "
            "list includes .1011 at weight 100"
        ),
        "trigger_boundary": (
            "adult non-chaste, non-celibate character with at least two eligible "
            "or already-owned rakish, reclusive, conversion, or athletic routes"
        ),
        "immediate_effect": (
            "saves root as stress_character, selects at most two coping routes, "
            "and may save a neglected_spouse while preparing reclusive effects"
        ),
        "option_semantics": {
            "0": (
                "adds rakish and invokes the brothel-night effect, which includes "
                "stress reduction and can create disease, pregnancy, or bastard "
                "consequences"
            ),
            "1": (
                "adds reclusive and invokes relationship-damage effects against "
                "the selected neglected_spouse"
            ),
            "2": (
                "same-religion faith conversion with piety and stress loss"
            ),
            "3": (
                "different-religion faith conversion with larger piety and "
                "stress loss"
            ),
            "4": "adds athletic and applies medium stress loss",
            "5": "unconditional mental-break opt-out stress gain",
        },
        "after_effect": (
            "runs the shared threshold cleanup and future-threshold cooldown "
            "preparation"
        ),
        "live_projection_boundary": (
            "R498 rendered native options 0, 1, and 5 with stress_character bound "
            "to the player and a distinct neglected_spouse; the contract admits "
            "only that exact two-scope, three-button projection"
        ),
    })
    desires_analysis["existing_boundaries"][
        "campaign_specific_binding_fields"
    ] = []
    desires_analysis["existing_boundaries"]["boundary_note"] = (
        "The reusable contract binds root and stress_character through $player, "
        "requires a distinct typed neglected_spouse, and leaves the R498 date "
        "and numeric identities in observations only."
    )

    poem_analysis = analysis["trait_specific_interactions.0011"]
    poem_analysis["migrated_from"]["review_kind"] = (
        "exact-build-original-definition-caller-effects-and-live-projection-review"
    )
    poem_analysis.update({
        "source_sha256": {
            "events/trait_specific_events/trait_specific_interaction_events.txt": (
                "2709B06223751133BD96B09657BB44C6F0987A66BFF6C3CF99288F67282CEE55"
            ),
            "common/character_interactions/00_poetry_interactions.txt": (
                "324439D9477AA6106F8F1C5206D75D53EFD5C670D0118BC53410A9E216DE9C7F"
            ),
            "common/scripted_effects/00_poetry_effects.txt": (
                "0BF4AACF776DC83AF32FC6FA6AEC93BCF01456CDE10DFC2E1C2E389A2CBB57FB"
            ),
        },
        "definition_lines": "128-205",
        "caller_semantics": (
            "send_poem_interaction fires .0011 on the adult recipient when the "
            "accepted interaction payload carries poem_theme_mourning; the live "
            "actor is distinct from the played recipient"
        ),
        "trigger_boundary": (
            "the sender is a poet, master bard, or laureate; sender and adult "
            "recipient are distinct and not imprisoned, and the accepted poem "
            "theme is mourning"
        ),
        "immediate_effect": (
            "the interaction has already selected the subject and poem theme; "
            "the event itself applies no additional immediate mutation"
        ),
        "option_semantics": {
            "0": (
                "runs a random diplomacy duel and resolves either the acceptance "
                "or rejection effect"
            ),
            "1": (
                "deterministically applies actor victory: optional poet XP, "
                "positive recipient opinion, medium recipient stress loss, and "
                "a 25-percent potential-friend check"
            ),
            "2": (
                "deterministically applies actor failure: possible minor poet "
                "XP, recipient opinion loss, minor prestige gain, and a "
                "20-percent potential-rival check"
            ),
        },
        "after_effect": (
            "clears the actor's temporary poetry_theme and poem_subject variables"
        ),
        "live_projection_boundary": (
            "R500 rendered native options 0, 1, and 2 with root, recipient, and "
            "subject bound to the player; actor was a distinct character, three "
            "generic interaction character slots had unavailable identities, "
            "and all five poem-theme scopes were typed booleans"
        ),
    })
    poem_analysis["existing_boundaries"][
        "campaign_specific_binding_fields"
    ] = []
    poem_analysis["existing_boundaries"]["boundary_note"] = (
        "The reusable contract binds root, recipient, and subject through "
        "$player; requires a distinct actor; preserves the exact weak-slot, "
        "boolean-theme, and option shape; and leaves R500 numeric identities "
        "and date in observations only."
    )

    travel_analysis = analysis["travel_completion_event.1000"]
    travel_analysis["migrated_from"]["review_kind"] = (
        "exact-build-original-definition-caller-and-live-projection-review"
    )
    travel_analysis.update({
        "source_sha256": {
            "events/travel_events/travel_completion_events.txt": (
                "525D15E895D989A1619B8608F006E9D9BA55946857DF939CEE27834C590960AB"
            ),
            "common/on_action/travel_on_actions.txt": (
                "7E433A0D6969E09CFED1D9DC50FB5276D944354024D6D2E045B314355F41040C"
            ),
        },
        "definition_lines": "15-203",
        "caller_semantics": (
            "on_travel_plan_complete selects .1000 as the generic first-valid "
            "completion event, while on_travel_plan_abort also lists it for "
            "ruler travel cleanup"
        ),
        "trigger_boundary": (
            "root is a landed available traveler with a non-aborted current "
            "travel plan and is not completing an activity tour"
        ),
        "immediate_effect": (
            "records travel statistics and presentation scopes, may grant tiny "
            "horse-track XP, and has already run before the player response"
        ),
        "option_semantics": {
            "0": (
                "already-home response; no explicit effect beyond possible "
                "craven or paranoid miniscule stress loss"
            ),
            "1": (
                "away-from-home response; may add miniscule stress for craven "
                "or paranoid and invokes return_home"
            ),
        },
        "after_effect": (
            "removes recently_completed_mandala_contract when that flag exists"
        ),
        "live_projection_boundary": (
            "R502 rendered only native option 0 with root and travel_owner bound "
            "to the player, a distinct travel leader, two travel-plan scopes, "
            "and three province scopes with opaque identities"
        ),
    })
    travel_analysis["existing_boundaries"][
        "campaign_specific_binding_fields"
    ] = []
    travel_analysis["existing_boundaries"]["boundary_note"] = (
        "The reusable contract binds root and travel_owner through $player, "
        "requires a distinct typed travel leader, preserves the exact travel-"
        "plan/province scope and single-rendered-option shape, and leaves R502 "
        "numeric identities and date in observations only."
    )

    epidemic_analysis = analysis["epidemic_events.1060"]
    epidemic_analysis["migrated_from"]["review_kind"] = (
        "exact-build-original-definition-caller-and-live-scope-variant-review"
    )
    epidemic_analysis.update({
        "source_sha256": {
            "events/dlc/ce1/epidemic_events.txt": (
                "FEF2972BD4F778818CD3A414C337D036F5132C1598FEBAB0E2623E0252DB7A1E"
            ),
            "common/on_action/ce1_on_actions.txt": (
                "96B42FA1A542836171A2A608B7155A8A80D30B0D8F8D9742EBE8AFF231B85E16"
            ),
        },
        "definition_lines": "1722-1995",
        "caller_semantics": (
            "the monthly epidemic_ongoing_events pool has a 95 percent "
            "no-event branch and lists .1060 at weight 100; the event itself "
            "has a fifteen-year cooldown"
        ),
        "immediate_effect": (
            "creates the plague-witch-hunt story and randomly blames animals, "
            "a character trait, or a religious minority; only the religious-"
            "minority branch exports the opaque faith_to_blame scope"
        ),
        "option_semantics": {
            "0": (
                "very-high-piety response with piety and trait-dependent "
                "effects; hidden in the R608 projection"
            ),
            "1": (
                "accepts rampant witch trials for ten years and may add "
                "trait-dependent stress"
            ),
            "2": (
                "slows witch trials for ten years, may add trait-dependent "
                "stress, and schedules no additional event"
            ),
        },
        "live_scope_variant_boundary": (
            "R608 observed epidemic, epidemic_scope, story_scope, and the "
            "religious-minority-only faith_to_blame scope with rendered native "
            "options 1 and 2; the earlier three-scope shape remains separately "
            "admitted"
        ),
        "safe_option_rationale": (
            "native option 2 preserves the reviewed terminal route and avoids "
            "the rampant-witch-trials modifier; the extra faith scope changes "
            "presentation context, not the selected option effects"
        ),
    })
    epidemic_analysis["existing_boundaries"][
        "campaign_specific_binding_fields"
    ] = []
    epidemic_analysis["existing_boundaries"]["boundary_note"] = (
        "The reusable contract binds root through $player and admits only the "
        "reviewed three-scope projection or the R608 four-scope projection with "
        "an opaque typed faith identity."
    )
    return analysis


VANILLA_EMBEDDED_A_ANALYSIS: Final[dict[str, dict[str, object]]] = (
    _build_analysis()
)


_TGP_MOVEMENT_0070_OBSERVATIONS: Final[
    dict[str, dict[str, object]]
] = {
    "tgp_movement_events.0070": {
        "exemplars": [
            *_LEGACY_MIGRATION_OBSERVATIONS[
                "tgp_movement_events.0070"
            ]["exemplars"],
            {
                "run": "R418-attempt-04",
                "kind": "same-process-hot-recovery-green",
                "artifact": (
                    "_runtime/p1-terminal-resume-r418-20260911/live-artifacts/"
                    "terminal-stages-red-attempt-05.json"
                ),
                "artifact_sha256": (
                    "B5048E4E5384BB50B6DA0DC57A928AF7B0F56A999B27E6FD2C462180A1DCDE70"
                ),
                "date_raw": 54017928,
                "event_instance_id": 1099,
                "root_character_id": 32904,
                "saved_character_ids": {"councillor": 50407232},
                "saved_scope_raw_types": {
                    "my_movement": 61,
                    "councillor": 4,
                },
                "rendered_native_option_indices": [0, 1, 2],
                "context_query_sequence": 16,
                "selected_option_number": 1,
                "selected_native_option_index": 0,
                "postcondition_verified": True,
                "starting_snapshot_id": "native:1376",
                "starting_revision": 1377,
                "ending_snapshot_id": "native:1377",
                "ending_revision": 1378,
                "connection_generation": 1,
                "bridge_pid": 204536,
                "process_restart_required": False,
                "mcp_only": True,
                "fixture_used": False,
                "ocr_used": False,
                "coordinates_used": False,
                "console_used": False,
            },
            {
                "run": "R418-attempt-05",
                "kind": "repeat-occurrence-bound-live-red",
                "red_classification": "product-contract-red",
                "artifact": (
                    "_runtime/p1-terminal-resume-r418-20260911/live-artifacts/"
                    "terminal-stages-red-attempt-05.json"
                ),
                "artifact_sha256": (
                    "B5048E4E5384BB50B6DA0DC57A928AF7B0F56A999B27E6FD2C462180A1DCDE70"
                ),
                "date_raw": 54114528,
                "event_instance_id": 1108,
                "root_character_id": 32904,
                "saved_character_ids": {"councillor": 125906},
                "saved_scope_raw_types": {
                    "my_movement": 61,
                    "councillor": 4,
                },
                "rendered_native_option_indices": [0, 1, 2],
                "context_query_sequence": 27,
                "snapshot_id": "native:2691",
                "revision": 2692,
                "native_revision": 2691,
                "selection_attempted": False,
                "retained_red": True,
                "connection_generation": 1,
                "bridge_pid": 204536,
                "process_restart_required": False,
                "mcp_only": True,
                "fixture_used": False,
                "ocr_used": False,
                "coordinates_used": False,
                "console_used": False,
            },
            {
                "run": "R418-attempt-06",
                "kind": "repeat-occurrence-same-process-green",
                "artifact": (
                    "_runtime/p1-terminal-resume-r418-20260911/live-artifacts/"
                    "terminal-stages-red-attempt-06.json"
                ),
                "artifact_sha256": (
                    "999828C356E88EB943A9E4CC22ACBF63BA294AFBAAFCA83FAE750C67D3342B76"
                ),
                "date_raw": 54114528,
                "event_instance_id": 1108,
                "root_character_id": 32904,
                "saved_character_ids": {"councillor": 125906},
                "saved_scope_raw_types": {
                    "my_movement": 61,
                    "councillor": 4,
                },
                "rendered_native_option_indices": [0, 1, 2],
                "context_query_sequence": 29,
                "selected_option_number": 1,
                "selected_native_option_index": 0,
                "postcondition_verified": True,
                "starting_snapshot_id": "native:2692",
                "starting_revision": 2693,
                "ending_snapshot_id": "native:2693",
                "ending_revision": 2694,
                "connection_generation": 1,
                "bridge_pid": 204536,
                "process_restart_required": False,
                "mcp_only": True,
                "fixture_used": False,
                "ocr_used": False,
                "coordinates_used": False,
                "console_used": False,
            },
        ],
    },
}


_CULTURE_NOTIFICATION_1111_OBSERVATIONS: Final[
    dict[str, dict[str, object]]
] = {
    "culture_notification.1111": {
        "exemplars": [
            *_LEGACY_MIGRATION_OBSERVATIONS[
                "culture_notification.1111"
            ]["exemplars"],
            {
                "run": "R420-attempt-01",
                "kind": "first-occurrence-production-live-green",
                "artifact": (
                    "_runtime/p1-b1-recovery-r420-20260911/live-artifacts/"
                    "terminal-stages-red-attempt-01.json"
                ),
                "artifact_sha256": (
                    "70B27E1064482C11FAE20CB730ED255755BDC5B70F1EAD1C048209EB31806866"
                ),
                "date_raw": 54225528,
                "event_instance_id": 1111,
                "root_character_id": 32904,
                "saved_character_ids": {"founder": 98415},
                "saved_scope_raw_types": {
                    "founder": 4,
                    "parent_culture_1": 26,
                    "new_culture": 26,
                    "parent_1": 26,
                    "ethos": 3,
                },
                "rendered_native_option_indices": [1],
                "context_query_sequence": 5,
                "selected_option_number": 2,
                "selected_native_option_index": 1,
                "postcondition_verified": True,
                "starting_snapshot_id": "native:1481",
                "starting_revision": 1482,
                "ending_snapshot_id": "native:1482",
                "ending_revision": 1483,
                "connection_generation": 1,
                "bridge_pid": 197452,
                "process_restart_required": False,
                "mcp_only": True,
                "fixture_used": False,
                "ocr_used": False,
                "coordinates_used": False,
                "console_used": False,
            },
            {
                "run": "R420-attempt-01",
                "kind": "repeat-occurrence-bound-live-red",
                "red_classification": "product-contract-red",
                "artifact": (
                    "_runtime/p1-b1-recovery-r420-20260911/live-artifacts/"
                    "terminal-stages-red-attempt-01.json"
                ),
                "artifact_sha256": (
                    "70B27E1064482C11FAE20CB730ED255755BDC5B70F1EAD1C048209EB31806866"
                ),
                "date_raw": 54251808,
                "event_instance_id": 1113,
                "root_character_id": 32904,
                "saved_character_ids": {"founder": 16881830},
                "saved_scope_raw_types": {
                    "founder": 4,
                    "parent_culture_1": 26,
                    "new_culture": 26,
                    "parent_1": 26,
                    "ethos": 3,
                },
                "rendered_native_option_indices": [1],
                "context_query_sequence": 7,
                "snapshot_id": "native:1824",
                "revision": 1825,
                "native_revision": 1824,
                "selection_attempted": False,
                "retained_red": True,
                "connection_generation": 1,
                "bridge_pid": 197452,
                "process_restart_required": False,
                "mcp_only": True,
                "fixture_used": False,
                "ocr_used": False,
                "coordinates_used": False,
                "console_used": False,
            },
            {
                "run": "R420-attempt-02",
                "kind": "repeat-occurrence-same-process-green",
                "artifact": (
                    "_runtime/p1-b1-recovery-r420-20260911/live-artifacts/"
                    "terminal-stages-red-attempt-02.json"
                ),
                "artifact_sha256": (
                    "6A579AAC9B9D183EE97CD0756F06A01AFC026DD2A3387388BD9A1D534B272A64"
                ),
                "date_raw": 54251808,
                "event_instance_id": 1113,
                "root_character_id": 32904,
                "saved_character_ids": {"founder": 16881830},
                "saved_scope_raw_types": {
                    "founder": 4,
                    "parent_culture_1": 26,
                    "new_culture": 26,
                    "parent_1": 26,
                    "ethos": 3,
                },
                "rendered_native_option_indices": [1],
                "selected_option_number": 2,
                "selected_native_option_index": 1,
                "postcondition_verified": True,
                "starting_snapshot_id": "native:1825",
                "starting_revision": 1826,
                "ending_snapshot_id": "native:1826",
                "ending_revision": 1827,
                "connection_generation": 1,
                "bridge_pid": 197452,
                "process_restart_required": False,
                "mcp_only": True,
                "fixture_used": False,
                "ocr_used": False,
                "coordinates_used": False,
                "console_used": False,
            },
        ],
    },
}


_STRESS_THRESHOLD_1721_OBSERVATIONS: Final[
    dict[str, dict[str, object]]
] = {
    "stress_threshold.1721": {
        "exemplars": [{
            "run": "R372",
            "kind": "pre-selection-live-red",
            "artifact": (
                "_runtime/p2r372-post-bound-continuation-live/"
                "stress-threshold-1721-no-confidant-red-report.json"
            ),
            "artifact_sha256": (
                "D07BB242C09933B238D977A8FA9F93097115A0AE1831F5DC7C97A83D5561E532"
            ),
            "park_artifact": (
                "_runtime/p2r372-post-bound-continuation-live/"
                "hot-recovery-park-8.json"
            ),
            "park_artifact_sha256": (
                "E9110611B7474BA6E648BDC9C89D34F63DB608C3F11ACF0CBBFB25010DCB40CF"
            ),
            "date_raw": 53470848,
            "event_instance_id": 849,
            "root_character_id": 32904,
            "saved_character_ids": {
                "stress_character": 32904,
                "deceased_character": 32797,
            },
            "rendered_native_option_indices": [7, 10, 12],
            "selection_attempted": False,
        }, {
            "run": "R372",
            "kind": "same-process-hot-recovery-contract-resolution-red",
            "artifact": (
                "_runtime/p2r372-post-bound-continuation-live/"
                "driver-state-hot-retry-8-snapshot.json"
            ),
            "artifact_sha256": (
                "9A5FCE5D0109E2B009826A15474BD469AA59EE6EA368A2FD00D40D1496AD02C3"
            ),
            "event_instance_id": 849,
            "driver_command_index": 2447,
            "selected_option_number": 10,
            "selected_native_option_index": 9,
            "expected_reviewed_option_number": 11,
            "expected_reviewed_native_option_index": 10,
            "postcondition_verified": True,
            "contract_reload_applied": True,
            "failure_stage": "submission_re_resolved_base_contract",
            "connection_generation": 1,
            "bridge_pid": 28772,
            "subsequent_event_instance_id": 853,
            "process_restart_required": False,
        }, {
            "run": "R375",
            "kind": "scope-option-variant-pre-selection-live-red",
            "artifact": (
                "_runtime/p2r375-post-publisher-fix-live/"
                "r375-stress-threshold-1721-red-freeze.json"
            ),
            "artifact_sha256": (
                "6F0F849C88EC48D78803B27B6BDE94C334FDD94F61024AA1BAA48EC88E2F4508"
            ),
            "park_artifact": (
                "_runtime/p2r375-post-publisher-fix-live/"
                "hot-recovery-park-3.json"
            ),
            "park_artifact_sha256": (
                "D5F18F8970B9D3A21C7AB5E72DF744D81DC85AD0E4CB55A340F97828B3EE40CE"
            ),
            "date_raw": 53611536,
            "event_instance_id": 1060,
            "root_character_id": 32904,
            "saved_character_ids": {
                "stress_character": 32904,
                "deceased_character": 37337,
            },
            "saved_scope_raw_types": {
                "stress_character": 4,
                "deceased_character": 4,
            },
            "rendered_native_option_indices": [7, 9, 12],
            "selection_attempted": False,
            "snapshot_option_count": 14,
            "snapshot_id": "native:440",
            "native_revision": 440,
            "revision": 441,
            "query_sequence": 16,
            "connection_generation": 1,
            "bridge_pid": 180544,
            "process_restart_required": False,
        }, {
            "run": "R375",
            "kind": "same-process-hot-recovery-green",
            "production_live_ordinal": 17,
            "artifact": (
                "_runtime/p2r375-post-publisher-fix-live/"
                "r375-live-017-stress-threshold-1721-green.json"
            ),
            "artifact_sha256": (
                "869BFE72B6FF2ABEF55FF3F4191F13D3A9F57E696F02B011367527256AD57EF3"
            ),
            "date_raw": 53611536,
            "event_instance_id": 1060,
            "root_character_id": 32904,
            "saved_character_ids": {
                "stress_character": 32904,
                "deceased_character": 37337,
            },
            "saved_scope_raw_types": {
                "stress_character": 4,
                "deceased_character": 4,
            },
            "rendered_native_option_indices": [7, 9, 12],
            "context_query_driver_command_index": 371,
            "selection_driver_command_index": 372,
            "query_sequence": 20,
            "selected_option_number": 10,
            "selected_native_option_index": 9,
            "postcondition_verified": True,
            "starting_snapshot_id": "native:440",
            "ending_snapshot_id": "native:441",
            "ending_revision": 442,
            "connection_generation": 1,
            "bridge_pid": 180544,
            "process_restart_required": False,
            "mcp_only": True,
            "fixture_used": False,
            "ocr_used": False,
            "coordinates_used": False,
            "console_used": False,
        }],
    },
}


_STRESS_THRESHOLD_1011_OBSERVATIONS: Final[
    dict[str, dict[str, object]]
] = {
    "stress_threshold.1011": {
        "exemplars": [{
            "run": "R498",
            "kind": "pre-selection-live-red",
            "artifact": (
                "_runtime/p1-stage10-player-publication-r497-r498-"
                "0aa1576-20260912/live-artifacts/"
                "stage10-player-subject-red.json"
            ),
            "artifact_sha256": (
                "B51B8960C470FA5D76A73724F6791425EF5B23BF4FC10B6D361DF4B6574F392F"
            ),
            "date_raw": 53155728,
            "event_instance_id": 20,
            "root_character_id": 27181,
            "saved_character_ids": {
                "stress_character": 27181,
                "neglected_spouse": 48337,
            },
            "saved_scope_raw_types": {
                "stress_character": 4,
                "neglected_spouse": 4,
            },
            "rendered_native_option_indices": [0, 1, 5],
            "snapshot_option_count": 6,
            "snapshot_id": "native:10",
            "native_revision": 10,
            "revision": 11,
            "query_sequence": 2,
            "connection_generation": 1,
            "bridge_pid": 37604,
            "selection_attempted": False,
            "process_restart_required": False,
        }],
    },
}


_TRAIT_SPECIFIC_INTERACTIONS_0011_OBSERVATIONS: Final[
    dict[str, dict[str, object]]
] = {
    "trait_specific_interactions.0011": {
        "exemplars": [{
            "run": "R500",
            "kind": "pre-selection-live-red",
            "artifact": (
                "_runtime/p1-stage10-player-publication-r499-r500-"
                "f522fbe-20260912/live-artifacts/"
                "stage10-player-subject-red.json"
            ),
            "artifact_sha256": (
                "8DF21A7682E1B30258A12DB736B975E348CE434C6A2A3D0AFFF11F30424B04AA"
            ),
            "date_raw": 53155992,
            "event_instance_id": 21,
            "root_character_id": 27181,
            "saved_character_ids": {
                "actor": 27168,
                "recipient": 27181,
                "subject": 27181,
            },
            "saved_scope_raw_types": {
                "actor": 4,
                "recipient": 4,
                "secondary_actor": 4,
                "secondary_recipient": 4,
                "intermediary": 4,
                "poem_theme_romance": 2,
                "poem_theme_legacy": 2,
                "poem_theme_mourning": 2,
                "poem_theme_strife": 2,
                "poem_theme_incompetence": 2,
                "subject": 4,
            },
            "rendered_native_option_indices": [0, 1, 2],
            "snapshot_option_count": 3,
            "snapshot_id": "native:18",
            "native_revision": 18,
            "revision": 19,
            "query_sequence": 3,
            "connection_generation": 1,
            "bridge_pid": 181268,
            "selection_attempted": False,
            "process_restart_required": False,
        }],
    },
}


_TRAVEL_COMPLETION_1000_OBSERVATIONS: Final[
    dict[str, dict[str, object]]
] = {
    "travel_completion_event.1000": {
        "exemplars": [{
            "run": "R502",
            "kind": "pre-selection-live-red",
            "artifact": (
                "_runtime/p1-stage10-player-publication-r501-r502-"
                "e824683-20260912/live-artifacts/"
                "stage10-player-subject-red.json"
            ),
            "artifact_sha256": (
                "E797ABDD300239ADBC9A60F41E7623B6F58E5B7ABA8D6BB97828F21CD24A6A5A"
            ),
            "date_raw": 53156184,
            "event_instance_id": 21,
            "root_character_id": 27181,
            "saved_character_ids": {
                "travel_owner": 27181,
                "travel_leader_scope": 32980,
            },
            "saved_scope_raw_types": {
                "travel_plan": 35,
                "travel_owner": 4,
                "destination": 8,
                "current_location": 8,
                "travel_plan_scope": 35,
                "final_destination_province": 8,
                "travel_leader_scope": 4,
            },
            "rendered_native_option_indices": [0],
            "snapshot_option_count": 2,
            "snapshot_id": "native:26",
            "native_revision": 26,
            "revision": 27,
            "query_sequence": 3,
            "connection_generation": 1,
            "bridge_pid": 149584,
            "selection_attempted": False,
            "process_restart_required": False,
        }],
    },
}


_EPIDEMIC_1060_OBSERVATIONS: Final[dict[str, dict[str, object]]] = {
    "epidemic_events.1060": {
        "exemplars": [
            *_LEGACY_MIGRATION_OBSERVATIONS[
                "epidemic_events.1060"
            ]["exemplars"],
        {
            "run": "R608",
            "kind": "scope-variant-pre-selection-live-red",
            "artifact": (
                "_runtime/p2-capture-r604-plus-e68cf74-20260913/capture/cell/"
                "phase2_promo_phase2_hc_workforce_mature_endgame_source_"
                "zg361we_360_native_event_wait_gate.json"
            ),
            "artifact_sha256": (
                "092451C4F9B2006982922F0D953790197FBC98A8938C6B2D0822E67BF8C8D82F"
            ),
            "date_raw": 53368992,
            "event_instance_id": 624,
            "root_character_id": 32904,
            "saved_scope_raw_types": {
                "epidemic": 50,
                "epidemic_scope": 50,
                "story_scope": 17,
                "faith_to_blame": 13,
            },
            "rendered_native_option_indices": [1, 2],
            "snapshot_option_count": 3,
            "snapshot_revision": 124,
            "connection_generation": 1,
            "bridge_pid": 129788,
            "selection_attempted": False,
            "process_restart_required": False,
        }, {
            "run": "R613",
            "kind": "production-live-base-projection-green",
            "artifact": (
                "_runtime/p2-capture-r609-plus-e658753-20260913/capture/cell/"
                "phase2_promo_phase2_hc_workforce_mature_endgame_source_"
                "zg361we_360_native_event_wait_gate.json"
            ),
            "artifact_sha256": (
                "7C4DD599138D0E3666A0A16337AA301DF52B43F3BB47836B721797501211BFB7"
            ),
            "date_raw": 53368272,
            "event_instance_id": 624,
            "root_character_id": 32904,
            "saved_scope_raw_types": {
                "epidemic": 50,
                "epidemic_scope": 50,
                "story_scope": 17,
            },
            "rendered_native_option_indices": [1, 2],
            "snapshot_option_count": 3,
            "snapshot_revision": 111,
            "selected_option_number": 3,
            "selected_native_option_index": 2,
            "postcondition_verified": True,
            "starting_snapshot_id": "native:33",
            "ending_snapshot_id": "native:34",
            "connection_generation": 1,
            "bridge_pid": 215080,
            "process_restart_required": False,
            "mcp_only": True,
        }],
    },
}


VANILLA_EMBEDDED_A_OBSERVATIONS: Final[
    dict[str, dict[str, object]]
] = {
    **_LEGACY_MIGRATION_OBSERVATIONS,
    **_TGP_MOVEMENT_0070_OBSERVATIONS,
    **_CULTURE_NOTIFICATION_1111_OBSERVATIONS,
    **_STRESS_THRESHOLD_1721_OBSERVATIONS,
    **_STRESS_THRESHOLD_1011_OBSERVATIONS,
    **_TRAIT_SPECIFIC_INTERACTIONS_0011_OBSERVATIONS,
    **_TRAVEL_COMPLETION_1000_OBSERVATIONS,
    **_EPIDEMIC_1060_OBSERVATIONS,
}


__all__ = [
    "EMBEDDED_A_EVENT_KEYS",
    "VANILLA_EMBEDDED_A_ANALYSIS",
    "VANILLA_EMBEDDED_A_OBSERVATIONS",
]
