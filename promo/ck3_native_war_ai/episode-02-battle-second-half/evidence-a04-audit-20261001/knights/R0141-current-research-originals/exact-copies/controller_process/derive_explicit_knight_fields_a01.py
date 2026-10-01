"""Add independent typed original knight getter checks to the research consumer."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
OLD_SHA = 'A3A31116C17E6313938677858AD230DD7945C8A8651FF16D475B14A3B1485CE5'

def main():
    spec = importlib.util.spec_from_file_location('_create_only_derivatives', ROOT / 'derive_full_panel_owner_proof_a01.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.require(module.identity(ROOT / 'scoped_ui_research_a07.py')['sha256'] == OLD_SHA,
                   'Predecessor bytes changed')
    function = '''def original_combat_knight_fields(body):
    require(body.get('combat_knights_read_available') is True, 'Original combat knight getter unavailable')
    for key in ('left_knight_count', 'right_knight_count'):
        require(type(body.get(key)) is int and 0 <= body[key] <= 4096, 'Original knight count missing or invalid: ' + key)
    for key in ('left_knight_breakdown', 'right_knight_breakdown'):
        require(type(body.get(key)) is str, 'Original knight breakdown markup missing or invalid: ' + key)
    return tuple(body[key] for key in ('left_knight_count', 'right_knight_count', 'left_knight_breakdown', 'right_knight_breakdown'))

'''
    controller = module.derive('scoped_ui_research_a07.py', 'scoped_ui_research_a08.py', [
        ('def verify_window(body, kind, subject_id, values, config):\n    original_gui_owner_identity(body)\n',
         function + 'def verify_window(body, kind, subject_id, values, config):\n    original_gui_owner_identity(body)\n    if kind == \'combat\':\n        original_combat_knight_fields(body)\n', 1)])
    sha = controller['derivative']['sha256']
    checkpoint = module.derive('preserve_paused_ui_checkpoint_a05.py', 'preserve_paused_ui_checkpoint_a06.py', [
        ('scoped_ui_research_a07.py', 'scoped_ui_research_a08.py', 1),
        (OLD_SHA, sha, 2), ('_reviewed_scoped_ui_a07', '_reviewed_scoped_ui_a08', 1)])
    stage = module.derive('run_paused_ui_stage_a06.py', 'run_paused_ui_stage_a07.py', [
        ('scoped_ui_research_a07.py', 'scoped_ui_research_a08.py', 1), (OLD_SHA, sha, 1),
        ('preserve_paused_ui_checkpoint_a05.py', 'preserve_paused_ui_checkpoint_a06.py', 2)])
    planner = module.derive('prepare_runtime_binding_and_plan_a07.py', 'prepare_runtime_binding_and_plan_a08.py', [
        ('scoped_ui_research_a07.py', 'scoped_ui_research_a08.py', 1)])
    records = [controller, checkpoint, stage, planner]
    for record in records:
        helper = record['derivative']
        argv = [sys.executable, '-B', helper['path'], '--help']
        result = subprocess.run(argv, capture_output=True, text=True, encoding='utf-8')
        module.write(Path(helper['path']).name + '-help-process.json', {'argv':argv,
                     'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'helper':helper})
        module.require(result.returncode == 0, 'New helper help probe failed')
    module.write('explicit-knight-fields-derivatives-a01.json', {
        'at_utc':datetime.now(timezone.utc).isoformat(),'records':records,
        'reason':'Reject missing equal-to-None knight getter fields independently of native backend normalization',
        'zero_count_and_empty_markup_allowed':True,'full_roster_ID_claim':False,
        'old_helpers_preserved':True,'new_live_pending':True,'movie_changed':False})
    print(json.dumps(records,ensure_ascii=False))

if __name__ == '__main__':
    main()
