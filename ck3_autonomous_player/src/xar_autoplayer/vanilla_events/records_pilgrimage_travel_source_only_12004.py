"""Source-reviewed .4 travel events, deliberately without an action contract.

Historical native indices are evidence, never permission for a fresh window.
"""
from __future__ import annotations

from typing import Literal, TypedDict


class SourcePin(TypedDict):
    game_relative_path: str
    bytes: int
    sha256: str
    relevant_lines: list[list[int]]


class SourceOption(TypedDict):
    source_key: str
    historical_native_index: int | None
    historical_label: str
    effects: list[str]
    visibility: str
    historical_R31_selected: bool


class SourceAnalysis(TypedDict):
    source_analysis_completed: Literal[True]
    migration_review_status: Literal["source_reviewed_no_occurrence_contract"]
    exact_build: Literal["1.20.0.4"]
    source_document: str
    source_document_sha256: str
    occurrence_document: str
    title: str
    source_pins: list[SourcePin]
    source_options: list[SourceOption]
    agent_reference: str
    current_native_legality: None
    action_ready: Literal[False]
    ordinary_auto_consumes: Literal[False]
    full_occurrence_contract_registered: Literal[False]
    selection_policy_changed: Literal[False]
    historical_index_is_current_selection_permission: Literal[False]
    historical_evidence_is_current_state: Literal[False]


class HistoricalObservation(TypedDict):
    machine_id: str
    observed_at_utc: str
    run_id: str
    actual: dict[str, object]
    policy_actually_used: Literal["native_first_displayed_v1"]
    registry_consumption_succeeded_live: Literal[False]


class SourceOnlyRecord(TypedDict):
    analysis: SourceAnalysis
    observations: HistoricalObservation


PILGRIMAGE_TRAVEL_SOURCE_ONLY_12004: dict[str, SourceOnlyRecord] = {'pilgrimage_intent.1060': {'analysis': {'source_analysis_completed': True,
                                         'migration_review_status': 'source_reviewed_no_occurrence_contract',
                                         'exact_build': '1.20.0.4',
                                         'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-intent-1060-source-analysis.json',
                                         'source_document_sha256': 'e6dac5facd7376733e90641344bd93f69d7ed83cb4aa76a437f767dc883fa483',
                                         'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0031-events-001-003-occurrence.json',
                                         'title': '昔日的帝国',
                                         'source_pins': [{'game_relative_path': 'events/activities/pilgrimage_activity/pilgrimage_intent_events.txt',
                                                          'bytes': 57928,
                                                          'sha256': '3ddbde37f029845aa265aae749fe131bed571f02a5c4faac5d0074a615b39878',
                                                          'relevant_lines': [[1516, 1778]]},
                                                         {'game_relative_path': 'common/on_action/activities/pilgrimage_on_actions.txt',
                                                          'bytes': 11904,
                                                          'sha256': 'fdf71f074882f94eb3df497a1ddb2cb9a95fb13e973aebf25d4c3569729ee354',
                                                          'relevant_lines': [[32, 78]]},
                                                         {'game_relative_path': 'localization/simp_chinese/event_localization/activities/pilgrimage_intent_events_l_simp_chinese.yml',
                                                          'bytes': 18043,
                                                          'sha256': '7f2a61394920a1c0675185905e4bb8b3ce431e9b24122267c2e7e5d2663a5b1a',
                                                          'relevant_lines': [[98, 110]]},
                                                         {'game_relative_path': 'common/modifiers/00_activity_pilgrimage_modifiers.txt',
                                                          'bytes': 8263,
                                                          'sha256': 'b4b087debf7975b02fdc30d3244a04aca634e3e26b2fafa4c42057e71a1c1580',
                                                          'relevant_lines': [[248, 258]]},
                                                         {'game_relative_path': 'common/scripted_effects/00_travel_effects.txt',
                                                          'bytes': 1867,
                                                          'sha256': '47a4b46a479a2215ffeda4b6d7b8d9226928f6ec0dc70c289b4e0e2fe2b5ec0e',
                                                          'relevant_lines': [[9, 31]]},
                                                         {'game_relative_path': 'common/scripted_effects/00_pilgrimage_effects.txt',
                                                          'bytes': 40713,
                                                          'sha256': '4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80',
                                                          'relevant_lines': [[1225, 1249]]},
                                                         {'game_relative_path': 'common/script_values/00_basic_values.txt',
                                                          'bytes': 50566,
                                                          'sha256': 'c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef',
                                                          'relevant_lines': [[475, 475],
                                                                             [1132, 1133],
                                                                             [1165, 1166]]},
                                                         {'game_relative_path': 'common/script_values/00_stress_values.txt',
                                                          'bytes': 3852,
                                                          'sha256': '821a0b77244fc5ee2d87d339cb24dbef00787b83d44ec2df9215fc1a93aec2d4',
                                                          'relevant_lines': [[14, 14], [27, 33]]}],
                                         'source_options': [{'source_key': 'pilgrimage_intent.1060.a',
                                                             'historical_native_index': 0,
                                                             'historical_label': '我应当默想古帝国。',
                                                             'effects': ['worldly_type_option_effect only '
                                                                         'when worldly type; not '
                                                                         'automatically pious progress',
                                                                         'delay_travel_plan10days',
                                                                         'minor_piety_gain50',
                                                                         'learning duel versus '
                                                                         'decent_skill_rating12: two base '
                                                                         'weights50 with opposite '
                                                                         'duel_value*0.5 compare modifiers; '
                                                                         'not a constant50percent coin',
                                                                         'success: stress-20 and15year '
                                                                         'imperial_contemplation_modifier(stewardship+1,title_creation_cost_mult-0.2); '
                                                                         'failure: toast only',
                                                                         'stress_and_fulfillment_impact '
                                                                         'base-15,lazy+20,impatient+20 '
                                                                         'before character/system modifiers'],
                                                             'visibility': 'Not independently narrowed by '
                                                                           'this source-only record; read '
                                                                           'source document.',
                                                             'historical_R31_selected': True},
                                                            {'source_key': 'pilgrimage_intent.1060.b',
                                                             'historical_native_index': 1,
                                                             'historical_label': '我应当默想古信仰。',
                                                             'effects': ['conditional pious progress',
                                                                         '10daydelay',
                                                                         'same learning duel weight '
                                                                         'structure',
                                                                         'success:15year '
                                                                         'contemplated_ancient_gods_modifier(learning+1,monthly_piety_gain_mult+0.2),open_minded_perk '
                                                                         'if missing,piety100,conditional '
                                                                         'mystic traitXP',
                                                                         'failure:toast only',
                                                                         'base stress-15 plus '
                                                                         'lazy/impatient/cynical/arrogant+20 '
                                                                         'inputs before modifiers'],
                                                             'visibility': 'Not independently narrowed by '
                                                                           'this source-only record; read '
                                                                           'source document.',
                                                             'historical_R31_selected': False},
                                                            {'source_key': 'pilgrimage_intent.1060.c',
                                                             'historical_native_index': 2,
                                                             'historical_label': '胡扯，阿普利亚将永世长存！',
                                                             'effects': ['zealous/patient medium '
                                                                         'stress-impact gain; no option '
                                                                         'piety/progress/10daydelay block'],
                                                             'visibility': 'not landless adventurer',
                                                             'historical_R31_selected': False},
                                                            {'source_key': 'pilgrimage_intent.1001.b',
                                                             'historical_native_index': 3,
                                                             'historical_label': 'pilgrimage_intent.1001.b',
                                                             'effects': ['same zealous/patient stress '
                                                                         'inputs'],
                                                             'visibility': 'landless_adventurer_government',
                                                             'historical_R31_selected': False}],
                                         'agent_reference': 'Recognize this source as analyzed; identify '
                                                            'exact namespace, fresh scope/options and '
                                                            'current legality. Ancient-empires A is not '
                                                            'ancient-faith B and does not automatically '
                                                            'advance this pious activity. Do not claim duel '
                                                            'success from ACK or floor-zero stress.',
                                         'current_native_legality': None,
                                         'action_ready': False,
                                         'ordinary_auto_consumes': False,
                                         'full_occurrence_contract_registered': False,
                                         'selection_policy_changed': False,
                                         'historical_index_is_current_selection_permission': False,
                                         'historical_evidence_is_current_state': False},
                            'observations': {'machine_id': '4-8e1c2f1861',
                                             'observed_at_utc': '2026-10-21T18:16:25.733875+00:00',
                                             'run_id': '4-8e1c2f1861--faith-engine--R0031',
                                             'actual': {'instance': 2,
                                                        'day': 22,
                                                        'selected_native_index': 0,
                                                        'ack_accepted': True,
                                                        'independent_old_window_gone': True,
                                                        'piety_delta_raw': 5000000,
                                                        'scale': 100000,
                                                        'gold_prestige_delta_raw': [0, 0],
                                                        'stress_before_after': [0, 0],
                                                        'duel_modifier_outcome_or_ETA_or_XP_observed': False},
                                             'policy_actually_used': 'native_first_displayed_v1',
                                             'registry_consumption_succeeded_live': False}},
 'travel_danger_events.1012': {'analysis': {'source_analysis_completed': True,
                                            'migration_review_status': 'source_reviewed_no_occurrence_contract',
                                            'exact_build': '1.20.0.4',
                                            'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/travel-danger-1012-source-analysis.json',
                                            'source_document_sha256': 'a8f238668f3f62ec96074383029e1b8be6274211ca6b69b2e0bcc9c391ee9b73',
                                            'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0031-events-001-003-occurrence.json',
                                            'title': '诱人的水果',
                                            'source_pins': [{'game_relative_path': 'events/travel_events/travel_danger_events_arky.txt',
                                                             'bytes': 43727,
                                                             'sha256': '1659b120131de258f1546c9f6a86b898662d7e2eef5ca949c69d93546a35ca47',
                                                             'relevant_lines': [[784, 914], [915, 1144]]},
                                                            {'game_relative_path': 'common/on_action/travel_on_actions.txt',
                                                             'bytes': 71526,
                                                             'sha256': 'cd40f30a9280ea9ba656b59005201550f3991afd646fd686d7474657b1b1ff70',
                                                             'relevant_lines': [[599, 686]]},
                                                            {'game_relative_path': 'localization/simp_chinese/event_localization/travel_events/travel_danger_events_l_simp_chinese.yml',
                                                             'bytes': 24128,
                                                             'sha256': '88958e34e416161acddf2ef091002782e2239725dbd54c94c83ae52b150717c1',
                                                             'relevant_lines': [[127, 141]]},
                                                            {'game_relative_path': 'common/modifiers/00_travel_modifiers.txt',
                                                             'bytes': 8782,
                                                             'sha256': 'b7a1365a14341bf647339cb843753e5da4f8d9990c52c92d6e10422a8530a2f1',
                                                             'relevant_lines': [[281, 297]]},
                                                            {'game_relative_path': 'common/scripted_effects/00_travel_effects.txt',
                                                             'bytes': 1867,
                                                             'sha256': '47a4b46a479a2215ffeda4b6d7b8d9226928f6ec0dc70c289b4e0e2fe2b5ec0e',
                                                             'relevant_lines': [[9, 31]]},
                                                            {'game_relative_path': 'common/scripted_effects/04_dlc_ep2_tour_effects.txt',
                                                             'bytes': 17935,
                                                             'sha256': '180a9e666317ba7e58525d11848544bca1bf2b6e6062b0fe1110f555abdf328e',
                                                             'relevant_lines': [[330, 367]]},
                                                            {'game_relative_path': 'common/script_values/00_lifestyle_values.txt',
                                                             'bytes': 22192,
                                                             'sha256': '4ddec87bf5c6aeefa2d5f48e42a421408e96b4c85f129727ed6db8fda8bbecc0',
                                                             'relevant_lines': [[7, 8]]},
                                                            {'game_relative_path': 'common/script_values/00_stress_values.txt',
                                                             'bytes': 3852,
                                                             'sha256': '821a0b77244fc5ee2d87d339cb24dbef00787b83d44ec2df9215fc1a93aec2d4',
                                                             'relevant_lines': [[14, 14], [27, 33]]}],
                                            'source_options': [{'source_key': 'travel_danger_events.1012.a',
                                                                'historical_native_index': 0,
                                                                'historical_label': '“等等，万一有毒呢？！”',
                                                                'effects': ['touched_poisonous_plant_effect',
                                                                            'weight50:root AND '
                                                                            'poisonous_plant_eater each '
                                                                            'receive5year touched '
                                                                            'modifier(health-0.05,attraction_opinion-10)',
                                                                            'other weight50+NPClearning '
                                                                            'plus100 if root or NPC knows '
                                                                            'plants or food_taster '
                                                                            'exists:root learning '
                                                                            'lifestyleXP100',
                                                                            'not fixed50percent; extra '
                                                                            'paranoid/compassionate/cynical '
                                                                            'stress-and-fulfillment inputs'],
                                                                'visibility': 'Not independently narrowed by '
                                                                              'this source-only record; read '
                                                                              'source document.',
                                                                'historical_R31_selected': True},
                                                               {'source_key': 'travel_danger_events.1012.b',
                                                                'historical_native_index': 1,
                                                                'historical_label': '让潘多尔夫尝尝看。',
                                                                'effects': ['ate_poisonous_plant_effect with '
                                                                            'PLANT_EATER=NPC36310',
                                                                            'weighted poison:5year eater '
                                                                            'modifier health-0.25/prowess-4; '
                                                                            'regular:root learning '
                                                                            'lifestyleXP100; good:5year '
                                                                            'eater '
                                                                            'prowess+2/stress_loss_mult+0.25',
                                                                            'weights50 '
                                                                            'poison,50+eaterLearning '
                                                                            'regular,1+200 if eater knows '
                                                                            'plants good; not fixed '
                                                                            'percentages',
                                                                            'root traveler dangerXP3..6 only '
                                                                            'if has '
                                                                            'lifestyle_traveler,or5..8 with '
                                                                            'journey_perk',
                                                                            'cynical/paranoid stress inputs'],
                                                                'visibility': 'Not independently narrowed by '
                                                                              'this source-only record; read '
                                                                              'source document.',
                                                                'historical_R31_selected': False},
                                                               {'source_key': 'travel_danger_events.1012.c',
                                                                'historical_native_index': 2,
                                                                'historical_label': '“只有我能先尝！”',
                                                                'effects': ['same eating helper with '
                                                                            'PLANT_EATER=root; '
                                                                            'target-specific modifiers now '
                                                                            'affect player',
                                                                            'same conditional traveler '
                                                                            'dangerXP helper',
                                                                            'comfort_eater/arbitrary/gluttonous '
                                                                            'loss and paranoid/content gain '
                                                                            'stress inputs'],
                                                                'visibility': 'comfort_eater OR arbitrary OR '
                                                                              'gluttonous',
                                                                'historical_R31_selected': False}],
                                            'agent_reference': 'Stopping the eater is not a guarantee of no '
                                                               'health consequence. Keep NPC and root '
                                                               'effects separate. The actual first option '
                                                               'has no authored traveler-dangerXP helper; do '
                                                               "not award it the unchosen eating options'XP. "
                                                               'Current snapshot zero wallet/stress changes '
                                                               'do not close hidden modifiers/XP.',
                                            'current_native_legality': None,
                                            'action_ready': False,
                                            'ordinary_auto_consumes': False,
                                            'full_occurrence_contract_registered': False,
                                            'selection_policy_changed': False,
                                            'historical_index_is_current_selection_permission': False,
                                            'historical_evidence_is_current_state': False},
                               'observations': {'machine_id': '4-8e1c2f1861',
                                                'observed_at_utc': '2026-10-21T18:16:25.733875+00:00',
                                                'run_id': '4-8e1c2f1861--faith-engine--R0031',
                                                'actual': {'instance': 3,
                                                           'day': 23,
                                                           'player_actor': 31254,
                                                           'NPC_plant_eater': 36310,
                                                           'food_taster_scope_present': False,
                                                           'selected_native_index': 0,
                                                           'ack_accepted': True,
                                                           'independent_old_window_gone': True,
                                                           'three_wallet_delta_raw': [0, 0, 0],
                                                           'stress_before_after': [0, 0],
                                                           'actual_modifier_or_health_or_XP_or_fulfillment_branch_observed': False},
                                                'policy_actually_used': 'native_first_displayed_v1',
                                                'registry_consumption_succeeded_live': False}}}

# This batch adds three source-only rows and corrects an unshown source ordinal.
_R31_EXTRA_SOURCE_ONLY_12004: dict[str, SourceOnlyRecord] = {'pilgrimage_intent.1060': {'analysis': {'source_analysis_completed': True,
                                         'migration_review_status': 'source_reviewed_no_occurrence_contract',
                                         'exact_build': '1.20.0.4',
                                         'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-intent-1060-source-analysis.json',
                                         'source_document_sha256': '52acf792591212a94027c1652d3995e3ef990f8d43ce6d51a4cbee581713c1a9',
                                         'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0031-events-001-013-index.json',
                                         'title': '昔日的帝国',
                                         'source_pins': [{'game_relative_path': 'events/activities/pilgrimage_activity/pilgrimage_intent_events.txt',
                                                          'bytes': 57928,
                                                          'sha256': '3ddbde37f029845aa265aae749fe131bed571f02a5c4faac5d0074a615b39878',
                                                          'relevant_lines': [[1516, 1778]]},
                                                         {'game_relative_path': 'common/on_action/activities/pilgrimage_on_actions.txt',
                                                          'bytes': 11904,
                                                          'sha256': 'fdf71f074882f94eb3df497a1ddb2cb9a95fb13e973aebf25d4c3569729ee354',
                                                          'relevant_lines': [[32, 78]]},
                                                         {'game_relative_path': 'localization/simp_chinese/event_localization/activities/pilgrimage_intent_events_l_simp_chinese.yml',
                                                          'bytes': 18043,
                                                          'sha256': '7f2a61394920a1c0675185905e4bb8b3ce431e9b24122267c2e7e5d2663a5b1a',
                                                          'relevant_lines': [[98, 110]]},
                                                         {'game_relative_path': 'common/modifiers/00_activity_pilgrimage_modifiers.txt',
                                                          'bytes': 8263,
                                                          'sha256': 'b4b087debf7975b02fdc30d3244a04aca634e3e26b2fafa4c42057e71a1c1580',
                                                          'relevant_lines': [[248, 258]]},
                                                         {'game_relative_path': 'common/scripted_effects/00_travel_effects.txt',
                                                          'bytes': 1867,
                                                          'sha256': '47a4b46a479a2215ffeda4b6d7b8d9226928f6ec0dc70c289b4e0e2fe2b5ec0e',
                                                          'relevant_lines': [[9, 31]]},
                                                         {'game_relative_path': 'common/scripted_effects/00_pilgrimage_effects.txt',
                                                          'bytes': 40713,
                                                          'sha256': '4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80',
                                                          'relevant_lines': [[1225, 1249]]},
                                                         {'game_relative_path': 'common/script_values/00_basic_values.txt',
                                                          'bytes': 50566,
                                                          'sha256': 'c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef',
                                                          'relevant_lines': [[475, 475],
                                                                             [1132, 1133],
                                                                             [1165, 1166]]},
                                                         {'game_relative_path': 'common/script_values/00_stress_values.txt',
                                                          'bytes': 3852,
                                                          'sha256': '821a0b77244fc5ee2d87d339cb24dbef00787b83d44ec2df9215fc1a93aec2d4',
                                                          'relevant_lines': [[14, 14], [27, 33]]}],
                                         'source_options': [{'source_key': 'pilgrimage_intent.1060.a',
                                                             'historical_native_index': 0,
                                                             'historical_label': '我应当默想古帝国。',
                                                             'effects': ['worldly_type_option_effect only '
                                                                         'when worldly type; not '
                                                                         'automatically pious progress',
                                                                         'delay_travel_plan10days',
                                                                         'minor_piety_gain50',
                                                                         'learning duel versus '
                                                                         'decent_skill_rating12: two base '
                                                                         'weights50 with opposite '
                                                                         'duel_value*0.5 compare modifiers; '
                                                                         'not a constant50percent coin',
                                                                         'success: stress-20 and15year '
                                                                         'imperial_contemplation_modifier(stewardship+1,title_creation_cost_mult-0.2); '
                                                                         'failure: toast only',
                                                                         'stress_and_fulfillment_impact '
                                                                         'base-15,lazy+20,impatient+20 '
                                                                         'before character/system modifiers'],
                                                             'visibility': 'See source document and fresh '
                                                                           'native context; history is not '
                                                                           'current permission.',
                                                             'historical_R31_selected': True},
                                                            {'source_key': 'pilgrimage_intent.1060.b',
                                                             'historical_native_index': 1,
                                                             'historical_label': '我应当默想古信仰。',
                                                             'effects': ['conditional pious progress',
                                                                         '10daydelay',
                                                                         'same learning duel weight '
                                                                         'structure',
                                                                         'success:15year '
                                                                         'contemplated_ancient_gods_modifier(learning+1,monthly_piety_gain_mult+0.2),open_minded_perk '
                                                                         'if missing,piety100,conditional '
                                                                         'mystic traitXP',
                                                                         'failure:toast only',
                                                                         'base stress-15 plus '
                                                                         'lazy/impatient/cynical/arrogant+20 '
                                                                         'inputs before modifiers'],
                                                             'visibility': 'See source document and fresh '
                                                                           'native context; history is not '
                                                                           'current permission.',
                                                             'historical_R31_selected': False},
                                                            {'source_key': 'pilgrimage_intent.1060.c',
                                                             'historical_native_index': 2,
                                                             'historical_label': '胡扯，阿普利亚将永世长存！',
                                                             'effects': ['zealous/patient medium '
                                                                         'stress-impact gain; no option '
                                                                         'piety/progress/10daydelay block'],
                                                             'visibility': 'not landless adventurer',
                                                             'historical_R31_selected': False},
                                                            {'source_key': 'pilgrimage_intent.1001.b',
                                                             'historical_native_index': None,
                                                             'historical_label': 'pilgrimage_intent.1001.b',
                                                             'effects': ['same zealous/patient stress '
                                                                         'inputs'],
                                                             'visibility': 'landless_adventurer_government',
                                                             'historical_R31_selected': False}],
                                         'agent_reference': 'Recognize this source as analyzed; identify '
                                                            'exact namespace, fresh scope/options and '
                                                            'current legality. Ancient-empires A is not '
                                                            'ancient-faith B and does not automatically '
                                                            'advance this pious activity. Do not claim duel '
                                                            'success from ACK or floor-zero stress.',
                                         'current_native_legality': None,
                                         'action_ready': False,
                                         'ordinary_auto_consumes': False,
                                         'full_occurrence_contract_registered': False,
                                         'selection_policy_changed': False,
                                         'historical_index_is_current_selection_permission': False,
                                         'historical_evidence_is_current_state': False},
                            'observations': {'machine_id': '4-8e1c2f1861',
                                             'observed_at_utc': '2026-10-21T18:16:25.733875+00:00',
                                             'run_id': '4-8e1c2f1861--faith-engine--R0031',
                                             'actual': {'instance': 2,
                                                        'day': 22,
                                                        'selected_native_index': 0,
                                                        'ack_accepted': True,
                                                        'independent_old_window_gone': True,
                                                        'stress_before_after': [0, 0],
                                                        'piety_delta_raw': 5000000,
                                                        'scale': 100000,
                                                        'gold_prestige_delta_raw': [0, 0],
                                                        'duel_modifier_outcome_or_ETA_or_XP_observed': False},
                                             'policy_actually_used': 'native_first_displayed_v1',
                                             'registry_consumption_succeeded_live': False}},
 'pilgrimage.6770': {'analysis': {'source_analysis_completed': True,
                                  'migration_review_status': 'source_reviewed_no_occurrence_contract',
                                  'exact_build': '1.20.0.4',
                                  'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-6770-source-analysis.json',
                                  'source_document_sha256': '796f8889c4810c5d9faad9296d0f97ace85d412738966097fc73ff5b9b9c1bfe',
                                  'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0031-events-001-013-index.json',
                                  'title': '圣物商贩（源码概括；题键 pilgrimage.6770.t）',
                                  'source_pins': [{'game_relative_path': 'events/activities/pilgrimage_activity/pilgrimage_events.txt',
                                                   'bytes': 358138,
                                                   'sha256': '900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06',
                                                   'relevant_lines': [[12589, 12877],
                                                                      [12566, 12575],
                                                                      [12577, 12585]]},
                                                  {'game_relative_path': 'common/scripted_effects/00_pilgrimage_effects.txt',
                                                   'bytes': 40713,
                                                   'sha256': '4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80',
                                                   'relevant_lines': [[1225, 1239],
                                                                      [1242, 1250],
                                                                      [1253, 1256]]}],
                                  'source_options': [{'source_key': 'pilgrimage.6770.a',
                                                      'historical_native_index': 0,
                                                      'historical_label': '它\x15EMP 必须\x15!是我的。',
                                                      'effects': ['bonus_to_all_types_effect invokes '
                                                                  'conditional pious/worldly progression '
                                                                  'helpers.',
                                                                  'In involved_activity optional log-entry '
                                                                  'branch, set merchant_relic owner=root and '
                                                                  'apply pilgrimage_6770_relic_effect '
                                                                  '(trusting: medium piety+medium prestige; '
                                                                  'else minor piety).',
                                                                  'pay_short_term_gold to merchant uses '
                                                                  'minor_gold_value with max10; '
                                                                  'greedy/avaricious stress modifiers are '
                                                                  'symbolic.'],
                                                      'visibility': '无显式option trigger；AI权重不是玩家按钮许可',
                                                      'historical_R31_selected': True},
                                                     {'source_key': 'pilgrimage.6770.b',
                                                      'historical_native_index': 1,
                                                      'historical_label': '“我敢肯定你不会想以贪婪的价格出售一件圣物……”',
                                                      'effects': ['worldly_type_option_effect; success can '
                                                                  'transfer relic and pay minor_gold_value '
                                                                  'capped5; failure can apply insulted '
                                                                  'opinion -10 from merchant to root.',
                                                                  'Two base weights50 carry opposing '
                                                                  'duel_value compare modifiers3.5/-3.5; not '
                                                                  'a fixed50/50 probability.',
                                                                  'lazy/gregarious stress modifiers may '
                                                                  'apply.'],
                                                      'visibility': '无显式option trigger；外交/管理duel分支',
                                                      'historical_R31_selected': False},
                                                     {'source_key': 'pilgrimage.6770.c',
                                                      'historical_native_index': 2,
                                                      'historical_label': '“我要把钱花在更有意义的事情上。”',
                                                      'effects': ['Refuse purchase; zealous symbolic minor '
                                                                  'stress gain; no explicit gold transfer in '
                                                                  'this option.'],
                                                      'visibility': '无显式option trigger',
                                                      'historical_R31_selected': False},
                                                     {'source_key': 'pilgrimage.6770.d',
                                                      'historical_native_index': None,
                                                      'historical_label': 'pilgrimage.6770.d',
                                                      'effects': ['bonus_to_all_types_effect; learning '
                                                                  'lifestyle gives '
                                                                  'major_lifestyle_experience, otherwise '
                                                                  'keen_eye_modifier.',
                                                                  'Base major stress loss with zealous '
                                                                  'medium stress gain; actual value depends '
                                                                  'on game traits/modifiers.'],
                                                      'visibility': 'learning >= high_skill_rating',
                                                      'historical_R31_selected': False}],
                                  'agent_reference': 'Read the canonical source document and fresh native '
                                                     'window. Source effects and historical wallet changes '
                                                     'are separate; no live execution contract is granted.',
                                  'current_native_legality': None,
                                  'action_ready': False,
                                  'ordinary_auto_consumes': False,
                                  'full_occurrence_contract_registered': False,
                                  'selection_policy_changed': False,
                                  'historical_index_is_current_selection_permission': False,
                                  'historical_evidence_is_current_state': False},
                     'observations': {'machine_id': '4-8e1c2f1861',
                                      'observed_at_utc': '2026-10-21T18:47:12.709783+00:00',
                                      'run_id': '4-8e1c2f1861--faith-engine--R0031',
                                      'actual': {'event_instance_id': 9,
                                                 'actor_character_id': 31254,
                                                 'historical_selected_native_index': 0,
                                                 'historical_selected_option_number': 1,
                                                 'ack_accepted': True,
                                                 'independent_old_window_gone': True,
                                                 'observed_bound_snapshot_delta': {'stress_points': 17,
                                                                                   'gold': {'raw_delta': -1000000,
                                                                                            'scale': 100000,
                                                                                            'display_delta': '-10'},
                                                                                   'prestige': {'raw_delta': 0,
                                                                                                'scale': 100000,
                                                                                                'display_delta': '0'},
                                                                                   'piety': {'raw_delta': 5000000,
                                                                                             'scale': 100000,
                                                                                             'display_delta': '50'}}},
                                      'policy_actually_used': 'native_first_displayed_v1',
                                      'registry_consumption_succeeded_live': False}},
 'pilgrimage.6830': {'analysis': {'source_analysis_completed': True,
                                  'migration_review_status': 'source_reviewed_no_occurrence_contract',
                                  'exact_build': '1.20.0.4',
                                  'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-6830-source-analysis.json',
                                  'source_document_sha256': 'ad27f45afd4996e5b6fc4d115e5679b9edbf93eaf7c023f9f96c81cb96b2a462',
                                  'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0031-events-001-013-index.json',
                                  'title': '圣地沉思（源码概括；题键 pilgrimage.6830.t）',
                                  'source_pins': [{'game_relative_path': 'events/activities/pilgrimage_activity/pilgrimage_events.txt',
                                                   'bytes': 358138,
                                                   'sha256': '900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06',
                                                   'relevant_lines': [[14149, 14325]]},
                                                  {'game_relative_path': 'common/scripted_effects/00_pilgrimage_effects.txt',
                                                   'bytes': 40713,
                                                   'sha256': '4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80',
                                                   'relevant_lines': [[1225, 1239],
                                                                      [1242, 1250],
                                                                      [1253, 1256]]}],
                                  'source_options': [{'source_key': 'pilgrimage.6830.a',
                                                      'historical_native_index': 0,
                                                      'historical_label': '祈祷的时间到了。',
                                                      'effects': ['pious_type_option_effect and '
                                                                  'add_piety=miniscule_piety_gain.',
                                                                  'Base medium stress loss, zealous '
                                                                  'additional loss; arrogant/cynical can add '
                                                                  'stress. Actual net is not a constant '
                                                                  'prediction.'],
                                                      'visibility': '无显式option trigger',
                                                      'historical_R31_selected': True},
                                                     {'source_key': 'pilgrimage.6830.b',
                                                      'historical_native_index': 1,
                                                      'historical_label': '看看那些拱门……真漂亮。',
                                                      'effects': ['worldly_type_option_effect; learning '
                                                                  'lifestyle may receive '
                                                                  'minor_lifestyle_experience.',
                                                                  'random_list80 gives '
                                                                  'architectural_interest_modifier '
                                                                  'for10years; weight20 gives learning '
                                                                  'skill+1. R31 did not select this branch.',
                                                                  'Base medium stress loss with zealous '
                                                                  'medium stress gain.'],
                                                      'visibility': '无显式option trigger',
                                                      'historical_R31_selected': False},
                                                     {'source_key': 'pilgrimage.6830.c',
                                                      'historical_native_index': 2,
                                                      'historical_label': '我应该进行奉献。',
                                                      'effects': ['pious_type_option_effect; miniscule piety '
                                                                  'gain; pilgrim trait XP+20.',
                                                                  'Hidden effect destroys '
                                                                  'scope:votive_artifact: this donation '
                                                                  'spends an artifact, not an explicit gold '
                                                                  'amount.',
                                                                  'Base medium stress loss with '
                                                                  'greedy/avaricious/cynical stress '
                                                                  'modifiers.'],
                                                      'visibility': 'votive_artifact exists; pilgrim trait; '
                                                                    'pilgrim trait XP<100',
                                                      'historical_R31_selected': False}],
                                  'agent_reference': 'Read the canonical source document and fresh native '
                                                     'window. Source effects and historical wallet changes '
                                                     'are separate; no live execution contract is granted.',
                                  'current_native_legality': None,
                                  'action_ready': False,
                                  'ordinary_auto_consumes': False,
                                  'full_occurrence_contract_registered': False,
                                  'selection_policy_changed': False,
                                  'historical_index_is_current_selection_permission': False,
                                  'historical_evidence_is_current_state': False},
                     'observations': {'machine_id': '4-8e1c2f1861',
                                      'observed_at_utc': '2026-10-21T18:47:12.709783+00:00',
                                      'run_id': '4-8e1c2f1861--faith-engine--R0031',
                                      'actual': {'event_instance_id': 10,
                                                 'actor_character_id': 31254,
                                                 'historical_selected_native_index': 0,
                                                 'historical_selected_option_number': 1,
                                                 'ack_accepted': True,
                                                 'independent_old_window_gone': True,
                                                 'observed_bound_snapshot_delta': {'stress_points': -33,
                                                                                   'gold': {'raw_delta': 0,
                                                                                            'scale': 100000,
                                                                                            'display_delta': '0'},
                                                                                   'prestige': {'raw_delta': 0,
                                                                                                'scale': 100000,
                                                                                                'display_delta': '0'},
                                                                                   'piety': {'raw_delta': 2500000,
                                                                                             'scale': 100000,
                                                                                             'display_delta': '25'}}},
                                      'policy_actually_used': 'native_first_displayed_v1',
                                      'registry_consumption_succeeded_live': False}},
 'pilgrimage.6820': {'analysis': {'source_analysis_completed': True,
                                  'migration_review_status': 'source_reviewed_no_occurrence_contract',
                                  'exact_build': '1.20.0.4',
                                  'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-6820-source-analysis.json',
                                  'source_document_sha256': 'a2e4bcb902faed6c85858bbf602736f44e0ac41cc666060d18368e1ac2270cc7',
                                  'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0031-events-001-013-index.json',
                                  'title': '朝圣者指南',
                                  'source_pins': [{'game_relative_path': 'events/activities/pilgrimage_activity/pilgrimage_events.txt',
                                                   'bytes': 358138,
                                                   'sha256': '900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06',
                                                   'relevant_lines': [[13925, 14136]]},
                                                  {'game_relative_path': 'localization/simp_chinese/event_localization/activities/pilgrimage_events_l_simp_chinese.yml',
                                                   'bytes': 136481,
                                                   'sha256': 'cecb7052ac6672f1fd99a0008a8e7d6ccca474069a17e8a9902c55571cd272b3',
                                                   'relevant_lines': [[915, 922]]},
                                                  {'game_relative_path': 'common/on_action/activities/pilgrimage_on_actions.txt',
                                                   'bytes': 11904,
                                                   'sha256': 'fdf71f074882f94eb3df497a1ddb2cb9a95fb13e973aebf25d4c3569729ee354',
                                                   'relevant_lines': [[379, 406]]},
                                                  {'game_relative_path': 'common/scripted_effects/00_pilgrimage_effects.txt',
                                                   'bytes': 40713,
                                                   'sha256': '4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80',
                                                   'relevant_lines': [[1225, 1256]]},
                                                  {'game_relative_path': 'common/modifiers/00_artifact_modifiers.txt',
                                                   'bytes': 79092,
                                                   'sha256': '06495c2f0b39634895f9587a4f3fb26725183d913851d4ea1ec6f4d3b8efe059',
                                                   'relevant_lines': [[504, 504], [772, 772]]},
                                                  {'game_relative_path': 'common/modifiers/00_activity_pilgrimage_modifiers.txt',
                                                   'bytes': 8263,
                                                   'sha256': 'b4b087debf7975b02fdc30d3244a04aca634e3e26b2fafa4c42057e71a1c1580',
                                                   'relevant_lines': [[169, 172]]},
                                                  {'game_relative_path': 'common/modifiers/00_ep2_travel_modifiers.txt',
                                                   'bytes': 3548,
                                                   'sha256': '61b162720efbe2e445b5556f423a6bc8c39c804b5ec6895decfe927fae1e11d3',
                                                   'relevant_lines': [[181, 184]]},
                                                  {'game_relative_path': 'common/script_values/00_basic_values.txt',
                                                   'bytes': 50566,
                                                   'sha256': 'c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef',
                                                   'relevant_lines': [[49, 51],
                                                                      [452, 452],
                                                                      [475, 475],
                                                                      [1131, 1131],
                                                                      [1164, 1164]]},
                                                  {'game_relative_path': 'common/script_values/01_dynamic_values.txt',
                                                   'bytes': 48201,
                                                   'sha256': '023165e7d27d106a34f34d7726d938efa8d5dce25650ea3256e0b5ea3f73cc2a',
                                                   'relevant_lines': [[53, 71]]},
                                                  {'game_relative_path': 'common/script_values/00_stress_values.txt',
                                                   'bytes': 3852,
                                                   'sha256': '821a0b77244fc5ee2d87d339cb24dbef00787b83d44ec2df9215fc1a93aec2d4',
                                                   'relevant_lines': [[27, 28]]}],
                                  'source_options': [{'source_key': 'pilgrimage.6820.a',
                                                      'historical_native_index': 0,
                                                      'historical_label': '“我来一本！”',
                                                      'effects': ['worldly_type_option_effect: progression '
                                                                  'only if the involved activity has worldly '
                                                                  'pilgrimage type; not automatic pious '
                                                                  'progression',
                                                                  'pay_short_term_gold to guide_merchant '
                                                                  'with gold value=min(minor_gold_value,5); '
                                                                  'this is a capped script quote, not '
                                                                  'whole-journey cost',
                                                                  'set guide_scope owner to root with '
                                                                  'purchased history',
                                                                  'if current_travel_plan exists, add '
                                                                  'pilgrim_guide_modifier whose definition '
                                                                  'is travel_safety_mult=0.3; this is a '
                                                                  'modifier value, not '
                                                                  'guaranteed30percentagepoints or zero '
                                                                  'travel danger',
                                                                  'stress_and_fulfillment_impact receives '
                                                                  'greedy,avaricious,arrogant '
                                                                  'each=minor_stress_impact_gain20 before '
                                                                  'character/system handling; actual current '
                                                                  'trait cause and fulfillment response were '
                                                                  'not independently read'],
                                                      'visibility': 'See source document and fresh native '
                                                                    'context; history is not current '
                                                                    'permission.',
                                                      'historical_R31_selected': True},
                                                     {'source_key': 'pilgrimage.6820.b',
                                                      'historical_native_index': 1,
                                                      'historical_label': '“让我看看——啊！如果你在这里转弯……”',
                                                      'effects': ['bonus_to_all_types_effect invokes '
                                                                  'pious_type_option_effect and '
                                                                  'worldly_type_option_effect; actual helper '
                                                                  'bodies remain type-gated, with pious '
                                                                  'helper also covering Hajj',
                                                                  'local_expert_modifier for10years; '
                                                                  'definition monthly_piety=0.2',
                                                                  'random_list weights80 empty /20 '
                                                                  'add_diplomacy_skill1; no actual random '
                                                                  'outcome exists because this option was '
                                                                  'not selected',
                                                                  'add pilgrim_guide_modifier to '
                                                                  'current_travel_plan; no book purchase or '
                                                                  'payment block',
                                                                  'humble=medium_stress_impact_gain40 input '
                                                                  'to stress_and_fulfillment_impact',
                                                                  'destroy the unsold guide_scope artifact'],
                                                      'visibility': 'See source document and fresh native '
                                                                    'context; history is not current '
                                                                    'permission.',
                                                      'historical_R31_selected': False},
                                                     {'source_key': 'pilgrimage.6820.c',
                                                      'historical_native_index': 2,
                                                      'historical_label': '神会引导我。',
                                                      'effects': ['pious_type_option_effect: only pious/Hajj '
                                                                  'activity types receive the helper '
                                                                  'progression',
                                                                  'add_piety=miniscule_piety_gain=miniscule_piety_value25',
                                                                  'destroy the unsold guide_scope artifact; '
                                                                  'no option payment block'],
                                                      'visibility': 'See source document and fresh native '
                                                                    'context; history is not current '
                                                                    'permission.',
                                                      'historical_R31_selected': False}],
                                  'agent_reference': 'Recognize the exact source as analyzed, but reacquire '
                                                     "the caller's current exact definition, instance, "
                                                     'root/saved scopes, rendered order, enabled state and '
                                                     'native revision before any action. A disabled expert '
                                                     'response cannot be selected merely because its source '
                                                     'benefit is attractive. Preserve ACK and independent '
                                                     'disappearance separately. Empty/incomplete effect '
                                                     'indicators cannot prove free cost, no trait effect or '
                                                     'no artifact transfer. Existing native-first-displayed '
                                                     'policy is recorded as historical behavior, not '
                                                     'replaced by this document. Unknown action outcomes '
                                                     'must not be resubmitted.',
                                  'current_native_legality': None,
                                  'action_ready': False,
                                  'ordinary_auto_consumes': False,
                                  'full_occurrence_contract_registered': False,
                                  'selection_policy_changed': False,
                                  'historical_index_is_current_selection_permission': False,
                                  'historical_evidence_is_current_state': False},
                     'observations': {'machine_id': '4-8e1c2f1861',
                                      'observed_at_utc': '2026-10-21T18:44:58.716696+00:00',
                                      'run_id': '4-8e1c2f1861--faith-engine--R0031',
                                      'actual': {'instance': 12,
                                                 'actor_full_id': 31254,
                                                 'selected_native_index': 0,
                                                 'selected_option_number': 1,
                                                 'ack_accepted': True,
                                                 'independent_old_window_gone': True,
                                                 'date_before_after': [53147760, 53147760],
                                                 'bridge_pid': 18136,
                                                 'connection_generation': 1,
                                                 'wallet_piety_prestige_readback': {'played_character_gold': {'before_raw': 16410784,
                                                                                                              'after_raw': 15910784,
                                                                                                              'delta_raw': -500000,
                                                                                                              'scale': 100000},
                                                                                    'played_character_piety': {'before_raw': 2038689750,
                                                                                                               'after_raw': 2038689750,
                                                                                                               'delta_raw': 0,
                                                                                                               'scale': 100000},
                                                                                    'played_character_prestige': {'before_raw': 221074740,
                                                                                                                  'after_raw': 221074740,
                                                                                                                  'delta_raw': 0,
                                                                                                                  'scale': 100000}},
                                                 'stress_before_after': [31, 48],
                                                 'material_effects_beyond_wallet_and_stress_observed': False},
                                      'policy_actually_used': 'native_first_displayed_v1',
                                      'registry_consumption_succeeded_live': False}}}
PILGRIMAGE_TRAVEL_SOURCE_ONLY_12004.update(_R31_EXTRA_SOURCE_ONLY_12004)


# R0034 source analysis and historical occurrence metadata only.
# historical_R31_selected remains false; R0034 selections live in observations.actual.
_R0034_SOURCE_ONLY: dict[str, SourceOnlyRecord] = {'travel_start_event.1060': {'analysis': {'source_analysis_completed': True,
                                          'migration_review_status': 'source_reviewed_no_occurrence_contract',
                                          'exact_build': '1.20.0.4',
                                          'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/travel-start-1060-source-analysis.json',
                                          'source_document_sha256': '50d844aa0fbf036b974fb0cd22fc7a340c374d8264f9ad6c1506ef9ef3066540',
                                          'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0034-events-occurrence.json',
                                          'title': '朝觐（源码题键 travel_start_event.1060.t_hajj）',
                                          'source_pins': [{'game_relative_path': 'events/travel_events/travel_start_events.txt',
                                                           'bytes': 95408,
                                                           'sha256': '4ef3fb9e9c1da72ec6660a98805ed4fdc4b90d95becc73d334b98487ddf13dc9',
                                                           'relevant_lines': [[2158, 2304],
                                                                              [2307, 2601]]},
                                                          {'game_relative_path': 'common/scripted_effects/00_pilgrimage_effects.txt',
                                                           'bytes': 40713,
                                                           'sha256': '4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80',
                                                           'relevant_lines': [[1225, 1249]]},
                                                          {'game_relative_path': 'common/scripted_effects/00_activity_effects.txt',
                                                           'bytes': 116295,
                                                           'sha256': 'd5c594f8746b923d34b13a67db881821e12f08ce1ab4e6e3f83933419c9e2d38',
                                                           'relevant_lines': [[4357, 4365]]},
                                                          {'game_relative_path': 'common/script_values/00_basic_values.txt',
                                                           'bytes': 50566,
                                                           'sha256': 'c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef',
                                                           'relevant_lines': [[1001, 1001],
                                                                              [1034, 1034],
                                                                              [1131, 1136],
                                                                              [1164, 1166]]},
                                                          {'game_relative_path': 'common/script_values/00_stress_values.txt',
                                                           'bytes': 3852,
                                                           'sha256': '821a0b77244fc5ee2d87d339cb24dbef00787b83d44ec2df9215fc1a93aec2d4',
                                                           'relevant_lines': [[5, 17], [25, 35]]},
                                                          {'game_relative_path': 'common/script_values/00_lifestyle_values.txt',
                                                           'bytes': 22192,
                                                           'sha256': '4ddec87bf5c6aeefa2d5f48e42a421408e96b4c85f129727ed6db8fda8bbecc0',
                                                           'relevant_lines': [[5, 11], [889, 891]]},
                                                          {'game_relative_path': 'common/modifiers/00_activity_pilgrimage_modifiers.txt',
                                                           'bytes': 8263,
                                                           'sha256': 'b4b087debf7975b02fdc30d3244a04aca634e3e26b2fafa4c42057e71a1c1580',
                                                           'relevant_lines': [[57, 71]]},
                                                          {'game_relative_path': 'common/scripted_effects/00_travel_effects.txt',
                                                           'bytes': 1867,
                                                           'sha256': '47a4b46a479a2215ffeda4b6d7b8d9226928f6ec0dc70c289b4e0e2fe2b5ec0e',
                                                           'relevant_lines': [[9, 31]]},
                                                          {'game_relative_path': 'common/on_action/activities/pilgrimage_on_actions.txt',
                                                           'bytes': 11904,
                                                           'sha256': 'fdf71f074882f94eb3df497a1ddb2cb9a95fb13e973aebf25d4c3569729ee354',
                                                           'relevant_lines': [[4, 17],
                                                                              [32, 37],
                                                                              [74, 91]]},
                                                          {'game_relative_path': 'common/on_action/travel_on_actions.txt',
                                                           'bytes': 71526,
                                                           'sha256': 'cd40f30a9280ea9ba656b59005201550f3991afd646fd686d7474657b1b1ff70',
                                                           'relevant_lines': [[1172, 1178],
                                                                              [1441, 1453]]},
                                                          {'game_relative_path': 'localization/simp_chinese/event_localization/travel_events/travel_start_events_l_simp_chinese.yml',
                                                           'bytes': 33689,
                                                           'sha256': '7c6146fc235866430d1fa2667afe2610b703830ef74d181cfae4a952b1372e78',
                                                           'relevant_lines': [[15, 19]]}],
                                          'source_options': [{'source_key': 'travel_start_event.1060/option[0]',
                                                              'historical_native_index': 0,
                                                              'historical_label': '我一生都在等待这一刻。',
                                                              'effects': ['One source option with '
                                                                          'conditional name; '
                                                                          'actual firstHajj name '
                                                                          'key '
                                                                          'travel_start_event.1000.a_hajj.',
                                                                          'Only shows conditional '
                                                                          'companion-count '
                                                                          'tooltip; no new direct '
                                                                          'wallet/trait/XP effect '
                                                                          'in option body.',
                                                                          'Companion assembly '
                                                                          'happened in immediate, '
                                                                          'not because option '
                                                                          'selection awarded '
                                                                          'companions.'],
                                                              'visibility': 'unconditional source '
                                                                            'option',
                                                              'historical_R31_selected': False}],
                                          'agent_reference': 'on_travel_plan_start events list '
                                                             'TRAVELOA:1172,1449; event requires '
                                                             'available travelling landed actor '
                                                             'and pilgrimage activity, '
                                                             'START:2405-2409. Plays start music; '
                                                             'saves travel leader; builds eligible '
                                                             'sameFaith local/neighbor-duchy '
                                                             'candidates excluding '
                                                             'cynical/nonbeliever; chooses/adds '
                                                             'companions up to pomp cap; '
                                                             'player-only generates additional '
                                                             'companions if still short. Protected '
                                                             'holy-place modifier may request+20 '
                                                             'activity progression. '
                                                             'START:2410-2533; helper '
                                                             'details2158-2304. Removes '
                                                             'rando_pilgrim_counter, '
                                                             'START:2597-2600. R0034 indices and '
                                                             'labels describe one historical '
                                                             'occurrence; fresh native '
                                                             'shown/enabled mapping is required. '
                                                             'R31 selection fields remain false '
                                                             'because this is R0034.',
                                          'current_native_legality': None,
                                          'action_ready': False,
                                          'ordinary_auto_consumes': False,
                                          'full_occurrence_contract_registered': False,
                                          'selection_policy_changed': False,
                                          'historical_index_is_current_selection_permission': False,
                                          'historical_evidence_is_current_state': False},
                             'observations': {'machine_id': '4-8e1c2f1861',
                                              'observed_at_utc': '2026-10-22T15:03:59.715221+00:00',
                                              'run_id': '4-8e1c2f1861--faith-engine--R0034',
                                              'actual': {'instance': 4,
                                                         'date_raw': 51394944,
                                                         'actor_character_id': 15893,
                                                         'actor_after_character_id': 15893,
                                                         'selected_native_index': 0,
                                                         'selected_option_number': 1,
                                                         'selected_source_option_key': 'travel_start_event.1060/option[0]',
                                                         'ack_accepted': True,
                                                         'independent_old_window_gone': True,
                                                         'gold_delta_raw': 0,
                                                         'prestige_delta_raw': 0,
                                                         'piety_delta_raw': 0,
                                                         'scale': 100000,
                                                         'stress_before_after': [0, 0],
                                                         'activity_progression_trait_xp_modifier_or_eta_observed': False,
                                                         'selection_execution_route': 'native_first_displayed_v1'},
                                              'policy_actually_used': 'native_first_displayed_v1',
                                              'registry_consumption_succeeded_live': False}},
 'pilgrimage_intent.1030': {'analysis': {'source_analysis_completed': True,
                                         'migration_review_status': 'source_reviewed_no_occurrence_contract',
                                         'exact_build': '1.20.0.4',
                                         'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-intent-1030-source-analysis.json',
                                         'source_document_sha256': '9b9e28ee6e63cf1497f2a33911396903d3d50f3344be0fdee9d3faa3c71a8c84',
                                         'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0034-events-occurrence.json',
                                         'title': '宁静的空地（源码题键 pilgrimage_intent.1030.t）',
                                         'source_pins': [{'game_relative_path': 'events/activities/pilgrimage_activity/pilgrimage_intent_events.txt',
                                                          'bytes': 57928,
                                                          'sha256': '3ddbde37f029845aa265aae749fe131bed571f02a5c4faac5d0074a615b39878',
                                                          'relevant_lines': [[781, 875],
                                                                             [1782, 1878]]},
                                                         {'game_relative_path': 'common/scripted_effects/00_pilgrimage_effects.txt',
                                                          'bytes': 40713,
                                                          'sha256': '4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80',
                                                          'relevant_lines': [[1225, 1249]]},
                                                         {'game_relative_path': 'common/scripted_effects/00_activity_effects.txt',
                                                          'bytes': 116295,
                                                          'sha256': 'd5c594f8746b923d34b13a67db881821e12f08ce1ab4e6e3f83933419c9e2d38',
                                                          'relevant_lines': [[4357, 4365]]},
                                                         {'game_relative_path': 'common/script_values/00_basic_values.txt',
                                                          'bytes': 50566,
                                                          'sha256': 'c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef',
                                                          'relevant_lines': [[1001, 1001],
                                                                             [1034, 1034],
                                                                             [1131, 1136],
                                                                             [1164, 1166]]},
                                                         {'game_relative_path': 'common/script_values/00_stress_values.txt',
                                                          'bytes': 3852,
                                                          'sha256': '821a0b77244fc5ee2d87d339cb24dbef00787b83d44ec2df9215fc1a93aec2d4',
                                                          'relevant_lines': [[5, 17], [25, 35]]},
                                                         {'game_relative_path': 'common/script_values/00_lifestyle_values.txt',
                                                          'bytes': 22192,
                                                          'sha256': '4ddec87bf5c6aeefa2d5f48e42a421408e96b4c85f129727ed6db8fda8bbecc0',
                                                          'relevant_lines': [[5, 11], [889, 891]]},
                                                         {'game_relative_path': 'common/modifiers/00_activity_pilgrimage_modifiers.txt',
                                                          'bytes': 8263,
                                                          'sha256': 'b4b087debf7975b02fdc30d3244a04aca634e3e26b2fafa4c42057e71a1c1580',
                                                          'relevant_lines': [[57, 71]]},
                                                         {'game_relative_path': 'common/scripted_effects/00_travel_effects.txt',
                                                          'bytes': 1867,
                                                          'sha256': '47a4b46a479a2215ffeda4b6d7b8d9226928f6ec0dc70c289b4e0e2fe2b5ec0e',
                                                          'relevant_lines': [[9, 31]]},
                                                         {'game_relative_path': 'common/on_action/activities/pilgrimage_on_actions.txt',
                                                          'bytes': 11904,
                                                          'sha256': 'fdf71f074882f94eb3df497a1ddb2cb9a95fb13e973aebf25d4c3569729ee354',
                                                          'relevant_lines': [[4, 17],
                                                                             [32, 37],
                                                                             [74, 91]]},
                                                         {'game_relative_path': 'localization/simp_chinese/event_localization/activities/pilgrimage_intent_events_l_simp_chinese.yml',
                                                          'bytes': 18043,
                                                          'sha256': '7f2a61394920a1c0675185905e4bb8b3ce431e9b24122267c2e7e5d2663a5b1a',
                                                          'relevant_lines': [[47, 51],
                                                                             [123, 127]]}],
                                         'source_options': [{'source_key': 'pilgrimage_intent.1030.a',
                                                             'historical_native_index': 0,
                                                             'historical_label': '这是安拉的意志。',
                                                             'effects': ['Pious/Hajj type helper '
                                                                         'requests+10 activity '
                                                                         'progression only if '
                                                                         'progression variable '
                                                                         'exists.',
                                                                         'Unconditional current '
                                                                         'travel-plan delay10days.',
                                                                         'NoPilgrim:piety50; '
                                                                         'existingPilgrim '
                                                                         'below100XP:baseXP10; '
                                                                         'otherwise:piety100.',
                                                                         'If mystic held:random '
                                                                         'base mysticXP3..5.',
                                                                         'Stress/fulfillment '
                                                                         'inputs '
                                                                         'base-15,zealous-15,impatient+20,cynical+20 '
                                                                         'before character/system '
                                                                         'processing.'],
                                                             'visibility': 'unconditional source '
                                                                           'option',
                                                             'historical_R31_selected': False},
                                                            {'source_key': 'pilgrimage_intent.1030.b',
                                                             'historical_native_index': 1,
                                                             'historical_label': '我们不能拖延！',
                                                             'effects': ['Stress/fulfillment '
                                                                         'inputs '
                                                                         'lazy+20,zealous+40,patient+40; '
                                                                         'no10day option delay, '
                                                                         'piety, PilgrimXP or '
                                                                         'type-progress helper.'],
                                                             'visibility': 'unconditional source '
                                                                           'option',
                                                             'historical_R31_selected': False}],
                                         'agent_reference': 'Shared pilgrimage_travel_events '
                                                            'weight50 at OA:74; reflection_intent '
                                                            'required; event cooldown2years, not '
                                                            'activity-global cooldown. '
                                                            'mp_delay_travel_plan90days only if '
                                                            'has_multiple_players=yes (MP:20-31); '
                                                            'not an unconditional90day '
                                                            'singleplayer delay. '
                                                            'mp_resume_travel_plan only for '
                                                            'multiplayer, INTENT:872-874; MP:9-17. '
                                                            'R0034 indices and labels describe one '
                                                            'historical occurrence; fresh native '
                                                            'shown/enabled mapping is required. '
                                                            'R31 selection fields remain false '
                                                            'because this is R0034.',
                                         'current_native_legality': None,
                                         'action_ready': False,
                                         'ordinary_auto_consumes': False,
                                         'full_occurrence_contract_registered': False,
                                         'selection_policy_changed': False,
                                         'historical_index_is_current_selection_permission': False,
                                         'historical_evidence_is_current_state': False},
                            'observations': {'machine_id': '4-8e1c2f1861',
                                             'observed_at_utc': '2026-10-22T15:05:11.732272+00:00',
                                             'run_id': '4-8e1c2f1861--faith-engine--R0034',
                                             'actual': {'instance': 5,
                                                        'date_raw': 51395088,
                                                        'actor_character_id': 15893,
                                                        'actor_after_character_id': 15893,
                                                        'selected_native_index': 0,
                                                        'selected_option_number': 1,
                                                        'selected_source_option_key': 'pilgrimage_intent.1030.a',
                                                        'ack_accepted': True,
                                                        'independent_old_window_gone': True,
                                                        'gold_delta_raw': 0,
                                                        'prestige_delta_raw': 0,
                                                        'piety_delta_raw': 5000000,
                                                        'scale': 100000,
                                                        'stress_before_after': [0, 0],
                                                        'activity_progression_trait_xp_modifier_or_eta_observed': False,
                                                        'selection_execution_route': 'native_first_displayed_v1'},
                                             'policy_actually_used': 'native_first_displayed_v1',
                                             'registry_consumption_succeeded_live': False}},
 'pilgrimage.3102': {'analysis': {'source_analysis_completed': True,
                                  'migration_review_status': 'source_reviewed_no_occurrence_contract',
                                  'exact_build': '1.20.0.4',
                                  'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0034-events-source-analysis-12004.json',
                                  'source_document_sha256': 'ad92aac15c6fc25d9c43c77b36ae6b8555fed7ed099516cf79ded1f320876b35',
                                  'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0034-events-occurrence.json',
                                  'title': '拜谒（源码题键 pilgrimage.3102.t）',
                                  'source_pins': [{'game_relative_path': 'events/activities/pilgrimage_activity/pilgrimage_events.txt',
                                                   'bytes': 358138,
                                                   'sha256': '900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06',
                                                   'relevant_lines': [[7285, 7401]]},
                                                  {'game_relative_path': 'common/scripted_effects/00_pilgrimage_effects.txt',
                                                   'bytes': 40713,
                                                   'sha256': '4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80',
                                                   'relevant_lines': [[1225, 1249]]},
                                                  {'game_relative_path': 'common/scripted_effects/00_activity_effects.txt',
                                                   'bytes': 116295,
                                                   'sha256': 'd5c594f8746b923d34b13a67db881821e12f08ce1ab4e6e3f83933419c9e2d38',
                                                   'relevant_lines': [[4357, 4365]]},
                                                  {'game_relative_path': 'common/script_values/00_basic_values.txt',
                                                   'bytes': 50566,
                                                   'sha256': 'c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef',
                                                   'relevant_lines': [[1001, 1001],
                                                                      [1034, 1034],
                                                                      [1131, 1136],
                                                                      [1164, 1166]]},
                                                  {'game_relative_path': 'common/script_values/00_stress_values.txt',
                                                   'bytes': 3852,
                                                   'sha256': '821a0b77244fc5ee2d87d339cb24dbef00787b83d44ec2df9215fc1a93aec2d4',
                                                   'relevant_lines': [[5, 17], [25, 35]]},
                                                  {'game_relative_path': 'common/script_values/00_lifestyle_values.txt',
                                                   'bytes': 22192,
                                                   'sha256': '4ddec87bf5c6aeefa2d5f48e42a421408e96b4c85f129727ed6db8fda8bbecc0',
                                                   'relevant_lines': [[5, 11], [889, 891]]},
                                                  {'game_relative_path': 'common/modifiers/00_activity_pilgrimage_modifiers.txt',
                                                   'bytes': 8263,
                                                   'sha256': 'b4b087debf7975b02fdc30d3244a04aca634e3e26b2fafa4c42057e71a1c1580',
                                                   'relevant_lines': [[57, 71]]},
                                                  {'game_relative_path': 'common/scripted_effects/00_travel_effects.txt',
                                                   'bytes': 1867,
                                                   'sha256': '47a4b46a479a2215ffeda4b6d7b8d9226928f6ec0dc70c289b4e0e2fe2b5ec0e',
                                                   'relevant_lines': [[9, 31]]},
                                                  {'game_relative_path': 'common/on_action/activities/pilgrimage_on_actions.txt',
                                                   'bytes': 11904,
                                                   'sha256': 'fdf71f074882f94eb3df497a1ddb2cb9a95fb13e973aebf25d4c3569729ee354',
                                                   'relevant_lines': [[4, 17], [32, 37], [74, 91]]},
                                                  {'game_relative_path': 'localization/simp_chinese/event_localization/activities/pilgrimage_events_l_simp_chinese.yml',
                                                   'bytes': 136481,
                                                   'sha256': 'cecb7052ac6672f1fd99a0008a8e7d6ccca474069a17e8a9902c55571cd272b3',
                                                   'relevant_lines': [[574, 579]]}],
                                  'source_options': [{'source_key': 'pilgrimage.3102.a',
                                                      'historical_native_index': 0,
                                                      'historical_label': '我想见识下安拉辉煌创造的全貌。',
                                                      'effects': ['Worldly helper gives+10 '
                                                                  'progression only for worldly '
                                                                  'type; on Hajj it does not '
                                                                  'match.',
                                                                  'If traveller held and '
                                                                  'travel-track below100:baseXP5.',
                                                                  'Stress request-10 and piety25.',
                                                                  'If mystic held:random base '
                                                                  'mysticXP3..5.',
                                                                  'Ten-year '
                                                                  'pilgrimage_worldly_modifier:owned_personal_scheme_success_chance_add15.'],
                                                      'visibility': 'unconditional source option',
                                                      'historical_R31_selected': False},
                                                     {'source_key': 'pilgrimage.3102.b',
                                                      'historical_native_index': 1,
                                                      'historical_label': '我的热情炽烈如火，我想做的也不仅仅是朝觐而已。',
                                                      'effects': ['Pious/Hajj helper '
                                                                  'requests+10progression if '
                                                                  'variable exists.',
                                                                  'If existingPilgrim '
                                                                  'below100:baseXP5; no trait '
                                                                  'creation.',
                                                                  'Piety50; ten-year '
                                                                  'dedicated_to_pilgrimage_modifier '
                                                                  'monthly_piety_gain_mult+0.1.'],
                                                      'visibility': 'not cynical; source also has '
                                                                    'show_as_unavailable cynical',
                                                      'historical_R31_selected': False},
                                                     {'source_key': 'pilgrimage.3102.c',
                                                      'historical_native_index': 2,
                                                      'historical_label': '我萌生的怀疑驱使我在这片遥远的土地上寻找答案。',
                                                      'effects': ['Pious/Hajj helper '
                                                                  'requests+10progression if '
                                                                  'variable exists.',
                                                                  'Stress/fulfillment inputs '
                                                                  'base+20,cynical-15,stubborn+20,arrogant+20.',
                                                                  'Requests500 learning '
                                                                  'lifestyleXP.'],
                                                      'visibility': 'not zealous; source also has '
                                                                    'show_as_unavailable zealous',
                                                      'historical_R31_selected': False}],
                                  'agent_reference': 'Shared pilgrimage_travel_events weight100 at '
                                                     'OA:91; Islam and legal land travel location '
                                                     'required; event cooldown2years. No immediate '
                                                     'effect block. No after effect block. R0034 '
                                                     'indices and labels describe one historical '
                                                     'occurrence; fresh native shown/enabled '
                                                     'mapping is required. R31 selection fields '
                                                     'remain false because this is R0034.',
                                  'current_native_legality': None,
                                  'action_ready': False,
                                  'ordinary_auto_consumes': False,
                                  'full_occurrence_contract_registered': False,
                                  'selection_policy_changed': False,
                                  'historical_index_is_current_selection_permission': False,
                                  'historical_evidence_is_current_state': False},
                     'observations': {'machine_id': '4-8e1c2f1861',
                                      'observed_at_utc': '2026-10-22T15:08:12.269658+00:00',
                                      'run_id': '4-8e1c2f1861--faith-engine--R0034',
                                      'actual': {'instance': 6,
                                                 'date_raw': 51395520,
                                                 'actor_character_id': 15893,
                                                 'actor_after_character_id': 15893,
                                                 'selected_native_index': 0,
                                                 'selected_option_number': 1,
                                                 'selected_source_option_key': 'pilgrimage.3102.a',
                                                 'ack_accepted': True,
                                                 'independent_old_window_gone': True,
                                                 'gold_delta_raw': 0,
                                                 'prestige_delta_raw': 0,
                                                 'piety_delta_raw': 2500000,
                                                 'scale': 100000,
                                                 'stress_before_after': [0, 0],
                                                 'activity_progression_trait_xp_modifier_or_eta_observed': False,
                                                 'selection_execution_route': 'native_first_displayed_v1'},
                                      'policy_actually_used': 'native_first_displayed_v1',
                                      'registry_consumption_succeeded_live': False}},
 'pilgrimage_intent.1100': {'analysis': {'source_analysis_completed': True,
                                         'migration_review_status': 'source_reviewed_no_occurrence_contract',
                                         'exact_build': '1.20.0.4',
                                         'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-intent-1100-source-analysis.json',
                                         'source_document_sha256': '4a4a32e38c359402143973c13b485f6a70e304420a1fe93b271aab3117d83d58',
                                         'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0034-events-occurrence.json',
                                         'title': '星空（源码题键 pilgrimage_intent.1100.t）',
                                         'source_pins': [{'game_relative_path': 'events/activities/pilgrimage_activity/pilgrimage_intent_events.txt',
                                                          'bytes': 57928,
                                                          'sha256': '3ddbde37f029845aa265aae749fe131bed571f02a5c4faac5d0074a615b39878',
                                                          'relevant_lines': [[781, 875],
                                                                             [1782, 1878]]},
                                                         {'game_relative_path': 'common/scripted_effects/00_pilgrimage_effects.txt',
                                                          'bytes': 40713,
                                                          'sha256': '4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80',
                                                          'relevant_lines': [[1225, 1249]]},
                                                         {'game_relative_path': 'common/scripted_effects/00_activity_effects.txt',
                                                          'bytes': 116295,
                                                          'sha256': 'd5c594f8746b923d34b13a67db881821e12f08ce1ab4e6e3f83933419c9e2d38',
                                                          'relevant_lines': [[4357, 4365]]},
                                                         {'game_relative_path': 'common/script_values/00_basic_values.txt',
                                                          'bytes': 50566,
                                                          'sha256': 'c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef',
                                                          'relevant_lines': [[1001, 1001],
                                                                             [1034, 1034],
                                                                             [1131, 1136],
                                                                             [1164, 1166]]},
                                                         {'game_relative_path': 'common/script_values/00_stress_values.txt',
                                                          'bytes': 3852,
                                                          'sha256': '821a0b77244fc5ee2d87d339cb24dbef00787b83d44ec2df9215fc1a93aec2d4',
                                                          'relevant_lines': [[5, 17], [25, 35]]},
                                                         {'game_relative_path': 'common/script_values/00_lifestyle_values.txt',
                                                          'bytes': 22192,
                                                          'sha256': '4ddec87bf5c6aeefa2d5f48e42a421408e96b4c85f129727ed6db8fda8bbecc0',
                                                          'relevant_lines': [[5, 11], [889, 891]]},
                                                         {'game_relative_path': 'common/modifiers/00_activity_pilgrimage_modifiers.txt',
                                                          'bytes': 8263,
                                                          'sha256': 'b4b087debf7975b02fdc30d3244a04aca634e3e26b2fafa4c42057e71a1c1580',
                                                          'relevant_lines': [[57, 71]]},
                                                         {'game_relative_path': 'common/scripted_effects/00_travel_effects.txt',
                                                          'bytes': 1867,
                                                          'sha256': '47a4b46a479a2215ffeda4b6d7b8d9226928f6ec0dc70c289b4e0e2fe2b5ec0e',
                                                          'relevant_lines': [[9, 31]]},
                                                         {'game_relative_path': 'common/on_action/activities/pilgrimage_on_actions.txt',
                                                          'bytes': 11904,
                                                          'sha256': 'fdf71f074882f94eb3df497a1ddb2cb9a95fb13e973aebf25d4c3569729ee354',
                                                          'relevant_lines': [[4, 17],
                                                                             [32, 37],
                                                                             [74, 91]]},
                                                         {'game_relative_path': 'localization/simp_chinese/event_localization/activities/pilgrimage_intent_events_l_simp_chinese.yml',
                                                          'bytes': 18043,
                                                          'sha256': '7f2a61394920a1c0675185905e4bb8b3ce431e9b24122267c2e7e5d2663a5b1a',
                                                          'relevant_lines': [[47, 51],
                                                                             [123, 127]]}],
                                         'source_options': [{'source_key': 'pilgrimage_intent.1100.a',
                                                             'historical_native_index': 0,
                                                             'historical_label': '这当然是我的神圣义务！',
                                                             'effects': ['Pious/Hajj helper '
                                                                         'requests+10progression '
                                                                         'if variable exists.',
                                                                         'Ten-year '
                                                                         'dedicated_to_pilgrimage_modifier:monthly_piety_gain_mult+0.1.',
                                                                         'Only if existingPilgrim '
                                                                         'below100:baseXP5; never '
                                                                         'awards Pilgrim from XP.',
                                                                         'If mystic held:random '
                                                                         'base mysticXP3..5.',
                                                                         'Cynical '
                                                                         'stress/fulfillment '
                                                                         'input+20. No direct '
                                                                         'piety grant.'],
                                                             'visibility': 'unconditional source '
                                                                           'option',
                                                             'historical_R31_selected': False},
                                                            {'source_key': 'pilgrimage_intent.1100.b',
                                                             'historical_native_index': 1,
                                                             'historical_label': '我真正想要的是享受和体验其他文化。',
                                                             'effects': ['Worldly helper matches '
                                                                         'worldly only, not Hajj.',
                                                                         'Stress request-20; '
                                                                         'ten-year '
                                                                         'pilgrimage_worldly_modifier '
                                                                         'personal scheme success '
                                                                         'chance+15.'],
                                                             'visibility': 'unconditional source '
                                                                           'option',
                                                             'historical_R31_selected': False},
                                                            {'source_key': 'pilgrimage_intent.1100.c',
                                                             'historical_native_index': 2,
                                                             'historical_label': '我所做的只是我所处的地位所要求的。',
                                                             'effects': ['Ten-year '
                                                                         'showy_about_pilgrimage_modifier '
                                                                         'zealot_opinion+5,clergy_opinion+10.',
                                                                         'Zealous '
                                                                         'stress/fulfillment '
                                                                         'input+20; no '
                                                                         'type-progress helper.'],
                                                             'visibility': 'unconditional source '
                                                                           'option',
                                                             'historical_R31_selected': False}],
                                         'agent_reference': 'Shared pilgrimage_travel_events '
                                                            'weight100 OA:78; reflection_intent; '
                                                            'event cooldown2years. No immediate '
                                                            'effect block. No after effect block. '
                                                            'R0034 indices and labels describe one '
                                                            'historical occurrence; fresh native '
                                                            'shown/enabled mapping is required. '
                                                            'R31 selection fields remain false '
                                                            'because this is R0034.',
                                         'current_native_legality': None,
                                         'action_ready': False,
                                         'ordinary_auto_consumes': False,
                                         'full_occurrence_contract_registered': False,
                                         'selection_policy_changed': False,
                                         'historical_index_is_current_selection_permission': False,
                                         'historical_evidence_is_current_state': False},
                            'observations': {'machine_id': '4-8e1c2f1861',
                                             'observed_at_utc': '2026-10-22T15:14:50.795675+00:00',
                                             'run_id': '4-8e1c2f1861--faith-engine--R0034',
                                             'actual': {'instance': 7,
                                                        'date_raw': 51395688,
                                                        'actor_character_id': 15893,
                                                        'actor_after_character_id': 15893,
                                                        'selected_native_index': 0,
                                                        'selected_option_number': 1,
                                                        'selected_source_option_key': 'pilgrimage_intent.1100.a',
                                                        'ack_accepted': True,
                                                        'independent_old_window_gone': True,
                                                        'gold_delta_raw': 0,
                                                        'prestige_delta_raw': 0,
                                                        'piety_delta_raw': 0,
                                                        'scale': 100000,
                                                        'stress_before_after': [0, 0],
                                                        'activity_progression_trait_xp_modifier_or_eta_observed': False,
                                                        'selection_execution_route': 'root_native_first_displayed_once'},
                                             'policy_actually_used': 'native_first_displayed_v1',
                                             'registry_consumption_succeeded_live': False}}}
PILGRIMAGE_TRAVEL_SOURCE_ONLY_12004.update(_R0034_SOURCE_ONLY)


# R0035 occurrence observations remain separate from every R0031 field.
_R0035_SOURCE_ONLY: dict[str, SourceOnlyRecord] = {
    "pilgrimage_intent.1040": {
        "analysis": {
            "source_analysis_completed": True,
            "migration_review_status": "source_reviewed_no_occurrence_contract",
            "exact_build": "1.20.0.4",
            "source_document": "promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-intent-1040-source-analysis.json",
            "source_document_sha256": "bbc377c91cb934371298ae13b9dd26f22c588af0dd93296fb433af830a942716",
            "occurrence_document": "promo/ck3_faith_and_power/episode02/docs/knowledge/r0035-events-occurrence.json",
            "title": "$reflections_intent_header$野兽预兆",
            "source_pins": [{"game_relative_path": "events/activities/pilgrimage_activity/pilgrimage_intent_events.txt", "bytes": 57928, "sha256": "3ddbde37f029845aa265aae749fe131bed571f02a5c4faac5d0074a615b39878", "relevant_lines": [[879, 1016]]}, {"game_relative_path": "common/scripted_effects/00_travel_effects.txt", "bytes": 1867, "sha256": "47a4b46a479a2215ffeda4b6d7b8d9226928f6ec0dc70c289b4e0e2fe2b5ec0e", "relevant_lines": [[9, 31]]}, {"game_relative_path": "common/scripted_effects/00_pilgrimage_effects.txt", "bytes": 40713, "sha256": "4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80", "relevant_lines": [[1225, 1238]]}, {"game_relative_path": "common/script_values/00_basic_values.txt", "bytes": 50566, "sha256": "c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef", "relevant_lines": [[1132, 1132], [1165, 1165]]}, {"game_relative_path": "localization/simp_chinese/event_localization/activities/pilgrimage_intent_events_l_simp_chinese.yml", "bytes": 18043, "sha256": "7f2a61394920a1c0675185905e4bb8b3ce431e9b24122267c2e7e5d2663a5b1a", "relevant_lines": [[53, 61]]}],
            "source_options": [{"source_key": "pilgrimage_intent.1040.a", "historical_native_index": 0, "historical_label": "那只瞪羚是安拉的使者！跟上他！", "effects": ["Pious/Hajj progression helper; travel delay10days; minor_piety_gain base50.", "Hidden outcome1041/1042/1043/1044 or lost-animal toast with separate predator/prey guards; not a guaranteed followup.", "Conditional stress/fulfillment: base/zealous minor loss; lazy/impatient/craven/paranoid minor gain."], "visibility": "Shown rendered0/native0 in R0035.", "historical_R31_selected": False}, {"source_key": "pilgrimage_intent.1040.b", "historical_native_index": 1, "historical_label": "我们不能分心。", "effects": ["No option-level detour, piety or progression declared.", "Conditional stress/fulfillment: zealous/patient/lifestyle_hunter medium gain."], "visibility": "Shown rendered1/native1 in R0035.", "historical_R31_selected": False}],
            "agent_reference": "Reuse K1040 unchanged, including old not-live followup labels. Immediate MP90day helper is multiplayer-only. R0035 actual1043 is recorded separately; no new policy.",
            "current_native_legality": None,
            "action_ready": False,
            "ordinary_auto_consumes": False,
            "full_occurrence_contract_registered": False,
            "selection_policy_changed": False,
            "historical_index_is_current_selection_permission": False,
            "historical_evidence_is_current_state": False,
        },
        "observations": {"machine_id": "4-8e1c2f1861", "observed_at_utc": "2026-10-22T16:48:30.349664+00:00", "run_id": "4-8e1c2f1861--faith-engine--R0035", "actual": {"instance_id": 6, "actor_character_id": 15893, "date_raw": [51395472, 51395472], "selected_native_option_index": 0, "selected_option_number": 1, "ack_accepted": True, "old_instance_gone_in_independent_snapshot": True, "wallet_delta_raw": {"gold": 0, "prestige": 0, "piety": 5000000}, "wallet_scale": 100000, "stress_before_after": [0, 0]}, "policy_actually_used": "native_first_displayed_v1", "registry_consumption_succeeded_live": False},
    },
    "pilgrimage_intent.1043": {
        "analysis": {
            "source_analysis_completed": True,
            "migration_review_status": "source_reviewed_no_occurrence_contract",
            "exact_build": "1.20.0.4",
            "source_document": "promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-intent-1040-source-analysis.json",
            "source_document_sha256": "bbc377c91cb934371298ae13b9dd26f22c588af0dd93296fb433af830a942716",
            "occurrence_document": "promo/ck3_faith_and_power/episode02/docs/knowledge/r0035-events-occurrence.json",
            "title": "预兆：阖家欢乐",
            "source_pins": [{"game_relative_path": "events/activities/pilgrimage_activity/pilgrimage_intent_events.txt", "bytes": 57928, "sha256": "3ddbde37f029845aa265aae749fe131bed571f02a5c4faac5d0074a615b39878", "relevant_lines": [[1151, 1245]]}, {"game_relative_path": "common/modifiers/00_activity_pilgrimage_modifiers.txt", "bytes": 8263, "sha256": "b4b087debf7975b02fdc30d3244a04aca634e3e26b2fafa4c42057e71a1c1580", "relevant_lines": [[225, 235]]}, {"game_relative_path": "localization/simp_chinese/event_localization/activities/pilgrimage_intent_events_l_simp_chinese.yml", "bytes": 18043, "sha256": "7f2a61394920a1c0675185905e4bb8b3ce431e9b24122267c2e7e5d2663a5b1a", "relevant_lines": [[75, 80]]}],
            "source_options": [{"source_key": "pilgrimage_intent.1043.a", "historical_native_index": 0, "historical_label": "我很快会有一个孩子！", "effects": ["Guard fertility>=0.1;20year pilgrimage_horny_omen_modifier fertility+0.3.", "Conditional stress/fulfillment base/lustful minor loss; chaste minor gain; not proof of pregnancy/newborn."], "visibility": "Shown rendered0/native0 in R0035.", "historical_R31_selected": False}, {"source_key": "pilgrimage_intent.1043.b", "historical_native_index": None, "historical_label": "我必须和我的敌人交朋友。", "effects": ["Guard any rival; remove one random rivalry.", "Conditional stress/fulfillment base minor loss,forgiving major loss,paranoid/callous/sadistic minor gain,vengeful major gain."], "visibility": "Not shown in R0035; label from source localization, no historical native index claimed.", "historical_R31_selected": False}, {"source_key": "pilgrimage_intent.1043.c", "historical_native_index": 2, "historical_label": "我应当把家庭放在第一位。", "effects": ["20year family modifier:house opinion10,close relative opinion15,monthly dynasty prestige0.1.", "Conditional stress/fulfillment base minor loss,paranoid/craven medium gain."], "visibility": "Shown rendered1/native2 in R0035.", "historical_R31_selected": False}],
            "agent_reference": "K1040 possible_followup_effects_not_live_observed[2] remains historical. Immediate existing Pilgrim+XP<100 requests10XP and creates good_prey memory. Actual modifier/XP/pregnancy not observed.",
            "current_native_legality": None,
            "action_ready": False,
            "ordinary_auto_consumes": False,
            "full_occurrence_contract_registered": False,
            "selection_policy_changed": False,
            "historical_index_is_current_selection_permission": False,
            "historical_evidence_is_current_state": False,
        },
        "observations": {"machine_id": "4-8e1c2f1861", "observed_at_utc": "2026-10-22T16:48:40.435583+00:00", "run_id": "4-8e1c2f1861--faith-engine--R0035", "actual": {"instance_id": 7, "actor_character_id": 15893, "date_raw": [51395472, 51395472], "selected_native_option_index": 0, "selected_option_number": 1, "ack_accepted": True, "old_instance_gone_in_independent_snapshot": True, "wallet_delta_raw": {"gold": 0, "prestige": 0, "piety": 0}, "wallet_scale": 100000, "stress_before_after": [0, 0]}, "policy_actually_used": "native_first_displayed_v1", "registry_consumption_succeeded_live": False},
    },
    "travel_danger_events.9010": {
        "analysis": {
            "source_analysis_completed": True,
            "migration_review_status": "source_reviewed_no_occurrence_contract",
            "exact_build": "1.20.0.4",
            "source_document": "promo/ck3_faith_and_power/episode02/docs/knowledge/r0035-events-source-only-analysis-12004.json",
            "source_document_sha256": "39c1eeb0887c3d61b310f62195dc2ca18cdc7a90370eebbeb8444ef482722ba1",
            "occurrence_document": "promo/ck3_faith_and_power/episode02/docs/knowledge/r0035-events-occurrence.json",
            "title": "$travel_danger_prefix$困于车轮",
            "source_pins": [{"game_relative_path": "events/travel_events/travel_danger_events_oltner.txt", "bytes": 27455, "sha256": "086725937d1b89b82be5f957aef461f95bf0810ff506abf09c2031c779f3ab3d", "relevant_lines": [[301, 440]]}, {"game_relative_path": "common/scripted_effects/04_dlc_ep2_tour_effects.txt", "bytes": 17935, "sha256": "180a9e666317ba7e58525d11848544bca1bf2b6e6062b0fe1110f555abdf328e", "relevant_lines": [[330, 366]]}, {"game_relative_path": "common/scripted_effects/00_travel_effects.txt", "bytes": 1867, "sha256": "47a4b46a479a2215ffeda4b6d7b8d9226928f6ec0dc70c289b4e0e2fe2b5ec0e", "relevant_lines": [[9, 31]]}, {"game_relative_path": "common/script_values/00_basic_values.txt", "bytes": 50566, "sha256": "c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef", "relevant_lines": [[1001, 1015], [1034, 1034]]}, {"game_relative_path": "common/on_action/travel_on_actions.txt", "bytes": 71526, "sha256": "cd40f30a9280ea9ba656b59005201550f3991afd646fd686d7474657b1b1ff70", "relevant_lines": [[12, 12], [599, 700]]}, {"game_relative_path": "localization/simp_chinese/event_localization/travel_events/travel_danger_events_oltner_l_simp_chinese.yml", "bytes": 7676, "sha256": "fbd5fd212ff052c3b0396946e3d7b5144d1bd9327bb7f475ed0efb0efdad983b", "relevant_lines": [[10, 14]]}],
            "source_options": [{"source_key": "travel_danger_events.9010.strong", "historical_native_index": None, "historical_label": "把马车抬离地面时大声叹息", "effects": ["Guard strong OR physique_good;prestige base+75;travel delay2days."], "visibility": "Not shown in R0035; source-localized label, no historical native index claimed.", "historical_R31_selected": False}, {"source_key": "travel_danger_events.9010.a", "historical_native_index": 1, "historical_label": "该死……我们要迟到了。", "effects": ["Travel delay5days; no direct wallet/stress effect declared."], "visibility": "Shown first rendered0/native1; first displayed is not native0.", "historical_R31_selected": False}, {"source_key": "travel_danger_events.9010.b", "historical_native_index": 2, "historical_label": "整理下补给品，从现在开始我会骑得很粗暴……", "effects": ["Prestige base-75;travel delay2days;arrogant medium stress/fulfillment gain."], "visibility": "Shown rendered1/native2 in R0035.", "historical_R31_selected": False}],
            "agent_reference": "Definition301-440;event cooldown1month. Immediate MP90day/after resume are multiplayer-only. Already-held Traveller dangerXP3..7,or5..9 with journey_perk; no Pilgrim XP. Actual ETA/XP not read.",
            "current_native_legality": None,
            "action_ready": False,
            "ordinary_auto_consumes": False,
            "full_occurrence_contract_registered": False,
            "selection_policy_changed": False,
            "historical_index_is_current_selection_permission": False,
            "historical_evidence_is_current_state": False,
        },
        "observations": {"machine_id": "4-8e1c2f1861", "observed_at_utc": "2026-10-22T16:55:57.968217+00:00", "run_id": "4-8e1c2f1861--faith-engine--R0035", "actual": {"instance_id": 9, "actor_character_id": 15893, "date_raw": [51396408, 51396408], "selected_native_option_index": 1, "selected_option_number": 2, "ack_accepted": True, "old_instance_gone_in_independent_snapshot": True, "wallet_delta_raw": {"gold": 0, "prestige": 0, "piety": 0}, "wallet_scale": 100000, "stress_before_after": [0, 0]}, "policy_actually_used": "native_first_displayed_v1", "registry_consumption_succeeded_live": False},
    },
    "rite_travel_events.1000": {
        "analysis": {
            "source_analysis_completed": True,
            "migration_review_status": "source_reviewed_no_occurrence_contract",
            "exact_build": "1.20.0.4",
            "source_document": "promo/ck3_faith_and_power/episode02/docs/knowledge/r0035-events-source-only-analysis-12004.json",
            "source_document_sha256": "39c1eeb0887c3d61b310f62195dc2ca18cdc7a90370eebbeb8444ef482722ba1",
            "occurrence_document": "promo/ck3_faith_and_power/episode02/docs/knowledge/r0035-events-occurrence.json",
            "title": "路过的[passive_learn_rite.GetAdherentNameNoTooltip]",
            "source_pins": [{"game_relative_path": "events/passive_rite_learning_events/passive_rite_learning_travel_events.txt", "bytes": 4947, "sha256": "7c7efde0843b328e0e83662a886238875b001735d1128e6343e4e1d8635af402", "relevant_lines": [[8, 104]]}, {"game_relative_path": "common/scripted_triggers/passive_rite_learning_triggers.txt", "bytes": 12365, "sha256": "4cde80d60a415b5dfef815d656f1b07c6d4d1582edc09cded9a91ed503224885", "relevant_lines": [[70, 89]]}, {"game_relative_path": "common/scripted_effects/00_pilgrimage_effects.txt", "bytes": 40713, "sha256": "4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80", "relevant_lines": [[1225, 1249]]}, {"game_relative_path": "common/scripted_effects/00_activity_effects.txt", "bytes": 116295, "sha256": "d5c594f8746b923d34b13a67db881821e12f08ce1ab4e6e3f83933419c9e2d38", "relevant_lines": [[4432, 4469]]}, {"game_relative_path": "common/on_action/travel_on_actions.txt", "bytes": 71526, "sha256": "cd40f30a9280ea9ba656b59005201550f3991afd646fd686d7474657b1b1ff70", "relevant_lines": [[1006, 1006]]}, {"game_relative_path": "localization/simp_chinese/passive_rite_learning_travel_l_simp_chinese.yml", "bytes": 2728, "sha256": "f06aab60a96ce5de92dab438933de399d818d61e46e65831911251179c8e5bfd", "relevant_lines": [[7, 11]]}, {"game_relative_path": "common/script_values/00_basic_values.txt", "bytes": 50566, "sha256": "c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef", "relevant_lines": [[1132, 1132], [1165, 1165]]}],
            "source_options": [{"source_key": "rite_travel_events.1000.a", "historical_native_index": 0, "historical_label": "非常有见地。", "effects": ["add_known_rite=source Rite;worldly helper;learned-Rite message.", "Stress/fulfillment base/humble minor loss; no current Rite/Faith setter declared."], "visibility": "Shown rendered0/native0 in R0035.", "historical_R31_selected": False}, {"source_key": "rite_travel_events.1000.b", "historical_native_index": 1, "historical_label": "她应该加入我。", "effects": ["Same knowledge/worldly/message;guarded add to court/entourage/activity;source grateful opinion+50 toward root.", "Zealous/paranoid minor stress/fulfillment gain."], "visibility": "Shown rendered1/native1 in R0035; gendered label is occurrence-specific.", "historical_R31_selected": False}, {"source_key": "rite_travel_events.1000.c", "historical_native_index": 2, "historical_label": "我对这种异端邪说不感兴趣。", "effects": ["Minor piety base50;pious helper matches Pious/Hajj;humble minor stress/fulfillment gain."], "visibility": "Shown rendered2/native2 in R0035.", "historical_R31_selected": False}],
            "agent_reference": "Definition8-104;event cooldown5years,not pilgrimage cooldown. Source19713 saved, Rite payload unavailable. Worldly helper does not match Hajj. Known-Rite/current Faith/Rite/entourage/progression actual changes not observed.",
            "current_native_legality": None,
            "action_ready": False,
            "ordinary_auto_consumes": False,
            "full_occurrence_contract_registered": False,
            "selection_policy_changed": False,
            "historical_index_is_current_selection_permission": False,
            "historical_evidence_is_current_state": False,
        },
        "observations": {"machine_id": "4-8e1c2f1861", "observed_at_utc": "2026-10-22T17:01:28.626817+00:00", "run_id": "4-8e1c2f1861--faith-engine--R0035", "actual": {"instance_id": 10, "actor_character_id": 15893, "date_raw": [51397080, 51397080], "selected_native_option_index": 0, "selected_option_number": 1, "ack_accepted": True, "old_instance_gone_in_independent_snapshot": True, "wallet_delta_raw": {"gold": 0, "prestige": 0, "piety": 0}, "wallet_scale": 100000, "stress_before_after": [0, 0]}, "policy_actually_used": "native_first_displayed_v1", "registry_consumption_succeeded_live": False},
    },
}
PILGRIMAGE_TRAVEL_SOURCE_ONLY_12004.update(_R0035_SOURCE_ONLY)


# Source-reviewed R0036 only; native first displayed policy is unchanged.
_R0036_SOURCE_ONLY: dict[str, SourceOnlyRecord] = {
    'travel_danger_events.1007': {
        'analysis': {
            'source_analysis_completed': True,
            'migration_review_status': 'source_reviewed_no_occurrence_contract',
            'exact_build': '1.20.0.4',
            'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0036-travel-danger-1007.source-only.json',
            'source_document_sha256': '2237a2bfcb2c05e249eb068bcea73d4636ffff832544740478f1f48f6f95a763',
            'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0036-events-occurrence.json',
            'title': 'Running out of water',
            'source_pins': [{'game_relative_path': 'events/travel_events/travel_danger_events.txt', 'bytes': 43538, 'sha256': 'f0db7d940d106d7031b118e6e2e3f0b3e92e7238859534b13c07f14ab6521b89', 'relevant_lines': [[806, 973]]}, {'game_relative_path': 'localization/simp_chinese/event_localization/travel_events/travel_danger_events_l_simp_chinese.yml', 'bytes': 24128, 'sha256': '88958e34e416161acddf2ef091002782e2239725dbd54c94c83ae52b150717c1', 'relevant_lines': [[51, 66]]}, {'game_relative_path': 'common/modifiers/07_ep3_laamp_flavor_modifiers.txt', 'bytes': 12197, 'sha256': '14c807e0de9c74b4cae59cf3ba2b9f5da7c6ff24be9998ca931f9fb7913bc7ce', 'relevant_lines': [[302, 305]]}, {'game_relative_path': 'common/modifiers/00_travel_modifiers.txt', 'bytes': 8782, 'sha256': 'b7a1365a14341bf647339cb843753e5da4f8d9990c52c92d6e10422a8530a2f1', 'relevant_lines': [[323, 327]]}, {'game_relative_path': 'common/script_values/00_basic_values.txt', 'bytes': 50566, 'sha256': 'c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef', 'relevant_lines': [[692, 692], [2300, 2300], [2319, 2322]]}, {'game_relative_path': 'common/scripted_effects/04_dlc_ep2_tour_effects.txt', 'bytes': 17935, 'sha256': '180a9e666317ba7e58525d11848544bca1bf2b6e6062b0fe1110f555abdf328e', 'relevant_lines': [[330, 366]]}, {'game_relative_path': 'common/scripted_effects/00_travel_effects.txt', 'bytes': 1867, 'sha256': '47a4b46a479a2215ffeda4b6d7b8d9226928f6ec0dc70c289b4e0e2fe2b5ec0e', 'relevant_lines': [[9, 31]]}, {'game_relative_path': 'common/on_action/travel_on_actions.txt', 'bytes': 71526, 'sha256': 'cd40f30a9280ea9ba656b59005201550f3991afd646fd686d7474657b1b1ff70', 'relevant_lines': [[678, 684]]}],
            'source_options': [{'source_key': 'travel_danger_events.1007.d', 'historical_native_index': None, 'historical_label': '好在我们带了额外的水！', 'effects': ['Domicile has supply_tent_reserve_water. Domicile provisions -75; no other explicit option effect.'], 'visibility': 'Not displayed; no actual native index claimed.', 'historical_R31_selected': False}, {'source_key': 'travel_danger_events.1007.a', 'historical_native_index': None, 'historical_label': '我知道附近有个绿洲，也许能拯救我们。', 'effects': ['Neighboring oasis required; add saved oasis province as travel waypoint. No explicit wallet cost.'], 'visibility': 'Not displayed; no actual native index claimed.', 'historical_R31_selected': False}, {'source_key': 'travel_danger_events.1007.b', 'historical_native_index': 2, 'historical_label': '都怪我的同行者玛赫莎喝得和\x15EMP 马\x15!一样多，无法忍受！', 'effects': ['Random weights10:90: death_thirst for water_hider; OR water_hider opinion of root -50 plus 2-year dehydration-t2 health-2. No explicit root wallet/stress change.'], 'visibility': 'Displayed rendered0/native2, selected in R0036.', 'historical_R31_selected': False}, {'source_key': 'travel_danger_events.1007.c', 'historical_native_index': 3, 'historical_label': '我们需要坚持下去。', 'effects': ['Root and every entourage character each get stacking dehydrated_modifier health-0.5 for2years.'], 'visibility': 'Displayed rendered1/native3; not selected.', 'historical_R31_selected': False}],
            'agent_reference': 'R0036 instance6; first shown native2, not source option0. R0036 outer pending tags retained unchanged; batch stopped at3101, no choice/noSave. No registry consumption credited.',
            'current_native_legality': None,
            'action_ready': False,
            'ordinary_auto_consumes': False,
            'full_occurrence_contract_registered': False,
            'selection_policy_changed': False,
            'historical_index_is_current_selection_permission': False,
            'historical_evidence_is_current_state': False,
        },
        'observations': {
            'machine_id': '4-8e1c2f1861',
            'observed_at_utc': '2026-10-22T20:08:01.322017+00:00',
            'run_id': '4-8e1c2f1861--faith-engine--R0036',
            'actual': {'instance_id': 6, 'actor_character_id': 15893, 'date_raw': 51396240, 'selected_native_option_index': 2, 'selected_option_number': 3, 'ack_accepted': True, 'old_instance_gone_in_independent_snapshot': True},
            'policy_actually_used': 'native_first_displayed_v1',
            'registry_consumption_succeeded_live': False,
        },
    },
    'pilgrimage.2060': {
        'analysis': {
            'source_analysis_completed': True,
            'migration_review_status': 'source_reviewed_no_occurrence_contract',
            'exact_build': '1.20.0.4',
            'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0036-pilgrimage-2060.source-only.json',
            'source_document_sha256': '8bd63c5e7ea6b4e698d52f85a807bf183b038baf7ee608d18f1f6a26de454b4f',
            'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0036-events-occurrence.json',
            'title': 'Tavern storytelling',
            'source_pins': [{'game_relative_path': 'events/activities/pilgrimage_activity/pilgrimage_events.txt', 'bytes': 358138, 'sha256': '900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06', 'relevant_lines': [[5211, 5436]]}, {'game_relative_path': 'common/scripted_effects/00_pilgrimage_effects.txt', 'bytes': 40713, 'sha256': '4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80', 'relevant_lines': [[1225, 1249]]}, {'game_relative_path': 'common/script_values/00_basic_values.txt', 'bytes': 50566, 'sha256': 'c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef', 'relevant_lines': [[1001, 1001], [1034, 1034], [1132, 1132], [1165, 1165]]}, {'game_relative_path': 'common/script_values/00_stress_values.txt', 'bytes': 3852, 'sha256': '821a0b77244fc5ee2d87d339cb24dbef00787b83d44ec2df9215fc1a93aec2d4', 'relevant_lines': [[25, 35]]}, {'game_relative_path': 'localization/simp_chinese/event_localization/activities/pilgrimage_events_l_simp_chinese.yml', 'bytes': 136481, 'sha256': 'cecb7052ac6672f1fd99a0008a8e7d6ccca474069a17e8a9902c55571cd272b3', 'relevant_lines': [[1114, 1121]]}, {'game_relative_path': 'common/on_action/activities/pilgrimage_on_actions.txt', 'bytes': 11904, 'sha256': 'fdf71f074882f94eb3df497a1ddb2cb9a95fb13e973aebf25d4c3569729ee354', 'relevant_lines': [[55, 55]]}, {'game_relative_path': 'common/scripted_triggers/00_pilgrimage_triggers.txt', 'bytes': 2851, 'sha256': '5d9058814175bcf018c659be2565f6f6edd3fa06bc2104d474f109cb12ec740a', 'relevant_lines': [[87, 113]]}],
            'source_options': [{'source_key': 'pilgrimage.2060.a', 'historical_native_index': 0, 'historical_label': '终于有点乐子了。', 'effects': ['Worldly-only progress helper; otherwise base medium stress-impact loss. Reveler/cynical additional medium loss, zealous minor gain. Saved pilgrim opinion of root +30. No direct Pilgrim trait or XP.'], 'visibility': 'Displayed in R0036 instance7.', 'historical_R31_selected': False}, {'source_key': 'pilgrimage.2060.b', 'historical_native_index': 1, 'historical_label': '“将故事转为祈祷。”', 'effects': ['Only pilgrimage_type_pious calls progress helper; ELSE piety+50, including Hajj because outer type check excludes Hajj. Saved pilgrim opinion of root -15. Zealous medium loss; shy minor, reveler medium, cynical major stress impacts. Catholic after1050 has alternate displayed text; same source option.'], 'visibility': 'Displayed in R0036 instance7.', 'historical_R31_selected': False}, {'source_key': 'pilgrimage.2060.c', 'historical_native_index': 2, 'historical_label': '平民的事情我并不关心。', 'effects': ['Prestige+75. Lazy minor stress-impact loss; zealous/reveler medium gain. No trait grant or XP.'], 'visibility': 'Displayed in R0036 instance7.', 'historical_R31_selected': False}],
            'agent_reference': 'R0036 instance7; source inventory progress branches reused, full options and occurrence added. R0036 outer pending tags retained unchanged; batch stopped at3101, no choice/noSave. No registry consumption credited.',
            'current_native_legality': None,
            'action_ready': False,
            'ordinary_auto_consumes': False,
            'full_occurrence_contract_registered': False,
            'selection_policy_changed': False,
            'historical_index_is_current_selection_permission': False,
            'historical_evidence_is_current_state': False,
        },
        'observations': {
            'machine_id': '4-8e1c2f1861',
            'observed_at_utc': '2026-10-22T20:18:57.388041+00:00',
            'run_id': '4-8e1c2f1861--faith-engine--R0036',
            'actual': {'instance_id': 7, 'actor_character_id': 15893, 'date_raw': 51398832, 'selected_native_option_index': 0, 'selected_option_number': 1, 'ack_accepted': True, 'old_instance_gone_in_independent_snapshot': True},
            'policy_actually_used': 'native_first_displayed_v1',
            'registry_consumption_succeeded_live': False,
        },
    },
    'pilgrimage_intent.1050': {
        'analysis': {
            'source_analysis_completed': True,
            'migration_review_status': 'source_reviewed_no_occurrence_contract',
            'exact_build': '1.20.0.4',
            'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0036-intent-1050.source-only.json',
            'source_document_sha256': '2cd62c3ed73e1a8ab05cd1da8f38591dcd931239fa84f09181d710eeaca5693f',
            'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0036-events-occurrence.json',
            'title': 'Brevity of life',
            'source_pins': [{'game_relative_path': 'events/activities/pilgrimage_activity/pilgrimage_intent_events.txt', 'bytes': 57928, 'sha256': '3ddbde37f029845aa265aae749fe131bed571f02a5c4faac5d0074a615b39878', 'relevant_lines': [[1307, 1512]]}, {'game_relative_path': 'common/scripted_effects/00_pilgrimage_effects.txt', 'bytes': 40713, 'sha256': '4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80', 'relevant_lines': [[1225, 1239]]}, {'game_relative_path': 'common/script_values/00_basic_values.txt', 'bytes': 50566, 'sha256': 'c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef', 'relevant_lines': [[475, 475], [1132, 1132], [1165, 1165], [1539, 1539]]}, {'game_relative_path': 'common/modifiers/00_activity_pilgrimage_modifiers.txt', 'bytes': 8263, 'sha256': 'b4b087debf7975b02fdc30d3244a04aca634e3e26b2fafa4c42057e71a1c1580', 'relevant_lines': [[237, 246]]}, {'game_relative_path': 'common/script_values/00_stress_values.txt', 'bytes': 3852, 'sha256': '821a0b77244fc5ee2d87d339cb24dbef00787b83d44ec2df9215fc1a93aec2d4', 'relevant_lines': [[6, 14], [25, 35]]}, {'game_relative_path': 'common/script_values/00_lifestyle_values.txt', 'bytes': 22192, 'sha256': '4ddec87bf5c6aeefa2d5f48e42a421408e96b4c85f129727ed6db8fda8bbecc0', 'relevant_lines': [[889, 891]]}, {'game_relative_path': 'common/scripted_effects/00_travel_effects.txt', 'bytes': 1867, 'sha256': '47a4b46a479a2215ffeda4b6d7b8d9226928f6ec0dc70c289b4e0e2fe2b5ec0e', 'relevant_lines': [[9, 31]]}, {'game_relative_path': 'localization/simp_chinese/event_localization/activities/pilgrimage_intent_events_l_simp_chinese.yml', 'bytes': 18043, 'sha256': '7f2a61394920a1c0675185905e4bb8b3ce431e9b24122267c2e7e5d2663a5b1a', 'relevant_lines': [[88, 96]]}],
            'source_options': [{'source_key': 'pilgrimage_intent.1050.a', 'historical_native_index': 0, 'historical_label': '我会充分利用我的时间。', 'effects': ['Pious/Hajj progress helper; delay10d. Learning vs12 duel:base60/40, adjusted +/-0.5 compare weights, not flat60%. Success stress-20,25yr monthly lifestyle XP+20%,piety+50; Mystic XP3..5 only if already held. Failure stress+40. Impatient/craven/ambitious minor stress impacts.'], 'visibility': 'Shown R0036', 'historical_R31_selected': False}, {'source_key': 'pilgrimage_intent.1050.b', 'historical_native_index': None, 'historical_label': '我还有大量丰富的生活！', 'effects': ['Age>=50 OR health<=1. Delay10d; learning vs12 adjusted base50/50 duel. Success stress-10,15yr health+0.5/stress_gain+20%;failure stress+20. Conditional impatient/content/depressed/infirm stress impacts.'], 'visibility': 'Not shown', 'historical_R31_selected': False}, {'source_key': 'pilgrimage_intent.1050.c', 'historical_native_index': 2, 'historical_label': '这些想法让我心痛。', 'effects': ['Zealous/patient minor stress impacts; no direct delay, wallet, trait or XP.'], 'visibility': 'Shown R0036', 'historical_R31_selected': False}],
            'agent_reference': 'R0036 instance9; source-bound options, no occurrence recommendation contract R0036 outer pending tags retained unchanged; batch stopped at3101, no choice/noSave. No registry consumption credited.',
            'current_native_legality': None,
            'action_ready': False,
            'ordinary_auto_consumes': False,
            'full_occurrence_contract_registered': False,
            'selection_policy_changed': False,
            'historical_index_is_current_selection_permission': False,
            'historical_evidence_is_current_state': False,
        },
        'observations': {
            'machine_id': '4-8e1c2f1861',
            'observed_at_utc': '2026-10-22T20:24:19.065575+00:00',
            'run_id': '4-8e1c2f1861--faith-engine--R0036',
            'actual': {'instance_id': 9, 'actor_character_id': 15893, 'date_raw': 51399408, 'selected_native_option_index': 0, 'selected_option_number': 1, 'ack_accepted': True, 'old_instance_gone_in_independent_snapshot': True},
            'policy_actually_used': 'native_first_displayed_v1',
            'registry_consumption_succeeded_live': False,
        },
    },
}
PILGRIMAGE_TRAVEL_SOURCE_ONLY_12004.update(_R0036_SOURCE_ONLY)


_R0037_SOURCE_ONLY: dict[str, SourceOnlyRecord] = {'travel_danger_events.4010': {'analysis': {'source_analysis_completed': True,
                                            'migration_review_status': 'source_reviewed_no_occurrence_contract',
                                            'exact_build': '1.20.0.4',
                                            'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0037-travel-danger-4010.source-analysis.json',
                                            'source_document_sha256': 'c6395188eedce6d43661fe31c354986989e935d927b02f15235a268e67984872',
                                            'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0037-events-occurrence.json',
                                            'title': '$travel_danger_prefix$旅途之苦',
                                            'source_pins': [{'game_relative_path': 'events/travel_events/travel_danger_events_filippa.txt',
                                                             'bytes': 27472,
                                                             'sha256': '64d2af2349ab6d7a5a8254e83ec41d068b47ea8a27637bda4321a5237411f95c',
                                                             'relevant_lines': [[407, 1113]]},
                                                            {'game_relative_path': 'localization/simp_chinese/event_localization/travel_events/travel_danger_events_filippa_l_simp_chinese.yml',
                                                             'bytes': 6133,
                                                             'sha256': '2737c88b1d6ae24b648f302cd55fcfdf3596da7fb9bf3c14ac5284730e69b36b',
                                                             'relevant_lines': [[23, 48]]},
                                                            {'game_relative_path': 'common/script_values/00_basic_values.txt',
                                                             'bytes': 50566,
                                                             'sha256': 'c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef',
                                                             'relevant_lines': [[476, 476]]},
                                                            {'game_relative_path': 'common/on_action/travel_on_actions.txt',
                                                             'bytes': 71526,
                                                             'sha256': 'cd40f30a9280ea9ba656b59005201550f3991afd646fd686d7474657b1b1ff70',
                                                             'relevant_lines': [[698, 698]]},
                                                            {'game_relative_path': 'common/scripted_effects/20_health_effects.txt',
                                                             'bytes': 107548,
                                                             'sha256': 'abefa738c913c660a52fa747bcc92fca2f57d77a0f47d903bedc2882f3d5a9db',
                                                             'relevant_lines': [[126, 171]]},
                                                            {'game_relative_path': 'common/scripted_effects/00_travel_effects.txt',
                                                             'bytes': 1867,
                                                             'sha256': '47a4b46a479a2215ffeda4b6d7b8d9226928f6ec0dc70c289b4e0e2fe2b5ec0e',
                                                             'relevant_lines': [[9, 31]]},
                                                            {'game_relative_path': 'common/script_values/00_stress_values.txt',
                                                             'bytes': 3852,
                                                             'sha256': '821a0b77244fc5ee2d87d339cb24dbef00787b83d44ec2df9215fc1a93aec2d4',
                                                             'relevant_lines': [[25, 35]]}],
                                            'source_options': [{'source_key': 'travel_danger_events.4010.a',
                                                                'historical_native_index': 0,
                                                                'historical_label': '我们应该让他休息直到完全康复。',
                                                                'effects': ['Request current travel-plan delay21days; '
                                                                            'remove ill from saved ill_character.',
                                                                            'Other entourage except root/ill_character '
                                                                            'receive opinion input+5 toward root; '
                                                                            'despite custom tooltip '
                                                                            'every_patient_entourage_tt, the actual '
                                                                            'limit has no patient-trait check.',
                                                                            'Ill character opinion input+10 toward '
                                                                            'root for rival/nemesis, else+20.',
                                                                            'Player stress/fulfillment inputs: '
                                                                            'impatient medium gain40; if '
                                                                            'bad-relationship helper matches, also '
                                                                            'vengeful medium gain40 and paranoid major '
                                                                            'gain80. Character/system processing and '
                                                                            'final actual stress are separate.'],
                                                                'visibility': 'Shown rendered0/native0; chosen R0037. '
                                                                              'Sea uses a_sea text with same effects.',
                                                                'historical_R31_selected': False},
                                                               {'source_key': 'travel_danger_events.4010.b',
                                                                'historical_native_index': None,
                                                                'historical_label': '我想我知道该怎么治。',
                                                                'effects': ['Guard root whole_of_body OR '
                                                                            'lifestyle_herbalist OR is_witch_trigger '
                                                                            'OR lifestyle_physician OR '
                                                                            'learning>high_skill_rating(15).',
                                                                            'Learning duel against15: source base '
                                                                            'weights75/25 and compare_modifier '
                                                                            'multipliers+3.5/-3.5 on duel_value, '
                                                                            'failure min5; these are adjusted weights, '
                                                                            'not fixed75% chance.',
                                                                            'Success removes NPC ill, gives root '
                                                                            'physicianXP10 only if physician already '
                                                                            'held and XP<100, and invokes '
                                                                            'improve_relationship_effect(TARGET=root,REASON=friend_cared_for_health) '
                                                                            'on NPC.',
                                                                            'Success root stress/fulfillment base-15, '
                                                                            'compassionate-15, arrogant-15; '
                                                                            'bad-relationship branch additionally '
                                                                            'vengeful+40/paranoid+80. Failure requests '
                                                                            'NPC pneumonic through '
                                                                            'contract_disease_effect(TREATMENT_EVENT=no), '
                                                                            'NPC opinion -30 for rival/nemesis '
                                                                            'else-15; root '
                                                                            'base+20/compassionate+20/arrogant+20, '
                                                                            'with vengeful-15 in bad-relationship '
                                                                            'branch.'],
                                                                'visibility': 'Not shown in R0037; source-localized '
                                                                              'label only, no actual native index '
                                                                              'claimed.',
                                                                'historical_R31_selected': False},
                                                               {'source_key': 'travel_danger_events.4010.c',
                                                                'historical_native_index': None,
                                                                'historical_label': '[medicine_person.GetTitledFirstNameNoTooltip]，你能治好[ill_character.GetHerHim]吗？',
                                                                'effects': ['Guard saved medicine_person exists. '
                                                                            'Court-physician branch removes NPC ill, '
                                                                            'grants NPC opinion input+10 for '
                                                                            'rival/nemesis else+20, and physician XP10 '
                                                                            'to already-held court physician '
                                                                            'below100XP.',
                                                                            'Without court physician: saved '
                                                                            'medical_character makes Learning duel '
                                                                            'against15, source weights50/50 adjusted '
                                                                            'by+3.5/-3.5 duel_value, failure min5. '
                                                                            'Success removes NPC ill and gives '
                                                                            'existing physicianXP10 below100; failure '
                                                                            'requests NPC pneumonic/no treatment '
                                                                            'event. No guaranteed cure from this '
                                                                            'non-court-physician branch.',
                                                                            'Root arrogant stress/fulfillment input+40 '
                                                                            'if root satisfies any self-treatment '
                                                                            'qualification listed in B.'],
                                                                'visibility': 'Not shown; no medicine_person saved in '
                                                                              'this occurrence. Source text is a '
                                                                              'template.',
                                                                'historical_R31_selected': False},
                                                               {'source_key': 'travel_danger_events.4010.d',
                                                                'historical_native_index': None,
                                                                'historical_label': '正好，我有样东西……',
                                                                'effects': ['Human-player-only and NPC has '
                                                                            'potential-rival/rival/nemesis relation to '
                                                                            'root. Duel uses learning+intrigue '
                                                                            'targeting ill_character, source '
                                                                            'weights50/50 adjusted+3.5/-3.5 '
                                                                            'duel_value, failure min5.',
                                                                            'Success kills NPC with death_poison, '
                                                                            'killer=root. Root stress/fulfillment '
                                                                            'inputs base-30, paranoid-65, craven+40, '
                                                                            'compassionate+100, just+40, honest+40.',
                                                                            'Failure adds and reveals '
                                                                            'secret_murder_attempt targeting NPC; '
                                                                            'guarded potential-rival->rival or '
                                                                            'rival->nemesis escalation, with NPC '
                                                                            'opinion input-30. Root '
                                                                            'paranoid+80,craven+40,compassionate+80,just+40,honest+40.'],
                                                                'visibility': 'Not shown in R0037; historical index '
                                                                              'remains null.',
                                                                'historical_R31_selected': False},
                                                               {'source_key': 'travel_danger_events.4010.e',
                                                                'historical_native_index': 4,
                                                                'historical_label': '这只是轻微的咳嗽。',
                                                                'effects': ['Unconditional source option. Random '
                                                                            'weights75:25: request NPC pneumonic/no '
                                                                            'treatment event OR no disease-change '
                                                                            'effect; both branches NPC opinion '
                                                                            'input-15 toward root. No ill removal in '
                                                                            'the no-change branch.',
                                                                            'Root stress/fulfillment inputs '
                                                                            'compassionate+40, impatient-15, '
                                                                            'sadistic-30. No option-level travel delay '
                                                                            'declared.'],
                                                                'visibility': 'Shown rendered1/native4; not selected.',
                                                                'historical_R31_selected': False}],
                                            'agent_reference': 'R0037 instance7; native0 submitted once; ACK and '
                                                               'independent disappearance verified. Source-only '
                                                               'knowledge; registry was not registered live. R0037 is '
                                                               'now normally closed; no current action/trait-award '
                                                               'permission follows.',
                                            'current_native_legality': None,
                                            'action_ready': False,
                                            'ordinary_auto_consumes': False,
                                            'full_occurrence_contract_registered': False,
                                            'selection_policy_changed': False,
                                            'historical_index_is_current_selection_permission': False,
                                            'historical_evidence_is_current_state': False},
                               'observations': {'machine_id': '4-8e1c2f1861',
                                                'observed_at_utc': '2026-10-23T00:01:26.771852+00:00',
                                                'run_id': '4-8e1c2f1861--faith-engine--R0037',
                                                'actual': {'event_instance_id': 7,
                                                           'event_definition_key': 'travel_danger_events.4010',
                                                           'input_observed_at_utc': '2026-10-23T00:01:20.893627+00:00',
                                                           'snapshot_revision': 105,
                                                           'date_raw': 51395760,
                                                           'actor_character_id': 15893,
                                                           'sick_character_id': 19350,
                                                           'ill_character_id': 19350,
                                                           'generic_saved_scopes_not_invalid': ['travel_plan',
                                                                                                'disease_type',
                                                                                                'destination'],
                                                           'medicine_person_saved': False,
                                                           'displayed_options': [{'rendered_index': 0,
                                                                                  'native_option_index': 0,
                                                                                  'enabled': True,
                                                                                  'label': '我们应该让他休息直到完全康复。'},
                                                                                 {'rendered_index': 1,
                                                                                  'native_option_index': 4,
                                                                                  'enabled': True,
                                                                                  'label': '这只是轻微的咳嗽。'}],
                                                           'selected_option_number': 1,
                                                           'selected_native_option_index': 0,
                                                           'submission_attempted': True,
                                                           'ack_accepted': True,
                                                           'old_instance_gone_in_independent_snapshot': True,
                                                           'post_actor_character_id': 15893,
                                                           'post_active_event': None,
                                                           'played_character_stress_points_before': 20,
                                                           'played_character_stress_points_after': 20,
                                                           'wallets_raw_before_and_after_equal': {'gold': 121786805,
                                                                                                  'prestige': 11561059,
                                                                                                  'piety': 227694250,
                                                                                                  'scale': 100000},
                                                           'live_registry_status': 'not_registered',
                                                           'live_registry_reason': 'event_definition_key_not_registered',
                                                           'legacy_registry_analysis_available_bool_not_evidence': True,
                                                           'evidence': [{'path': 'C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261023-a02/live/4-8e1c2f1861--faith-engine--R0037/case-output/faith-e02-journey-001-event-7-offline-analysis-input.json',
                                                                         'bytes': 72308,
                                                                         'sha256': '06ef92061a1b29b366ccc90c0664d23f48a269405d3a794cc8f4c46c3df9c300'},
                                                                        {'path': 'C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261023-a02/live/4-8e1c2f1861--faith-engine--R0037/case-output/faith-e02-journey-001-event-7-selection-observed.json',
                                                                         'bytes': 36088,
                                                                         'sha256': '00995bb8521df16cd21fae6a407115e1ab01369b9a7cd6e849e990d3ef0cf3dd'}]},
                                                'policy_actually_used': 'native_first_displayed_v1',
                                                'registry_consumption_succeeded_live': False}},
 'pilgrimage.3101': {'analysis': {'source_analysis_completed': True,
                                  'migration_review_status': 'source_reviewed_no_occurrence_contract',
                                  'exact_build': '1.20.0.4',
                                  'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0037-pilgrimage-3101.source-analysis.json',
                                  'source_document_sha256': '53e3539d8191ea3687748a1bf9dcd4bf37db2589c2a7f6b8a5a742599be76134',
                                  'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0037-events-occurrence.json',
                                  'title': '受戒',
                                  'source_pins': [{'game_relative_path': 'events/activities/pilgrimage_activity/pilgrimage_events.txt',
                                                   'bytes': 358138,
                                                   'sha256': '900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06',
                                                   'relevant_lines': [[8908, 9010]]},
                                                  {'game_relative_path': 'localization/simp_chinese/event_localization/activities/pilgrimage_events_l_simp_chinese.yml',
                                                   'bytes': 136481,
                                                   'sha256': 'cecb7052ac6672f1fd99a0008a8e7d6ccca474069a17e8a9902c55571cd272b3',
                                                   'relevant_lines': [[627, 630]]},
                                                  {'game_relative_path': 'common/script_values/00_basic_values.txt',
                                                   'bytes': 50566,
                                                   'sha256': 'c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef',
                                                   'relevant_lines': [[1131, 1133], [1147, 1150], [1165, 1165]]},
                                                  {'game_relative_path': 'common/script_values/00_stress_values.txt',
                                                   'bytes': 3852,
                                                   'sha256': '821a0b77244fc5ee2d87d339cb24dbef00787b83d44ec2df9215fc1a93aec2d4',
                                                   'relevant_lines': [[5, 16]]},
                                                  {'game_relative_path': 'common/scripted_effects/00_pilgrimage_effects.txt',
                                                   'bytes': 40713,
                                                   'sha256': '4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80',
                                                   'relevant_lines': [[1224, 1250]]},
                                                  {'game_relative_path': 'common/scripted_effects/00_activity_effects.txt',
                                                   'bytes': 116295,
                                                   'sha256': 'd5c594f8746b923d34b13a67db881821e12f08ce1ab4e6e3f83933419c9e2d38',
                                                   'relevant_lines': [[4357, 4365]]},
                                                  {'game_relative_path': 'common/activities/activity_types/pilgrimage.txt',
                                                   'bytes': 111931,
                                                   'sha256': '24153043485b035cb0477de7306649027cb68c039e4a9d903776eddd870d8b9f',
                                                   'relevant_lines': [[2474, 2485]]}],
                                  'source_options': [{'source_key': 'pilgrimage.3101.a',
                                                      'historical_native_index': 0,
                                                      'historical_label': '我会全心全意、至诚至敬地完成受戒仪式。',
                                                      'effects': ['Invoke pious_type_option_effect: Pious/Hajj '
                                                                  'activity +10 activity_special_type_progression only '
                                                                  'if that variable exists. This is an activity score '
                                                                  'variable, not elapsed travel days.',
                                                                  'Direct piety input minor_piety_gain=50.',
                                                                  'Stress/fulfillment inputs use non-impact constants: '
                                                                  'base+40; zealous-20; temperate/humble/chaste/calm '
                                                                  'each-10; '
                                                                  'lustful/arrogant/wrathful/sadistic/vengeful/arbitrary '
                                                                  'each+40; '
                                                                  'hashishiyah/drunkard/rakish/gluttonous/impatient/deceitful/cynical '
                                                                  'each+20. These conditional source inputs precede '
                                                                  'character/system processing.'],
                                                      'visibility': 'Shown rendered0/native0 and selected once in '
                                                                    'R0037 instance13.',
                                                      'historical_R31_selected': False},
                                                     {'source_key': 'pilgrimage.3101.b',
                                                      'historical_native_index': 1,
                                                      'historical_label': '呃……貌似没人会清楚我有没有掉链子吧。',
                                                      'effects': ['Invoke worldly_type_option_effect, which matches '
                                                                  'worldly only; Hajj does not match this helper.',
                                                                  'Direct piety input medium_piety_loss=-100.',
                                                                  'Stress/fulfillment inputs use non-impact constants: '
                                                                  'zealous+60; honest/just each+40; lustful/arrogant '
                                                                  'each-20; '
                                                                  'sadistic/vengeful/wrathful/gluttonous/impatient/deceitful/cynical '
                                                                  'each-10.'],
                                                      'visibility': 'Shown rendered1/native1; not selected.',
                                                      'historical_R31_selected': False}],
                                  'agent_reference': 'R0037 instance13; native0 submitted once after Root recording '
                                                     'checkpoint; ACK and independent disappearance verified. '
                                                     'Source-only knowledge; registry was not registered live. R0037 '
                                                     'is now normally closed; no current action/trait-award permission '
                                                     'follows.',
                                  'current_native_legality': None,
                                  'action_ready': False,
                                  'ordinary_auto_consumes': False,
                                  'full_occurrence_contract_registered': False,
                                  'selection_policy_changed': False,
                                  'historical_index_is_current_selection_permission': False,
                                  'historical_evidence_is_current_state': False},
                     'observations': {'machine_id': '4-8e1c2f1861',
                                      'observed_at_utc': '2026-10-23T00:34:43.020974+00:00',
                                      'run_id': '4-8e1c2f1861--faith-engine--R0037',
                                      'actual': {'event_instance_id': 13,
                                                 'event_definition_key': 'pilgrimage.3101',
                                                 'input_observed_at_utc': '2026-10-23T00:32:32.533530+00:00',
                                                 'snapshot_revision': 637,
                                                 'date_raw': 51401016,
                                                 'actor_character_id': 15893,
                                                 'host_character_id': 15893,
                                                 'generic_saved_scopes_not_invalid': ['activity', 'province'],
                                                 'displayed_options': [{'rendered_index': 0,
                                                                        'native_option_index': 0,
                                                                        'enabled': True,
                                                                        'label': '我会全心全意、至诚至敬地完成受戒仪式。'},
                                                                       {'rendered_index': 1,
                                                                        'native_option_index': 1,
                                                                        'enabled': True,
                                                                        'label': '呃……貌似没人会清楚我有没有掉链子吧。'}],
                                                 'selected_option_number': 1,
                                                 'selected_native_option_index': 0,
                                                 'submission_attempted': True,
                                                 'ack_accepted': True,
                                                 'old_instance_gone_in_independent_snapshot': True,
                                                 'post_actor_character_id': 15893,
                                                 'post_active_event': None,
                                                 'played_character_stress_points_before': 0,
                                                 'played_character_stress_points_after': 35,
                                                 'played_character_piety_raw_before': 249266750,
                                                 'played_character_piety_raw_after': 254266750,
                                                 'wallet_scale': 100000,
                                                 'gold_raw_before_and_after': 133441293,
                                                 'prestige_raw_before_and_after': 15434435,
                                                 'live_registry_status': 'not_registered',
                                                 'live_registry_reason': 'event_definition_key_not_registered',
                                                 'evidence': [{'path': 'C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261023-a02/live/4-8e1c2f1861--faith-engine--R0037/case-output/faith-e02-journey-001-event-13-offline-analysis-input.json',
                                                               'bytes': 71199,
                                                               'sha256': 'e02316d052fd6982b17fa9de88ce6e8548757a75a2487a139cb8761515dfc877'},
                                                              {'path': 'C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261023-a02/live/4-8e1c2f1861--faith-engine--R0037/case-output/faith-e02-journey-001-event-13-selection-observed.json',
                                                               'bytes': 78073,
                                                               'sha256': 'b777779bd028eb45f5e1de3ab7b822ca192a1e9448610559d9035a1f05b91f4a'}]},
                                      'policy_actually_used': 'native_first_displayed_v1',
                                      'registry_consumption_succeeded_live': False}}}
PILGRIMAGE_TRAVEL_SOURCE_ONLY_12004.update(_R0037_SOURCE_ONLY)

_R0039_SOURCE_ONLY: dict[str, SourceOnlyRecord] = {'pilgrimage.2008': {'analysis': {'source_analysis_completed': True,
                                  'migration_review_status': 'source_reviewed_no_occurrence_contract',
                                  'exact_build': '1.20.0.4',
                                  'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0039-pilgrimage-2008.source-analysis.json',
                                  'source_document_sha256': '7f2c6e043fe0e6d1ee4765c77bb008d3ae7dedf11ba94d10ea12e1e0c3ed3441',
                                  'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0039-events-occurrence.json',
                                  'title': '朝圣：染病',
                                  'source_pins': [{'game_relative_path': 'events/activities/pilgrimage_activity/pilgrimage_events.txt',
                                                   'bytes': 358138,
                                                   'sha256': '900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06',
                                                   'relevant_lines': [[3437, 3516]]},
                                                  {'game_relative_path': 'common/scripted_effects/20_health_effects.txt',
                                                   'bytes': 107548,
                                                   'sha256': 'abefa738c913c660a52fa747bcc92fca2f57d77a0f47d903bedc2882f3d5a9db',
                                                   'relevant_lines': [[127, 216], [302, 309], [719, 911]]},
                                                  {'game_relative_path': 'events/health_events.txt',
                                                   'bytes': 278987,
                                                   'sha256': '74073e049a416c744b36a2a996fa467610705e38d53c836b050f1ac6f66e1212',
                                                   'relevant_lines': [[972, 1270]]},
                                                  {'game_relative_path': 'common/on_action/travel_on_actions.txt',
                                                   'bytes': 71526,
                                                   'sha256': 'cd40f30a9280ea9ba656b59005201550f3991afd646fd686d7474657b1b1ff70',
                                                   'relevant_lines': [[732, 732]]},
                                                  {'game_relative_path': 'localization/simp_chinese/event_localization/activities/pilgrimage_events_l_simp_chinese.yml',
                                                   'bytes': 136481,
                                                   'sha256': 'cecb7052ac6672f1fd99a0008a8e7d6ccca474069a17e8a9902c55571cd272b3',
                                                   'relevant_lines': [[346, 351]]}],
                                  'source_options': [{'source_key': 'pilgrimage.2008.whole_of_body',
                                                      'historical_native_index': None,
                                                      'historical_label': '哦，这种轻微的咳嗽很快就会过去的。',
                                                      'effects': ['Visible only with whole_of_body. Hidden '
                                                                  'recover_from_disease_effect(DISEASE=ill); '
                                                                  'displayed remove_trait=ill is tooltip '
                                                                  'only.',
                                                                  'No direct option-level travel delay, '
                                                                  'wallet, pilgrimage score or reward-trait '
                                                                  'effect declared.'],
                                                      'visibility': 'Not shown in R0039 instance8; no '
                                                                    'current or historical native index '
                                                                    'inferred from source order.',
                                                      'historical_R31_selected': False},
                                                     {'source_key': 'pilgrimage.2008.court_physician',
                                                      'historical_native_index': None,
                                                      'historical_label': '[traveling_court_physician.GetTitledFirstNameNoTooltip|U]，给我调制点汤药。',
                                                      'effects': ['Visible only with saved '
                                                                  'traveling_court_physician. Hidden '
                                                                  'recover_from_disease_effect(DISEASE=ill); '
                                                                  'displayed remove_trait=ill is tooltip '
                                                                  'only.',
                                                                  'No direct option-level travel delay, '
                                                                  'wallet, pilgrimage score or reward-trait '
                                                                  'effect declared.'],
                                                      'visibility': 'Not shown and no '
                                                                    'traveling_court_physician scope saved '
                                                                    'in R0039 instance8.',
                                                      'historical_R31_selected': False},
                                                     {'source_key': 'pilgrimage.2008.a',
                                                      'historical_native_index': 2,
                                                      'historical_label': '如果这是真主的旨意。',
                                                      'effects': ['Unconditional source option. '
                                                                  'custom_tooltip warns of continuing while '
                                                                  'ill; trigger_event=health.1001 requests a '
                                                                  'separate event, not direct travel '
                                                                  'cancellation or healing.',
                                                                  'health.1001 has its own '
                                                                  'can_contract_disease_trigger(DISEASE=ill); '
                                                                  'its appearance is not guaranteed by this '
                                                                  'request or by ACK.',
                                                                  "Illness is processed in this event's "
                                                                  'immediate before selection, not awarded '
                                                                  'by option A. The immediate helper '
                                                                  'requests health.3100 after5days, subject '
                                                                  'to actual game dispatch; no follow-up '
                                                                  'appearance credited here.'],
                                                      'visibility': 'Only shown legal row in R0039 '
                                                                    'instance8: rendered0/native2, selected '
                                                                    'once; do not hardcode2 for a fresh '
                                                                    'window.',
                                                      'historical_R31_selected': False}],
                                  'agent_reference': 'R0039 instance8: player15893, sick_character15893. '
                                                     'Travel-plan and disease-flag scopes are available '
                                                     'generic scopes with unavailable payload identity, not '
                                                     'invalid scopes. Definition3437-3516: event-local10year '
                                                     'cooldown; on-land pilgrimage, '
                                                     'next_destination_progress>0.2, can_contract ill. '
                                                     'Immediate calls '
                                                     'contract_disease_effect(ill,TREATMENT_EVENT=yes), '
                                                     'saves traveling physician only if present. Source '
                                                     'helper saves sick_character/disease_type, adds ill, '
                                                     'schedules treatment/recovery. Runtime illness '
                                                     'membership and follow-up events were not independently '
                                                     'read. ACK and independent instance disappearance are '
                                                     'confirmed; no claim of healing, actual delay, Hajj '
                                                     'completion, Hajjaj reward or return. Source-only '
                                                     'knowledge; fresh scopes, shown/enabled order and '
                                                     'current legality remain mandatory. Existing policy is '
                                                     'unchanged.',
                                  'current_native_legality': None,
                                  'action_ready': False,
                                  'ordinary_auto_consumes': False,
                                  'full_occurrence_contract_registered': False,
                                  'selection_policy_changed': False,
                                  'historical_index_is_current_selection_permission': False,
                                  'historical_evidence_is_current_state': False},
                     'observations': {'machine_id': '4-8e1c2f1861',
                                      'observed_at_utc': '2026-10-23T04:52:53.096137+00:00',
                                      'run_id': '4-8e1c2f1861--faith-engine--R0039',
                                      'actual': {'event_instance_id': 8,
                                                 'event_definition_key': 'pilgrimage.2008',
                                                 'input_observed_at_utc': '2026-10-23T04:52:44.384284+00:00',
                                                 'selection_observed_at_utc': '2026-10-23T04:52:53.096137+00:00',
                                                 'snapshot_revision': 337,
                                                 'date_raw': 51397512,
                                                 'actor_character_id': 15893,
                                                 'displayed_options': [{'rendered_index': 0,
                                                                        'native_option_index': 2,
                                                                        'shown': True,
                                                                        'enabled': True,
                                                                        'fallback': False,
                                                                        'cancel': False,
                                                                        'resolved_name': '如果这是真主的旨意。'}],
                                                 'selected_native_option_index': 2,
                                                 'selected_option_number': 3,
                                                 'intent_submission_attempted': False,
                                                 'submission_attempted': True,
                                                 'ack_accepted': True,
                                                 'old_instance_gone_in_independent_snapshot': True,
                                                 'post_actor_character_id': 15893,
                                                 'post_date_raw': 51397512,
                                                 'post_snapshot_revision': 338,
                                                 'post_active_event': None,
                                                 'played_character_stress_points_before': 0,
                                                 'played_character_stress_points_after': 0,
                                                 'wallets_before': {'played_character_gold': {'raw': 125995729,
                                                                                              'scale': 100000},
                                                                    'played_character_prestige': {'raw': 13008025,
                                                                                                  'scale': 100000},
                                                                    'played_character_piety': {'raw': 225777000,
                                                                                               'scale': 100000}},
                                                 'wallets_after': {'played_character_gold': {'raw': 125995729,
                                                                                             'scale': 100000},
                                                                   'played_character_prestige': {'raw': 13008025,
                                                                                                 'scale': 100000},
                                                                   'played_character_piety': {'raw': 225777000,
                                                                                              'scale': 100000}},
                                                 'live_registry_status': 'not_registered',
                                                 'live_registry_reason': 'event_definition_key_not_registered',
                                                 'legacy_registry_analysis_available_bool': True,
                                                 'legacy_analysis_bool_is_not_source_completion_evidence': True,
                                                 'policy_actually_used': 'native_first_displayed_v1',
                                                 'evidence': [{'path': 'C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261023-a02/live/4-8e1c2f1861--faith-engine--R0039/case-output/faith-e02-journey-001-event-8-offline-analysis-input.json',
                                                               'bytes': 73706,
                                                               'sha256': '87fa42ec7df65511d4b3931fe782a1d5a5eebcd4400a0c997644d4a67e966220'},
                                                              {'path': 'C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261023-a02/live/4-8e1c2f1861--faith-engine--R0039/case-output/faith-e02-journey-001-event-8-selection-intent.json',
                                                               'bytes': 76797,
                                                               'sha256': 'c33e00b0878ef46d922c504fdb5229eb8ce5dc578707a806309d10ee4c4558c0'},
                                                              {'path': 'C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261023-a02/live/4-8e1c2f1861--faith-engine--R0039/case-output/faith-e02-journey-001-event-8-selection-observed.json',
                                                               'bytes': 37905,
                                                               'sha256': '072a63863282dc3405a0451ad33cd9addf6f223fba9dd4c8ed14ee9ccc96260b'},
                                                              {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0039\\case-output\\faith-e02-journey-001-0030-event-select-once.actual-results.json',
                                                               'bytes': 42082,
                                                               'sha256': '48b7181ba24ec8991f4c3b678f7a554ed6bbfd0ddfed9f0faf4f7ab556387ee0'}],
                                                 'actual_effect_boundary': 'ACK and independent old-window '
                                                                           'disappearance only. No '
                                                                           'unmeasured disease, NPC health, '
                                                                           'opinion, known-Rite, net '
                                                                           'travel-delay or reward result '
                                                                           'credited.'},
                                      'policy_actually_used': 'native_first_displayed_v1',
                                      'registry_consumption_succeeded_live': False}}}
PILGRIMAGE_TRAVEL_SOURCE_ONLY_12004.update(_R0039_SOURCE_ONLY)

_R0039_R0041_SOURCE_ONLY: dict[str, SourceOnlyRecord] = {'pilgrimage.2003': {'analysis': {'source_analysis_completed': True,
                                  'migration_review_status': 'source_reviewed_no_occurrence_contract',
                                  'exact_build': '1.20.0.4',
                                  'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0039-pilgrimage-2003.source-analysis.json',
                                  'source_document_sha256': 'd6bfaae744e81599d1e90455607af0a4bc3b28004abcb87c7669bb3368f80867',
                                  'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0039-final-event-closure.json',
                                  'title': '朝圣：安全问题',
                                  'source_pins': [{'game_relative_path': 'events/activities/pilgrimage_activity/pilgrimage_events.txt',
                                                   'bytes': 358138,
                                                   'sha256': '900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06',
                                                   'relevant_lines': [[2581, 2821]]},
                                                  {'game_relative_path': 'localization/simp_chinese/event_localization/activities/pilgrimage_events_l_simp_chinese.yml',
                                                   'bytes': 136481,
                                                   'sha256': 'cecb7052ac6672f1fd99a0008a8e7d6ccca474069a17e8a9902c55571cd272b3',
                                                   'relevant_lines': [[314, 318]]},
                                                  {'game_relative_path': 'common/script_values/01_dynamic_values.txt',
                                                   'bytes': 48201,
                                                   'sha256': '023165e7d27d106a34f34d7726d938efa8d5dce25650ea3256e0b5ea3f73cc2a',
                                                   'relevant_lines': [[53, 71]]},
                                                  {'game_relative_path': 'common/scripted_effects/00_pilgrimage_effects.txt',
                                                   'bytes': 40713,
                                                   'sha256': '4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80',
                                                   'relevant_lines': [[488, 513], [1225, 1238]]},
                                                  {'game_relative_path': 'common/scripted_effects/00_activity_effects.txt',
                                                   'bytes': 116295,
                                                   'sha256': 'd5c594f8746b923d34b13a67db881821e12f08ce1ab4e6e3f83933419c9e2d38',
                                                   'relevant_lines': [[4357, 4365], [4549, 4590]]},
                                                  {'game_relative_path': 'common/modifiers/00_activity_pilgrimage_modifiers.txt',
                                                   'bytes': 8263,
                                                   'sha256': 'b4b087debf7975b02fdc30d3244a04aca634e3e26b2fafa4c42057e71a1c1580',
                                                   'relevant_lines': [[43, 48], [196, 199]]},
                                                  {'game_relative_path': 'common/on_action/activities/pilgrimage_on_actions.txt',
                                                   'bytes': 11904,
                                                   'sha256': 'fdf71f074882f94eb3df497a1ddb2cb9a95fb13e973aebf25d4c3569729ee354',
                                                   'relevant_lines': [[44, 44]]}],
                                  'source_options': [{'source_key': 'pilgrimage.2003.a',
                                                      'historical_native_index': 0,
                                                      'historical_label': '为了我的朝圣之旅，我应该雇佣他们中的一些人。',
                                                      'effects': ['Visible only when the current travel plan '
                                                                  'does not already have '
                                                                  'hire_experienced_mercenaries_option.',
                                                                  'Conditional pious_type_option_effect when '
                                                                  'the current Rite has '
                                                                  'tenet_armed_pilgrimages, otherwise '
                                                                  'tenet_struggle_submission; this helper '
                                                                  'matches Pious/Hajj and changes an '
                                                                  'activity score, not elapsed travel days.',
                                                                  'Add pilgrim_protection_modifier to the '
                                                                  'current travel plan: travel_safety+10. '
                                                                  'Remove short-term gold using dynamic '
                                                                  'minor_gold_value; its income '
                                                                  'formula/clamps/round-to5 are not a '
                                                                  'universal75gold cost.',
                                                                  'Humble and greedy each supply '
                                                                  'medium_stress_impact_gain to '
                                                                  'stress_and_fulfillment_impact. No direct '
                                                                  'option-level travel delay or '
                                                                  'Pilgrim/Hajjaj trait grant declared.'],
                                                      'visibility': 'R0039 instance9 rendered0/native0, '
                                                                    'shown/enabled and selected once. Fresh '
                                                                    'window order/legality is still '
                                                                    'required.',
                                                      'historical_R31_selected': False},
                                                     {'source_key': 'pilgrimage.2003.b',
                                                      'historical_native_index': 1,
                                                      'historical_label': '萨阿德丁似乎是一个很棒的家伙。',
                                                      'effects': ['Conditional pious_type_option_effect only '
                                                                  'for current Rite tenet_warmonger.',
                                                                  'Remove short-term gold using dynamic '
                                                                  'minor_gold_value; '
                                                                  'recruit_to_entourage_court_and_activity_effect '
                                                                  'targets saved2002_local_warrior. The '
                                                                  'helper guards court/companion/activity '
                                                                  'additions; this option was not selected '
                                                                  'and actual recruitment is unobserved.',
                                                                  'Humble and greedy each supply '
                                                                  'medium_stress_impact_gain. This is the '
                                                                  'candidate-warrior recruitment option, '
                                                                  "distinct from A's travel-plan safety "
                                                                  'modifier.'],
                                                      'visibility': 'R0039 instance9 rendered1/native1, '
                                                                    'shown/enabled, not selected. Name is '
                                                                    'occurrence-specific.',
                                                      'historical_R31_selected': False},
                                                     {'source_key': 'pilgrimage.2003.c',
                                                      'historical_native_index': 2,
                                                      'historical_label': '不。我坚定地信仰着安拉。',
                                                      'effects': ['Invoke pious_type_option_effect and '
                                                                  'give_pilgrim_xp_effect. The latter '
                                                                  'gives+5PilgrimXP only with owned pilgrim '
                                                                  'below100XP; otherwise it branches to '
                                                                  'medium Learning lifestyleXP, zealous '
                                                                  'medium stress loss, or minor stress loss. '
                                                                  'It does not add pilgrim or convert '
                                                                  'hajjaj.',
                                                                  'Add pilgrimage_divine_protection_modifier '
                                                                  'for10years: '
                                                                  'monthly_piety_gain_mult+0.05,diplomacy_per_piety_level+1,intrigue_per_piety_level-1.',
                                                                  'If current Rite has '
                                                                  'tenet_inner_journey_humble_pilgrimage_bonus, '
                                                                  'add medium_piety_gain. Arrogant/craven '
                                                                  'stress inputs use '
                                                                  'minor/medium_stress_impact_gain. No '
                                                                  'purchase or direct travel delay in this '
                                                                  'option body.'],
                                                      'visibility': 'R0039 instance9 rendered2/native2, '
                                                                    'shown/enabled, not selected. Source '
                                                                    'effects are not credited as native '
                                                                    'results.',
                                                      'historical_R31_selected': False}],
                                  'agent_reference': 'R0039 instance9, actual day150.0, player15893, '
                                                     'saved2002_local_warrior19735. Three current '
                                                     'shown/enabled rows native0/1/2; first displayed '
                                                     'native0 selected once. ACK and independent old-window '
                                                     'disappearance confirmed at unchanged date51398520. '
                                                     'Gold raw127430533→119930533(scale100000), a same-date '
                                                     'decrease75; piety225971250 unchanged and stress0→0. '
                                                     'Actual travel_safety modifier, candidate recruitment, '
                                                     'score progression and unused C rewards were not '
                                                     'independently queried. Source-local2year event '
                                                     'cooldown is not the activity cooldown. Immediate '
                                                     'chooses an eligible local pool warrior or creates one; '
                                                     "this occurrence's creation branch is not established. "
                                                     'All indices/labels are historical evidence only. '
                                                     'Current shared registry before proposal has migration '
                                                     'metadata but no source_analysis_completed flag '
                                                     'for2003. No policy or action contract is added.',
                                  'current_native_legality': None,
                                  'action_ready': False,
                                  'ordinary_auto_consumes': False,
                                  'full_occurrence_contract_registered': False,
                                  'selection_policy_changed': False,
                                  'historical_index_is_current_selection_permission': False,
                                  'historical_evidence_is_current_state': False},
                     'observations': {'machine_id': '4-8e1c2f1861',
                                      'observed_at_utc': '2026-10-23T05:02:05.641495+00:00',
                                      'run_id': '4-8e1c2f1861--faith-engine--R0039',
                                      'actual': {'event_instance_id': 9,
                                                 'event_definition_key': 'pilgrimage.2003',
                                                 'selected_native_option_index': 0,
                                                 'selected_option_number': 1,
                                                 'submission_attempted': True,
                                                 'ack_accepted': True,
                                                 'old_instance_gone_in_independent_snapshot': True,
                                                 'date_raw': 51398520,
                                                 'game_day': 150,
                                                 'snapshot_revision': 466,
                                                 'actor_character_id': 15893,
                                                 'local_warrior_character_id': 19735,
                                                 'displayed_options': [{'rendered_index': 0,
                                                                        'native_option_index': 0,
                                                                        'shown': True,
                                                                        'enabled': True,
                                                                        'fallback': False,
                                                                        'cancel': False,
                                                                        'resolved_name': '为了我的朝圣之旅，我应该雇佣他们中的一些人。',
                                                                        'unavailable_reason': '',
                                                                        'effect_indicators': {'status': 'available',
                                                                                              'coverage': 'played-character-event-icon-indicators-1.20.0.4-v1',
                                                                                              'complete_effect_set': False,
                                                                                              'rows': []},
                                                                        'effect_preview': {'status': 'unavailable',
                                                                                           'reason': 'indicator_subset_has_no_completeness_signal'},
                                                                        'resource_deltas': {'status': 'unavailable'},
                                                                        'relationship_deltas': {'status': 'unavailable'}},
                                                                       {'rendered_index': 1,
                                                                        'native_option_index': 1,
                                                                        'shown': True,
                                                                        'enabled': True,
                                                                        'fallback': False,
                                                                        'cancel': False,
                                                                        'resolved_name': '萨阿德丁似乎是一个很棒的家伙。',
                                                                        'unavailable_reason': '',
                                                                        'effect_indicators': {'status': 'available',
                                                                                              'coverage': 'played-character-event-icon-indicators-1.20.0.4-v1',
                                                                                              'complete_effect_set': False,
                                                                                              'rows': []},
                                                                        'effect_preview': {'status': 'unavailable',
                                                                                           'reason': 'indicator_subset_has_no_completeness_signal'},
                                                                        'resource_deltas': {'status': 'unavailable'},
                                                                        'relationship_deltas': {'status': 'unavailable'}},
                                                                       {'rendered_index': 2,
                                                                        'native_option_index': 2,
                                                                        'shown': True,
                                                                        'enabled': True,
                                                                        'fallback': False,
                                                                        'cancel': False,
                                                                        'resolved_name': '不。我坚定地信仰着安拉。',
                                                                        'unavailable_reason': '',
                                                                        'effect_indicators': {'status': 'available',
                                                                                              'coverage': 'played-character-event-icon-indicators-1.20.0.4-v1',
                                                                                              'complete_effect_set': False,
                                                                                              'rows': [{'kind': 'stress',
                                                                                                        'direction': 'decrease',
                                                                                                        'magnitude': {'status': 'unavailable'},
                                                                                                        'affected_by_trait': False,
                                                                                                        'critical': False}]},
                                                                        'effect_preview': {'status': 'unavailable',
                                                                                           'reason': 'indicator_subset_has_no_completeness_signal'},
                                                                        'resource_deltas': {'status': 'unavailable'},
                                                                        'relationship_deltas': {'status': 'unavailable'}}],
                                                 'typed_scope_projection': {'schema': 'current-event-window-context-v1',
                                                                            'schema_version': 1,
                                                                            'status': 'available',
                                                                            'snapshot_revision': 466,
                                                                            'date_raw': 51398520,
                                                                            'current_event_instance_id': 9,
                                                                            'window_match_count': 1,
                                                                            'unavailable_reason': None,
                                                                            'event_definition_key': 'pilgrimage.2003',
                                                                            'calculated_event_id': 2742003,
                                                                            'runtime_stats_ordinal': 3591,
                                                                            'root_scope': {'status': 'available',
                                                                                           'raw_type_index': 4,
                                                                                           'type_key': 'character',
                                                                                           'subtype': 0,
                                                                                           'typed_identity': {'status': 'available',
                                                                                                              'kind': 'character',
                                                                                                              'character_id': 15893}},
                                                                            'saved_scopes': [{'name': 'travel_plan',
                                                                                              'name_identifier': 211,
                                                                                              'scope': {'status': 'available',
                                                                                                        'raw_type_index': 35,
                                                                                                        'type_key': 'travel_plan',
                                                                                                        'subtype': 0,
                                                                                                        'typed_identity': {'status': 'unavailable',
                                                                                                                           'reason': 'generic_scope_payload_identity_not_closed'}}},
                                                                                             {'name': '2002_local_warrior',
                                                                                              'name_identifier': 20219,
                                                                                              'scope': {'status': 'available',
                                                                                                        'raw_type_index': 4,
                                                                                                        'type_key': 'character',
                                                                                                        'subtype': 0,
                                                                                                        'typed_identity': {'status': 'available',
                                                                                                                           'kind': 'character',
                                                                                                                           'character_id': 19735}}}],
                                                                            'readiness': {'event_definition_identity_ready': True,
                                                                                          'root_scope_ready': True,
                                                                                          'saved_scopes_ready': True,
                                                                                          'option_presentation_ready': True,
                                                                                          'effect_indicators_ready': True,
                                                                                          'effect_preview_ready': False,
                                                                                          'semantic_decision_ready': False},
                                                                            'provenance': {'root': 'module+0x5C6A520->+0x10',
                                                                                           'idler_vtable_rva': '0x44BC418',
                                                                                           'manager_offset': '+0x28',
                                                                                           'backend_id': 'ck3-1.20.0.4-native-event-window-v1'}},
                                                 'post_actor_character_id': 15893,
                                                 'post_date_raw': 51398520,
                                                 'post_active_event': None,
                                                 'policy_actually_used': 'native_first_displayed_v1',
                                                 'live_registry_status': 'not_registered',
                                                 'wallet_scale': 100000,
                                                 'evidence': [{'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0039\\case-output\\faith-e02-journey-001-event-9-offline-analysis-input.json',
                                                               'bytes': 75401,
                                                               'sha256': '11b4680c68078c017c3c404e3b2a8230919817f0f093fee998febbac0912ed45'},
                                                              {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0039\\case-output\\faith-e02-journey-001-event-9-selection-intent.json',
                                                               'bytes': 80247,
                                                               'sha256': '8aead2ac1cff92fc5bde0487c7160fc51048ced19d48f018b1a13fb70ae57b26'},
                                                              {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0039\\case-output\\faith-e02-journey-001-event-9-selection-observed.json',
                                                               'bytes': 37998,
                                                               'sha256': '81b764d04b8f673b39bc54704e8352f2a6051b6ac1762a0f088b3413ba28952d'},
                                                              {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0039\\case-output\\faith-e02-journey-001-0039-event-select-once.actual-results.json',
                                                               'bytes': 42197,
                                                               'sha256': 'c43d639da0197a1f45e4fdcc2277fe7863936f3b0adaf08e5f2ced4bf5e3cbf2'}],
                                                 'gold_raw_before': 127430533,
                                                 'gold_raw_after': 119930533,
                                                 'piety_raw_before': 225971250,
                                                 'piety_raw_after': 225971250,
                                                 'stress_before': 0,
                                                 'stress_after': 0},
                                      'policy_actually_used': 'native_first_displayed_v1',
                                      'registry_consumption_succeeded_live': False}},
 'travel_events_oltner_2.1030': {'analysis': {'source_analysis_completed': True,
                                              'migration_review_status': 'source_reviewed_no_occurrence_contract',
                                              'exact_build': '1.20.0.4',
                                              'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0041-events-source-analysis-12004.json',
                                              'source_document_sha256': 'b35d2835d1526b55d0dede20d111efdcad832f7993b0da3eea9c17ec50b8c68c',
                                              'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0041-events-occurrence.json',
                                              'title': '满载的商队',
                                              'source_pins': [{'game_relative_path': 'events/travel_events/travel_events_oltner_2.txt',
                                                               'bytes': 144369,
                                                               'sha256': '6de5bfc12d2765da90541e98337529c4e974d8eec749943b40a30908e640b37b',
                                                               'relevant_lines': [[715, 982]]},
                                                              {'game_relative_path': 'common/scripted_effects/00_ep1_artifact_creation_effects.txt',
                                                               'bytes': 397942,
                                                               'sha256': '1b60d78e54e1ebff7601bd13e59b2251cff47d96f595a4431c666fa3ee11a831',
                                                               'relevant_lines': [[12325, 13497]]},
                                                              {'game_relative_path': 'common/scripted_effects/00_travel_effects.txt',
                                                               'bytes': 1867,
                                                               'sha256': '47a4b46a479a2215ffeda4b6d7b8d9226928f6ec0dc70c289b4e0e2fe2b5ec0e',
                                                               'relevant_lines': [[9, 31]]},
                                                              {'game_relative_path': 'common/modifiers/00_travel_modifiers_oltner.txt',
                                                               'bytes': 2657,
                                                               'sha256': 'bd5875b3a24e7ee15062a41cd5f2307176edf74215013b71a0adf1896956144e',
                                                               'relevant_lines': [[14, 17]]},
                                                              {'game_relative_path': 'common/script_values/01_dynamic_values.txt',
                                                               'bytes': 48201,
                                                               'sha256': '023165e7d27d106a34f34d7726d938efa8d5dce25650ea3256e0b5ea3f73cc2a',
                                                               'relevant_lines': [[53, 71]]},
                                                              {'game_relative_path': 'localization/simp_chinese/travel/oltner_travel_l_simp_chinese.yml',
                                                               'bytes': 42803,
                                                               'sha256': '49e7fe26506f1b03ef345a26539c9f4615c6a6582e16a8b43377ee3f5180c77f',
                                                               'relevant_lines': [[27, 32]]}],
                                              'source_options': [{'source_key': 'travel_events_oltner_2.1030.a',
                                                                  'historical_native_index': 0,
                                                                  'historical_label': '“你挑起我的兴趣了，让我们来交易吧。”',
                                                                  'effects': ['pay_short_term_gold to saved '
                                                                              'local_character using dynamic '
                                                                              'minor_gold_value; not a fixed '
                                                                              'universal price.',
                                                                              'Call generate_trinket_effect '
                                                                              'with '
                                                                              'receiver=root,giver=local_character,GRAB_ALL_TRINKETS=yes,HISTORY_TYPE=created; '
                                                                              'it runs a weighted random '
                                                                              'trinket generator, then event '
                                                                              'requests owner=root through '
                                                                              'new_trinket scope. No '
                                                                              'artifact identity, type, '
                                                                              'quality or ownership readback '
                                                                              'was made in this occurrence.',
                                                                              'Paranoid medium and impatient '
                                                                              'minor stress/fulfillment gain '
                                                                              'inputs. Actual same-date '
                                                                              'wallet decreases55 and stress '
                                                                              'stays0; source stress inputs '
                                                                              'are not final native stress '
                                                                              'deltas.'],
                                                                  'visibility': 'Shown/enabled in R0041; '
                                                                                'native index and label are '
                                                                                'historical evidence only. '
                                                                                'Fresh native shown order '
                                                                                'and legality are mandatory.',
                                                                  'historical_R31_selected': False},
                                                                 {'source_key': 'travel_events_oltner_2.1030.b',
                                                                  'historical_native_index': 1,
                                                                  'historical_label': '“用不着，但也许我们暂时可以一起旅行？”',
                                                                  'effects': ['Add '
                                                                              'traveling_with_camel_merchants_modifier '
                                                                              'to current travel plan '
                                                                              'for1month: travel_safety+10.',
                                                                              'Paranoid major and arrogant '
                                                                              'minor stress/fulfillment gain '
                                                                              'inputs. No direct purchase '
                                                                              'payment in this option body; '
                                                                              'this branch was not '
                                                                              'selected.'],
                                                                  'visibility': 'Shown/enabled in R0041; '
                                                                                'native index and label are '
                                                                                'historical evidence only. '
                                                                                'Fresh native shown order '
                                                                                'and legality are mandatory.',
                                                                  'historical_R31_selected': False},
                                                                 {'source_key': 'travel_events_oltner_2.1030.c',
                                                                  'historical_native_index': 2,
                                                                  'historical_label': '“给我看些独特的东西，而且得是库法的真正瑰宝。”',
                                                                  'effects': ['Pay dynamic major_gold_value '
                                                                              'to local_character; set '
                                                                              'generator quality/wealth '
                                                                              'scopes to70.',
                                                                              'Random list has six equal '
                                                                              'base weights10 for '
                                                                              'weapon,armor,regalia,crown,brooch,book '
                                                                              'creation helpers, then '
                                                                              'requests new artifact '
                                                                              'ownership=root. Generator '
                                                                              'input70 and famed tooltip do '
                                                                              'not establish an actual fixed '
                                                                              'quality/rank.',
                                                                              'Greedy/paranoid medium and '
                                                                              'impatient minor '
                                                                              'stress/fulfillment gain '
                                                                              'inputs. Branch not selected; '
                                                                              'no generated artifact '
                                                                              'credited.'],
                                                                  'visibility': 'Shown/enabled in R0041; '
                                                                                'native index and label are '
                                                                                'historical evidence only. '
                                                                                'Fresh native shown order '
                                                                                'and legality are mandatory.',
                                                                  'historical_R31_selected': False},
                                                                 {'source_key': 'travel_events_oltner_2.1030.d',
                                                                  'historical_native_index': 3,
                                                                  'historical_label': '“我们携带的行囊已经够多了……”',
                                                                  'effects': ['Decline trading. '
                                                                              'Generous/gregarious minor '
                                                                              'stress/fulfillment gains, '
                                                                              'paranoid medium loss; no '
                                                                              'direct purchase/generator '
                                                                              'body.'],
                                                                  'visibility': 'Shown/enabled in R0041; '
                                                                                'native index and label are '
                                                                                'historical evidence only. '
                                                                                'Fresh native shown order '
                                                                                'and legality are mandatory.',
                                                                  'historical_R31_selected': False}],
                                              'agent_reference': 'R0041 instance5/day28, '
                                                                 'actor15893/local_character41708. A/native0 '
                                                                 'selected once; ACK and old-window '
                                                                 'disappearance at unchanged date51395592. '
                                                                 'Gold raw121786805→116286805(scale100000), '
                                                                 'delta-55; prestige/piety/stress unchanged. '
                                                                 'saved new_trinket is root character15893 '
                                                                 'before selection, explicitly initialized '
                                                                 'for error suppression; do not infer an '
                                                                 'artifact ID or invalid scope from its '
                                                                 'name. Immediate '
                                                                 'mp_delay_travel_plan(DAYS=90) and after '
                                                                 'mp_resume_travel_plan both require '
                                                                 'has_multiple_players in the shared helper. '
                                                                 "Do not count them as this run's "
                                                                 'observed90day delays or travel advance. '
                                                                 'Event-local10year cooldown is not the '
                                                                 'pilgrimage cooldown; after only cleans up '
                                                                 'an AI-created local character.',
                                              'current_native_legality': None,
                                              'action_ready': False,
                                              'ordinary_auto_consumes': False,
                                              'full_occurrence_contract_registered': False,
                                              'selection_policy_changed': False,
                                              'historical_index_is_current_selection_permission': False,
                                              'historical_evidence_is_current_state': False},
                                 'observations': {'machine_id': '4-8e1c2f1861',
                                                  'observed_at_utc': '2026-10-23T07:21:26.555421+00:00',
                                                  'run_id': '4-8e1c2f1861--faith-engine--R0041',
                                                  'actual': {'event_instance_id': 5,
                                                             'event_definition_key': 'travel_events_oltner_2.1030',
                                                             'selected_native_option_index': 0,
                                                             'selected_option_number': 1,
                                                             'submission_attempted': True,
                                                             'ack_accepted': True,
                                                             'old_instance_gone_in_independent_snapshot': True,
                                                             'actor_character_id': 15893,
                                                             'date_raw': 51395592,
                                                             'game_day': 28,
                                                             'snapshot_revision': 82,
                                                             'post_actor_character_id': 15893,
                                                             'post_date_raw': 51395592,
                                                             'post_active_event': None,
                                                             'stress_before': 0,
                                                             'stress_after': 0,
                                                             'wallets_before': {'played_character_gold': {'raw': 121786805,
                                                                                                          'scale': 100000},
                                                                                'played_character_prestige': {'raw': 11561059,
                                                                                                              'scale': 100000},
                                                                                'played_character_piety': {'raw': 225194250,
                                                                                                           'scale': 100000}},
                                                             'wallets_after': {'played_character_gold': {'raw': 116286805,
                                                                                                         'scale': 100000},
                                                                               'played_character_prestige': {'raw': 11561059,
                                                                                                             'scale': 100000},
                                                                               'played_character_piety': {'raw': 225194250,
                                                                                                          'scale': 100000}},
                                                             'evidence': [{'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0041\\case-output\\faith-e02-journey-001-event-5-offline-analysis-input.json',
                                                                           'bytes': 73483,
                                                                           'sha256': '050cfecbc86f056c0854b255c14476c27f5fe1176ad724614dd63da3240481f5'},
                                                                          {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0041\\case-output\\faith-e02-journey-001-event-5-selection-intent.json',
                                                                           'bytes': 79124,
                                                                           'sha256': '7f8465a92da60c7db6d45da3f0289e85a70346d9088eba4d5cbd8177a8e323a5'},
                                                                          {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0041\\case-output\\faith-e02-journey-001-event-5-selection-observed.json',
                                                                           'bytes': 36083,
                                                                           'sha256': 'fdcc66d447d814bd0f1b47d40f969874631ebdb7acee6f506204a25492801e11'},
                                                                          {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0041\\case-output\\faith-e02-journey-001-0033-event-select-once.actual-results.json',
                                                                           'bytes': 40004,
                                                                           'sha256': '079e0fd97691a2b2a361002d693cebd3e78f3cadc2d0786ad664e61b5713bb3b'}],
                                                             'displayed_options': [{'rendered_index': 0,
                                                                                    'native_option_index': 0,
                                                                                    'shown': True,
                                                                                    'enabled': True,
                                                                                    'fallback': False,
                                                                                    'cancel': False,
                                                                                    'resolved_name': '“你挑起我的兴趣了，让我们来交易吧。”',
                                                                                    'unavailable_reason': '',
                                                                                    'effect_indicators': {'status': 'available',
                                                                                                          'coverage': 'played-character-event-icon-indicators-1.20.0.4-v1',
                                                                                                          'complete_effect_set': False,
                                                                                                          'rows': []},
                                                                                    'effect_preview': {'status': 'unavailable',
                                                                                                       'reason': 'indicator_subset_has_no_completeness_signal'},
                                                                                    'resource_deltas': {'status': 'unavailable'},
                                                                                    'relationship_deltas': {'status': 'unavailable'}},
                                                                                   {'rendered_index': 1,
                                                                                    'native_option_index': 1,
                                                                                    'shown': True,
                                                                                    'enabled': True,
                                                                                    'fallback': False,
                                                                                    'cancel': False,
                                                                                    'resolved_name': '“用不着，但也许我们暂时可以一起旅行？”',
                                                                                    'unavailable_reason': '',
                                                                                    'effect_indicators': {'status': 'available',
                                                                                                          'coverage': 'played-character-event-icon-indicators-1.20.0.4-v1',
                                                                                                          'complete_effect_set': False,
                                                                                                          'rows': []},
                                                                                    'effect_preview': {'status': 'unavailable',
                                                                                                       'reason': 'indicator_subset_has_no_completeness_signal'},
                                                                                    'resource_deltas': {'status': 'unavailable'},
                                                                                    'relationship_deltas': {'status': 'unavailable'}},
                                                                                   {'rendered_index': 2,
                                                                                    'native_option_index': 2,
                                                                                    'shown': True,
                                                                                    'enabled': True,
                                                                                    'fallback': False,
                                                                                    'cancel': False,
                                                                                    'resolved_name': '“给我看些独特的东西，而且得是库法的真正瑰宝。”',
                                                                                    'unavailable_reason': '',
                                                                                    'effect_indicators': {'status': 'available',
                                                                                                          'coverage': 'played-character-event-icon-indicators-1.20.0.4-v1',
                                                                                                          'complete_effect_set': False,
                                                                                                          'rows': []},
                                                                                    'effect_preview': {'status': 'unavailable',
                                                                                                       'reason': 'indicator_subset_has_no_completeness_signal'},
                                                                                    'resource_deltas': {'status': 'unavailable'},
                                                                                    'relationship_deltas': {'status': 'unavailable'}},
                                                                                   {'rendered_index': 3,
                                                                                    'native_option_index': 3,
                                                                                    'shown': True,
                                                                                    'enabled': True,
                                                                                    'fallback': False,
                                                                                    'cancel': False,
                                                                                    'resolved_name': '“我们携带的行囊已经够多了……”',
                                                                                    'unavailable_reason': '',
                                                                                    'effect_indicators': {'status': 'available',
                                                                                                          'coverage': 'played-character-event-icon-indicators-1.20.0.4-v1',
                                                                                                          'complete_effect_set': False,
                                                                                                          'rows': [{'kind': 'stress',
                                                                                                                    'direction': 'increase',
                                                                                                                    'magnitude': {'status': 'unavailable'},
                                                                                                                    'affected_by_trait': True,
                                                                                                                    'critical': False}]},
                                                                                    'effect_preview': {'status': 'unavailable',
                                                                                                       'reason': 'indicator_subset_has_no_completeness_signal'},
                                                                                    'resource_deltas': {'status': 'unavailable'},
                                                                                    'relationship_deltas': {'status': 'unavailable'}}]},
                                                  'policy_actually_used': 'native_first_displayed_v1',
                                                  'registry_consumption_succeeded_live': False}},
 'travel_danger_events.6030': {'analysis': {'source_analysis_completed': True,
                                            'migration_review_status': 'source_reviewed_no_occurrence_contract',
                                            'exact_build': '1.20.0.4',
                                            'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0041-events-source-analysis-12004.json',
                                            'source_document_sha256': 'b35d2835d1526b55d0dede20d111efdcad832f7993b0da3eea9c17ec50b8c68c',
                                            'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0041-events-occurrence.json',
                                            'title': '食物变质',
                                            'source_pins': [{'game_relative_path': 'events/travel_events/travel_danger_events_joe.txt',
                                                             'bytes': 77064,
                                                             'sha256': '43d8990d84fb154e3671780ed251abc4ffa14e0cb185a262ba3c15683f88f900',
                                                             'relevant_lines': [[2364, 3034]]},
                                                            {'game_relative_path': 'common/scripted_effects/00_travel_effects.txt',
                                                             'bytes': 1867,
                                                             'sha256': '47a4b46a479a2215ffeda4b6d7b8d9226928f6ec0dc70c289b4e0e2fe2b5ec0e',
                                                             'relevant_lines': [[9, 31]]},
                                                            {'game_relative_path': 'common/scripted_effects/04_dlc_ep2_tour_effects.txt',
                                                             'bytes': 17935,
                                                             'sha256': '180a9e666317ba7e58525d11848544bca1bf2b6e6062b0fe1110f555abdf328e',
                                                             'relevant_lines': [[330, 367]]},
                                                            {'game_relative_path': 'common/modifiers/04_ep2_modifiers.txt',
                                                             'bytes': 7458,
                                                             'sha256': 'e2020dc5dfaffac77b381104d63b30dc3127a75b80b9121319fc4ccc1fb96fe4',
                                                             'relevant_lines': [[229, 232]]},
                                                            {'game_relative_path': 'common/modifiers/00_travel_modifiers.txt',
                                                             'bytes': 8782,
                                                             'sha256': 'b7a1365a14341bf647339cb843753e5da4f8d9990c52c92d6e10422a8530a2f1',
                                                             'relevant_lines': [[334, 337]]},
                                                            {'game_relative_path': 'common/scripted_effects/20_health_effects.txt',
                                                             'bytes': 107548,
                                                             'sha256': 'abefa738c913c660a52fa747bcc92fca2f57d77a0f47d903bedc2882f3d5a9db',
                                                             'relevant_lines': [[127, 216]]},
                                                            {'game_relative_path': 'localization/simp_chinese/event_localization/travel_events/travel_danger_events_joe_l_simp_chinese.yml',
                                                             'bytes': 18030,
                                                             'sha256': 'f21f957544dbc254e703b15ee93a868e6285881485f2bd21f5d7e8f6601ad4b4',
                                                             'relevant_lines': [[124, 135]]}],
                                            'source_options': [{'source_key': 'travel_danger_events.6030.a',
                                                                'historical_native_index': 0,
                                                                'historical_label': '只是有点发霉而已！',
                                                                'effects': ['If domicile exists, '
                                                                            'change_provisions=minor_provisions_loss.',
                                                                            'If not already ill: '
                                                                            'base40percent random, reduced '
                                                                            'by '
                                                                            'strong(-10),physique_good_1/2/3(-5/-10/-15),entourage '
                                                                            'herbalist(-10), requests '
                                                                            'contract_disease_effect(ill,TREATMENT_EVENT=yes). '
                                                                            'This is conditional and '
                                                                            'trait-adjusted, not an '
                                                                            'unconditional40percent outcome.',
                                                                            'If already ill: base50percent '
                                                                            'random, similarly reduced by '
                                                                            'strong/physique,logistician(-10),herbalist(-10), '
                                                                            'adds bad_soup_modifier '
                                                                            'for5years(stress_gain_mult+0.1). '
                                                                            'The source does not directly '
                                                                            'add pneumonia.',
                                                                            'No illness/modifier membership '
                                                                            'or danger-trackXP was read '
                                                                            'back. Wallets and stress '
                                                                            'unchanged at same date; later '
                                                                            'health1101 is not proof this A '
                                                                            'roll caused the illness.'],
                                                                'visibility': 'Shown/enabled in R0041; '
                                                                              'native index and label are '
                                                                              'historical evidence only. '
                                                                              'Fresh native shown order and '
                                                                              'legality are mandatory.',
                                                                'historical_R31_selected': False},
                                                               {'source_key': 'travel_danger_events.6030.b',
                                                                'historical_native_index': 1,
                                                                'historical_label': '大自然会为我们提供食物！',
                                                                'effects': ['Forage using '
                                                                            'highest_learning_entourage_member '
                                                                            'if its Learning exceeds root, '
                                                                            'otherwise root. Learning duel '
                                                                            'against medium_skill_rating '
                                                                            'with base '
                                                                            'weights15(success),5(illness),1(death), '
                                                                            'min1 and numerous '
                                                                            'skill/terrain/trait/entourage '
                                                                            'adjustments; these are not '
                                                                            'fixed15:5:1 probabilities.',
                                                                            'Success changes domicile '
                                                                            'provisions by '
                                                                            'minor_provisions_loss; '
                                                                            'poisoning requests '
                                                                            'ill/TREATMENT_EVENT=yes plus '
                                                                            'medium_provisions_loss; fatal '
                                                                            'branch kills root by '
                                                                            'death_poisonous_forage plus '
                                                                            'medium_provisions_loss. '
                                                                            'Actor-scope branches differ; '
                                                                            'source branch not selected.'],
                                                                'visibility': 'Shown/enabled in R0041; '
                                                                              'native index and label are '
                                                                              'historical evidence only. '
                                                                              'Fresh native shown order and '
                                                                              'legality are mandatory.',
                                                                'historical_R31_selected': False},
                                                               {'source_key': 'travel_danger_events.6030.c',
                                                                'historical_native_index': 2,
                                                                'historical_label': '肯定能从这里的本地人那弄到点\x15EMP '
                                                                                    '什么\x15!。',
                                                                'effects': ['Land-only steal option; '
                                                                            'add_prestige=minor_prestige_loss '
                                                                            'and optional domicile '
                                                                            'minor_provisions_loss.',
                                                                            'Within same top-liege realm: '
                                                                            'province owner other than root '
                                                                            'gets opinion-10; county gets '
                                                                            'travel_stealing_food_modifier '
                                                                            'for5years(county_opinion_add-25).',
                                                                            'Outside that branch, '
                                                                            'base50percent(-15 if no '
                                                                            'province owner) chooses an '
                                                                            'adult entourage woundee with '
                                                                            'prowess/role weights and '
                                                                            'requests '
                                                                            'increase_wounds_effect. '
                                                                            'Just/generous minor '
                                                                            'stress/fulfillment gain inputs; '
                                                                            'branch not selected.'],
                                                                'visibility': 'Shown/enabled in R0041; '
                                                                              'native index and label are '
                                                                              'historical evidence only. '
                                                                              'Fresh native shown order and '
                                                                              'legality are mandatory.',
                                                                'historical_R31_selected': False}],
                                            'agent_reference': 'R0041 instance7/day66 actor15893, '
                                                               'travel_leader/highest_learning_entourage_member34769. '
                                                               'A/native0 selected once; ACK and old-window '
                                                               'disappearance at unchanged date51396504. '
                                                               'Actual wallets/stress unchanged; no ill '
                                                               'membership/provisions/XP query. Immediate '
                                                               'mp_delay_travel_plan(DAYS=90) and after '
                                                               'mp_resume_travel_plan both require '
                                                               'has_multiple_players in the shared helper. '
                                                               "Do not count them as this run's "
                                                               'observed90day delays or travel advance. '
                                                               'After invokes '
                                                               'traveler_danger_xp_effect(MIN3,MAX6): only '
                                                               'owned lifestyle_traveler gains dangerXP3–6, '
                                                               'or5–8 with journey_perk; it does not grant '
                                                               'the trait. Six-month cooldown is '
                                                               'event-local. Localization6030.d exists but '
                                                               'there is no fourth source option in this '
                                                               'definition.',
                                            'current_native_legality': None,
                                            'action_ready': False,
                                            'ordinary_auto_consumes': False,
                                            'full_occurrence_contract_registered': False,
                                            'selection_policy_changed': False,
                                            'historical_index_is_current_selection_permission': False,
                                            'historical_evidence_is_current_state': False},
                               'observations': {'machine_id': '4-8e1c2f1861',
                                                'observed_at_utc': '2026-10-23T07:24:44.854327+00:00',
                                                'run_id': '4-8e1c2f1861--faith-engine--R0041',
                                                'actual': {'event_instance_id': 7,
                                                           'event_definition_key': 'travel_danger_events.6030',
                                                           'selected_native_option_index': 0,
                                                           'selected_option_number': 1,
                                                           'submission_attempted': True,
                                                           'ack_accepted': True,
                                                           'old_instance_gone_in_independent_snapshot': True,
                                                           'actor_character_id': 15893,
                                                           'date_raw': 51396504,
                                                           'game_day': 66,
                                                           'snapshot_revision': 157,
                                                           'post_actor_character_id': 15893,
                                                           'post_date_raw': 51396504,
                                                           'post_active_event': None,
                                                           'stress_before': 0,
                                                           'stress_after': 0,
                                                           'wallets_before': {'played_character_gold': {'raw': 117594432,
                                                                                                        'scale': 100000},
                                                                              'played_character_prestige': {'raw': 12030564,
                                                                                                            'scale': 100000},
                                                                              'played_character_piety': {'raw': 225388500,
                                                                                                         'scale': 100000}},
                                                           'wallets_after': {'played_character_gold': {'raw': 117594432,
                                                                                                       'scale': 100000},
                                                                             'played_character_prestige': {'raw': 12030564,
                                                                                                           'scale': 100000},
                                                                             'played_character_piety': {'raw': 225388500,
                                                                                                        'scale': 100000}},
                                                           'evidence': [{'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0041\\case-output\\faith-e02-journey-001-event-7-offline-analysis-input.json',
                                                                         'bytes': 76616,
                                                                         'sha256': '7da35cfe2951e3b11093d3294d9d6fadabdba579af56d1b3a27c4caca877f410'},
                                                                        {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0041\\case-output\\faith-e02-journey-001-event-7-selection-intent.json',
                                                                         'bytes': 82048,
                                                                         'sha256': 'e2dcefd2beae1ad10bb2410614b21ec77bcc952ca19e2e0b954f3968df9b4e95'},
                                                                        {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0041\\case-output\\faith-e02-journey-001-event-7-selection-observed.json',
                                                                         'bytes': 37922,
                                                                         'sha256': 'fe90e58ebc938f719db68056bdf66dcbc90e22538a4b0a20f540a35ae294dbb0'},
                                                                        {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0041\\case-output\\faith-e02-journey-001-0059-event-select-once.actual-results.json',
                                                                         'bytes': 42080,
                                                                         'sha256': '7d2cca40555b0fa14f3ab3ca77ea6a4917f095bced0bdf6b9ca3e40bd7c28456'}],
                                                           'displayed_options': [{'rendered_index': 0,
                                                                                  'native_option_index': 0,
                                                                                  'shown': True,
                                                                                  'enabled': True,
                                                                                  'fallback': False,
                                                                                  'cancel': False,
                                                                                  'resolved_name': '只是有点发霉而已！',
                                                                                  'unavailable_reason': '',
                                                                                  'effect_indicators': {'status': 'available',
                                                                                                        'coverage': 'played-character-event-icon-indicators-1.20.0.4-v1',
                                                                                                        'complete_effect_set': False,
                                                                                                        'rows': [{'kind': 'trait',
                                                                                                                  'operation': 'add',
                                                                                                                  'trait': {'status': 'available',
                                                                                                                            'native_id': 109,
                                                                                                                            'key': 'ill'}}]},
                                                                                  'effect_preview': {'status': 'unavailable',
                                                                                                     'reason': 'indicator_subset_has_no_completeness_signal'},
                                                                                  'resource_deltas': {'status': 'unavailable'},
                                                                                  'relationship_deltas': {'status': 'unavailable'}},
                                                                                 {'rendered_index': 1,
                                                                                  'native_option_index': 1,
                                                                                  'shown': True,
                                                                                  'enabled': True,
                                                                                  'fallback': False,
                                                                                  'cancel': False,
                                                                                  'resolved_name': '大自然会为我们提供食物！',
                                                                                  'unavailable_reason': '',
                                                                                  'effect_indicators': {'status': 'available',
                                                                                                        'coverage': 'played-character-event-icon-indicators-1.20.0.4-v1',
                                                                                                        'complete_effect_set': False,
                                                                                                        'rows': [{'kind': 'trait',
                                                                                                                  'operation': 'add',
                                                                                                                  'trait': {'status': 'available',
                                                                                                                            'native_id': 109,
                                                                                                                            'key': 'ill'}},
                                                                                                                 {'kind': 'death',
                                                                                                                  'subject': 'played_character',
                                                                                                                  'direction': 'not_applicable'}]},
                                                                                  'effect_preview': {'status': 'unavailable',
                                                                                                     'reason': 'indicator_subset_has_no_completeness_signal'},
                                                                                  'resource_deltas': {'status': 'unavailable'},
                                                                                  'relationship_deltas': {'status': 'unavailable'}},
                                                                                 {'rendered_index': 2,
                                                                                  'native_option_index': 2,
                                                                                  'shown': True,
                                                                                  'enabled': True,
                                                                                  'fallback': False,
                                                                                  'cancel': False,
                                                                                  'resolved_name': '肯定能从这里的本地人那弄到点\x15EMP '
                                                                                                   '什么\x15!。',
                                                                                  'unavailable_reason': '',
                                                                                  'effect_indicators': {'status': 'available',
                                                                                                        'coverage': 'played-character-event-icon-indicators-1.20.0.4-v1',
                                                                                                        'complete_effect_set': False,
                                                                                                        'rows': [{'kind': 'stress',
                                                                                                                  'direction': 'increase',
                                                                                                                  'magnitude': {'status': 'unavailable'},
                                                                                                                  'affected_by_trait': True,
                                                                                                                  'critical': False}]},
                                                                                  'effect_preview': {'status': 'unavailable',
                                                                                                     'reason': 'indicator_subset_has_no_completeness_signal'},
                                                                                  'resource_deltas': {'status': 'unavailable'},
                                                                                  'relationship_deltas': {'status': 'unavailable'}}]},
                                                'policy_actually_used': 'native_first_displayed_v1',
                                                'registry_consumption_succeeded_live': False}}}
PILGRIMAGE_TRAVEL_SOURCE_ONLY_12004.update(_R0039_R0041_SOURCE_ONLY)


_R0042_SOURCE_ONLY: dict[str, SourceOnlyRecord] = {'pilgrimage_intent.1044': {'analysis': {'source_analysis_completed': True,
                                         'migration_review_status': 'source_reviewed_no_occurrence_contract',
                                         'exact_build': '1.20.0.4',
                                         'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0042-events-source-analysis-12004.json',
                                         'source_document_sha256': '577e30c6f4c167685e3623c86e927926a00ad7a845f42ef44acfa2d0f2cbd220',
                                         'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0042-final-events-occurrence.json',
                                         'title': '预兆：悲哀的景象',
                                         'source_pins': [{'game_relative_path': 'events/activities/pilgrimage_activity/pilgrimage_intent_events.txt',
                                                          'bytes': 57928,
                                                          'sha256': '3ddbde37f029845aa265aae749fe131bed571f02a5c4faac5d0074a615b39878',
                                                          'relevant_lines': [[1249, 1303]]},
                                                         {'game_relative_path': 'common/modifiers/00_activity_pilgrimage_modifiers.txt',
                                                          'bytes': 8263,
                                                          'sha256': 'b4b087debf7975b02fdc30d3244a04aca634e3e26b2fafa4c42057e71a1c1580',
                                                          'relevant_lines': [[214, 223]]},
                                                         {'game_relative_path': 'localization/simp_chinese/event_localization/activities/pilgrimage_intent_events_l_simp_chinese.yml',
                                                          'bytes': 18043,
                                                          'sha256': '7f2a61394920a1c0675185905e4bb8b3ce431e9b24122267c2e7e5d2663a5b1a',
                                                          'relevant_lines': [[82, 85]]}],
                                         'source_options': [{'source_key': 'pilgrimage_intent.1044.a',
                                                             'historical_native_index': 0,
                                                             'historical_label': '有东西冲我来了！',
                                                             'effects': ['Add pilgrimage_failure_omen_modifier '
                                                                         'for20years: stress_gain_mult+0.2; '
                                                                         'health_negative is its icon, not a '
                                                                         'health reduction.',
                                                                         'Create bad_prey_omen_memory. Request '
                                                                         'stress_and_fulfillment_impact: base '
                                                                         'medium gain; cynical minor loss; '
                                                                         'brave/trusting minor gain. Actual '
                                                                         'amount depends on the character and '
                                                                         'modifiers.',
                                                                         'R42 native0 was submitted once; '
                                                                         'same-date independent snapshot shows '
                                                                         'stress0->20, wallets unchanged. '
                                                                         'Modifier and memory membership were '
                                                                         'not read back.'],
                                                             'visibility': 'R42 instance7: only '
                                                                           'rendered0/native0 shown and '
                                                                           'enabled.',
                                                             'historical_R31_selected': False},
                                                            {'source_key': 'pilgrimage_intent.1044.b',
                                                             'historical_native_index': 1,
                                                             'historical_label': '我将神不知鬼不觉地摧毁我的敌人！',
                                                             'effects': ['Requires lifestyle_mystic. Add '
                                                                         'pilgrimage_hostile_omen_modifier '
                                                                         'for20years: intrigue+1 and '
                                                                         'hostile_scheme_phase_duration_add=medium_scheme_phase_duration_bonus_value.',
                                                                         'Create '
                                                                         'bad_but_good_prey_omen_memory. '
                                                                         'Request base/brave minor stress '
                                                                         'loss, compassionate/forgiving minor '
                                                                         'stress gain.'],
                                                             'visibility': 'Source ordinal1/native1 was hidden '
                                                                           'in R42; this is no current '
                                                                           'permission.',
                                                             'historical_R31_selected': False}],
                                         'agent_reference': 'R0042 preserved native input/intent/ACK and '
                                                            'independent old-window disappearance; exact-build '
                                                            'source reviewed offline. This is an omen '
                                                            'follow-up event, not arrival, a ritual '
                                                            'completion, or Pilgrim/Hajjaj reward. No direct '
                                                            'travel delay effect is present in this '
                                                            'definition. dangerous_local_game saved scope '
                                                            'resolves as character root15893 in this actual '
                                                            'window; its animal-like name is not proof of an '
                                                            'animal character or invalid scope.',
                                         'current_native_legality': None,
                                         'action_ready': False,
                                         'ordinary_auto_consumes': False,
                                         'full_occurrence_contract_registered': False,
                                         'selection_policy_changed': False,
                                         'historical_index_is_current_selection_permission': False,
                                         'historical_evidence_is_current_state': False},
                            'observations': {'machine_id': '4-8e1c2f1861',
                                             'observed_at_utc': '2026-10-23T10:11:54.010569+00:00',
                                             'run_id': '4-8e1c2f1861--faith-engine--R0042',
                                             'actual': {'event_instance_id': 7,
                                                        'event_definition_key': 'pilgrimage_intent.1044',
                                                        'observed_at_utc': '2026-10-23T10:11:47.444789+00:00',
                                                        'input': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0042\\case-output\\faith-e02-journey-001-event-7-offline-analysis-input.json',
                                                                  'bytes': 73625,
                                                                  'sha256': '808ae160e5596de9dcf9bba504998872bffbc78e9e16e1fa5743a9f1604b788c'},
                                                        'date_raw': 51396648,
                                                        'knowledge_status': 'unavailable',
                                                        'unavailable_reason': 'event_definition_key_not_registered',
                                                        'source_analysis_completed': False,
                                                        'has_migration_placeholder_only': True,
                                                        'selection_observed': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0042\\case-output\\faith-e02-journey-001-event-7-selection-observed.json',
                                                                               'bytes': 37917,
                                                                               'sha256': '4578ea8941055da914ddf1889bf928d11ee7f76228bfc8e01d6762d7e4fc60b5'},
                                                        'selected_native_option_index': 0,
                                                        'submission_attempted': True,
                                                        'ack_accepted': True,
                                                        'old_instance_gone_in_independent_snapshot': True,
                                                        'input_observed_at_utc': '2026-10-23T10:11:47.444789+00:00'},
                                             'policy_actually_used': 'native_first_displayed_v1',
                                             'registry_consumption_succeeded_live': False}},
 'travel_danger_events.9020': {'analysis': {'source_analysis_completed': True,
                                            'migration_review_status': 'source_reviewed_no_occurrence_contract',
                                            'exact_build': '1.20.0.4',
                                            'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0042-events-source-analysis-12004.json',
                                            'source_document_sha256': '577e30c6f4c167685e3623c86e927926a00ad7a845f42ef44acfa2d0f2cbd220',
                                            'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0042-final-events-occurrence.json',
                                            'title': '紧急情况的消瘦',
                                            'source_pins': [{'game_relative_path': 'events/travel_events/travel_danger_events_oltner.txt',
                                                             'bytes': 27455,
                                                             'sha256': '086725937d1b89b82be5f957aef461f95bf0810ff506abf09c2031c779f3ab3d',
                                                             'relevant_lines': [[442, 798]]},
                                                            {'game_relative_path': 'common/scripted_effects/00_secret_effects.txt',
                                                             'bytes': 69449,
                                                             'sha256': '4b86ba489602089969293c810a6aaee81ea5d213f7c0456f051ae8785addf7f9',
                                                             'relevant_lines': [[87, 108], [268, 294]]},
                                                            {'game_relative_path': 'common/scripted_effects/00_travel_effects.txt',
                                                             'bytes': 1867,
                                                             'sha256': '47a4b46a479a2215ffeda4b6d7b8d9226928f6ec0dc70c289b4e0e2fe2b5ec0e',
                                                             'relevant_lines': [[9, 31]]},
                                                            {'game_relative_path': 'common/scripted_effects/04_dlc_ep2_tour_effects.txt',
                                                             'bytes': 17935,
                                                             'sha256': '180a9e666317ba7e58525d11848544bca1bf2b6e6062b0fe1110f555abdf328e',
                                                             'relevant_lines': [[330, 367]]},
                                                            {'game_relative_path': 'common/modifiers/00_travel_modifiers.txt',
                                                             'bytes': 8782,
                                                             'sha256': 'b7a1365a14341bf647339cb843753e5da4f8d9990c52c92d6e10422a8530a2f1',
                                                             'relevant_lines': [[316, 321]]},
                                                            {'game_relative_path': 'localization/simp_chinese/event_localization/travel_events/travel_danger_events_oltner_l_simp_chinese.yml',
                                                             'bytes': 7676,
                                                             'sha256': 'fbd5fd212ff052c3b0396946e3d7b5144d1bd9327bb7f475ed0efb0efdad983b',
                                                             'relevant_lines': [[15, 27]]}],
                                            'source_options': [{'source_key': 'travel_danger_events.9020.cannibal',
                                                                'historical_native_index': 0,
                                                                'historical_label': '啊，马哈茂德，你愿意为阿拉伯帝国献出生命吗？',
                                                                'effects': ['Shown if '
                                                                            'sadistic/arbitrary/gluttonous/callous '
                                                                            'or already cannibal. Requests '
                                                                            'death_vanished for saved '
                                                                            'emaciated_character, not root. '
                                                                            'R42 saved target is19281; death '
                                                                            'was not independently read back.',
                                                                            'Call '
                                                                            'give_cannibal_secret_or_trait_effect '
                                                                            'on root and every entourage '
                                                                            'member. For someone not already '
                                                                            'cannibal: an available advanced '
                                                                            'ruler may learn '
                                                                            'tenet_ritual_cannibalism; if '
                                                                            'cannibal is shunned/criminal '
                                                                            'under own or liege Rite, add '
                                                                            'secret_cannibal and conditional '
                                                                            'personal spiritual-fulfillment '
                                                                            'loss (medium if shunned, major if '
                                                                            'criminal); otherwise add cannibal '
                                                                            'trait.',
                                                                            "Reveal each entourage member's "
                                                                            'previously unknown cannibal '
                                                                            "secret to root, and root's "
                                                                            'previously unknown cannibal '
                                                                            'secret to each entourage member. '
                                                                            'Does not unconditionally give '
                                                                            'every character a public cannibal '
                                                                            'trait.',
                                                                            'R42 native0 was submitted once, '
                                                                            'ACK accepted and old instance '
                                                                            'gone; root alive/same actor, '
                                                                            'wallets and stress unchanged at '
                                                                            'same date. Target death, '
                                                                            'secret/trait, known-tenet and '
                                                                            'fulfillment values were not '
                                                                            'independently read back.'],
                                                                'visibility': 'R42 instance10 '
                                                                              'rendered0/native0 '
                                                                              'shown/enabled; actual first '
                                                                              'displayed option, not source '
                                                                              '.a.',
                                                                'historical_R31_selected': False},
                                                               {'source_key': 'travel_danger_events.9020.hunter',
                                                                'historical_native_index': 1,
                                                                'historical_label': '某处一定有猎物！',
                                                                'effects': ['Requires lifestyle_hunter. '
                                                                            'Weighted70 branch requests5 '
                                                                            'hunter-track XP; weighted30 '
                                                                            'branch gives root and every '
                                                                            'entourage member '
                                                                            'emaciated_modifier3years and '
                                                                            'current_weight-50.',
                                                                            'emaciated_modifier: health-0.5, '
                                                                            'negate_health_penalty_add-1, '
                                                                            'prowess-5. These are source '
                                                                            'branch effects, not R42 '
                                                                            'outcomes.'],
                                                                'visibility': 'Source ordinal1/native1 hidden '
                                                                              'in R42.',
                                                                'historical_R31_selected': False},
                                                               {'source_key': 'travel_danger_events.9020.a',
                                                                'historical_native_index': 2,
                                                                'historical_label': '真希望那些话能吃……',
                                                                'effects': ['Root and every entourage member '
                                                                            'receive emaciated_modifier3years '
                                                                            'and hidden current_weight-50.',
                                                                            'emaciated_modifier: health-0.5, '
                                                                            'negate_health_penalty_add-1, '
                                                                            'prowess-5. Arrogant medium '
                                                                            'stress/fulfillment gain input.'],
                                                                'visibility': 'R42 rendered1/native2 '
                                                                              'shown/enabled, not selected.',
                                                                'historical_R31_selected': False},
                                                               {'source_key': 'travel_danger_events.9020.b',
                                                                'historical_native_index': 3,
                                                                'historical_label': '我们剩的那点全都归我！',
                                                                'effects': ['Root loses major prestige and '
                                                                            'major piety (dynamic script '
                                                                            'values). Every entourage member '
                                                                            'receives '
                                                                            'emaciated_modifier3years, '
                                                                            'current_weight-50 and '
                                                                            'cruelty_opinion toward root with '
                                                                            'opinion-35.',
                                                                            'Humility/compassionate medium and '
                                                                            'content/just minor '
                                                                            'stress/fulfillment gain inputs. '
                                                                            'No root emaciated modifier is '
                                                                            'directly assigned in this '
                                                                            'option.'],
                                                                'visibility': 'R42 rendered2/native3 '
                                                                              'shown/enabled, not selected.',
                                                                'historical_R31_selected': False}],
                                            'agent_reference': 'R0042 preserved native input/intent/ACK and '
                                                               'independent old-window disappearance; '
                                                               'exact-build source reviewed offline. Trigger '
                                                               'requires available adult traveller, eligible '
                                                               'entourage and desert/sea/army/occupation/siege '
                                                               'danger, with specified culture exclusions. '
                                                               'Event-local cooldown1month is not pilgrimage '
                                                               'cooldown. Immediate selects '
                                                               'emaciated_character with weight=current_weight '
                                                               'and requests traveler danger XP10-15 only if '
                                                               'lifestyle_traveler already owned; journey_perk '
                                                               'adds2 to each bound (12-17). No new traveler '
                                                               'trait grant. Actual XP was not read back. '
                                                               'Immediate mp_delay_travel_plan90 and after '
                                                               'mp_resume_travel_plan are guarded by '
                                                               'has_multiple_players in shared helper; do not '
                                                               'claim a single-player90-day delay. No direct '
                                                               'ordinary Pilgrim/Hajjaj trait grant or '
                                                               'conversion is present.',
                                            'current_native_legality': None,
                                            'action_ready': False,
                                            'ordinary_auto_consumes': False,
                                            'full_occurrence_contract_registered': False,
                                            'selection_policy_changed': False,
                                            'historical_index_is_current_selection_permission': False,
                                            'historical_evidence_is_current_state': False},
                               'observations': {'machine_id': '4-8e1c2f1861',
                                                'observed_at_utc': '2026-10-23T10:13:59.799750+00:00',
                                                'run_id': '4-8e1c2f1861--faith-engine--R0042',
                                                'actual': {'event_instance_id': 10,
                                                           'event_definition_key': 'travel_danger_events.9020',
                                                           'observed_at_utc': '2026-10-23T10:13:52.744146+00:00',
                                                           'input': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0042\\case-output\\faith-e02-journey-001-event-10-offline-analysis-input.json',
                                                                     'bytes': 76339,
                                                                     'sha256': 'ab5d9a4f4efc4baee179300176ff939decba5aa1365212627f3232db21bed301'},
                                                           'date_raw': 51397368,
                                                           'knowledge_status': 'unavailable',
                                                           'unavailable_reason': 'event_definition_key_not_registered',
                                                           'source_analysis_completed': False,
                                                           'has_migration_placeholder_only': True,
                                                           'selection_observed': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0042\\case-output\\faith-e02-journey-001-event-10-selection-observed.json',
                                                                                  'bytes': 37925,
                                                                                  'sha256': 'c104a5bb7e65e8e7a31e6e2e50058d32a725431aa241009a7f4633f198e527d3'},
                                                           'selected_native_option_index': 0,
                                                           'submission_attempted': True,
                                                           'ack_accepted': True,
                                                           'old_instance_gone_in_independent_snapshot': True,
                                                           'input_observed_at_utc': '2026-10-23T10:13:52.744146+00:00'},
                                                'policy_actually_used': 'native_first_displayed_v1',
                                                'registry_consumption_succeeded_live': False}},
 'hajj.3010': {'analysis': {'source_analysis_completed': True,
                            'migration_review_status': 'source_reviewed_no_occurrence_contract',
                            'exact_build': '1.20.0.4',
                            'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-v5-doctrines-hajj-12004.json',
                            'source_document_sha256': 'a717fc94a06ccc2d90405d28304e2a98d6ab9f9ec531d6a4b4528ba5a8c0c360',
                            'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0042-final-events-occurrence.json',
                            'title': '易卜拉欣立足地',
                            'source_pins': [{'game_relative_path': 'common/scripted_effects/00_pilgrimage_effects.txt',
                                             'bytes': 40713,
                                             'sha256': '4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80',
                                             'relevant_lines': [[55, 670],
                                                                [137, 137],
                                                                [240, 240],
                                                                [286, 286],
                                                                [672, 874],
                                                                [1028, 1206],
                                                                [1196, 1196],
                                                                [1197, 1197],
                                                                [1225, 1420]]},
                                            {'game_relative_path': 'events/activities/pilgrimage_activity/hajj_events.txt',
                                             'bytes': 29519,
                                             'sha256': '0e0617fd6a17192a87fcdb21fe07ae896a42c4c1c5e0e93e0f0a7ee3d0fc67c0',
                                             'relevant_lines': [[293, 496]]},
                                            {'game_relative_path': 'common/modifiers/00_activity_pilgrimage_modifiers.txt',
                                             'bytes': 8263,
                                             'sha256': 'b4b087debf7975b02fdc30d3244a04aca634e3e26b2fafa4c42057e71a1c1580',
                                             'relevant_lines': [[3, 26],
                                                                [78, 83],
                                                                [126, 159],
                                                                [308, 320],
                                                                [322, 364]]},
                                            {'game_relative_path': 'common/script_values/00_basic_values.txt',
                                             'bytes': 50566,
                                             'sha256': 'c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef',
                                             'relevant_lines': [[16, 180],
                                                                [451, 455],
                                                                [1131, 1135],
                                                                [1139, 1162],
                                                                [1164, 1168]]},
                                            {'game_relative_path': 'localization/simp_chinese/event_localization/activities/hajj_events_l_simp_chinese.yml',
                                             'bytes': 12384,
                                             'sha256': '96331cb1368c6e889e467b870ec0bb5b46a7736af760434923c02cdadb1a305d',
                                             'relevant_lines': [[58, 58],
                                                                [60, 60],
                                                                [63, 63],
                                                                [65, 65],
                                                                [68, 68],
                                                                [72, 72],
                                                                [74, 74],
                                                                [83, 83],
                                                                [86, 86],
                                                                [88, 88],
                                                                [89, 89],
                                                                [90, 90],
                                                                [95, 95],
                                                                [97, 97],
                                                                [99, 99],
                                                                [101, 101],
                                                                [105, 105],
                                                                [107, 107],
                                                                [109, 109],
                                                                [111, 111],
                                                                [114, 114],
                                                                [116, 116],
                                                                [118, 118],
                                                                [120, 120],
                                                                [122, 122],
                                                                [125, 125],
                                                                [130, 130],
                                                                [131, 131]]},
                                            {'game_relative_path': 'common/script_values/01_dynamic_values.txt',
                                             'bytes': 48201,
                                             'sha256': '023165e7d27d106a34f34d7726d938efa8d5dce25650ea3256e0b5ea3f73cc2a',
                                             'relevant_lines': [[13, 31], [53, 71], [93, 111], [173, 191]]}],
                            'source_options': [{'source_key': 'hajj.3010.a',
                                                'historical_native_index': 0,
                                                'historical_label': '我应该为了更实质性的东西而祈祷……',
                                                'effects': ['Conditional weighted pool can grant wealth3years, '
                                                            'prestige5years, opinion10years, '
                                                            'superstition10years or stress. Existing modifiers '
                                                            'affect eligibility and callous changes '
                                                            'bad-outcome weight. These are alternatives, not a '
                                                            'combined grant.',
                                                            'R42 selected native0 once; same-date wallets and '
                                                            'stress remained unchanged. Which modifier or '
                                                            'random branch occurred was not read back.'],
                                                'visibility': 'R42 shown/enabled rendered0/native0; selected.',
                                                'historical_R31_selected': False},
                                               {'source_key': 'hajj.3010.b',
                                                'historical_native_index': 1,
                                                'historical_label': '咱们下来细想一下。',
                                                'effects': ['Request50piety and pious_type_option_effect; '
                                                            'activity log records the prayer. Personality '
                                                            'stress/fulfillment inputs are separate.'],
                                                'visibility': 'R42 shown/enabled rendered1/native1; not '
                                                              'selected.',
                                                'historical_R31_selected': False}],
                            'agent_reference': 'After either option schedule hajj.3020 in15days; event '
                                               'scheduling is not a measured trip delay. Reuses existing '
                                               'exact-build source analysis; R42 final failure is preserved. '
                                               'The former nonempty migration placeholder did not prove '
                                               'completed source analysis.',
                            'current_native_legality': None,
                            'action_ready': False,
                            'ordinary_auto_consumes': False,
                            'full_occurrence_contract_registered': False,
                            'selection_policy_changed': False,
                            'historical_index_is_current_selection_permission': False,
                            'historical_evidence_is_current_state': False},
               'observations': {'machine_id': '4-8e1c2f1861',
                                'observed_at_utc': '2026-10-23T11:22:17.564013+00:00',
                                'run_id': '4-8e1c2f1861--faith-engine--R0042',
                                'actual': {'event_instance_id': 12,
                                           'event_definition_key': 'hajj.3010',
                                           'observed_at_utc': '2026-10-23T11:22:17.564013+00:00',
                                           'input': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0042\\case-output\\faith-e02-journey-001-event-12-offline-analysis-input.json',
                                                     'bytes': 68993,
                                                     'sha256': 'ba26bd22c0531d7da7425102caa1cd269d67029acae0efc251f32458846cb820'},
                                           'date_raw': 51401376,
                                           'knowledge_status': 'unavailable',
                                           'unavailable_reason': 'event_definition_key_not_registered',
                                           'source_analysis_completed': False,
                                           'has_migration_placeholder_only': True,
                                           'selection_observed': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0042\\case-output\\faith-e02-journey-001-event-12-selection-observed.json',
                                                                  'bytes': 76023,
                                                                  'sha256': '18ca35c0eb5c9d154da850bfc46e7e72ac251fbb1f0bb2be158bb26260ee1259'},
                                           'selected_native_option_index': 0,
                                           'submission_attempted': True,
                                           'ack_accepted': True,
                                           'old_instance_gone_in_independent_snapshot': True,
                                           'saved_scopes': [{'name': 'activity',
                                                             'name_identifier': 2,
                                                             'scope': {'status': 'available',
                                                                       'raw_type_index': 6,
                                                                       'type_key': 'activity',
                                                                       'subtype': 0,
                                                                       'typed_identity': {'status': 'unavailable',
                                                                                          'reason': 'generic_scope_payload_identity_not_closed'}}},
                                                            {'name': 'host',
                                                             'name_identifier': 62,
                                                             'scope': {'status': 'available',
                                                                       'raw_type_index': 4,
                                                                       'type_key': 'character',
                                                                       'subtype': 0,
                                                                       'typed_identity': {'status': 'available',
                                                                                          'kind': 'character',
                                                                                          'character_id': 15893}}},
                                                            {'name': 'province',
                                                             'name_identifier': 37,
                                                             'scope': {'status': 'available',
                                                                       'raw_type_index': 8,
                                                                       'type_key': 'province',
                                                                       'subtype': 0,
                                                                       'typed_identity': {'status': 'unavailable',
                                                                                          'reason': 'generic_scope_payload_identity_not_closed'}}}],
                                           'displayed_options': [{'rendered_index': 0,
                                                                  'native_option_index': 0,
                                                                  'shown': True,
                                                                  'enabled': True,
                                                                  'resolved_name': '我应该为了更实质性的东西而祈祷……'},
                                                                 {'rendered_index': 1,
                                                                  'native_option_index': 1,
                                                                  'shown': True,
                                                                  'enabled': True,
                                                                  'resolved_name': '咱们下来细想一下。'}],
                                           'before': {'date_raw': 51401376,
                                                      'actor': 15893,
                                                      'stress': 97,
                                                      'played_character_gold': {'raw': 133425117,
                                                                                'scale': 100000},
                                                      'played_character_prestige': {'raw': 15434246,
                                                                                    'scale': 100000},
                                                      'played_character_piety': {'raw': 246748250,
                                                                                 'scale': 100000}},
                                           'after': {'date_raw': 51401376,
                                                     'actor': 15893,
                                                     'stress': 97,
                                                     'played_character_gold': {'raw': 133425117,
                                                                               'scale': 100000},
                                                     'played_character_prestige': {'raw': 15434246,
                                                                                   'scale': 100000},
                                                     'played_character_piety': {'raw': 246748250,
                                                                                'scale': 100000}},
                                           'selection_source': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0042\\case-output\\faith-e02-journey-001-0248-event-select-once.actual-results.json',
                                                                'bytes': 39222,
                                                                'sha256': 'e7a83b180145a00652fd100fc1dfdf7e3245bf86887d206d209b40d35f24fc87'},
                                           'input_observed_at_utc': '2026-10-23T11:16:55.235879+00:00'},
                                'policy_actually_used': 'native_first_displayed_v1',
                                'registry_consumption_succeeded_live': False}},
 'hajj.3020': {'analysis': {'source_analysis_completed': True,
                            'migration_review_status': 'source_reviewed_no_occurrence_contract',
                            'exact_build': '1.20.0.4',
                            'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-v5-doctrines-hajj-12004.json',
                            'source_document_sha256': 'a717fc94a06ccc2d90405d28304e2a98d6ab9f9ec531d6a4b4528ba5a8c0c360',
                            'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0042-final-events-occurrence.json',
                            'title': '赛法和麦尔维',
                            'source_pins': [{'game_relative_path': 'common/scripted_effects/00_pilgrimage_effects.txt',
                                             'bytes': 40713,
                                             'sha256': '4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80',
                                             'relevant_lines': [[55, 670],
                                                                [137, 137],
                                                                [240, 240],
                                                                [286, 286],
                                                                [672, 874],
                                                                [1028, 1206],
                                                                [1196, 1196],
                                                                [1197, 1197],
                                                                [1225, 1420]]},
                                            {'game_relative_path': 'events/activities/pilgrimage_activity/hajj_events.txt',
                                             'bytes': 29519,
                                             'sha256': '0e0617fd6a17192a87fcdb21fe07ae896a42c4c1c5e0e93e0f0a7ee3d0fc67c0',
                                             'relevant_lines': [[498, 784]]},
                                            {'game_relative_path': 'common/modifiers/00_activity_pilgrimage_modifiers.txt',
                                             'bytes': 8263,
                                             'sha256': 'b4b087debf7975b02fdc30d3244a04aca634e3e26b2fafa4c42057e71a1c1580',
                                             'relevant_lines': [[3, 26],
                                                                [78, 83],
                                                                [126, 159],
                                                                [308, 320],
                                                                [322, 364]]},
                                            {'game_relative_path': 'common/script_values/00_basic_values.txt',
                                             'bytes': 50566,
                                             'sha256': 'c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef',
                                             'relevant_lines': [[16, 180],
                                                                [451, 455],
                                                                [1131, 1135],
                                                                [1139, 1162],
                                                                [1164, 1168]]},
                                            {'game_relative_path': 'localization/simp_chinese/event_localization/activities/hajj_events_l_simp_chinese.yml',
                                             'bytes': 12384,
                                             'sha256': '96331cb1368c6e889e467b870ec0bb5b46a7736af760434923c02cdadb1a305d',
                                             'relevant_lines': [[58, 58],
                                                                [60, 60],
                                                                [63, 63],
                                                                [65, 65],
                                                                [68, 68],
                                                                [72, 72],
                                                                [74, 74],
                                                                [83, 83],
                                                                [86, 86],
                                                                [88, 88],
                                                                [89, 89],
                                                                [90, 90],
                                                                [95, 95],
                                                                [97, 97],
                                                                [99, 99],
                                                                [101, 101],
                                                                [105, 105],
                                                                [107, 107],
                                                                [109, 109],
                                                                [111, 111],
                                                                [114, 114],
                                                                [116, 116],
                                                                [118, 118],
                                                                [120, 120],
                                                                [122, 122],
                                                                [125, 125],
                                                                [130, 130],
                                                                [131, 131]]},
                                            {'game_relative_path': 'common/script_values/01_dynamic_values.txt',
                                             'bytes': 48201,
                                             'sha256': '023165e7d27d106a34f34d7726d938efa8d5dce25650ea3256e0b5ea3f73cc2a',
                                             'relevant_lines': [[13, 31], [53, 71], [93, 111], [173, 191]]}],
                            'source_options': [{'source_key': 'hajj.3020.a',
                                                'historical_native_index': 0,
                                                'historical_label': '为什么就是七次！',
                                                'effects': ['Requires athletic. Request100piety, '
                                                            'pious_type_option_effect,1year '
                                                            'hajj_pushed_the_marwah_modifier '
                                                            '(stress_gain_mult-0.2, health+0.25), personality '
                                                            'stress/fulfillment inputs.'],
                                                'visibility': 'Source native0 hidden in R42.',
                                                'historical_R31_selected': False},
                                               {'source_key': 'hajj.3020.b',
                                                'historical_native_index': 1,
                                                'historical_label': '认真走完七圈就可以了。',
                                                'effects': ['Request50piety, pious_type_option_effect, log; '
                                                            'personality stress/fulfillment inputs.',
                                                            'R42 this was the only shown option: native1 '
                                                            'submitted once, same-date piety+50, other wallets '
                                                            'and stress unchanged.'],
                                                'visibility': 'R42 rendered0/native1 shown/enabled and '
                                                              'selected; do not replace first displayed with '
                                                              'native0.',
                                                'historical_R31_selected': False},
                                               {'source_key': 'hajj.3020.c',
                                                'historical_native_index': 2,
                                                'historical_label': '会有人注意到我少走了几圈吗？',
                                                'effects': ['Requires lazy. Intrigue duel: success requests '
                                                            'piety-25 and1year hajj_skimp_on_safa_modifier '
                                                            '(stress_gain_mult-0.3); failure schedules '
                                                            'hajj.3021 with its separate immediate penalty. '
                                                            'Compared weights are not a fixed60percent '
                                                            'probability.'],
                                                'visibility': 'Source native2 hidden in R42.',
                                                'historical_R31_selected': False}],
                            'agent_reference': 'After schedule hajj.3030 in15days;3021 is conditional and did '
                                               'not occur in this batch. Reuses existing exact-build source '
                                               'analysis; R42 final failure is preserved. The former nonempty '
                                               'migration placeholder did not prove completed source analysis.',
                            'current_native_legality': None,
                            'action_ready': False,
                            'ordinary_auto_consumes': False,
                            'full_occurrence_contract_registered': False,
                            'selection_policy_changed': False,
                            'historical_index_is_current_selection_permission': False,
                            'historical_evidence_is_current_state': False},
               'observations': {'machine_id': '4-8e1c2f1861',
                                'observed_at_utc': '2026-10-23T11:27:49.554458+00:00',
                                'run_id': '4-8e1c2f1861--faith-engine--R0042',
                                'actual': {'event_instance_id': 13,
                                           'event_definition_key': 'hajj.3020',
                                           'observed_at_utc': '2026-10-23T11:27:49.554458+00:00',
                                           'input': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0042\\case-output\\faith-e02-journey-001-event-13-offline-analysis-input.json',
                                                     'bytes': 68484,
                                                     'sha256': '639f7431631ca37f20c959c5d18b05cdaa663e6cdcbe82afbfd7752cf0b5ae25'},
                                           'date_raw': 51401736,
                                           'knowledge_status': 'unavailable',
                                           'unavailable_reason': 'event_definition_key_not_registered',
                                           'source_analysis_completed': False,
                                           'has_migration_placeholder_only': True,
                                           'selection_observed': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0042\\case-output\\faith-e02-journey-001-event-13-selection-observed.json',
                                                                  'bytes': 74526,
                                                                  'sha256': 'a1ce1bb0c21e88e8043ef48d1ae8ed4d016b66d1bd5f469fe237c82b4784e2d7'},
                                           'selected_native_option_index': 1,
                                           'submission_attempted': True,
                                           'ack_accepted': True,
                                           'old_instance_gone_in_independent_snapshot': True,
                                           'saved_scopes': [{'name': 'activity',
                                                             'name_identifier': 2,
                                                             'scope': {'status': 'available',
                                                                       'raw_type_index': 6,
                                                                       'type_key': 'activity',
                                                                       'subtype': 0,
                                                                       'typed_identity': {'status': 'unavailable',
                                                                                          'reason': 'generic_scope_payload_identity_not_closed'}}},
                                                            {'name': 'host',
                                                             'name_identifier': 62,
                                                             'scope': {'status': 'available',
                                                                       'raw_type_index': 4,
                                                                       'type_key': 'character',
                                                                       'subtype': 0,
                                                                       'typed_identity': {'status': 'available',
                                                                                          'kind': 'character',
                                                                                          'character_id': 15893}}},
                                                            {'name': 'province',
                                                             'name_identifier': 37,
                                                             'scope': {'status': 'available',
                                                                       'raw_type_index': 8,
                                                                       'type_key': 'province',
                                                                       'subtype': 0,
                                                                       'typed_identity': {'status': 'unavailable',
                                                                                          'reason': 'generic_scope_payload_identity_not_closed'}}}],
                                           'displayed_options': [{'rendered_index': 0,
                                                                  'native_option_index': 1,
                                                                  'shown': True,
                                                                  'enabled': True,
                                                                  'resolved_name': '认真走完七圈就可以了。'}],
                                           'before': {'date_raw': 51401736,
                                                      'actor': 15893,
                                                      'stress': 97,
                                                      'played_character_gold': {'raw': 135009623,
                                                                                'scale': 100000},
                                                      'played_character_prestige': {'raw': 16205259,
                                                                                    'scale': 100000},
                                                      'played_character_piety': {'raw': 246942500,
                                                                                 'scale': 100000}},
                                           'after': {'date_raw': 51401736,
                                                     'actor': 15893,
                                                     'stress': 97,
                                                     'played_character_gold': {'raw': 135009623,
                                                                               'scale': 100000},
                                                     'played_character_prestige': {'raw': 16205259,
                                                                                   'scale': 100000},
                                                     'played_character_piety': {'raw': 251942500,
                                                                                'scale': 100000}},
                                           'selection_source': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0042\\case-output\\faith-e02-journey-001-0269-event-select-once.actual-results.json',
                                                                'bytes': 39174,
                                                                'sha256': '2e9114d03f4becf73338c16e3e1edd5d8f5ae9c702462e0f8e10577a6277ab52'},
                                           'input_observed_at_utc': '2026-10-23T11:26:15.667701+00:00'},
                                'policy_actually_used': 'native_first_displayed_v1',
                                'registry_consumption_succeeded_live': False}},
 'hajj.3030': {'analysis': {'source_analysis_completed': True,
                            'migration_review_status': 'source_reviewed_no_occurrence_contract',
                            'exact_build': '1.20.0.4',
                            'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-v5-doctrines-hajj-12004.json',
                            'source_document_sha256': 'a717fc94a06ccc2d90405d28304e2a98d6ab9f9ec531d6a4b4528ba5a8c0c360',
                            'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0042-final-events-occurrence.json',
                            'title': '渗渗泉',
                            'source_pins': [{'game_relative_path': 'common/scripted_effects/00_pilgrimage_effects.txt',
                                             'bytes': 40713,
                                             'sha256': '4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80',
                                             'relevant_lines': [[55, 670],
                                                                [137, 137],
                                                                [240, 240],
                                                                [286, 286],
                                                                [672, 874],
                                                                [1028, 1206],
                                                                [1196, 1196],
                                                                [1197, 1197],
                                                                [1225, 1420]]},
                                            {'game_relative_path': 'events/activities/pilgrimage_activity/hajj_events.txt',
                                             'bytes': 29519,
                                             'sha256': '0e0617fd6a17192a87fcdb21fe07ae896a42c4c1c5e0e93e0f0a7ee3d0fc67c0',
                                             'relevant_lines': [[785, 976]]},
                                            {'game_relative_path': 'common/modifiers/00_activity_pilgrimage_modifiers.txt',
                                             'bytes': 8263,
                                             'sha256': 'b4b087debf7975b02fdc30d3244a04aca634e3e26b2fafa4c42057e71a1c1580',
                                             'relevant_lines': [[3, 26],
                                                                [78, 83],
                                                                [126, 159],
                                                                [308, 320],
                                                                [322, 364]]},
                                            {'game_relative_path': 'common/script_values/00_basic_values.txt',
                                             'bytes': 50566,
                                             'sha256': 'c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef',
                                             'relevant_lines': [[16, 180],
                                                                [451, 455],
                                                                [1131, 1135],
                                                                [1139, 1162],
                                                                [1164, 1168]]},
                                            {'game_relative_path': 'localization/simp_chinese/event_localization/activities/hajj_events_l_simp_chinese.yml',
                                             'bytes': 12384,
                                             'sha256': '96331cb1368c6e889e467b870ec0bb5b46a7736af760434923c02cdadb1a305d',
                                             'relevant_lines': [[58, 58],
                                                                [60, 60],
                                                                [63, 63],
                                                                [65, 65],
                                                                [68, 68],
                                                                [72, 72],
                                                                [74, 74],
                                                                [83, 83],
                                                                [86, 86],
                                                                [88, 88],
                                                                [89, 89],
                                                                [90, 90],
                                                                [95, 95],
                                                                [97, 97],
                                                                [99, 99],
                                                                [101, 101],
                                                                [105, 105],
                                                                [107, 107],
                                                                [109, 109],
                                                                [111, 111],
                                                                [114, 114],
                                                                [116, 116],
                                                                [118, 118],
                                                                [120, 120],
                                                                [122, 122],
                                                                [125, 125],
                                                                [130, 130],
                                                                [131, 131]]},
                                            {'game_relative_path': 'common/script_values/01_dynamic_values.txt',
                                             'bytes': 48201,
                                             'sha256': '023165e7d27d106a34f34d7726d938efa8d5dce25650ea3256e0b5ea3f73cc2a',
                                             'relevant_lines': [[13, 31], [53, 71], [93, 111], [173, 191]]}],
                            'source_options': [{'source_key': 'hajj.3030.a',
                                                'historical_native_index': 0,
                                                'historical_label': '我应该让其他人先饮。',
                                                'effects': ['Requires calm/patient/compassionate. '
                                                            'Request100piety, miniscule prestige loss, '
                                                            'pious_type_option_effect and log.',
                                                            'R42 same-date piety+100 and prestige-35; '
                                                            'gold/stress unchanged. Do not treat the dynamic '
                                                            'prestige amount as universal.'],
                                                'visibility': 'R42 shown/enabled rendered0/native0; selected.',
                                                'historical_R31_selected': False},
                                               {'source_key': 'hajj.3030.b',
                                                'historical_native_index': 1,
                                                'historical_label': '消解我灵魂的干渴！',
                                                'effects': ['Request50piety, pious_type_option_effect and log. '
                                                            'Medical-perk/learning conditions influence '
                                                            'personality stress inputs.'],
                                                'visibility': 'R42 shown/enabled rendered1/native1; not '
                                                              'selected.',
                                                'historical_R31_selected': False},
                                               {'source_key': 'hajj.3030.c',
                                                'historical_native_index': 2,
                                                'historical_label': '也许我该用手稍微蘸一下。',
                                                'effects': ['Requires wash_your_hands, not healthy, learning '
                                                            'at least medium. Request piety-50; conditional '
                                                            'branch5year hygienic modifier (health+0.5, '
                                                            'zealot_opinion-5), or100learningXP, or '
                                                            'conditional health-perk chance; no guaranteed '
                                                            'perk.'],
                                                'visibility': 'Source native2 hidden in R42.',
                                                'historical_R31_selected': False}],
                            'agent_reference': 'After schedule hajj.3040 in15days. Reuses existing exact-build '
                                               'source analysis; R42 final failure is preserved. The former '
                                               'nonempty migration placeholder did not prove completed source '
                                               'analysis.',
                            'current_native_legality': None,
                            'action_ready': False,
                            'ordinary_auto_consumes': False,
                            'full_occurrence_contract_registered': False,
                            'selection_policy_changed': False,
                            'historical_index_is_current_selection_permission': False,
                            'historical_evidence_is_current_state': False},
               'observations': {'machine_id': '4-8e1c2f1861',
                                'observed_at_utc': '2026-10-23T11:32:49.085200+00:00',
                                'run_id': '4-8e1c2f1861--faith-engine--R0042',
                                'actual': {'event_instance_id': 14,
                                           'event_definition_key': 'hajj.3030',
                                           'observed_at_utc': '2026-10-23T11:32:49.085200+00:00',
                                           'input': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0042\\case-output\\faith-e02-journey-001-event-14-offline-analysis-input.json',
                                                     'bytes': 66481,
                                                     'sha256': 'a3272ff4535bad7f5123821d4a1103d31c9a6de01fd437bc5f30856dc229b7bb'},
                                           'date_raw': 51402096,
                                           'knowledge_status': 'unavailable',
                                           'unavailable_reason': 'event_definition_key_not_registered',
                                           'source_analysis_completed': False,
                                           'has_migration_placeholder_only': True,
                                           'selection_observed': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0042\\case-output\\faith-e02-journey-001-event-14-selection-observed.json',
                                                                  'bytes': 72389,
                                                                  'sha256': '035dcce4098201a8cda3d57c4f9e8ab6ee1990a5f78fc4ad3c1d14056b8cdb95'},
                                           'selected_native_option_index': 0,
                                           'submission_attempted': True,
                                           'ack_accepted': True,
                                           'old_instance_gone_in_independent_snapshot': True,
                                           'saved_scopes': [{'name': 'activity',
                                                             'name_identifier': 2,
                                                             'scope': {'status': 'available',
                                                                       'raw_type_index': 6,
                                                                       'type_key': 'activity',
                                                                       'subtype': 0,
                                                                       'typed_identity': {'status': 'unavailable',
                                                                                          'reason': 'generic_scope_payload_identity_not_closed'}}},
                                                            {'name': 'host',
                                                             'name_identifier': 62,
                                                             'scope': {'status': 'available',
                                                                       'raw_type_index': 4,
                                                                       'type_key': 'character',
                                                                       'subtype': 0,
                                                                       'typed_identity': {'status': 'available',
                                                                                          'kind': 'character',
                                                                                          'character_id': 15893}}},
                                                            {'name': 'province',
                                                             'name_identifier': 37,
                                                             'scope': {'status': 'available',
                                                                       'raw_type_index': 8,
                                                                       'type_key': 'province',
                                                                       'subtype': 0,
                                                                       'typed_identity': {'status': 'unavailable',
                                                                                          'reason': 'generic_scope_payload_identity_not_closed'}}}],
                                           'displayed_options': [{'rendered_index': 0,
                                                                  'native_option_index': 0,
                                                                  'shown': True,
                                                                  'enabled': True,
                                                                  'resolved_name': '我应该让其他人先饮。'},
                                                                 {'rendered_index': 1,
                                                                  'native_option_index': 1,
                                                                  'shown': True,
                                                                  'enabled': True,
                                                                  'resolved_name': '消解我灵魂的干渴！'}],
                                           'before': {'date_raw': 51402096,
                                                      'actor': 15893,
                                                      'stress': 97,
                                                      'played_character_gold': {'raw': 135009623,
                                                                                'scale': 100000},
                                                      'played_character_prestige': {'raw': 16205259,
                                                                                    'scale': 100000},
                                                      'played_character_piety': {'raw': 251942500,
                                                                                 'scale': 100000}},
                                           'after': {'date_raw': 51402096,
                                                     'actor': 15893,
                                                     'stress': 97,
                                                     'played_character_gold': {'raw': 135009623,
                                                                               'scale': 100000},
                                                     'played_character_prestige': {'raw': 12705259,
                                                                                   'scale': 100000},
                                                     'played_character_piety': {'raw': 261942500,
                                                                                'scale': 100000}},
                                           'selection_source': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0042\\case-output\\faith-e02-journey-001-0278-event-select-once.actual-results.json',
                                                                'bytes': 37622,
                                                                'sha256': 'a908cd007a3d4021c38d66f1bacb374534408673cf44d6b9506d3d2f675a47f8'},
                                           'input_observed_at_utc': '2026-10-23T11:29:23.142620+00:00'},
                                'policy_actually_used': 'native_first_displayed_v1',
                                'registry_consumption_succeeded_live': False}},
 'hajj.3040': {'analysis': {'source_analysis_completed': True,
                            'migration_review_status': 'source_reviewed_no_occurrence_contract',
                            'exact_build': '1.20.0.4',
                            'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-v5-doctrines-hajj-12004.json',
                            'source_document_sha256': 'a717fc94a06ccc2d90405d28304e2a98d6ab9f9ec531d6a4b4528ba5a8c0c360',
                            'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0042-final-events-occurrence.json',
                            'title': '为安拉宰牲',
                            'source_pins': [{'game_relative_path': 'common/scripted_effects/00_pilgrimage_effects.txt',
                                             'bytes': 40713,
                                             'sha256': '4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80',
                                             'relevant_lines': [[55, 670],
                                                                [137, 137],
                                                                [240, 240],
                                                                [286, 286],
                                                                [672, 874],
                                                                [1028, 1206],
                                                                [1196, 1196],
                                                                [1197, 1197],
                                                                [1225, 1420]]},
                                            {'game_relative_path': 'events/activities/pilgrimage_activity/hajj_events.txt',
                                             'bytes': 29519,
                                             'sha256': '0e0617fd6a17192a87fcdb21fe07ae896a42c4c1c5e0e93e0f0a7ee3d0fc67c0',
                                             'relevant_lines': [[979, 1192]]},
                                            {'game_relative_path': 'common/modifiers/00_activity_pilgrimage_modifiers.txt',
                                             'bytes': 8263,
                                             'sha256': 'b4b087debf7975b02fdc30d3244a04aca634e3e26b2fafa4c42057e71a1c1580',
                                             'relevant_lines': [[3, 26],
                                                                [78, 83],
                                                                [126, 159],
                                                                [308, 320],
                                                                [322, 364]]},
                                            {'game_relative_path': 'common/script_values/00_basic_values.txt',
                                             'bytes': 50566,
                                             'sha256': 'c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef',
                                             'relevant_lines': [[16, 180],
                                                                [451, 455],
                                                                [1131, 1135],
                                                                [1139, 1162],
                                                                [1164, 1168]]},
                                            {'game_relative_path': 'localization/simp_chinese/event_localization/activities/hajj_events_l_simp_chinese.yml',
                                             'bytes': 12384,
                                             'sha256': '96331cb1368c6e889e467b870ec0bb5b46a7736af760434923c02cdadb1a305d',
                                             'relevant_lines': [[58, 58],
                                                                [60, 60],
                                                                [63, 63],
                                                                [65, 65],
                                                                [68, 68],
                                                                [72, 72],
                                                                [74, 74],
                                                                [83, 83],
                                                                [86, 86],
                                                                [88, 88],
                                                                [89, 89],
                                                                [90, 90],
                                                                [95, 95],
                                                                [97, 97],
                                                                [99, 99],
                                                                [101, 101],
                                                                [105, 105],
                                                                [107, 107],
                                                                [109, 109],
                                                                [111, 111],
                                                                [114, 114],
                                                                [116, 116],
                                                                [118, 118],
                                                                [120, 120],
                                                                [122, 122],
                                                                [125, 125],
                                                                [130, 130],
                                                                [131, 131]]},
                                            {'game_relative_path': 'common/script_values/01_dynamic_values.txt',
                                             'bytes': 48201,
                                             'sha256': '023165e7d27d106a34f34d7726d938efa8d5dce25650ea3256e0b5ea3f73cc2a',
                                             'relevant_lines': [[13, 31], [53, 71], [93, 111], [173, 191]]}],
                            'source_options': [{'source_key': 'hajj.3040.a',
                                                'historical_native_index': 0,
                                                'historical_label': '六十三峰骆驼！',
                                                'effects': ['Requires not already hajj_prophet_like_modifier. '
                                                            'Pay dynamic massive_gold_value; request250piety, '
                                                            'major prestige, medium dynasty prestige, '
                                                            'very_pious_type_option_effect, prophet-like '
                                                            'modifier and memory, logscore75.',
                                                            'Prophet-like modifier: clergy_opinion+10, '
                                                            'zealot_opinion+10, monthly_piety_gain_mult+0.05.',
                                                            'R42 same-date actual gold-455, prestige+350, '
                                                            'piety+250; stress unchanged. Dynasty '
                                                            'prestige/modifier/memory/performance were not '
                                                            "read back;455 is this occurrence's payment, not a "
                                                            'fixed Hajj price.'],
                                                'visibility': 'R42 shown/enabled rendered0/native0; selected.',
                                                'historical_R31_selected': False},
                                               {'source_key': 'hajj.3040.b',
                                                'historical_native_index': 1,
                                                'historical_label': '一匹骆驼应该就够多了。',
                                                'effects': ['Pay dynamic medium_gold_value; request100piety '
                                                            'and minor prestige, pious_type_option_effect, '
                                                            'logscore50.10year camel-knowledge modifier '
                                                            '(clergy/zealot '
                                                            'opinion+5,monthly_piety_gain_mult+0.1), or '
                                                            'zealot-vassal opinion if already known.'],
                                                'visibility': 'R42 shown/enabled rendered1/native1; not '
                                                              'selected.',
                                                'historical_R31_selected': False},
                                               {'source_key': 'hajj.3040.c',
                                                'historical_native_index': 2,
                                                'historical_label': '我们用羊吧。',
                                                'effects': ['Pay dynamic minor_gold_value; request50piety, '
                                                            'pious_type_option_effect, logscore50.'],
                                                'visibility': 'R42 shown/enabled rendered2/native2; not '
                                                              'selected.',
                                                'historical_R31_selected': False},
                                               {'source_key': 'hajj.3040.d',
                                                'historical_native_index': 3,
                                                'historical_label': '我会参加那边的宰牛祭。',
                                                'effects': ['Pay dynamic tiny_gold_value; request25piety and '
                                                            'miniscule prestige loss, logscore50; no pious '
                                                            'performance helper in this option.'],
                                                'visibility': 'R42 shown/enabled rendered3/native3; not '
                                                              'selected.',
                                                'historical_R31_selected': False}],
                            'agent_reference': 'After schedule hajj.3001 in10days. Reuses existing exact-build '
                                               'source analysis; R42 final failure is preserved. The former '
                                               'nonempty migration placeholder did not prove completed source '
                                               'analysis.',
                            'current_native_legality': None,
                            'action_ready': False,
                            'ordinary_auto_consumes': False,
                            'full_occurrence_contract_registered': False,
                            'selection_policy_changed': False,
                            'historical_index_is_current_selection_permission': False,
                            'historical_evidence_is_current_state': False},
               'observations': {'machine_id': '4-8e1c2f1861',
                                'observed_at_utc': '2026-10-23T11:37:53.320795+00:00',
                                'run_id': '4-8e1c2f1861--faith-engine--R0042',
                                'actual': {'event_instance_id': 15,
                                           'event_definition_key': 'hajj.3040',
                                           'observed_at_utc': '2026-10-23T11:37:53.320795+00:00',
                                           'input': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0042\\case-output\\faith-e02-journey-001-event-15-offline-analysis-input.json',
                                                     'bytes': 69043,
                                                     'sha256': '317148c19f9f21a1531f6d66afd1f3f5729e3fe7a0f2afb70e3b9c4d6b5b7e86'},
                                           'date_raw': 51402456,
                                           'knowledge_status': 'unavailable',
                                           'unavailable_reason': 'event_definition_key_not_registered',
                                           'source_analysis_completed': False,
                                           'has_migration_placeholder_only': True,
                                           'selection_observed': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0042\\case-output\\faith-e02-journey-001-event-15-selection-observed.json',
                                                                  'bytes': 74502,
                                                                  'sha256': '3f22f9d340b20f39032ae4043c9b49d5fc8a5ddbedb6a10c6e589863fc612b4a'},
                                           'selected_native_option_index': 0,
                                           'submission_attempted': True,
                                           'ack_accepted': True,
                                           'old_instance_gone_in_independent_snapshot': True,
                                           'saved_scopes': [{'name': 'activity',
                                                             'name_identifier': 2,
                                                             'scope': {'status': 'available',
                                                                       'raw_type_index': 6,
                                                                       'type_key': 'activity',
                                                                       'subtype': 0,
                                                                       'typed_identity': {'status': 'unavailable',
                                                                                          'reason': 'generic_scope_payload_identity_not_closed'}}},
                                                            {'name': 'host',
                                                             'name_identifier': 62,
                                                             'scope': {'status': 'available',
                                                                       'raw_type_index': 4,
                                                                       'type_key': 'character',
                                                                       'subtype': 0,
                                                                       'typed_identity': {'status': 'available',
                                                                                          'kind': 'character',
                                                                                          'character_id': 15893}}},
                                                            {'name': 'province',
                                                             'name_identifier': 37,
                                                             'scope': {'status': 'available',
                                                                       'raw_type_index': 8,
                                                                       'type_key': 'province',
                                                                       'subtype': 0,
                                                                       'typed_identity': {'status': 'unavailable',
                                                                                          'reason': 'generic_scope_payload_identity_not_closed'}}},
                                                            {'name': 'root_scope',
                                                             'name_identifier': 9386,
                                                             'scope': {'status': 'available',
                                                                       'raw_type_index': 4,
                                                                       'type_key': 'character',
                                                                       'subtype': 0,
                                                                       'typed_identity': {'status': 'available',
                                                                                          'kind': 'character',
                                                                                          'character_id': 15893}}}],
                                           'displayed_options': [{'rendered_index': 0,
                                                                  'native_option_index': 0,
                                                                  'shown': True,
                                                                  'enabled': True,
                                                                  'resolved_name': '六十三峰骆驼！'},
                                                                 {'rendered_index': 1,
                                                                  'native_option_index': 1,
                                                                  'shown': True,
                                                                  'enabled': True,
                                                                  'resolved_name': '一匹骆驼应该就够多了。'},
                                                                 {'rendered_index': 2,
                                                                  'native_option_index': 2,
                                                                  'shown': True,
                                                                  'enabled': True,
                                                                  'resolved_name': '我们用羊吧。'},
                                                                 {'rendered_index': 3,
                                                                  'native_option_index': 3,
                                                                  'shown': True,
                                                                  'enabled': True,
                                                                  'resolved_name': '我会参加那边的宰牛祭。'}],
                                           'before': {'date_raw': 51402456,
                                                      'actor': 15893,
                                                      'stress': 97,
                                                      'played_character_gold': {'raw': 136598844,
                                                                                'scale': 100000},
                                                      'played_character_prestige': {'raw': 13476285,
                                                                                    'scale': 100000},
                                                      'played_character_piety': {'raw': 262136750,
                                                                                 'scale': 100000}},
                                           'after': {'date_raw': 51402456,
                                                     'actor': 15893,
                                                     'stress': 97,
                                                     'played_character_gold': {'raw': 91098844,
                                                                               'scale': 100000},
                                                     'played_character_prestige': {'raw': 48476285,
                                                                                   'scale': 100000},
                                                     'played_character_piety': {'raw': 287136750,
                                                                                'scale': 100000}},
                                           'selection_source': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0042\\case-output\\faith-e02-journey-001-0287-event-select-once.actual-results.json',
                                                                'bytes': 37626,
                                                                'sha256': 'a35a2b2c0504368d16dee34ca3104ce1319a93291c88f8efa787c53c15d59b1e'},
                                           'input_observed_at_utc': '2026-10-23T11:34:27.883318+00:00'},
                                'policy_actually_used': 'native_first_displayed_v1',
                                'registry_consumption_succeeded_live': False}},
 'hajj.3001': {'analysis': {'source_analysis_completed': True,
                            'migration_review_status': 'source_reviewed_no_occurrence_contract',
                            'exact_build': '1.20.0.4',
                            'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-v5-doctrines-hajj-12004.json',
                            'source_document_sha256': 'a717fc94a06ccc2d90405d28304e2a98d6ab9f9ec531d6a4b4528ba5a8c0c360',
                            'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0042-final-events-occurrence.json',
                            'title': '剃发',
                            'source_pins': [{'game_relative_path': 'common/scripted_effects/00_pilgrimage_effects.txt',
                                             'bytes': 40713,
                                             'sha256': '4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80',
                                             'relevant_lines': [[55, 670],
                                                                [137, 137],
                                                                [240, 240],
                                                                [286, 286],
                                                                [672, 874],
                                                                [1028, 1206],
                                                                [1196, 1196],
                                                                [1197, 1197],
                                                                [1225, 1420]]},
                                            {'game_relative_path': 'events/activities/pilgrimage_activity/hajj_events.txt',
                                             'bytes': 29519,
                                             'sha256': '0e0617fd6a17192a87fcdb21fe07ae896a42c4c1c5e0e93e0f0a7ee3d0fc67c0',
                                             'relevant_lines': [[1195, 1317]]},
                                            {'game_relative_path': 'common/modifiers/00_activity_pilgrimage_modifiers.txt',
                                             'bytes': 8263,
                                             'sha256': 'b4b087debf7975b02fdc30d3244a04aca634e3e26b2fafa4c42057e71a1c1580',
                                             'relevant_lines': [[3, 26],
                                                                [78, 83],
                                                                [126, 159],
                                                                [308, 320],
                                                                [322, 364]]},
                                            {'game_relative_path': 'common/script_values/00_basic_values.txt',
                                             'bytes': 50566,
                                             'sha256': 'c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef',
                                             'relevant_lines': [[16, 180],
                                                                [451, 455],
                                                                [1131, 1135],
                                                                [1139, 1162],
                                                                [1164, 1168]]},
                                            {'game_relative_path': 'localization/simp_chinese/event_localization/activities/hajj_events_l_simp_chinese.yml',
                                             'bytes': 12384,
                                             'sha256': '96331cb1368c6e889e467b870ec0bb5b46a7736af760434923c02cdadb1a305d',
                                             'relevant_lines': [[58, 58],
                                                                [60, 60],
                                                                [63, 63],
                                                                [65, 65],
                                                                [68, 68],
                                                                [72, 72],
                                                                [74, 74],
                                                                [83, 83],
                                                                [86, 86],
                                                                [88, 88],
                                                                [89, 89],
                                                                [90, 90],
                                                                [95, 95],
                                                                [97, 97],
                                                                [99, 99],
                                                                [101, 101],
                                                                [105, 105],
                                                                [107, 107],
                                                                [109, 109],
                                                                [111, 111],
                                                                [114, 114],
                                                                [116, 116],
                                                                [118, 118],
                                                                [120, 120],
                                                                [122, 122],
                                                                [125, 125],
                                                                [130, 130],
                                                                [131, 131]]},
                                            {'game_relative_path': 'common/script_values/01_dynamic_values.txt',
                                             'bytes': 48201,
                                             'sha256': '023165e7d27d106a34f34d7726d938efa8d5dce25650ea3256e0b5ea3f73cc2a',
                                             'relevant_lines': [[13, 31], [53, 71], [93, 111], [173, 191]]}],
                            'source_options': [{'source_key': 'hajj.3001.a',
                                                'historical_native_index': 0,
                                                'historical_label': '全部剪掉！',
                                                'effects': ['Requires dominant gender or gender-equal current '
                                                            'Rite. Request pious_type_option_effect; add '
                                                            'host6month hajj_halq_modifier: '
                                                            'monthly_piety+5,same_faith_opinion+5,attraction_opinion-10; '
                                                            'logscore50.',
                                                            'Cynical/arrogant/beauty traits minor stress gain '
                                                            'inputs, humble minor loss input. R42 same-date '
                                                            'wallets/stress unchanged; modifier membership was '
                                                            'not read back.'],
                                                'visibility': 'R42 shown/enabled rendered0/native0; selected.',
                                                'historical_R31_selected': False},
                                               {'source_key': 'hajj.3001.b',
                                                'historical_native_index': 1,
                                                'historical_label': '只剪一缕。',
                                                'effects': ['Logscore50; non-dominant gender under '
                                                            'opposite-sex dominant Rite receives miniscule '
                                                            'piety gain (+25source value), otherwise minor '
                                                            'piety loss(-50source value). Zealous medium and '
                                                            'humble minor stress gain inputs.'],
                                                'visibility': 'R42 shown/enabled rendered1/native1; not '
                                                              'selected.',
                                                'historical_R31_selected': False}],
                            'agent_reference': 'After progress_activity_phase_after weeks1; this permits '
                                               'phase-end consumers to award Hajjaj. Choosing hair option '
                                               'itself is not add_trait=hajjaj. Reuses existing exact-build '
                                               'source analysis; R42 final failure is preserved. The former '
                                               'nonempty migration placeholder did not prove completed source '
                                               'analysis.',
                            'current_native_legality': None,
                            'action_ready': False,
                            'ordinary_auto_consumes': False,
                            'full_occurrence_contract_registered': False,
                            'selection_policy_changed': False,
                            'historical_index_is_current_selection_permission': False,
                            'historical_evidence_is_current_state': False},
               'observations': {'machine_id': '4-8e1c2f1861',
                                'observed_at_utc': '2026-10-23T11:42:04.784234+00:00',
                                'run_id': '4-8e1c2f1861--faith-engine--R0042',
                                'actual': {'event_instance_id': 16,
                                           'event_definition_key': 'hajj.3001',
                                           'observed_at_utc': '2026-10-23T11:42:04.784234+00:00',
                                           'input': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0042\\case-output\\faith-e02-journey-001-event-16-offline-analysis-input.json',
                                                     'bytes': 67138,
                                                     'sha256': '240a68260f35766355697f41889ec57e56c93920e33e19725ba88e5cd362e994'},
                                           'date_raw': 51402696,
                                           'knowledge_status': 'unavailable',
                                           'unavailable_reason': 'event_definition_key_not_registered',
                                           'source_analysis_completed': False,
                                           'has_migration_placeholder_only': True,
                                           'selection_observed': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0042\\case-output\\faith-e02-journey-001-event-16-selection-observed.json',
                                                                  'bytes': 72511,
                                                                  'sha256': '8ca417564193a62d9c6a5e6186729779790dec6fa4852d05eb3a1416af05f33a'},
                                           'selected_native_option_index': 0,
                                           'submission_attempted': True,
                                           'ack_accepted': True,
                                           'old_instance_gone_in_independent_snapshot': True,
                                           'saved_scopes': [{'name': 'activity',
                                                             'name_identifier': 2,
                                                             'scope': {'status': 'available',
                                                                       'raw_type_index': 6,
                                                                       'type_key': 'activity',
                                                                       'subtype': 0,
                                                                       'typed_identity': {'status': 'unavailable',
                                                                                          'reason': 'generic_scope_payload_identity_not_closed'}}},
                                                            {'name': 'host',
                                                             'name_identifier': 62,
                                                             'scope': {'status': 'available',
                                                                       'raw_type_index': 4,
                                                                       'type_key': 'character',
                                                                       'subtype': 0,
                                                                       'typed_identity': {'status': 'available',
                                                                                          'kind': 'character',
                                                                                          'character_id': 15893}}},
                                                            {'name': 'province',
                                                             'name_identifier': 37,
                                                             'scope': {'status': 'available',
                                                                       'raw_type_index': 8,
                                                                       'type_key': 'province',
                                                                       'subtype': 0,
                                                                       'typed_identity': {'status': 'unavailable',
                                                                                          'reason': 'generic_scope_payload_identity_not_closed'}}},
                                                            {'name': 'root_scope',
                                                             'name_identifier': 9386,
                                                             'scope': {'status': 'available',
                                                                       'raw_type_index': 4,
                                                                       'type_key': 'character',
                                                                       'subtype': 0,
                                                                       'typed_identity': {'status': 'available',
                                                                                          'kind': 'character',
                                                                                          'character_id': 15893}}},
                                                            {'name': 'new_memory',
                                                             'name_identifier': 210,
                                                             'scope': {'status': 'available',
                                                                       'raw_type_index': 34,
                                                                       'type_key': 'character_memory',
                                                                       'subtype': 0,
                                                                       'typed_identity': {'status': 'unavailable',
                                                                                          'reason': 'generic_scope_payload_identity_not_closed'}}}],
                                           'displayed_options': [{'rendered_index': 0,
                                                                  'native_option_index': 0,
                                                                  'shown': True,
                                                                  'enabled': True,
                                                                  'resolved_name': '全部剪掉！'},
                                                                 {'rendered_index': 1,
                                                                  'native_option_index': 1,
                                                                  'shown': True,
                                                                  'enabled': True,
                                                                  'resolved_name': '只剪一缕。'}],
                                           'before': {'date_raw': 51402696,
                                                      'actor': 15893,
                                                      'stress': 97,
                                                      'played_character_gold': {'raw': 91098844,
                                                                                'scale': 100000},
                                                      'played_character_prestige': {'raw': 48476285,
                                                                                    'scale': 100000},
                                                      'played_character_piety': {'raw': 288636750,
                                                                                 'scale': 100000}},
                                           'after': {'date_raw': 51402696,
                                                     'actor': 15893,
                                                     'stress': 97,
                                                     'played_character_gold': {'raw': 91098844,
                                                                               'scale': 100000},
                                                     'played_character_prestige': {'raw': 48476285,
                                                                                   'scale': 100000},
                                                     'played_character_piety': {'raw': 288636750,
                                                                                'scale': 100000}},
                                           'selection_source': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0042\\case-output\\faith-e02-journey-001-0294-event-select-once.actual-results.json',
                                                                'bytes': 37625,
                                                                'sha256': '5c2a96d7e745862a199d1256e62f9f74a0c71d061493358c1137dfffc4a29cc9'},
                                           'input_observed_at_utc': '2026-10-23T11:39:02.771884+00:00'},
                                'policy_actually_used': 'native_first_displayed_v1',
                                'registry_consumption_succeeded_live': False}},
 'pilgrimage.7000': {'analysis': {'source_analysis_completed': True,
                                  'migration_review_status': 'source_reviewed_no_occurrence_contract',
                                  'exact_build': '1.20.0.4',
                                  'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-7000-source-analysis.json',
                                  'source_document_sha256': '414aca26d0e16b15bc2ac9e6b5bebbdd78229154fb84744d6f8ec8fa67b4a3c9',
                                  'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0042-final-events-occurrence.json',
                                  'title': '目的地完成总结',
                                  'source_pins': [{'game_relative_path': 'events/activities/pilgrimage_activity/pilgrimage_events.txt',
                                                   'bytes': 358138,
                                                   'sha256': '900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06',
                                                   'relevant_lines': [[13303, 13678], [14725, 15147]]},
                                                  {'game_relative_path': 'localization/simp_chinese/event_localization/activities/pilgrimage_events_l_simp_chinese.yml',
                                                   'bytes': 136481,
                                                   'sha256': 'cecb7052ac6672f1fd99a0008a8e7d6ccca474069a17e8a9902c55571cd272b3',
                                                   'relevant_lines': [[899, 907], [973, 977]]},
                                                  {'game_relative_path': 'common/activities/activity_types/pilgrimage.txt',
                                                   'bytes': 111931,
                                                   'sha256': '24153043485b035cb0477de7306649027cb68c039e4a9d903776eddd870d8b9f',
                                                   'relevant_lines': [[2544, 2579], [2906, 2907]]},
                                                  {'game_relative_path': 'common/scripted_effects/00_pilgrimage_effects.txt',
                                                   'bytes': 40713,
                                                   'sha256': '4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80',
                                                   'relevant_lines': [[55, 91],
                                                                      [516, 627],
                                                                      [1028, 1120],
                                                                      [1136, 1169],
                                                                      [1301, 1335]]},
                                                  {'game_relative_path': 'common/on_action/activities/pilgrimage_on_actions.txt',
                                                   'bytes': 11904,
                                                   'sha256': 'fdf71f074882f94eb3df497a1ddb2cb9a95fb13e973aebf25d4c3569729ee354',
                                                   'relevant_lines': [[379, 401]]},
                                                  {'game_relative_path': 'common/script_values/00_basic_values.txt',
                                                   'bytes': 50566,
                                                   'sha256': 'c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef',
                                                   'relevant_lines': [[1131, 1136], [1164, 1169]]}],
                                  'source_options': [{'source_key': 'pilgrimage.7000.a_hajj',
                                                      'historical_native_index': 0,
                                                      'historical_label': '来到麦加是一种荣幸。',
                                                      'effects': ['This source option has name variants '
                                                                  'a_hajj_cynical/a_hajj/a_cynical/a. It shows '
                                                                  'custom tooltip and show_as_tooltip '
                                                                  'pilgrimage_completed_log_entry_effect; the '
                                                                  'main reward has already been resolved by '
                                                                  'phase-end consumers and is not awarded '
                                                                  'again by clicking this tooltip option.',
                                                                  'R42 instance17 was displayed only. No '
                                                                  'submission, ACK or independent '
                                                                  'disappearance occurred before original host '
                                                                  'failure; no completion/return credit.'],
                                                      'visibility': 'R42 only rendered0/native0 shown/enabled; '
                                                                    'never selected.',
                                                      'historical_R31_selected': False},
                                                     {'source_key': 'pilgrimage.7000.b',
                                                      'historical_native_index': 1,
                                                      'historical_label': 'Source conditional Gallowsbait '
                                                                          'reduction option; not shown in R42',
                                                      'effects': ['Requires EP3,gallowsbait with XP and pious '
                                                                  'or Hajj activity. Depending on source '
                                                                  'Pilgrim-XP50/high-or-perfect pious '
                                                                  'conditions remove gallowsbait, otherwise '
                                                                  'lower gallowsbaitXP25; completed-reward '
                                                                  'tooltip only.'],
                                                      'visibility': 'Source native1 hidden in R42.',
                                                      'historical_R31_selected': False}],
                                  'agent_reference': 'Immediate may create conditional Christian saint-bone '
                                                     'artifact, localization memory scopes/old-host scope or '
                                                     'increment existing repent_oath_pilgrimage_counter. After '
                                                     'selection cleans reward flags. Neither stage was '
                                                     'independently proven in R42. Hajjaj-award source '
                                                     'consumer is phase-end completion log '
                                                     '->give_hajj_trait_or_xp_effect, not option0. Preserve '
                                                     'R42 original shared-host failure, no ReturnSave and no '
                                                     'replay.',
                                  'current_native_legality': None,
                                  'action_ready': False,
                                  'ordinary_auto_consumes': False,
                                  'full_occurrence_contract_registered': False,
                                  'selection_policy_changed': False,
                                  'historical_index_is_current_selection_permission': False,
                                  'historical_evidence_is_current_state': False},
                     'observations': {'machine_id': '4-8e1c2f1861',
                                      'observed_at_utc': '2026-10-23T11:42:48.422008+00:00',
                                      'run_id': '4-8e1c2f1861--faith-engine--R0042',
                                      'actual': {'event_instance_id': 17,
                                                 'event_definition_key': 'pilgrimage.7000',
                                                 'observed_at_utc': '2026-10-23T11:42:48.422008+00:00',
                                                 'input': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0042\\case-output\\faith-e02-journey-001-event-17-offline-analysis-input.json',
                                                           'bytes': 65642,
                                                           'sha256': '07ddd59db592e9ff444412b123cadfac81dc7e62b41142bb8847dee8892cd725'},
                                                 'date_raw': 51402864,
                                                 'knowledge_status': 'unavailable',
                                                 'unavailable_reason': 'event_definition_key_not_registered',
                                                 'source_analysis_completed': False,
                                                 'has_migration_placeholder_only': True,
                                                 'selection_observed': None,
                                                 'selected_native_option_index': None,
                                                 'submission_attempted': False,
                                                 'ack_accepted': None,
                                                 'old_instance_gone_in_independent_snapshot': None,
                                                 'saved_scopes': [{'name': 'activity',
                                                                   'name_identifier': 2,
                                                                   'scope': {'status': 'available',
                                                                             'raw_type_index': 6,
                                                                             'type_key': 'activity',
                                                                             'subtype': 0,
                                                                             'typed_identity': {'status': 'unavailable',
                                                                                                'reason': 'generic_scope_payload_identity_not_closed'}}},
                                                                  {'name': 'host',
                                                                   'name_identifier': 62,
                                                                   'scope': {'status': 'available',
                                                                             'raw_type_index': 4,
                                                                             'type_key': 'character',
                                                                             'subtype': 0,
                                                                             'typed_identity': {'status': 'available',
                                                                                                'kind': 'character',
                                                                                                'character_id': 15893}}},
                                                                  {'name': 'province',
                                                                   'name_identifier': 37,
                                                                   'scope': {'status': 'available',
                                                                             'raw_type_index': 8,
                                                                             'type_key': 'province',
                                                                             'subtype': 0,
                                                                             'typed_identity': {'status': 'unavailable',
                                                                                                'reason': 'generic_scope_payload_identity_not_closed'}}}],
                                                 'displayed_options': [{'rendered_index': 0,
                                                                        'native_option_index': 0,
                                                                        'shown': True,
                                                                        'enabled': True,
                                                                        'resolved_name': '来到麦加是一种荣幸。'}],
                                                 'before': {'date_raw': 51402864,
                                                            'actor': 15893,
                                                            'stress': 97,
                                                            'played_character_gold': {'raw': 91098844,
                                                                                      'scale': 100000},
                                                            'played_character_prestige': {'raw': 48476285,
                                                                                          'scale': 100000},
                                                            'played_character_piety': {'raw': 326136750,
                                                                                       'scale': 100000}},
                                                 'after': None,
                                                 'input_observed_at_utc': '2026-10-23T11:42:48.422008+00:00',
                                                 'milestone_before_option': {'packet': {'path': 'C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261023-a02/live/4-8e1c2f1861--faith-engine--R0042/case-output/ordinary-pilgrimage-milestone-13-faith-e02-journey-001-pilgrimage-7000-17-window.json',
                                                                                        'bytes': 5417,
                                                                                        'sha256': '88c69b9b355df759f8557fd7879b923b547168345e77b0e7d66c1aa82f433ab8'},
                                                                             'query_source': {'path': 'C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261023-a02/live/4-8e1c2f1861--faith-engine--R0042/case-output/ordinary-pilgrimage-milestone-13-faith-e02-journey-001-pilgrimage-7000-17-window.actual-results.json',
                                                                                              'bytes': 62522,
                                                                                              'sha256': '5ca84a3e1ff4f3df28bed7b49a0c0ddc5823eab38aa329278b080bc29ef90b18'},
                                                                             'actual': {'definition_key': 'pilgrimage.7000',
                                                                                        'instance_id': 17,
                                                                                        'actor_id': 15893,
                                                                                        'date_raw': 51402864,
                                                                                        'capture_epoch': '513101',
                                                                                        'hajjaj': True,
                                                                                        'pilgrim': False,
                                                                                        'trait_query_available': True,
                                                                                        'location_query_available': False,
                                                                                        'submission_attempted': False,
                                                                                        'ack_accepted': None,
                                                                                        'old_instance_gone': None,
                                                                                        'return_save': False},
                                                                             'boundary': 'Trait presence is a '
                                                                                         'native observation '
                                                                                         'before option0. This '
                                                                                         'does not prove '
                                                                                         'clicking7000 awarded '
                                                                                         'the trait, a normal '
                                                                                         'host close, return, '
                                                                                         'or dual traits.'}},
                                      'policy_actually_used': 'native_first_displayed_v1',
                                      'registry_consumption_succeeded_live': False}}}

PILGRIMAGE_TRAVEL_SOURCE_ONLY_12004.update(_R0042_SOURCE_ONLY)


_R0044_SOURCE_ONLY: dict[str, SourceOnlyRecord] = {'pilgrimage.9001': {'analysis': {'source_analysis_completed': True,
                                  'migration_review_status': 'source_reviewed_no_occurrence_contract',
                                  'exact_build': '1.20.0.4',
                                  'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-9001-source-analysis.json',
                                  'source_document_sha256': '0b1ff25113c1804bc2513bf1a45e8e9c17a81505b902b9b50ffcc8cb316f5d24',
                                  'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0044-events-occurrence.json',
                                  'title': 'Pilgrimage return: source-reviewed end-of-journey acknowledgment',
                                  'source_pins': [{'game_relative_path': 'events/activities/pilgrimage_activity/pilgrimage_events.txt',
                                                   'bytes': 358138,
                                                   'sha256': '900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06',
                                                   'relevant_lines': [[15160, 15280]]},
                                                  {'game_relative_path': 'common/on_action/travel_on_actions.txt',
                                                   'bytes': 71526,
                                                   'sha256': 'cd40f30a9280ea9ba656b59005201550f3991afd646fd686d7474657b1b1ff70',
                                                   'relevant_lines': [[1464, 1475]]},
                                                  {'game_relative_path': 'localization/simp_chinese/event_localization/activities/pilgrimage_events_l_simp_chinese.yml',
                                                   'bytes': 136481,
                                                   'sha256': 'cecb7052ac6672f1fd99a0008a8e7d6ccca474069a17e8a9902c55571cd272b3',
                                                   'relevant_lines': [[982, 989]]}],
                                  'source_options': [{'source_key': 'pilgrimage.9001.a',
                                                      'historical_native_index': 0,
                                                      'historical_label': '回家真好。',
                                                      'effects': ['custom tooltip: journey has ended; not '
                                                                  'another main pilgrimage reward execution',
                                                                  'Immediate/after effects are conditional and '
                                                                  'not another Pilgrim/Hajjaj main reward '
                                                                  'execution.'],
                                                      'visibility': 'One source option; a_invalidated/a name '
                                                                    'variants. R44 only rendered0/native0 '
                                                                    'shown/enabled.',
                                                      'historical_R31_selected': False}],
                                  'agent_reference': 'Read analyzed source plus fresh native context; known '
                                                     'qualified policy first, otherwise actual current first '
                                                     'shown. Do not replay return or assume hidden follow-up '
                                                     'occurred. Hook can also complete through script; no '
                                                     'coordinate-home or travel-flag-clear inference. Preserve '
                                                     'conditional immediate rank-up/Horse XP and after '
                                                     'cleanup/9010/9100 as source requests, not observed '
                                                     'results.',
                                  'current_native_legality': None,
                                  'action_ready': False,
                                  'ordinary_auto_consumes': False,
                                  'full_occurrence_contract_registered': False,
                                  'selection_policy_changed': False,
                                  'historical_index_is_current_selection_permission': False,
                                  'historical_evidence_is_current_state': False},
                     'observations': {'machine_id': '4-8e1c2f1861',
                                      'observed_at_utc': '2026-10-23T20:26:47.695151+00:00',
                                      'run_id': '4-8e1c2f1861--faith-engine--R0044',
                                      'actual': {'event_instance_id': 22,
                                                 'event_definition_key': 'pilgrimage.9001',
                                                 'observed_at_utc': '2026-10-23T20:26:47.695151+00:00',
                                                 'selected_option_number': 1,
                                                 'selected_native_option_index': 0,
                                                 'submission_attempted': True,
                                                 'ack_accepted': True,
                                                 'old_instance_gone_in_independent_snapshot': True,
                                                 'date_raw': 51407520,
                                                 'input': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0044\\case-output\\faith-e02-journey-001-event-22-offline-analysis-input.json',
                                                           'bytes': 71467,
                                                           'sha256': '0b3b3683246d95baf5cd6138e518edf252ed3e76f23ae9d2a9f35cc007cc324e'},
                                                 'intent': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0044\\case-output\\faith-e02-journey-001-event-22-selection-intent.json',
                                                            'bytes': 74543,
                                                            'sha256': 'aa0db425d539411dbedebdc27137818d0a2912e9a3ea4d37880e04c321a65e58'},
                                                 'selection_observed': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0044\\case-output\\faith-e02-journey-001-event-22-selection-observed.json',
                                                                        'bytes': 77916,
                                                                        'sha256': 'c49fcc3d233096f513937b7f776f48a1ea92a6a37cd251ed1729b27cb46da2de'},
                                                 'selection_source': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0044\\case-output\\faith-e02-journey-001-0188-event-select-once.actual-results.json',
                                                                      'bytes': 41466,
                                                                      'sha256': '181d4242f056c5c46b6732eb310163dd41e2a5b4757407e203aaa021d0cf26cd'},
                                                 'saved_scopes': [{'name': 'travel_plan',
                                                                   'name_identifier': 211,
                                                                   'scope': {'status': 'available',
                                                                             'raw_type_index': 35,
                                                                             'type_key': 'travel_plan',
                                                                             'subtype': 0,
                                                                             'typed_identity': {'status': 'unavailable',
                                                                                                'reason': 'generic_scope_payload_identity_not_closed'}}},
                                                                  {'name': 'travel_owner',
                                                                   'name_identifier': 44217,
                                                                   'scope': {'status': 'available',
                                                                             'raw_type_index': 4,
                                                                             'type_key': 'character',
                                                                             'subtype': 0,
                                                                             'typed_identity': {'status': 'available',
                                                                                                'kind': 'character',
                                                                                                'character_id': 15893}}}],
                                                 'before': {'date_raw': 51407520,
                                                            'revision': 558,
                                                            'native_revision': 557,
                                                            'played_character_gold': {'raw': 94915142,
                                                                                      'scale': 100000},
                                                            'played_character_prestige': {'raw': 51271234,
                                                                                          'scale': 100000},
                                                            'played_character_piety': {'raw': 341895800,
                                                                                       'scale': 100000},
                                                            'active_event': {'source': 'native',
                                                                             'instance_id': 22,
                                                                             'option_count': 1,
                                                                             'title': None,
                                                                             'options': [{'index': 0,
                                                                                          'option_number': 1,
                                                                                          'label': None,
                                                                                          'enabled': True}]},
                                                            'actor': 15893,
                                                            'stress': 0},
                                                 'after': {'date_raw': 51407520,
                                                           'revision': 559,
                                                           'native_revision': 558,
                                                           'played_character_gold': {'raw': 94915142,
                                                                                     'scale': 100000},
                                                           'played_character_prestige': {'raw': 51271234,
                                                                                         'scale': 100000},
                                                           'played_character_piety': {'raw': 341895800,
                                                                                      'scale': 100000},
                                                           'active_event': None,
                                                           'actor': 15893,
                                                           'stress': 0}},
                                      'policy_actually_used': 'native_first_displayed_v1',
                                      'registry_consumption_succeeded_live': False}}}

PILGRIMAGE_TRAVEL_SOURCE_ONLY_12004.update(_R0044_SOURCE_ONLY)


_R0046_SOURCE_ONLY: dict[str, SourceOnlyRecord] = {'travel_events.4020': {'analysis': {'source_analysis_completed': True,
                                     'migration_review_status': 'source_reviewed_no_occurrence_contract',
                                     'exact_build': '1.20.0.4',
                                     'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0046-events-source-analysis-12004.json',
                                     'source_document_sha256': '73bf38a6eb843e1d3a7c11a29d4c0dedc8cb6f9e321f06ad3e1108404e51f7e3',
                                     'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0046-events-occurrence.json',
                                     'title': '外来者：当地宗教热忱者索取通行赎罪',
                                     'source_pins': [{'game_relative_path': 'events/travel_events/travel_events_james.txt',
                                                      'bytes': 175108,
                                                      'sha256': '68c3306f533d6bb285b9e3e82665be57a588879820e387bfd2045563e643da1a',
                                                      'relevant_lines': [[3637, 3793]]},
                                                     {'game_relative_path': 'localization/simp_chinese/event_localization/travel_events/travel_events_l_simp_chinese.yml',
                                                      'bytes': 56854,
                                                      'sha256': 'fac480f9b6051fbeebe114244b60c6b03d6027423f38076cc9109b0c2ded4f58',
                                                      'relevant_lines': [[166, 183]]},
                                                     {'game_relative_path': 'common/script_values/00_basic_values.txt',
                                                      'bytes': 50566,
                                                      'sha256': 'c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef',
                                                      'relevant_lines': [[1131, 1166]]},
                                                     {'game_relative_path': 'common/script_values/01_dynamic_values.txt',
                                                      'bytes': 48201,
                                                      'sha256': '023165e7d27d106a34f34d7726d938efa8d5dce25650ea3256e0b5ea3f73cc2a',
                                                      'relevant_lines': [[53, 71]]}],
                                     'source_options': [{'source_key': 'travel_events.4020.a',
                                                         'historical_native_index': 0,
                                                         'historical_label': '愚蠢的男人，你才是异端！',
                                                         'effects': ['Learning duel against saved '
                                                                     'strong_believer_scope; two base '
                                                                     'weights50 modified by duel_value '
                                                                     'multipliers+3.5/-3.5, not a '
                                                                     'fixed50-percent outcome.',
                                                                     'Winning toast requests '
                                                                     'medium_piety_gain (+100 base piety). '
                                                                     'Losing toast requests '
                                                                     'medium_piety_loss (-100 base piety) '
                                                                     'and '
                                                                     'remove_short_term_gold=minor_gold_value.',
                                                                     'Cynical/humble medium '
                                                                     'stress-and-fulfillment gain. Actual '
                                                                     'net wallet/stress is separately '
                                                                     'recorded.'],
                                                         'visibility': 'Unconditional source option; R46 '
                                                                       'rendered0/native0 shown/enabled and '
                                                                       'selected.',
                                                         'historical_R31_selected': False},
                                                        {'source_key': 'travel_events.4020.b',
                                                         'historical_native_index': 1,
                                                         'historical_label': '最好还是交钱了事。',
                                                         'effects': ['remove_short_term_gold=minor_gold_value, '
                                                                     'a dynamic value.',
                                                                     'Arrogant/greedy medium and zealous '
                                                                     'major stress-and-fulfillment gain. AI '
                                                                     'affordability weights are not a '
                                                                     'current player-legality grant.'],
                                                         'visibility': 'Unconditional source option; R46 '
                                                                       'rendered1/native1 shown/enabled, '
                                                                       'unselected.',
                                                         'historical_R31_selected': False},
                                                        {'source_key': 'travel_events.4020.c',
                                                         'historical_native_index': 2,
                                                         'historical_label': '源条件选项：烧死这群疯子。',
                                                         'effects': ['Saved strong_believer_scope death '
                                                                     'request, killer=root, '
                                                                     'death_reason=death_burned_witch.',
                                                                     'Sadistic/callous/zealous medium stress '
                                                                     'loss; compassionate/just/calm major '
                                                                     'stress gain.'],
                                                         'visibility': 'Requires '
                                                                       'sadistic/wrathful/impatient/zealous; '
                                                                       'not shown in R46.',
                                                         'historical_R31_selected': False}],
                                     'agent_reference': 'Source3637-3793: ten-year event cooldown, requires '
                                                        'available travelling playable actor on land in '
                                                        'other-religion county with zealous_people '
                                                        'tradition. Immediate requests small '
                                                        'wayfarer-storyteller fame, creates scholar '
                                                        'local-faith/rite character44666 in R46, and '
                                                        'select_local_animal_effect(TYPE=prowling). After '
                                                        'requests silent_disappearance_ai_if_created_effect '
                                                        'on believer. R46 selecteda, ACK and independent '
                                                        'gone, wallet-15gold/-100piety; consistent with loss '
                                                        'branch but no independent duel-toast observation. '
                                                        'No hidden character disappearance/fame outcome '
                                                        'claimed.',
                                     'current_native_legality': None,
                                     'action_ready': False,
                                     'ordinary_auto_consumes': False,
                                     'full_occurrence_contract_registered': False,
                                     'selection_policy_changed': False,
                                     'historical_index_is_current_selection_permission': False,
                                     'historical_evidence_is_current_state': False},
                        'observations': {'machine_id': '4-8e1c2f1861',
                                         'observed_at_utc': '2026-10-23T23:45:53.289463+00:00',
                                         'run_id': '4-8e1c2f1861--faith-engine--R0046',
                                         'actual': {'event_instance_id': 24,
                                                    'event_definition_key': 'travel_events.4020',
                                                    'observed_at_utc': '2026-10-23T23:45:53.289463+00:00',
                                                    'date_raw': 51407592,
                                                    'input': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0046\\case-output\\faith-e02-journey-001-event-24-offline-analysis-input.json',
                                                              'bytes': 73763,
                                                              'sha256': '54d7c817bd13dad92d60ecf7e600756af1d69050fb0abedc72b961ddf981ba75'},
                                                    'actor_character_id': 15893,
                                                    'saved_scope_characters': {'strong_believer_scope': 44666,
                                                                               'prowling_local_game': 15893},
                                                    'before': {'date_raw': 51407592,
                                                               'paused': True,
                                                               'revision': 17,
                                                               'native_revision': 16,
                                                               'active_event': {'source': 'native',
                                                                                'instance_id': 24,
                                                                                'option_count': 3,
                                                                                'title': None,
                                                                                'options': [{'index': 0,
                                                                                             'option_number': 1,
                                                                                             'label': None,
                                                                                             'enabled': True},
                                                                                            {'index': 1,
                                                                                             'option_number': 2,
                                                                                             'label': None,
                                                                                             'enabled': True},
                                                                                            {'index': 2,
                                                                                             'option_number': 3,
                                                                                             'label': None,
                                                                                             'enabled': True}]},
                                                               'played_character_gold': {'raw': 82115142,
                                                                                         'scale': 100000},
                                                               'played_character_prestige': {'raw': 51271234,
                                                                                             'scale': 100000},
                                                               'played_character_piety': {'raw': 341895800,
                                                                                          'scale': 100000},
                                                               'actor_character_id': 15893,
                                                               'stress': 0},
                                                    'selected_native_option_index': 0,
                                                    'selected_option_number': 1,
                                                    'submission_attempted': True,
                                                    'ack_accepted': True,
                                                    'old_instance_gone_in_independent_snapshot': True,
                                                    'selection_observed': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0046\\case-output\\faith-e02-journey-001-event-24-selection-observed.json',
                                                                           'bytes': 37341,
                                                                           'sha256': '8f4bdbd788b5824993fbd081c6dec570f638ac76cc61eb7a1baadfbecf931b95'},
                                                    'selection_source': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0046\\case-output\\faith-e02-journey-001-0008-event-select-once.actual-results.json',
                                                                         'bytes': 41449,
                                                                         'sha256': '114ea6b0dc5c1806e607812a957f04c181fc2062ecd9c2030a16bd436eebb706'},
                                                    'intent': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0046\\case-output\\faith-e02-journey-001-event-24-selection-intent.json',
                                                               'bytes': 77601,
                                                               'sha256': '256518b123dbf3ea42a87715cbba51f873c87d31bc08e3d3df7bfc3c596b9c3f'},
                                                    'after': {'date_raw': 51407592,
                                                              'paused': True,
                                                              'revision': 18,
                                                              'native_revision': 17,
                                                              'active_event': None,
                                                              'played_character_gold': {'raw': 80615142,
                                                                                        'scale': 100000},
                                                              'played_character_prestige': {'raw': 51271234,
                                                                                            'scale': 100000},
                                                              'played_character_piety': {'raw': 331895800,
                                                                                         'scale': 100000},
                                                              'actor_character_id': 15893,
                                                              'stress': 0}},
                                         'policy_actually_used': 'native_first_displayed_v1',
                                         'registry_consumption_succeeded_live': False}},
 'pilgrimage.4001': {'analysis': {'source_analysis_completed': True,
                                  'migration_review_status': 'source_reviewed_no_occurrence_contract',
                                  'exact_build': '1.20.0.4',
                                  'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0046-events-source-analysis-12004.json',
                                  'source_document_sha256': '73bf38a6eb843e1d3a7c11a29d4c0dedc8cb6f9e321f06ad3e1108404e51f7e3',
                                  'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0046-events-occurrence.json',
                                  'title': '普通朝圣通用抵达：选择后授予朝圣者',
                                  'source_pins': [{'game_relative_path': 'events/activities/pilgrimage_activity/pilgrimage_events.txt',
                                                   'bytes': 358138,
                                                   'sha256': '900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06',
                                                   'relevant_lines': [[9059, 9105]]},
                                                  {'game_relative_path': 'common/scripted_effects/00_pilgrimage_effects.txt',
                                                   'bytes': 40713,
                                                   'sha256': '4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80',
                                                   'relevant_lines': [[216, 274], [1209, 1221]]},
                                                  {'game_relative_path': 'localization/simp_chinese/event_localization/activities/pilgrimage_events_l_simp_chinese.yml',
                                                   'bytes': 136481,
                                                   'sha256': 'cecb7052ac6672f1fd99a0008a8e7d6ccca474069a17e8a9902c55571cd272b3',
                                                   'relevant_lines': [[633, 733]]}],
                                  'source_options': [{'source_key': 'pilgrimage.4001.a',
                                                      'historical_native_index': 0,
                                                      'historical_label': '我走过了神圣的道路。',
                                                      'effects': ['Option9099 calls '
                                                                  'give_pilgrim_trait_or_xp_effect; it is '
                                                                  'not in the immediate block. For non-Hajj '
                                                                  'host, arrived activity-log root effects '
                                                                  'add_trait=pilgrim if absent '
                                                                  '(effects216-234); this branch does not '
                                                                  'remove Hajjaj. Existing-Pilgrim branches '
                                                                  'are XP/lifestyle/piety logic, not a trait '
                                                                  'conversion.',
                                                                  'Option9100 calls '
                                                                  'pilgrimage_arrival_stress_loss_effect: '
                                                                  'zealous medium, cynical no loss, '
                                                                  'otherwise minor stress-and-fulfillment '
                                                                  'loss.',
                                                                  'Names a_dead/a_cynical/a share this '
                                                                  'single source option. After9103 calls '
                                                                  'check_for_pilgrimage_badge_event_effect; '
                                                                  'subsequent4100 actual order is retained '
                                                                  'without claiming a native callstack.'],
                                                      'visibility': 'Unconditional source option; R46 '
                                                                    'rendered0/native0 shown/enabled, with '
                                                                    'add-pilgrim indicator, and selected.',
                                                      'historical_R31_selected': False}],
                                  'agent_reference': 'Source immediate9084-9087 only plays arrival music and '
                                                     'calls conditional Christian saint-bone creation. '
                                                     'Source grant consumer is option9099 -> effects216-234, '
                                                     'not window display/7000/6500. R46 before-start native '
                                                     'Pilgrimfalse/Hajjajtrue and later before6500 native '
                                                     'bothtrue/XP0 bracket the transition; no immediate '
                                                     'post4001 trait-membership query was captured. Source '
                                                     'consumer and actual later membership remain separate. '
                                                     'No instantaneous native timing or hidden artifact '
                                                     'result is inferred.',
                                  'current_native_legality': None,
                                  'action_ready': False,
                                  'ordinary_auto_consumes': False,
                                  'full_occurrence_contract_registered': False,
                                  'selection_policy_changed': False,
                                  'historical_index_is_current_selection_permission': False,
                                  'historical_evidence_is_current_state': False},
                     'observations': {'machine_id': '4-8e1c2f1861',
                                      'observed_at_utc': '2026-10-23T23:46:19.959173+00:00',
                                      'run_id': '4-8e1c2f1861--faith-engine--R0046',
                                      'actual': {'event_instance_id': 25,
                                                 'event_definition_key': 'pilgrimage.4001',
                                                 'observed_at_utc': '2026-10-23T23:46:19.959173+00:00',
                                                 'date_raw': 51407760,
                                                 'input': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0046\\case-output\\faith-e02-journey-001-event-25-offline-analysis-input.json',
                                                           'bytes': 72336,
                                                           'sha256': '280ac447bfbd23d7c0b72d73efdb15d98bf061740d2fca9fe9090bd22c883146'},
                                                 'actor_character_id': 15893,
                                                 'saved_scope_characters': {'host': 15893},
                                                 'before': {'date_raw': 51407760,
                                                            'paused': True,
                                                            'revision': 27,
                                                            'native_revision': 26,
                                                            'active_event': {'source': 'native',
                                                                             'instance_id': 25,
                                                                             'option_count': 1,
                                                                             'title': None,
                                                                             'options': [{'index': 0,
                                                                                          'option_number': 1,
                                                                                          'label': None,
                                                                                          'enabled': True}]},
                                                            'played_character_gold': {'raw': 80615142,
                                                                                      'scale': 100000},
                                                            'played_character_prestige': {'raw': 51271234,
                                                                                          'scale': 100000},
                                                            'played_character_piety': {'raw': 331895800,
                                                                                       'scale': 100000},
                                                            'actor_character_id': 15893,
                                                            'stress': 0},
                                                 'selected_native_option_index': 0,
                                                 'selected_option_number': 1,
                                                 'submission_attempted': True,
                                                 'ack_accepted': True,
                                                 'old_instance_gone_in_independent_snapshot': True,
                                                 'selection_observed': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0046\\case-output\\faith-e02-journey-001-event-25-selection-observed.json',
                                                                        'bytes': 37337,
                                                                        'sha256': 'fc8a278a0206be4f8849aace9eb09685316147c412c6c8e7fce5ba0e8088f3ae'},
                                                 'selection_source': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0046\\case-output\\faith-e02-journey-001-0012-event-select-once.actual-results.json',
                                                                      'bytes': 41452,
                                                                      'sha256': '093ae409f22fc25d87418111bbc246ba23f059ba20045ba61d0a495cdcbb3955'},
                                                 'intent': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0046\\case-output\\faith-e02-journey-001-event-25-selection-intent.json',
                                                            'bytes': 75900,
                                                            'sha256': '47420017d7deb3109b8fe807888f3ffdba0745518c013c913e1b0b59b8c94d78'},
                                                 'after': {'date_raw': 51407760,
                                                           'paused': True,
                                                           'revision': 28,
                                                           'native_revision': 27,
                                                           'active_event': None,
                                                           'played_character_gold': {'raw': 80615142,
                                                                                     'scale': 100000},
                                                           'played_character_prestige': {'raw': 51271234,
                                                                                         'scale': 100000},
                                                           'played_character_piety': {'raw': 331895800,
                                                                                      'scale': 100000},
                                                           'actor_character_id': 15893,
                                                           'stress': 0}},
                                      'policy_actually_used': 'native_first_displayed_v1',
                                      'registry_consumption_succeeded_live': False}},
 'pilgrimage.4100': {'analysis': {'source_analysis_completed': True,
                                  'migration_review_status': 'source_reviewed_no_occurrence_contract',
                                  'exact_build': '1.20.0.4',
                                  'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-4100-source-analysis.json',
                                  'source_document_sha256': '1b02cd0156716c39166f0c247973538c31e8c997d74c308e3bf6d645592842e3',
                                  'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0046-events-occurrence.json',
                                  'title': '朝圣徽章：动态支付与有条件所有权转移',
                                  'source_pins': [{'game_relative_path': 'events/activities/pilgrimage_activity/pilgrimage_events.txt',
                                                   'bytes': 358138,
                                                   'sha256': '900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06',
                                                   'relevant_lines': [[9446, 9619], [9698, 9717]]},
                                                  {'game_relative_path': 'localization/simp_chinese/event_localization/activities/pilgrimage_events_l_simp_chinese.yml',
                                                   'bytes': 136481,
                                                   'sha256': 'cecb7052ac6672f1fd99a0008a8e7d6ccca474069a17e8a9902c55571cd272b3',
                                                   'relevant_lines': [[665, 668]]},
                                                  {'game_relative_path': 'common/scripted_effects/00_artifact_badge_scripted_effects.txt',
                                                   'bytes': 12465,
                                                   'sha256': '9da2e2f4e0fc70fb17d55afdb23b9dd2b2a92b7a4ffddaf3fe00c1f172b1c83e',
                                                   'relevant_lines': [[283, 317]]},
                                                  {'game_relative_path': 'common/script_values/01_dynamic_values.txt',
                                                   'bytes': 48201,
                                                   'sha256': '023165e7d27d106a34f34d7726d938efa8d5dce25650ea3256e0b5ea3f73cc2a',
                                                   'relevant_lines': [[53, 71]]}],
                                  'source_options': [{'source_key': 'pilgrimage.4100.a',
                                                      'historical_native_index': 0,
                                                      'historical_label': '“请给我一个徽章！”',
                                                      'effects': ['pay_short_term_gold to pilgrim_vendor: '
                                                                  'minor_gold_value; multiply1.25 only if '
                                                                  'badge_to_buy exists and '
                                                                  'rarity=illustrious',
                                                                  'If involved_activity exists: add '
                                                                  'activity_log entry pilgrimage_badge_log, '
                                                                  'score50, show_in_conclusion=yes; its root '
                                                                  'effects conditionally set badge_to_buy '
                                                                  'owner=root with purchased history'],
                                                      'visibility': 'R46 rendered0/native0 shown/enabled, '
                                                                    'selected. Dynamic minor_gold; '
                                                                    'multiply1.25 only for illustrious '
                                                                    'badge. Empty indicators are not free '
                                                                    'cost.',
                                                      'historical_R31_selected': False},
                                                     {'source_key': 'pilgrimage.4100.b',
                                                      'historical_native_index': 1,
                                                      'historical_label': '我的金钱有更好的用途。',
                                                      'effects': ['stress_impact '
                                                                  'greedy=minor_stress_impact_loss; no '
                                                                  'purchase or owner transfer in this option '
                                                                  'block'],
                                                      'visibility': 'R46 rendered1/native1 shown/enabled, '
                                                                    'unselected.',
                                                      'historical_R31_selected': False}],
                                  'agent_reference': 'Reuse immutable earlier4100 analysis and exact source '
                                                     'pins. Immediate finds/creates bystander and vendor and '
                                                     'creates badge owned by vendor. Option0 pays dynamic '
                                                     'minor_gold and conditionally transfers saved badge '
                                                     'owner through activity log. R46 wallet-25gold is '
                                                     'observed; generic artifact saved scope does not '
                                                     'establish artifact ID, rarity, actual owner, stats or '
                                                     'equipment. Source after cleanup is conditional; no '
                                                     'hidden disappearance outcome claimed.',
                                  'current_native_legality': None,
                                  'action_ready': False,
                                  'ordinary_auto_consumes': False,
                                  'full_occurrence_contract_registered': False,
                                  'selection_policy_changed': False,
                                  'historical_index_is_current_selection_permission': False,
                                  'historical_evidence_is_current_state': False},
                     'observations': {'machine_id': '4-8e1c2f1861',
                                      'observed_at_utc': '2026-10-23T23:46:42.035758+00:00',
                                      'run_id': '4-8e1c2f1861--faith-engine--R0046',
                                      'actual': {'event_instance_id': 26,
                                                 'event_definition_key': 'pilgrimage.4100',
                                                 'observed_at_utc': '2026-10-23T23:46:42.035758+00:00',
                                                 'date_raw': 51407784,
                                                 'input': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0046\\case-output\\faith-e02-journey-001-event-26-offline-analysis-input.json',
                                                           'bytes': 76592,
                                                           'sha256': '46fe3a0fc42e4aaa3c15ef7cf85adbab4a8797f2711acc504ff2ba8d28c1c5ee'},
                                                 'actor_character_id': 15893,
                                                 'saved_scope_characters': {'host': 15893,
                                                                            'pilgrim_bystander': 44659,
                                                                            'pilgrim_vendor': 44688,
                                                                            'receiving_char': 44688,
                                                                            'badge_acquirer': 44688},
                                                 'before': {'date_raw': 51407784,
                                                            'paused': True,
                                                            'revision': 32,
                                                            'native_revision': 31,
                                                            'active_event': {'source': 'native',
                                                                             'instance_id': 26,
                                                                             'option_count': 2,
                                                                             'title': None,
                                                                             'options': [{'index': 0,
                                                                                          'option_number': 1,
                                                                                          'label': None,
                                                                                          'enabled': True},
                                                                                         {'index': 1,
                                                                                          'option_number': 2,
                                                                                          'label': None,
                                                                                          'enabled': True}]},
                                                            'played_character_gold': {'raw': 80615142,
                                                                                      'scale': 100000},
                                                            'played_character_prestige': {'raw': 51271234,
                                                                                          'scale': 100000},
                                                            'played_character_piety': {'raw': 331895800,
                                                                                       'scale': 100000},
                                                            'actor_character_id': 15893,
                                                            'stress': 0},
                                                 'selected_native_option_index': 0,
                                                 'selected_option_number': 1,
                                                 'submission_attempted': True,
                                                 'ack_accepted': True,
                                                 'old_instance_gone_in_independent_snapshot': True,
                                                 'selection_observed': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0046\\case-output\\faith-e02-journey-001-event-26-selection-observed.json',
                                                                        'bytes': 37340,
                                                                        'sha256': '1d273f3aab5128357d68e520fc1efdbfde15fadcb514e319a2fe6a45f87cb9a9'},
                                                 'selection_source': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0046\\case-output\\faith-e02-journey-001-0016-event-select-once.actual-results.json',
                                                                      'bytes': 41455,
                                                                      'sha256': 'b32b3051386b2fa476c92580c91bfdf8bff4bc51c48ad25c8b54d95bb7025e81'},
                                                 'intent': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0046\\case-output\\faith-e02-journey-001-event-26-selection-intent.json',
                                                            'bytes': 80410,
                                                            'sha256': 'cf7094b966fd5ae7108d68e5ce990c7470cebdbc6379a6d6b95cf7ce33060156'},
                                                 'after': {'date_raw': 51407784,
                                                           'paused': True,
                                                           'revision': 33,
                                                           'native_revision': 32,
                                                           'active_event': None,
                                                           'played_character_gold': {'raw': 78115142,
                                                                                     'scale': 100000},
                                                           'played_character_prestige': {'raw': 51271234,
                                                                                         'scale': 100000},
                                                           'played_character_piety': {'raw': 331895800,
                                                                                      'scale': 100000},
                                                           'actor_character_id': 15893,
                                                           'stress': 0}},
                                      'policy_actually_used': 'native_first_displayed_v1',
                                      'registry_consumption_succeeded_live': False}},
 'pilgrimage.6500': {'analysis': {'source_analysis_completed': True,
                                  'migration_review_status': 'source_reviewed_no_occurrence_contract',
                                  'exact_build': '1.20.0.4',
                                  'source_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0046-events-source-analysis-12004.json',
                                  'source_document_sha256': '73bf38a6eb843e1d3a7c11a29d4c0dedc8cb6f9e321f06ad3e1108404e51f7e3',
                                  'occurrence_document': 'promo/ck3_faith_and_power/episode02/docs/knowledge/r0046-events-occurrence.json',
                                  'title': '谢恩：首显示文化选项可以禁用',
                                  'source_pins': [{'game_relative_path': 'events/activities/pilgrimage_activity/pilgrimage_events.txt',
                                                   'bytes': 358138,
                                                   'sha256': '900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06',
                                                   'relevant_lines': [[10499, 10630]]},
                                                  {'game_relative_path': 'common/scripted_effects/00_pilgrimage_effects.txt',
                                                   'bytes': 40713,
                                                   'sha256': '4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80',
                                                   'relevant_lines': [[1225, 1250]]},
                                                  {'game_relative_path': 'localization/simp_chinese/event_localization/activities/pilgrimage_events_l_simp_chinese.yml',
                                                   'bytes': 136481,
                                                   'sha256': 'cecb7052ac6672f1fd99a0008a8e7d6ccca474069a17e8a9902c55571cd272b3',
                                                   'relevant_lines': [[758, 763]]},
                                                  {'game_relative_path': 'common/script_values/00_basic_values.txt',
                                                   'bytes': 50566,
                                                   'sha256': 'c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef',
                                                   'relevant_lines': [[1131, 1166]]}],
                                  'source_options': [{'source_key': 'pilgrimage.6500.a',
                                                      'historical_native_index': 0,
                                                      'historical_label': '我知道！让我们尽情享受吧！',
                                                      'effects': ['worldly_type_option_effect; selected '
                                                                  'pilgrimage_member opinion toward root+20.',
                                                                  'Base medium stress-and-fulfillment loss, '
                                                                  'with '
                                                                  'sadistic/cynical/paranoid/craven/reclusive '
                                                                  'minor gains.'],
                                                      'visibility': 'Requires tradition_xenophilic; '
                                                                    'show_as_unavailable10558-10563 '
                                                                    'intentionally renders disabled when '
                                                                    'absent. R46 rendered0/native0 shown but '
                                                                    'disabled; never submitted.',
                                                      'historical_R31_selected': False},
                                                     {'source_key': 'pilgrimage.6500.b',
                                                      'historical_native_index': 1,
                                                      'historical_label': '属神的人才能达到的壮举！',
                                                      'effects': ['pious_type_option_effect and '
                                                                  'add_piety=miniscule_piety_gain (+25 '
                                                                  'base).',
                                                                  'Cynical minor stress-and-fulfillment '
                                                                  'gain. No trait-award operation in this '
                                                                  'option.'],
                                                      'visibility': 'No option trigger. R46 '
                                                                    'rendered1/native1 shown/enabled; '
                                                                    'explicit Root second-choice once after '
                                                                    'default case stopped, not first-display '
                                                                    'fallback.',
                                                      'historical_R31_selected': False},
                                                     {'source_key': 'pilgrimage.6500.c',
                                                      'historical_native_index': 2,
                                                      'historical_label': '源条件选项：人建造了这个地方，不是神灵。',
                                                      'effects': ['Cynical minor stress-and-fulfillment '
                                                                  'loss; saved pilgrimage_member opinion '
                                                                  'toward root-10.'],
                                                      'visibility': 'Requires cynical; hidden in R46.',
                                                      'historical_R31_selected': False}],
                                  'agent_reference': 'One-year event cooldown, not the activity cooldown. '
                                                     'Immediate selects eligible adult entourage member. R46 '
                                                     'generic frame advertises3 slots enabled; dedicated '
                                                     'reader shows only native0(disabled, no xenophilic) and '
                                                     'native1(enabled). Default first-display case stopped '
                                                     'PARTIAL without submission. Root decision and native1 '
                                                     'ACK/postcondition/independent snapshot are separate '
                                                     'historical resolution. Both traits already true '
                                                     'before6500 selection;6500 must never be described as '
                                                     'awarding Pilgrim.',
                                  'current_native_legality': None,
                                  'action_ready': False,
                                  'ordinary_auto_consumes': False,
                                  'full_occurrence_contract_registered': False,
                                  'selection_policy_changed': False,
                                  'historical_index_is_current_selection_permission': False,
                                  'historical_evidence_is_current_state': False},
                     'observations': {'machine_id': '4-8e1c2f1861',
                                      'observed_at_utc': '2026-10-23T23:48:42.943735+00:00',
                                      'run_id': '4-8e1c2f1861--faith-engine--R0046',
                                      'actual': {'event_instance_id': 28,
                                                 'event_definition_key': 'pilgrimage.6500',
                                                 'observed_at_utc': '2026-10-23T23:48:42.943735+00:00',
                                                 'date_raw': 51408624,
                                                 'input': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\live\\4-8e1c2f1861--faith-engine--R0046\\case-output\\faith-e02-journey-001-event-28-offline-analysis-input.json',
                                                           'bytes': 74413,
                                                           'sha256': '8647389c64593e56373db6dceabe508a01d6fedab56765c564442b400202d2d2'},
                                                 'actor_character_id': 15893,
                                                 'saved_scope_characters': {'host': 15893,
                                                                            'pilgrimage_member': 44658},
                                                 'before': {'date_raw': 51408624,
                                                            'paused': True,
                                                            'revision': 83,
                                                            'native_revision': 82,
                                                            'active_event': {'source': 'native',
                                                                             'instance_id': 28,
                                                                             'option_count': 3,
                                                                             'title': None,
                                                                             'options': [{'index': 0,
                                                                                          'option_number': 1,
                                                                                          'label': None,
                                                                                          'enabled': True},
                                                                                         {'index': 1,
                                                                                          'option_number': 2,
                                                                                          'label': None,
                                                                                          'enabled': True},
                                                                                         {'index': 2,
                                                                                          'option_number': 3,
                                                                                          'label': None,
                                                                                          'enabled': True}]},
                                                            'played_character_gold': {'raw': 78953210,
                                                                                      'scale': 100000},
                                                            'played_character_prestige': {'raw': 51756085,
                                                                                          'scale': 100000},
                                                            'played_character_piety': {'raw': 337156500,
                                                                                       'scale': 100000},
                                                            'actor_character_id': 15893,
                                                            'stress': 0},
                                                 'selected_native_option_index': None,
                                                 'selected_option_number': None,
                                                 'submission_attempted': False,
                                                 'ack_accepted': None,
                                                 'old_instance_gone_in_independent_snapshot': None,
                                                 'selection_observed': None,
                                                 'after': None,
                                                 'policy_scope': 'original_automated_case_stopped_without_submission',
                                                 'root_explicit_resolution': {'decision': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\commands\\root-r0046-event28-native1-once-a01.decision.actual.json',
                                                                                           'bytes': 3480,
                                                                                           'sha256': 'f18d8200be8769f31ec3fffb2c4d25d4cc25a97d16c50a2bb422be3f18748a34'},
                                                                              'native_execution': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\commands\\root-r0046-event28-native1-once-a01.native.actual.json',
                                                                                                   'bytes': 115721,
                                                                                                   'sha256': 'b9308483dafeb107ef8ebd0c5f7969802d993d10fa29f28e57c270b8d9f3d738'},
                                                                              'queue_exit': {'path': 'C:\\workspace\\ck3-faith-and-power-20261017\\episode02\\v7-filming-20261023-a02\\commands\\root-r0046-event28-native1-once-a01.queue-exit.actual.json',
                                                                                             'bytes': 733,
                                                                                             'sha256': '96c90583730f2b32f403396550c13a711040d840a817a87b646a0ae90e4aa55c'},
                                                                              'reviewer': '/root',
                                                                              'observed_at_utc': '2026-10-23T23:55:45.844916+00:00',
                                                                              'reason': 'Actual Native first '
                                                                                        'shown option lacks '
                                                                                        'xenophilic culture; '
                                                                                        'independently '
                                                                                        'Source-reviewed '
                                                                                        'second '
                                                                                        'shown/enabled '
                                                                                        'option gives pious '
                                                                                        'progress '
                                                                                        'and25piety. '
                                                                                        'Explicit Root '
                                                                                        'decision; not '
                                                                                        'first-display '
                                                                                        'fallback.',
                                                                              'selected_rendered_index': 1,
                                                                              'selected_native_option_index': 1,
                                                                              'selected_option_number': 2,
                                                                              'submission_attempted': True,
                                                                              'ack_accepted': True,
                                                                              'native_postcondition': {'status': 'event_instance_advanced',
                                                                                                       'postcondition_verified': True,
                                                                                                       'old_event_instance_id': 28,
                                                                                                       'new_event_instance_id': None},
                                                                              'old_instance_gone_in_independent_snapshot': True,
                                                                              'independent_post': {'date_raw': 51408624,
                                                                                                   'paused': True,
                                                                                                   'revision': 84,
                                                                                                   'native_revision': 83,
                                                                                                   'active_event': None,
                                                                                                   'played_character_gold': {'raw': 78953210,
                                                                                                                             'scale': 100000},
                                                                                                   'played_character_prestige': {'raw': 51756085,
                                                                                                                                 'scale': 100000},
                                                                                                   'played_character_piety': {'raw': 339656500,
                                                                                                                              'scale': 100000},
                                                                                                   'actor_character_id': 15893,
                                                                                                   'stress': 0},
                                                                              'is_original_first_displayed_choice': False,
                                                                              'original_case_status_overwritten': False}},
                                      'policy_actually_used': 'native_first_displayed_v1',
                                      'registry_consumption_succeeded_live': False}}}

PILGRIMAGE_TRAVEL_SOURCE_ONLY_12004.update(_R0046_SOURCE_ONLY)
