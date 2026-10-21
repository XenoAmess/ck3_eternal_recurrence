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
