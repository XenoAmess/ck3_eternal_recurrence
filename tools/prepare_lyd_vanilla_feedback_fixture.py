"""Prepare a self-only original Confucian setup; never a business PASS fixture."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


SETUP = '''# GENERATED FILE by tools/prepare_lyd_vanilla_feedback_fixture.py
on_game_start_after_lobby = { on_actions = { lyd_feedback_setup } }
lyd_feedback_setup = {
    effect = {
        random_player = {
            if = {
                limit = { is_ai = no NOT = { has_character_flag = lyd_feedback_setup_done } }
                set_character_rite = rite:jingxue
                add_character_flag = lyd_feedback_setup_done
                debug_log = "LYD_FEEDBACK: SELF_JINGXUE_SETUP_APPLIED"
            }
        }
    }
}
'''


SAVED_GUARD = '''this = character:1128
        is_ai = no
        is_alive = yes
        current_date = 1066.9.15
        NOT = { has_character_flag = lyd_feedback_saved_entry_dispatched }
        NOT = { has_character_flag = lyd_feedback_setup_done }'''



# Saved-only observation. Every marker is selected by an engine limit/else.
# These branches never create rites, set faith, advance time, or change state.
SAVED_PREDICATE_OBSERVATIONS = r'''
            if = {
                limit = { faith = faith:confucian_faith }
                debug_log = "LYD_FEEDBACK_OBS: ACTOR_FAITH_CONFUCIAN_TRUE"
            }
            else = { debug_log = "LYD_FEEDBACK_OBS: ACTOR_FAITH_CONFUCIAN_FALSE" }
            if = {
                limit = { rite = rite:jingxue }
                debug_log = "LYD_FEEDBACK_OBS: ACTOR_RITE_JINGXUE_TRUE"
            }
            else = { debug_log = "LYD_FEEDBACK_OBS: ACTOR_RITE_JINGXUE_FALSE" }
            if = {
                limit = { rite = rite:daoxue }
                debug_log = "LYD_FEEDBACK_OBS: ACTOR_RITE_DAOXUE_TRUE"
            }
            else = { debug_log = "LYD_FEEDBACK_OBS: ACTOR_RITE_DAOXUE_FALSE" }
            if = {
                limit = { exists = rite:lyd_rite_kongmen }
                debug_log = "LYD_FEEDBACK_OBS: KONGMEN_EXISTS_TRUE"
                if = {
                    limit = { faith = rite:lyd_rite_kongmen.faith }
                    debug_log = "LYD_FEEDBACK_OBS: KONGMEN_FAITH_EQUALS_ACTOR_FAITH_TRUE"
                }
                else = { debug_log = "LYD_FEEDBACK_OBS: KONGMEN_FAITH_EQUALS_ACTOR_FAITH_FALSE" }
            }
            else = {
                debug_log = "LYD_FEEDBACK_OBS: KONGMEN_EXISTS_FALSE"
                debug_log = "LYD_FEEDBACK_OBS: KONGMEN_FAITH_NOT_OBSERVED_MISSING_RITE"
            }
            if = {
                limit = { exists = faith.religious_head this = faith.religious_head }
                debug_log = "LYD_FEEDBACK_OBS: ACTOR_IS_FAITH_HEAD_TRUE"
            }
            else = { debug_log = "LYD_FEEDBACK_OBS: ACTOR_IS_FAITH_HEAD_FALSE" }
            if = {
                limit = { exists = rite.head_of_rite this = rite.head_of_rite }
                debug_log = "LYD_FEEDBACK_OBS: ACTOR_IS_CURRENT_RITE_HEAD_TRUE"
            }
            else = { debug_log = "LYD_FEEDBACK_OBS: ACTOR_IS_CURRENT_RITE_HEAD_FALSE" }
            if = {
                limit = { has_character_flag = lyd_enabled }
                debug_log = "LYD_FEEDBACK_OBS: LYD_ENABLED_TRUE"
            }
            else = { debug_log = "LYD_FEEDBACK_OBS: LYD_ENABLED_FALSE" }
            if = {
                limit = { lyd_catalogue_rite_trigger = yes }
                debug_log = "LYD_FEEDBACK_OBS: LYD_CATALOGUE_RITE_TRUE"
            }
            else = { debug_log = "LYD_FEEDBACK_OBS: LYD_CATALOGUE_RITE_FALSE" }
'''



# Explicit controlled Saved prerequisites; never a payment/ADD/learning PASS.
SAVED_FUNDED_KNOWN_TENETS = '''
            add_gold = 1000
            add_piety = 1000
            add_stress = 90
            if = {
                limit = { NOT = { knows_tenet = lyd_tenet_reverent_heaven } }
                add_known_tenet = lyd_tenet_reverent_heaven
            }
            if = {
                limit = { NOT = { knows_tenet = lyd_tenet_knowing_acting_support } }
                add_known_tenet = lyd_tenet_knowing_acting_support
            }
'''



# Controlled initial slot preparation; stock loss hooks are intentionally retained.
SAVED_CLEAR_APOSTOLIC = '''
            if = {
                limit = { has_personal_tenet = tenet_apostolic_succession }
                remove_personal_tenet = tenet_apostolic_succession
            }
'''


def saved_entry_files(*, funded_known_tenets: bool = False, clear_apostolic_personal_tenet: bool = False) -> dict[str, str]:
    """Original Saved setup plus an explicit opt-in controlled self prerequisite."""
    if type(funded_known_tenets) is not bool:
        raise ValueError("funded_known_tenets must be a strict boolean")
    if type(clear_apostolic_personal_tenet) is not bool or (clear_apostolic_personal_tenet and not funded_known_tenets):
        raise ValueError("Apostolic removal requires explicit controlled funded Saved setup and strict boolean")
    from fixture_engine_prepare import balanced_excerpt
    original = balanced_excerpt(SETUP, r'^\s*random_player\s*=\s*\{')
    original_body = original[original.index('{') + 1:original.rfind('}')]
    prerequisites_body = SAVED_FUNDED_KNOWN_TENETS if funded_known_tenets else ''
    if clear_apostolic_personal_tenet:
        prerequisites_body = prerequisites_body.replace('            add_stress = 90\n', '')
    return {
        'common/scripted_guis/lyd_feedback_saved_entry_guis.txt': f'''lyd_feedback_saved_entry_gui = {{
    scope = character
    is_shown = {{ {SAVED_GUARD} }}
    effect = {{
        if = {{
            limit = {{ {SAVED_GUARD} }}
            add_character_flag = lyd_feedback_saved_entry_dispatched
{original_body}
{SAVED_CLEAR_APOSTOLIC if clear_apostolic_personal_tenet else ""}{prerequisites_body}
{SAVED_PREDICATE_OBSERVATIONS}
        }}
    }}
}}
''',
        'gui/lyd_feedback_saved_entry_bridge.gui': '''window = {
    name = "lyd_feedback_saved_entry_bridge_window"
    size = { 1 1 }
    layer = tutorial
    position = { 0 0 }
    visible = "[GetPlayer.IsValid]"
    alwaystransparent = yes
    state = {
        name = "lyd_feedback_saved_entry_bootstrap"
        trigger_when = "[GetScriptedGui('lyd_feedback_saved_entry_gui').IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
        on_start = "[GetScriptedGui('lyd_feedback_saved_entry_gui').Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
    }
}
''',
        'gui/scripted_widgets/lyd_feedback_saved_entry_widgets.txt':
            'gui/lyd_feedback_saved_entry_bridge.gui = lyd_feedback_saved_entry_bridge_window\n',
    }


def generate(output: Path, identity: dict, saved_entry_bridge: bool = False, *, funded_known_tenets: bool = False, clear_apostolic_personal_tenet: bool = False) -> dict:
    """Pure small fixture emission; callers own exact engine qualification."""
    if type(clear_apostolic_personal_tenet) is not bool or (clear_apostolic_personal_tenet and not (saved_entry_bridge and funded_known_tenets)):
        raise ValueError("Apostolic removal requires explicit controlled funded Saved setup and strict boolean")
    if type(funded_known_tenets) is not bool or (funded_known_tenets and not saved_entry_bridge):
        raise ValueError('Controlled prerequisites require explicit Saved entry and strict boolean')
    if type(saved_entry_bridge) is not bool:
        raise ValueError('saved_entry_bridge must be a strict boolean')
    if saved_entry_bridge and (not isinstance(identity.get('game_version'), str)
                               or re.fullmatch(r'[1-9][0-9]*(?:\.[0-9]+){2,3}', identity['game_version']) is None):
        raise ValueError('Saved entry requires an exact numeric engine game_version')
    if output.exists():
        raise ValueError('Fresh fixture output required')
    output.mkdir(parents=True)
    files = {
        'descriptor.mod': 'name="LYD original Confucian feedback setup"\nversion="1"\nsupported_version="1.20.*"\n',
        'common/on_action/lyd_feedback_setup.txt': SETUP,
    }
    if saved_entry_bridge:
        files = {
            'descriptor.mod': ('name="LYD original Confucian feedback setup"\nversion="1"\n'
                               f'supported_version="{identity["game_version"]}"\n'),
            **saved_entry_files(funded_known_tenets=funded_known_tenets, clear_apostolic_personal_tenet=clear_apostolic_personal_tenet),
        }
    refs = []
    for relative, text in files.items():
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = text.encode('utf-8-sig')
        target.write_bytes(raw)
        refs.append({'relative_path': relative, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    receipt = {
        'schema': 'lyd-vanilla-feedback-setup-v1', 'engine_identity': identity,
        'fixture_files': refs, 'required_markers': ['LYD_FEEDBACK: SELF_JINGXUE_SETUP_APPLIED'],
        'setup_scope': 'sole selected human player; Robert 29829 is verified by public admission and GUI readback',
        'setup_changes': ['self character rite to original jingxue', 'self idempotence flag'],
        'fixture_flag_is_business_proof': False, 'business_pass': False,
        'faith_main_rite_or_NPC_or_title_changes': False,
    }
    if saved_entry_bridge:
        receipt['setup_scope'] = 'sole selected human Robert authored history1128; actual runtime ID must come from public Saved admission/readback'
        receipt['saved_entry'] = {
            'actor_history_id': 1128, 'required_source_game_date': '1066.9.15',
            'runtime_actor_id': 'NOT_INFERRED_FROM_HISTORY_ID',
            'source_save_binding': 'REQUIRED_BY_PUBLIC_SAVED_PREPARATION',
            'requires_human_alive_unstarted_actor': True,
            'once_flag': 'lyd_feedback_saved_entry_dispatched',
            'original_self_setup': 'UNCHANGED', 'new_game_on_action_included': False,
            'maximum_natural_days': 0, 'runtime_status': 'NOT_RUN',
            'predicate_logs_are_observations_only': True,
            'predicate_log_prefix': 'LYD_FEEDBACK_OBS:',
            'missing_kongmen_faith_observation': 'NOT_OBSERVED_MISSING_RITE',
        }
    if funded_known_tenets:
        receipt['setup_changes'] += ['self gold +1000', 'self piety +1000', 'self stress +90',
            'self known T01/T33 only; no personal adoption']
        receipt['controlled_prerequisites'] = {
            'contract': 'NEW_CONTROLLED_SELF_PREREQUISITES_NOT_ORIGINAL_PURE_SETUP_PASS',
            'gold_delta': 1000, 'piety_delta': 1000, 'stress_delta': 90,
            'known_tenets': ['lyd_tenet_reverent_heaven', 'lyd_tenet_knowing_acting_support'],
            'personal_adoption_or_payment_or_cooldown_or_business_flags_written': False,
            'learning_decision_or_knowledge_acquisition_validated': False,
            'engine_invariants_and_resources_require_actual_readback': True,
        }
    if clear_apostolic_personal_tenet:
        receipt['setup_changes'] = [x for x in receipt['setup_changes'] if x != 'self stress +90']
        receipt['controlled_prerequisites']['stress_delta'] = 0
        receipt['controlled_prerequisites']['fixture_stress_grant_omitted_stock_loss_stress_retained'] = True
        receipt['setup_changes'] += ['self remove existing Apostolic personal tenet if present; stock loss hooks retained']
        receipt['controlled_personal_slot'] = {
            'removed_if_present': 'tenet_apostolic_succession',
            'native_available_slot_or_Can_or_ADD_proven': False,
            'extra_slots_or_target_personal_adoption_or_cooldown_bypass': False,
            'stock_loss_stress_fulfillment_modifier_secret_popularity_effects_not_suppressed': True,
            'requires_new_actual_baseline_after_all_setup': True,
        }
    with (output / 'setup-receipt.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--saved-entry-bridge', action='store_true',
                        help='explicit Robert1128/1066.9.15 Saved entry; only the original self setup, no business actions')
    parser.add_argument('--funded-known-tenets', action='store_true',
                        help='Saved-only controlled self resources and T01/T33 knowledge; not business proof')
    parser.add_argument("--clear-apostolic-personal-tenet", action="store_true",
                        help="controlled Saved init only: remove Apostolic if present; retain stock loss side effects")
    args = parser.parse_args()
    import fixture_engine_prepare as prep
    repo, output = args.repo.resolve(), args.output.resolve()
    if output == repo or repo in output.parents:
        raise ValueError('Fixture output must be outside repository')
    # Shared prepare installs its selected exact-build implementation here.
    identity = prep.engine_identity(repo)
    receipt = generate(output, identity, args.saved_entry_bridge, funded_known_tenets=args.funded_known_tenets, clear_apostolic_personal_tenet=args.clear_apostolic_personal_tenet)
    print(json.dumps({'status': 'SETUP_EMITTED_NOT_RUN', 'output': str(output),
                      'engine_identity': receipt['engine_identity'], 'business_pass': False}))


if __name__ == '__main__':
    main()
