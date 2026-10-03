#!/usr/bin/env python3
"""Prepare CK3 1.20 Ox Here initialization; production choices remain UI work."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from fixture_engine_prepare import checked_output, engine_identity

START = '''on_game_start_after_lobby = {
    on_actions = { oxa120_start }
}

oxa120_start = {
    effect = {
        debug_log = "OXA120: TEST BEGIN engine_startup"
        random_player = { trigger_event = { id = oxa120.1 } }
    }
}
'''
EVENTS = '''namespace = oxa120

oxa120.1 = {
    type = character_event
    hidden = yes
    immediate = {
        add_character_flag = oxa_initialize_pending
        oxa_initialize_effect = yes
        character:1316 = {
            if = {
                limit = { has_character_flag = oxa_initialized }
                debug_log = "OXA120: TEST READY production_choices"
            }
        }
    }
}
'''

def prepare(repo: Path, output: Path) -> dict:
    repo, output = checked_output(repo, output)
    source = repo / 'tools/fixtures/ox_here_acceptance'
    shutil.copytree(source,output)
    for relative, text in (('common/on_action/oxa120_on_actions.txt',START), ('events/oxa120_events.txt',EVENTS)):
        target = output / relative
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(text,encoding='utf-8-sig',newline='\n')
    receipt = {
        'product':'ox_here', **engine_identity(repo),
        'source_fixture':str(source), 'prepared_fixture':str(output),
        'runtime_status':'NOT_RUN', 'native_abi_loaded':False,
        'entry':'on_game_start_after_lobby -> oxa120_start -> oxa120.1 -> oxa_initialize_effect',
        'advance_game_days':0, 'production_ui_choices_required':True,
        'required_additional_markers':['OXA120: TEST BEGIN engine_startup','OXA120: TEST READY production_choices'],
        'ui_steps':['production decline choice','existing fixture verify-decline decision','production recruit choice and arrival event','existing fixture verify-recruit decision and summary option'],
        'source_file_sha256':{p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(source.rglob('*')) if p.is_file()},
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
