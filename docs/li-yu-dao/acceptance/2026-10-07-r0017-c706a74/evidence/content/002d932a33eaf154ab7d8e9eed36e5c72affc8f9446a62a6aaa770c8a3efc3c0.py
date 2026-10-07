"""Derive a Title token from existing native query and parsed checkpoint JSON only.

No checkpoint body, SDK, process, bus, or desktop access. This emits separate
evidence and a candidate legacy binding; it never edits an existing STATE.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from types import ModuleType

sys.dont_write_bytecode = True
SCHEMA = 'lyd.saved-title-reference-before-frame-request.v1'
MODULE_KEYS = {'reader', 'transition', 'strict', 'parser', 'save_fields',
               'dto_primitives', 'event_context', 'version_identity'}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def unique_json(data):
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, 'duplicate JSON key ' + key)
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('nonfinite JSON ' + value)
    return json.loads(data.decode('utf-8-sig'), object_pairs_hook=pairs, parse_constant=invalid)


def artifact(desc, *, suffix):
    need(type(desc) is dict and set(desc) == {'path', 'bytes', 'sha256'}, 'closed artifact descriptor')
    path = Path(desc['path'])
    need(path.is_absolute() and path.suffix == suffix, 'artifact absolute path/suffix')
    need(type(desc['bytes']) is int and 0 < desc['bytes'] <= 8 * 1024 * 1024, 'bounded compact artifact')
    need(type(desc['sha256']) is str and re.fullmatch('[0-9a-f]{64}', desc['sha256']), 'artifact SHA')
    data = path.read_bytes()
    need(len(data) == desc['bytes'] and digest(data) == desc['sha256'], 'artifact bytes/SHA changed ' + str(path))
    return data


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_bound_modules(refs):
    need(type(refs) is dict and set(refs) == MODULE_KEYS, 'closed source module set')
    for desc in refs.values():
        artifact(desc, suffix='.py')
    root = Path(refs['reader']['path']).parent
    need(Path(refs['transition']['path']).parent == root and Path(refs['strict']['path']).parent == root, 'reader module directory')
    sys.path.insert(0, str(root))
    reader = load_module('i3b_checkpoint_reader', refs['reader']['path'])
    transition = load_module('checkpoint_transition_v2', refs['transition']['path'])
    actual = {'reader': reader, 'transition': transition, 'strict': transition.strict,
              'parser': sys.modules['bounded_save_parser'],
              'save_fields': sys.modules['save_fields'], 'dto_primitives': transition.strict.sdk}
    # Load the two exact pure contracts without executing bridge/__init__.py.
    namespace = 'saved_title_evidence_contracts'
    package = ModuleType(namespace)
    package.__path__ = [str(Path(refs['event_context']['path']).parent)]
    sys.modules[namespace] = package
    actual['version_identity'] = load_module(namespace + '.version_identity', refs['version_identity']['path'])
    actual['event_context'] = load_module(namespace + '.event_window_context_contract', refs['event_context']['path'])
    for key, module in actual.items():
        need(Path(module.__file__).resolve() == Path(refs[key]['path']).resolve(), 'loaded module path differs ' + key)
        artifact(refs[key], suffix='.py')
    return actual


def derive(checkpoint, query, state, provenance, modules):
    """One strict before-frame Title witness; all arguments are existing JSON."""
    reader, transition = modules['reader'], modules['transition']
    same = transition.same_json
    after, save_transition = transition.bind_checkpoint_transition(checkpoint, provenance)
    before = save_transition['before_binding']
    transition.strict.outer_identity(query, provenance)
    need(query.get('status') == 'native_event_query_verified', 'original native query receipt status')
    result = query.get('result')
    need(type(result) is dict and result.get('step') == 'query-current-event-window-context-v1'
         and result.get('accepted') is True and result.get('status') == 'available'
         and result.get('backend_id') == 'native-headless' and result.get('scope') == 'exact-current-event-window', 'native query result')
    expected_frame = {'snapshot_id': before['snapshot_id'], 'revision': before['revision'],
                      'native_revision': before['native_revision'], 'date_raw': before['date_raw']}
    need(result.get('source') == {**expected_frame, 'paused': True, 'backend_id': 'native-headless'}, 'original query source is not exact checkpoint-before frame')
    event = checkpoint['snapshot_before']['active_event']
    need(type(event) is dict and event.get('source') == 'native' and type(event.get('instance_id')) is int, 'native current before event')
    need(result.get('binding') == {**expected_frame, 'expected_revision': before['revision'],
                                  'event_instance_id': event['instance_id']}, 'original query event/frame binding')
    for field, value in (('queried_snapshot_id', before['snapshot_id']),
                         ('queried_revision', before['revision']), ('queried_native_revision', before['native_revision'])):
        need(type(result.get(field)) is type(value) and result[field] == value, 'query frame ' + field)
    context = modules['event_context'].normalize_current_event_window_context_v1(
        result.get('current_event_window_context'), expected_event_instance_id=event['instance_id'],
        expected_date_raw=before['date_raw'], expected_snapshot_revision=before['native_revision'])
    need(context['status'] == 'available' and context['window_match_count'] == 1
         and context['event_definition_key'] == 'lyd.430'
         and result.get('current_event_window_context_ready') is True, 'available single formal review event context')
    for key, value in context.items():
        need(key in result and same(value, result[key]), 'flattened/native context differs ' + key)
    actor_scope = context['root_scope']
    need(actor_scope == {'status': 'available', 'raw_type_index': 4, 'type_key': 'character', 'subtype': 0,
                         'typed_identity': {'status': 'available', 'kind': 'character', 'character_id': before['played_character_id']}}, 'native root actor join')
    rows = checkpoint['snapshot_before']['native_command_history']
    wrapper_keys = {'scope', 'source', 'binding'}
    raw_keys = set(context) | {'step', 'accepted', 'query_sequence', 'backend_id', 'current_event_window_context',
                               'current_event_window_context_ready', 'current_event_effect_indicators_ready',
                               'queried_snapshot_id', 'queried_revision', 'queried_native_revision'}
    need(set(result) == raw_keys | wrapper_keys, 'closed original query result fields')
    need(type(result['query_sequence']) is int and result['query_sequence'] > 0
         and result['current_event_effect_indicators_ready'] is True, 'original query positive sequence/readiness')
    # The profile's scope/source/binding wrapper is validated above, not added
    # to raw native history. Every native field must still match exactly.
    native_result = {key: value for key, value in result.items() if key not in wrapper_keys}
    need(type(rows) is list and rows and rows[-1] == {'index': len(rows), 'command': result['step'], 'ok': True, 'result': native_result}, 'original query native fields are not exact last unchanged before-history row')
    candidates = [row for row in context['saved_scopes'] if row['name'] == 'lyd_i3b_title']
    need(len(candidates) == 1, 'unique named native Title sample required')
    native = candidates[0]['scope']
    need(native.get('status') == 'available' and type(native.get('raw_type_index')) is int
         and native['raw_type_index'] == 5 and native.get('type_key') == 'landed_title'
         and type(native.get('subtype')) is int and native['subtype'] == 0, 'observed native landed Title scope')
    identity = native.get('typed_identity')
    need(type(identity) is dict and set(identity) == {'status', 'kind', 'title_id'}
         and identity['status'] == 'available' and identity['kind'] == 'landed_title', 'native full Title identity')
    title_id = reader.valid_id(identity['title_id'], 'native sample full Title id')

    need(state.get('schema') == 'lyd.i3b.checkpoint-observations.v1'
         and state.get('source_head') == reader.HEAD and provenance.get('reader_contract_source_head') == reader.HEAD, 'saved reader semantic contract')
    si = state['identity']
    need(si['pid'] == after['game_pid'] and si['session_id'] == provenance['session_id']
         and si['revision'] == after['native_revision'] and si['actor_id'] == after['played_character_id'], 'saved observations identity/frame')
    ck = checkpoint['result']['checkpoint']
    need(state.get('checkpoint_sha256') == ck['sha256'] and Path(si['checkpoint_id']) == Path(ck['path']), 'saved observation exact checkpoint identity')
    actor = state['actor']
    need(actor['character_id'] == si['actor_id'] and actor['AST_sha256'] == reader.ast_sha(actor['entries']), 'saved actor full AST')
    raw_actor = reader.raw_character(actor['character_id'], actor['entries'])
    raw_lists = raw_actor['lists']
    need(same(raw_lists, actor['lists']), 'saved actor list projection differs from retained raw AST')
    saved_list = raw_lists.get('lyd_i3b_political_titles')
    need(type(saved_list) is dict and saved_list.get('present') is True, 'actual saved political Title list')
    items = saved_list['items']
    found = [item for item in items if item.get('identity') == str(title_id)]
    need(len(found) == 1, 'unique exact saved full-ID native Title sample')
    sample = found[0]
    token = sample.get('type')
    need(type(token) is str and token and token not in ('char', 'faith', 'rite', 'value', 'boolean'), 'contradictory saved Title token')
    need(sample['entries'] == [{'key': 'type', 'value': token}, {'key': 'identity', 'value': str(title_id)}], 'closed actual saved typed sample AST')
    ids = []
    for item in items:
        need(item['type'] == token, 'heterogeneous saved Title list token')
        ids.append(reader.scalar_id(item['identity'], 'saved political Title full id'))
    need(len(ids) == len(set(ids)), 'duplicate saved Title full ids')
    titles = [row for row in state['protected_titles'] if row['title_id'] == title_id]
    need(len(titles) == 1, 'unique actual full saved Title record')
    title = titles[0]
    need(title['AST_sha256'] == reader.ast_sha(title['entries']) == title['baseline_AST_sha256'], 'sample Title raw/full protected AST differs')
    raw_holder = reader.scalar_id(reader.one(title['entries'], 'holder'), 'saved Title holder')
    need(raw_holder == title['holder'] == title['baseline_holder'] == si['actor_id'], 'actual full Title holder join')
    for name in (f'political_{title_id}_holder', f'political_{title_id}_full_AST_protected'):
        check = [row for row in state['checks'] if row['name'] == name]
        need(len(check) == 1 and check[0]['matches'] is True, 'existing protected Title check ' + name)
    return {'schema': 'lyd.saved-native-title-reference-before-frame-evidence.v1',
            'runtime_source_head': provenance['source_head'], 'reader_contract_source_head': reader.HEAD,
            'qualification': 'ACTUAL_NATIVE_BEFORE_FRAME_AND_SAVED_TYPED_FULL_ID_JOIN_OBSERVED',
            'checkpoint_sha256': state['checkpoint_sha256'], 'native_query_before_frame': before,
            'saved_observation_after_frame': after, 'raw_native_revision_rewritten': False,
            'save_transition': {key: value for key, value in save_transition.items()
                                if key not in ('snapshot_before_original', 'snapshot_after_original')},
            'query_history_index': rows[-1]['index'], 'event_instance_id': context['current_event_instance_id'],
            'native_Title_sample': candidates[0], 'saved_typed_sample': sample,
            'derived_title_type': token, 'saved_title_full_id': title_id, 'saved_title_holder': raw_holder,
            'saved_title_AST_sha256': title['AST_sha256'], 'saved_actor_AST_sha256': actor['AST_sha256'],
            'scope': 'current exact paused checkpoint, build, profile, connection and observed serialized Title token',
            'old_reference_qualification_retained': state['native_reference_qualification'],
            'old_assessment_retained': state['assessment'], 'actual_pass': None,
            'actual_native_runtime_pass': None, 'formal_mandate_credit': None,
            'limitations': ['G2/G3 alone supply no precommit Title sample; metadata is a declared DTO contract.',
                           'This does not qualify religious-head factory properties or formal callback serial/nonce/value payloads.',
                           'A different checkpoint/frame requires its own validated witness or an explicit frozen mapping contract.']}


def run(request):
    need(type(request) is dict and set(request) == {'schema', 'checkpoint', 'query', 'state', 'provenance', 'modules', 'output'}, 'closed derivation request')
    need(request['schema'] == SCHEMA, 'derivation request schema')
    output = Path(request['output'])
    need(output.is_absolute() and not output.exists(), 'fresh external output required')
    sources = {key: unique_json(artifact(request[key], suffix='.json')) for key in ('checkpoint', 'query', 'state', 'provenance')}
    modules = load_bound_modules(request['modules'])
    evidence = derive(**sources, modules=modules)
    evidence['input_artifacts'] = {key: request[key] for key in sources}
    evidence['source_artifacts'] = request['modules']
    data = json_bytes(evidence)
    binding = {'schema': 'lyd.saved-native-reference-binding.v1', 'source_head': modules['reader'].HEAD,
               'evidence_sha256': digest(data), 'title_type': evidence['derived_title_type']}
    output.mkdir(parents=True, exist_ok=False)
    (output / 'TITLE-REFERENCE-EVIDENCE.actual.json').write_bytes(data)
    (output / 'TITLE-REFERENCE-BINDING.candidate.json').write_bytes(json_bytes(binding))
    return {'status': evidence['qualification'], 'derived_title_type': binding['title_type'],
            'title_full_id': evidence['saved_title_full_id'], 'evidence_sha256': digest(data),
            'actual_pass': None, 'formal_mandate_credit': None, 'existing_STATE_changed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(unique_json(args.request.read_bytes())), ensure_ascii=False))


if __name__ == '__main__':
    main()
