from pathlib import Path
import json

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004/live-attempt-010/mcp-client-evidence-002')
FILES = ['0020-r10-0020-player-consent-yes.native-01.json',
         '0022-r10-0022-source-ballot-yes.native-01.json',
         '0025-r10-0025-review-open.native-01.json']
KEYWORDS = ['eventinstance', 'event_instance', 'definitionkey', 'definition_key',
            'optionnumber', 'option_number', 'optionindex', 'option_index', 'handled',
            'confirmed', 'selected', 'revision', 'stage', 'status', 'postcondition',
            'submission', 'native_index', 'public_ordinal', 'public_option', 'decision_key']


def walk(value, path='', depth=0):
    if depth > 12:
        return
    if isinstance(value, dict):
        for key, child in value.items():
            if 'history' in key.lower() or key == 'source_inventory':
                continue
            where = path + '/' + key
            if not isinstance(child, (dict, list)) and any(term in key.lower() for term in KEYWORDS):
                yield where, child
            if isinstance(child, (dict, list)):
                yield from walk(child, where, depth + 1)
    elif isinstance(value, list):
        for index, child in enumerate(value[:15]):
            yield from walk(child, path + '/' + str(index), depth + 1)


for filename in FILES:
    data = json.loads((BASE / filename).read_bytes().decode('utf-8-sig'))
    result = data.get('result', {})
    summary = {'file': filename, 'status': data.get('status'),
               'session_id': data.get('session_id'), 'profile_sha256': data.get('profile_sha256')}
    if 'event_selection' in result:
        selection = result['event_selection']
        summary['event_selection'] = {key: selection.get(key) for key in [
            'status', 'postcondition_verified', 'old_event_instance_id', 'new_event_instance_id',
            'selected_option_number', 'selected_native_option_index', 'starting_revision', 'ending_revision']}
    later = result.get('later_actual_observation', {})
    if later:
        summary['later_actual_observation'] = {key: later.get(key) for key in [
            'current_event_instance_id', 'event_definition_key', 'queried_revision', 'queried_native_revision']}
    ack = result.get('native_ack', {})
    if ack:
        summary['native_ack'] = {key: ack.get(key) for key in [
            'status', 'native_handled', 'postcondition_verified', 'decision_key', 'expected_event_definition_key']}
    print(json.dumps(summary, ensure_ascii=False))
