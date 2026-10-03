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

def prepare(repo: Path, output: Path) -> dict:
    repo, output = checked_output(repo, output)
    source = repo / 'tools/fixtures/tributary_expansion_directives_acceptance'
    files = [source / 'descriptor.mod', source / 'common/scripted_effects/tea_effects.txt', *sorted((source / 'localization').rglob('*.yml'))]
    for path in files:
        target = output / path.relative_to(source)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,target)
    for relative, text in (('common/on_action/tea120_on_actions.txt',START), ('events/tea120_events.txt',EVENTS)):
        target = output / relative
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(text,encoding='utf-8-sig',newline='\n')
    receipt = {
        'product':'mod_tributary_expansion_directives', **engine_identity(repo),
        'source_fixture':str(source), 'prepared_fixture':str(output),
        'runtime_status':'NOT_RUN', 'native_abi_loaded':False,
        'entry':'on_game_start_after_lobby -> tea120_start -> tea120.1/2/3',
        'advance_game_days':2, 'gui_callbacks_mounted':False,
        'required_additional_marker':'TEA120: TEST BEGIN engine_startup',
        'coverage':'existing core response effects; production interaction selector UI is not executed',
        'source_file_sha256':{p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        'prepared_file_sha256':{p.relative_to(output).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.rglob('*')) if p.is_file()},
    }
    output.with_suffix('.prepare.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    return receipt

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=Path.cwd())
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    receipt = prepare(args.repo,args.output)
    print(json.dumps({'prepared_fixture':receipt['prepared_fixture'],'runtime_status':'NOT_RUN'}))

if __name__ == '__main__':
    main()
