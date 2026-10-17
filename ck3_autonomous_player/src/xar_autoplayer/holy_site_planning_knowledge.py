"""Frozen holy-site planning inputs, separate from native state and permission.

This resource can be read without a game or a gameplay driver. It describes
reviewed 1.20.0.4 resource scripts; it never evaluates their runtime scopes.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Literal


HolySitePlanningAction = Literal["adopt", "enshrine_relic", "remove_relic"]
HOLY_SITE_KNOWLEDGE_BUILD = "1.20.0.4"
_SOURCE_COMMIT = "074429b3f6d9352a3cf4c5671725fee2f41267ba"
_SOURCE_REPOSITORY = "https://github.com/jesec/ck3-mod-base"
_DECISIONS = "common/decisions/50_holy_site_decisions.txt"
_DECISIONS_SHA = "80ad6a6045bdafdce514cbccf59a9cd1370eaef6749d510adcec759468065fb4"
_RULES = "common/scripted_rules/02_holy_sites.txt"
_RULES_SHA = "02dafa910b976b6428725775cfb14fdcfc345032fd2fdf77a5bbec0dd42e6054"
_VALUES = "common/script_values/00_holy_site_values.txt"
_VALUES_SHA = "946bf28d0c1f1a7966596dc8ba11772f98425e1007a63eb24a197506593182b7"
_INVENTORY = "common/on_action/inventory_on_actions.txt"
_INVENTORY_SHA = "fcab2d2e740d32f3e8b5cb4058196dd3592153343ea3ae7a41c980fc0a334f67"


def _source(path: str, sha256: str, first: int, last: int) -> dict[str, object]:
    return {
        "path": path,
        "sha256": sha256,
        "line_start": first,
        "line_end": last,
        "commit": _SOURCE_COMMIT,
        "url": f"{_SOURCE_REPOSITORY}/blob/{_SOURCE_COMMIT}/base/game/{path}#L{first}",
    }


_COMMON_OBSERVATIONS = [
    "exact_runtime_build_exe_and_loaded_mods",
    "paused_actor_id_current_rite_id_faith_id_and_distinct_faith_main_rite_id",
    "holy_site_full_instance_id_type_id_county_id_and_barony_id",
    "county_holder_top_liege_clerical_region_holder_and_their_faith_rite_ids",
    "all_associated_faith_ids_and_each_faith_site_level",
    "same_site_inventory_id_and_artifact_full_ids_owners_slots_recognition_sets",
    "native_final_permission_literal_failure_reasons_and_actual_resource_quote",
]
_COMMON_POSTCONDITIONS = [
    "Read the same site instance/type and all associated Faith memberships/levels.",
    "Read inventory, each retained/replaced/removed artifact ID and actual owner kind/ID.",
    "Read IsActive, total active rarity and actual beneficiary IDs/effects independently.",
    "Compare actor balances and any relevant free-action/cooldown variables with the baseline.",
    "Retain the native request and later material state; an ACK is not a completed action.",
]
_COMMON_UNKNOWNS = [
    "The engine's complete final command validator and holy-site action ABI.",
    "HolySite.IsActive implementation, effective rarity calculation and actual beneficiaries.",
    "Whether different Faith views share the same inventory; join by actual site/inventory IDs.",
    "Native owner/slot/replacement legality and final costs for this actor/artifact/site.",
]

_KNOWLEDGE: dict[str, dict[str, object]] = {
    "adopt": {
        "decision_key": "adopt_holy_site_decision",
        "entrypoint": {
            "is_invisible": True,
            "keyed_decision_list_reachability_verified": False,
            "meaning": (
                "The decision declares is_invisible=yes. Existing keyed decision-list tools "
                "require an actual list row and cannot be assumed to reach this action. "
                "Map the original HolySite-window/picker caller and verify its selected object."
            ),
            "sources": [_source(_DECISIONS, _DECISIONS_SHA, 482, 482)],
        },
        "candidate_pipeline": [
            {
                "stage": "gui_candidate_source",
                "enumeration": ["actor.every_realm_county", "county.every_county_holy_site"],
                "filter": "Exclude sites already associated with actor.faith, then append item_list.",
                "sources": [_source(_DECISIONS, _DECISIONS_SHA, 588, 601)],
            },
            {
                "stage": "gui_item_filter",
                "filter": (
                    "Site not in actor.faith; county holder has actor.faith; any associated Faith "
                    "has county followers; faith_holy_site_kingdom_unused_trigger passes."
                ),
                "is_final_permission": False,
                "sources": [_source(_DECISIONS, _DECISIONS_SHA, 603, 616)],
            },
            {
                "stage": "decision_script_requirements",
                "filter": (
                    "Independent ruler and can_manage_faith_holy_sites_trigger; Faith site count "
                    "below Religion maximum; selected county holder is in the actor's hierarchy "
                    "via target_is_same_character_or_above and has actor.faith; site is not already "
                    "associated; faith_can_use_holy_site_kingdom_trigger; compatibility branch; "
                    "any associated Faith has num_county_followers > 0."
                ),
                "is_complete_native_validator": False,
                "sources": [_source(_DECISIONS, _DECISIONS_SHA, 491, 534)],
            },
        ],
        "compatibility": {
            "quantifier": "OR over all associated Faiths, not one arbitrarily selected Faith",
            "expression": (
                "actor.current_rite.allow_adopt_any_holy_site OR any associated Faith with "
                "((same Religion OR actor.faith is syncretic with that Faith) AND "
                "actor.faith hostility toward that Faith <= astray)"
            ),
            "parameter_scope": "The script reads actor.rite, independently of personal Tenets and Faith main Rite.",
            "missing_parameter_observation_is_false": False,
            "personal_tenet_warning": (
                "Adaptive core parameters include allow_adopt_any_holy_site; its personal "
                "parameters do not. Do not grant core permissions from a personal Tenet name."
            ),
            "sources": [
                _source("common/scripted_triggers/00_religious_triggers.txt",
                        "e9d0b56130464eabdcd670fa6cf814534d11c99da1e8b3fc1e69e9c3e36d2bb2", 1964, 1987),
                _source("common/religion/tenet_types/00_tenet_types.txt",
                        "d9e18a077d81f18f030d795ef45cb4aa5b7db246007043d5b0fe401baaf88abd", 1753, 1780),
            ],
        },
        "management_permission": {
            "script_summary": (
                "With a Head of Faith, actor or its internal/external theological puppet must "
                "be that head. Without a head, the actor/puppeteer branch requires the "
                "scripted realm-priest/theocracy condition and piety level >= 4."
            ),
            "must_read_native_final_result": True,
            "sources": [_source("common/scripted_triggers/pam_scripted_triggers.txt",
                                "0ad98f123b6739593b9ab2c170d0e8c9b3d9d941baa9d3580296dd2139b2ea6e", 1294, 1337)],
        },
        "cost_and_cooldown": {
            "script_base_piety": 1000,
            "free_action_branch": "While the Faith has a free holy-site action, script piety and decision cooldown are zero.",
            "otherwise_script_cooldown_years": 5,
            "actual_native_quote": None,
            "sources": [
                _source(_DECISIONS, _DECISIONS_SHA, 543, 562),
                _source("common/script_values/00_basic_values.txt",
                        "c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef", 1136, 1136),
                _source(_VALUES, _VALUES_SHA, 13, 27),
            ],
        },
        "declared_effect": {
            "script": "actor.faith.add_holy_site(target=selected_item, actor=actor), then consume_free_holy_site_action_effect.",
            "sources": [_source(_DECISIONS, _DECISIONS_SHA, 555, 562)],
        },
        "additional_observations": [
            "complete_realm_county_site_candidates_and_independent_gui_item_validity",
            "current_rite_effective_parameters_separate_from_personal_and_faith_main_rite",
            "all_associated_faith_religions_syncretism_hostility_and_county_followers",
            "faith_site_limit_dynamic_kingdom_records_free_actions_and_this_decision_cooldown",
        ],
        "additional_unknowns": [
            "Adoption's default ordinary/major level and whether instance/type/inventory are retained.",
            "Exact candidate order and recalculation timing beyond the visible script enumeration.",
        ],
    },
    "enshrine_relic": {
        "scripted_rule": "can_enshrine_artifact",
        "candidate_pipeline": [{
            "stage": "candidate_source",
            "status": "unknown",
            "reason": "No complete native artifact/site picker producer has been mapped; inventory membership alone is insufficient.",
        }],
        "script_requirements": {
            "expression": (
                "(county holder == actor OR county holder.top_liege == actor OR "
                "county.clerical_region_title.holder == actor) AND actor.faith has this site"
            ),
            "is_complete_native_validator": False,
            "sources": [_source(_RULES, _RULES_SHA, 1, 26)],
        },
        "cost_and_cooldown": {
            "actual_native_quote": None,
            "script_boundary": "Enshrinement/replacement callbacks contain conditional piety/opinion effects; do not promise a positive reward.",
            "sources": [_source(_INVENTORY, _INVENTORY_SHA, 129, 320)],
        },
        "additional_observations": [
            "selected_artifact_recognition_for_each_associated_faith_and_effective_rarity",
            "selected_slot_actual_owner_inventory_and_optional_replacing_artifact_identity",
            "native_artifact_picker_candidates_and_selected_candidate_final_permission",
        ],
        "additional_unknowns": [],
    },
    "remove_relic": {
        "scripted_rule": "can_remove_enshrined_artifact",
        "candidate_pipeline": [{
            "stage": "candidate_source",
            "status": "unknown",
            "reason": "Read the actual site inventory and selected artifact; the full native removal producer is not mapped.",
        }],
        "script_requirements": {
            "expression": (
                "county holder == actor OR county holder.top_liege == actor OR "
                "county.clerical_region_title.holder == actor"
            ),
            "actor_faith_site_membership_required_by_this_subrule": False,
            "is_complete_native_validator": False,
            "sources": [_source(_RULES, _RULES_SHA, 47, 64)],
        },
        "cost_and_cooldown": {
            "actual_native_quote": None,
            "script_boundary": "Removal callbacks declare conditional piety/opinion/CB effects. Freeze the selected artifact's actual quote and later effects.",
            "sources": [_source(_INVENTORY, _INVENTORY_SHA, 322, 540)],
        },
        "additional_observations": [
            "removed_artifact_destination_owner_and_any_replacement_identity",
            "whether_this_is_the_last_effective_relic_for_each_relevant_faith",
            "actual_piety_opinion_cb_and_active_effect_changes_on_a_recoverable_save_branch",
        ],
        "additional_unknowns": [],
    },
}


def query_holy_site_planning_knowledge_v1(
    action: HolySitePlanningAction, *, ck3_build: str = HOLY_SITE_KNOWLEDGE_BUILD,
) -> dict[str, object]:
    """Return source-bound planning questions, never native eligibility or an action."""
    if not isinstance(action, str) or action not in _KNOWLEDGE:
        raise ValueError("unsupported holy-site planning action")
    if not isinstance(ck3_build, str) or not ck3_build:
        raise ValueError("ck3_build must be a nonempty exact version")
    result: dict[str, object] = {
        "schema": "xar.ck3.holy-site-planning-knowledge.v1",
        "action": action,
        "requested_build": ck3_build,
        "supported_build": HOLY_SITE_KNOWLEDGE_BUILD,
        "read_only": True,
        "requires_ck3": False,
        "executes_action": False,
        "state_observed": False,
        "native_legality": None,
        "action_ready": False,
        "status": "unavailable",
        "qualification": "unsupported_build",
        "source_manifest": "docs/ck3-native-ai/evidence/faith-and-power-holy-sites-12004/source-manifest.json",
        "source_kind": "versioned_game_resource_scripts_and_gui_not_engine_cpp",
        "knowledge": None,
    }
    if ck3_build != HOLY_SITE_KNOWLEDGE_BUILD:
        result["reason"] = "Revalidate the source rules for the requested build; 1.20.0.4 rules are not a new-build permission."
        return result
    knowledge = deepcopy(_KNOWLEDGE[action])
    fields = _COMMON_OBSERVATIONS + knowledge.pop("additional_observations")
    knowledge["required_observations"] = [{"field": field, "status": "unknown"} for field in fields]
    knowledge["postconditions"] = list(_COMMON_POSTCONDITIONS)
    knowledge["unknowns"] = _COMMON_UNKNOWNS + knowledge.pop("additional_unknowns")
    knowledge["rarity_source_boundary"] = {
        "declaration": "The resource describes the controlling Faith's recognized relic rarity sum, only when that Faith also has the site; tiers contribute 1/2/3/4.",
        "native_algorithm_verified": False,
        "sources": [_source(_VALUES, _VALUES_SHA, 1, 10)],
    }
    result.update(status="available", qualification="source_reviewed_static", knowledge=knowledge)
    return result
