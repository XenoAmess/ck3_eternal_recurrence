#!/usr/bin/env python3
"""Prepare a disposable CK3 1.20 TED core fixture; never launch the game."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from fixture_engine_prepare import checked_output, engine_identity

START = '''on_game_start_after_lobby = {
    on_actions = { tea120_start }
}

tea120_start = {
    effect = {
        debug_log = "TEA120: TEST BEGIN engine_startup"
        random_player = { trigger_event = { id = tea120.1 } }
    }
}
'''
EVENTS = '''namespace = tea120

tea120.1 = {
    type = character_event
    hidden = yes
    # Preserve the original decision entry gate when GUI callbacks are omitted.
    trigger = { NOT = { has_character_flag = tea_fixture_initialized } }
    immediate = {
        add_character_flag = tea_initialize_pending
        tea_initialize_effect = yes
        character:han_8052 = {
            if = {
                limit = { has_character_flag = tea_setup_pending }
                trigger_event = { id = tea120.2 days = 1 }
            }
        }
    }
}

tea120.2 = {
    type = character_event
    hidden = yes
    immediate = {
        tea_setup_and_execute_effect = yes
        if = {
            limit = { has_character_flag = tea_verify_attacker_pending }
            var:tea_recipient = { trigger_event = { id = tea120.3 days = 1 } }
        }
    }
}

tea120.3 = {
    type = character_event
    hidden = yes
    immediate = { tea_verify_attacker_effect = yes }
}
'''

SAVED_GUARD = '''this = character:1128
        is_ai = no
        is_alive = yes
        current_date = 1066.9.15
        NOT = { has_character_flag = tea120_saved_entry_dispatched }
        NOT = { has_character_flag = tea_fixture_initialized }
        character:han_8052 = {
            NOT = { has_character_flag = tea120_saved_entry_dispatched }
            NOT = { has_character_flag = tea_fixture_initialized }
            NOT = { has_character_flag = tea_setup_pending }
        }'''


def saved_entry_files(production_ui: bool) -> dict[str, str]:
    """Replace only the lobby entry with a guarded current-player Saved bridge.

    Public Saved preparation binds the actual Save separately. History1128 is
    never reported as a runtime ID. The original event owns all setup/behavior.
    """
    event_id = 'teaui.1' if production_ui else 'tea120.1'
    start_marker = ('TEAUI: TEST BEGIN ui_context_only' if production_ui
                    else 'TEA120: TEST BEGIN engine_startup')
    return {
        'common/scripted_guis/tea120_saved_entry_guis.txt': f'''tea120_saved_entry_gui = {{
    scope = character
    is_shown = {{ {SAVED_GUARD} }}
    effect = {{
        if = {{
            limit = {{ {SAVED_GUARD} }}
            add_character_flag = tea120_saved_entry_dispatched
            character:han_8052 = {{ add_character_flag = tea120_saved_entry_dispatched }}
            debug_log = "{start_marker}"
            trigger_event = {{ id = {event_id} }}
        }}
    }}
}}
''',
        'gui/tea120_saved_entry_bridge.gui': '''window = {
    name = "tea120_saved_entry_bridge_window"
    size = { 1 1 }
    layer = tutorial
    position = { 0 0 }
    visible = "[GetPlayer.IsValid]"
    alwaystransparent = yes
    state = {
        name = "tea120_saved_entry_bootstrap"
        trigger_when = "[GetScriptedGui('tea120_saved_entry_gui').IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
        on_start = "[GetScriptedGui('tea120_saved_entry_gui').Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
    }
}
''',
        'gui/scripted_widgets/tea120_saved_entry_widgets.txt':
            'gui/tea120_saved_entry_bridge.gui = tea120_saved_entry_bridge_window\n',
    }


def prepare(repo: Path, output: Path, production_ui: bool = False, saved_entry_bridge: bool = False) -> dict[str, object]:
    if type(saved_entry_bridge) is not bool:
        raise ValueError('saved_entry_bridge must be a strict boolean')
    repo, output = checked_output(repo, output)
    source = repo / 'tools/fixtures/tributary_expansion_directives_acceptance'
    files = [source / 'descriptor.mod', source / 'common/scripted_effects/tea_effects.txt', *sorted((source / 'localization').rglob('*.yml'))]
    for path in files:
        target = output / path.relative_to(source)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,target)
    generated: tuple[tuple[str, str], ...] = () if production_ui else (('common/on_action/tea120_on_actions.txt',START), ('events/tea120_events.txt',EVENTS))
    if saved_entry_bridge:
        generated = tuple((relative, text) for relative, text in generated
                          if not relative.startswith('common/on_action/'))
    for relative, text in generated:
        target = output / relative
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(text,encoding='utf-8-sig',newline='\n')
    if production_ui:
        ui_source = source / 'ui'
        if len([path for path in ui_source.rglob('*') if path.is_file()]) != 3:
            raise ValueError('all three original production-UI data files are required')
        for path in sorted(ui_source.rglob('*')):
            if path.is_file():
                ui_relative = path.relative_to(ui_source)
                if saved_entry_bridge and ui_relative.as_posix() == 'common/on_action/teaui_on_actions.txt':
                    continue
                target = output / ui_relative
                target.parent.mkdir(parents=True,exist_ok=True)
                with target.open('xb') as stream:stream.write(path.read_bytes())
    if saved_entry_bridge:
        for relative, text in saved_entry_files(production_ui).items():
            target = output / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding='utf-8-sig', newline='\n')
    receipt: dict[str, object] = {
        'product':'mod_tributary_expansion_directives', **engine_identity(repo),
        'source_fixture':str(source), 'prepared_fixture':str(output),
        'runtime_status':'NOT_RUN', 'native_abi_loaded':False,
        'entry':('on_game_start_after_lobby -> teaui.1/2 -> context only; real production Send remains Root' if production_ui else 'on_game_start_after_lobby -> tea120_start -> tea120.1/2/3'),
        'production_ui':production_ui,
        'advance_game_days':1 if production_ui else 2, 'gui_callbacks_mounted':False,
        'required_additional_marker':('TEAUI: TEST READY production_interaction_no_response_executed' if production_ui else 'TEA120: TEST BEGIN engine_startup'),
        'coverage':('existing context-only fixture; no response or war effect executed; real interaction GUI required' if production_ui else 'existing core response effects; production interaction selector UI is not executed'),
        'source_file_sha256':{p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        'prepared_file_sha256':{p.relative_to(output).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.rglob('*')) if p.is_file()},
    }
    if saved_entry_bridge:
        receipt['entry'] = ('Saved GetPlayer bridge -> original teaui.1/2; context only' if production_ui
                            else 'Saved GetPlayer bridge -> original tea120.1/2/3; original two-day schedule')
        receipt['saved_entry'] = {
            'actor_history_id': 1128, 'required_source_game_date': '1066.9.15',
            'runtime_actor_id': 'NOT_INFERRED_FROM_HISTORY_ID',
            'source_save_binding': 'REQUIRED_BY_PUBLIC_SAVED_PREPARATION',
            'requires_human_alive_unstarted_actor': True,
            'paired_once_flag': 'tea120_saved_entry_dispatched',
            'paired_target': 'character:han_8052', 'original_event_and_setup': 'UNCHANGED',
            'new_game_on_action_included': False, 'runtime_status': 'NOT_RUN',
        }
    output.with_suffix('.prepare.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    return receipt

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=Path.cwd())
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--production-ui',action='store_true')
    parser.add_argument('--saved-entry-bridge', action='store_true',
                        help='explicit Robert1128/1066.9.15 Saved entry; original core/context behavior unchanged')
    args = parser.parse_args()
    receipt = prepare(args.repo,args.output,args.production_ui,args.saved_entry_bridge)
    print(json.dumps({'prepared_fixture':receipt['prepared_fixture'],'runtime_status':'NOT_RUN'}))

if __name__ == '__main__':
    main()
