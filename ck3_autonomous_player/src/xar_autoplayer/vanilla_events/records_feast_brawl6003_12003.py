"""The reviewed current .3 feast brawl and bounded fighter-two choice."""

from typing import Final

from .registry import PLAYER_SENTINEL


FEAST_BRAWL6003_12003_RECORDS: Final = {'feast_default.6003': {'contract': {'date_policy': 'product-observation-window',
                                     'root_character_id': PLAYER_SENTINEL,
                                     'character_scopes': {'host': PLAYER_SENTINEL},
                                     'scope_types': {'activity': 'activity',
                                                     'host': 'character',
                                                     'province': 'province',
                                                     'fighter_1': 'character',
                                                     'fighter_2': 'character'},
                                     'saved_scope_name_sets': (('activity',
                                                                'host',
                                                                'province',
                                                                'fighter_1',
                                                                'fighter_2'),),
                                     'saved_scope_count': 5,
                                     'option_count': 2,
                                     'snapshot_option_count': 3,
                                     'native_option_indices': (0, 1),
                                     'selected_option_number': 2,
                                     'selected_native_option_index': 1,
                                     'occurrence_policy': 'repeatable-within-product-observation-window'},
                        'analysis': {'exact_build': {'game_version': '1.20.0.3',
                                                     'ck3_executable_sha256': '94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6',
                                                     'steam_build_id': 25652598},
                                     'source_sha256': {'events/activities/feast_activity/main_events/feast_default_events.txt': 'D26B858CEF9CEF76C9E1BF6FB796E2BFA9E103E54853676B0D28A1927052A3F1',
                                                       'common/scripted_triggers/00_feast_activity_triggers.txt': 'B6DDE849AB49F66F78701B4F09E9090EE6E1D81B418EE077EFEF49C950DC2FBA',
                                                       'common/opinion_modifiers/00_activity_feast_opinions.txt': '901D2C588CE01C7B49541B1EDA92EF44CA04CBD0A142FBAFC8927FDEF327F892',
                                                       'common/scripted_effects/00_relation_effects.txt': 'B4668EED284175E67FB7F4DF42D1B2007075DEE25C0F348823C87664545B1891',
                                                       'common/scripted_triggers/00_relation_triggers.txt': '973ED236B5544F56D20D11FF8F2A183527438C32E30FF973FAE54B39AC2DEF44',
                                                       'common/script_values/00_basic_values.txt': 'C379CC0C58ED1574033F0E07A58697DFC6F8475C26AA4B117F2332008D4A27EF'},
                                     'definition_lines': '10043-10183',
                                     'definition_block_sha256': '86104175AF5663FCAE442B51EE9F7D5044C05347400D57A39D98D1B82329B4B4',
                                     'definition_block_hash_convention': 'SourceTree key token through '
                                                                         'closing brace; original newlines '
                                                                         'retained; following newline '
                                                                         'excluded',
                                     'source_dependency_blocks': [{'key': 'feast_default_6003_fighter_1_trigger',
                                                                   'relative_path': 'events/activities/feast_activity/main_events/feast_default_events.txt',
                                                                   'line': 10032,
                                                                   'end_line': 10041,
                                                                   'raw_token_block_sha256': 'A9535D736645E733CE31E980C281A1F74C1BF20F8C61110988F50AF5DD3116D4'},
                                                                  {'key': 'feast_default_6003_fighter_2_temp_trigger',
                                                                   'relative_path': 'events/activities/feast_activity/main_events/feast_default_events.txt',
                                                                   'line': 9975,
                                                                   'end_line': 10001,
                                                                   'raw_token_block_sha256': '6F7F45FFBB784C22E6927DFAE3BE51F6C6D8BAE7868A564528AA2FDC96A88C23'},
                                                                  {'key': 'feast_default_6003_fighter_2_trigger',
                                                                   'relative_path': 'events/activities/feast_activity/main_events/feast_default_events.txt',
                                                                   'line': 10003,
                                                                   'end_line': 10030,
                                                                   'raw_token_block_sha256': '734F5FB8547AD886AC6400EC104C6661066FD53926A35F70D4AB6ACFC3FA663A'},
                                                                  {'key': 'feast_default_participant_trigger',
                                                                   'relative_path': 'common/scripted_triggers/00_feast_activity_triggers.txt',
                                                                   'line': 31,
                                                                   'end_line': 38,
                                                                   'raw_token_block_sha256': 'A847E9F0E9ABE5729998D1CE6ADFA1490EED1BCB61C8F9B1E965E4B617167A33'},
                                                                  {'key': 'feast_sided_with_me_in_my_fight_opinion',
                                                                   'relative_path': 'common/opinion_modifiers/00_activity_feast_opinions.txt',
                                                                   'line': 240,
                                                                   'end_line': 244,
                                                                   'raw_token_block_sha256': '50DA90DE18E1091AD1E8E0444744DE73382D35BA367BC8748CCE6AB615D2EE1C'},
                                                                  {'key': 'feast_sided_against_me_in_my_fight_opinion',
                                                                   'relative_path': 'common/opinion_modifiers/00_activity_feast_opinions.txt',
                                                                   'line': 247,
                                                                   'end_line': 251,
                                                                   'raw_token_block_sha256': '419E133BD3FF20EF2F769CD1D43CFA3425A1E18F37F75B3911950F9E4D3AA97C'},
                                                                  {'key': 'progress_towards_friend_effect',
                                                                   'relative_path': 'common/scripted_effects/00_relation_effects.txt',
                                                                   'line': 31,
                                                                   'end_line': 204,
                                                                   'raw_token_block_sha256': '20E2D3EE40A3D214034723CBAC6909781AF05955A5D9C7A6394C3113C32ED915'},
                                                                  {'key': 'progress_towards_rival_effect',
                                                                   'relative_path': 'common/scripted_effects/00_relation_effects.txt',
                                                                   'line': 207,
                                                                   'end_line': 431,
                                                                   'raw_token_block_sha256': 'BFD74A6A1F83D28D0BB8F793566D90DD828BC1C95AC8B747512F3105AAC0671C'},
                                                                  {'key': 'can_set_relation_potential_friend_trigger',
                                                                   'relative_path': 'common/scripted_triggers/00_relation_triggers.txt',
                                                                   'line': 9,
                                                                   'end_line': 12,
                                                                   'raw_token_block_sha256': 'E63AFF01AA7D077446869154FBB8B5571DC8F81E4BD7A6EED0ACDCA2884CD102'},
                                                                  {'key': 'can_set_relation_friend_trigger',
                                                                   'relative_path': 'common/scripted_triggers/00_relation_triggers.txt',
                                                                   'line': 14,
                                                                   'end_line': 22,
                                                                   'raw_token_block_sha256': 'A1DDA25CB9CD0EB4A9C62DF9EB29F3CFADC41D1D725D8A597680BC706654B3E4'},
                                                                  {'key': 'can_set_relation_potential_rival_trigger',
                                                                   'relative_path': 'common/scripted_triggers/00_relation_triggers.txt',
                                                                   'line': 82,
                                                                   'end_line': 85,
                                                                   'raw_token_block_sha256': '6E5E8D18A64164C52D0B8F7D6EAA618D00BFE1C94FA746A7C87DCA9E5E05A16C'},
                                                                  {'key': 'can_set_relation_rival_if_adult_trigger',
                                                                   'relative_path': 'common/scripted_triggers/00_relation_triggers.txt',
                                                                   'line': 87,
                                                                   'end_line': 95,
                                                                   'raw_token_block_sha256': 'D2F95E4095DE226F0D526923F70FBCF055CD44DCA8FDC606C6F8D16E2A8E3C8F'},
                                                                  {'key': 'can_set_relation_rival_trigger',
                                                                   'relative_path': 'common/scripted_triggers/00_relation_triggers.txt',
                                                                   'line': 97,
                                                                   'end_line': 101,
                                                                   'raw_token_block_sha256': 'B6BB355E7F8EE712AA488034858EC594A2E779CA4E7EB286615FE3D3315C87EC'},
                                                                  {'key': 'medium_prestige_value',
                                                                   'relative_path': 'common/script_values/00_basic_values.txt',
                                                                   'line': 1002,
                                                                   'end_line': 1002,
                                                                   'raw_token_block_sha256': '63502C6C06F8E8C256319B7E9FD4974E69340476B1B9B2DAA3A38E47FEDD60E6'},
                                                                  {'key': 'medium_prestige_gain',
                                                                   'relative_path': 'common/script_values/00_basic_values.txt',
                                                                   'line': 1035,
                                                                   'end_line': 1035,
                                                                   'raw_token_block_sha256': '15DF1EFF9F32E16C3F5C7473754944BB1119315DC8749AABAF04778192E773DE'}],
                                     'event_type': 'activity_event',
                                     'caller_semantics': 'unknown: Exact key in installed events finds '
                                                         'definition/inline gates; exact key in '
                                                         'common/activities had no textual caller. No native '
                                                         'scheduler/PE or broader audit was performed.',
                                     'caller_boundary': 'actual natural materialization permits bounded '
                                                        'continuation; unknown incoming caller adds no '
                                                        'decision gate',
                                     'trigger_semantics': {'cooldown_years': 1,
                                                           'ai_only_filter': 'If is_ai=yes '
                                                                             'static_group_filter '
                                                                             'groupfeast_default.6003 '
                                                                             'match0.1',
                                                           'local_gates': 'No local had6003/had6351',
                                                           'pair_criteria': 'Eligible alive/nonimprisoned AI '
                                                                            'attending characters other than '
                                                                            'root; fighter2 distinct '
                                                                            'fromfighter1 and rival OR '
                                                                            'mutually opinion<=-20 plus '
                                                                            'bothfemale/bothmale branch.',
                                                           'immediate': 'Set local had6003=yes; choose '
                                                                        'random eligiblefighter1, then '
                                                                        'distinct eligiblefighter2; save '
                                                                        'scopes. Pre-choice selection/local '
                                                                        'flag are not new option outcomes.',
                                                           'after': None},
                                     'immediate_effect': 'Set local had6003=yes; choose random '
                                                         'eligiblefighter1, then distinct eligiblefighter2; '
                                                         'save scopes. Pre-choice selection/local flag are '
                                                         'not new option outcomes.',
                                     'immediate_evidence_boundary': 'participant selection and local flag '
                                                                    'precede the choice and receive no '
                                                                    'option outcome credit',
                                     'option_semantics': {'0': {'native_option_index': 0,
                                                                'api_option_number': 1,
                                                                'name': 'feast_default.6003.a',
                                                                'line_range': [10109, 10140],
                                                                'shown_actual': True,
                                                                'backed_scope': 'fighter_1',
                                                                'opposed_scope': 'fighter_2',
                                                                'effects': {'backed_opinion_toward_player': 20,
                                                                            'backed_opinion_duration_years': 20,
                                                                            'backed_relation': 'progress_towards_friend_effect '
                                                                                               'withOPINION0/reasonfriend_took_side_in_fight',
                                                                            'opposed_opinion_toward_player': -20,
                                                                            'opposed_opinion_duration_years': 15,
                                                                            'opposed_relation': 'progress_towards_rival_effect '
                                                                                                'withOPINION0/reasonrival_other_fighter_side'},
                                                                'ai_chance': {'base': 100,
                                                                              'opinion_modifier': {'opinion_target': 'fighter_1',
                                                                                                   'min': -99},
                                                                              'modifier': {'add': 500,
                                                                                           'has_relation_friend': 'fighter_1'}}},
                                                          '1': {'native_option_index': 1,
                                                                'api_option_number': 2,
                                                                'name': 'feast_default.6003.b',
                                                                'line_range': [10142, 10173],
                                                                'shown_actual': True,
                                                                'backed_scope': 'fighter_2',
                                                                'opposed_scope': 'fighter_1',
                                                                'effects': {'backed_opinion_toward_player': 20,
                                                                            'backed_opinion_duration_years': 20,
                                                                            'backed_relation': 'progress_towards_friend_effect '
                                                                                               'withOPINION0/reasonfriend_took_side_in_fight',
                                                                            'opposed_opinion_toward_player': -20,
                                                                            'opposed_opinion_duration_years': 15,
                                                                            'opposed_relation': 'progress_towards_rival_effect '
                                                                                                'withOPINION0/reasonrival_other_fighter_side'},
                                                                'ai_chance': {'base': 100,
                                                                              'opinion_modifier': {'opinion_target': 'fighter_1',
                                                                                                   'min': -99},
                                                                              'modifier': {'add': 500,
                                                                                           'has_relation_friend': 'fighter_1'}},
                                                                'literal_source_warning': 'Both native1 AI '
                                                                                          'entries '
                                                                                          'namefighter1, '
                                                                                          'notfighter2. '
                                                                                          'Preserve exact '
                                                                                          'source rather '
                                                                                          'than silently '
                                                                                          'symmetrizing it.'},
                                                          '2': {'native_option_index': 2,
                                                                'api_option_number': 3,
                                                                'name': 'feast_default.6003.c',
                                                                'line_range': [10175, 10182],
                                                                'shown_actual': False,
                                                                'trigger': 'diplomacy>=15',
                                                                'skill': 'diplomacy',
                                                                'effects': {'prestige_gain': 150},
                                                                'ai_chance': None,
                                                                'eligibility_boundary': 'Not an actual '
                                                                                        'candidate; raw '
                                                                                        'snapshot '
                                                                                        'option_count3/enabled '
                                                                                        'flags do not '
                                                                                        'override '
                                                                                        'presentation.'}},
                                     'authored_option_name_aliases': ['feast_default.6003.a',
                                                                      'feast_default.6003.b',
                                                                      'feast_default.6003.c'],
                                     'native_ai_weights': {'0': {'base': 100,
                                                                 'opinion_modifier': {'opinion_target': 'fighter_1',
                                                                                      'min': -99},
                                                                 'modifier': {'add': 500,
                                                                              'has_relation_friend': 'fighter_1'}},
                                                           '1': {'base': 100,
                                                                 'opinion_modifier': {'opinion_target': 'fighter_1',
                                                                                      'min': -99},
                                                                 'modifier': {'add': 500,
                                                                              'has_relation_friend': 'fighter_1'}},
                                                           '2': None},
                                     'native_ai_quality_boundary': 'both native0 and native1 literally '
                                                                   'target fighter_1 in their opinion and '
                                                                   'friend weights; these weights do not '
                                                                   'establish a preference for native1',
                                     'localization_sources': {'localization/english/event_localization/activities/feast_default_events_l_english.yml': 'F93DFC48CE2D0D45947AFB0E918855B6CBC2CBBBEEC7578FE3E894BDD82F3004',
                                                              'localization/simp_chinese/event_localization/activities/feast_default_events_l_simp_chinese.yml': 'EA35C5F94BC872B0C5F3D1496ED78030C7FEDED6EAAEF6F49C90C03C288BF6FA'},
                                     'after_effect': None,
                                     'scope_boundary': 'actual root=host five-scope route with only '
                                                       'native0/1 rendered; fighter identities remain '
                                                       'dynamic and activity/province remain opaque; hidden '
                                                       'native2 is not admitted',
                                     'authored_option_effect_profiles': {'0': {'schema': 'xar.ck3.vanilla-event-choice-effect',
                                                                               'schema_version': 1,
                                                                               'selected_native_option_index': 0,
                                                                               'completeness': 'all-authored-options-and-common-after-source-reviewed',
                                                                               'selected_option_effects': [{'domain': 'relationship_opinion',
                                                                                                            'source': 'reverse_add_opinion',
                                                                                                            'character_scope': 'fighter_1',
                                                                                                            'target_scope': 'root',
                                                                                                            'modifier_key': 'feast_sided_with_me_in_my_fight_opinion',
                                                                                                            'authored_opinion': 20,
                                                                                                            'duration_years': 20,
                                                                                                            'decaying': True},
                                                                                                           {'domain': 'relationship_progress',
                                                                                                            'source': 'progress_towards_friend_effect',
                                                                                                            'character_scope': 'root',
                                                                                                            'target_scope': 'fighter_1',
                                                                                                            'opinion_parameter': 0,
                                                                                                            'reason': 'friend_took_side_in_fight',
                                                                                                            'conditional_result': 'Existing '
                                                                                                                                  'potentialfriend '
                                                                                                                                  'and '
                                                                                                                                  'can_set_friend '
                                                                                                                                  'upgrades '
                                                                                                                                  'to '
                                                                                                                                  'friend; '
                                                                                                                                  'otherwise '
                                                                                                                                  'sets '
                                                                                                                                  'potentialfriend '
                                                                                                                                  'if '
                                                                                                                                  'allowed. '
                                                                                                                                  'OPINION0 '
                                                                                                                                  'suppresses '
                                                                                                                                  'ordinary '
                                                                                                                                  'friendliness_opinion '
                                                                                                                                  'writes. '
                                                                                                                                  'Possible '
                                                                                                                                  'befriend '
                                                                                                                                  'intent '
                                                                                                                                  'completion/logging '
                                                                                                                                  'remains '
                                                                                                                                  'conditional.'},
                                                                                                           {'domain': 'relationship_opinion',
                                                                                                            'source': 'reverse_add_opinion',
                                                                                                            'character_scope': 'fighter_2',
                                                                                                            'target_scope': 'root',
                                                                                                            'modifier_key': 'feast_sided_against_me_in_my_fight_opinion',
                                                                                                            'authored_opinion': -20,
                                                                                                            'duration_years': 15,
                                                                                                            'decaying': True},
                                                                                                           {'domain': 'relationship_progress',
                                                                                                            'source': 'progress_towards_rival_effect',
                                                                                                            'character_scope': 'root',
                                                                                                            'target_scope': 'fighter_2',
                                                                                                            'opinion_parameter': 0,
                                                                                                            'reason': 'rival_other_fighter_side',
                                                                                                            'conditional_grudge_opinion_direction': 'root_to_opposed_character',
                                                                                                            'conditional_grudge_opinion': -20,
                                                                                                            'conditional_result': 'Tier/family/heir '
                                                                                                                                  'asymmetry '
                                                                                                                                  'can '
                                                                                                                                  'setgrudge '
                                                                                                                                  'or '
                                                                                                                                  'add '
                                                                                                                                  'root→target '
                                                                                                                                  'grudge '
                                                                                                                                  'opinion-20 '
                                                                                                                                  'when '
                                                                                                                                  'alreadygrudging; '
                                                                                                                                  'otherwise '
                                                                                                                                  'existing '
                                                                                                                                  'potentialrival '
                                                                                                                                  'upgrades '
                                                                                                                                  'to '
                                                                                                                                  'rival '
                                                                                                                                  'when '
                                                                                                                                  'allowed '
                                                                                                                                  'or '
                                                                                                                                  'creates '
                                                                                                                                  'potentialrival. '
                                                                                                                                  'OPINION0 '
                                                                                                                                  'suppresses '
                                                                                                                                  'ordinary '
                                                                                                                                  'hate_opinion '
                                                                                                                                  'writes, '
                                                                                                                                  'not '
                                                                                                                                  'the '
                                                                                                                                  'explicit '
                                                                                                                                  'grudge '
                                                                                                                                  'branch.'}],
                                                                               'common_after_effects': [],
                                                                               'observable_postcondition': None,
                                                                               'source_anchors': ['events/activities/feast_activity/main_events/feast_default_events.txt:10109-10140',
                                                                                                  'events/activities/feast_activity/main_events/feast_default_events.txt:10032-10041',
                                                                                                  'events/activities/feast_activity/main_events/feast_default_events.txt:9975-10001',
                                                                                                  'events/activities/feast_activity/main_events/feast_default_events.txt:10003-10030',
                                                                                                  'common/scripted_triggers/00_feast_activity_triggers.txt:31-38',
                                                                                                  'common/opinion_modifiers/00_activity_feast_opinions.txt:240-244',
                                                                                                  'common/opinion_modifiers/00_activity_feast_opinions.txt:247-251',
                                                                                                  'common/scripted_effects/00_relation_effects.txt:31-204',
                                                                                                  'common/scripted_effects/00_relation_effects.txt:207-431',
                                                                                                  'common/scripted_triggers/00_relation_triggers.txt:9-12',
                                                                                                  'common/scripted_triggers/00_relation_triggers.txt:14-22',
                                                                                                  'common/scripted_triggers/00_relation_triggers.txt:82-85',
                                                                                                  'common/scripted_triggers/00_relation_triggers.txt:87-95',
                                                                                                  'common/scripted_triggers/00_relation_triggers.txt:97-101',
                                                                                                  'common/script_values/00_basic_values.txt:1002-1002',
                                                                                                  'common/script_values/00_basic_values.txt:1035-1035'],
                                                                               'source_sha256': {'events/activities/feast_activity/main_events/feast_default_events.txt': 'D26B858CEF9CEF76C9E1BF6FB796E2BFA9E103E54853676B0D28A1927052A3F1',
                                                                                                 'common/scripted_triggers/00_feast_activity_triggers.txt': 'B6DDE849AB49F66F78701B4F09E9090EE6E1D81B418EE077EFEF49C950DC2FBA',
                                                                                                 'common/opinion_modifiers/00_activity_feast_opinions.txt': '901D2C588CE01C7B49541B1EDA92EF44CA04CBD0A142FBAFC8927FDEF327F892',
                                                                                                 'common/scripted_effects/00_relation_effects.txt': 'B4668EED284175E67FB7F4DF42D1B2007075DEE25C0F348823C87664545B1891',
                                                                                                 'common/scripted_triggers/00_relation_triggers.txt': '973ED236B5544F56D20D11FF8F2A183527438C32E30FF973FAE54B39AC2DEF44',
                                                                                                 'common/script_values/00_basic_values.txt': 'C379CC0C58ED1574033F0E07A58697DFC6F8475C26AA4B117F2332008D4A27EF'},
                                                                               'material_evidence_boundary': 'authored '
                                                                                                             'modifiers '
                                                                                                             'and '
                                                                                                             'conditional '
                                                                                                             'helpers '
                                                                                                             'do '
                                                                                                             'not '
                                                                                                             'establish '
                                                                                                             'total '
                                                                                                             'opinion '
                                                                                                             'deltas '
                                                                                                             'or '
                                                                                                             'friend/rival/grudge '
                                                                                                             'outcomes; '
                                                                                                             'current '
                                                                                                             'visible '
                                                                                                             'route '
                                                                                                             'has '
                                                                                                             'no '
                                                                                                             'matching '
                                                                                                             'generic '
                                                                                                             'material '
                                                                                                             'comparator'},
                                                                         '1': {'schema': 'xar.ck3.vanilla-event-choice-effect',
                                                                               'schema_version': 1,
                                                                               'selected_native_option_index': 1,
                                                                               'completeness': 'all-authored-options-and-common-after-source-reviewed',
                                                                               'selected_option_effects': [{'domain': 'relationship_opinion',
                                                                                                            'source': 'reverse_add_opinion',
                                                                                                            'character_scope': 'fighter_2',
                                                                                                            'target_scope': 'root',
                                                                                                            'modifier_key': 'feast_sided_with_me_in_my_fight_opinion',
                                                                                                            'authored_opinion': 20,
                                                                                                            'duration_years': 20,
                                                                                                            'decaying': True},
                                                                                                           {'domain': 'relationship_progress',
                                                                                                            'source': 'progress_towards_friend_effect',
                                                                                                            'character_scope': 'root',
                                                                                                            'target_scope': 'fighter_2',
                                                                                                            'opinion_parameter': 0,
                                                                                                            'reason': 'friend_took_side_in_fight',
                                                                                                            'conditional_result': 'Existing '
                                                                                                                                  'potentialfriend '
                                                                                                                                  'and '
                                                                                                                                  'can_set_friend '
                                                                                                                                  'upgrades '
                                                                                                                                  'to '
                                                                                                                                  'friend; '
                                                                                                                                  'otherwise '
                                                                                                                                  'sets '
                                                                                                                                  'potentialfriend '
                                                                                                                                  'if '
                                                                                                                                  'allowed. '
                                                                                                                                  'OPINION0 '
                                                                                                                                  'suppresses '
                                                                                                                                  'ordinary '
                                                                                                                                  'friendliness_opinion '
                                                                                                                                  'writes. '
                                                                                                                                  'Possible '
                                                                                                                                  'befriend '
                                                                                                                                  'intent '
                                                                                                                                  'completion/logging '
                                                                                                                                  'remains '
                                                                                                                                  'conditional.'},
                                                                                                           {'domain': 'relationship_opinion',
                                                                                                            'source': 'reverse_add_opinion',
                                                                                                            'character_scope': 'fighter_1',
                                                                                                            'target_scope': 'root',
                                                                                                            'modifier_key': 'feast_sided_against_me_in_my_fight_opinion',
                                                                                                            'authored_opinion': -20,
                                                                                                            'duration_years': 15,
                                                                                                            'decaying': True},
                                                                                                           {'domain': 'relationship_progress',
                                                                                                            'source': 'progress_towards_rival_effect',
                                                                                                            'character_scope': 'root',
                                                                                                            'target_scope': 'fighter_1',
                                                                                                            'opinion_parameter': 0,
                                                                                                            'reason': 'rival_other_fighter_side',
                                                                                                            'conditional_grudge_opinion_direction': 'root_to_opposed_character',
                                                                                                            'conditional_grudge_opinion': -20,
                                                                                                            'conditional_result': 'Tier/family/heir '
                                                                                                                                  'asymmetry '
                                                                                                                                  'can '
                                                                                                                                  'setgrudge '
                                                                                                                                  'or '
                                                                                                                                  'add '
                                                                                                                                  'root→target '
                                                                                                                                  'grudge '
                                                                                                                                  'opinion-20 '
                                                                                                                                  'when '
                                                                                                                                  'alreadygrudging; '
                                                                                                                                  'otherwise '
                                                                                                                                  'existing '
                                                                                                                                  'potentialrival '
                                                                                                                                  'upgrades '
                                                                                                                                  'to '
                                                                                                                                  'rival '
                                                                                                                                  'when '
                                                                                                                                  'allowed '
                                                                                                                                  'or '
                                                                                                                                  'creates '
                                                                                                                                  'potentialrival. '
                                                                                                                                  'OPINION0 '
                                                                                                                                  'suppresses '
                                                                                                                                  'ordinary '
                                                                                                                                  'hate_opinion '
                                                                                                                                  'writes, '
                                                                                                                                  'not '
                                                                                                                                  'the '
                                                                                                                                  'explicit '
                                                                                                                                  'grudge '
                                                                                                                                  'branch.'}],
                                                                               'common_after_effects': [],
                                                                               'observable_postcondition': None,
                                                                               'source_anchors': ['events/activities/feast_activity/main_events/feast_default_events.txt:10142-10173',
                                                                                                  'events/activities/feast_activity/main_events/feast_default_events.txt:10032-10041',
                                                                                                  'events/activities/feast_activity/main_events/feast_default_events.txt:9975-10001',
                                                                                                  'events/activities/feast_activity/main_events/feast_default_events.txt:10003-10030',
                                                                                                  'common/scripted_triggers/00_feast_activity_triggers.txt:31-38',
                                                                                                  'common/opinion_modifiers/00_activity_feast_opinions.txt:240-244',
                                                                                                  'common/opinion_modifiers/00_activity_feast_opinions.txt:247-251',
                                                                                                  'common/scripted_effects/00_relation_effects.txt:31-204',
                                                                                                  'common/scripted_effects/00_relation_effects.txt:207-431',
                                                                                                  'common/scripted_triggers/00_relation_triggers.txt:9-12',
                                                                                                  'common/scripted_triggers/00_relation_triggers.txt:14-22',
                                                                                                  'common/scripted_triggers/00_relation_triggers.txt:82-85',
                                                                                                  'common/scripted_triggers/00_relation_triggers.txt:87-95',
                                                                                                  'common/scripted_triggers/00_relation_triggers.txt:97-101',
                                                                                                  'common/script_values/00_basic_values.txt:1002-1002',
                                                                                                  'common/script_values/00_basic_values.txt:1035-1035'],
                                                                               'source_sha256': {'events/activities/feast_activity/main_events/feast_default_events.txt': 'D26B858CEF9CEF76C9E1BF6FB796E2BFA9E103E54853676B0D28A1927052A3F1',
                                                                                                 'common/scripted_triggers/00_feast_activity_triggers.txt': 'B6DDE849AB49F66F78701B4F09E9090EE6E1D81B418EE077EFEF49C950DC2FBA',
                                                                                                 'common/opinion_modifiers/00_activity_feast_opinions.txt': '901D2C588CE01C7B49541B1EDA92EF44CA04CBD0A142FBAFC8927FDEF327F892',
                                                                                                 'common/scripted_effects/00_relation_effects.txt': 'B4668EED284175E67FB7F4DF42D1B2007075DEE25C0F348823C87664545B1891',
                                                                                                 'common/scripted_triggers/00_relation_triggers.txt': '973ED236B5544F56D20D11FF8F2A183527438C32E30FF973FAE54B39AC2DEF44',
                                                                                                 'common/script_values/00_basic_values.txt': 'C379CC0C58ED1574033F0E07A58697DFC6F8475C26AA4B117F2332008D4A27EF'},
                                                                               'material_evidence_boundary': 'authored '
                                                                                                             'modifiers '
                                                                                                             'and '
                                                                                                             'conditional '
                                                                                                             'helpers '
                                                                                                             'do '
                                                                                                             'not '
                                                                                                             'establish '
                                                                                                             'total '
                                                                                                             'opinion '
                                                                                                             'deltas '
                                                                                                             'or '
                                                                                                             'friend/rival/grudge '
                                                                                                             'outcomes; '
                                                                                                             'current '
                                                                                                             'visible '
                                                                                                             'route '
                                                                                                             'has '
                                                                                                             'no '
                                                                                                             'matching '
                                                                                                             'generic '
                                                                                                             'material '
                                                                                                             'comparator'},
                                                                         '2': {'schema': 'xar.ck3.vanilla-event-choice-effect',
                                                                               'schema_version': 1,
                                                                               'selected_native_option_index': 2,
                                                                               'completeness': 'all-authored-options-and-common-after-source-reviewed',
                                                                               'selected_option_effects': [{'domain': 'player_character_prestige',
                                                                                                            'source': 'add_prestige',
                                                                                                            'base_script_value': 'medium_prestige_gain',
                                                                                                            'authored_value': 150,
                                                                                                            'eligibility_boundary': 'diplomacy>=15; '
                                                                                                                                    'native2 '
                                                                                                                                    'is '
                                                                                                                                    'not '
                                                                                                                                    'rendered '
                                                                                                                                    'in '
                                                                                                                                    'the '
                                                                                                                                    'current '
                                                                                                                                    'route'}],
                                                                               'common_after_effects': [],
                                                                               'observable_postcondition': None,
                                                                               'source_anchors': ['events/activities/feast_activity/main_events/feast_default_events.txt:10175-10182',
                                                                                                  'events/activities/feast_activity/main_events/feast_default_events.txt:10032-10041',
                                                                                                  'events/activities/feast_activity/main_events/feast_default_events.txt:9975-10001',
                                                                                                  'events/activities/feast_activity/main_events/feast_default_events.txt:10003-10030',
                                                                                                  'common/scripted_triggers/00_feast_activity_triggers.txt:31-38',
                                                                                                  'common/opinion_modifiers/00_activity_feast_opinions.txt:240-244',
                                                                                                  'common/opinion_modifiers/00_activity_feast_opinions.txt:247-251',
                                                                                                  'common/scripted_effects/00_relation_effects.txt:31-204',
                                                                                                  'common/scripted_effects/00_relation_effects.txt:207-431',
                                                                                                  'common/scripted_triggers/00_relation_triggers.txt:9-12',
                                                                                                  'common/scripted_triggers/00_relation_triggers.txt:14-22',
                                                                                                  'common/scripted_triggers/00_relation_triggers.txt:82-85',
                                                                                                  'common/scripted_triggers/00_relation_triggers.txt:87-95',
                                                                                                  'common/scripted_triggers/00_relation_triggers.txt:97-101',
                                                                                                  'common/script_values/00_basic_values.txt:1002-1002',
                                                                                                  'common/script_values/00_basic_values.txt:1035-1035'],
                                                                               'source_sha256': {'events/activities/feast_activity/main_events/feast_default_events.txt': 'D26B858CEF9CEF76C9E1BF6FB796E2BFA9E103E54853676B0D28A1927052A3F1',
                                                                                                 'common/scripted_triggers/00_feast_activity_triggers.txt': 'B6DDE849AB49F66F78701B4F09E9090EE6E1D81B418EE077EFEF49C950DC2FBA',
                                                                                                 'common/opinion_modifiers/00_activity_feast_opinions.txt': '901D2C588CE01C7B49541B1EDA92EF44CA04CBD0A142FBAFC8927FDEF327F892',
                                                                                                 'common/scripted_effects/00_relation_effects.txt': 'B4668EED284175E67FB7F4DF42D1B2007075DEE25C0F348823C87664545B1891',
                                                                                                 'common/scripted_triggers/00_relation_triggers.txt': '973ED236B5544F56D20D11FF8F2A183527438C32E30FF973FAE54B39AC2DEF44',
                                                                                                 'common/script_values/00_basic_values.txt': 'C379CC0C58ED1574033F0E07A58697DFC6F8475C26AA4B117F2332008D4A27EF'},
                                                                               'material_evidence_boundary': 'authored '
                                                                                                             'modifiers '
                                                                                                             'and '
                                                                                                             'conditional '
                                                                                                             'helpers '
                                                                                                             'do '
                                                                                                             'not '
                                                                                                             'establish '
                                                                                                             'total '
                                                                                                             'opinion '
                                                                                                             'deltas '
                                                                                                             'or '
                                                                                                             'friend/rival/grudge '
                                                                                                             'outcomes; '
                                                                                                             'current '
                                                                                                             'visible '
                                                                                                             'route '
                                                                                                             'has '
                                                                                                             'no '
                                                                                                             'matching '
                                                                                                             'generic '
                                                                                                             'material '
                                                                                                             'comparator'}},
                                     'selected_choice_effect_profile': {'schema': 'xar.ck3.vanilla-event-choice-effect',
                                                                        'schema_version': 1,
                                                                        'selected_native_option_index': 1,
                                                                        'completeness': 'all-authored-options-and-common-after-source-reviewed',
                                                                        'selected_option_effects': [{'domain': 'relationship_opinion',
                                                                                                     'source': 'reverse_add_opinion',
                                                                                                     'character_scope': 'fighter_2',
                                                                                                     'target_scope': 'root',
                                                                                                     'modifier_key': 'feast_sided_with_me_in_my_fight_opinion',
                                                                                                     'authored_opinion': 20,
                                                                                                     'duration_years': 20,
                                                                                                     'decaying': True},
                                                                                                    {'domain': 'relationship_progress',
                                                                                                     'source': 'progress_towards_friend_effect',
                                                                                                     'character_scope': 'root',
                                                                                                     'target_scope': 'fighter_2',
                                                                                                     'opinion_parameter': 0,
                                                                                                     'reason': 'friend_took_side_in_fight',
                                                                                                     'conditional_result': 'Existing '
                                                                                                                           'potentialfriend '
                                                                                                                           'and '
                                                                                                                           'can_set_friend '
                                                                                                                           'upgrades '
                                                                                                                           'to '
                                                                                                                           'friend; '
                                                                                                                           'otherwise '
                                                                                                                           'sets '
                                                                                                                           'potentialfriend '
                                                                                                                           'if '
                                                                                                                           'allowed. '
                                                                                                                           'OPINION0 '
                                                                                                                           'suppresses '
                                                                                                                           'ordinary '
                                                                                                                           'friendliness_opinion '
                                                                                                                           'writes. '
                                                                                                                           'Possible '
                                                                                                                           'befriend '
                                                                                                                           'intent '
                                                                                                                           'completion/logging '
                                                                                                                           'remains '
                                                                                                                           'conditional.'},
                                                                                                    {'domain': 'relationship_opinion',
                                                                                                     'source': 'reverse_add_opinion',
                                                                                                     'character_scope': 'fighter_1',
                                                                                                     'target_scope': 'root',
                                                                                                     'modifier_key': 'feast_sided_against_me_in_my_fight_opinion',
                                                                                                     'authored_opinion': -20,
                                                                                                     'duration_years': 15,
                                                                                                     'decaying': True},
                                                                                                    {'domain': 'relationship_progress',
                                                                                                     'source': 'progress_towards_rival_effect',
                                                                                                     'character_scope': 'root',
                                                                                                     'target_scope': 'fighter_1',
                                                                                                     'opinion_parameter': 0,
                                                                                                     'reason': 'rival_other_fighter_side',
                                                                                                     'conditional_grudge_opinion_direction': 'root_to_opposed_character',
                                                                                                     'conditional_grudge_opinion': -20,
                                                                                                     'conditional_result': 'Tier/family/heir '
                                                                                                                           'asymmetry '
                                                                                                                           'can '
                                                                                                                           'setgrudge '
                                                                                                                           'or '
                                                                                                                           'add '
                                                                                                                           'root→target '
                                                                                                                           'grudge '
                                                                                                                           'opinion-20 '
                                                                                                                           'when '
                                                                                                                           'alreadygrudging; '
                                                                                                                           'otherwise '
                                                                                                                           'existing '
                                                                                                                           'potentialrival '
                                                                                                                           'upgrades '
                                                                                                                           'to '
                                                                                                                           'rival '
                                                                                                                           'when '
                                                                                                                           'allowed '
                                                                                                                           'or '
                                                                                                                           'creates '
                                                                                                                           'potentialrival. '
                                                                                                                           'OPINION0 '
                                                                                                                           'suppresses '
                                                                                                                           'ordinary '
                                                                                                                           'hate_opinion '
                                                                                                                           'writes, '
                                                                                                                           'not '
                                                                                                                           'the '
                                                                                                                           'explicit '
                                                                                                                           'grudge '
                                                                                                                           'branch.'}],
                                                                        'common_after_effects': [],
                                                                        'observable_postcondition': None,
                                                                        'source_anchors': ['events/activities/feast_activity/main_events/feast_default_events.txt:10142-10173',
                                                                                           'events/activities/feast_activity/main_events/feast_default_events.txt:10032-10041',
                                                                                           'events/activities/feast_activity/main_events/feast_default_events.txt:9975-10001',
                                                                                           'events/activities/feast_activity/main_events/feast_default_events.txt:10003-10030',
                                                                                           'common/scripted_triggers/00_feast_activity_triggers.txt:31-38',
                                                                                           'common/opinion_modifiers/00_activity_feast_opinions.txt:240-244',
                                                                                           'common/opinion_modifiers/00_activity_feast_opinions.txt:247-251',
                                                                                           'common/scripted_effects/00_relation_effects.txt:31-204',
                                                                                           'common/scripted_effects/00_relation_effects.txt:207-431',
                                                                                           'common/scripted_triggers/00_relation_triggers.txt:9-12',
                                                                                           'common/scripted_triggers/00_relation_triggers.txt:14-22',
                                                                                           'common/scripted_triggers/00_relation_triggers.txt:82-85',
                                                                                           'common/scripted_triggers/00_relation_triggers.txt:87-95',
                                                                                           'common/scripted_triggers/00_relation_triggers.txt:97-101',
                                                                                           'common/script_values/00_basic_values.txt:1002-1002',
                                                                                           'common/script_values/00_basic_values.txt:1035-1035'],
                                                                        'source_sha256': {'events/activities/feast_activity/main_events/feast_default_events.txt': 'D26B858CEF9CEF76C9E1BF6FB796E2BFA9E103E54853676B0D28A1927052A3F1',
                                                                                          'common/scripted_triggers/00_feast_activity_triggers.txt': 'B6DDE849AB49F66F78701B4F09E9090EE6E1D81B418EE077EFEF49C950DC2FBA',
                                                                                          'common/opinion_modifiers/00_activity_feast_opinions.txt': '901D2C588CE01C7B49541B1EDA92EF44CA04CBD0A142FBAFC8927FDEF327F892',
                                                                                          'common/scripted_effects/00_relation_effects.txt': 'B4668EED284175E67FB7F4DF42D1B2007075DEE25C0F348823C87664545B1891',
                                                                                          'common/scripted_triggers/00_relation_triggers.txt': '973ED236B5544F56D20D11FF8F2A183527438C32E30FF973FAE54B39AC2DEF44',
                                                                                          'common/script_values/00_basic_values.txt': 'C379CC0C58ED1574033F0E07A58697DFC6F8475C26AA4B117F2332008D4A27EF'},
                                                                        'material_evidence_boundary': 'authored '
                                                                                                      'modifiers '
                                                                                                      'and '
                                                                                                      'conditional '
                                                                                                      'helpers '
                                                                                                      'do '
                                                                                                      'not '
                                                                                                      'establish '
                                                                                                      'total '
                                                                                                      'opinion '
                                                                                                      'deltas '
                                                                                                      'or '
                                                                                                      'friend/rival/grudge '
                                                                                                      'outcomes; '
                                                                                                      'current '
                                                                                                      'visible '
                                                                                                      'route '
                                                                                                      'has '
                                                                                                      'no '
                                                                                                      'matching '
                                                                                                      'generic '
                                                                                                      'material '
                                                                                                      'comparator'},
                                     'selected_choice_campaign_utility_profile': {'schema': 'xar.ck3.vanilla-event-campaign-utility',
                                                                                  'schema_version': 1,
                                                                                  'selected_native_option_index': 1,
                                                                                  'objective_id': 'continue_started_feast_balance_current_guest_cooperation',
                                                                                  'comparison_kind': 'source_reviewed_ordinal',
                                                                                  'selected_rank': 1,
                                                                                  'rank_count': 2,
                                                                                  'selected_utility': {'material_direction': 'support_fighter_2_and_oppose_fighter_1',
                                                                                                       'resource_cost': 'none_authored',
                                                                                                       'outcome_variance': 'conditional_friend_rival_grudge_and_total_opinion_caps',
                                                                                                       'timeline_value': 'required_to_continue_started_feast'},
                                                                                  'alternatives': [{'native_option_index': 0,
                                                                                                    'rank': 2,
                                                                                                    'tradeoff': 'supports '
                                                                                                                'fighter_1 '
                                                                                                                'and '
                                                                                                                'opposes '
                                                                                                                'fighter_2; '
                                                                                                                'root '
                                                                                                                'selected '
                                                                                                                'the '
                                                                                                                'reverse '
                                                                                                                'for '
                                                                                                                'the '
                                                                                                                'current '
                                                                                                                'observed '
                                                                                                                'cooperation '
                                                                                                                'balance'}],
                                                                                  'selection_basis': 'ROOT '
                                                                                                     'explicitly '
                                                                                                     'authorized '
                                                                                                     'native1 '
                                                                                                     'after '
                                                                                                     'independent '
                                                                                                     'current '
                                                                                                     'guest-opinion '
                                                                                                     'totals '
                                                                                                     'fighter1=100/fighter2=12, '
                                                                                                     'to '
                                                                                                     'protect '
                                                                                                     'the '
                                                                                                     'lower-affinity '
                                                                                                     'side '
                                                                                                     'from '
                                                                                                     'becoming '
                                                                                                     'negative; '
                                                                                                     'no '
                                                                                                     'fixed '
                                                                                                     'fighter '
                                                                                                     'IDs/opinion '
                                                                                                     'gate '
                                                                                                     'or '
                                                                                                     'guaranteed80/32 '
                                                                                                     'outcomes',
                                                                                  'cross_event_numeric_score': None,
                                                                                  'calibration_status': 'not_calibrated',
                                                                                  'decision_scope': 'bounded_timeline_continuation',
                                                                                  'source_sha256': {'events/activities/feast_activity/main_events/feast_default_events.txt': 'D26B858CEF9CEF76C9E1BF6FB796E2BFA9E103E54853676B0D28A1927052A3F1',
                                                                                                    'common/scripted_triggers/00_feast_activity_triggers.txt': 'B6DDE849AB49F66F78701B4F09E9090EE6E1D81B418EE077EFEF49C950DC2FBA',
                                                                                                    'common/opinion_modifiers/00_activity_feast_opinions.txt': '901D2C588CE01C7B49541B1EDA92EF44CA04CBD0A142FBAFC8927FDEF327F892',
                                                                                                    'common/scripted_effects/00_relation_effects.txt': 'B4668EED284175E67FB7F4DF42D1B2007075DEE25C0F348823C87664545B1891',
                                                                                                    'common/scripted_triggers/00_relation_triggers.txt': '973ED236B5544F56D20D11FF8F2A183527438C32E30FF973FAE54B39AC2DEF44',
                                                                                                    'common/script_values/00_basic_values.txt': 'C379CC0C58ED1574033F0E07A58697DFC6F8475C26AA4B117F2332008D4A27EF'},
                                                                                  'readiness': 'static-ready',
                                                                                  'new_live_evidence': False},
                                     'source_review_receipt_sha256': 'EAB02530B3A72C5F0CF41EBC9C9A382C2C0A0A8F25F79CCC168137C19B94553A',
                                     'readiness': 'static-ready',
                                     'new_live_evidence': False,
                                     'material_evidence_boundary': 'no material, M2 or terminal Feast credit '
                                                                   'from authored +/-20 values, helper '
                                                                   'invocation, ACK or modal advance; '
                                                                   'directed opinions and actual helper '
                                                                   'outcome require independent observation'},
                        'observations': {'exemplars': [{'kind': 'closed-production-red',
                                                        'artifact': 'artifacts/g2-maintainer-2026-10-02/resume-12003/m7-robert/fowl9002-following-normal30-2f0-v22-actual-02/turn-004/natural-event/003-ck3_query_vanilla_event_knowledge_v1-service-receipt.json',
                                                        'artifact_sha256': '4CAF71E819E44FA593501ED0497E12B1149C4906745915D990DA52C2C73CFEF5',
                                                        'typed_context_sha256': '33D74D9174856A146E226323FEFB7065EF54D8394A25B7F663B83E6474A62F93',
                                                        'snapshot_sha256': '8ACCFC5C86A7C4BE776828752CC4C4E14EF213AC1C9B41104BD24A0DB7A1C32C',
                                                        'event_instance_id': 17,
                                                        'root_character_id': 29829,
                                                        'fighter_1_character_id': 38293,
                                                        'fighter_2_character_id': 31073,
                                                        'date_raw': 53222640,
                                                        'selection_attempted': False,
                                                        'boundary': 'natural modal with available typed '
                                                                    'five-scope/two-visible presentation and '
                                                                    'original not_registered knowledge; no '
                                                                    'selected or independent material '
                                                                    'result'}]}}}
