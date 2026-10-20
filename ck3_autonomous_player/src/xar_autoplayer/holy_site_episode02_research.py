"""Portable E02 research references, never current game state or permission.

The existing holy-site knowledge MCP returns a fresh copy of this resource.
No game, installation path, evidence file or gameplay driver is read here.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Literal, NotRequired, TypedDict


_EXE = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"
_REFERENCE = "docs/ck3-native-ai/faith-and-power-episode02-agent-reference-12004.md"
_ARTIFACTS = "promo/ck3_faith_and_power/episode02/docs/research-artifacts-and-site-effects.md"
_POWER = "promo/ck3_faith_and_power/episode02/docs/research-spiritual-head-and-ghw.md"
_PILGRIMAGE = "promo/ck3_faith_and_power/episode02/docs/research-pilgrimage.md"
_SITES = "common/religion/holy_site_types/00_holy_site_types.txt"
_SITES_SHA = "0824df55d4cd0a7c6d2c2d8b45bf577cca9ec0e5e1b4a6f699848b8661b17b40"



class SourceOnlyEvent(TypedDict):
    """Source knowledge and optional historical receipts, never a current event."""

    source_document: str
    static_definition_id: Literal["pilgrimage.5001", "travel_start_event.1060", "travel_events_cities.1020", "pilgrimage.4100"]
    live_native_definition_id: str | None
    analysis_status: Literal["source_bound_not_live_observed", "historical_live_native_definition_observed", "completed_source_analysis_native_current_shown_variant", "native_definition_observed_existing_source_analysis_reused", "completed_source_analysis_actual_native_shown_options"]
    full_occurrence_contract_registered: Literal[False]
    selection_policy_changed: Literal[False]
    historical_observation_is_current_state: Literal[False]
    # Omitted when no such receipt exists; absence is not a null/empty receipt.
    occurrence_document: NotRequired[str]
    post_observation_document: NotRequired[str]
    related_interaction_document: NotRequired[str]


_EVENT_DOCUMENTS = "promo/ck3_faith_and_power/episode02/docs/knowledge/"
_SOURCE_ONLY_EVENTS: list[SourceOnlyEvent] = [
    {"source_document": _EVENT_DOCUMENTS + "pilgrimage-5001-source-analysis.json",
     "static_definition_id": "pilgrimage.5001", "live_native_definition_id": "pilgrimage.5001",
     "analysis_status": "native_definition_observed_existing_source_analysis_reused",
     "occurrence_document": _EVENT_DOCUMENTS + "pilgrimage-5001-r0012-occurrence-analysis.json",
     "post_observation_document": _EVENT_DOCUMENTS + "r0012-5001-4100-post.json",
     "full_occurrence_contract_registered": False, "selection_policy_changed": False,
     "historical_observation_is_current_state": False},
    {"source_document": _EVENT_DOCUMENTS + "travel-start-1060-source-analysis.json",
     "static_definition_id": "travel_start_event.1060", "live_native_definition_id": "travel_start_event.1060",
     "analysis_status": "historical_live_native_definition_observed",
     "occurrence_document": _EVENT_DOCUMENTS + "travel-start-1060-r0012-occurrence.json",
     "full_occurrence_contract_registered": False, "selection_policy_changed": False,
     "historical_observation_is_current_state": False},
    {"source_document": _EVENT_DOCUMENTS + "travel-cities-1020-source-analysis.json",
     "static_definition_id": "travel_events_cities.1020", "live_native_definition_id": "travel_events_cities.1020",
     "analysis_status": "completed_source_analysis_native_current_shown_variant",
     "post_observation_document": _EVENT_DOCUMENTS + "r0012-event2-interaction35-post.json",
     "related_interaction_document": _EVENT_DOCUMENTS + "r0012-arrange-marriage-source-occurrence.json",
     "full_occurrence_contract_registered": False, "selection_policy_changed": False,
     "historical_observation_is_current_state": False},
    {"source_document": _EVENT_DOCUMENTS + "pilgrimage-4100-source-analysis.json",
     "static_definition_id": "pilgrimage.4100", "live_native_definition_id": "pilgrimage.4100",
     "analysis_status": "completed_source_analysis_actual_native_shown_options",
     "post_observation_document": _EVENT_DOCUMENTS + "r0012-5001-4100-post.json",
     "full_occurrence_contract_registered": False, "selection_policy_changed": False,
     "historical_observation_is_current_state": False},
]


def _validate_source_only_events(events: list[SourceOnlyEvent]) -> None:
    """Validate the shared static rows without reading their referenced files."""
    expected = {"pilgrimage.5001", "travel_start_event.1060", "travel_events_cities.1020", "pilgrimage.4100"}
    if len(events) != 4 or {event["static_definition_id"] for event in events} != expected:
        raise ValueError("E02 source-event definition set differs")
    for event in events:
        definition = event["static_definition_id"]
        live_id = event["live_native_definition_id"]
        if live_id != definition:
            raise ValueError("E02 source-event historical native identity differs")
        if (event["full_occurrence_contract_registered"] is not False
                or event["selection_policy_changed"] is not False
                or event["historical_observation_is_current_state"] is not False):
            raise ValueError("E02 historical reference cannot grant current state or policy")
        for field in ("source_document", "occurrence_document", "post_observation_document", "related_interaction_document"):
            path = event.get(field)
            if path is not None and (not isinstance(path, str) or not path.startswith(_EVENT_DOCUMENTS)
                    or ".." in path.split("/") or ":" in path or "\\" in path):
                raise ValueError("E02 source-event document must be repository-relative")


def _source(path: str, sha256: str, first: int, last: int) -> dict[str, object]:
    return {"game_relative_path": path, "sha256": sha256, "line_ranges": [[first, last]]}


_RESEARCH: dict[str, object] = {
    "schema": "xar.ck3.holy-site-episode02-research.v1",
    "ck3_build": "1.20.0.4",
    "executable_sha256": _EXE,
    "qualification": "source_reviewed_reference_and_separately_scoped_history",
    "shared_reference": _REFERENCE,
    "read_only": True,
    "requires_ck3": False,
    "runtime_file_access_required": False,
    "state_observed": False,
    "native_legality": None,
    "action_ready": False,
    "ordinary_auto_consumes": False,
    "consumer_scope": (
        "Returned by the existing holy-site planning knowledge MCP for an agent to consult. "
        "This does not install a policy or prove ordinary auto calls, ranks or executes it."
    ),
    "historical_evidence_is_current_state": False,
    "current_observations_must_be_fresh": True,
    "fresh_observations_required": [
        "Exact running build/EXE and loaded sources, game PID, connection generation and public/native frame.",
        "Actual played and target full IDs, each target's own Rite/Faith/devotion level, date and current availability.",
        "Selected site full ID/type, each Faith's major relation, county-holder Faith, inventory/owner/slot/recognition.",
        "Current normal native legality, complete resource quote and affordability, selection and independent post-state.",
    ],
    "action_and_observation_rules": [
        "A source rule, listed tool or historical success never grants current permission; unavailable remains unknown.",
        "Freeze actual identity/selection/quote, retain one durable intent, use the normal legal callback once, then independently read material state.",
        "An ACK is not an effect. Unknown commands are not resubmitted by changing run, date, request ID or ledger root.",
        "Keep item definitions, site previews, actor totals and attributed single-site contributions separate.",
        "Two-pass stability is not a cache refresh. Cache generation and selected-site attribution remain unknown unless independently established.",
    ],
    "topics": {
        "artifacts": {
            "documents": [_REFERENCE, _ARTIFACTS, "docs/ck3-native-ai/holy-site-relic-actions-python12004.md"],
            "rules": [
                "Personal, court and holy-site equipment are distinct inventories/slots; a holy-site equipped flag is not personal equipment.",
                "item_modifier_definition and original item effect text describe the item, not the actor's actual net gain.",
                "Equip/unequip and enshrine are separate legal world actions, each requiring its own permission, intent and independent owner/slot post-read.",
            ],
            "observer_contracts": [
                "ck3_autonomous_player/src/xar_autoplayer/bridge/faith_observers_private_transport_v1.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/artifact_personal_use_action_private_transport_v1.py",
            ],
            "sources": [
                _source("common/artifacts/slots/00_default.txt", "dc2a21281fd9275ef9de2d271ff835b181e46d1dac6f6d953e092cfc13914a69", 1, 78),
                _source("common/artifacts/slots/01_holy_site.txt", "748a4c2f87bfea5959843c88456f38851eb968e507ef376bff0a725a6ac425df", 1, 20),
            ],
            "unknowns": ["Current legal candidate/slot/replacement and independent personal benefit; item text does not close either."],
        },
        "site_effects_and_cache": {
            "documents": [_REFERENCE, _ARTIFACTS, "docs/ck3-native-ai/holy-site-grade-effects-and-limits-12004.md", "docs/ck3-native-ai/holy-site-effect-observation-12004.md"],
            "rules": [
                "Faith fixed/scaled effects require the Faith/site major relation and county-holder Faith gate; local fixed and county-scaled effects have distinct recipient/Active gates.",
                "Recipients may have different Rites within the same Faith; preserve each recipient's own Rite/Faith/full ID instead of asserting cross-person Rite equality.",
                "cached_world_state.total_active_artifact_rarity and current_relic_evaluation.active_artifact_rarity_sum are different observations; retain cache_evaluation_disagreement.",
                "The rarity evaluator reads site+1C; current rarity reevaluation and the character's cached skills/modifiers do not establish when either cache was rebuilt.",
                "A same-paused-frame grade transition with unchanged named actor text does not prove the mechanic ineffective or the benefit applied.",
            ],
            "native_source_chain": {
                "faith_producer": "29CC520->24FB270->Rite+20/+2C",
                "character_consumer": "291C0B0->291F080->2438830",
                "cached_rarity_reader": "2B0C740 reads HolySite+1C",
                "current_rarity_producer": "265A3F0",
                "refresh_schedule_verified": False,
            },
            "observer_contracts": [
                "ck3_autonomous_player/src/xar_autoplayer/bridge/player_holy_site_relic_context_private_transport.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/character_skill_effects_private_transport_v1.py",
            ],
            "unknowns": ["Cache generation time, natural refresh schedule and single-site actual contribution; two reads do not answer them."],
        },
        "mecca": {
            "documents": [_REFERENCE, "docs/ck3-native-ai/holy-site-major-grade-value12004.md", _ARTIFACTS],
            "rules": [
                "Mecca's local fixed knight-effectiveness +0.05 is separate from Faith scaled knight_effectiveness_mult +0.01 per effective rarity and piety_level_impact_mult +0.01 per effective rarity.",
                "Use knight_effectiveness_raw and actual_knight_effectiveness_breakdown only with a stable actual owned actor context; a shared 100% fallback is not qualified.",
                "KnightEffectiveness does not measure piety_level_impact, Diplomacy or devotion level. Read each actor's own level separately.",
            ],
            "observer_contracts": ["ck3_autonomous_player/src/xar_autoplayer/bridge/character_knight_effectiveness_private_transport_v1.py"],
            "sources": [_source(_SITES, _SITES_SHA, 687, 710)],
            "site_attribution_observed": False,
            "selected_site_contribution_raw": None,
            "unknowns": ["Current actor totals/original source text, piety_level_impact actual beneficiaries and selected-site net contribution."],
        },
        "head_of_faith": {
            "documents": [_REFERENCE, _POWER],
            "rules": [
                "Spiritual-head creation can count qualifying ordinary sites; control, holder Faith and the complete native requirements remain separate.",
                "Piety, gold/treasury prices and non-main-Rite/eminent-site multipliers have separate source scopes; do not multiply all resources together.",
                "Read the actual resulting head, title, Faith and main Rite independently; the creator is not automatically the resulting head.",
            ],
            "sources": [
                _source("common/scripted_triggers/00_religious_triggers.txt", "e9d0b56130464eabdcd670fa6cf814534d11c99da1e8b3fc1e69e9c3e36d2bb2", 1405, 1528),
                _source("common/script_values/02_religion_values.txt", "9e55618b00b463589af310bd17511b4f260fea4d3acb43e512e209cfc1517ded", 4094, 4188),
            ],
            "unknowns": ["This actor's current normal legality, complete payable quote and actual post-creation recipient/title state."],
        },
        "pilgrimage": {
            "documents": [
                _REFERENCE, _PILGRIMAGE,
                _EVENT_DOCUMENTS + "pilgrimage-3001-source-analysis.json",
                _EVENT_DOCUMENTS + "pilgrimage-3001-r0014-occurrence.json",
                _EVENT_DOCUMENTS + "travel-cities-1020-r0014-display-variant.json",
                _EVENT_DOCUMENTS + "r0014-event-batch-summary.json",
            ],
            "rules": [
                "Read the current Rite and actual legal planner choices; mandatory_hajj without hajjaj can exclude ordinary pious/worldly choices.",
                "Planner selection, final configured full10 activity quote (not proven whole-journey cost), Start, arrival, destination completion and return are separate observed states.",
                "The ordinary-site half multiplier belongs to its specific piety reward calculation, not every reward. A destination stay is not the whole travel duration.",
                "An end-window tooltip or empty activity list alone does not establish reward receipt or return home; retain actual IDs, event state and independent outcome.",
                "Empty event effect_indicators.rows with complete_effect_set=false and unavailable resource_deltas does not prove no cost; pilgrimage.4100 has a normal scripted purchase charge.",
                "pilgrimage.4100 activity_log score50 is a log score, not 50 piety. Historical R0012 post reads confirm an extra31.25gold charge for that occurrence only; future prices remain dynamic.",
                "An arrival/badge event window consumed does not prove pilgrim trait/XP, badge ownership/full artifact ID/equipment, full journey conclusion or return.",
                "Historical R0014 pilgrimage.3001 first-shown choice had ACK plus independent old-window disappearance and +100 piety on the same actor/date. Conditional illness and pilgrim/learning XP remain unobserved; this is not final pilgrimage settlement.",
                "travel_events_cities.1020 R0014 has a different unselected learning-option label in the same official option block; bind current native shown options, never reuse the historical label/index as current permission.",
                "The R0014 five-event batch contains 1060, 3001, 1020, 5001 and 4100; it ended without observed 7000/9001, full journey completion or independent home position. These source/actual references add no occurrence registry or ordinary-auto execution policy.",
            ],
            "sources": [
                _source("common/scripted_effects/00_pilgrimage_effects.txt", "4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80", 516, 629),
                _source("events/activities/pilgrimage_activity/pilgrimage_events.txt", "900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06", 15187, 15279),
            ],
            "source_only_events": _SOURCE_ONLY_EVENTS,
            "unknowns": ["Current choices/configured activity quote/Start permission; whole-journey cost is not established, nor real elapsed travel and independent actual reward/return state."],
        },
        "great_holy_war": {
            "documents": [_REFERENCE, _POWER],
            "rules": [
                "Religion unlock flags, the Faith's current permission, preparation object and linked live War are distinct states.",
                "The 120-day condition has source-specific target exceptions; a preparation object or requested action does not prove a declared war.",
                "Observed absence is different from query failure; use full generation-bearing references and separately read any linked War.",
            ],
            "sources": [
                _source("events/religion_events/great_holy_war_events.txt", "dfac5841107682613a78ec817d48c10b6ffb7ad411d9043901079de0a27897c0", 41, 131),
                _source("common/scripted_triggers/00_great_holy_war_triggers.txt", "7e449bcfa18bc02cf97cffff950d7b6f2d97aab7e0e93110db6c39d5e26505ba", 9, 117),
            ],
            "unknowns": ["Current unlock/permission/preparation and actual live War; static research is not a declaration result."],
        },
    },
    "historical_observation_limits": {
        "scope": "Historical observations are evidence examples, never the caller's current state or a replay instruction.",
        "machine_id": "4-8e1c2f1861",
        "observed_at_utc": "2026-10-20T05:33:21.126604Z",
        "medina27": {
            "result_sha256": "343efbbe8ebd1cd8dcc1b72835fcf2e18624c93610a4876d17d456002d834b7c",
            "proven": "One major-to-ordinary relation change and independent 1000 piety payment.",
            "not_proven": "Selected-site net benefit: two actors' Diplomacy and named Medina entries stayed unchanged in the paused frame; cache time unknown.",
            "intent_consumed": True,
            "post_save_available": False,
            "replay_authorized": False,
        },
    },
}


def episode02_research() -> dict[str, object]:
    """Return independent source-valued knowledge without reading the world."""
    _validate_source_only_events(_SOURCE_ONLY_EVENTS)
    return deepcopy(_RESEARCH)
