"""Read bounded summaries of the saved round/recovery evidence only."""

from pathlib import Path
import json

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
RUN = BASE / 'live-attempt-018'
FILES = [
    RUN / 'B3-r1-pending-author-001/STATE.json',
    RUN / 'B3-r1-pending-author-001/TYPED-PROTECTION.json',
    RUN / 'B3-r2-pending-author-001/STATE.json',
    RUN / 'B3-r2-pending-author-001/TYPED-PROTECTION.json',
    RUN / 'B3-r2-pending-author-001/RESULT.json',
    RUN / 'formal-r1-cancel-001/RESULT.actual.json',
    RUN / 'formal-r2-cancel-001/RESULT.actual.json',
    BASE / 'r18-root-B3-r2-pending-materialize-execution-20261007-001/RESULT.actual.json',
    BASE / 'r18-root-B3-r2-pending-materialize-execution-20261007-002/RESULT.actual.json',
    RUN / 'root-request-executions/072-r2-pending-save/RESULT.actual.json',
    RUN / 'root-request-executions/086-r2-cancel-cleanup-save/RESULT.actual.json',
    BASE / 'r18-checkpoint-author-sourceonly-20261008-003/INDEX.json',
]
for index in [80, 84, 88]:
    FILES.extend(sorted((RUN / 'mcp-client-001').glob(f'{index:04d}-*.sdk-result.json')))
    FILES.extend(sorted((RUN / 'mcp-client-001').glob(f'{index:04d}-*.native-01.json')))

def shape(value):
    if isinstance(value, dict):
        return {'keys': list(value)[:45]}
    if isinstance(value, list):
        return {'items': len(value)}
    if isinstance(value, str) and len(value) > 1600:
        return value[:1600] + ' [bounded]'
    return value

for path in FILES:
    obj = json.loads(path.read_text(encoding='utf-8-sig'))
    summary = {key: shape(value) for key, value in obj.items()}
    for key in ['round', 'identity', 'frame_binding', 'calls', 'event_selection', 'result', 'request', 'response', 'official_native_copies', 'error']:
        value = obj.get(key)
        if isinstance(value, dict):
            summary[key] = {k: shape(v) for k, v in value.items()}
        elif isinstance(value, list) and key != 'calls':
            summary[key] = value[:3]
    if path.name == 'STATE.json':
        roster = obj.get('roster', {})
        summary['roster_selection'] = {key: roster.get(key) for key in ['saved_current_human_ids', 'saved_current_human_faith_ids', 'captured_member_ids']}
        summary['actor_variable_shapes'] = shape(obj.get('actor', {}).get('variables'))
    if path.name.endswith('.sdk-result.json'):
        summary['content_excerpt'] = [shape(block.get('text')) for block in obj.get('content', []) if isinstance(block, dict) and block.get('type') == 'text'][:2]
    print('\nFILE ' + str(path), flush=True)
    print(json.dumps(summary, indent=2, ensure_ascii=False)[:14500], flush=True)
