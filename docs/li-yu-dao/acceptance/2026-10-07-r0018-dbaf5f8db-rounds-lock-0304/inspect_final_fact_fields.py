from pathlib import Path
import json

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
RUN = BASE / 'live-attempt-018'
for index in [1, 2]:
    state = json.loads((RUN / f'B3-r{index}-pending-author-001/STATE.json').read_text(encoding='utf-8'))
    print('SCHOOLS ' + str(index) + ' ' + json.dumps(state.get('schools'), ensure_ascii=False)[:5000], flush=True)
    cancel = json.loads((RUN / f'formal-r{index}-cancel-001/RESULT.actual.json').read_text(encoding='utf-8'))
    print('CANCEL RESULT ' + str(index) + ' ' + json.dumps(cancel, ensure_ascii=False)[:7500], flush=True)
    frame = json.loads((RUN / f'formal-r{index}-cancel-001/FINAL-SNAPSHOT.actual.json').read_text(encoding='utf-8'))
    print('CANCEL FRAME ' + str(index) + ' ' + json.dumps({'keys': list(frame), 'scalars': {key: value for key, value in frame.items() if not isinstance(value, (dict, list))}, 'snapshot_fields': {key: frame.get(key) for key in ['revision', 'native_revision', 'active_event', 'paused', 'played_character', 'snapshot_id']}, 'diagnostics_identity': {key: frame.get('diagnostics', {}).get(key) for key in ['bridge_pid', 'connection_generation']}}, ensure_ascii=False)[:6500], flush=True)
failed = json.loads((BASE / 'r18-root-B3-r2-pending-materialize-execution-20261007-001/RESULT.actual.json').read_text(encoding='utf-8'))
print('MATERIALIZER FAILED ' + json.dumps(failed, ensure_ascii=False), flush=True)
projection = json.loads((BASE / 'r18-checkpoint-author-sourceonly-20261008-003/HOTFIX-SOURCE-PROJECTION.actual.json').read_text(encoding='utf-8'))
print('HOTFIX PROJECTION ' + json.dumps(projection, ensure_ascii=False)[:6500], flush=True)
