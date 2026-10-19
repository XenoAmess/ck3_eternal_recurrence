"""Saved mechanism capture through the public profile and CaseClient only.

This adapter launches no process and imports no frozen episode helper. Its
interactive checkpoint preserves a paused world; presentation is separately
restricted by tools/faith_e02_capture_queue.py. Neither completion nor query ACK
awards mechanism, GUI, beneficiary or product acceptance.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

CASE = 'faith-engine-e02-types-readonly-v1'
PRODUCT = 'faith-engine'
SAVED_IDENTITY = {
    'bytes': 50210503,
    'sha256': '7bd48c5eb8c51a24badd02ba57cb030dba3526da4483479ae9adc231cea7ea7e',
    'player_id': 15893,
    'date_raw': 51394920,
}
CREATION_UI_TOOLS = frozenset({
    'ck3_open_holy_site_creation_window_v1', 'ck3_select_holy_site_creation_type_v1',
    'ck3_select_holy_site_creation_barony_v1', 'ck3_set_holy_site_creation_artifact_selection_v1',
})
READONLY_TOOLS = frozenset({
    'ck3_query_player_holy_site_creation_context_v1', 'ck3_query_player_religion_context_v1',
    'ck3_query_player_holy_site_v1', 'ck3_query_faith_power_ui_v1',
})
LIFECYCLE_TOOLS = frozenset({
    'ck3_take_snapshot', 'ck3_get_capabilities', 'ck3_query_campaign_root_context_v1',
    'ck3_query_current_event_window_context_v1', 'ck3_open_faith_window_v1',
    'ck3_open_holy_site_window_v1', 'ck3_query_ingame_ui_window_v1',
    'ck3_present_faith_power_ui_v1', 'ck3_query_normal_exit_context_v1',
    'ck3_request_normal_exit_v1', 'ck3_observe_normal_exit_v1',
})
REQUIRED_TOOLS = CREATION_UI_TOOLS | READONLY_TOOLS | LIFECYCLE_TOOLS


def require(value, message):
    if not value:
        raise ValueError(message)


def pin(path):
    path = Path(path).resolve()
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest.hexdigest()}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def validate_contract(context):
    contract = context['case_contract']
    require(contract.get('schema') == 'faith-engine-e02-saved-readonly-case-v1'
            and contract.get('product') == context.get('product') == PRODUCT
            and contract.get('case') == context.get('case') == CASE,
            'B1 saved readonly case identity differs')
    saved = contract.get('saved_input', {})
    require(set(saved) == {'save', *SAVED_IDENTITY} and isinstance(saved['save'], str)
            and all(type(saved[k]) is type(v) and saved[k] == v for k, v in SAVED_IDENTITY.items()),
            'B1 requires the original actual-C2 save, player and date')
    require(contract.get('profile') == {'enabled_mods': [], 'product_files': []}
            and contract.get('scope') == {
                'world_confirmation_allowed': False, 'day_advance_allowed': False,
                'new_save_allowed': False, 'ordinary_campaign_credit': False,
                'preparation_mod_mounted': False},
            'B1 is an unmodified saved vanilla mechanism capture')
    require(isinstance(contract.get('machine_id'), str) and contract['machine_id']
            and contract['machine_id'] != 'unknown', 'Explicit target machine identity required')
    case = context.get('case_spec')
    if case is not None:
        require(case.get('opt_in_holy_site_creation_ui') is True
                and case.get('opt_in_holy_site_creation_create_once') is False
                and case.get('opt_in_holy_site_relic_actions') is False
                and case.get('opt_in_player_rite_creation_actions') is False,
                'B1 enables selectors only, never a world action lane')
        required = case.get('required_mcp_tools', [])
        readonly = case.get('opt_in_read_only_mcp_tools', [])
        require(len(required) == len(set(required)) and set(required) == REQUIRED_TOOLS
                and len(readonly) == len(set(readonly)) and set(readonly) == READONLY_TOOLS,
                'B1 finite tool contract differs; all four selectors are required')
    return contract


def _admission(context, machine):
    reference = context['case_inputs']['storage_admission']
    require(pin(reference['path']) == reference, 'Current B1 storage admission changed')
    value = read(reference['path'])
    require(value.get('machine_id') == machine and value.get('active') is True,
            'Current B1 storage admission belongs to another machine or is inactive')
    expiry = datetime.fromisoformat(value['expires_at_utc'].replace('Z', '+00:00'))
    require(expiry.tzinfo is not None and datetime.now(timezone.utc) < expiry,
            'Current B1 storage admission expired')
    return reference


def prepare_case(context):
    from ck3_mod_acceptance_prepare import materialize_product_profile, finish_product_profile
    contract = validate_contract(context)
    from ck3_live_run_id import current_machine_id
    require(current_machine_id() == contract['machine_id'], 'B1 executing machine differs')
    admission = _admission(context, contract['machine_id'])
    saved = dict(context['saved_campaign'])
    require(saved == contract['saved_input'], 'B1 prepare input differs from its reviewed C2 contract')
    path = Path(saved['save'])
    require(path.suffix.casefold() == '.ck3' and path.is_file() and not path.is_symlink(),
            'Original immutable ordinary C2 save is required')
    before = path.stat()
    actual = pin(path)
    after = path.stat()
    require(actual['bytes'] == saved['bytes'] and actual['sha256'] == saved['sha256']
            and before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns,
            'Original C2 checkpoint bytes/SHA changed while preparing')
    profile = materialize_product_profile(context, None, context['case_inputs']['configuration'])
    profile = finish_product_profile(context, profile, provenance={
        'machine_id': contract['machine_id'], 'kind': 'faith-e02-actual-C2-readonly-capture',
        'saved_input': saved, 'storage_admission': admission,
        'preparation_mod_mounted': False, 'world_actions_performed': False,
        'actual_restore_observed': False})
    return {'startup': {'mode': 'saved_campaign', 'state_dir': profile['state_dir'],
                        'saved_campaign': {**saved, 'product_inventory': profile['product_inventory']['path']}},
            'profile': profile, 'initial_plan': context['case_spec']['initial_plan'],
            'runtime_status': 'NOT_RUN', 'business_pass': False, 'product_release_pass': False}


def validate_capture_frame(frame, contract):
    saved = contract['saved_input']
    require(frame.get('paused') is True and frame.get('active_event') is None
            and frame.get('date_raw') == saved['date_raw']
            and type(frame.get('played_character', {}).get('character_id')) is int
            and frame['played_character']['character_id'] == saved['player_id'],
            'B1 actual paused actor/date/event state crossed the original saved scene')


def run_case(context, client):
    from ck3_mod_acceptance_client import write_once
    contract = validate_contract(context)
    before = client.snapshot()
    validate_capture_frame(before, contract)
    client.checkpoint('faith-e02-readonly-before', before)
    response = client.root_checkpoint('faith-e02-readonly-finish', {
        'machine_id': contract['machine_id'], 'case': CASE,
        'capture_queue_validator': 'tools/faith_e02_capture_queue.py',
        'allowed_scope': 'native observations and finite original GUI selections, independently read back',
        'world_confirmation_allowed': False, 'day_advance_allowed': False,
        'new_save_allowed': False, 'ACK_is_world_result': False,
        'Root_finish_requires_original_ck3_alive': True, 'business_pass': False}, reserve=120)
    require(response.get('run_id') == context['run_id']
            and response.get('reviewer') == client.operator_reviewer and response.get('status') == 'complete',
            'B1 Root finish crossed actual run/reviewer or remains incomplete')
    after = client.snapshot()
    validate_capture_frame(after, contract)
    client.checkpoint('faith-e02-readonly-after', after)
    result = {'schema': 'faith-engine-e02-readonly-holder-result-v1',
              'machine_id': contract['machine_id'], 'run_id': context['run_id'], 'case': CASE,
              'root_finish': response, 'research_holder_completed': True,
              'before_snapshot_id': before.get('snapshot_id'), 'after_snapshot_id': after.get('snapshot_id'),
              'paused_actor_date_preserved': True, 'world_mutation_absence_proven': False,
              'case_contract_qualified': False, 'gui_contract_qualified': False,
              'business_pass': False, 'product_release_pass': False}
    write_once(Path(context['output']) / 'faith-e02-readonly-holder-result.json', result)
    return result


def verify_case(context):
    contract = validate_contract(context)
    result = read(Path(context['output']) / 'faith-e02-readonly-holder-result.json')
    require(result.get('run_id') == context['run_id'] and result.get('case') == CASE
            and result.get('machine_id') == contract['machine_id'], 'B1 holder result crossed its run/machine')
    return {'research_holder_completed': result.get('research_holder_completed') is True,
            'paused_actor_date_preserved': result.get('paused_actor_date_preserved') is True,
            'case_contract_qualified': False, 'gui_contract_qualified': False,
            'business_pass': False, 'product_release_pass': False,
            'scope': 'readonly capture holder; each source, selection, pixel and mechanism outcome is separate'}
