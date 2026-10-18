"""Normal R10 preparation through the original public CaseClient.

This is a readiness/policy-input case, not a three-arm execution engine. It
retains the public control row and labels derived full-wire views explicitly.
No SDK/host/session, sampling, time advance, Move, split or merge is created.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import sys
import importlib
from datetime import datetime, timezone


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def pin(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def small_json(ref, limit=1024 * 1024):
    path = Path(ref['path'])
    need(path.stat().st_size <= limit, 'R10 small input exceeds bound')
    actual = pin(path)
    need(actual['bytes'] == ref['bytes'] and actual['sha256'] == ref['sha256'], 'R10 exact input changed')
    return json.loads(path.read_bytes())


def module(path, name):
    path = Path(path)
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    original = list(sys.path)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(value)
    finally:
        sys.path[:] = original
    return value


def evaluate_policy_records(repo, label, *, plan, evidence, **records):
    """Use existing pure A/B/C consumers, without a legacy live constructor.

    These are their existing arguments, not a new arm schema. Caller must
    provide actual cold-start/preview/runtime records for A and an already
    qualified observation for C. This neither dispatches actions nor grants
    readiness/site/fee/native credit. Formal per-arm orchestration is pending.
    """
    repo = Path(repo).resolve()
    base = repo / 'promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02'
    original = list(sys.path)
    sys.path.insert(0, str(base / 'comparison'))
    try:
        compare = importlib.import_module('r10_compare')
        need(Path(compare.__file__).resolve() == base / 'comparison/r10_compare.py',
             'Existing comparison import comes from another source')
        if label == 'A':
            consumer = importlib.import_module('strategy_a')
            need(Path(consumer.__file__).resolve() == base / 'comparison/strategy_a.py',
                 'Existing A import comes from another source')
            return consumer.admit(plan, records['runtime'], records['loaded_save_sha256'],
                                  records['cold_start'], records['fresh_preview'], evidence)
        if label == 'B':
            consumer = importlib.import_module('strategy_b')
            need(Path(consumer.__file__).resolve() == base / 'comparison/strategy_b.py',
                 'Existing B import comes from another source')
            return consumer.recipe(plan, evidence)
        need(label == 'C', 'Existing strategy label must be A/B/C')
        consumer = module(base / 'strategy_c/strategy_c.py', 'r10_common_existing_C_consumer')
        return consumer.start(plan, records['observation'])
    finally:
        sys.path[:] = original


def validate_contract(context):
    need(context['case_contract'].get('schema') == 'xar.e04.r10-common-preparation.v1',
         'R10 common preparation contract differs')
    value = context.get('case_inputs', {})
    if not value:
        return
    for key in ('army_id', 'war_id', 'goal_province_id', 'staging_province_id'):
        need(type(value.get(key)) is int and 0 <= value[key] < 2**31, 'Observed R10 ' + key + ' required')
    if value.get('native_carmy_id') is not None:
        need(type(value['native_carmy_id']) is int and -(2**31) <= value['native_carmy_id'] < 2**31
             and value['native_carmy_id'] != -1, 'Signed full native CArmy ID required')
    if value.get('agreed_commander_id') is not None:
        need(type(value['agreed_commander_id']) is int and 0 <= value['agreed_commander_id'] < 2**31,
             'Agreed commander must be an actual observed ID')
    need(type(value.get('director_scope_revision')) is str and value['director_scope_revision'],
         'Explicit director scope revision required')
    need(value.get('phase', 'readiness') == 'readiness',
         'This common preparation case has no formal A/B/C executor; never label a pilot as an arm')


def prepare_case(context):
    from ck3_live_run_id import current_machine_id
    from ck3_mod_acceptance_prepare import materialize_product_profile, finish_product_profile, write_json
    validate_contract(context)
    values, seed = context['case_inputs'], context['saved_campaign']
    for name in ('normal_checkpoint_receipt', 'normal_checkpoint_build_receipt'):
        small_json(values[name])
    repo = Path(context['shared_source_root'])
    bootstrap = module(repo / 'promo/ck3_native_war_ai/episode-04-march-logistics/tools/capture_bootstrap.py',
                       'r10_common_normal_checkpoint_library')
    qualified = bootstrap.checkpoint_source(Path(seed['save']), Path(values['normal_checkpoint_receipt']['path']),
        Path(values['normal_checkpoint_build_receipt']['path']), bootstrap.game_target('1.20.0.4'), seed['player_id'])
    need(qualified is not None and qualified['actor_id'] == seed['player_id']
         and qualified['date_raw'] == seed['date_raw'] and qualified['save']['bytes'] == seed['bytes']
         and qualified['save']['sha256'] == seed['sha256'], 'Normal source does not match selected saved campaign')
    # Existing shared primitive explicitly supports None => no enabled mods.
    profile = materialize_product_profile(context, None, values['plain_configuration'])
    finished = finish_product_profile(context, profile, provenance={
        'kind': 'R10-normal-preparation-readiness-only', 'normal_checkpoint': qualified,
        'common_T0_frozen': False, 'formal_ABC_arm': False,
        'open_kaishek': {'status': 'not-applicable',
                        'reason': 'No script/fixture generated; typed native queries and normal-save provenance only.'}})
    initial = Path(context['output']) / 'initial-plan.json'
    write_json(initial, {'steps': []})
    return {'machine_id': current_machine_id(), 'startup': {'mode': 'saved_campaign',
        'state_dir': profile['state_dir'], 'saved_campaign': {**seed, 'product_inventory': profile['product_inventory']['path']}},
        'initial_plan': pin(initial), 'profile_preparation': finished, 'files': profile['files'],
        'fixture_mounted': False, 'runtime_status': 'NOT_RUN', 'formal_ABC_arm': False,
        'business_contract_applicable': False, 'business_pass': False}


class CommonRequestRelay:
    """Legacy envelope shape over the same public queue, with honest origin.

    A compact public row and a derived full-wire body intentionally differ.
    Existing legacy raw_result_reference is not manufactured: it means Driver
    bytes, which the shared full-wire recovery does not claim to have produced.
    """
    def __init__(self, context, client, *, machine):
        from ck3_mod_acceptance_full_army import ensure_common_full_army_client
        self.client = ensure_common_full_army_client(client)
        self.RUN = Path(context['run_dir'])
        self.ASSETS = self.RUN.parent
        self.CONTEXT = {'machine_id': machine, 'run_id': context['run_id'],
                        'origin': 'actual_public_common_case_not_legacy_vanilla_allocation'}
        self.machine = machine
        self.refs = {}

    def request(self, identifier, tool, arguments, timeout=None):
        need(re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,100}', identifier) is not None, 'Bounded request ID required')
        need(identifier not in self.refs, 'Original common request already consumed; never replay')
        # Claim before submit, including failures/unknown results.
        self.refs[identifier] = {'status': 'submitted_result_not_yet_known'}
        rows = self.client.execute_plan([{'id': identifier, 'tool': tool, 'args': arguments,
                                        'fresh_revision': False, 'continue_on_error': True}],
                                       identifier, timeout=timeout)
        need(len(rows) == 1 and rows[0].get('id') == identifier, 'Original common result identity differs')
        row = rows[0]
        public_name = row.get('continuation_public_step_id', identifier)
        # A wrapper prefix maps the plan name and the physical step ID together.
        original = Path(self.client.output) / (public_name + '.actual-results.json')
        saved = json.loads(original.read_bytes())
        actual = saved.get('rows')
        need(type(actual) is list and len(actual) == 1 and actual[0].get('id') == public_name,
             'Original compact public control receipt absent or ambiguous')
        body = row.get('result')
        error = row.get('ok') is not True or bool(row.get('error'))
        envelope = {'machine_id': self.machine,
            'request': {'request_id': identifier, 'tool': tool, 'arguments': arguments},
            'is_error': error, 'body': body,
            'transport_origin': 'derived_common_control_envelope_not_original_SDK_transport',
            'common_original': {**pin(original), 'pointer': '/rows/0'},
            'common_public_step_id': public_name, 'wire_full_result_proof': row.get('wire_full_result_proof'),
            'original_Driver_raw_result_reference_available': False}
        path = self.client.checkpoint(identifier + '-r10-common-envelope', envelope)
        self.refs[identifier] = {'status': 'error' if error else 'received', 'envelope': pin(path)}
        need(not error and type(body) is dict, 'Common query failed; original preserved, never replay')
        return envelope


def collect_ready_t0(context, relay, *, source_binding):
    from xar_autoplayer.bridge.episode04_ready_t0_12004 import (
        ready_t0_readonly_requests_12004, evaluate_episode04_ready_t0_12004)
    values = context['case_inputs']
    before = relay.request('r10-ready-before', 'ck3_take_snapshot', {'include_native_command_history': False})['body']
    requests = ready_t0_readonly_requests_12004(before, army_id=values['army_id'], war_id=values['war_id'])
    names = ('strengths', 'commander', 'cash', 'occupation', 'after')
    bodies = {}
    for name, request in zip(names, requests):
        bodies[name] = relay.request('r10-ready-' + name, request['tool'], request['arguments'])['body']
    result = evaluate_episode04_ready_t0_12004(before=before, after=bodies['after'],
        strengths=bodies['strengths'], commander=bodies['commander'], cash=bodies['cash'],
        occupation=bodies['occupation'], source_binding=source_binding,
        **{key: values.get(key) for key in ('army_id', 'native_carmy_id', 'war_id', 'goal_province_id',
                                      'staging_province_id', 'agreed_commander_id')})
    return {'readiness': result, 'sources': dict(relay.refs), 'queries_submitted': 6,
            'natural_days_advanced': 0, 'Move_split_merge_Save_submitted': False,
            'common_T0_frozen': False, 'formal_ABC_arm': False}


def run_case(context, client):
    from ck3_live_run_id import current_machine_id
    from ck3_mod_acceptance_cases.r08_writer_common_adapter import retained_creation_filetime
    validate_contract(context)
    machine = current_machine_id()
    client.retain_process()
    # PID/create-time comes from the original retained OS handle, not old proofs.
    relay = CommonRequestRelay(context, client, machine=machine)
    frame = relay.client.snapshot()
    need(frame['diagnostics']['bridge_pid'] == client._process['pid'], 'Owned OS/native PID differs')
    values = context['case_inputs']
    source = values['normal_checkpoint_receipt']
    small_json(source)
    binding = {'machine_id': machine, 'pid': client._process['pid'],
        'process_creation_filetime_100ns': retained_creation_filetime(client),
        'connection_generation': frame['diagnostics']['connection_generation'],
        'actor_id': frame['played_character']['character_id'], 'episode_run_id': frame['episode_run_id'],
        'game_version': context['shared_game']['version'],
        'executable_sha256': context['shared_game']['exe_sha256'],
        'normal_source_receipt_sha256': source['sha256'],
        'director_scope_revision': values['director_scope_revision']}
    result = collect_ready_t0(context, relay, source_binding=binding)
    result.update(machine_id=machine, observed_at_utc=datetime.now(timezone.utc).isoformat(),
        source_binding=binding, status='READINESS_PILOT_ONLY',
        remaining=['Root chooses and normally saves common S0 after actual route/site pilot',
                   'two distinct stationary sites with qualified actual positive stock growth',
                   'frozen PLAN then three independent normal cold loads',
                   'formal common A/B/C stage executor connection and actual 90-day horizon',
                   'R08 qualified applied maintenance/payer/cadence before compare_fees=true'],
        research_card_closed=False, business_pass=False, formal_ABC_completed=0)
    client.checkpoint('r10-common-preparation-result', result)
    return result


def verify_case(context):
    path = Path(context['output']) / 'r10-common-preparation-result.json'
    result = json.loads(path.read_bytes()) if path.is_file() else {}
    return {'machine_id': result.get('machine_id', 'unknown'),
        'readiness_inputs_collected': bool(result),
        'military_t0_frame_ready': result.get('readiness', {}).get('military_t0_frame_ready') is True,
        'case_contract_qualified': False, 'gui_contract_qualified': False,
        'business_contract_applicable': False, 'business_pass': False,
        'formal_ABC_completed': 0, 'research_card_closed': False,
        'scope': 'Common normal-source readiness pilot; no formal ABC or growth/payment qualification'}
