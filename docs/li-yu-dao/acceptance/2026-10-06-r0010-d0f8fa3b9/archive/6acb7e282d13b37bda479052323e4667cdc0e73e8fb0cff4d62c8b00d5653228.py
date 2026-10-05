from pathlib import Path
import json

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
RUN = BASE / 'live-attempt-010'
SDK = RUN / 'mcp-client-evidence-002'

def read(path):
    return json.loads(Path(path).read_bytes().decode('utf-8-sig'))

def emit(label, value):
    print(json.dumps({'label': label, 'value': value}, ensure_ascii=False))

for sequence in []:
    response_path = next(SDK.glob(f'{sequence:04d}-*.response.json'))
    response = read(response_path)
    request = read(SDK / (response_path.name[:-len('.response.json')] + '.request.json'))
    natives = []
    for row in response.get('native_receipts', []):
        receipt = read(SDK / row['copy'])
        result = receipt.get('result', {})
        event = result.get('current_event_window_context', {})
        if not isinstance(event, dict):
            event = {}
        ordinary = result.get('character_interaction_ordinary_context', {})
        if not isinstance(ordinary, dict):
            ordinary = {}
        natives.append({'status': receipt.get('status'), 'result_keys': list(result),
                        'event_id': event.get('current_event_instance_id'),
                        'event_key': event.get('event_definition_key'),
                        'public_revision': result.get('queried_revision'),
                        'native_revision': result.get('queried_native_revision'),
                        'binding': result.get('binding'),
                        'ordinary_ready': ordinary.get('ready_to_initiate'),
                        'ordinary_can_send': ordinary.get('can_send'),
                        'action': result.get('action'),
                        'business_verified': receipt.get('business_effects_verified')})
    emit('SDK', {'sequence': sequence, 'request_id': request['request_id'],
                 'operation': request['operation'], 'arguments': request.get('arguments'),
                 'response_status': response['status'], 'native': natives})

actions = RUN / 'native-state/native-session/ordinary-interaction-actions'
for path in sorted(actions.glob('*')):
    if path.is_file() and path.name.endswith(('claim.json', 'release.json', 'release.consumed.json')):
        value = read(path)
        emit(path.name, {k: value.get(k) for k in ['schema', 'request_id', 'status', 'claim_ordinal',
                         'new_intent_lineage', 'permit_sha256', 'permit_path', 'next_intent_id',
                         'consumed_at_utc', 'claimed_at_utc', 'claim_path', 'new_claim_request_id'] if k in value})
for directory in ['root-first-consumption-host-request-001',
                  'root-first-consumption-emit-invocation-002',
                  'root-first-consumption-release-invocation-001']:
    emit('DIRECTORY', {'path': directory, 'files': [p.name for p in (RUN / directory).iterdir()]})
facts = read(BASE / 'r10-actual-second-open-join-readback-20261005-001/PROPOSAL-OPENED-FACTS.json')
emit('SECOND_TYPED_KEYS', list(facts))
for key, value in facts.items():
    if not isinstance(value, (dict, list)) or key in ['proposal_before', 'proposal_after', 'round_counts',
                                                    'current_round_votes', 'current_player_vote',
                                                    'wallet_before', 'wallet_after', 'history_before', 'history_after']:
        emit('SECOND_TYPED_' + key, value)
for sequence in [42, 54]:
    path = next(SDK.glob(f'{sequence:04d}-*.native-01.json'))
    value = read(path)
    result = value['result']
    emit('ACTION' + str(sequence), {k: result.get(k) for k in ['status',
                 'event_selection', 'active_event', 'revision', 'snapshot_id', 'action_request_id',
                 'action_claim_path', 'verification_scope', 'business_effects_verified', 'full_product_acceptance_credit'] if k in result})
