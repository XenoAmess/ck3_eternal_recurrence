"""Print bounded summaries of already saved JSON; never contact the game."""

from pathlib import Path
import json

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
RUN = BASE / 'live-attempt-018'
FILES = [
    BASE / 'r18-root-head-export-20261007-002/REPORT.json',
    BASE / 'r18-actual-sdk-metadata-20261007-001/RESULT.json',
    RUN / 'baseline-author-001/RESULT.json',
    RUN / 'baseline-author-001/STATE.json',
    RUN / 'baseline-author-001/TYPED-PROTECTION.json',
    RUN / 'initial0240-political-control-002/REPORT.json',
    RUN / 'mcp-client-001/0012-r18-012-first430-reference-query.native-01.json',
    RUN / 'mcp-client-001/0013-r18-013-first430-wait.native-01.json',
]

def shape(value):
    if isinstance(value, dict):
        return {'keys': list(value)[:45]}
    if isinstance(value, list):
        return {'items': len(value)}
    return value

for path in FILES:
    obj = json.loads(path.read_text(encoding='utf-8-sig'))
    summary = {key: shape(value) for key, value in obj.items()}
    for key in ['source_binding', 'native_clean_gate_contract', 'reader_result', 'reader', 'coverage', 'game_identity', 'actual_binding', 'complete_political_AST_matches', 'before_frame_binding', 'after_frame_binding']:
        if key in obj and isinstance(obj[key], dict):
            summary[key] = {k: shape(v) for k, v in obj[key].items()}
    if path.name.endswith('native-01.json'):
        result = obj.get('result', {})
        summary['result'] = {key: shape(value) for key, value in result.items()}
        if 'event_selection' in result:
            summary['event_selection'] = result['event_selection']
        for which in ['snapshot_before', 'snapshot_after']:
            frame = obj.get(which, {})
            summary[which] = {key: frame.get(key) for key in ['snapshot_id', 'revision', 'date_raw', 'paused', 'played_character', 'played_character_gold', 'played_character_prestige', 'played_character_piety', 'active_event']}
    print('\nFILE ' + str(path), flush=True)
    print(json.dumps(summary, ensure_ascii=False, indent=2)[:18000], flush=True)
