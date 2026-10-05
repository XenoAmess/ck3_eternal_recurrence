from pathlib import Path
import json

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
RUN = BASE / 'live-attempt-010'
SDK = RUN / 'mcp-client-evidence-002'

def read(path):
    return json.loads(Path(path).read_bytes().decode('utf-8-sig'))

def emit(label, value):
    print(json.dumps({'label': label, 'value': value}, ensure_ascii=False))

for sequence in range(56, 151):
    path = next(SDK.glob(f'{sequence:04d}-*.response.json'))
    response = read(path)
    prefix = path.name[:-len('.response.json')]
    request = read(SDK / (prefix + '.request.json'))
    values = []
    for native in response.get('native_receipts', []):
        raw = read(SDK / native['copy'])
        result = raw.get('result', {})
        context = result.get('current_event_window_context') or {}
        row = {'status': raw.get('status')}
        if context:
            row.update({'event': context.get('current_event_instance_id'), 'key': context.get('event_definition_key')})
        if sequence in [142, 143, 144, 146, 147, 148, 149, 150]:
            selection = result.get('event_selection') or {}
            ordinary = result.get('character_interaction_ordinary_context') or {}
            row.update({'result_status': result.get('status'), 'public': result.get('queried_revision'),
                'native': result.get('queried_native_revision'), 'selection_old': selection.get('old_event_instance_id'),
                'selection_new': selection.get('new_event_instance_id'),
                'selection_option': selection.get('selected_option_number'),
                'ordinary_can_send': ordinary.get('can_send'), 'ordinary_ready': ordinary.get('ready_to_initiate'),
                'ordinary_active': ordinary.get('active_event_present'), 'ordinary_date': ordinary.get('date_raw'),
                'ordinary_PID': ordinary.get('game_pid')})
        values.append(row)
    emit('SDK', {'sequence': sequence, 'request_id': request['request_id'], 'status': response['status'],
                 'sdk_bytes': (SDK / response['sdk_result']).stat().st_size, 'native': values})
for name in ['r10-0143-sixth-final-review-detail', 'r10-0144-sixth-detail-readback', 'r10-0145-sixth-final-review-confirm']:
    directory = RUN / 'root-call-stdio' / name
    emit('LOCAL_FILES', {'path': str(directory), 'files': [p.name for p in directory.iterdir()]})
    for path in directory.glob('*.stderr.bin'):
        if path.stat().st_size:
            emit('LOCAL_STDERR', {'path': str(path), 'text': path.read_bytes().decode('utf-8', errors='replace')[:2400]})
for directory in ['r10-second-proposal-emitted-evidence-20261005-002',
                  'r10-third-proposal-emitted-evidence-20261005-002',
                  'r10-fourth-proposal-emitted-evidence-20261005-002',
                  'r10-fifth-proposal-emitted-evidence-20261005-002']:
    value = read(BASE / directory / 'CONSUMPTION-MANIFEST.json')
    emit('EMITTED', {'path': directory, 'claim_request': value.get('claim_request_id')})
emit('ORPHAN_CONFIRM_ARGUMENTS', read(RUN / 'root-explicit-arguments/0144-sixth-final-review-confirm.json'))
