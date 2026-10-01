"""Create a new consumer attempt with explicit original application/GUI owner proof."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
DEST = ROOT.parent / 'root-attempt-05-scoped-ui'
OLD_SHA = 'BF88D05E946233993F64F5F3275C11A20AE1297105F4194A0699586F45E90A6E'
FILES = ('build_frozen_research_a03.py', 'reviewed-native-targets-a02.json',
    'freeze_capture_checkout_a02.py', 'prepare_new_capture.py', 'run_new_capture_sdk.py',
    'prepare_runtime_binding_and_plan_a05.py', 'scoped_ui_research_a05.py',
    'run_paused_ui_stage_a04.py', 'preserve_paused_ui_checkpoint_a03.py',
    'capture_current_steam_offline.py', 'display_mode_research.py', 'restore_and_release_screen.py')

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def identity(path):
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest().upper()
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest}

def write(name, value):
    with (DEST / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def derive(original, new, replacements):
    value = (ROOT / original).read_text(encoding='utf-8')
    for before, after, count in replacements:
        require(value.count(before) == count, 'Reviewed derivative anchor count differs: ' + before[:60])
        value = value.replace(before, after)
    compile(value, str(DEST / new), 'exec')
    with (DEST / new).open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(value)
    return identity(DEST / new)

def main():
    require(identity(ROOT / 'scoped_ui_research_a05.py')['sha256'] == OLD_SHA, 'Reviewed previous controller changed')
    DEST.mkdir(exist_ok=False)
    copies = []
    for name in FILES:
        destination = DEST / name
        with destination.open('xb') as stream:
            stream.write((ROOT / name).read_bytes())
        require(identity(destination)['sha256'] == identity(ROOT / name)['sha256'], 'Exact precursor copy differs')
        copies.append({'original': identity(ROOT / name), 'copy': identity(destination)})
    proof_function = '''def original_gui_owner_identity(body):
    require(body.get('application_owner_thread_verified') is True and body.get('gui_owner_binding_verified') is True,
            'Original application thread or GUI object binding not verified')
    require(body.get('rng_owner_is_ui_admission_gate') is False, 'RNG ownership cannot substitute for UI ownership')
    for key in ('gui_context_address', 'gui_owner_address'):
        require(type(body.get(key)) is int and 0 < body[key] < 2**64, 'No actual original GUI pointer: ' + key)
    require(type(body.get('thread_id')) is int and 0 < body['thread_id'] < 2**32, 'No actual original application owner thread')
    require(type(body.get('rng_owner_thread_id')) is int and 0 <= body['rng_owner_thread_id'] < 2**32,
            'Missing actual RNG diagnostic; zero must remain zero')
    return (body['thread_id'], body['gui_context_address'], body['gui_owner_address'])

'''
    controller = derive('scoped_ui_research_a05.py', 'scoped_ui_research_a06.py', [
        ('def verify_window(body, kind, subject_id, values, config):\n', proof_function + 'def verify_window(body, kind, subject_id, values, config):\n    original_gui_owner_identity(body)\n', 1),
        ("    verify_window(again, kind, subject, pv, config)\n", "    verify_window(again, kind, subject, pv, config)\n    require(original_gui_owner_identity(result) == original_gui_owner_identity(again), 'Original GUI owner changed around the character/army/window frame')\n", 1),
        ("    hover_gate(again, pv)\n", "    hover_gate(again, pv)\n    require(original_gui_owner_identity(result) == original_gui_owner_identity(again), 'Original GUI owner changed around the knight tooltip frame')\n", 1),
        ("'hovered_widget_name', 'hovered_ui_side', 'hovered_combat_id')}", "'hovered_widget_name', 'hovered_ui_side', 'hovered_combat_id', 'gui_context_address', 'gui_owner_address')}", 1),
    ])
    sha = controller['sha256']
    checkpoint = derive('preserve_paused_ui_checkpoint_a03.py', 'preserve_paused_ui_checkpoint_a04.py', [
        ('scoped_ui_research_a05.py', 'scoped_ui_research_a06.py', 1), (OLD_SHA, sha, 2),
        ('_reviewed_scoped_ui_a05', '_reviewed_scoped_ui_a06', 1)])
    stage = derive('run_paused_ui_stage_a04.py', 'run_paused_ui_stage_a05.py', [
        ('scoped_ui_research_a05.py', 'scoped_ui_research_a06.py', 1), (OLD_SHA, sha, 1),
        ('preserve_paused_ui_checkpoint_a03.py', 'preserve_paused_ui_checkpoint_a04.py', 2),
        ('Independently reviewed a05 controller changed', 'Reviewed original GUI owner controller changed', 1)])
    planner = derive('prepare_runtime_binding_and_plan_a05.py', 'prepare_runtime_binding_and_plan_a06.py', [
        ('scoped_ui_research_a05.py', 'scoped_ui_research_a06.py', 1)])
    write('attempt-provenance.json', {'at_utc': datetime.now(timezone.utc).isoformat(),
        'reason': 'R0140 real paused original UI admission rejected due to invalid RNG ownership requirement; new source pending',
        'precursor_helpers': copies, 'derived_helpers': [controller, checkpoint, stage, planner],
        'R0140_research_status': 'RED_UI_ADMISSION_NO_DAY_ADVANCE',
        'R0140_all_originals_retained': True, 'movie_changed': False, 'new_live_pending': True,
        'actual_UI_owner_proof_required': True})
    for name in ('scoped_ui_research_a06.py', 'run_paused_ui_stage_a05.py',
                 'preserve_paused_ui_checkpoint_a04.py', 'prepare_runtime_binding_and_plan_a06.py'):
        argv = [sys.executable, '-B', str(DEST / name), '--help']
        result = subprocess.run(argv, capture_output=True, text=True, encoding='utf-8')
        write(name + '-help-process.json', {'argv': argv, 'returncode': result.returncode,
            'stdout': result.stdout, 'stderr': result.stderr, 'helper': identity(DEST / name)})
        require(result.returncode == 0, 'New consumer help probe failed')
    print(json.dumps({'attempt': str(DEST), 'controller': controller, 'stage': stage, 'checkpoint': checkpoint, 'planner': planner}))

if __name__ == '__main__':
    main()
