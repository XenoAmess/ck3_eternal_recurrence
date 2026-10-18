"""Portable source-valued V5 planning corrections; no game/file lookup at runtime."""
from __future__ import annotations
from copy import deepcopy

SPECIAL_BUILDINGS = {'schema': 'ck3-special-building-planning-knowledge-v1',
 'machine_id': '4-8e1c2f1861',
 'observed_at_utc': '2026-10-18T06:19:14.602956+00:00',
 'repository_document': 'docs/ck3-native-ai/special-building-religion-holy-site-gates12004.md',
 'source_manifest_sha256': '2d138768ab1948d8f34e94511e7fbe3d6fca3b1cd63cf9125c361a7bfcfb6b54',
 'catalogue_sha256': '28aa530f1f3c220518852429561ab9fd3b03151ea252044bf72cb3088f2aca09',
 'source_game_version': '1.20.0.4',
 'scope_counts': {'all_definitions': 989,
                  'special': 482,
                  'special_religion_holy_gates': 115,
                  'great_building_supplement': 15,
                  'great_religion_gates': 3},
 'decision_inputs': ['specific building definition key/level',
                     'actual barony/holding holder and Faith, religion, personal rite',
                     'actual barony holy-site membership for that Faith',
                     'all four construction/enablement domains',
                     'current building presence/slot/level/ruin-state/cost and original Can',
                     'actual DLC flag/override/fallback when applicable'],
 'rules': ['Adopt/create only changes a possible H input; it cannot satisfy a separate AND affiliation '
           'gate.',
           'If an OR affiliation branch already passes, adding H is not necessary for that branch.',
           'can_construct domains and is_enabled differ. Construction additionally requires is_enabled.',
           'scope:holder means barony-title holder. County holder or player Faith cannot replace it.',
           'The H predicate here has no explicit major, relic Active or rarity requirement; do not import '
           'those site-modifier gates.',
           'A built, enabled structure, an ownership title, the source modifier definition and actual net '
           'effects are separate observations.',
           'Physical DLC definition availability does not prove current DLC entitlement/enabled state.'],
 'examples': [{'keys': ['holy_site_great_mosque_of_mecca_01'],
               'explanation': '麦加大清真寺：名称不等于硬编码伊斯兰门。定义启用只检查持有者Faith圣地关系H。',
               'conditions': [{'key': 'holy_site_great_mosque_of_mecca_01',
                               'official_zh_hans_name': '麦加大清真寺',
                               'phases': {'is_enabled': {'class': 'holy_association_route',
                                                         'logic': 'H',
                                                         'full_expanded_gate': 'AND(AND(barony{is_holy_site_of '
                                                                               '= scope:holder.faith}))',
                                                         'source': ['common/buildings/00_special_buildings.txt',
                                                                    1059,
                                                                    1066]},
                                          'can_construct_potential': {'class': 'no_religion_or_holy_gate',
                                                                      'logic': '—',
                                                                      'full_expanded_gate': 'AND(NOT(AND(scope:holder{OR(government_has_flag '
                                                                                            '= '
                                                                                            'government_is_tribal, '
                                                                                            'government_has_flag '
                                                                                            '= '
                                                                                            'government_is_nomadic, '
                                                                                            'government_has_flag '
                                                                                            '= '
                                                                                            'government_is_wanua)})))',
                                                                      'source': ['common/buildings/00_special_buildings.txt',
                                                                                 1055,
                                                                                 1057]}},
                               'source': ['common/buildings/00_special_buildings.txt', 1038, 1107],
                               'source_file_sha256': '33322505fa7f79ca1a61fdc2682d3e0c36ec0a063cbafe95ba615479b5e3f8b4'}]},
              {'keys': ['hagia_sophia_01', 'hagia_sophia_02'],
               'explanation': '圣索菲亚大教堂启用H；阿亚索菲亚清真寺额外建造I，启用I OR H。伊斯兰分支已真时，不必为启用另补H。',
               'conditions': [{'key': 'hagia_sophia_01',
                               'official_zh_hans_name': '圣索菲亚大教堂',
                               'phases': {'is_enabled': {'class': 'holy_association_route',
                                                         'logic': 'H',
                                                         'full_expanded_gate': 'AND(AND(barony{is_holy_site_of '
                                                                               '= scope:holder.faith}))',
                                                         'source': ['common/buildings/00_special_buildings.txt',
                                                                    3380,
                                                                    3387]},
                                          'can_construct_potential': {'class': 'no_religion_or_holy_gate',
                                                                      'logic': '—',
                                                                      'full_expanded_gate': 'AND(NOT(AND(scope:holder{OR(government_has_flag '
                                                                                            '= '
                                                                                            'government_is_tribal, '
                                                                                            'government_has_flag '
                                                                                            '= '
                                                                                            'government_is_nomadic, '
                                                                                            'government_has_flag '
                                                                                            '= '
                                                                                            'government_is_wanua)})))',
                                                                      'source': ['common/buildings/00_special_buildings.txt',
                                                                                 3376,
                                                                                 3378]}},
                               'source': ['common/buildings/00_special_buildings.txt', 3360, 3427],
                               'source_file_sha256': '33322505fa7f79ca1a61fdc2682d3e0c36ec0a063cbafe95ba615479b5e3f8b4'},
                              {'key': 'hagia_sophia_02',
                               'official_zh_hans_name': '阿亚索菲亚清真寺',
                               'phases': {'is_enabled': {'class': 'holy_OR_affiliation_or_other_alternative',
                                                         'logic': 'OR(I, H)',
                                                         'full_expanded_gate': 'AND(AND(OR(AND(scope:holder{OR(faith.religion '
                                                                               '= religion:islam_religion, '
                                                                               'rite{rite_has_parameter = '
                                                                               'islamic_syncretic_actor})}), '
                                                                               'AND(barony{is_holy_site_of '
                                                                               '= scope:holder.faith}))))',
                                                         'source': ['common/buildings/00_special_buildings.txt',
                                                                    3454,
                                                                    3467]},
                                          'can_construct_potential': {'class': 'no_religion_or_holy_gate',
                                                                      'logic': '—',
                                                                      'full_expanded_gate': 'AND(NOT(AND(scope:holder{OR(government_has_flag '
                                                                                            '= '
                                                                                            'government_is_tribal, '
                                                                                            'government_has_flag '
                                                                                            '= '
                                                                                            'government_is_nomadic, '
                                                                                            'government_has_flag '
                                                                                            '= '
                                                                                            'government_is_wanua)})))',
                                                                      'source': ['common/buildings/00_special_buildings.txt',
                                                                                 3446,
                                                                                 3448]},
                                          'can_construct': {'class': 'affiliation_hard_gate',
                                                            'logic': 'I',
                                                            'full_expanded_gate': 'AND(AND(scope:holder{OR(faith.religion '
                                                                                  '= '
                                                                                  'religion:islam_religion, '
                                                                                  'rite{rite_has_parameter '
                                                                                  '= '
                                                                                  'islamic_syncretic_actor})}))',
                                                            'source': ['common/buildings/00_special_buildings.txt',
                                                                       3450,
                                                                       3452]}},
                               'source': ['common/buildings/00_special_buildings.txt', 3429, 3498],
                               'source_file_sha256': '33322505fa7f79ca1a61fdc2682d3e0c36ec0a063cbafe95ba615479b5e3f8b4'}]},
              {'keys': ['dome_of_the_rock_01'],
               'explanation': '圆顶清真寺启用H AND NOT J：只有圣地关联仍不足；犹太教或相容个人礼仪反而触发排除。',
               'conditions': [{'key': 'dome_of_the_rock_01',
                               'official_zh_hans_name': '圆顶清真寺',
                               'phases': {'is_enabled': {'class': 'holy_AND_affiliation_exclusion_or_conditional',
                                                         'logic': 'AND(H, NOT(J))',
                                                         'full_expanded_gate': 'AND(AND(barony{is_holy_site_of '
                                                                               '= scope:holder.faith}), '
                                                                               'NOT(AND(scope:holder{OR(faith.religion '
                                                                               '= '
                                                                               'religion:judaism_religion, '
                                                                               'rite{rite_has_parameter = '
                                                                               'jewish_syncretic_actor})})))',
                                                         'source': ['common/buildings/00_special_buildings.txt',
                                                                    3519,
                                                                    3529]},
                                          'can_construct_potential': {'class': 'no_religion_or_holy_gate',
                                                                      'logic': '—',
                                                                      'full_expanded_gate': 'AND(NOT(AND(scope:holder{OR(government_has_flag '
                                                                                            '= '
                                                                                            'government_is_tribal, '
                                                                                            'government_has_flag '
                                                                                            '= '
                                                                                            'government_is_nomadic, '
                                                                                            'government_has_flag '
                                                                                            '= '
                                                                                            'government_is_wanua)})))',
                                                                      'source': ['common/buildings/00_special_buildings.txt',
                                                                                 3515,
                                                                                 3517]}},
                               'source': ['common/buildings/00_special_buildings.txt', 3504, 3573],
                               'source_file_sha256': '33322505fa7f79ca1a61fdc2682d3e0c36ec0a063cbafe95ba615479b5e3f8b4'}]},
              {'keys': ['temple_in_jerusalem_01'],
               'explanation': '第三圣殿额外建造H AND J，启用H OR J。能使用既有建筑，不表示满足新建条件。',
               'conditions': [{'key': 'temple_in_jerusalem_01',
                               'official_zh_hans_name': '第三圣殿',
                               'phases': {'is_enabled': {'class': 'holy_OR_affiliation_or_other_alternative',
                                                         'logic': 'OR(H, J)',
                                                         'full_expanded_gate': 'AND(AND(OR(AND(barony{is_holy_site_of '
                                                                               '= scope:holder.faith}), '
                                                                               'AND(scope:holder{OR(faith.religion '
                                                                               '= '
                                                                               'religion:judaism_religion, '
                                                                               'rite{rite_has_parameter = '
                                                                               'jewish_syncretic_actor})}))))',
                                                         'source': ['common/buildings/00_special_buildings.txt',
                                                                    3600,
                                                                    3613]},
                                          'can_construct_potential': {'class': 'no_religion_or_holy_gate',
                                                                      'logic': '—',
                                                                      'full_expanded_gate': 'AND(NOT(AND(scope:holder{OR(government_has_flag '
                                                                                            '= '
                                                                                            'government_is_tribal, '
                                                                                            'government_has_flag '
                                                                                            '= '
                                                                                            'government_is_nomadic, '
                                                                                            'government_has_flag '
                                                                                            '= '
                                                                                            'government_is_wanua)})))',
                                                                      'source': ['common/buildings/00_special_buildings.txt',
                                                                                 3586,
                                                                                 3588]},
                                          'can_construct': {'class': 'holy_AND_affiliation',
                                                            'logic': 'AND(H, J)',
                                                            'full_expanded_gate': 'AND(AND(barony{is_holy_site_of '
                                                                                  '= scope:holder.faith}), '
                                                                                  'AND(scope:holder{OR(faith.religion '
                                                                                  '= '
                                                                                  'religion:judaism_religion, '
                                                                                  'rite{rite_has_parameter '
                                                                                  '= '
                                                                                  'jewish_syncretic_actor})}))',
                                                            'source': ['common/buildings/00_special_buildings.txt',
                                                                       3590,
                                                                       3598]}},
                               'source': ['common/buildings/00_special_buildings.txt', 3575, 3659],
                               'source_file_sha256': '33322505fa7f79ca1a61fdc2682d3e0c36ec0a063cbafe95ba615479b5e3f8b4'}]},
              {'keys': ['brihadeeswarar_temple_01'],
               'explanation': '苾利诃地湿伐罗神庙启用E，额外建造需持有者文化庄园创新；它没有H门，也不是只限印度教。',
               'conditions': [{'key': 'brihadeeswarar_temple_01',
                               'official_zh_hans_name': '苾利诃地湿伐罗神庙',
                               'phases': {'is_enabled': {'class': 'affiliation_hard_gate',
                                                         'logic': 'E',
                                                         'full_expanded_gate': 'AND(AND(AND(scope:holder{OR(faith.religion{is_in_family '
                                                                               '= rf_eastern}, '
                                                                               'rite{rite_has_parameter = '
                                                                               'eastern_syncretic_actor})})))',
                                                         'source': ['common/buildings/00_special_buildings.txt',
                                                                    2988,
                                                                    2993]},
                                          'can_construct_potential': {'class': 'no_religion_or_holy_gate',
                                                                      'logic': '—',
                                                                      'full_expanded_gate': 'AND(NOT(AND(scope:holder{OR(government_has_flag '
                                                                                            '= '
                                                                                            'government_is_tribal, '
                                                                                            'government_has_flag '
                                                                                            '= '
                                                                                            'government_is_nomadic, '
                                                                                            'government_has_flag '
                                                                                            '= '
                                                                                            'government_is_wanua)})))',
                                                                      'source': ['common/buildings/00_special_buildings.txt',
                                                                                 2976,
                                                                                 2978]},
                                          'can_construct': {'class': 'no_religion_or_holy_gate',
                                                            'logic': '—',
                                                            'full_expanded_gate': 'AND(scope:holder{culture{has_innovation '
                                                                                  '= '
                                                                                  'innovation_manorialism}})',
                                                            'source': ['common/buildings/00_special_buildings.txt',
                                                                       2980,
                                                                       2986]}},
                               'source': ['common/buildings/00_special_buildings.txt', 2959, 3031],
                               'source_file_sha256': '33322505fa7f79ca1a61fdc2682d3e0c36ec0a063cbafe95ba615479b5e3f8b4'}]},
              {'keys': ['parthenon'],
               'explanation': '帕特农神庙额外建造要求持有者宗教等于hellenic_pagan所属宗教，启用还要H。这是宗教层级相等，不能改说成exact '
                              'Faith，也没有综摄替代。',
               'conditions': [{'key': 'parthenon',
                               'official_zh_hans_name': '帕特农神庙',
                               'phases': {'is_enabled': {'class': 'holy_AND_affiliation',
                                                         'logic': 'AND(scope:holder.faith.religion = '
                                                                  'faith:hellenic_pagan.religion, H)',
                                                         'full_expanded_gate': 'AND(scope:holder.faith.religion '
                                                                               '= '
                                                                               'faith:hellenic_pagan.religion, '
                                                                               'AND(barony{is_holy_site_of '
                                                                               '= scope:holder.faith}))',
                                                         'source': ['common/buildings/00_special_buildings.txt',
                                                                    6123,
                                                                    6131]},
                                          'can_construct': {'class': 'affiliation_hard_gate',
                                                            'logic': 'scope:holder.faith.religion = '
                                                                     'faith:hellenic_pagan.religion',
                                                            'full_expanded_gate': 'AND(scope:holder.faith.religion '
                                                                                  '= '
                                                                                  'faith:hellenic_pagan.religion)',
                                                            'source': ['common/buildings/00_special_buildings.txt',
                                                                       6119,
                                                                       6121]}},
                               'source': ['common/buildings/00_special_buildings.txt', 6108, 6168],
                               'source_file_sha256': '33322505fa7f79ca1a61fdc2682d3e0c36ec0a063cbafe95ba615479b5e3f8b4'}]}],
 'native_legality': None,
 'state_observed': False,
 'action_ready': False,
 'business_pass': False}
