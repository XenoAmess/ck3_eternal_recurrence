"""A06 RAM adapter over the actual closed A05 graph and original union composer.

No runtime, Task, screen, Game, Git or large-body write/hash is provided.
The consumed A05 namespaces remain immutable inputs, never retry targets.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import types

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve().parent
sys.path.insert(0, str(OWN))
import prepare_c23_a05_union_v1 as prior

MACHINE = prior.MACHINE
U5 = prior.T5
U6 = U5.with_name('runtime-a06')
O = prior.O
HELPER = prior.HELPER
UNION_PIN = (25193, '0e2befdca7cac51f13d9d7e4e85a5d66e5dad159eb127457207a3160072db004')
QUOTE_PIN = (114511, 'fd03557ffc5e7e36551f4216a8ef360d93df58b349d96e162be1e41e63fc591f')
AMEND_PIN = (12225, '67dd439927c4b8e28bc2cb58a2b148d6c579f528cf7e98c66794f4d1a39d9baf')
INDEX = O / 'A05-SOURCE-PRELAUNCH-FAILURE-INDEX01.json'
INDEX_PIN = (2348, '57988d13bce96d0d3632ae9412ce012a3f585be17b9e14d7b6f9a87aca1e3b1f')
ADOPTER_PIN = (19887, '46c23f995d52883150e60985ba5776fdbae279fab5c59b6e46e24cf209d4c5f6')
T0 = prior.T0
T5 = U6


def require(ok, why):
    if not ok:
        raise ValueError('A06 finite adapter denied: ' + why)


def exact(path, expected, limit=524288):
    data = prior.raw(path, limit)
    require((len(data), prior.sha(data)) == expected, 'actual fixed input differs: ' + str(path))
    return data


def actual_graph():
    """Verify all119 original/amended inputs; do not copy failure-only outputs."""
    quote = json.loads(exact(O / 'A05-ROOT-QUOTE02.json', QUOTE_PIN))
    amend = json.loads(exact(O / 'A05-COLD-AMENDMENT-COMPLETE01.json', AMEND_PIN))
    require(amend.get('machine_id') == MACHINE and amend.get('actual_projected_pins_verified') == 119
            and amend.get('status') == 'ACTUAL_COLD_AMENDMENT_VERIFIED_NOT_RUN', 'actual cold amendment required')
    rows = {Path(row['path']).resolve(): {key: row[key] for key in ('path', 'bytes', 'sha256')}
            for row in quote['files']}
    require(len(rows) == 119, 'actual original119 required')
    for pair in amend['archived_originals']:
        path = Path(pair['old']['path']).resolve()
        require(rows[path] == pair['old'], 'amendment predecessor differs')
        rows[path] = pair['new']
    values = {}
    for path, item in rows.items():
        data = prior.raw(path, 524288)
        require((len(data), prior.sha(data)) == (item['bytes'], item['sha256']),
                'actual projected119 leaf differs: ' + str(path))
        values[path] = data
    index = json.loads(exact(INDEX, INDEX_PIN))
    require(index.get('machine_id') == MACHINE and index.get('no_Game_creation_attempted') is True
            and index.get('no_SEM_CAP_or_gameplay') is True and index.get('NEXT') == 10481
            and index.get('Game_business_credit') == 0
            and index.get('original_projected_119_unchanged_since_cold_amendment') is True,
            'actual no-Game A05 closed index required')
    for item in index['actual_facts']:
        prior.checked(item, 32768)
    return values, quote, rows


def guard_source():
    return f'''
def _validate_a06_attempt(args,config):
    value=_validate_a05_attempt(args,config)
    reference=value['prior_failure_a05']
    require((reference.get('bytes'),reference.get('sha256'))=={INDEX_PIN!r},'exact actual A05 prelaunch failure index required')
    index=_a03_checked(reference)
    require(index.get('machine_id')==MACHINE and index.get('no_Game_creation_attempted') is True
        and index.get('no_SEM_CAP_or_gameplay') is True and index.get('Game_business_credit')==0
        and index.get('NEXT')==index.get('first_sequence_not_submitted')==10481,
        'actual A05 no-Game no-RPC frontier required')
    rows={{Path(row['path']).name:row for row in index['actual_facts']}}
    closed=_a03_checked(rows['ROOT-FRESH-SUPERVISOR-CLOSED-C23-A05.json'])
    task=_a03_checked(rows['CLOSED.json'])
    removed=_a03_checked(rows['ROOT-A05-supervisor-UNREGISTER01.json'])
    require(closed.get('machine_id')==task.get('machine_id')==removed.get('machine_id')==MACHINE
        and closed.get('attempt_id')=='a05' and closed.get('cleanup_classification')=='NO_GAME_CREATION_ATTEMPTED'
        and closed.get('failure')=={{'type':'RuntimeError','message':'actual offline pixels expired before Game launch; no automatic retry'}}
        and closed.get('owned_cleanup') is None and closed.get('sdk_actual_exit') is None
        and (closed.get('keeper') or {{}}).get('thread_exited') is True
        and task.get('nonce')==closed.get('task_nonce') and task.get('child_exit_code')==task.get('bootstrap_exit_code')==1
        and task.get('job_active_after_stage')==0 and task.get('forced_remaining_cleanup') is False,
        'actual A05 uncreated Game and consumed Task closure required')
    require(removed.get('returncode')==0 and isinstance(removed.get('stdout'),str)
        and len(removed['stdout'])<=16384,'actual A05 unregister wrapper required')
    operation=json.loads(removed['stdout']);actual=operation.get('actual') or {{}}
    require(operation.get('machine_id')==MACHINE and operation.get('operation')=='unregister'
        and operation.get('task_name')=='XARG2ManagedOwner-'+closed['task_nonce']
        and actual.get('absent_after') is True and actual.get('instances')==0,
        'actual A05 consumed Task absent required')
    old={{closed['attempt_nonce'],closed['task_nonce']}}
    require(args.attempt_nonce not in old and args.task_nonce not in old,'A06 requires independent attempt/Task nonces')
    return value

'''.encode('utf-8')


def build_sources():
    values, quote, rows = actual_graph()
    names = list(quote['sources']['predecessors'])
    names += ['creator-tools/g2_saved_campaign/' + name for name in (
        'canonical_native_provider_chain_v1.py', 'mcp_owned_stdio_binding_v1.py', 'sdk_process_custody.py')]
    require(len(names) == len(set(names)) == 89, 'exact original89 source closure required')
    source = {name: values[(U5 / name).resolve()] for name in names}
    before_helper = source[HELPER]
    for name, data in tuple(source.items()):
        source[name] = data.replace(b'C23-A05', b'C23-A06')
    require(source[HELPER] == before_helper
            and (len(before_helper), prior.sha(before_helper)) ==
                (17637, 'bae312f0fb07d370252ecc5714666fe1790a4db33bca32599e0e9bcb56d64a8e'),
            'qualified strict Source26 helper must remain byte-identical')
    supervisor = source['root_native30_supervisor_c23.py']
    for before, after, count in (
        ("args.attempt=='a05'", "args.attempt=='a06'", 1),
        ("value.get('attempt_id')=='a05'", "value.get('attempt_id')=='a06'", 1),
        ('choices=("a05",)', 'choices=("a06",)', 1),
        ('"attempt_id":"a05"', '"attempt_id":"a06"', 2),
        ('_validate_a05_attempt(args, config)', '_validate_a06_attempt(args, config)', 1),
    ):
        supervisor = prior.swap(supervisor, before, after, count)
    require(supervisor.count(b'def main(args):') == 1, 'single original supervisor main required')
    source['root_native30_supervisor_c23.py'] = supervisor.replace(b'def main(args):', guard_source() + b'def main(args):')
    for name, data in source.items():
        compile(data, name, 'exec')
    return source, {'schema': 'xar.C23-A06-actual-A05-source-adapter/v1', 'machine_id': MACHINE,
        'source_count': 86, 'private_creator_count': 3, 'feeder': {},
        'actual_source_rows': [rows[(U5 / name).resolve()] for name in names],
        'verified_predecessor_pins': 119, 'strict_Source26_helper_byte_identical': True,
        'A05_failure_index': prior.ref(INDEX), 'new_runtime_root': str(U6),
        'actual_Game_or_RPC_credit': 0}


def state_guard():
    report = prior.state_guard()
    require((U5 / 'state').resolve(strict=True) == (prior.T0 / 'state').resolve(strict=True),
            'actual A05 state alias differs')
    report['future_alias'] = str(U6 / 'state')
    return report


def compose(plan, *, display_values, display_review, companion_values):
    """Reuse the original exact union algorithm with finite named A06 seams."""
    original = exact(prior.__file__, UNION_PIN).decode('utf-8')
    node = next(node for node in ast.parse(original).body
                if isinstance(node, ast.FunctionDef) and node.name == 'compose')
    source = ast.get_source_segment(original, node)
    source = source.replace('C23-A05', 'C23-A06').replace('C23-A04', 'C23-A05')
    source = source.replace("'a05'", "'a06'").replace('spec-supervisor-a05', 'spec-supervisor-a06')
    require(source.count('2026-10-20T06:30:00+00:00') == 1, 'one original review deadline seam required')
    source = source.replace('2026-10-20T06:30:00+00:00', '2026-10-20T10:30:00+00:00')
    before = "prior_failure_a04_unregistered=ref(O/'SUPERVISOR-A04-UNREGISTER.json'))"
    after = "prior_failure_a04_unregistered=ref(O/'SUPERVISOR-A04-UNREGISTER.json'),prior_failure_a05=ref(INDEX))"
    require(source.count(before) == 1, 'one explicit predecessor config seam required')
    source = source.replace(before, after, 1)
    scope = {**vars(prior), '__file__': __file__, 'T4': U5, 'T5': U6,
             'INDEX': INDEX, 'build_sources': build_sources, 'state_guard': state_guard}
    exec(compile(source, 'A06-original-union-compose-finite-RAM-projection', 'exec'), scope)
    outputs, quote = scope['compose'](plan, display_values=display_values,
        display_review=display_review, companion_values=companion_values)
    quote['original_union_source'] = prior.ref(prior.__file__)
    quote['actual_A05_failure_index'] = prior.ref(INDEX)
    quote['once_only_predecessor_Task_retained'] = True
    return outputs, quote


def compose_plan(plan_ref):
    """Root plan/ref interface, matching the original adopter's three tuple."""
    plan = prior.checked(plan_ref, 131072)
    require(prior.ref(__file__) == plan['union_producer'], 'actual reviewed A06 adapter required')
    path = Path(plan['display_producer']['path']).resolve()
    require(path == OWN / 'prepare_c23_a06_display_v1.py'
            and prior.ref(path) == plan['display_producer'], 'actual reviewed A06 display adapter required')
    display = prior._module(path, '_a06_exact_display_RAM')
    values, review, companion = display.compose(plan['display'])
    outputs, quote = compose(plan, display_values=values, display_review=review, companion_values=companion)
    quote['adopter'] = prior.ref(__file__)
    quote['input_plan'] = plan_ref
    quote['original_adopter_source'] = prior.ref(OWN / 'adopt_c23_a05_union_v1.py')
    return plan, outputs, quote


def adopt(plan_ref, quote_ref, card_ref):
    """Explicit Root-only call; project the already reviewed create-only writer.

    No CLI or automatic execution path exists. The original writer still
    requires the exact separately admitted A06 quote/card and absent roots.
    """
    path = OWN / 'adopt_c23_a05_union_v1.py'
    text = exact(path, ADOPTER_PIN).decode('utf-8')
    module = prior._module(path, '_a06_original_adopter_helpers_RAM')
    node = next(node for node in ast.parse(text).body
                if isinstance(node, ast.FunctionDef) and node.name == 'adopt')
    source = ast.get_source_segment(text, node).replace('A05', 'A06').replace('a05', 'a06')
    bridge = types.SimpleNamespace(MACHINE=MACHINE, T5=U6, T0=T0, O=O,
        checked=prior.checked, ref=prior.ref, raw=prior.raw, _module=prior._module)
    scope = {**vars(module), 'compose': compose_plan, 'union': bridge}
    exec(compile(source, 'A06-original-create-only-adopter-finite-projection', 'exec'), scope)
    return scope['adopt'](plan_ref, quote_ref, card_ref)


def cold_owner(inputs):
    """Reuse the qualified Source26 metadata builder after actual new frames."""
    text = exact(prior.__file__, UNION_PIN).decode('utf-8')
    node = next(node for node in ast.parse(text).body
                if isinstance(node, ast.FunctionDef) and node.name == 'cold_owner')
    source = ast.get_source_segment(text, node).replace('A05', 'A06').replace('a05', 'a06')
    scope = {**vars(prior), 'T5': U6}
    exec(compile(source, 'A06-existing-cold-owner-finite-projection', 'exec'), scope)
    return scope['cold_owner'](inputs)
