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


class SourceAnalyzedPilgrimageEvent(TypedDict):
    """Indexed source knowledge with historical proof, never current permission."""

    static_definition_id: Literal["pilgrimage.2070", "pilgrimage_intent.1100", "pilgrimage_intent.1040"]
    historical_native_definition_id: str
    analysis_status: Literal["source_closed_actual_native_definition_and_choice_observed"]
    source_analysis_completed: Literal[True]
    source_document: str
    occurrence_document: str
    definition_source_sha256: str
    decision_summary: str
    historical_observation_summary: str
    unobserved: list[str]
    historical_run_id: Literal["4-8e1c2f1861--faith-engine--R0018"]
    historical_machine_id: Literal["4-8e1c2f1861"]
    historical_evidence_is_current_state: Literal[False]
    full_occurrence_contract_registered: Literal[False]
    selection_policy_changed: Literal[False]
    ordinary_auto_consumes: Literal[False]
    state_observed: Literal[False]
    native_legality: None
    action_ready: Literal[False]


_R18_SOURCE_ANALYZED_EVENTS: dict[str, SourceAnalyzedPilgrimageEvent] = {
    "pilgrimage.2070": {
        "static_definition_id": "pilgrimage.2070",
        "historical_native_definition_id": "pilgrimage.2070",
        "analysis_status": "source_closed_actual_native_definition_and_choice_observed",
        "source_analysis_completed": True,
        "source_document": _EVENT_DOCUMENTS + "pilgrimage-2070-source-analysis.json",
        "occurrence_document": _EVENT_DOCUMENTS + "r0018-events-001-003-occurrence.json",
        "definition_source_sha256": "900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06",
        "decision_summary": "First option uses the pious activity-performance branch OR the direct base50piety ELSE; it does not grant both. Other options declare a5-day prayer/friendship step or travel-speed modifier. Bind current type, traits and legal shown rows.",
        "historical_observation_summary": "R0018 native0/public1 ACK and independent old-window disappearance were observed; same actor/date gold, piety, prestige and stress did not change. This does not prove no activity-performance or conditional effect.",
        "unobserved": ["activity performance", "fulfillment", "trait-conditioned stress inputs", "friendship", "travel ETA"],
        "historical_run_id": "4-8e1c2f1861--faith-engine--R0018",
        "historical_machine_id": "4-8e1c2f1861",
        "historical_evidence_is_current_state": False,
        "full_occurrence_contract_registered": False, "selection_policy_changed": False,
        "ordinary_auto_consumes": False, "state_observed": False,
        "native_legality": None, "action_ready": False,
    },
    "pilgrimage_intent.1100": {
        "static_definition_id": "pilgrimage_intent.1100",
        "historical_native_definition_id": "pilgrimage_intent.1100",
        "analysis_status": "source_closed_actual_native_definition_and_choice_observed",
        "source_analysis_completed": True,
        "source_document": _EVENT_DOCUMENTS + "pilgrimage-intent-1100-source-analysis.json",
        "occurrence_document": _EVENT_DOCUMENTS + "r0018-events-001-003-occurrence.json",
        "definition_source_sha256": "3ddbde37f029845aa265aae749fe131bed571f02a5c4faac5d0074a615b39878",
        "decision_summary": "First option declares conditional pious/hajj performance, a10-year monthly_piety_gain_mult=0.1 modifier and conditional pilgrim/mystic XP. It does not immediately grant10piety or establish the final total monthly multiplier. Other options have separate stress/worldly/personal-scheme or opinion modifiers.",
        "historical_observation_summary": "R0018 native0/public1 ACK and independent old-window disappearance were observed; immediate gold/piety/prestige/stress deltas were0. Later natural-time growth was not attributed solely to the declared modifier.",
        "unobserved": ["modifier membership", "monthly piety attribution", "pilgrim XP", "mystic XP", "fulfillment", "activity performance"],
        "historical_run_id": "4-8e1c2f1861--faith-engine--R0018",
        "historical_machine_id": "4-8e1c2f1861",
        "historical_evidence_is_current_state": False,
        "full_occurrence_contract_registered": False, "selection_policy_changed": False,
        "ordinary_auto_consumes": False, "state_observed": False,
        "native_legality": None, "action_ready": False,
    },
    "pilgrimage_intent.1040": {
        "static_definition_id": "pilgrimage_intent.1040",
        "historical_native_definition_id": "pilgrimage_intent.1040",
        "analysis_status": "source_closed_actual_native_definition_and_choice_observed",
        "source_analysis_completed": True,
        "source_document": _EVENT_DOCUMENTS + "pilgrimage-intent-1040-source-analysis.json",
        "occurrence_document": _EVENT_DOCUMENTS + "r0018-event004-and-scene-cutoff.json",
        "definition_source_sha256": "3ddbde37f029845aa265aae749fe131bed571f02a5c4faac5d0074a615b39878",
        "decision_summary": "Two displayed options in R0018. Following the animal declares base50piety, a10-day detour and conditional performance/hidden omen outcomes. The separate90-day helper is multiplayer-only. Source1044 literally checks predator_omen despite its prey comment; no hidden outcome or XP is inferred from a toast.",
        "historical_observation_summary": "R0018 native0/public1 ACK and independent old-window disappearance were observed; same actor/date piety increased50 while gold/prestige/stress did not change. This was a journey event, not the final on_end settlement.",
        "unobserved": ["live ETA change", "hidden followup definition/outcome", "trait XP", "modifier membership", "fulfillment", "activity performance", "animal province ID"],
        "historical_run_id": "4-8e1c2f1861--faith-engine--R0018",
        "historical_machine_id": "4-8e1c2f1861",
        "historical_evidence_is_current_state": False,
        "full_occurrence_contract_registered": False, "selection_policy_changed": False,
        "ordinary_auto_consumes": False, "state_observed": False,
        "native_legality": None, "action_ready": False,
    },
}


class R0022SourceAnalyzedEvent(TypedDict):
    """Additional analyzed source/history; no current observation or permission."""

    static_definition_id: str
    historical_native_definition_id: str
    analysis_status: Literal["source_closed_actual_native_definition_and_choice_observed"]
    source_analysis_completed: Literal[True]
    source_document: str
    occurrence_document: str
    definition_source_sha256: str
    decision_summary: str
    historical_observation_summary: str
    historical_run_id: Literal["4-8e1c2f1861--faith-engine--R0022"]
    historical_machine_id: Literal["4-8e1c2f1861"]
    historical_evidence_is_current_state: Literal[False]
    full_occurrence_contract_registered: Literal[False]
    selection_policy_changed: Literal[False]
    ordinary_auto_consumes: Literal[False]
    state_observed: Literal[False]
    native_legality: None
    action_ready: Literal[False]


_R22_SOURCE_ANALYZED_EVENTS: dict[str, R0022SourceAnalyzedEvent] = {'pilgrimage.3004': {'static_definition_id': 'pilgrimage.3004',
                     'historical_native_definition_id': 'pilgrimage.3004',
                     'analysis_status': 'source_closed_actual_native_definition_and_choice_observed',
                     'source_analysis_completed': True,
                     'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-3004-source-analysis.json',
                     'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0022-events-001-003-occurrence.json',
                     'definition_source_sha256': '900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06',
                     'decision_summary': '3004.B is the first of two actually shown options; '
                                         'learning-gated A is hidden, not a legal candidate to invent.',
                     'historical_observation_summary': 'Selected indulgence option: wallets and floor-zero '
                                                       'stress unchanged; source base stress loss does not '
                                                       'mean no authored effect.',
                     'historical_run_id': '4-8e1c2f1861--faith-engine--R0022',
                     'historical_machine_id': '4-8e1c2f1861',
                     'historical_evidence_is_current_state': False,
                     'full_occurrence_contract_registered': False,
                     'selection_policy_changed': False,
                     'ordinary_auto_consumes': False,
                     'state_observed': False,
                     'native_legality': None,
                     'action_ready': False},
 'pilgrimage_intent.1030': {'static_definition_id': 'pilgrimage_intent.1030',
                            'historical_native_definition_id': 'pilgrimage_intent.1030',
                            'analysis_status': 'source_closed_actual_native_definition_and_choice_observed',
                            'source_analysis_completed': True,
                            'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-intent-1030-source-analysis.json',
                            'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0022-events-001-003-occurrence.json',
                            'definition_source_sha256': '3ddbde37f029845aa265aae749fe131bed571f02a5c4faac5d0074a615b39878',
                            'decision_summary': 'Ten-day delay and conditional XP/piety branches; '
                                                'separate90-day helper is multiplayer-only.',
                            'historical_observation_summary': 'Same-day piety+50, other wallets/stress0; '
                                                              'ETA, traitXP and performance not '
                                                              'independently observed.',
                            'historical_run_id': '4-8e1c2f1861--faith-engine--R0022',
                            'historical_machine_id': '4-8e1c2f1861',
                            'historical_evidence_is_current_state': False,
                            'full_occurrence_contract_registered': False,
                            'selection_policy_changed': False,
                            'ordinary_auto_consumes': False,
                            'state_observed': False,
                            'native_legality': None,
                            'action_ready': False},
 'pilgrimage.6840': {'static_definition_id': 'pilgrimage.6840',
                     'historical_native_definition_id': 'pilgrimage.6840',
                     'analysis_status': 'source_closed_actual_native_definition_and_choice_observed',
                     'source_analysis_completed': True,
                     'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-6840-source-analysis.json',
                     'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0022-events-006-010-and-marriage-occurrence.json',
                     'definition_source_sha256': '900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06',
                     'decision_summary': 'Blessing fee is dynamic with15gold cap; artifact durability/stat '
                                         'changes require independent artifact readback. Unselected '
                                         'prestige modifier code and localization differ.',
                     'historical_observation_summary': 'Native0 charged15gold and gave25piety; '
                                                       'stress81to98. Artifact identity/stats remain '
                                                       'opaque.',
                     'historical_run_id': '4-8e1c2f1861--faith-engine--R0022',
                     'historical_machine_id': '4-8e1c2f1861',
                     'historical_evidence_is_current_state': False,
                     'full_occurrence_contract_registered': False,
                     'selection_policy_changed': False,
                     'ordinary_auto_consumes': False,
                     'state_observed': False,
                     'native_legality': None,
                     'action_ready': False},
 'stress_threshold.1701': {'static_definition_id': 'stress_threshold.1701',
                           'historical_native_definition_id': 'stress_threshold.1701',
                           'analysis_status': 'source_closed_actual_native_definition_and_choice_observed',
                           'source_analysis_completed': True,
                           'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/stress-threshold-1701-r0022-display-variant.json',
                           'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0022-events-006-010-and-marriage-occurrence.json',
                           'definition_source_sha256': 'feb4702321a7b872ebb39c1d3fab6bdfd2002300098e912fcd307abdc775a339',
                           'decision_summary': 'Five official source SHA pins match. Existing dedicated '
                                               'route ran first but rejected the actual2scope/3shown3,6,8 '
                                               'envelope, so current first native3 was used; no hot '
                                               'registry expansion.',
                           'historical_observation_summary': 'Native3 cost105gold, stress115to97; '
                                                             'profligate add indicator is not independent '
                                                             'membership. Future dynamic price/current '
                                                             'legality unknown.',
                           'historical_run_id': '4-8e1c2f1861--faith-engine--R0022',
                           'historical_machine_id': '4-8e1c2f1861',
                           'historical_evidence_is_current_state': False,
                           'full_occurrence_contract_registered': False,
                           'selection_policy_changed': False,
                           'ordinary_auto_consumes': False,
                           'state_observed': False,
                           'native_legality': None,
                           'action_ready': False},
 'pilgrimage.6750': {'static_definition_id': 'pilgrimage.6750',
                     'historical_native_definition_id': 'pilgrimage.6750',
                     'analysis_status': 'source_closed_actual_native_definition_and_choice_observed',
                     'source_analysis_completed': True,
                     'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-6750-source-analysis.json',
                     'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0022-events-006-010-and-marriage-occurrence.json',
                     'definition_source_sha256': '900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06',
                     'decision_summary': 'Selected redemption removes one eligible secret OR first '
                                         'matching coping trait, not every trait. Immediate '
                                         'once-per-character marker is set even if choosing B. Log score50 '
                                         'is not piety.',
                     'historical_observation_summary': 'Native0 piety+100/stress97to165; removed-trait '
                                                       'indicator does not prove XP or complete trait '
                                                       'membership.',
                     'historical_run_id': '4-8e1c2f1861--faith-engine--R0022',
                     'historical_machine_id': '4-8e1c2f1861',
                     'historical_evidence_is_current_state': False,
                     'full_occurrence_contract_registered': False,
                     'selection_policy_changed': False,
                     'ordinary_auto_consumes': False,
                     'state_observed': False,
                     'native_legality': None,
                     'action_ready': False},
 'councillor_spouse_learning.2601': {'static_definition_id': 'councillor_spouse_learning.2601',
                                     'historical_native_definition_id': 'councillor_spouse_learning.2601',
                                     'analysis_status': 'source_closed_actual_native_definition_and_choice_observed',
                                     'source_analysis_completed': True,
                                     'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/councillor-spouse-learning-2601-source-analysis.json',
                                     'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0022-event011-occurrence.json',
                                     'definition_source_sha256': 'e9d59eba1d239784695586c6fa5d90470c370bc8d9897ae130d7fe2665c78f59',
                                     'decision_summary': 'Ordinary spouse tutoring, not a pilgrimage '
                                                         'reward. Random raw weights and root/student '
                                                         'flags retain their own scopes.',
                                     'historical_observation_summary': 'First shown native0 acknowledged; '
                                                                       'wallets and stress147 unchanged. '
                                                                       'Education/skill/opinion/modifier/nickname '
                                                                       'outcome unobserved.',
                                     'historical_run_id': '4-8e1c2f1861--faith-engine--R0022',
                                     'historical_machine_id': '4-8e1c2f1861',
                                     'historical_evidence_is_current_state': False,
                                     'full_occurrence_contract_registered': False,
                                     'selection_policy_changed': False,
                                     'ordinary_auto_consumes': False,
                                     'state_observed': False,
                                     'native_legality': None,
                                     'action_ready': False},
 'pilgrimage.6800': {'static_definition_id': 'pilgrimage.6800',
                     'historical_native_definition_id': 'pilgrimage.6800',
                     'analysis_status': 'source_closed_actual_native_definition_and_choice_observed',
                     'source_analysis_completed': True,
                     'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-6800-source-analysis.json',
                     'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0022-events-012-013-settlement-occurrence.json',
                     'definition_source_sha256': '900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06',
                     'decision_summary': 'Called-member monk effects target NPC36310, not the player; '
                                         'devoted is not celibate. Score50 and player100piety are '
                                         'separate.',
                     'historical_observation_summary': 'Player gained100piety at same date; no independent '
                                                       'NPC court/spouse/trait post or XP.',
                     'historical_run_id': '4-8e1c2f1861--faith-engine--R0022',
                     'historical_machine_id': '4-8e1c2f1861',
                     'historical_evidence_is_current_state': False,
                     'full_occurrence_contract_registered': False,
                     'selection_policy_changed': False,
                     'ordinary_auto_consumes': False,
                     'state_observed': False,
                     'native_legality': None,
                     'action_ready': False},
 'pilgrimage.7000': {'static_definition_id': 'pilgrimage.7000',
                     'historical_native_definition_id': 'pilgrimage.7000',
                     'analysis_status': 'source_closed_actual_native_definition_and_choice_observed',
                     'source_analysis_completed': True,
                     'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-7000-source-analysis.json',
                     'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0022-events-012-013-settlement-occurrence.json',
                     'definition_source_sha256': '900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06',
                     'decision_summary': 'Normal phase on_end resolves main rewards before the conclusion '
                                         'button; normal A shows reward tooltip without a second payout.',
                     'historical_observation_summary': 'Last-before/first-after24h piety+125 is observed, '
                                                       'not a single-effect attribution; button wallets0 '
                                                       'is not reward0. Historical milestone '
                                                       'devotion/fulfillment remain unknown.',
                     'historical_run_id': '4-8e1c2f1861--faith-engine--R0022',
                     'historical_machine_id': '4-8e1c2f1861',
                     'historical_evidence_is_current_state': False,
                     'full_occurrence_contract_registered': False,
                     'selection_policy_changed': False,
                     'ordinary_auto_consumes': False,
                     'state_observed': False,
                     'native_legality': None,
                     'action_ready': False},
 'pilgrimage.9001': {'static_definition_id': 'pilgrimage.9001',
                     'historical_native_definition_id': 'pilgrimage.9001',
                     'analysis_status': 'source_closed_actual_native_definition_and_choice_observed',
                     'source_analysis_completed': True,
                     'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-9001-source-analysis.json',
                     'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0022-events-014-015-return-occurrence.json',
                     'definition_source_sha256': '900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06',
                     'decision_summary': 'Travel completion hook includes script completion and event '
                                         'supports invalidated branches; never infer independent home '
                                         'position or success from9001 alone.',
                     'historical_observation_summary': 'ACK+old-window disappearance, same-activity '
                                                       'completed=true/invalidated=false and independent '
                                                       'Apulia tooltip align. Return-button wallets0; '
                                                       'current fulfillment35/devotion level5 are not '
                                                       'historical reward deltas.',
                     'historical_run_id': '4-8e1c2f1861--faith-engine--R0022',
                     'historical_machine_id': '4-8e1c2f1861',
                     'historical_evidence_is_current_state': False,
                     'full_occurrence_contract_registered': False,
                     'selection_policy_changed': False,
                     'ordinary_auto_consumes': False,
                     'state_observed': False,
                     'native_legality': None,
                     'action_ready': False}}


def _validate_r22_source_events(events: dict[str, R0022SourceAnalyzedEvent]) -> None:
    """Validate finite reference identity/paths and reject permission promotion."""
    if set(events) != {'pilgrimage.3004', 'stress_threshold.1701', 'pilgrimage_intent.1030', 'councillor_spouse_learning.2601', 'pilgrimage.6750', 'pilgrimage.9001', 'pilgrimage.7000', 'pilgrimage.6800', 'pilgrimage.6840'}:
        raise ValueError("R22 analyzed definition set differs")
    for definition, event in events.items():
        if (event["static_definition_id"] != definition
                or event["historical_native_definition_id"] != definition
                or event["analysis_status"] != "source_closed_actual_native_definition_and_choice_observed"
                or event["source_analysis_completed"] is not True):
            raise ValueError("R22 analyzed source identity differs")
        if (event["historical_evidence_is_current_state"] is not False
                or event["full_occurrence_contract_registered"] is not False
                or event["selection_policy_changed"] is not False
                or event["ordinary_auto_consumes"] is not False
                or event["state_observed"] is not False
                or event["native_legality"] is not None
                or event["action_ready"] is not False):
            raise ValueError("R22 history cannot grant current state or permission")
        for path in (event["source_document"], event["occurrence_document"]):
            if not path.startswith(_EVENT_DOCUMENTS) or ".." in path.split("/") or ":" in path or "\\" in path:
                raise ValueError("R22 source path must be repository-relative")
        digest = event["definition_source_sha256"]
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise ValueError("R22 source SHA differs")


def _validate_source_analyzed_events(events: dict[str, SourceAnalyzedPilgrimageEvent]) -> None:
    """Check the finite source index without reading evidence or game state."""
    if set(events) != {"pilgrimage.2070", "pilgrimage_intent.1100", "pilgrimage_intent.1040"}:
        raise ValueError("E02 source-analyzed definition set differs")
    for definition, event in events.items():
        if (event["static_definition_id"] != definition
                or event["historical_native_definition_id"] != definition
                or event["analysis_status"] != "source_closed_actual_native_definition_and_choice_observed"
                or event["source_analysis_completed"] is not True):
            raise ValueError("E02 analyzed source identity or qualification differs")
        if (event["historical_evidence_is_current_state"] is not False
                or event["full_occurrence_contract_registered"] is not False
                or event["selection_policy_changed"] is not False
                or event["ordinary_auto_consumes"] is not False
                or event["state_observed"] is not False
                or event["native_legality"] is not None
                or event["action_ready"] is not False):
            raise ValueError("E02 source knowledge cannot grant current state or permission")
        for path in (event["source_document"], event["occurrence_document"]):
            if (not path.startswith(_EVENT_DOCUMENTS) or ".." in path.split("/")
                    or ":" in path or "\\" in path):
                raise ValueError("E02 analyzed source document must be repository-relative")
        digest = event["definition_source_sha256"]
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise ValueError("E02 analyzed source digest differs")


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
            "documents": [_REFERENCE, _ARTIFACTS, "docs/ck3-native-ai/holy-site-grade-effects-and-limits-12004.md", "docs/ck3-native-ai/holy-site-effect-observation-12004.md", _EVENT_DOCUMENTS + "r0021-promotion-cap-source-analysis.json"],
            "rules": [
                "Faith fixed/scaled effects require the Faith/site major relation and county-holder Faith gate; local fixed and county-scaled effects have distinct recipient/Active gates.",
                "Recipients may have different Rites within the same Faith; preserve each recipient's own Rite/Faith/full ID instead of asserting cross-person Rite equality.",
                "cached_world_state.total_active_artifact_rarity and current_relic_evaluation.active_artifact_rarity_sum are different observations; retain cache_evaluation_disagreement.",
                "The rarity evaluator reads site+1C; current rarity reevaluation and the character's cached skills/modifiers do not establish when either cache was rebuilt.",
                "A same-paused-frame grade transition with unchanged named actor text does not prove the mechanic ineffective or the benefit applied.",
                "Before promote, read the complete current Faith major membership/count and that current Religion actual max/override; do not inspect only the selected site or assume universal max3. Keep missing typed limit unknown and retain current native requirement text with source.",
                "Final normal CanConfirm, native CanConfirm, bypass0, cooldown and complete10-resource quote/affordability must be fresh. A free-action count or zero quote never waives the major-count cap or another legal requirement.",
                "R0021 historical Faith103 already had major sites0/1/3, so target32 promotion failed count<3 with free-action text2 and all10 costs0; no Confirm or promotion result occurred. Read the linked source analysis, never reuse this history as current state.",
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
                "The no-eminent HoF multiplier tests the whole Faith for any major-site county controlled by root with holder Faith=root Faith; selected-site ordinary/major alone never decides the quote. Releasing one cap slot can leave other qualifying majors and unchanged cost.",
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
                _EVENT_DOCUMENTS + "pilgrimage-2070-source-analysis.json",
                _EVENT_DOCUMENTS + "pilgrimage-intent-1100-source-analysis.json",
                _EVENT_DOCUMENTS + "pilgrimage-intent-1040-source-analysis.json",
                _EVENT_DOCUMENTS + "r0018-events-001-003-occurrence.json",
                _EVENT_DOCUMENTS + "r0018-event004-and-scene-cutoff.json",
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
                "Lookup source_analyzed_events by current native definition to find the already-analyzed2070/intent1100/intent1040 source and historical references. Recognition as analyzed is not native permission or a new execution policy; current scopes/options and any existing dedicated strategy still decide the live action.",
                "R0018 actually captured4 events and56 elapsed days/57 day requests, then failed before arrival, final settlement or return. Game/host/public-run exits1/1/2 and normalclose=false are historical failure facts, not completed-pilgrimage or normal-Quit evidence.",
            ],
            "sources": [
                _source("common/scripted_effects/00_pilgrimage_effects.txt", "4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80", 516, 629),
                _source("events/activities/pilgrimage_activity/pilgrimage_events.txt", "900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06", 15187, 15279),
            ],
            "source_only_events": _SOURCE_ONLY_EVENTS,
            "source_analyzed_events": _R18_SOURCE_ANALYZED_EVENTS,
            "r0022_source_analyzed_events": _R22_SOURCE_ANALYZED_EVENTS,
            "r0022_complete_event_index_document": _EVENT_DOCUMENTS + "r0022-all-event-source-index.json",
            "r0022_ending_document": _EVENT_DOCUMENTS + "r0022-pilgrimage-ending-observed.json",
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
    _validate_r22_source_events(_R22_SOURCE_ANALYZED_EVENTS)
    _validate_source_only_events(_SOURCE_ONLY_EVENTS)
    _validate_source_analyzed_events(_R18_SOURCE_ANALYZED_EVENTS)
    return deepcopy(_RESEARCH)
