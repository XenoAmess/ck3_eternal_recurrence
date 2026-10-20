"""A07 finite RAM adapter; preserve the consumed A06 tree and its real failure.

Only the two external OBS configs are mutable historical outputs. All117
immutable prepared inputs are checked exactly; no runtime/Task/screen writes.
"""
import ast
import json
from pathlib import Path
import sys
import types

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve().parent
sys.path.insert(0, str(OWN))
import prepare_c23_a06_union_v1 as previous

prior = previous.prior
MACHINE, O, T0 = previous.MACHINE, previous.O, previous.T0
U6 = previous.U6
U7 = U6.with_name('runtime-a07')
T5 = U7
HELPER = previous.HELPER
UNION_PIN = previous.UNION_PIN
ADOPTER_PIN = previous.ADOPTER_PIN
PREVIOUS_PIN = (12213, 'efc9dd071f14b1e0338bdad96a3babcf3bee5b99f272e913098c5f9c61828538')
PREPARED = O / 'A06-PREPARED01.json'
PREPARED_PIN = (32683, 'b122568b7129b42c220b329eeca130aadeb39ae46238b483182ea9f3f963671d')
INDEX = O / 'A06-SOURCE-PREFLIGHT-FAILURE-INDEX01.json'
INDEX_PIN = (4092, '56d898e80e8dac113844dcefedc669d26c9d906b0b0757becb2b337b2c99a44b')
require, exact = previous.require, previous.exact


def actual_graph():
    exact(previous.__file__, PREVIOUS_PIN)
    prepared = json.loads(exact(PREPARED, PREPARED_PIN))
    require(prepared.get('machine_id') == MACHINE and prepared.get('complete44_actual_readback') is True
            and prepared.get('canonical6_original_max8_verifier_passed') is True,
            'actual A06 prepared closure required')
    quote = prior.checked(prepared['quote'], 262144)
    require(quote['machine_id'] == MACHINE and len(prepared['outputs']) == 119,
            'actual A06 prepared119 required')
    profile = prior.checked(next(row for row in prepared['outputs']
        if Path(row['path']) == U6 / 'ROOT-OBS-PROFILE-C23.json'))
    config = Path(profile['config_root'])
    mutable = {config / 'basic/profiles' / profile['profile_name'] / 'basic.ini',
               config / 'basic/scenes' / (profile['collection_name'] + '.json')}
    rows, values, observations = {}, {}, []
    for row in prepared['outputs']:
        path = Path(row['path']).resolve()
        require(path not in rows, 'unique actual prepared path required')
        data = prior.raw(path, 524288)
        if path in mutable:
            observations.append({'historical_prepared': row, 'current': prior.ref(path),
                'role': 'OBS mutable historical config; body is not reused for new private profile'})
        else:
            require((len(data), prior.sha(data)) == (row['bytes'], row['sha256']),
                    'immutable A06 prepared leaf differs: ' + str(path))
            values[path] = data
        rows[path] = row
    require(len(rows) == 119 and len(values) == 117 and len(observations) == 2,
            'exact117 immutable and two observed mutable OBS configs required')
    index = json.loads(exact(INDEX, INDEX_PIN))
    require(index.get('machine_id') == MACHINE and index.get('no_SEM_CAP_or_gameplay') is True
            and index.get('NEXT') == index.get('first_sequence_not_submitted') == 10481
            and index.get('Game_business_credit') == 0
            and index.get('actual_Game_created_and_forced_exit1') is True
            and index.get('original_119_sources_immutable_except_two_OBS_private_configs') is True,
            'actual A06 forced no-business failure index required')
    for row in index['actual_facts']:
        exact(row['path'], (row['bytes'], row['sha256']), 32768)
    return values, quote, rows, observations


def guard_source():
    return f'''
def _validate_a07_attempt(args,config):
    value=_validate_a06_attempt(args,config)
    reference=value['prior_failure_a06']
    require((reference.get('bytes'),reference.get('sha256'))=={INDEX_PIN!r},'exact actual A06 preflight failure index required')
    index=_a03_checked(reference)
    require(index.get('machine_id')==MACHINE and index.get('no_SEM_CAP_or_gameplay') is True
        and index.get('Game_business_credit')==0 and index.get('actual_Game_created_and_forced_exit1') is True
        and index.get('NEXT')==index.get('first_sequence_not_submitted')==10481,
        'actual forced A06 Game with unchanged business frontier required')
    rows={{Path(row['path']).name:row for row in index['actual_facts']}}
    closed=_a03_checked(rows['ROOT-FRESH-SUPERVISOR-CLOSED-C23-A06.json'])
    game=_a03_checked(rows['ROOT-ACTUAL-GAME-EXIT-C23.json'])
    require(closed.get('machine_id')==game.get('machine_id')==MACHINE
        and closed.get('attempt_id')=='a06' and closed.get('cleanup_classification')=='FORCED_OWNED_GAME_CLEANUP'
        and closed.get('failure')=={{'type':'BrokenPipeError','message':'[WinError 109] private custody peek'}}
        and (closed.get('owned_cleanup') or {{}}).get('ck3_pid')==game.get('pid')==59668
        and game.get('creation_filetime')==134369485859890359 and game.get('kernel_signaled') is True
        and game.get('exit_code')==1 and game.get('forced_owned_job_cleanup') is True
        and game.get('normal_wm_close_qualified') is False
        and closed['owned_cleanup'].get('ck3_exit_code')==1
        and closed['owned_cleanup'].get('job_active_processes_final')==0
        and closed['owned_cleanup'].get('tree_gone') is True and closed['owned_cleanup'].get('cleanup_proven') is True
        and (closed.get('keeper') or {{}}).get('thread_exited') is True,
        'actual A06 forced Game1/job0 closure required; never convert it to normal exit')
    tasks={{Path(row['path']).parent.name:row for row in index['actual_facts'] if Path(row['path']).name=='CLOSED.json'}}
    nonces={{closed['attempt_nonce'],closed['task_nonce']}}
    for role,code in (('supervisor',1),('display',0)):
        task=_a03_checked(tasks['spec-'+role+'-a06'])
        removed=_a03_checked(rows['ROOT-A06-'+role+'-UNREGISTER01.json'])
        require(task.get('machine_id')==removed.get('machine_id')==MACHINE
            and task.get('child_exit_code')==task.get('bootstrap_exit_code')==code
            and task.get('job_active_after_stage')==0 and task.get('forced_remaining_cleanup') is False
            and removed.get('returncode')==0 and isinstance(removed.get('stdout'),str)
            and len(removed['stdout'])<=16384,'actual A06 consumed '+role+' Task closure required')
        operation=json.loads(removed['stdout']);actual=operation.get('actual') or {{}}
        require(operation.get('machine_id')==MACHINE and operation.get('operation')=='unregister'
            and operation.get('task_name')=='XARG2ManagedOwner-'+task['nonce']
            and actual.get('absent_after') is True and actual.get('instances')==0,
            'actual A06 '+role+' Task absence required')
        nonces.add(task['nonce'])
    released=_a03_checked(rows['ROOT-A06-SCREEN-RELEASE01.json'])
    require(released.get('returncode')==0 and isinstance(released.get('stdout'),str),'actual A06 screen release wrapper required')
    release=json.loads(released['stdout']);retirement=(release.get('event') or {{}}).get('retirement') or {{}}
    require(release.get('ok') is True and (release.get('task') or {{}}).get('resources')==[]
        and release['task'].get('state')=='waiting' and retirement.get('kind')=='expired-own-claim-released'
        and retirement.get('prior_sequence')==7595,'actual expired A06 screen claim released, unresolved RED preserved')
    require(args.attempt_nonce not in nonces and args.task_nonce not in nonces,'A07 needs independent attempt and Task nonces')
    return value

'''.encode('utf-8')


def build_sources():
    values, quote, rows, mutable = actual_graph()
    names = [Path(row['path']).relative_to(previous.U5).as_posix()
             for row in quote['sources']['actual_source_rows']]
    require(len(names) == len(set(names)) == 89, 'actual89 source names required')
    source = {name: values[(U6 / name).resolve()] for name in names}
    helper = source[HELPER]
    for name, data in tuple(source.items()):
        source[name] = data.replace(b'C23-A06', b'C23-A07')
    require(source[HELPER] == helper and (len(helper), prior.sha(helper)) ==
        (17637, 'bae312f0fb07d370252ecc5714666fe1790a4db33bca32599e0e9bcb56d64a8e'),
        'qualified Source26 helper remains byte-identical')
    supervisor = source['root_native30_supervisor_c23.py']
    for before, after, count in (
        ("args.attempt=='a06'", "args.attempt=='a07'", 1),
        ("value.get('attempt_id')=='a06'", "value.get('attempt_id')=='a07'", 1),
        ('choices=("a06",)', 'choices=("a07",)', 1),
        ('"attempt_id":"a06"', '"attempt_id":"a07"', 2),
        ('_validate_a06_attempt(args, config)', '_validate_a07_attempt(args, config)', 1),
    ):
        supervisor = prior.swap(supervisor, before, after, count)
    require(supervisor.count(b'def main(args):') == 1, 'one original supervisor main required')
    source['root_native30_supervisor_c23.py'] = supervisor.replace(b'def main(args):', guard_source() + b'def main(args):')
    for name, data in source.items():
        compile(data, name, 'exec')
    return source, {'schema': 'xar.C23-A07-actual-A06-source-adapter/v1', 'machine_id': MACHINE,
        'source_count': 86, 'private_creator_count': 3, 'feeder': {},
        'actual_source_rows': [rows[(U6 / name).resolve()] for name in names],
        'prepared_rows_observed': 119, 'immutable_prepared_rows_verified': 117,
        'mutable_OBS_config_observations': mutable, 'strict_Source26_helper_byte_identical': True,
        'A06_failure_index': prior.ref(INDEX), 'new_runtime_root': str(U7), 'actual_Game_or_RPC_credit': 0}


def state_guard():
    report = previous.state_guard()
    require((U6 / 'state').resolve(strict=True) == (T0 / 'state').resolve(strict=True), 'actual A06 state alias differs')
    report['future_alias'] = str(U7 / 'state')
    return report


def compose(plan, *, display_values, display_review, companion_values):
    original = exact(prior.__file__, UNION_PIN).decode('utf-8')
    node = next(node for node in ast.parse(original).body if isinstance(node, ast.FunctionDef) and node.name == 'compose')
    source = ast.get_source_segment(original, node)
    source = source.replace('C23-A05', 'C23-A07').replace('C23-A04', 'C23-A06')
    source = source.replace("'a05'", "'a07'").replace('spec-supervisor-a05', 'spec-supervisor-a07')
    require(source.count('2026-10-20T06:30:00+00:00') == 1, 'one original review seam required')
    source = source.replace('2026-10-20T06:30:00+00:00', '2026-10-20T10:30:00+00:00')
    before = "prior_failure_a04_unregistered=ref(O/'SUPERVISOR-A04-UNREGISTER.json'))"
    after = "prior_failure_a04_unregistered=ref(O/'SUPERVISOR-A04-UNREGISTER.json'),prior_failure_a06=ref(INDEX))"
    require(source.count(before) == 1, 'one new predecessor config seam required')
    source = source.replace(before, after, 1)
    scope = {**vars(prior), '__file__': __file__, 'T4': U6, 'T5': U7,
             'INDEX': INDEX, 'build_sources': build_sources, 'state_guard': state_guard}
    exec(compile(source, 'A07-original-union-finite-RAM-projection', 'exec'), scope)
    outputs, quote = scope['compose'](plan, display_values=display_values,
        display_review=display_review, companion_values=companion_values)
    quote.update(original_union_source=prior.ref(prior.__file__), previous_A06_adapter_source=prior.ref(previous.__file__),
                 actual_A06_failure_index=prior.ref(INDEX),
                 once_only_predecessor_Task_retained=True)
    return outputs, quote


def compose_plan(plan_ref):
    plan = prior.checked(plan_ref, 131072)
    require(prior.ref(__file__) == plan['union_producer'], 'actual reviewed A07 adapter required')
    path = Path(plan['display_producer']['path']).resolve()
    require(path == OWN / 'prepare_c23_a07_display_v1.py' and prior.ref(path) == plan['display_producer'],
            'actual reviewed A07 display adapter required')
    display = prior._module(path, '_a07_exact_display_RAM')
    values, review, companion = display.compose(plan['display'])
    outputs, quote = compose(plan, display_values=values, display_review=review, companion_values=companion)
    quote.update(adopter=prior.ref(__file__), input_plan=plan_ref,
                 original_adopter_source=prior.ref(OWN / 'adopt_c23_a05_union_v1.py'))
    return plan, outputs, quote


def adopt(plan_ref, quote_ref, card_ref):
    path = OWN / 'adopt_c23_a05_union_v1.py'
    text = exact(path, ADOPTER_PIN).decode('utf-8')
    module = prior._module(path, '_a07_original_adopter_helpers_RAM')
    node = next(node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef) and node.name == 'adopt')
    source = ast.get_source_segment(text, node).replace('A05', 'A07').replace('a05', 'a07')
    bridge = types.SimpleNamespace(MACHINE=MACHINE, T5=U7, T0=T0, O=O,
        checked=prior.checked, ref=prior.ref, raw=prior.raw, _module=prior._module)
    scope = {**vars(module), 'compose': compose_plan, 'union': bridge}
    exec(compile(source, 'A07-original-create-only-adopter-projection', 'exec'), scope)
    return scope['adopt'](plan_ref, quote_ref, card_ref)


def cold_owner(inputs):
    text = exact(prior.__file__, UNION_PIN).decode('utf-8')
    node = next(node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef) and node.name == 'cold_owner')
    source = ast.get_source_segment(text, node).replace('A05', 'A07').replace('a05', 'a07')
    scope = {**vars(prior), 'T5': U7}
    exec(compile(source, 'A07-existing-cold-owner-projection', 'exec'), scope)
    return scope['cold_owner'](inputs)
