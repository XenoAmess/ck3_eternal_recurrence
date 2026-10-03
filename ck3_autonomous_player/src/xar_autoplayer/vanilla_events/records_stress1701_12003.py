"""Exact installed1.20.0.3 source knowledge; choices require explicit review."""

from typing import Final

STRESS1701_12003_RECORDS: Final = {'stress_threshold.1701': {'contract': {'date_policy': 'product-observation-window',
                                        'root_character_id': '$player',
                                        'option_count': 9,
                                        'snapshot_option_count': 9,
                                        'native_option_indices': (0, 1, 2, 3, 4, 5, 6, 7, 8),
                                        'selected_option_number': 9,
                                        'selected_native_option_index': 8,
                                        'occurrence_policy': 'source-conditional',
                                        'scope_observation_policy': 'Read actual native envelope; '
                                                                    'no inferred scope count or '
                                                                    'name set'},
                           'analysis': {'exact_build': {'game_version': '1.20.0.3',
                                                        'ck3_executable_sha256': '94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6',
                                                        'steam_build_id': 25652598},
                                        'readiness': 'static-ready',
                                        'new_live_evidence': False,
                                        'material_evidence_boundary': 'Exact installed source '
                                                                      'knowledge only; actual '
                                                                      'acknowledgement belongs to '
                                                                      'separate '
                                                                      'image/instance/revision-bound '
                                                                      'evidence',
                                        'source_sha256': {'events/stress_events/stress_threshold_events.txt': 'FEB4702321A7B872EBB39C1D3FAB6BDFD2002300098E912FCD307ABDC775A339',
                                                          'common/scripted_effects/00_stress_effects.txt': 'B496B45EBD5557562C9E2F10AAA747833062C2E7B049EFB9D86B7D0DC18E2BA9',
                                                          'common/script_values/00_stress_values.txt': '821A0B77244FC5EE2D87D339CB24DBEF00787B83D44EC2DF9215FC1A93AEC2D4',
                                                          'common/script_values/01_dynamic_values.txt': '023165E7D27D106A34F34D7726D938EFA8D5DCE25650EA3256E0B5EA3F73CC2A',
                                                          'localization/simp_chinese/event_localization/stress_events/stress_threshold_events_1_l_simp_chinese.yml': 'CAC3CB2EF54775242053E88B309504D0FA807FF22320B006FF8F2E2937585426'},
                                        'definition_lines': '5017-5805',
                                        'event_type': 'character_event',
                                        'authored_options': [{'native_index': 0,
                                                              'coping_family': 'rakish'},
                                                             {'native_index': 1,
                                                              'coping_family': 'irritable'},
                                                             {'native_index': 2,
                                                              'coping_family': 'flagellant'},
                                                             {'native_index': 3,
                                                              'coping_family': 'profligate'},
                                                             {'native_index': 4,
                                                              'coping_family': 'journaller'},
                                                             {'native_index': 5,
                                                              'coping_family': 'confider'},
                                                             {'native_index': 6,
                                                              'coping_family': 'drunkard'},
                                                             {'native_index': 7,
                                                              'coping_family': 'hashishiyah'},
                                                             {'native_index': 8,
                                                              'coping_family': 'push-through'}],
                                        'native_visibility_boundary': 'SDK exposes nine authored '
                                                                      'options as enabled; actual '
                                                                      'GUI may show only three. '
                                                                      'Native enabled is not proof '
                                                                      'of visible choice. Index8 '
                                                                      'is selected only after '
                                                                      'explicit image/source '
                                                                      'review and authorization.',
                                        'option_semantics': {'3': 'add_trait profligate; minor '
                                                                  'stress loss -15 before '
                                                                  'character modifiers; '
                                                                  'remove_short_term_gold '
                                                                  'major_gold_value '
                                                                  '(income-scaled, bounded and '
                                                                  'rounded)',
                                                             '6': 'minor stress loss; existing '
                                                                  'drunkard gains three-year '
                                                                  'stress_drinking_binge, else '
                                                                  'add_trait drunkard',
                                                             '8': 'stress_threshold.1701.k; '
                                                                  'add_stress '
                                                                  'medium_stress_impact_gain=40 '
                                                                  'before character modifiers; no '
                                                                  'selected-option trait or gold '
                                                                  'effects'},
                                        'common_after_effect': '00_stress_effects.txt:47-96 cleans '
                                                               'option flags, applies recorded '
                                                               'stress-level cooldown flag, '
                                                               'removes recorded-level flags, '
                                                               'schedules stress_threshold.0005 '
                                                               'after '
                                                               'stress_threshold_second_check_timing, '
                                                               'emits cooldown tooltip. Event '
                                                               'after5724-5804 also adds matching '
                                                               'personality had_desc blocker flag '
                                                               'for10years.',
                                        'selected_choice_effect_profile': {'schema': 'xar.ck3.vanilla-event-choice-effect',
                                                                           'schema_version': 1,
                                                                           'selected_native_option_index': 8,
                                                                           'completeness': 'selected-option-and-common-after-source-reviewed',
                                                                           'selected_option_effects': [{'effect': 'add_stress',
                                                                                                        'value': 'medium_stress_impact_gain',
                                                                                                        'base_value': 40,
                                                                                                        'actual_amount_boundary': 'Character '
                                                                                                                                  'stress '
                                                                                                                                  'modifiers '
                                                                                                                                  'apply; '
                                                                                                                                  'base40 '
                                                                                                                                  'does '
                                                                                                                                  'not '
                                                                                                                                  'prove '
                                                                                                                                  'exact '
                                                                                                                                  'actual '
                                                                                                                                  'delta'}],
                                                                           'common_after_effects': ['stress-threshold '
                                                                                                    'flag '
                                                                                                    'cleanup/cooldown',
                                                                                                    'schedule '
                                                                                                    'stress_threshold.0005',
                                                                                                    'conditional10-year '
                                                                                                    'personality '
                                                                                                    'description '
                                                                                                    'blocker'],
                                                                           'observable_postcondition': None,
                                                                           'source_anchors': ['events/stress_events/stress_threshold_events.txt:5715-5805',
                                                                                              'common/scripted_effects/00_stress_effects.txt:47-96'],
                                                                           'source_sha256': 'FEB4702321A7B872EBB39C1D3FAB6BDFD2002300098E912FCD307ABDC775A339'},
                                        'safe_option_rationale': 'No automatic permission for this '
                                                                 'important multiple-choice event. '
                                                                 'Index8 preserved traits and gold '
                                                                 'in authored option but increases '
                                                                 'stress; explicit operator choice '
                                                                 'required.'},
                           'observations': {}}}
