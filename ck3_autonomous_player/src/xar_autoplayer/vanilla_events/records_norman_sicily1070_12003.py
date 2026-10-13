"""Exact installed1.20.0.3 source knowledge; choices require explicit review."""

from typing import Final

NORMAN_SICILY1070_12003_RECORDS: Final = {'bookmark.1070': {'contract': {'date_policy': 'product-observation-window',
                                'root_character_id': '$player',
                                'option_count': 3,
                                'snapshot_option_count': 3,
                                'native_option_indices': (0, 1, 2),
                                'selected_option_number': 3,
                                'selected_native_option_index': 2,
                                'occurrence_policy': 'source-conditional',
                                'scope_observation_policy': 'Read actual native envelope; no '
                                                            'inferred scope count or name set'},
                   'analysis': {'exact_build': {'game_version': '1.20.0.3',
                                                'ck3_executable_sha256': '94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6',
                                                'steam_build_id': 25652598},
                                'selected_option_scope_dependency_review': {
                                    'schema': 'xar.ck3.source-reviewed-selected-option-scopes/v1',
                                    'ck3_build': '1.20.0.4',
                                    'selected_native_option_index': 2,
                                    'source_sha256': '5A5CE08980D8C4FDA1DCF40EC26E12D8973C01286F4DA42A6D939776CFD50E03',
                                    'root_dependencies': ('root.capital_province',),
                                    'saved_scope_dependencies': (),
                                    'common_after_effects': ()},
                                'readiness': 'static-ready',
                                'new_live_evidence': False,
                                'material_evidence_boundary': 'Exact installed source knowledge '
                                                              'only; actual acknowledgement '
                                                              'belongs to separate '
                                                              'typed-instance/revision-bound '
                                                              'evidence',
                                'source_sha256': {'events/bookmark_events.txt': '5A5CE08980D8C4FDA1DCF40EC26E12D8973C01286F4DA42A6D939776CFD50E03',
                                                  'localization/simp_chinese/bookmark/bookmark_rags_to_riches_1066_l_simp_chinese.yml': '89F12E753511E0688FB002420BC66B1F5CBFD85D20F5B83F0D2F2333141629DD'},
                                'definition_lines': '1210-1423',
                                'event_type': 'character_event',
                                'option_localization_keys': {'0': 'bookmark.1070.a',
                                                             '1': 'bookmark.1070.b',
                                                             '2': 'bookmark.1070.c'},
                                'option_caption_simp_chinese': {'2': '教宗和皇帝都可以保留他们的土地……'},
                                'immediate_effect': 'Before acknowledgement, gain pressed claims '
                                                    'on '
                                                    'd_salerno,c_napoli,d_capua,c_siracusa,c_agrigento,c_palermo; '
                                                    'save emperor and pope scopes; music and '
                                                    'tooltip. These effects are not '
                                                    'selected-choice material credit.',
                                'option_semantics': {'0': 'Additional d_benevento/d_spoleto '
                                                          'claims;3 native armies each250, each with125levies,50bowmen,50light_horsemen,25conrois; emperor '
                                                          'and pope angry opinion-30',
                                                     '1': 'Additional d_benevento claim;2 native '
                                                          'armies each250, each with125levies,50bowmen,50light_horsemen,25armored_horsemen; pope angry opinion-30',
                                                     '2': 'Spawn1 army250 at '
                                                          'capital:125levies,50bowmen,50light_horsemen,25armored_horsemen; '
                                                          'no extra '
                                                          'claim/opinion/trait/gold/stress; no '
                                                          'after'},
                                'selected_choice_effect_profile': {'schema': 'xar.ck3.vanilla-event-choice-effect',
                                                                   'schema_version': 1,
                                                                   'selected_native_option_index': 2,
                                                                   'completeness': 'all-authored-options-and-common-after-source-reviewed',
                                                                   'selected_option_effects': [{'effect': 'spawn_army',
                                                                                                'levies': 125,
                                                                                                'men_at_arms': {'bowmen': 50,
                                                                                                                'light_horsemen': 50,
                                                                                                                'armored_horsemen': 25},
                                                                                                'location': 'root.capital_province'}],
                                                                   'common_after_effects': [],
                                                                   'observable_postcondition': {
                                                                       'metric': 'player_armies.bookmark1070_spawn',
                                                                       'expected_relation': 'new_army_source_shape',
                                                                       'material_change_required_for_evidence': True},
                                                                   'source_anchors': ['events/bookmark_events.txt:1210-1423'],
                                                                   'source_sha256': '5A5CE08980D8C4FDA1DCF40EC26E12D8973C01286F4DA42A6D939776CFD50E03'},
                                'selected_choice_campaign_utility_profile': {
                                    'schema': 'xar.ck3.vanilla-event-campaign-utility',
                                    'schema_version': 1,
                                    'selected_native_option_index': 2,
                                    'objective_id': 'obtain_event_army_without_additional_papal_or_imperial_hostility',
                                    'comparison_kind': 'source_reviewed_ordinal',
                                    'selected_rank': 1,
                                    'rank_count': 3,
                                    'selected_utility': {
                                        'event_armies': 1,
                                        'source_defined_soldiers': 250,
                                        'additional_claims': [],
                                        'additional_pope_opinion_cost': 0,
                                        'additional_emperor_opinion_cost': 0,
                                        'timeline_value': 'continue_actual_campaign',
                                        'tradeoff': 'Forgo the additional troops and claims offered by the other two routes.'},
                                    'alternatives': [{
                                        'native_option_index': 0,
                                        'authored_ai_base': 100,
                                        'event_armies': 3,
                                        'source_defined_soldiers': 750,
                                        'additional_claims': ['d_benevento', 'd_spoleto'],
                                        'additional_pope_opinion_cost': -30,
                                        'additional_emperor_opinion_cost': -30,
                                        'source_tradeoff': 'More troops and two claims; each army uses25conrois rather than armored_horsemen; incurs both rulers hostility.'}, {
                                        'native_option_index': 1,
                                        'authored_ai_base': 100,
                                        'event_armies': 2,
                                        'source_defined_soldiers': 500,
                                        'additional_claims': ['d_benevento'],
                                        'additional_pope_opinion_cost': -30,
                                        'additional_emperor_opinion_cost': 0,
                                        'source_tradeoff': 'More troops and one claim; incurs papal hostility.'}],
                                    'authored_selected_ai_base': 100,
                                    'native_preference_observed': False,
                                    'immediate_pressed_claims_excluded_from_choice_credit': True,
                                    'cross_event_numeric_score': None,
                                    'calibration_status': 'not_calibrated',
                                    'decision_scope': 'bounded_timeline_continuation',
                                    'source_sha256': {'events/bookmark_events.txt': '5A5CE08980D8C4FDA1DCF40EC26E12D8973C01286F4DA42A6D939776CFD50E03'},
                                    'readiness': 'static-ready',
                                    'new_live_evidence': False},
                                'safe_option_rationale': 'Important multiple-choice event, not an '
                                                         'empty acknowledgement. Source-reviewed '
                                                         'bounded continuation, not an optimal '
                                                         'choice; index2 still creates troops.'},
                   'observations': {}}}
