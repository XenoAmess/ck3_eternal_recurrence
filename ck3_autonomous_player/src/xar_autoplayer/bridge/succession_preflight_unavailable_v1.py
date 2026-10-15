"""A typed unavailable root observation cannot become succession/action evidence."""

SCHEMA = 'xar.succession-preflight-unavailable.v1'

def observe_unavailable_preflight_v1(bundle, snapshot, frame):
    from .turn_bundle_contract import TURN_BUNDLE_V1_SCHEMA
    from .campaign_root_context_contract import QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY

    if not isinstance(bundle, dict) or bundle.get('schema') != TURN_BUNDLE_V1_SCHEMA:
        raise ValueError('succession preflight bundle schema differs')
    if bundle.get('status') != 'unavailable':
        raise ValueError('succession preflight observation requires unavailable')
    reason, source, binding = (bundle.get(k) for k in ('unavailable_reason', 'source', 'binding'))
    if (not isinstance(reason, str) or not reason or len(reason) > 4096
            or not isinstance(source, dict)
            or source.get('capability') != QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY
            or type(source.get('query_sequence')) is not int
            or not 1 <= source['query_sequence'] <= 2**64 - 1
            or not isinstance(binding, dict)):
        raise ValueError('succession preflight unavailable provenance is malformed')
    played = snapshot.get('played_character')
    if (snapshot.get('paused') is not True or snapshot.get('map_ready') is not True
            or snapshot.get('one_life_terminal_reason') is not None
            or snapshot.get('active_event') is not None
            or snapshot.get('pending_character_interaction') is not None
            or not isinstance(played, dict) or played.get('alive') is not True
            or type(played.get('character_id')) is not int or played['character_id'] <= 0
            or not isinstance(frame, dict) or frame.get('status') != 'complete'):
        raise ValueError('succession preflight unavailable is not a living paused frame')
    for key in ('snapshot_id', 'revision', 'native_revision', 'date_raw'):
        if binding.get(key) != snapshot.get(key) or frame.get(key) != snapshot.get(key):
            raise ValueError('succession preflight unavailable frame changed')
    if (frame.get('actor_character_id') != played['character_id']
            or frame.get('episode_run_id') != snapshot.get('episode_run_id')):
        raise ValueError('succession preflight unavailable identity differs')
    return {'schema': SCHEMA, 'status': 'unavailable', 'available': False,
            'read_only': True, 'business_submission': False, 'accepted': False,
            'replan_required': True, 'replay_allowed': False,
            'unavailable_reason': reason, 'binding': dict(frame),
            'source': dict(source), 'succession_expectation_retained': False}
