"""Preserve predecessor bytes and add the missing full-panel frame owner check."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
OLD_SHA = 'F77B638232D59594F0344E084B7FCE88DF3EB6BD1A27C99A0A734798BF3B4F52'

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def identity(path):
    path = Path(path)
    return {'path': str(path), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest().upper()}

def write(name, value):
    with (ROOT / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def derive(old, new, replacements):
    value = (ROOT / old).read_text(encoding='utf-8')
    for before, after, count in replacements:
        require(value.count(before) == count, 'Derivative anchor count changed: ' + before)
        value = value.replace(before, after)
    compile(value, str(ROOT / new), 'exec')
    with (ROOT / new).open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(value)
    return {'predecessor': identity(ROOT / old), 'derivative': identity(ROOT / new)}

def main():
    require(identity(ROOT / 'scoped_ui_research_a06.py')['sha256'] == OLD_SHA,
            'Original reviewed precursor changed')
    controller = derive('scoped_ui_research_a06.py', 'scoped_ui_research_a07.py', [
        ("    verify_window(again, 'combat', config['combat_id'], pv, config)\n    require(geometry_gate",
         "    verify_window(again, 'combat', config['combat_id'], pv, config)\n    require(original_gui_owner_identity(result) == original_gui_owner_identity(again), 'Original GUI owner changed around the full combat panel frame')\n    require(geometry_gate", 1)])
    sha = controller['derivative']['sha256']
    checkpoint = derive('preserve_paused_ui_checkpoint_a04.py', 'preserve_paused_ui_checkpoint_a05.py', [
        ('scoped_ui_research_a06.py', 'scoped_ui_research_a07.py', 1),
        (OLD_SHA, sha, 2), ('_reviewed_scoped_ui_a06', '_reviewed_scoped_ui_a07', 1)])
    stage = derive('run_paused_ui_stage_a05.py', 'run_paused_ui_stage_a06.py', [
        ('scoped_ui_research_a06.py', 'scoped_ui_research_a07.py', 1),
        (OLD_SHA, sha, 1),
        ('preserve_paused_ui_checkpoint_a04.py', 'preserve_paused_ui_checkpoint_a05.py', 2)])
    planner = derive('prepare_runtime_binding_and_plan_a06.py', 'prepare_runtime_binding_and_plan_a07.py', [
        ('scoped_ui_research_a06.py', 'scoped_ui_research_a07.py', 1)])
    records = [controller, checkpoint, stage, planner]
    for record in records:
        helper = record['derivative']
        argv = [sys.executable, '-B', helper['path'], '--help']
        result = subprocess.run(argv, capture_output=True, text=True, encoding='utf-8')
        write(Path(helper['path']).name + '-help-process.json',
              {'argv': argv, 'returncode': result.returncode,
               'stdout': result.stdout, 'stderr': result.stderr, 'helper': helper})
        require(result.returncode == 0, 'Derivative help probe failed')
    write('full-panel-owner-proof-derivatives-a01.json', {
        'at_utc': datetime.now(timezone.utc).isoformat(), 'records': records,
        'purpose': 'Require identical actual application thread and GUI singleton context/owner before and after full combat panel pixels',
        'old_helpers_preserved': True, 'live_research_pending': True,
        'movie_changed': False, 'human_movie_signoff': False})
    print(json.dumps(records, ensure_ascii=False))

if __name__ == '__main__':
    main()
