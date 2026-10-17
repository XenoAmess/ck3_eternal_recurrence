"""Frozen holy-site planning inputs, separate from native state and permission.

This resource can be read without a game or a gameplay driver. It describes
reviewed 1.20.0.4 resource scripts and separately scoped historical cases; it
never evaluates current runtime scopes or grants native permission.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Literal

from .holy_site_historical_cases import HOLY_SITE_ADOPTION_HISTORICAL_CASES


HolySitePlanningAction = Literal["adopt", "create", "promote", "demote", "abandon", "enshrine_relic", "remove_relic"]
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
    "same_site_inventory_owner_binding_and_artifact_full_ids_owners_slots_recognition_sets",
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
    "Whether different Faith views share the same site-bound inventory; do not invent an independent inventory ID.",
    "Native owner/slot/replacement legality and final costs for this actor/artifact/site.",
]

_KNOWLEDGE: dict[str, dict[str, object]] = {
    "adopt": {
        "historical_case_evidence": HOLY_SITE_ADOPTION_HISTORICAL_CASES,
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


_RELIGION_ACTIONS = "common/on_action/religion_on_actions.txt"
_RELIGION_ACTIONS_SHA = "ef9367ddf5f89c912b895743f8b72441e88af3a5b03a5c1a9eddea0e5681ee2d"
_RELIGION_EFFECTS = "common/scripted_effects/00_religion_effects.txt"
_RELIGION_EFFECTS_SHA = "5bf6b0df3316f72f711507c310a349d508a3b83aef99373ea6440de20e4e4931"
_PLANNING_CONTRACT = "docs/ck3-native-ai/faith-and-power-episode01-planning.md"
_DEFAULT_LIMITS = {
    "total_max": 9, "eminent_max": 3, "total_min": 1, "eminent_min": 1,
    "runtime_limits_must_be_observed": True,
    "sources": [_source("common/defines/00_defines.txt",
                        "8e430d77eb6e8767030f34b1c53d5dae84277fb354bd73cc42f93dc500be8982", 919, 926)],
}


def _decision_cost(decision: str, first: int, last: int) -> dict[str, object]:
    return {
        "script_base_piety": 1000,
        "decision_cooldown_key": decision,
        "free_action_branch": "Piety and this decision cooldown are zero while the Faith has a free action.",
        "otherwise_script_cooldown_years": 5,
        "actual_native_quote": None,
        "boundary": "Separate decision keys; observe the last free action's actual charge and cooldown timing.",
        "sources": [_source(_DECISIONS, _DECISIONS_SHA, first, last),
                    _source(_VALUES, _VALUES_SHA, 13, 27)],
    }


def _grade_social_effects(elevated: bool) -> dict[str, object]:
    return {
        "non_actor_county_holder_opinion": 50 if elevated else -50,
        "opinion_decays_over_years": 10,
        "actor_modifier_years": 10,
        "actor_same_faith_opinion": {"zealot": 30} if elevated else {"zealot": -20, "parochial": -20},
        "actual_opinion_and_modifier_reapplication": None,
        "sources": [
            _source("common/opinion_modifiers/00_religious_opinions.txt",
                    "7d99ff4ca1b0808337c78e452c7253497c158f0fc39c8db9ecd1791485c025be", 4, 15),
            _source("common/modifiers/00_religion_modifiers.txt",
                    "47379ec300977d1fbd7371424b6d623d215d3175bd83b81cc79ea8551851d9b9", 7, 16),
        ],
    }


_KNOWLEDGE.update({
    "create": {
        "planning_contract": _PLANNING_CONTRACT,
        "entrypoint": {
            "gui": "HolySiteCreationWindow.OnCreateButtonClicked",
            "native_command_abi_verified": False,
            "sources": [_source("gui/window_holy_site_creation.gui",
                                "7e6cd0cf6cc70616fa1f3137dca1c229f60c68a7f18bb3d43cd44dd9bf367310", 704, 714)],
        },
        "candidate_pipeline": [
            {
                "stage": "capital_opportunity_hint",
                "enumeration": ["actor.capital_barony", "actor.character_artifacts"],
                "filter": "Landed, no creation lock, unleased non-site capital, authority, total/kingdom room and unequipped recognized relic combinations.",
                "is_complete_candidate_directory": False,
                "payment_checked_by_this_hint": False,
                "sources": [_source("common/important_actions/pam_actions.txt",
                                    "ec8d868ee521618220ab019d8c488d4c14bc44e8509c820f090ef880941fbea5", 1514, 1574)],
            },
            {
                "stage": "gui_candidate_models",
                "models": ["GetAvailableHolySiteTypes", "GetPotentialBaronyTitles", "GetEnshrinableArtifacts"],
                "native_producer_status": "unknown",
                "is_complete_native_validator": False,
                "boundary": "Do not substitute the adoption realm-county enumeration or the capital hint for these complete models.",
                "sources": [_source("gui/window_holy_site_creation.gui",
                                    "7e6cd0cf6cc70616fa1f3137dca1c229f60c68a7f18bb3d43cd44dd9bf367310", 447, 607)],
            },
        ],
        "management_permission": _KNOWLEDGE["adopt"]["management_permission"],
        "script_requirements": {
            "expression": "can_manage_faith_holy_sites_trigger AND no actor.holy_site_creation_cooldown AND faith_can_use_holy_site_kingdom_trigger for selected barony",
            "free_action_does_not_bypass_existing_creation_lock": True,
            "is_complete_native_validator": False,
            "sources": [_source(_RULES, _RULES_SHA, 28, 45)],
        },
        "creation_relic_budget": {
            "script_required_rarity": 3,
            "defined_holy_site_slots": 3,
            "native_selected_artifacts_validated": False,
            "sources": [_source("common/defines/00_defines.txt",
                                "8e430d77eb6e8767030f34b1c53d5dae84277fb354bd73cc42f93dc500be8982", 928, 932),
                        _source("common/artifacts/slots/01_holy_site.txt",
                                "748a4c2f87bfea5959843c88456f38851eb968e507ef376bff0a725a6ac425df", 7, 20)],
        },
        "default_limits": _DEFAULT_LIMITS,
        "cost_and_cooldown": {
            "script_base_piety": 2000,
            "free_action_branch": "Target Faith free action waives scripted cost; creation callback consumes one instead of setting its new lock.",
            "creation_cooldown_variable": "holy_site_creation_cooldown",
            "otherwise_script_cooldown_years": 5,
            "actual_native_quote": None,
            "sources": [_source("common/scripted_costs/00_costs.txt",
                                "8c5f429b0c89b90a0aba29cb7420567db9f3cf18a644b8e85866065600d600d0", 770, 791),
                        _source(_RELIGION_ACTIONS, _RELIGION_ACTIONS_SHA, 2048, 2064),
                        _source(_VALUES, _VALUES_SHA, 13, 16)],
        },
        "declared_effect": {
            "script": "Creation callback consumes free action or sets actor creation lock, and adds only a missing fallback special-building slot.",
            "actual_created_site_id_and_level": None,
            "sources": [_source(_RELIGION_ACTIONS, _RELIGION_ACTIONS_SHA, 2048, 2064),
                        _source(_RELIGION_EFFECTS, _RELIGION_EFFECTS_SHA, 1343, 1358)],
        },
        "base_observations": _COMMON_OBSERVATIONS[:2],
        "additional_observations": [
            "complete_native_type_barony_artifact_candidates_and_each_refusal_reason",
            "selected_barony_county_kingdom_holder_lease_and_existing_sites",
            "target_faith_memberships_types_effective_limits_free_actions_and_used_kingdoms",
            "selected_artifact_ids_owners_equipped_recognition_rarity_count_and_native_sum",
            "effective_actor_payer_actual_quote_and_creation_variable_expiry",
        ],
        "postconditions": [
            "Read the newly created full site ID/type/barony and its actual Faith membership/level.",
            "Read selected artifact IDs, destination inventory owner binding and actual owner kind/ID.",
            "Read balances, Faith free actions, actor creation lock, used kingdoms and special-building slot.",
            "Read Active, effective rarity and actual beneficiary effects independently.",
            "Retain native request and independent material state; an ACK is not a completed action.",
        ],
        "additional_unknowns": ["Complete native model producers, selection invalidation and final creation command.",
                                "Runtime creation ordering, site level, ownership transfer and actual cost."],
    },
    "promote": {
        "planning_contract": _PLANNING_CONTRACT,
        "decision_key": "elevate_holy_site_decision",
        "entrypoint": {"is_invisible": True, "keyed_decision_list_reachability_verified": False,
                       "meaning": "Use the original parameterized HolySite-window caller; a generic keyed row is not guaranteed.",
                       "sources": [_source(_DECISIONS, _DECISIONS_SHA, 19, 19)]},
        "candidate_pipeline": [{"stage": "decision_widget", "enumeration": ["actor.faith.every_holy_site(is_eminent=no)"],
                                "is_final_permission": False, "sources": [_source(_DECISIONS, _DECISIONS_SHA, 125, 163)]}],
        "management_permission": _KNOWLEDGE["adopt"]["management_permission"],
        "script_requirements": {
            "expression": "Own regular site, authority, eminent count below maximum; actor is HoF OR site barony holder in actor hierarchy; county holder has actor.faith.",
            "is_complete_native_validator": False,
            "sources": [_source(_DECISIONS, _DECISIONS_SHA, 25, 59)],
        },
        "default_limits": _DEFAULT_LIMITS,
        "declared_count_delta": {"total": 0, "eminent": 1, "regular": -1, "is_runtime_observation": False},
        "cost_and_cooldown": _decision_cost("elevate_holy_site_decision", 62, 84),
        "declared_effect": {"script": "make_holy_site_eminent; consume free action; apply county-holder/actor social modifiers.",
                            "sources": [_source(_DECISIONS, _DECISIONS_SHA, 74, 100)]},
        "social_effects": _grade_social_effects(True),
        "additional_observations": ["complete_own_regular_sites_and_each_native_final_permission", "effective_total_eminent_counts_limits_free_actions_and_elevation_cooldown", "actual_county_holder_opinion_actor_modifiers_and_beneficiary_changes"],
        "additional_unknowns": ["Actual modifier reapplication and actual grade/beneficiary result."],
    },
    "demote": {
        "planning_contract": _PLANNING_CONTRACT,
        "decision_key": "demote_holy_site_decision",
        "entrypoint": {"is_invisible": True, "keyed_decision_list_reachability_verified": False,
                       "meaning": "Use the original parameterized HolySite-window caller; a generic keyed row is not guaranteed.",
                       "sources": [_source(_DECISIONS, _DECISIONS_SHA, 185, 185)]},
        "candidate_pipeline": [{"stage": "decision_widget", "enumeration": ["actor.faith.every_eminent_holy_site"],
                                "is_final_permission": False, "sources": [_source(_DECISIONS, _DECISIONS_SHA, 282, 309)]}],
        "management_permission": _KNOWLEDGE["adopt"]["management_permission"],
        "script_requirements": {
            "expression": "Own eminent site, authority, eminent count strictly above Religion minimum; this script does not add elevation's holder/faith checks.",
            "is_complete_native_validator": False,
            "sources": [_source(_DECISIONS, _DECISIONS_SHA, 191, 211)],
        },
        "default_limits": _DEFAULT_LIMITS,
        "declared_count_delta": {"total": 0, "eminent": -1, "regular": 1, "is_runtime_observation": False},
        "frees_total_capacity_or_kingdom_record": False,
        "cost_and_cooldown": _decision_cost("demote_holy_site_decision", 214, 235),
        "declared_effect": {"script": "make_holy_site_not_eminent; consume free action; social penalties; qualifying Christian schism progress effect.",
                            "sources": [_source(_DECISIONS, _DECISIONS_SHA, 226, 265)]},
        "social_effects": _grade_social_effects(False),
        "schism_side_effect": {
            "condition": "actor.faith == christian_faith and site county rite is in current schism pair",
            "declared_effect_input": 1, "actual_progress_delta": None,
            "sources": [_source(_DECISIONS, _DECISIONS_SHA, 253, 265),
                        _source("common/script_values/pam_values.txt",
                                "458d1bd882e8854005e3158339fca343177cff13eac7f83cb5877a8a37171965", 9277, 9277)],
        },
        "additional_observations": ["complete_own_eminent_sites_and_effective_minimum", "this_demotion_cooldown_and_shared_faith_free_actions", "actual_social_modifiers_county_rite_schism_pair_and_progress"],
        "additional_unknowns": ["Actual social stacking and schism progress; reverse elevation is not a world-state rollback."],
    },
    "abandon": {
        "planning_contract": _PLANNING_CONTRACT,
        "decision_key": "abandon_holy_site_decision",
        "entrypoint": {"is_invisible": True, "keyed_decision_list_reachability_verified": False,
                       "meaning": "Use the original parameterized HolySite-window caller; a generic keyed row is not guaranteed.",
                       "sources": [_source(_DECISIONS, _DECISIONS_SHA, 331, 331)]},
        "candidate_pipeline": [{"stage": "decision_widget", "enumeration": ["actor.faith.every_holy_site(is_eminent=no)"],
                                "is_final_permission": False, "sources": [_source(_DECISIONS, _DECISIONS_SHA, 430, 459)]}],
        "management_permission": _KNOWLEDGE["adopt"]["management_permission"],
        "script_requirements": {
            "expression": "Own regular site, authority, total site count strictly above Religion minimum.",
            "is_complete_native_validator": False,
            "sources": [_source(_DECISIONS, _DECISIONS_SHA, 337, 358)],
        },
        "default_limits": _DEFAULT_LIMITS,
        "declared_count_delta": {"total": -1, "eminent": 0, "regular": -1, "is_runtime_observation": False},
        "cost_and_cooldown": _decision_cost("abandon_holy_site_decision", 361, 396),
        "declared_effect": {
            "script": "If county holder exists and no other associated Faith remains, assign all enshrined artifacts to county holder; then remove actor.faith membership and consume free action.",
            "inventory_recipient": "county holder, possibly the actor; not universally the actor",
            "other_faith_follower_count_checked_by_return_branch": False,
            "uses_explicit_remove_relic_effect": False,
            "sources": [_source(_DECISIONS, _DECISIONS_SHA, 373, 413), _source(_INVENTORY, _INVENTORY_SHA, 322, 329)],
        },
        "social_effects": _grade_social_effects(False),
        "kingdom_release": {
            "expression": "Release only if this Faith has no holy site remaining anywhere in that de jure kingdom; other remaining associated Faith may acquire its own record.",
            "sources": [_source(_RELIGION_EFFECTS, _RELIGION_EFFECTS_SHA, 1312, 1340),
                        _source(_RELIGION_ACTIONS, _RELIGION_ACTIONS_SHA, 1995, 2004)],
        },
        "recovery_boundary": {
            "re_adoption_is_general_undo": False,
            "reason": "If no associated Faith remains, adoption's any-related-Faith-with-followers requirement cannot pass. Use an independently frozen baseline branch.",
            "is_runtime_observation": False,
            "sources": [_source(_DECISIONS, _DECISIONS_SHA, 377, 395), _source(_DECISIONS, _DECISIONS_SHA, 528, 534)],
        },
        "additional_observations": ["complete_own_regular_sites_total_count_minimum_free_actions_and_abandon_cooldown", "all_associated_faiths_including_extinct_and_all_artifact_owner_destinations", "all_remaining_faith_sites_in_kingdom_and_all_affected_faith_record_lists", "actual_social_modifiers_and_site_reentry_terms_on_recoverable_branch"],
        "additional_unknowns": ["Site lifetime, artifact return, actual kingdom-list callback order and non-generic native side effects."],
    },
})


# Source-reviewed read-only creation follow-up; no current state or action credit.
_KNOWLEDGE["create"]["native_read_only_context"] = {'qualification': 'source_reviewed_static_offline_query_qualified_live_pending',
 'query_tool': 'ck3_query_player_holy_site_creation_context_v1',
 'requires_explicit_private_opt_in': True,
 'source_contract_ref': 'docs/ck3-native-ai/evidence/holy-site-creation-native12004/source-contract.json',
 'source_contract_sha256': '7add888e9607df317b8f9981ab15a34f97723c2c63ed5db31ed949f483f1920b',
 'explanation_ref': 'docs/ck3-native-ai/holy-site-creation-native12004.md',
 'source_machine_id': '4-8e1c2f1861',
 'current_state_observed': False,
 'action_ready': False,
 'executes_create': False,
 'original_models': {'types': '17EACB0->window+130',
                     'baronies': 'SetData17E92F0 current player domain ->window+100',
                     'artifacts': '17EA880 actual player inventory, unequipped and native Faith '
                                  'recognition ->window+118',
                     'selected_whole': 'GetSelectedArtifacts->window+E0; not single focused '
                                       'artifact'},
 'query_fields': ['available_holy_site_types',
                  'potential_barony_title_ids',
                  'enshrinable_artifact_ids',
                  'selected_type_key',
                  'selected_barony_title_id',
                  'selected_artifact_ids',
                  'native_create_button_enabled',
                  'bypass_requirements_raw',
                  'create_tooltip',
                  'cached_resource_vector_raw'],
 'truth_boundaries': ['Original final enabled and refusal are separate from static script '
                      'declarations.',
                      'Normal legality requires observed bypass=0; missing is unknown.',
                      'Cached quote freshness and standalone affordability remain unobserved.',
                      'Rendered visibility and independent UI selection need separately opted-in '
                      'typed UI.',
                      'No Create command, payment/free use/cooldown or world transition '
                      'qualification.',
                      'Signed native actor is preserved; the public CharacterRef entrance still '
                      'rejects negative IDs.']}
_KNOWLEDGE["create"]["candidate_pipeline"][1]["native_producer_status"] = "static-confirmed-exact4-source-live-pending"
_KNOWLEDGE["create"]["additional_unknowns"] = [
    "Actual live creation picker models, selected state and final native terms.",
    "Actual Create invocation, runtime ordering, site level, ownership transfer, payment/free use and cooldown.",
]


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
        "source_manifest_additions": "docs/ck3-native-ai/evidence/faith-and-power-episode01-planning/knowledge-source-comparison.json",
        "knowledge": None,
    }
    if ck3_build != HOLY_SITE_KNOWLEDGE_BUILD:
        result["reason"] = "Revalidate the source rules for the requested build; 1.20.0.4 rules are not a new-build permission."
        return result
    knowledge = deepcopy(_KNOWLEDGE[action])
    fields = knowledge.pop("base_observations", _COMMON_OBSERVATIONS) + knowledge.pop("additional_observations")
    knowledge["required_observations"] = [{"field": field, "status": "unknown"} for field in fields]
    knowledge["postconditions"] = knowledge.pop("postconditions", list(_COMMON_POSTCONDITIONS))
    knowledge["unknowns"] = _COMMON_UNKNOWNS + knowledge.pop("additional_unknowns")
    knowledge["rarity_source_boundary"] = {
        "declaration": "The resource describes the controlling Faith's recognized relic rarity sum, only when that Faith also has the site; tiers contribute 1/2/3/4.",
        "native_algorithm_verified": False,
        "sources": [_source(_VALUES, _VALUES_SHA, 1, 10)],
    }
    result.update(status="available", qualification="source_reviewed_static", knowledge=knowledge)
    return result
