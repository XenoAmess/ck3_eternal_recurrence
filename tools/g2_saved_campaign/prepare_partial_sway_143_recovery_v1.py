"""Create-only dynamic control candidate and exact-input software qualification."""
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

import partial_sway_143_recovery_v1 as leaf


def pin(path):
    path = Path(path).resolve(strict=True)
    with path.open('rb') as stream: raw = stream.read(1024**2 + 1)
    if len(raw) > 1024**2: raise ValueError('bounded input only')
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def transformed(raw, admission_pin):
    tree = ast.parse(raw.decode('utf-8-sig'))
    function = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'recover')
    lines = raw.decode('utf-8-sig').splitlines(keepends=True)
    branch = ("    if request.get('arguments') == {'recovery_kind': 'partial_sway_readonly_143'}:\n"
              "        from root_p37c3_partial_sway_recap import recover as recover_partial_sway\n"
              f"        return await recover_partial_sway(queue, session, request, path, env, admission_pin={admission_pin!r}, birth_reader=birth_reader)\n")
    lines[function.lineno:function.lineno] = [branch]
    changed = ''.join(lines).encode()
    after = ast.parse(changed.decode('utf-8-sig'))
    actual = next(n for n in after.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'recover')
    if not isinstance(actual.body[0], ast.If): raise AssertionError('one exact leading dispatch branch required')
    actual.body = actual.body[1:]
    if ast.dump(tree) != ast.dump(after): raise AssertionError('an existing recovery contract changed')
    return changed


async def exercise(patched, admission_pin, admission, temporary, *, negative=None):
    meta, state, row = leaf.validate_admission(admission)
    root = Path(temporary)
    for sub in ('q', 'in', 'out'): (root / sub).mkdir()
    calls = []
    preserved = copy.deepcopy(state)
    original = root / 'out/0143-1-result.json'
    def read(path, limit=1024**2):
        if path == root / 'q/ROOT-CUMULATIVE-LOOP-STATE.json': return copy.deepcopy(preserved)
        if path == original: return copy.deepcopy(row)
        return json.loads(Path(path).read_bytes())
    def atomic(path, value, **kwargs):
        with Path(path).open('xb') as stream: stream.write(json.dumps(value, ensure_ascii=False).encode())
    env = {'Q': root / 'q', 'INBOX': root / 'in', 'OUTBOX': root / 'out',
           'SEMANTIC': 'ck3_take_semantic_snapshot_private_v1', 'REPLY_RESERVE': 1024**2,
           'read': read, 'atomic': atomic, 'now': lambda: datetime.now(timezone.utc),
           'decoded': lambda value: value['result']['structured_content']}
    launch = json.loads((Path(admission['runtime']) / 'ROOT-ACTUAL-GAME-LAUNCH.json').read_bytes())
    semantic = json.loads((Path(admission['runtime']) / 'p37-responses/0141-1-result.json').read_bytes())['result']['structured_content']
    semantic['native_revision'] = 58; semantic['snapshot_id'] = 'native:58'
    semantic['revision'] = 22
    if negative == 'changed_fresh_date': semantic['date_raw'] += 24
    if negative == 'changed_connection': semantic['diagnostics']['connection_generation'] = 99
    class Queue:
        def __init__(self):
            self.next_sequence = 144
            self.launch = launch
            self.job = {'game_creation_filetime': 134368503807325674}
            self.full_loop_state = copy.deepcopy(state)
            self.expected_lifecycle_binding = semantic['succession_lifecycle']
            self.halted = {'request': row['request'], 'row': copy.deepcopy(row), 'response': str(original)}
            self.current_attempt = self.held_control = None
            self.semantic = None
            if negative == 'changed_complete_count': self.full_loop_state['completed_cycles'] += 1
            if negative == 'unknown_original': self.halted['row']['client_error'] = 'unknown'
        def guard(self): pass
        def consume_sequence(self, request):
            if request['sequence'] != self.next_sequence: raise AssertionError('sequence differs')
            self.next_sequence += 1
            return request['sequence']
        def call_budget(self, tool): return 300
        def persist_loop_state(self): pass
    class Session:
        async def call_tool(self, tool, arguments, **kwargs):
            calls.append(tool)
            if tool != env['SEMANTIC'] or arguments != {}: raise AssertionError('non-readonly call')
            return types.SimpleNamespace(model_dump=lambda **kwargs: {'is_error': False, 'structured_content': semantic})
    queue = Queue()
    namespace = {'__file__': str(Path(admission['runtime']) / 'root_p37_known_pause_recovery_control.py')}
    exec(compile(patched, namespace['__file__'], 'exec'), namespace)
    child = types.ModuleType('root_p37c3_partial_sway_recap'); child.recover = leaf.recover
    request = {'sequence': 144, 'command': 'recover_partial_life_advance', 'arguments': {'recovery_kind': leaf.KIND}}
    with mock.patch.dict(sys.modules, {child.__name__: child}):
        try:
            result = await namespace['recover'](queue, Session(), request, root / 'in/0144-1-result.json', env,
                birth_reader=lambda pid: 0 if negative == 'changed_birth' else 134368503807325674)
        except ValueError as error:
            if negative is None: raise
            if queue.halted is None or queue.full_loop_state != state and negative != 'changed_complete_count':
                raise AssertionError('rejected partial recap cleared the original or changed state')
            return {'case': negative, 'rejected': True, 'fake_readonly_calls': len(calls)}
    if negative is not None: raise AssertionError('negative input admitted: ' + negative)
    if (calls != [env['SEMANTIC']] or queue.next_sequence != 146 or queue.halted is not None
            or queue.full_loop_state['completed_cycles'] != 57
            or queue.full_loop_state['counts'] != state['counts']
            or queue.full_loop_state['pending_cycle'] is not None
            or result['ordinary_cycle_credit'] != 0 or result['game_day_credit'] != 0):
        raise AssertionError('partial transition granted full credit or replayed action')
    return {'case': 'actual143_source_fake_one_fresh_SEM', 'status': 'PASS', 'fake_readonly_calls': len(calls),
        'AUTO_or_action_calls': 0, 'complete_cycles': 57, 'next_sequence': 146,
        'counts_unchanged': True, 'ordinary_cycle_credit': 0, 'game_day_credit': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root', type=Path, required=True)
    parser.add_argument('--review-meta', type=Path, required=True)
    parser.add_argument('--state-freeze', type=Path, required=True)
    parser.add_argument('--output-root', type=Path, required=True)
    parser.add_argument('--temporary-root', type=Path, required=True)
    args = parser.parse_args()
    root = args.runtime_root.resolve(strict=True)
    frozen = json.loads(args.state_freeze.read_bytes())
    state_ref = next(item for item in frozen['source_entries'] if Path(item['source_path']).name == 'ROOT-CUMULATIVE-LOOP-STATE.json')
    admission = {'schema': 'xar.partial-sway143-recap-admission/v1',
        'machine_id': frozen['machine_id'], 'runtime': str(root), 'source_review': pin(args.review_meta),
        'retained_state': {'path': state_ref['frozen_path'], 'bytes': state_ref['bytes'], 'sha256': state_ref['sha256']}}
    leaf.validate_admission(admission)
    args.output_root.mkdir(parents=True, exist_ok=False)
    admission_raw = (json.dumps(admission, ensure_ascii=False, indent=2) + '\n').encode()
    (args.output_root / 'ROOT-P37C3-PARTIAL143-ADMISSION.json').write_bytes(admission_raw)
    final_admission = {'path': str(root / 'ROOT-P37C3-PARTIAL143-ADMISSION.json'),
        'bytes': len(admission_raw), 'sha256': hashlib.sha256(admission_raw).hexdigest()}
    original = root / 'root_p37_known_pause_recovery_control.py'
    original_pin = pin(original)
    patched = transformed(original.read_bytes(), final_admission)
    helper = Path(leaf.__file__).resolve()
    (args.output_root / original.name).write_bytes(patched)
    (args.output_root / 'root_p37c3_partial_sway_recap.py').write_bytes(helper.read_bytes())
    # The software run uses the identical admission bytes under its review path;
    # the final actual dynamic control resolves the fixed runtime path above.
    test_pin = {**final_admission, 'path': str(args.output_root / 'ROOT-P37C3-PARTIAL143-ADMISSION.json')}
    test_patched = transformed(original.read_bytes(), test_pin)
    freeze = json.loads((root / 'ROOT-FINAL-SDK-FREEZE-P37C.json').read_bytes())
    sys.path[:0] = [str(root), freeze['source_root']]
    cases = []
    for negative in (None, 'changed_birth', 'changed_complete_count', 'unknown_original', 'changed_fresh_date', 'changed_connection'):
        with tempfile.TemporaryDirectory(prefix='partial143-', dir=args.temporary_root) as temporary:
            cases.append(asyncio.run(exercise(test_patched, test_pin, admission, temporary, negative=negative)))
    result = {'schema': 'xar.partial-sway143-recap-software-qualification/v1', 'machine_id': admission['machine_id'],
        'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'old_dynamic_source': original_pin,
        'sources': [pin(args.review_meta), pin(args.state_freeze), pin(helper)],
        'candidate_files': [pin(args.output_root / name) for name in (original.name, 'root_p37c3_partial_sway_recap.py', 'ROOT-P37C3-PARTIAL143-ADMISSION.json')],
        'old_recovery_function_AST_unchanged_except_one_leading_specific_dispatch': True,
        'actual143_source_and_failed57_state_bound': True, 'cases': cases,
        'new_actual_Game_MCP_Native_calls': 0, 'runtime_files_mutated': 0,
        'live_adopted': False, 'fresh_SEM_in_qualification': 'explicit fake session; actual one fresh SEM remains required',
        'next_control': {'sequence': 144, 'command': 'recover_partial_life_advance', 'arguments': {'recovery_kind': leaf.KIND}}}
    (args.output_root / 'QUALIFICATION.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'review': str(args.output_root), 'files': result['candidate_files'], 'status': 'PASS'}))


if __name__ == '__main__': main()
