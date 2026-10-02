"""The current .3 five-scope travel-home response and conditional shared cleanup."""

from typing import Final

from .registry import PLAYER_SENTINEL


TRAVEL_COMPLETION1000_12003_RECORDS: Final = {'travel_completion_event.1000': {'contract': {'date_policy': 'product-observation-window',
                                               'root_character_id': PLAYER_SENTINEL,
                                               'character_scopes': {'travel_owner': PLAYER_SENTINEL},
                                               'scope_types': {'travel_plan': 'travel_plan',
                                                               'travel_owner': 'character',
                                                               'current_location': 'province',
                                                               'travel_plan_scope': 'travel_plan',
                                                               'final_destination_province': 'province'},
                                               'saved_scope_name_sets': (('travel_plan',
                                                                          'travel_owner',
                                                                          'current_location',
                                                                          'travel_plan_scope',
                                                                          'final_destination_province'),),
                                               'saved_scope_count': 5,
                                               'option_count': 1,
                                               'snapshot_option_count': 2,
                                               'native_option_indices': (0,),
                                               'selected_option_number': 1,
                                               'selected_native_option_index': 0,
                                               'occurrence_policy': 'repeatable-within-product-observation-window'},
                                  'analysis': {'exact_build': {'game_version': '1.20.0.3',
                                                               'ck3_executable_sha256': '94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6',
                                                               'steam_build_id': 25652598},
                                               'source_sha256': {'events/travel_events/travel_completion_events.txt': '2FB4F01EB814A3FE28180D05B69856A01B271171A9D754CE16501400F3D19CA1',
                                                                 'common/on_action/travel_on_actions.txt': 'CD40F30A9280EA9BA656B59005201550F3991AFD646FD686D7474657B1B1FF70'},
                                               'definition_lines': '15-194',
                                               'definition_block_sha256': '5951EC5F8E23698F329875B28DAE6F57D9251037FD8E31D5CB8F06E505BEAAE0',
                                               'definition_block_hash_convention': 'SourceTree key token '
                                                                                   'through closing brace; '
                                                                                   'original CRLF retained; '
                                                                                   'following newline excluded',
                                               'event_type': 'character_event',
                                               'authored_option_count': 2,
                                               'source_event_field_blocks': [{'key': 'travel_completion_event.1000:trigger',
                                                                              'relative_path': 'events/travel_events/travel_completion_events.txt',
                                                                              'line': 85,
                                                                              'end_line': 97,
                                                                              'raw_token_block_sha256': 'EF2499583548422482179662B71188E1CA60D31EB640954484139F26ED892D93'},
                                                                             {'key': 'travel_completion_event.1000:immediate',
                                                                              'relative_path': 'events/travel_events/travel_completion_events.txt',
                                                                              'line': 99,
                                                                              'end_line': 161,
                                                                              'raw_token_block_sha256': '91199E0DB0AF3DF479CC1618138315CEED07D99C41B1E03020A7413725B58559'},
                                                                             {'key': 'travel_completion_event.1000:option0',
                                                                              'relative_path': 'events/travel_events/travel_completion_events.txt',
                                                                              'line': 164,
                                                                              'end_line': 171,
                                                                              'raw_token_block_sha256': 'BD3CE809154D03D378489A191B0A43D5A4881BD87A4C8BDF5BEFF84E79F101A0'},
                                                                             {'key': 'travel_completion_event.1000:option1',
                                                                              'relative_path': 'events/travel_events/travel_completion_events.txt',
                                                                              'line': 174,
                                                                              'end_line': 187,
                                                                              'raw_token_block_sha256': 'B3AA2B538255750DCE46B951EBB43361C0B2D7DCE654E92FB206AD34E9D56A55'},
                                                                             {'key': 'travel_completion_event.1000:after',
                                                                              'relative_path': 'events/travel_events/travel_completion_events.txt',
                                                                              'line': 188,
                                                                              'end_line': 193,
                                                                              'raw_token_block_sha256': '564CA9A8B5CE8B4750CB3B129EE684ACF7395091B7BC7F9E1FECE09C6F621E1B'}],
                                               'source_dependency_blocks': [],
                                               'source_caller_blocks': [{'key': 'on_travel_plan_complete:trigger',
                                                                         'relative_path': 'common/on_action/travel_on_actions.txt',
                                                                         'line': 1467,
                                                                         'end_line': 1469,
                                                                         'raw_token_block_sha256': '06061A431C96CB3CEFE8E25EAB9A9741F3C96537C1495CC4E68B088F3210BFD8'},
                                                                        {'key': 'on_travel_plan_complete:first_valid',
                                                                         'relative_path': 'common/on_action/travel_on_actions.txt',
                                                                         'line': 1470,
                                                                         'end_line': 1476,
                                                                         'raw_token_block_sha256': 'FA5628C6CF037BBCE7A957CB3F101F43D211989E9FE1BAC3A619F902C3643342'},
                                                                        {'key': 'on_travel_plan_abort:trigger',
                                                                         'relative_path': 'common/on_action/travel_on_actions.txt',
                                                                         'line': 1780,
                                                                         'end_line': 1780,
                                                                         'raw_token_block_sha256': 'EF0F9CB8BA5ED3B867D611403C1FA81E8425C3EC5FE041BAE6A2BB96B441BD48'},
                                                                        {'key': 'on_travel_plan_abort:events',
                                                                         'relative_path': 'common/on_action/travel_on_actions.txt',
                                                                         'line': 1781,
                                                                         'end_line': 1784,
                                                                         'raw_token_block_sha256': '7A4BA43179347BFCD6503C07258660D0CFF09B4A675C92219B7D399FED59C1BC'}],
                                               'caller_semantics': 'Ruler completion first_valid and abort '
                                                                   'events both list this key; actual incoming '
                                                                   'callback is unobserved and does not add a '
                                                                   'choice gate',
                                               'option_semantics': {'0': {'native_option_index': 0,
                                                                          'api_option_number': 1,
                                                                          'name': 'travel_completion_event.1000.a',
                                                                          'line_range': [163, 171],
                                                                          'shown_actual': True,
                                                                          'enabled_actual': True,
                                                                          'trigger': 'location=root.default_location',
                                                                          'authored_ai_chance': None,
                                                                          'effects_empty': True,
                                                                          'executed_option_effects': [],
                                                                          'name_variant': 'landless_adventurer_government '
                                                                                          'changes text only'},
                                                                    '1': {'native_option_index': 1,
                                                                          'api_option_number': 2,
                                                                          'name': 'travel_completion_event.1000.b',
                                                                          'line_range': [174, 187],
                                                                          'shown_actual': False,
                                                                          'trigger': 'location!=root.default_location',
                                                                          'authored_ai_chance': {'base': 100},
                                                                          'effects_empty': False,
                                                                          'executed_option_effects': ['return_home=yes'],
                                                                          'eligibility_boundary': 'Hidden '
                                                                                                  'actual '
                                                                                                  'option; do '
                                                                                                  'not select '
                                                                                                  'or register '
                                                                                                  'a new '
                                                                                                  'away-from-home '
                                                                                                  'route in '
                                                                                                  'this '
                                                                                                  'task.'}},
                                               'authored_option_name_aliases': ['travel_completion_event.1000.a',
                                                                                'travel_completion_event.1000.b'],
                                               'native_ai_weights': {'0': 'no authored ai_chance',
                                                                     '1': 'base=100; hidden in current actual '
                                                                          'projection'},
                                               'localization_sources': {'localization/english/event_localization/travel_events/travel_completion_events_l_english.yml': '26D11A84D2BCFE2376F7F71B283C8DCC12E69BDF453D2832554EF9C3FC725FBE',
                                                                        'localization/simp_chinese/event_localization/travel_events/travel_completion_events_l_simp_chinese.yml': '8712C9FB364943E204385F9C16CF36998F391F009F7196E4B81FD0753D9DACC4'},
                                               'immediate_effect': {'line_range': [102, 160],
                                                                    'pre_choice': True,
                                                                    'effects': ['travel music',
                                                                                'traveler_lifestyle_rank_up_check_effect',
                                                                                'current_location/travel_plan_scope/final_destination_province '
                                                                                'saves',
                                                                                'optional travel_leader_scope '
                                                                                'and travel_conc_memory saves',
                                                                                'travel_plan end date and '
                                                                                'elapsed day variables',
                                                                                'optional cultural ambassador '
                                                                                'tooltip',
                                                                                'conditional '
                                                                                'tourney_participant horse XP '
                                                                                'value1-3'],
                                                                    'optional_scope_boundary': 'travel_leader?= '
                                                                                               'and '
                                                                                               'random_memory?= '
                                                                                               'may save no '
                                                                                               'scope; caller '
                                                                                               'supplied '
                                                                                               'destination is '
                                                                                               'not required '
                                                                                               "by the event's "
                                                                                               'selected '
                                                                                               'option. Actual '
                                                                                               'onlytravel_owner '
                                                                                               'character is '
                                                                                               'consistent '
                                                                                               'with this '
                                                                                               'source.'},
                                               'after_effect': {'line_range': [188, 193],
                                                                'effects': ['If '
                                                                            'recently_completed_mandala_contract '
                                                                            'flag exists, remove it'],
                                                                'unconditional_resource_effect': False,
                                                                'flag_state_observed': False,
                                                                'credit': 0},
                                               'scope_boundary': 'Current exact five-name route has only '
                                                                 'travel_owner as a character and binds it to '
                                                                 'the player; optional leader and memory may '
                                                                 'save nothing; travel-plan/province payload '
                                                                 'identities remain opaque',
                                               'source_migration_reuse': {'source_sha256': '5783AE09C2A9B51622FD0C87AD90ECF8AA7D041273E3FEAB3D147426E3E461C2',
                                                                          'classification': 'unchanged-source-file-bytes',
                                                                          'boundary': 'Reuse reviewed '
                                                                                      'unchanged .2-to-.3 '
                                                                                      'authored body only; old '
                                                                                      'seven-scope data and .2 '
                                                                                      'record are preserved; '
                                                                                      'removed old stress '
                                                                                      'effects are not '
                                                                                      'expected'},
                                               'selected_choice_effect_profile': {'schema': 'xar.ck3.vanilla-event-choice-effect',
                                                                                  'schema_version': 1,
                                                                                  'selected_native_option_index': 0,
                                                                                  'completeness': 'all-authored-options-and-common-after-source-reviewed',
                                                                                  'selected_option_effects': [],
                                                                                  'common_after_effects': [{'domain': 'player_character_flag',
                                                                                                            'source': 'remove_character_flag',
                                                                                                            'character_scope': 'root',
                                                                                                            'flag_key': 'recently_completed_mandala_contract',
                                                                                                            'condition': 'has_character_flag=recently_completed_mandala_contract',
                                                                                                            'source_lines': [188,
                                                                                                                             193],
                                                                                                            'flag_state_observed': False}],
                                                                                  'observable_postcondition': None,
                                                                                  'source_anchors': ['events/travel_events/travel_completion_events.txt:163-171',
                                                                                                     'events/travel_events/travel_completion_events.txt:188-193'],
                                                                                  'source_sha256': {'events/travel_events/travel_completion_events.txt': '2FB4F01EB814A3FE28180D05B69856A01B271171A9D754CE16501400F3D19CA1',
                                                                                                    'common/on_action/travel_on_actions.txt': 'CD40F30A9280EA9BA656B59005201550F3991AFD646FD686D7474657B1B1FF70'},
                                                                                  'material_evidence_boundary': 'The '
                                                                                                                'selected '
                                                                                                                'home '
                                                                                                                'button '
                                                                                                                'is '
                                                                                                                'empty; '
                                                                                                                'common '
                                                                                                                'after '
                                                                                                                'conditionally '
                                                                                                                'removes '
                                                                                                                'a '
                                                                                                                'flag '
                                                                                                                'whose '
                                                                                                                'state '
                                                                                                                'is '
                                                                                                                'unobserved. '
                                                                                                                'No '
                                                                                                                'resource, '
                                                                                                                'pre-choice '
                                                                                                                'XP, '
                                                                                                                'hidden '
                                                                                                                'return_home, '
                                                                                                                'independent '
                                                                                                                'arrival, '
                                                                                                                'travel '
                                                                                                                'fullID/phase '
                                                                                                                'or '
                                                                                                                'terminal '
                                                                                                                'material '
                                                                                                                'is '
                                                                                                                'established'},
                                               'selected_choice_campaign_utility_profile': {'schema': 'xar.ck3.vanilla-event-campaign-utility',
                                                                                            'schema_version': 1,
                                                                                            'selected_native_option_index': 0,
                                                                                            'objective_id': 'continue_current_travel_home_modal',
                                                                                            'comparison_kind': 'sole_legal_route',
                                                                                            'selected_rank': 1,
                                                                                            'rank_count': 1,
                                                                                            'selected_utility': {'material_direction': 'empty_home_response_with_conditional_flag_cleanup',
                                                                                                                 'resource_cost': 'none_authored_in_selected_option_or_common_after',
                                                                                                                 'outcome_variance': 'conditional_flag_presence_unobserved',
                                                                                                                 'timeline_value': 'required_to_continue_current_modal'},
                                                                                            'alternatives': [],
                                                                                            'cross_event_numeric_score': None,
                                                                                            'calibration_status': 'not_calibrated',
                                                                                            'decision_scope': 'bounded_timeline_continuation',
                                                                                            'source_sha256': {'events/travel_events/travel_completion_events.txt': '2FB4F01EB814A3FE28180D05B69856A01B271171A9D754CE16501400F3D19CA1',
                                                                                                              'common/on_action/travel_on_actions.txt': 'CD40F30A9280EA9BA656B59005201550F3991AFD646FD686D7474657B1B1FF70'},
                                                                                            'readiness': 'static-ready',
                                                                                            'new_live_evidence': False},
                                               'source_review_receipt_sha256': '73DD4553762EE64E325B8D1C83A8374F3F96982A40C6D64B9E4E92D3C784CFAD',
                                               'readiness': 'static-ready',
                                               'new_live_evidence': False,
                                               'material_evidence_boundary': 'No stress, gold, XP, flag '
                                                                             'clearing, travel phase, live, M2 '
                                                                             'or independent travel/Feast '
                                                                             'terminal credit from this '
                                                                             'current five-scope record or '
                                                                             'modal advance'},
                                  'observations': {'exemplars': [{'kind': 'closed-production-red',
                                                                  'artifact': 'Z:\\ck3_mod_rewrite\\artifacts\\g2-maintainer-2026-10-02\\resume-12003\\m2-events\\robert-queued19-a391c881-v23-actual-observe-01\\result.json',
                                                                  'artifact_sha256': 'B354D8FCC8DDB1C3B2C37F95D504452A3261D643392C4495AFEB6A6FE413CCFA',
                                                                  'event_instance_id': 19,
                                                                  'root_character_id': 29829,
                                                                  'date_raw': 53222952,
                                                                  'selection_attempted': False,
                                                                  'failed_checks': ['direct_projection_support:character_scopes',
                                                                                    'direct_projection_support:unique_character_scope_excludes'],
                                                                  'boundary': 'Closed natural five-scope home '
                                                                              'modal rejects inherited '
                                                                              'seven-scope/distinct-leader '
                                                                              'contract; no selected '
                                                                              'flag/XP/resource/travel-phase '
                                                                              'outcome in this exemplar'}]}}}
