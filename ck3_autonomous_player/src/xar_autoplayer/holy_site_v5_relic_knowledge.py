"""Portable source-valued V5 planning corrections; no game/file lookup at runtime."""
from __future__ import annotations
from copy import deepcopy

RELIC_AI_AND_CB = {'actor_admission': {'all': ['AI',
                             'available_ai_adult',
                             'actor Faith == top_liege Faith',
                             'top_liege AI',
                             'ownFaith religious_head absent OR AI',
                             'zealous trait OR ai_zeal>=25',
                             'exists direct-held county target witness'],
                     'independent_topliege': 'self',
                     'human_protection_checks_exactly': ['top_liege', 'actor currentFaith religious_head'],
                     'not_checked_as_human_protection': ['original donor',
                                                         'any intermediate liege',
                                                         'another associatedFaith religious_head'],
                     'availability': {'all_quick_flags': {'ai': True,
                                                          'adult': True,
                                                          'alive': True,
                                                          'travel': False,
                                                          'in_army': False,
                                                          'imprisoned': False,
                                                          'incapable': False},
                                      'adult_stock_defines': {'male': 16, 'female': 16},
                                      'contagious_deadly_disease_trait_flag_absent': True,
                                      'involved_activity_absent': True,
                                      'no_any_variables': ['homage_liege_scope',
                                                           'meditation_character_flag',
                                                           'local_shrine_rite',
                                                           'petition_liege_character_flag',
                                                           'petition_head_of_faith_petitioner',
                                                           'holding_court_character_flag',
                                                           'gone_adventuring'],
                                      'is_being_visited_on_tour_strict': False,
                                      'planning_an_activity_character_flag_absent': True},
                     'realm_at_war_excluded': False},
 'per_item': {'definitions': {'F': 'actor currentFaith',
                              'S': 'current HolySite',
                              'I': 'current enshrined artifact',
                              'G': 'associated Faith being iterated',
                              'R': 'original is_holy_relic_for',
                              'OwnSite': 'Faith F in associated HolySite faiths'},
              'is_valid_witness_A': 'OwnSite(S,F) AND exists I: NOT R(I,F) AND CanRemove(actor,S,I)',
              'is_valid_witness_B': 'exists associated G!=F: G.num_county_followers>0 AND '
                                    'hostility(F,G)>=2 AND exists I: R(I,G) AND CanRemove(actor,S,I)',
              'effect_A': 'G==F AND NOT R(I,F)',
              'effect_B': 'G!=F AND G.num_county_followers>0 AND hostility(F,G)>=2 AND R(I,G) AND NOT '
                          'R(I,F) AND NOT OwnSite(S,F)',
              'combined_static_filter': 'NOT R(I,F) AND (OwnSite(S,F) OR exists associated G!=F: '
                                        'G.num_county_followers>0 AND hostility(F,G)>=2 AND R(I,G))',
              'final_admission': 'original remove script effect rechecks29ABB20 for each attempted '
                                 'removal; no implication from is_valid witness to actual success',
              'hostile_branch_protection_truth_table': [{'recognized_self': False,
                                                         'own_site': False,
                                                         'multi_clause_NOT': True,
                                                         'hostile_branch_protected': False},
                                                        {'recognized_self': True,
                                                         'own_site': False,
                                                         'multi_clause_NOT': False,
                                                         'hostile_branch_protected': True},
                                                        {'recognized_self': False,
                                                         'own_site': True,
                                                         'multi_clause_NOT': False,
                                                         'hostile_branch_protected': True},
                                                        {'recognized_self': True,
                                                         'own_site': True,
                                                         'multi_clause_NOT': False,
                                                         'hostile_branch_protected': True}],
              'county_followers_scope': 'G Faith scope; not asserted to be local to S county',
              'loop_atomicity': 'not asserted; per-item callbacks may alter later world state'},
 'CB_AI_local_rules': {'key': 'reclaim_relic_artifact_war',
                       'AI_zeal_minimum': 100,
                       'AI_highest_held_title_tier_minimum': 'tier_duchy',
                       'zealous_trait_bypass_for_AI_100_gate': False,
                       'humans_exempt_from_these_two_AI_gates': True,
                       'all_attackers_exclude_landless_adventurer': True,
                       'different_attacker_defender_Faith': True,
                       'ordinary_item_all': ['recognized by attackerFaith',
                                             'not recognized by defenderFaith',
                                             'artifact_prevent_transfer variable absent'],
                       'ordinary_item_hostility_2_gate_present': False,
                       'original_donor_or_personal_claim_gate_present': False,
                       'AI_inventory_scope': 'defender own character inventory',
                       'human_extra_inventory_scope': 'defender vassal-or-below whose Faith differs from '
                                                      'attackerFaith',
                       'AI_neighbor_only_config': True,
                       'max_ai_diplo_distance_to_title_config': 500,
                       'struggle_item': 'separate Iberian struggle flag/access branch; exact2231..2248 '
                                        'retained',
                       'native_full_declare_permission': 'still separate, not observed',
                       'natural_choice_and_result': 'not observed'},
 'normal_remove_recipient': 'valid current AI actor, not donor',
 'scope': 'static planning knowledge; no current actor permission/natural execution qualification',
 'current_actor_admission_observed': False,
 'natural_execution_observed': False}

LAST_FAITH_RETURN = {'scope': 'Normal vanilla1.20.0.4 Abandon action with valid objects and completed original decision '
          'effect. Script target guarantees are distinct from live postcondition observations.',
 'identities': {'A': 'decision root/actor',
                'F': 'A.faith',
                'S': 'selected HolySite',
                'H': 'S.holy_site_county.holder, saved once before return loop',
                'D': 'original donor, not read by this return branch'},
 'ordered_effect': ['Save H from S.holy_site_county.holder at374–375',
                    'If H exists and no associated Faith other than F, every_enshrined_artifact set_owner '
                    'H at379–387',
                    'F.remove_holy_site S with actor A at391–395',
                    'Consume free HolySite action at396',
                    'If H exists and H!=A, countyholder opinion modifier at398–408',
                    'Actor ten-year modifier at410–413'],
 'decision_table': [{'case': 'normal decision not admitted',
                     'conditions': 'selected Site missing, this Faith not associated, current Site eminent '
                                   'for actor Faith, total count at minimum, or other normal decision '
                                   'guard fails',
                     'transfer': 'No normal Abandon execution',
                     'membership': 'No normal execution',
                     'confidence': 'source validity gates; not a failed live attempt'},
                    {'case': 'another associated Faith remains',
                     'conditions': 'At least one any_holy_site_faith full identity != actor.faith, '
                                   'regardless followers/grade/recognition',
                     'transfer': 'No return loop; original site keeps its enshrined artifacts through this '
                                 'script',
                     'membership': 'Remove only actor Faith relation',
                     'confidence': 'source; R0010 nonempty shared readback corroborates'},
                    {'case': 'last associated Faith, H exists, enshrined objects exist',
                     'conditions': 'No other associated Faith; saved countyholder H resolves',
                     'transfer': 'Every object enumerated by every_holy_site_enshrined_artifact gets '
                                 'set_owner target H before membership removal',
                     'membership': 'Remove actor Faith after transfers',
                     'confidence': 'script guarantees chosen target; R0011 confirms H=actor only'},
                    {'case': 'last associated Faith, H exists, no enshrined objects',
                     'conditions': 'Same return guard, but iterator yields none',
                     'transfer': 'Zero objects transferred; no object is created',
                     'membership': 'Remove actor Faith',
                     'confidence': 'script empty-loop boundary, no new live test'},
                    {'case': 'last associated Faith, H absent',
                     'conditions': 'exists scope:county_holder is false',
                     'transfer': 'Return branch skipped; no actor/donor/HoF fallback and no transfer in '
                                 'this script',
                     'membership': 'Remove actor Faith still follows',
                     'confidence': 'source branch only; do not claim a new no-holder live outcome or later '
                                   'object reachability'}],
 'recipient_tests': {'H_equals_actor': 'Not required; only when H=A does return happen to actor',
                     'H_equals_original_donor': 'Not required; original donor is not selected',
                     'H_is_vassal_of_A': 'Not tested; H receives because H holds the county, not because '
                                         'of vassal status',
                     'H_faith_equals_F': 'Not tested',
                     'H_faith_recognizes_each_relic': 'Not tested',
                     'other_associated_faith_followers_positive': 'Not tested; any other association '
                                                                  'blocks this last-Faith return loop',
                     'other_associated_faith_eminent': 'Not tested',
                     'site_Active_or_rarity': 'Not tested by return guard'},
 'what_H_is_not': ['top liege',
                   'barony/temple holder merely by local rank',
                   'original donor',
                   'current actor unless the same countyholder',
                   'automatic Head of Faith'],
 'different_path_comparison': {'explicit_remove': 'old object -> valid command actor, explicit removal '
                                                  'callback applies',
                               'same_slot_replacement': 'old object -> valid command actor, new object -> '
                                                        'site; enshrine/remove callbacks apply',
                               'Abandon_last_Faith': 'objects -> saved countyholder via generic set_owner, '
                                                     'not explicit removal callback'},
 'cost_scope': 'Abandon retains its own piety/cooldown/free-use/opinion logic. inventory_on_actions322–325 '
               'excludes generic effects from explicit relic-removal on_action; do not add explicit remove '
               'piety/devotion cost or declare every unrelated owner effect risk-free.',
 'historical_observations': {'R0010': '2026-10-17 20:12:41–42Z: site14 leaves Faith50 but '
                                      'still26/27/36/49; artifact64 remains slot0, owner site14. Actor is '
                                      'countyholder; this is shared branch.',
                             'R0011': '2026-10-17 20:51:03Z independent artifact237 owner=15893, holy-site '
                                      'owner null, player owned true/unequipped; last Faith exits site326. '
                                      'Actor and H are both15893; this does not empirically distinguish '
                                      'different-person target selection. Successful Abandon action was '
                                      'not recorded on video.'},
 'planner_observations_before': ['actual A/F/S identity and original fresh normal permission',
                                 'complete associated Faith fullID list, not followers or recognition '
                                 'substitutes',
                                 'actual county title holder H, distinct from barony holder/top liege',
                                 'actual enshrined objects via existing supported native context; raw ref '
                                 'list is not assumed equivalent to the original iterator'],
 'planner_observations_after': ['Faith relation removal',
                                'independent each-object character/holy-site owner and receiver inventory',
                                'world Site/object availability and inventory, not assume destroyed',
                                'resource/cooldown/opinion postconditions separately from ACK']}

OPINION_ROLES = {
    "qualification": "source_reviewed_static_not_actual_net_opinion",
    "definitions": {"A": "actor", "F": "actor Faith", "N": "new relic", "O": "old relic",
        "R": "native is_holy_relic_for(item, Faith)"},
    "direction": "Every selected subject's opinion of A; never A's opinion of the subject.",
    "liege_zeal_gate": "ai_zeal >= 50 OR devoted OR zealous; distinct from vassal_stance=zealot.",
    "official_terms": {"devoted": "誓愿者；男性修士、女性修女", "zealous": "狂热",
        "vassal_stance_zealot": "宗教狂热立场", "vassal_stance_minority": "少数族群立场"},
    "positive_15": {
        "nonempty_total_gate": "R(N,F) AND R(O,F) AND old.rarity >= new.rarity; not an upgrade-only reward.",
        "empty_slot_nullable_replacing_semantics": "unknown; no unconditional first-enshrinement reward claim",
        "subjects": [
            {"role": "direct vassal", "filter": "zealot stance AND recognizes N; same Faith not required", "lines": [245,258]},
            {"role": "each current liege or above", "filter": "liege zeal gate AND recognizes N; no same-Faith or vassal-stance requirement", "lines": [260,276]},
            {"role": "own Faith head", "filter": "exists, not A, head's current Faith recognizes N; no zeal/stance/followers requirement", "lines": [277,294]},
        ],
    },
    "loss_gate_L": "R(O,F) AND (no N OR new.rarity < old.rarity)",
    "negative_20_when_L": [
        {"role": "direct vassal", "filter": "same Faith AND zealot stance", "lines": [403,413]},
        {"role": "direct vassal", "filter": "same Faith AND minority stance", "lines": [414,424]},
        {"role": "current direct liege's direct vassal", "filter": "A has liege, same Faith AND zealot stance; no minority branch", "lines": [426,441]},
        {"role": "each current liege or above", "filter": "A has liege, liege zeal gate AND recognizes O; same Faith not required", "lines": [442,458]},
        {"role": "head of each associated Faith", "filter": "that Faith county-followers > 0, head exists and is not A, head current Faith recognizes O; no zeal/stance gate", "lines": [355,383]},
    ],
    "negative_20_when_not_L": {
        "subjects": ["direct vassals", "current direct liege's direct vassals when A has liege", "each current liege or above when A has liege"],
        "shared_filter": "subject Faith != F AND subject Faith recognizes O",
        "no_gates": ["zealot/minority stance", "ai_zeal or traits", "subject Faith associated with site"],
        "separate_head_of_faith_loop": False,
        "lines": [462,522],
    },
    "duration": {"years":10,"decaying":True,"default_stacking":False,
        "same_key_reapplied":"refreshes duration, not multiplication by number of relationship roles",
        "positive_and_negative_keys":"different keys may coexist; net jump is not guaranteed to equal the base +/- value"},
    "source_resources": [
        {"relative_to_game":"common/on_action/inventory_on_actions.txt","sha256":"fcab2d2e740d32f3e8b5cb4058196dd3592153343ea3ae7a41c980fc0a334f67","lines":[129,524]},
        {"relative_to_game":"common/opinion_modifiers/pam_opinions.txt","sha256":"68cdfc641a32a38daf6e9de6651634278b522b26c2886fbf6b55341ce7e09b52","lines":[111,121]},
        {"relative_to_game":"common/opinion_modifiers/_opinions.info","sha256":"fac241b8983c5593d9528e8e3e84ce98e9f8cf089760f24ad534d80d381efec0","line_ranges":[[5,22],[39,43]]},
    ],
}
