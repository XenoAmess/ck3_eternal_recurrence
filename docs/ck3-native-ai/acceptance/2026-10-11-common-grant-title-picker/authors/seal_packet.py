"""Seal only small, explicitly selected source and command records; no runtime actions."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = Path('C:/workspace/ck3_eternal_recurrence')
BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')

def pin(path):
    raw = path.read_bytes()
    if len(raw) > 1024**2:
        raise ValueError('Only explicitly bounded small records may be sealed')
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

selected = [
    'prepare_candidate.py', 'test_ck3_mod_acceptance_grant_title_picker.py',
    'run_focused.py', 'finish_candidate.py', 'run_changed_metadata.py', 'seal_packet.py',
    'candidate-001/PUBLIC-GRANT.incremental.patch', 'candidate-001/INTEGRATION-MANIFEST.json',
    'candidate-002/PUBLIC-GRANT.incremental.patch', 'candidate-002/INTEGRATION-MANIFEST.json',
    'focused-001/RESULT.actual.json', 'focused-001/stdout.log', 'focused-001/stderr.log',
    'focused-001/test-source.original.py', 'focused-002/RESULT.actual.json',
    'focused-002/stdout.log', 'focused-002/stderr.log',
    'REPORT.md', 'FUTURE-MANIFEST.fragment.json', 'TOPIC.candidate.md', 'prepare_ci.py',
    'ci-001/PUBLIC-GRANT-CI.incremental.patch', 'ci-001/INTEGRATION-MANIFEST.json',
    'close_source_task.py', 'TASKBUS-CLOSE.actual.json',
]
head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=REPO,
                      capture_output=True, check=True).stdout.decode('ascii').strip()
manifest = json.loads((HERE/'candidate-002/INTEGRATION-MANIFEST.json').read_text(encoding='utf-8'))
if head != manifest['authoring_head']:
    raise ValueError('MAIN HEAD changed while sealing')
for record in manifest['files']:
    current = REPO/record['relative_path']
    if record['before'] is None:
        if current.exists():
            raise ValueError('Candidate new MAIN path unexpectedly exists')
    else:
        actual = pin(current)
        if any(actual[key] != record['before'][key] for key in ('bytes', 'sha256')):
            raise ValueError('MAIN source changed while sealing: ' + record['relative_path'])
result = {
    'schema': 'lyd.common-grant-public-candidate-index.v1',
    'status': 'STATIC_READY_LIVE_NOT_RUN', 'MAIN_head': head,
    'final_candidate': pin(HERE/'candidate-002/INTEGRATION-MANIFEST.json'),
    'source_paths': [item['relative_path'] for item in manifest['files']] + ['.github/workflows/static-ci.yml'],
    'proposed_document': {'path':'docs/ck3-native-ai/2026-10-11-common-grant-title-picker.md',
                          'source':pin(HERE/'TOPIC.candidate.md'), 'MAIN_write':False},
    'CI_delta':pin(HERE/'ci-001/INTEGRATION-MANIFEST.json'),
    'files': [pin(HERE/name) for name in selected],
    'readonly_apply_check': {'argv': ['git','apply','--check','--whitespace=nowarn',
        str(HERE/'candidate-002/PUBLIC-GRANT.incremental.patch')], 'cwd': str(REPO),
        'exit_code': 0, 'tool_chunk_id': '2ec3b7', 'wall_time_seconds': 0.3403299,
        'started_utc': None, 'stdout': '', 'stderr': ''},
    'qualification': {'first_actual_tests': 8, 'first_actual_passed': 7,
        'first_actual_errors': 1, 'first_RED_preserved': True,
        'changed_metadata_case_actual_tests': 1, 'changed_metadata_case_exit': 0,
        'unchanged_seven_not_repeated': True,
        'test_only_delta': 'ToolAnnotations.model_dump(by_alias=True); production four paths unchanged'},
    'source_inputs': [pin(Path('C:/workspace/ck3-common-runtime/20261011-013/manifest.json')),
        pin(Path('C:/cbr3/CMakeCache.txt')),
        pin(REPO/'ck3_autonomous_player/src/xar_autoplayer/bridge/grant_title_picker_v1.py'),
        pin(REPO/'docs/ck3-native-ai/2026-10-10-common-challenger-graph-readonly.md'),
        pin(REPO/'docs/li-yu-dao/i3b-public-formal-b4.md'),
        pin(REPO/'docs/li-yu-dao/2026-10-11-i3b-formal-b5-source.md')],
    'future_source_head': None, 'future_runtime_key': None, 'future_title_full_id': None,
    'current_NPC_qualified': None, 'business_credit': None,
    'overall_status': '75_PERCENT_ESTIMATE_NOT_GREEN',
    'MAIN_mutations': 0, 'native_builds': 0, 'SDK_calls': 0, 'game_calls': 0,
    'existing_O13_R54_unchanged': True,
    'retention': {'raw_commands_days': 30, 'summary_days': 180,
                  'scope': 'small external source package only; no cache/save/ETL/wire/source-tree bodies'},
}
raw = (json.dumps(result, indent=2)+'\n').encode('utf-8')
if len(raw) > 65536:
    raise ValueError('Compact index exceeded cap')
with (HERE/'INDEX.json').open('xb') as stream:
    stream.write(raw)
print(json.dumps({'INDEX': pin(HERE/'INDEX.json'), 'status': result['status'],
                  'selected_files': len(selected), 'MAIN_head': head}))
