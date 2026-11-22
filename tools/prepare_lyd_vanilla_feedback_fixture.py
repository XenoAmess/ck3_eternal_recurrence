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


def saved_entry_files() -> dict[str, str]:
    """Run only the original self setup from a guarded explicit Saved entry."""
    from fixture_engine_prepare import balanced_excerpt
    original = balanced_excerpt(SETUP, r'^\s*random_player\s*=\s*\{')
    original_body = original[original.index('{') + 1:original.rfind('}')]
    return {
        'common/scripted_guis/lyd_feedback_saved_entry_guis.txt': f'''lyd_feedback_saved_entry_gui = {{
    scope = character
    is_shown = {{ {SAVED_GUARD} }}
    effect = {{
        if = {{
            limit = {{ {SAVED_GUARD} }}
            add_character_flag = lyd_feedback_saved_entry_dispatched
{original_body}
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


def generate(output: Path, identity: dict, saved_entry_bridge: bool = False) -> dict:
    """Pure small fixture emission; callers own exact engine qualification."""
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
            **saved_entry_files(),
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
    args = parser.parse_args()
    import fixture_engine_prepare as prep
    repo, output = args.repo.resolve(), args.output.resolve()
    if output == repo or repo in output.parents:
        raise ValueError('Fixture output must be outside repository')
    # Shared prepare installs its selected exact-build implementation here.
    identity = prep.engine_identity(repo)
    receipt = generate(output, identity, args.saved_entry_bridge)
    print(json.dumps({'status': 'SETUP_EMITTED_NOT_RUN', 'output': str(output),
                      'engine_identity': receipt['engine_identity'], 'business_pass': False}))


if __name__ == '__main__':
    main()
