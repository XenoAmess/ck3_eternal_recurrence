"""Compose normal cold phases with original full_loop; no future cold pass claim."""
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
from types import ModuleType, SimpleNamespace

from prepare_c3_life_opening_classifier_v1 import load_functions, pinned


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime-root', type=Path, required=True)
    p.add_argument('--seed', type=Path, required=True)
    p.add_argument('--output-root', type=Path, required=True)
    args = p.parse_args(); root = args.runtime_root.resolve(strict=True)
    # Reproduce the historical phase-only qualification against its exact leaf;
    # the corrected current source uses qualify_saved61_call_order_v1.py.
    leaf, lp = pinned(root / 'root_p37c4_cold_resume.py',
        expected='82d40a057f5091094728c0ca1a77cdb990c8b649b6c2ce2199f8dde53d2b44d9')
    old_scope = {}
    exec(compile(leaf, str(root / 'root_p37c4_cold_resume.py'), 'exec'), old_scope)
    make_saved61_cold_queue_v1 = old_scope['make_saved61_cold_queue_v1']
    queue, qp = pinned(root / 'root_p37c3_sdk_queue.py', expected='18bfcbe93b17c625b80fa2701a29e44229f2a554b5daee75c32544c677e9c2b6', limit=1024**2)
    seed_raw, sp = pinned(args.seed, expected='13ace44626932920b7558ac7c74e5f648e697d291aa1d84a6671d166be4efdbc')
    seed = json.loads(seed_raw)
    save, save_pin = pinned(root / 'p37-responses/0197-1-result.json', expected='b59bbd30235fd0273cd11b0fbab05ceaa5d635f8e9cdfcfb3d66995b64778b71')
    if json.loads(save)['result']['structured_content']['checkpoint'] != seed['actual_saved_checkpoint']:
        raise AssertionError('Actual197 seed mismatch')
    freeze, fp = pinned(root / 'ROOT-FINAL-SDK-FREEZE-P37C.json', limit=1024**2)
    sys.path.insert(0, json.loads(freeze)['source_root'])
    args.output_root.mkdir(parents=True, exist_ok=False)
    (args.output_root / 'root_p37c4_cold_resume.py').write_bytes(leaf)
    classifier, cp = pinned(root / 'root_p37c3_native_deadline_classifier_v2.py',
        expected='d47350282ad422978bac99653aa5757a5d72d6af10fb690e615592a3ff825991')
    classifier_scope = {'Path': Path, 'ast': ast, 'json': json, 'hashlib': hashlib, 'copy': copy}
    load_functions(classifier, classifier_scope, str(root / 'root_p37c3_native_deadline_classifier_v2.py'))
    classifier_pin_path = args.output_root / 'SOFTWARE-FIXTURE-classifier-pin.json'
    classifier_pin_body = {'source': cp['path'], 'sha256': cp['sha256']}
    classifier_pin_path.write_text(json.dumps(classifier_pin_body), encoding='utf-8')
    cpr = {'path': str(classifier_pin_path.resolve()), 'bytes': classifier_pin_path.stat().st_size,
        'sha256': hashlib.sha256(classifier_pin_path.read_bytes()).hexdigest()}
    calls = []; writes = []
    launch = {'pid': 900001, 'creation_filetime': 900000000000000001,
        'pipe': r'\\.\pipe\xar-g2-robert30-v20261019-campaign01'}
    fake_body = {'snapshot_id': 'native:1', 'revision': 1, 'native_revision': 1,
        'date_raw': 53145792, 'paused': True, 'map_ready': True,
        'played_character': {'character_id': 31254, 'alive': True},
        'episode_run_id': seed['before']['episode_run_id'], 'one_life_terminal': False,
        'succession_lifecycle': seed['actual_saved_checkpoint']['succession_lifecycle'],
        'campaign_goal': seed['campaign_goal_anchor'], 'active_event': None, 'pending_character_interaction': None,
        'diagnostics': {'bridge_pid': launch['pid'], 'connection_generation': 1, 'pipe_name': launch['pipe'],
            'hello': {'pid': launch['pid'], 'connection_generation': 1, 'ck3_build_match': True,
                'game_adapter_id': 'ck3-1.20.0.4-msvc-x64', 'game_adapter_status': 'ready'}}}
    cap = {'episode_run_id': seed['before']['episode_run_id'], 'episode_character_id': 31254,
        'episode_identity_pending': False, 'one_life_terminal': False,
        'native_session_control': {'driver_state_restored': True, 'driver_state_restore_kind': 'cold_checkpoint',
            'episode_binding_state': 'active_resumed', 'driver_state_error': None, 'cold_candidate_rejection': None}}
    tree = ast.parse(queue)
    clean_class = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'CleanRobertMainMenuQueue')
    selected = [next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'frame')]
    for name in ('consume_sequence', 'persist_loop_state', 'generated', 'full_loop'):
        selected.append(next(n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name))
    selected.extend(copy.deepcopy(next(n for n in clean_class.body if isinstance(n, ast.FunctionDef) and n.name == name))
        for name in ('check_after', 'require_camera_pixel_admission'))
    class CurrentMap(ast.NodeTransformer):
        def visit_Constant(self, node):
            if node.value == 'ROOT-CAMPAIGN-MAP-ADMITTED.json': node.value = 'ROOT-CAMPAIGN-MAP-ADMITTED-C4.json'
            return node
    selected = [CurrentMap().visit(n) for n in selected]
    opening = {k: fake_body[k] for k in ('snapshot_id', 'revision', 'native_revision', 'date_raw', 'episode_run_id')}
    opening['actor_character_id'] = 31254
    map_receipt = {'status': 'GREEN', 'reviewer': '/root', 'game_pid': launch['pid'],
        'game_creation_filetime': launch['creation_filetime'], 'Game_map_visible': True,
        'decision_text_visible': True, 'recording_session_id': 'SOFTWARE-FIXTURE', 'actual_initial_frame': opening}
    def read(file, *a):
        if Path(file).name == 'ROOT-CAMPAIGN-MAP-ADMITTED-C4.json': return copy.deepcopy(map_receipt)
        return json.loads(Path(file).read_bytes())
    env = {'Path': Path, 'copy': copy, 'N': root, 'Q': args.output_root, 'INBOX': args.output_root / 'inbox',
        'OUTBOX': args.output_root / 'outbox', 'FRONTEND': ('a', 'b', 'c'),
        'SEMANTIC': 'ck3_take_semantic_snapshot_private_v1', 'CAPABILITIES': 'ck3_capabilities',
        'METRICS': 'root_current_runtime_metrics', 'AUTO': 'ck3_auto_turn', 'SAVE': 'ck3_save_checkpoint',
        'read': read, 'now': lambda: datetime.now(timezone.utc),
        'atomic': lambda file, value, **kw: writes.append((str(file), copy.deepcopy(value))),
        'pending_request_paths': lambda *a, **kw: [],
        'load_cold_result_classifier': lambda: classifier_scope['classify_auto_result_credit_v1']}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(root / 'root_p37c3_sdk_queue.py'), 'exec'), env)
    class StopAtNewAUTO(BaseException):
        pass
    class Base(SimpleNamespace):
        consume_sequence = env['consume_sequence']; persist_loop_state = env['persist_loop_state']
        generated = env['generated']; full_loop = env['full_loop']
        check_after = env['check_after']; require_camera_pixel_admission = env['require_camera_pixel_admission']
        def check_before(self, *a): pass
        def guard(self, **kw): pass
        async def call(self, session, request, path):
            calls.append(copy.deepcopy(request))
            if request['tool'] != env['AUTO']: raise AssertionError('Old MET/AUTO unexpectedly supplied')
            raise StopAtNewAUTO()
    Cold = make_saved61_cold_queue_v1(Base, env, admission_path=Path('NOT-ACTUAL-ADMISSION'))
    def make():
        q = Cold.__new__(Cold)
        q.__dict__.update(launch=copy.deepcopy(launch), next_sequence=198,
            initial_frame=None, initial_save=None, semantic=None, zero_day_preparation=False,
            expected_lifecycle_binding=seed['actual_saved_checkpoint']['succession_lifecycle'],
            _saved61_cold={'phase': 'semantic', 'seed': copy.deepcopy(seed),
                'governance': {'state': {'council_pending': None, 'construction_actions': {}, 'crown_pending': None}, 'pending_focus': None},
                'checkpoint': seed['actual_saved_checkpoint'], 'admission': {'classifier_pin': cpr}},
            job={'session_id': 'SOFTWARE-FIXTURE'}, halted=None, current_attempt=None, held_control=None, loop_count=0)
        return q
    score = ModuleType('root_score_month_samples')
    score.END_RAW = 53407128; score.anchor_path = lambda *a: None; score.observe_semantic = lambda *a: None
    prior = sys.modules.get('root_score_month_samples'); sys.modules['root_score_month_samples'] = score
    try:
        q = make(); q.check_before(env['SEMANTIC'], {})
        q.consume_sequence({'sequence': 198, 'tool': env['SEMANTIC']}); q.check_after(env['SEMANTIC'], {}, copy.deepcopy(fake_body))
        q.check_before(env['CAPABILITIES'], {})
        q.consume_sequence({'sequence': 199, 'tool': env['CAPABILITIES']}); q.check_after(env['CAPABILITIES'], {}, cap)
        if q.initial_frame != opening or q.full_loop_state['before'] != opening or q.full_loop_state['start_date_raw'] != 53144328:
            raise AssertionError('Session opening and T0 anchor mixed')
        if q.full_loop_state['counts'] != seed['counts'] or q.full_loop_state['completed_cycles'] != 74:
            raise AssertionError('Historical credit changed')
        if Cold.generated is not Base.generated or Cold.full_loop is not Base.full_loop:
            raise AssertionError('Original generated/full_loop not inherited')
        q.require_camera_pixel_admission()
        try:
            asyncio.run(q.full_loop(object(), {'sequence': 200, 'command': 'full_loop', 'arguments': {'max_turns': 1}},
                env['INBOX'] / '0200-1-result.json'))
        except StopAtNewAUTO:
            pass
        if len(calls) != 1 or calls[0]['sequence'] != 201 or q.full_loop_state['pending_cycle']['global_turn'] != 75:
            raise AssertionError('Original loop did not start exactly one new AUTO75')
        negatives = []
        for name in ('wrong_date', 'wrong_episode', 'hot_CAP'):
            bad = copy.deepcopy(fake_body); instance = make()
            try:
                if name == 'wrong_date': bad['date_raw'] += 24
                elif name == 'wrong_episode': bad['episode_run_id'] = 'foreign'
                instance.next_sequence = 199
                instance.check_after(env['SEMANTIC'], {}, bad)
                if name == 'hot_CAP':
                    badcap = copy.deepcopy(cap); badcap['native_session_control']['driver_state_restore_kind'] = 'same_pid_hot'
                    instance.next_sequence = 200; instance.check_after(env['CAPABILITIES'], {}, badcap)
            except ValueError:
                negatives.append(name)
            else: raise AssertionError('Wrong cold binding accepted: ' + name)
    finally:
        if prior is None: sys.modules.pop('root_score_month_samples', None)
        else: sys.modules['root_score_month_samples'] = prior
    result = {'schema': 'xar.saved61-cold-phase-software-qualification/v1',
        'machine_id': 'xenoamess-full-tower-eb9d2c1186', 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'sources': [lp, qp, sp, save_pin, fp, cp], 'fixture_scope': 'Explicit synthetic future Game SEM/CAP and map. Actual preflight/new Game/Native26/recording not qualified.',
        'original_full_loop_generated_inherited': True, 'original_consume_persist_camera_contract_used': True,
        'cold_native1_rebinds_old_native98': True, 'T0_start_date_unchanged': True,
        'historical_cycles74_counts_unchanged': True, 'next_original_loop_request': calls[0],
        'negative_cases_rejected': negatives, 'new_Game_Native_MCP_calls': 0, 'runtime_mutations': 0,
        'actual_future_preflight_or_cold_pass_claimed': False}
    (args.output_root / 'QUALIFICATION.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'leaf': lp, 'qualification': str(args.output_root / 'QUALIFICATION.json')}))


if __name__ == '__main__': main()
