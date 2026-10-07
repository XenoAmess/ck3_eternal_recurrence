from pathlib import Path
import json

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
RUN = BASE / 'live-attempt-018'

def compact(row):
    if not isinstance(row, dict):
        return row
    return {key: row[key] for key in ['present', 'number', 'scale', 'type', 'identity', 'value', 'status', 'reason'] if key in row}

for index in [1, 2]:
    directory = RUN / f'B3-r{index}-pending-author-001'
    state = json.loads((directory / 'STATE.json').read_text(encoding='utf-8'))
    typed = json.loads((directory / 'TYPED-PROTECTION.json').read_text(encoding='utf-8'))
    result = json.loads((directory / 'RESULT.json').read_text(encoding='utf-8'))
    actor = state['actor']
    roster = state['roster']['members']
    selected = []
    iterable = roster.values() if isinstance(roster, dict) else roster
    for member in iterable:
        if member.get('character_id', member.get('id')) in [31254, 65865]:
            selected.append({key: compact(value) for key, value in member.items() if key in ['character_id', 'member_serial', 'was_player', 'player_yes', 'vote', 'was_elector', 'member_rite_id']})
    print(json.dumps({'round': index, 'state_round': state['round'], 'actor_votes': {key: compact(actor.get(key)) for key in ['was_player', 'player_yes', 'vote', 'was_elector']}, 'relevant_actor_variables': {key: compact(value) for key, value in actor.get('variables', {}).items() if key.startswith('lyd_i3b_') and any(part in key for part in ['signed', 'yes', 'vot', 'count', 'elect', 'serial', 'nonce', 'phase'])}, 'members': selected, 'typed_checks': len(typed['checks']), 'protection_checks_match': typed['protection_checks_match'], 'assessment': state.get('assessment'), 'author_result': {key: result.get(key) for key in ['status', 'utc', 'game_calls', 'save_body_reads', 'actual_pass', 'formal_mandate_credit']}}, indent=2, ensure_ascii=False), flush=True)

paths = [
    BASE / 'r18-root-B3-r2-pending-materialize-execution-20261007-001/RESULT.actual.json',
    BASE / 'r18-root-B3-r2-pending-materialize-execution-20261007-002/RESULT.actual.json',
    RUN / 'formal-r1-cancel-001/RESULT.actual.json',
    RUN / 'formal-r2-cancel-001/RESULT.actual.json',
]
for path in paths:
    obj = json.loads(path.read_text(encoding='utf-8'))
    output = {key: value for key, value in obj.items() if not isinstance(value, (dict, list))}
    output['calls'] = [{key: value for key, value in row.items() if not isinstance(value, (dict, list))} for row in obj.get('calls', [])]
    print('\nFILE ' + str(path), flush=True)
    print(json.dumps(output, indent=2, ensure_ascii=False), flush=True)
    if 'error' in obj:
        print('ERROR ' + str(obj['error']), flush=True)

index = json.loads((BASE / 'r18-checkpoint-author-sourceonly-20261008-003/INDEX.json').read_text(encoding='utf-8'))
print('SOURCE PREPARATION ' + json.dumps({key: index.get(key) for key in ['correction', 'hotfix_projection', 'ROOT_save72_recovery_argv', 'actual_SAVE72_input']}, indent=2, ensure_ascii=False), flush=True)
