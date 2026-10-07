"""Independent optional numeric query input; keeps legacy formalEvent UNKNOWN."""
from pathlib import Path
import derive_saved_title_reference_v3 as proof
import title_reference_hook as title_hook
import optional_numeric_scopes
need=proof.need
NUMERIC_QUERY_SCHEMA='lyd.author.native-event-value-query.v1'
EVENT_SOURCE_SHA='1d9b3a887f13dfeb3a5c1021fd37dc3c9952a9a380d7d6ccc1a3cb7a2dee1823'

def authenticate_query_source(spec,provenance):
    need(type(spec) is dict and set(spec)=={'schema','native_receipt','sdk_result'} and spec['schema']==NUMERIC_QUERY_SCHEMA,'closed explicit native numeric query descriptor')
    # The original SDK/native bytes remain untouched; reuse the exact common
    # authentication of the same closed native profile query receipt.
    common=dict(spec);common['schema']=title_hook.QUERY_SCHEMA
    return title_hook.authenticate_query_source(common,provenance)

def bind_before_frame(checkpoint, query, state, provenance, modules):
    """Exact original query binding; a Title scope is optional here."""
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
    need(state['checkpoint_sha256']==checkpoint['result']['checkpoint']['sha256'], 'actual saved query/checkpoint SHA')
    si=state['identity']
    need(si['pid']==after['game_pid'] and si['session_id']==provenance['session_id'] and si['revision']==after['native_revision'] and si['actor_id']==after['played_character_id'], 'actual saved query identity/frame')
    need(state['actual_pass'] is None and state['formal_mandate_credit'] is None, 'saved state invented credit')
    return context,before

def observe_bound(checkpoint,query,state,provenance,reader,converter,export,input_artifacts):
    refs=title_hook.bound_source_refs(reader,converter,export)
    need(refs['event_context']['sha256']==EVENT_SOURCE_SHA,'approved optional numeric contract source differs')
    modules=proof.load_bound_modules(refs)
    context,before=bind_before_frame(checkpoint,query,state,provenance,modules)
    observed=optional_numeric_scopes.observe(context,state,before,modules['event_context'])
    observed['source_artifacts']=refs
    observed['input_artifacts']=input_artifacts
    observed['after_frame']=converter.frame_binding(checkpoint['snapshot_after'])
    observed['raw_native_query_rewritten']=False
    observed['same_existing_verified_buffer_join']=True
    observed['extra_checkpoint_body_reads']=0
    return observed
