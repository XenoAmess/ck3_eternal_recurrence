"""Author007 explicit original SDK/native query source and current-frame join."""
from pathlib import Path
import sys
import derive_saved_title_reference_v3 as proof
from bind_existing_join_request import bind_existing_join_request

QUERY_SCHEMA = 'lyd.author.native-title-reference-query.v1'


def validate_sdk_native(sdk, native):
    need = proof.need
    need(type(sdk) is dict and set(sdk) == {'_meta', 'content', 'structuredContent', 'isError', 'resultType'}, 'closed original SDK query result')
    need(sdk['isError'] is False and sdk['resultType'] == 'complete', 'successful complete original SDK query required')
    need(sdk['_meta'] == {'io.modelcontextprotocol/serverInfo': {'name': 'CK3 frozen native profile', 'version': ''}}, 'actual SDK native profile server identity')
    content = sdk['content']
    need(type(content) is list and len(content) == 1 and type(content[0]) is dict
         and set(content[0]) == {'type', 'text', 'annotations', '_meta'}, 'one exact SDK native text receipt')
    text = content[0]
    need(text['type'] == 'text' and type(text['text']) is str and text['annotations'] is None and text['_meta'] is None, 'original SDK text receipt shape')
    detached = proof.unique_json(text['text'].encode('utf-8'))
    same = lambda a, b: proof.json_bytes(a) == proof.json_bytes(b)
    need(same(detached, native) and same(sdk['structuredContent'], native), 'SDK text/structuredContent/original native receipt differ')
    return native


def authenticate_query_source(spec, provenance):
    need = proof.need
    need(type(spec) is dict and set(spec) == {'schema', 'native_receipt', 'sdk_result'}, 'closed explicit Title query descriptor')
    need(spec['schema'] == QUERY_SCHEMA, 'explicit Title query descriptor schema')
    native = proof.unique_json(proof.artifact(spec['native_receipt'], suffix='.json'))
    sdk = proof.unique_json(proof.artifact(spec['sdk_result'], suffix='.json'))
    validate_sdk_native(sdk, native)
    need(native.get('schema') == 'ck3.native-profile-receipt.v1' and native.get('status') == 'native_event_query_verified', 'original native query profile receipt')
    for key in ('session_id', 'profile_sha256', 'pipe_name'):
        need(native.get(key) == provenance[key], 'explicit query actual provenance differs ' + key)
    need(type(native.get('recorded_at_utc')) is str and native['recorded_at_utc'], 'actual query recorded UTC')
    need(type(native.get('receipt_path')) is str and Path(native['receipt_path']).resolve() == Path(spec['native_receipt']['path']).resolve(), 'native original receipt_path differs from supplied file')
    return native


def bound_source_refs(reader, converter, export):
    root = Path(export['source_root']) / 'ck3_autonomous_player/src/xar_autoplayer/bridge'
    paths = {'reader': Path(reader.__file__), 'transition': Path(converter.transition.__file__),
             'strict': Path(converter.transition.strict.__file__),
             'parser': Path(sys.modules['bounded_save_parser'].__file__),
             'save_fields': Path(sys.modules['save_fields'].__file__),
             'dto_primitives': Path(converter.transition.strict.sdk.__file__),
             'event_context': root / 'event_window_context_contract.py', 'version_identity': root / 'version_identity.py'}
    result = {}
    for key, path in paths.items():
        data = path.read_bytes()
        result[key] = {'path': str(path), 'bytes': len(data), 'sha256': proof.digest(data)}
    return result


def bind_current_query(checkpoint, query, state, provenance, request, reader, converter, export, input_artifacts, output):
    """Uses the author's retained parsed state and existing later buffer join."""
    need = proof.need
    need(export['source']['head'] == provenance['source_head'], 'Title proof actual clean source HEAD')
    source_refs = bound_source_refs(reader, converter, export)
    executing = provenance['executing_reader_artifact']
    need(source_refs['reader']['bytes'] == executing['bytes'] and source_refs['reader']['sha256'] == executing['sha256'], 'Title proof executing reader differs from actual registry')
    modules = proof.load_bound_modules(source_refs)
    new_request, evidence, binding = bind_existing_join_request(
        checkpoint, query, state, provenance, request, modules, input_artifacts, source_refs)
    evidence_path = Path(output) / 'TITLE-REFERENCE-EVIDENCE.actual.json'
    binding_path = Path(output) / 'TITLE-REFERENCE-BINDING.actual-or-pending.json'
    for path, data in ((evidence_path, evidence), (binding_path, binding)):
        with path.open('xb') as stream:
            stream.write(data)
    observed = proof.unique_json(evidence)
    return new_request, {'schema': 'lyd.author.current-checkpoint-title-reference-observation.v1',
        'qualification': observed['qualification'], 'explicit_current_query': input_artifacts['query'],
        'original_SDK_query': input_artifacts['sdk_result'],
        'before_frame': observed['native_query_before_frame'], 'after_frame': observed['saved_observation_after_frame'],
        'evidence': {'path': str(evidence_path), 'bytes': len(evidence), 'sha256': proof.digest(evidence)},
        'binding': {'path': str(binding_path), 'bytes': len(binding), 'sha256': proof.digest(binding)},
        'same_existing_verified_buffer_join': True, 'extra_checkpoint_body_reads': 0,
        'old_STATE_retained': True, 'actual_pass': None, 'formal_mandate_credit': None}
