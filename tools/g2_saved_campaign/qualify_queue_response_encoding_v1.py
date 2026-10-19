"""Qualify single JSON encoding against one exact, unimported queue source.

Only the extracted local writer, decoder, and MCP call method run, with a fake
session and finite temporary receipts. No owner module, Game, Driver, or MCP
transport is loaded. The source candidate grants no runtime admission.
"""
from __future__ import annotations

import argparse
import ast
import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import sys
import tempfile
import time
import types
from unittest import mock
import uuid

from owner_response_json_once_v1 import prepare_success_response_row_v1
from owner_response_source_transform_v1 import transform_owner_source_v1

LIMIT = 1024 * 1024


def selected(raw):
    tree = ast.parse(raw.decode('utf-8-sig'))
    functions = [node for node in ast.walk(tree)
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    calls = [node for node in functions if node.name == 'call' and any(
        isinstance(item, ast.Name) and item.id == 'dumped' for item in ast.walk(node))]
    if len(calls) != 1:
        raise ValueError('one actual full response call required')
    local = [node for node in tree.body if isinstance(node, ast.FunctionDef)
             and node.name in {'atomic', 'atomic_payload_v1', 'decoded'}]
    if {node.name for node in local} not in (
            {'atomic', 'decoded'}, {'atomic', 'atomic_payload_v1', 'decoded'}):
        raise ValueError('actual writer and decoder definitions required')
    return local + calls


def preserved_ast(before, after):
    """Every function outside the reviewed writer/call transformation is exact."""
    def untouched(raw):
        output = []
        for node in ast.walk(ast.parse(raw.decode('utf-8-sig'))):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name in {'atomic', 'atomic_payload_v1'}:
                continue
            if node.name == 'call' and any(isinstance(item, ast.Name) and item.id == 'dumped'
                                           for item in ast.walk(node)):
                continue
            output.append(ast.dump(node))
        return output
    if untouched(before) != untouched(after):
        raise AssertionError('an unrelated actual queue function changed')
    old = next(node for node in selected(before) if node.name == 'call')
    new = next(node for node in selected(after) if node.name == 'call')
    def tail(node):
        starts = [i for i, statement in enumerate(node.body)
                  if i > 1 and isinstance(statement, ast.Assign) and any(
                      isinstance(target, ast.Attribute) and target.attr == 'current_attempt'
                      for target in statement.targets)]
        if len(starts) != 1:
            raise ValueError('one actual post-result tail required')
        return [ast.dump(statement) for statement in node.body[starts[0]:]]
    if tail(old) != tail(new):
        raise AssertionError('actual relay, decoder, postverification or credits changed')


async def exercise(raw, root, *, rpc_error=False, reject_after=False, existing=False):
    for directory in (root, root / 'out', root / 'queue', root / 'p37-display-responses'):
        directory.mkdir(exist_ok=True)
    events, calls = [], []
    ticks = iter(100 + index * .25 for index in range(100))
    complete = {'structured_content': {'status': 'executed', 'selected_step': 'fixture',
        'result': {'status': 'completed', 'accepted': True, 'postcondition_verified': True,
            'date_raw': 53144328, 'query_sequence': 2**63 + 8, 'optional': None,
            'all_fields_retained': ['完整原生字段\n\\\"🪶', -0.0, False, -(2**63)]}},
        'content': [{'type': 'text', 'text': '原始响应'}], 'is_error': False}
    scope = {'json': json, 'os': __import__('os'), 'uuid': uuid,
        'time': types.SimpleNamespace(monotonic=lambda: next(ticks), sleep=lambda _: None),
        'REPLY_RESERVE': LIMIT, 'N': root, 'Q': root / 'queue', 'OUTBOX': root / 'out',
        'AUTO': 'ck3_auto_turn', 'INITIAL_CAMERA': 'initial-camera',
        'now': lambda: datetime(2020, 1, 1, tzinfo=timezone.utc),
        'preserve_first_exception': lambda *args, **kwargs: events.append('preserve_exception'),
        'display_projection': lambda row, body: {'status': body.get('status')},
        '_owner_response_success_row_once_v1': prepare_success_response_row_v1,
        'print': lambda *args, **kwargs: None}
    nodes = selected(raw)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<exact-queue-excerpt>', 'exec'), scope)
    call = next(node for node in nodes if node.name == 'call')
    relay_imports = [node for node in ast.walk(call) if isinstance(node, ast.ImportFrom)
                     and any(name.name == 'relay_compact' for name in node.names)]
    if len(relay_imports) != 1:
        raise ValueError('one actual local relay import required')
    relay = types.ModuleType(relay_imports[0].module)
    relay.relay_compact = lambda *args: events.append('relay')
    relay.error_projection = lambda row: {'error': True}

    class Session:
        async def call_tool(self, tool, arguments, *, read_timeout_seconds):
            calls.append((tool, arguments, read_timeout_seconds))
            events.append('call_tool')
            if rpc_error:
                raise RuntimeError('synthetic unknown outcome')
            return types.SimpleNamespace(model_dump=lambda **kwargs: complete)

    class Owner:
        last_auto_observation = {'synthetic_only': True}
        def check_before(self, *args):
            events.append('check_before')
        def call_budget(self, tool):
            return 300
        def consume_sequence(self, request):
            events.append('consume_sequence')
            return request['sequence']
        def check_after(self, *args):
            events.append('check_after')
            if reject_after:
                raise ValueError('synthetic postverification refusal')

    response = root / 'out/0007-1-result.json'
    if existing:
        response.write_bytes(b'protected original')
    request = {'sequence': 7, 'tool': 'ck3_auto_turn', 'arguments': {}, 'source': 'qualification'}
    error = None
    with mock.patch.dict(sys.modules, {relay.__name__: relay}):
        try:
            await scope['call'](Owner(), Session(), request, Path('synthetic-request.json'))
        except Exception as caught:
            error = (type(caught).__name__, str(caught))
    return {'events': events, 'calls': calls, 'error': error,
        'response': response.read_bytes() if response.exists() else None,
        'credit': (root / 'queue/0007-ordinary-result-credit.json').exists()}


def qualify_calls(before, after, temporary_root):
    reports = []
    for name, kwargs in [('success', {}), ('unknown', {'rpc_error': True}),
                         ('postverification_refusal', {'reject_after': True}),
                         ('existing_original', {'existing': True})]:
        old_root, new_root = temporary_root / (name + '-old'), temporary_root / (name + '-new')
        old = asyncio.run(exercise(before, old_root, **kwargs))
        new = asyncio.run(exercise(after, new_root, **kwargs))
        if old != new:
            raise AssertionError('actual queue excerpt behavior differs: ' + name)
        expected_calls = 0 if name == 'existing_original' else 1
        if len(new['calls']) != expected_calls or new['credit'] != (name == 'success'):
            raise AssertionError('original unknown/credit guard differs: ' + name)
        if name == 'unknown' and json.loads(new['response'])['replay_allowed'] is not False:
            raise AssertionError('unknown outcome acquired replay permission')
        reports.append({'case': name, 'response_bytes_identical': True,
            'response_bytes': len(new['response'] or b''), 'same_check_and_relay_order': True,
            'fake_RPC_calls_before_and_after': expected_calls, 'ordinary_credit': new['credit'],
            'error_type': new['error'][0] if new['error'] else None})
    return reports


def benchmark(size):
    # Repeated native-shaped rows are deliberately synthetic, never a live body.
    row = {'entity_id': 2**63 + 5, 'generation': 0, 'date_raw': 53144328,
           'name': 'synthetic 王国', 'available': True, 'optional': None,
           'details': [1, 2, 3, '完整字段', -0.0]}
    unit = len(json.dumps(row, ensure_ascii=False, separators=(',', ':')).encode()) + 1
    result = {'structured_content': {'status': 'executed', 'synthetic_rows': [row] * (size // unit)},
              'is_error': False}
    arguments = {'started_at_utc': 'a', 'ended_at_utc': 'b', 'elapsed_seconds': .125,
                 'request': {'sequence': 1}, 'result': result}
    def old():
        encoded = json.dumps(result, ensure_ascii=False, separators=(',', ':')).encode()
        full = {'started_at_utc': 'a', 'ended_at_utc': 'b', 'elapsed_seconds': .125,
                'request': {'sequence': 1}, 'result': result,
                'mcp_result_projection_json_utf8_bytes': len(encoded)}
        return json.dumps(full, ensure_ascii=False, separators=(',', ':')).encode()
    def new():
        return prepare_success_response_row_v1(**arguments)[1]
    baseline, candidate = old(), new()
    if baseline != candidate:
        raise AssertionError('synthetic full response bytes differ')
    del baseline, candidate
    timings = {'before': [], 'after': []}
    for index in range(5):
        order = [('before', old), ('after', new)]
        if index % 2:
            order.reverse()
        for key, function in order:
            start = time.perf_counter()
            payload = function()
            timings[key].append(time.perf_counter() - start)
            del payload
    return {'synthetic_only': True, 'approximate_result_bytes': size,
        'full_response_bytes': len(old()), 'full_result_traversals_before': 2,
        'full_result_traversals_after': 1, 'full_response_bytes_identical': True,
        'seconds': timings, 'median_seconds': {key: statistics.median(value)
                                               for key, value in timings.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--temporary-root', required=True, type=Path)
    parser.add_argument('--machine-id', required=True)
    parser.add_argument('--receipt', required=True, type=Path)
    args = parser.parse_args()
    if args.source.stat().st_size > LIMIT:
        raise ValueError('small queue source only')
    before = args.source.read_bytes()
    after = transform_owner_source_v1(before, expected_source_sha256=args.source_sha256)
    preserved_ast(before, after)
    args.temporary_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='queue-encoding-', dir=args.temporary_root) as temporary:
        reports = qualify_calls(before, after, Path(temporary))
    result = {'schema': 'xar.queue-response-encoding-qualification/v1',
        'machine_id': args.machine_id, 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'source': {'path': str(args.source.resolve()), 'bytes': len(before),
                   'sha256': hashlib.sha256(before).hexdigest()},
        'candidate_source': {'bytes': len(after), 'sha256': hashlib.sha256(after).hexdigest(),
            'produced_by': 'owner_response_source_transform_v1.transform_owner_source_v1'},
        'actual_source_excerpts': reports, 'unrelated_function_AST_unchanged': True,
        'post_result_tail_AST_unchanged': True,
        'benchmarks': [benchmark(4 * 1024**2), benchmark(16 * 1024**2)],
        'new_Game_Driver_Native_or_MCP_calls': 0, 'runtime_source_mutations': 0,
        'live_adopted': False, 'seconds_per_game_day_measured': False,
        'limits': ['Synthetic encoding wall time is not end-to-end campaign throughput.',
            'Actual response size and frequency determine useful savings.',
            'An active frozen owner must not be hot-swapped.'],
        'storage': {'policy_version': '1.0.0', 'temporary_receipts_deleted_after_test': True,
                    'maximum_source_bytes': LIMIT, 'maximum_receipt_bytes': LIMIT}}
    data = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode()
    if len(data) > LIMIT:
        raise ValueError('finite result limit exceeded')
    with args.receipt.open('xb') as stream:
        stream.write(data)
    print(json.dumps({'receipt': str(args.receipt), 'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(), 'source_cases': len(reports),
        'median_seconds': [row['median_seconds'] for row in result['benchmarks']]}))


if __name__ == '__main__':
    main()
