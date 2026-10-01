#!/usr/bin/env python3
"""Prepare a disposable CK3 1.20 MRM fixture; never launch the game."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil

START = '''on_game_start_after_lobby = {
    on_actions = { mrma120_start }
}

mrma120_start = {
    trigger = { has_game_rule = mrm_enabled }
    effect = {
        debug_log = "MRMA120: TEST BEGIN engine_startup"
        trigger_event = { on_action = mrma_start }
    }
}
'''

def prepare(repo: Path, output: Path) -> dict:
    repo, output = repo.resolve(), output.resolve()
    if output == repo or repo in output.parents:
        raise ValueError('fixture output must be outside the repository')
    if output.exists():
        raise ValueError('use a new output directory for each attempt')
    source = repo / 'tools/fixtures/remove_mandala_acceptance'
    on_action = source / 'common/on_action/mrma_on_actions.txt'
    original = on_action.read_text(encoding='utf-8-sig')
    boundary = '\n\nmrma_start = {'
    if original.count(boundary) != 1 or not original.startswith('on_game_start_after_lobby = {'):
        raise ValueError('original fixture startup shape changed; review before preparing')
    core = 'mrma_start = {' + original.split(boundary, 1)[1]
    # split() retains the opening key's suffix; preserve every byte of the
    # existing core block, replacing only the old post-lobby registration.
    shutil.copytree(source, output)
    (output / 'common/on_action/mrma_on_actions.txt').write_text(START + '\n' + core, encoding='utf-8-sig', newline='\n')
    receipt = {
        'product':'mod_remove_mandala', 'game_version':'1.20.0.2',
        'source_fixture':str(source), 'prepared_fixture':str(output),
        'runtime_status':'NOT_RUN', 'native_abi_loaded':False,
        'entry':'on_game_start_after_lobby -> mrma120_start -> mrma_start',
        'advance_game_days':8,
        'required_additional_marker':'MRMA120: TEST BEGIN engine_startup',
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
