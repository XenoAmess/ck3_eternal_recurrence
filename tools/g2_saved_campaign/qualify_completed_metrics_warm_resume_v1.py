"""Bounded offline composition of exact original full_loop and MET110 adapter."""
from __future__ import annotations
import argparse
import ast
import asyncio
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
from unittest import mock

from completed_metrics_warm_resume_v1 import (bind_verified_absence_lifecycle_v1, checked,
                                            make_met_resume_queue_v1, validate_inputs)
from pending_request_paths import pending_request_paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--admission', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--temporary-root', type=Path, required=True)
    args = parser.parse_args()
    admission = json.loads(args.admission.read_bytes())
    request, state, governance, metrics, ack = validate_inputs(admission)
    actual_root = args.admission.resolve().parent
    freeze = json.loads((actual_root / 'ROOT-FINAL-SDK-FREEZE-P37.json').read_bytes())
    sys.path.insert(0, freeze['source_root'])
    from xar_autoplayer.bridge.succession_transition_contract import bind_succession_lifecycle_from_environment_v1
    manifest = json.loads((actual_root / 'state/profile/xar-autoplayer-environment.json').read_bytes())
    absence = json.loads((actual_root / 'ROOT-CLEAN-CAMPAIGN-MOD-ABSENCE-ACTUAL.json').read_bytes())
    launch = {'pid': admission['Game_pid'], 'creation_filetime': admission['Game_creation_filetime']}
    actual_binding = bind_verified_absence_lifecycle_v1(manifest, absence, launch,
        bind_succession_lifecycle_from_environment_v1, machine_id=admission['machine_id'])
    if actual_binding != state['actual_saved_checkpoint']['succession_lifecycle']:
        raise AssertionError('actual retained vanilla binder differs from original checkpoint lifecycle')
    source = admission['original_source']
    raw = Path(source['path']).read_bytes()
    if len(raw) > 1024**2 or hashlib.sha256(raw).hexdigest() != source['sha256']:
        raise ValueError('exact bounded actual queue source required')
    tree = ast.parse(raw.decode('utf-8-sig'))
    loops = [node for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef)
        and node.name == 'full_loop' and 'One batch <=30' in (ast.get_docstring(node) or '')]
    generators = [node for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef)
                  and node.name == 'generated']
    if len(loops) != 1 or len(generators) != 1:
        raise ValueError('one original full_loop and generated method required')
    if 'full_loop' in make_met_resume_queue_v1.__code__.co_names:
        raise AssertionError('adapter must not copy the settlement method')
    calls, guards, saved_states, inherited_postchecks = [], [], [], []
    with tempfile.TemporaryDirectory(prefix='completed-met-', dir=args.temporary_root) as temporary:
        root = Path(temporary)
        for relative in ('p37-queue', 'p37-requests', 'p37-responses', 'campaign-score/months'):
            (root / relative).mkdir(parents=True, exist_ok=True)
        (root / 'campaign-score/months/month-000.json').write_bytes(b'{}')
        def atomic(path, value, **kwargs):
            with Path(path).open('xb') as stream:
                stream.write(json.dumps(value, ensure_ascii=False).encode())
        env = {'N': root, 'Q': root / 'p37-queue', 'INBOX': root / 'p37-requests',
            'OUTBOX': root / 'p37-responses', 'METRICS': 'root_current_runtime_metrics',
            'AUTO': 'ck3_auto_turn', 'SEMANTIC': 'ck3_take_semantic_snapshot_private_v1',
            'CAPABILITIES': 'ck3_get_capabilities', 'SAVE': 'ck3_save_checkpoint',
            'atomic': atomic, 'now': lambda: datetime.now(timezone.utc), 'copy': copy,
            'frame': lambda body, **kwargs: {key: body[key] for key in
                ('snapshot_id', 'revision', 'native_revision', 'date_raw', 'episode_run_id')}
                | {'actor_character_id': (body.get('played_character') or {}).get('character_id', body.get('actor_character_id'))},
            'pending_request_paths': pending_request_paths,
            'pending_marker_from_credit': lambda *a, **kwargs: None,
            'checkpoint_after_settled_cycle': lambda *a: False,
            'checkpoint_context_from_auto': lambda *a: None,
            'load_cold_result_classifier': lambda: (lambda *a, **kwargs: None)}
        exec(compile(ast.Module(body=loops + generators, type_ignores=[]), str(source['path']), 'exec'), env)
        class Base:
            full_loop = env['full_loop']
            generated = env['generated']
            def guard(self, **kwargs):
                guards.append(kwargs)
            def require_camera_pixel_admission(self):
                guards.append('original_camera_gate')
            def consume_sequence(self, command):
                if command['sequence'] != self.next_sequence:
                    raise AssertionError('sequence mismatch')
                self.next_sequence += 1
                return command['sequence']
            def persist_loop_state(self):
                saved_states.append(copy.deepcopy(self.full_loop_state))
            def check_before(self, *a):
                return None
            def check_after(self, tool, arguments, body):
                inherited_postchecks.append(tool)
                env['frame'](body)
            async def call(self, session, command, path):
                self.check_before(command['tool'], command['arguments'])
                self.consume_sequence(command)
                calls.append(command['tool'])
                if command['tool'] == env['AUTO']:
                    self.last_auto_observation = {'primitive_accepted': True}
                    return {'selected_step': 'synthetic-next-query', 'plan': {'phase': 'synthetic'}}, path
                return copy.deepcopy(metrics), path
        Composed = make_met_resume_queue_v1(Base, env, admission_path=args.admission)
        if Composed.full_loop is not Base.full_loop:
            raise AssertionError('full_loop was replaced')
        queue = object.__new__(Composed)
        queue._completed_met_resume = {'admission': admission, 'request': request,
            'state': copy.deepcopy(state), 'governance': governance, 'body': metrics,
            'ack': ack, 'phase': 'semantic_required'}
        queue.checkpoint_bootstrap_verified = False
        queue.launch = {'pid': admission['Game_pid']}
        queue.next_sequence = 113  # Fresh SEM111 and CAP112 have their own new IDs.
        queue.semantic = None
        queue.expected_lifecycle_binding = {}
        queue.loop_count = 0
        queue.held_control = None
        queue.halted = None
        queue.current_attempt = None
        queue.initial_frame = checked(admission['original_map_admission'])['actual_initial_frame']
        t0 = copy.deepcopy(queue.initial_frame)
        negatives = []
        try:
            queue.check_before(env['AUTO'], {})
        except ValueError:
            negatives.append('AUTO_before_fresh_SEM_CAP_rejected')
        else:
            raise AssertionError('AUTO before fresh observations admitted')
        semantic = copy.deepcopy(metrics)
        semantic.update(native_revision=metrics['native_revision'] + 1,
            campaign_goal=copy.deepcopy(state['campaign_goal_anchor']),
            diagnostics={'bridge_pid': admission['Game_pid'], 'hello': {'pid': admission['Game_pid']}},
            played_character={'character_id': metrics['actor_character_id'], 'alive': True})
        wrong = copy.deepcopy(semantic)
        wrong['date_raw'] += 24
        try:
            queue.check_after(env['SEMANTIC'], {}, wrong)
        except ValueError:
            negatives.append('changed_date_fresh_SEM_rejected')
        else:
            raise AssertionError('wrong fresh frame admitted')
        queue.check_after(env['SEMANTIC'], {}, semantic)
        cap = {'episode_run_id': metrics['episode_run_id'], 'native_session_control': {
            'driver_state_restored': True, 'driver_state_restore_kind': 'same_pid_hot',
            'episode_binding_state': 'active_resumed', 'driver_state_error': None,
            'cold_candidate_rejection': None}}
        wrong = copy.deepcopy(cap)
        wrong['native_session_control']['driver_state_restore_kind'] = 'cold'
        try:
            queue.check_after(env['CAPABILITIES'], {}, wrong)
        except ValueError:
            negatives.append('cold_restore_rejected')
        else:
            raise AssertionError('cold restore admitted')
        queue.check_after(env['CAPABILITIES'], {}, cap)
        if queue.full_loop_state != state or queue.initial_frame != t0:
            raise AssertionError('retained47state/pending48/T0 changed at restore')
        try:
            asyncio.run(queue.generated(None, env['AUTO']))
        except ValueError:
            negatives.append('AUTO_before_original_MET110_settled_rejected')
        else:
            raise AssertionError('pending48 skipped its original MET')
        samples = types.ModuleType('root_score_month_samples')
        samples.END_RAW = 53407128
        samples.anchor_path = None
        samples.persist = lambda *a, **kwargs: None
        with mock.patch.dict(sys.modules, {samples.__name__: samples}):
            first = asyncio.run(queue.full_loop(None, {'sequence': 113, 'command': 'full_loop',
                'arguments': {'max_turns': 1}}, Path('0113-1-result.json')))
            if calls or first['cumulative_cycles'] != 48 or first['actual_turns'] != 1:
                raise AssertionError('original MET settlement issued a new RPC or wrong credit')
            if queue.full_loop_state['before_metrics_response'] != request['original_completed_MET']['path']:
                raise AssertionError('original MET path lost')
            first_counts = copy.deepcopy(queue.full_loop_state['counts'])
            second = asyncio.run(queue.full_loop(None, {'sequence': 114, 'command': 'full_loop',
                'arguments': {'max_turns': 1}}, Path('0114-1-result.json')))
        if calls != [env['AUTO'], env['METRICS']] or second['cumulative_cycles'] != 49:
            raise AssertionError('next fresh AUTO did not use original generated method exactly once')
        if queue.initial_frame != t0 or queue.full_loop_state['pending_cycle'] is not None:
            raise AssertionError('T0 or original settlement algorithm changed')
        for key, value in state['counts'].items():
            expected = value + (1 if key == 'primitive_accepted_turns' else 0)
            if first_counts[key] != expected:
                raise AssertionError('count changed outside original pending48 observation: ' + key)
    result = {'schema': 'xar.completed-metrics-resume-software-qualification/v1',
        'machine_id': admission['machine_id'], 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'admission': {'path': str(args.admission), 'sha256': hashlib.sha256(args.admission.read_bytes()).hexdigest()},
        'source': source, 'exact_original_full_loop_AST_used': True,
        'old_closed_status': 'honest Queue1/App0, normal=false',
        'restore47_and_pending48_unchanged': True, 'T0_map_anchor_retained': True,
        'actual_vanilla_environment_binder_verified': True, 'manifest_mutated': False,
        'actual_lifecycle_binding': actual_binding,
        'original_MET110_consumed_with_new_RPC_calls': 0,
        'first_settled_cycle': first['cumulative_cycles'], 'next_settled_cycle': second['cumulative_cycles'],
        'next_new_fake_RPC_tools': calls, 'inherited_MET_postcheck_retained': True,
        'original_camera_gate_calls': guards.count('original_camera_gate'),
        'negative_cases': negatives, 'new_actual_MCP_Native_Game_calls': 0,
        'runtime_files_mutated': 0, 'live_qualified': False,
        'limits': ['Constructor recording/process/identity guards need actual runtime readback.',
            'Fresh SEM/CAP in this software composition are explicit fixtures.',
            'Checkpoint/month helper side effects are bounded fixture callbacks; settlement is original full_loop AST.']}
    data = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode()
    with args.receipt.open('xb') as stream:
        stream.write(data)
    print(json.dumps({'receipt': str(args.receipt), 'bytes': len(data),
                      'sha256': hashlib.sha256(data).hexdigest(), 'status': 'PASS'}))


if __name__ == '__main__':
    main()
