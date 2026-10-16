"""Exact1.20.0.4 papal bull letter acknowledgement; observed R186 envelope."""
from typing import Final

EVENT_KEY: Final = 'pam_bull_events.0004'
PAM_BULL0004_12004_RECORD: Final = {'contract': {'date_policy': 'product-observation-window',
              'root_character_id': '$player',
              'scope_types': {'puppeteer': 'character-or-unavailable',
                              'actor': 'character',
                              'selected_item': 'tenet',
                              'bull_issuer': 'character',
                              'pam_tenet_stance_issuer': 'character',
                              'pam_tenet_stance_permit': 'character',
                              'pam_tenet_stance_tenet': 'tenet',
                              'tenet_scope': 'tenet'},
              'saved_scope_name_sets': (('puppeteer',
                                         'actor',
                                         'selected_item',
                                         'bull_issuer',
                                         'pam_tenet_stance_issuer',
                                         'pam_tenet_stance_permit',
                                         'pam_tenet_stance_tenet',
                                         'tenet_scope'),),
              'saved_scope_count': 8,
              'option_count': 1,
              'snapshot_option_count': 2,
              'native_option_indices': (0,),
              'selected_option_number': 1,
              'selected_native_option_index': 0,
              'occurrence_policy': 'repeatable-within-product-observation-window'},
 'analysis': {'exact_build': {'game_version': '1.20.0.4',
                              'steam_build_id': 25734779,
                              'ck3_executable_sha256': '98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518'},
              'source_sha256': {'events/dlc/pam/pam_bull_events.txt': '596A8F4CE0C9E64119B2E65917EC56F984C58882E5CCB0ADBD2E56893D89F937',
                                'common/scripted_effects/pam_effects.txt': 'FC4C77974A7844C31C1271DCC2ACE24B17906620A832658919AA281E42A2B94F'},
              'definition_lines': '283-328',
              'definition_block_sha256': 'EBBDCDE661D287DE1ED8FE9E1CD8EB05343EDF7BA3E84AF883461E720F7EBA5F',
              'definition_block_hash_convention': 'key token through closing brace; original CRLF '
                                                  'retained; following newline excluded',
              'event_type': 'letter_event',
              'sender': 'scope:bull_issuer',
              'caller_lines': 'common/scripted_effects/pam_effects.txt:7176-7188',
              'caller_semantics': 'notify helper schedules .0004 after1 day to rulers of issuer '
                                  'faith excluding issuer; static edge, not proof of the actual '
                                  'producer branch',
              'description_selection': 'first_valid tests issuer bull_option flags in order: '
                                       'crusade, heresy, tenet_permitted, tenet_forbidden; actual '
                                       'flag value was not independently read',
              'immediate_effect_lines': '308-316',
              'immediate_effect': 'only conditional CE3 sound when issuer bull_option is heresy '
                                  'and root has heresiarch; no trait write',
              'option_lines': {'0': '318-320', '1': '322-327'},
              'authored_option_count': 2,
              'authored_option_name_aliases': ['pam_bull_events.0004.a', 'pam_bull_events.0004.c'],
              'option_semantics': {'0': 'unconditional empty acknowledgement; name only',
                                   '1': 'crusade-only trigger; empty acknowledgement; name and '
                                        'trigger only'},
              'selected_choice_effect_profile': {'schema': 'xar.ck3.vanilla-event-choice-effect',
                                                 'schema_version': 1,
                                                 'selected_native_option_index': 0,
                                                 'completeness': 'all-authored-options-and-common-after-source-reviewed',
                                                 'selected_option_effects': [],
                                                 'common_after_effects': [],
                                                 'observable_postcondition': None,
                                                 'source_anchors': ['events/dlc/pam/pam_bull_events.txt:283-328'],
                                                 'source_sha256': '596A8F4CE0C9E64119B2E65917EC56F984C58882E5CCB0ADBD2E56893D89F937'},
              'native_ai_weights': 'neither authored option has ai_chance; no runtime AI '
                                   'preference or probability asserted',
              'randomness': 'no random/random_list or numeric random range in this event node; '
                            'upstream distribution not reviewed',
              'after_effect': None,
              'follow_up_event': None,
              'safe_option_rationale': 'use existing generic consumer only for observed '
                                       'eight-name/type envelope, sole rendered enabled native0 '
                                       'and snapshot authored-count2; no new event policy',
              'scope_boundary': 'root and actor/issuer typed in exemplar; puppeteer character '
                                'scope is null; selected_item/pam_tenet_stance_tenet/tenet_scope '
                                'have tenet type but identity remains opaque. Type/name envelope '
                                'does not identify a tenet or guarantee alias identities on future '
                                'frames. Other envelopes/two-rendered-option crusade form remain '
                                'source-only.',
              'material_evidence_boundary': 'acknowledgement and independent disappearance only; '
                                            'no tenet permission/stance/callback/trait/religious '
                                            'or resource reward established. Upstream mutations '
                                            'cannot be attributed to empty option.',
              'prior_analysis': 'docs/ck3-native-ai/current-event-scopes.md:378-397 reviewed same '
                                'SHA on1.20.0.3; historical machine_id unknown, not reused as '
                                'current machine qualification. .4 registry was missing despite '
                                'prose analysis.',
              'automatic_selection': False,
              'readiness': 'source-reviewed-with-production-live-primitive',
              'deployment_boundary': 'external candidate only; frozen R186 runtime not modified or '
                                     're-queried'},
 'observations': {'exemplars': [{'kind': 'production-live-primitive',
                                 'machine_id': 'desktop-3fevhd2-1c74096080',
                                 'observed_at_utc': '2026-10-16T17:06:01.480477+00:00',
                                 'run_id': 'desktop-3fevhd2-1c74096080--vanilla--R0186',
                                 'episode_run_id': 'native-31254-68303c9ae4fb',
                                 'artifact': 'docs/ck3-native-ai/evidence/episode04-pam-bull0004-r186-12004/actual-packet.json.gz',
                                 'original_context': {'path': 'D:/workspace/ck3_native_war_ai_promo_work/e04-r186-window-capture-a01/desktop-3fevhd2-1c74096080--vanilla--R0186/responses/r186-event02-context-a01.json',
                                                      'bytes': 47292,
                                                      'sha256': '5824183ad513b66911ea566cafe0dca2e57428dfae08f9e5418fb122b7d45ef4'},
                                 'original_selection': {'path': 'D:/workspace/ck3_native_war_ai_promo_work/e04-r186-window-capture-a01/desktop-3fevhd2-1c74096080--vanilla--R0186/responses/r186-event02-select-first-once.json',
                                                        'bytes': 13860,
                                                        'sha256': '09aa81eb3fce5b95fa3d8118025cc9b714f36d8c4f2d9b107c502f04a5bf3d0e'},
                                 'independent_after': {'path': 'D:/workspace/ck3_native_war_ai_promo_work/e04-r186-window-capture-a01/desktop-3fevhd2-1c74096080--vanilla--R0186/responses/r186-event02-after-a01.json',
                                                       'bytes': 137214,
                                                       'sha256': '82d3499da30dfee3f89064a4e5987d983c628eff3a36048f43cc96c67d9a919e'},
                                 'event_instance_id': 2,
                                 'root_character_id': 31254,
                                 'actor_character_id': 30490,
                                 'bull_issuer_character_id': 30490,
                                 'date_raw': 53148792,
                                 'rendered_native_option_indices': [0],
                                 'snapshot_authored_option_count': 2,
                                 'selected_native_option_index': 0,
                                 'selection_ack': 'accepted/submitted',
                                 'selection_postcondition_verified': True,
                                 'independent_active_event': None,
                                 'independent_paused': True,
                                 'boundary': 'no additional gameplay command or actual effect test '
                                             'performed by this offline analysis'}]}}
PAM_BULL0004_12004_SOURCE: Final = {'namespace': 'pam_bull_events',
 'definition': {'relative_path': 'events/dlc/pam/pam_bull_events.txt',
                'line': 283,
                'file_sha256': '596A8F4CE0C9E64119B2E65917EC56F984C58882E5CCB0ADBD2E56893D89F937'},
 'caller_candidate_resolution': 'external-definition-file',
 'caller_candidates': [{'relative_path': 'common/scripted_effects/pam_effects.txt',
                        'line': 7184,
                        'column': 28,
                        'file_sha256': 'FC4C77974A7844C31C1271DCC2ACE24B17906620A832658919AA281E42A2B94F',
                        'kind': 'exact-token-lexical-candidate'}]}
