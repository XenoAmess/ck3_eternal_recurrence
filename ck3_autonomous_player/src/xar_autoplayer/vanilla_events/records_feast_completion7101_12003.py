"""The actual .3 completion modal and its executed rank-check continuation."""

from typing import Final

from .registry import PLAYER_SENTINEL


FEAST_COMPLETION7101_12003_RECORDS: Final = {'feast.7101': {'contract': {'date_policy': 'product-observation-window',
                             'root_character_id': PLAYER_SENTINEL,
                             'character_scopes': {'host': PLAYER_SENTINEL,
                                                  'root_scope': PLAYER_SENTINEL},
                             'scope_types': {'activity': 'activity',
                                             'host': 'character',
                                             'province': 'province',
                                             'activity_location': 'province',
                                             'root_scope': 'character'},
                             'saved_scope_name_sets': (('activity',
                                                        'host',
                                                        'province',
                                                        'activity_location',
                                                        'root_scope'),),
                             'saved_scope_count': 5,
                             'option_count': 1,
                             'snapshot_option_count': 1,
                             'native_option_indices': (0,),
                             'selected_option_number': 1,
                             'selected_native_option_index': 0,
                             'occurrence_policy': 'repeatable-within-product-observation-window'},
                'analysis': {'exact_build': {'game_version': '1.20.0.3',
                                             'ck3_executable_sha256': '94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6',
                                             'steam_build_id': 25652598},
                             'source_sha256': {'events/activities/feast_activity/feast_events.txt': 'F5820211444E7DBAF0A318ADF65BEBF4CA581D3A4E9F381ADD63D3BF02AAF77E',
                                               'common/scripted_effects/00_lifestyle_focus_effects.txt': '051706E95FD0F0535AAA6201941ABFC86DF1C0E44DFCBA6BED5E6D9E94DB849C',
                                               'common/script_values/00_basic_values.txt': 'C379CC0C58ED1574033F0E07A58697DFC6F8475C26AA4B117F2332008D4A27EF',
                                               'common/scripted_effects/00_activity_effects.txt': 'D5C594F8746B923D34B13A67DB881821E12F08CE1AB4E6E3F83933419C9E2D38',
                                               'common/activities/activity_types/feast.txt': 'FBC2E6E3F74BC8C2DB1BB1EB01609AA7CF50E9546671A12617301F175BE84598'},
                             'definition_lines': '1378-1469',
                             'definition_block_sha256': 'EF36486354CD4B41268C64CA6B7F7DB46DB7A90569B8E3C3E7D63F5C4757232E',
                             'definition_block_hash_convention': 'SourceTree key token through closing '
                                                                 'brace; original CRLF retained; following '
                                                                 'newline excluded',
                             'source_dependency_blocks': [{'key': 'reveler_lifestyle_rank_up_check_effect',
                                                           'relative_path': 'common/scripted_effects/00_lifestyle_focus_effects.txt',
                                                           'line': 261,
                                                           'end_line': 360,
                                                           'raw_token_block_sha256': 'D9A340CAEF098D095B36A77F5C6028B20CB1B344E41F64EB2952E011AF4F02BA'},
                                                          {'key': 'reveler_rank_up_1_threshold',
                                                           'relative_path': 'common/script_values/00_basic_values.txt',
                                                           'line': 1462,
                                                           'end_line': 1462,
                                                           'raw_token_block_sha256': 'FF0C880C2EBCBAC272B00D8CAF642B41BE32E3F453110B6F233FD8D1EE570FA2'},
                                                          {'key': 'reveler_rank_up_2_threshold',
                                                           'relative_path': 'common/script_values/00_basic_values.txt',
                                                           'line': 1463,
                                                           'end_line': 1463,
                                                           'raw_token_block_sha256': '915730BE6C92137C5D87DA52FD102DFF80FE37A904985BDDA5169CF9142B35D1'},
                                                          {'key': 'reveler_rank_up_3_threshold',
                                                           'relative_path': 'common/script_values/00_basic_values.txt',
                                                           'line': 1464,
                                                           'end_line': 1464,
                                                           'raw_token_block_sha256': '54B6004AB2B702EC53592E858C410384B935AA37BD251D143B3A5209B11D877B'},
                                                          {'key': 'disburse_feast_activity_rewards',
                                                           'relative_path': 'common/scripted_effects/00_activity_effects.txt',
                                                           'line': 3052,
                                                           'end_line': 3852,
                                                           'raw_token_block_sha256': 'B3015014E61BD1F08B248630C50E3A9E6B51D83E6201A431CFE68AAEE780870B'},
                                                          {'key': 'feast.0050',
                                                           'relative_path': 'events/activities/feast_activity/feast_events.txt',
                                                           'line': 119,
                                                           'end_line': 204,
                                                           'raw_token_block_sha256': '5E3C82054223102C291F2EBDFA9E59931F0876D31C97A9A26F733060A75862B5'}],
                             'event_type': 'activity_event',
                             'caller_semantics': 'activity on_complete non-murder host branch saves '
                                                 'activity_location/root_scope, triggers .7101, then '
                                                 'disburses common rewards in that callback',
                             'caller_lines': 'common/activities/activity_types/feast.txt:4992-5016',
                             'immediate_effect': {'line_range': [1438, 1457],
                                                  'effects': ['save root_scope',
                                                              'grandfeast music cue',
                                                              'if spouse not saved and married: save an '
                                                              'available primary spouse or alternative '
                                                              'available spouse'],
                                                  'reward_disbursement': False,
                                                  'pre_choice_credit': 0},
                             'option_lines': '1460-1468',
                             'option_semantics': {'0': {'native_option_index': 0,
                                                        'api_option_number': 1,
                                                        'name': 'feast.7101.a',
                                                        'line_range': [1460, 1468],
                                                        'shown_actual': True,
                                                        'enabled_actual': True,
                                                        'english_label': "And with that, it's all done.",
                                                        'simp_chinese_label': '就这样，一切都完成了。',
                                                        'authored_ai_chance': None,
                                                        'effects_empty': False,
                                                        'executed_effects': ['hidden_effect '
                                                                             'reveler_lifestyle_rank_up_check_effect=yes'],
                                                        'tooltip_only': ['disburse_feast_activity_rewards=yes, '
                                                                         'including stress/reward '
                                                                         'presentation'],
                                                        'direct_resource_delta': None,
                                                        'conditional_profile': 'Without lifestyle_reveler, '
                                                                               'randomized feast.0050 '
                                                                               'follow-up; helper add_trait '
                                                                               'is tooltip-only. With '
                                                                               'lifestyle_reveler, trait XP '
                                                                               'plus progress reset. Do not '
                                                                               'call the option '
                                                                               'deterministic trait grant or '
                                                                               'stress/prestige payout.'}},
                             'authored_option_name_aliases': ['feast.7101.a'],
                             'native_ai_weights': {'0': 'sole authored option; no ai_chance block'},
                             'localization_sources': {'localization/english/event_localization/activities/feast_events_l_english.yml': '167F119A424BF17525205359BCCE2ED20BDCB3CAB3C1965717D27F331344F5A1',
                                                      'localization/simp_chinese/event_localization/activities/feast_events_l_simp_chinese.yml': 'A33E34631EAB35D5B05BE34DE123D39E173C76866616267467C5049682B3AE7C'},
                             'after_effect': None,
                             'scope_boundary': 'only the actual root=host=root_scope five-scope route; '
                                               'activity/province/activity_location remain opaque and '
                                               'optional spouse variants are not admitted',
                             'common_reward_ownership': {'on_complete_pin': {'relative_path': 'common/activities/activity_types/feast.txt',
                                                                             'key': 'activity_feast:on_complete',
                                                                             'line': 4992,
                                                                             'end_line': 5193,
                                                                             'file_sha256': 'FBC2E6E3F74BC8C2DB1BB1EB01609AA7CF50E9546671A12617301F175BE84598',
                                                                             'raw_file_sha256': 'FBC2E6E3F74BC8C2DB1BB1EB01609AA7CF50E9546671A12617301F175BE84598',
                                                                             'lf_file_sha256': '20256A699E5A77515EF9EE15113796400DA72BE1FE5CB3CAA81A31ECEC7DD008',
                                                                             'block_sha256': '55319395527A581D742013D196182C9B59F6278FD8195B4E0183370176D815B7',
                                                                             'raw_token_block_sha256': '55319395527A581D742013D196182C9B59F6278FD8195B4E0183370176D815B7',
                                                                             'lf_token_block_sha256': '13FC49DAA7F8AD3D511E5819A13260D77E66B9A7708871AAACC070972EB3B66C',
                                                                             'raw_lines_sha256': '2534AA218EC7A8C932D457CC22DC1BFEBAEF9AFF57E673248235110764D60EDD',
                                                                             'lf_lines_sha256': '171DB331E74A1A834C18E240FA4A0322A5776C0EE88FB2F21DE1ECA05A4C8CAB',
                                                                             'ordered_token_sha256': 'C105AFF8692B63055C53F82715999CAE27E9995405F7D20DEF4228A3E14BBB87',
                                                                             'token_count': 515},
                                                         'exact_host_branch': [4992, 5016],
                                                         'source_order': ['save activity_location',
                                                                          'non-murder host branch saves '
                                                                          'root_scope',
                                                                          'trigger_event feast.7101',
                                                                          'disburse_feast_activity_rewards'],
                                                         'reward_body_pin': {'relative_path': 'common/scripted_effects/00_activity_effects.txt',
                                                                             'key': 'disburse_feast_activity_rewards',
                                                                             'line': 3052,
                                                                             'end_line': 3852,
                                                                             'file_sha256': 'D5C594F8746B923D34B13A67DB881821E12F08CE1AB4E6E3F83933419C9E2D38',
                                                                             'raw_file_sha256': 'D5C594F8746B923D34B13A67DB881821E12F08CE1AB4E6E3F83933419C9E2D38',
                                                                             'lf_file_sha256': '0265684CE4394C595B8A91D5F97A40C138207686A959BE20CB839AF73B161471',
                                                                             'block_sha256': 'B3015014E61BD1F08B248630C50E3A9E6B51D83E6201A431CFE68AAEE780870B',
                                                                             'raw_token_block_sha256': 'B3015014E61BD1F08B248630C50E3A9E6B51D83E6201A431CFE68AAEE780870B',
                                                                             'lf_token_block_sha256': '39887D573D8CA959DB73887595F802A0013E74047E3A36517BE498C87A349C4A',
                                                                             'raw_lines_sha256': 'C7835C62CFF7D526C07ECC21DA107F4DFAF401B371EDB1968EA39D6C94A6A566',
                                                                             'lf_lines_sha256': '302D218F22A9F81AFEEA82681961E356F0D6E1B2760DB82047F3B579D56B55B8',
                                                                             'ordered_token_sha256': 'B18900928319458C22E654FCCACD077C4F06BA24F7927DC5AED5E60C3AABF051',
                                                                             'token_count': 1908},
                                                         'boundary': 'Full common reward body frozen for '
                                                                     'ownership/attribution only. No '
                                                                     'resource/helper cascade expansion. '
                                                                     'Feast owner owns prior/post reward and '
                                                                     'hosted-terminal material.'},
                             'common_reward_evidence_boundary': 'callback ownership is source evidence, not '
                                                                'an observed payout or terminal '
                                                                'postcondition from selecting this event',
                             'selected_choice_effect_profile': {'schema': 'xar.ck3.vanilla-event-choice-effect',
                                                                'schema_version': 1,
                                                                'selected_native_option_index': 0,
                                                                'completeness': 'all-authored-options-and-common-after-source-reviewed',
                                                                'selected_option_effects': [{'domain': 'player_character_lifestyle_progress',
                                                                                             'source': 'reveler_lifestyle_rank_up_check_effect',
                                                                                             'hidden_effect': True,
                                                                                             'character_scope': 'root',
                                                                                             'conditional_profile': 'Without '
                                                                                                                    'lifestyle_reveler, '
                                                                                                                    'randomized '
                                                                                                                    'feast.0050 '
                                                                                                                    'follow-up; '
                                                                                                                    'helper '
                                                                                                                    'add_trait '
                                                                                                                    'is '
                                                                                                                    'tooltip-only. '
                                                                                                                    'With '
                                                                                                                    'lifestyle_reveler, '
                                                                                                                    'trait '
                                                                                                                    'XP '
                                                                                                                    'plus '
                                                                                                                    'progress '
                                                                                                                    'reset. '
                                                                                                                    'Do '
                                                                                                                    'not '
                                                                                                                    'call '
                                                                                                                    'the '
                                                                                                                    'option '
                                                                                                                    'deterministic '
                                                                                                                    'trait '
                                                                                                                    'grant '
                                                                                                                    'or '
                                                                                                                    'stress/prestige '
                                                                                                                    'payout.',
                                                                                             'source_helper_semantics': {'line_range': [261,
                                                                                                                                        360],
                                                                                                                         'base_random_chance': 15,
                                                                                                                         'random_additive_modifiers': [{'when': 'rite '
                                                                                                                                                                'treats '
                                                                                                                                                                'reveler '
                                                                                                                                                                'as '
                                                                                                                                                                'sin',
                                                                                                                                                        'add': -10},
                                                                                                                                                       {'when': 'temperate',
                                                                                                                                                        'add': -10},
                                                                                                                                                       {'when': 'inappetetic',
                                                                                                                                                        'add': -10},
                                                                                                                                                       {'when': 'culture '
                                                                                                                                                                'reveler_traits_more_valued',
                                                                                                                                                        'add': 10},
                                                                                                                                                       {'when': 'gluttonous',
                                                                                                                                                        'add': 5},
                                                                                                                                                       {'when': 'drunkard',
                                                                                                                                                        'add': 5},
                                                                                                                                                       {'when': 'comfort_eater',
                                                                                                                                                        'add': 5},
                                                                                                                                                       {'when': 'progress>=7',
                                                                                                                                                        'add': 15},
                                                                                                                                                       {'when': 'progress>=5',
                                                                                                                                                        'add': 15},
                                                                                                                                                       {'when': 'progress>=3',
                                                                                                                                                        'add': 15}],
                                                                                                                         'follow_up': 'feast.0050 '
                                                                                                                                      'only '
                                                                                                                                      'if '
                                                                                                                                      'random '
                                                                                                                                      'branch '
                                                                                                                                      'succeeds; '
                                                                                                                                      'pinned '
                                                                                                                                      'as '
                                                                                                                                      'dependency, '
                                                                                                                                      'not '
                                                                                                                                      'registered '
                                                                                                                                      'or '
                                                                                                                                      'selected '
                                                                                                                                      'in '
                                                                                                                                      'this '
                                                                                                                                      'task',
                                                                                                                         'existing_trait_order': [{'literal_condition': 'NOT '
                                                                                                                                                                        'lifestyle_reveler '
                                                                                                                                                                        'AND '
                                                                                                                                                                        'progress>=7',
                                                                                                                                                   'xp': 10},
                                                                                                                                                  {'literal_condition': 'progress>=5',
                                                                                                                                                   'xp': 5},
                                                                                                                                                  {'literal_condition': 'progress>=3',
                                                                                                                                                   'xp': 3},
                                                                                                                                                  {'literal_condition': 'else',
                                                                                                                                                   'xp': 1}],
                                                                                                                         'literal_source_boundary': 'Preserve '
                                                                                                                                                    'the '
                                                                                                                                                    'NOT '
                                                                                                                                                    'lifestyle_reveler '
                                                                                                                                                    'condition '
                                                                                                                                                    'in '
                                                                                                                                                    'the '
                                                                                                                                                    'existing-trait '
                                                                                                                                                    'else '
                                                                                                                                                    'branch; '
                                                                                                                                                    'no '
                                                                                                                                                    'source '
                                                                                                                                                    'correction '
                                                                                                                                                    'or '
                                                                                                                                                    'engine '
                                                                                                                                                    'behavior '
                                                                                                                                                    'inference.',
                                                                                                                         'existing_trait_final_effect': 'set '
                                                                                                                                                        'reveler_lifestyle_progress=0'}}],
                                                                'common_after_effects': [],
                                                                'observable_postcondition': None,
                                                                'source_anchors': ['events/activities/feast_activity/feast_events.txt:1460-1468',
                                                                                   'common/scripted_effects/00_lifestyle_focus_effects.txt:261-360',
                                                                                   'common/script_values/00_basic_values.txt:1462-1464'],
                                                                'source_sha256': {'events/activities/feast_activity/feast_events.txt': 'F5820211444E7DBAF0A318ADF65BEBF4CA581D3A4E9F381ADD63D3BF02AAF77E',
                                                                                  'common/scripted_effects/00_lifestyle_focus_effects.txt': '051706E95FD0F0535AAA6201941ABFC86DF1C0E44DFCBA6BED5E6D9E94DB849C',
                                                                                  'common/script_values/00_basic_values.txt': 'C379CC0C58ED1574033F0E07A58697DFC6F8475C26AA4B117F2332008D4A27EF',
                                                                                  'common/scripted_effects/00_activity_effects.txt': 'D5C594F8746B923D34B13A67DB881821E12F08CE1AB4E6E3F83933419C9E2D38',
                                                                                  'common/activities/activity_types/feast.txt': 'FBC2E6E3F74BC8C2DB1BB1EB01609AA7CF50E9546671A12617301F175BE84598'},
                                                                'material_evidence_boundary': 'nonempty '
                                                                                              'rank-up '
                                                                                              'helper; '
                                                                                              'disburse '
                                                                                              'rewards occur '
                                                                                              'only in '
                                                                                              'show_as_tooltip '
                                                                                              'in this '
                                                                                              'option; no '
                                                                                              'stress/prestige/button '
                                                                                              'reward, '
                                                                                              'deterministic '
                                                                                              'trait grant, '
                                                                                              'XP outcome or '
                                                                                              'hosted-terminal '
                                                                                              'result is '
                                                                                              'established'},
                             'selected_choice_campaign_utility_profile': {'schema': 'xar.ck3.vanilla-event-campaign-utility',
                                                                          'schema_version': 1,
                                                                          'selected_native_option_index': 0,
                                                                          'objective_id': 'continue_started_feast_completion_modal',
                                                                          'comparison_kind': 'sole_legal_route',
                                                                          'selected_rank': 1,
                                                                          'rank_count': 1,
                                                                          'selected_utility': {'material_direction': 'conditional_reveler_rank_check',
                                                                                               'resource_cost': 'none_authored_in_executed_option',
                                                                                               'outcome_variance': 'conditional_trait_xp_or_random_followup',
                                                                                               'timeline_value': 'required_to_continue_current_modal'},
                                                                          'alternatives': [],
                                                                          'cross_event_numeric_score': None,
                                                                          'calibration_status': 'not_calibrated',
                                                                          'decision_scope': 'bounded_timeline_continuation',
                                                                          'source_sha256': {'events/activities/feast_activity/feast_events.txt': 'F5820211444E7DBAF0A318ADF65BEBF4CA581D3A4E9F381ADD63D3BF02AAF77E',
                                                                                            'common/scripted_effects/00_lifestyle_focus_effects.txt': '051706E95FD0F0535AAA6201941ABFC86DF1C0E44DFCBA6BED5E6D9E94DB849C',
                                                                                            'common/script_values/00_basic_values.txt': 'C379CC0C58ED1574033F0E07A58697DFC6F8475C26AA4B117F2332008D4A27EF',
                                                                                            'common/scripted_effects/00_activity_effects.txt': 'D5C594F8746B923D34B13A67DB881821E12F08CE1AB4E6E3F83933419C9E2D38',
                                                                                            'common/activities/activity_types/feast.txt': 'FBC2E6E3F74BC8C2DB1BB1EB01609AA7CF50E9546671A12617301F175BE84598'},
                                                                          'readiness': 'static-ready',
                                                                          'new_live_evidence': False},
                             'source_review_receipt_sha256': 'B8C5204F938BBC17B73C27A3E97AB58F951270E823661EA0E408ADA9D75A49AA',
                             'readiness': 'static-ready',
                             'new_live_evidence': False,
                             'material_evidence_boundary': 'no resource, trait/XP, live, M2 or terminal '
                                                           'Feast credit from tooltip, title, source helper, '
                                                           'ACK or modal advance; conditional .0050 is a '
                                                           'source dependency, not registered here'},
                'observations': {'exemplars': [{'kind': 'closed-production-red',
                                                'artifact': 'artifacts/g2-maintainer-2026-10-02/resume-12003/m7-robert/feast6003-following-normal30-2c4-v23-actual-01/turn-008/natural-event/003-ck3_query_vanilla_event_knowledge_v1-service-receipt.json',
                                                'artifact_sha256': '78307245632763D421ADABC00B50304539DD7ADDF4F7E7151817B9F478FA82A4',
                                                'typed_context_sha256': 'FAF9A3B74C73BCBBAF2DFD28A4B6F7F7B2E6A34D185B2DB4B5F3392A254FF47C',
                                                'snapshot_sha256': '8860878D0C95A5668F1B0AEE10EE8CB88E2F0DA21485BAE94BC203711BCC17BF',
                                                'event_instance_id': 20,
                                                'root_character_id': 29829,
                                                'date_raw': 53222952,
                                                'selection_attempted': False,
                                                'boundary': 'natural five-scope sole-option modal with '
                                                            'not_registered knowledge; no selected, '
                                                            'trait/XP, resource or terminal outcome in this '
                                                            'record'}]}}}
