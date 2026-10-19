"""Software-only source/control equivalence; no files, SDK or Game calls."""
import ast
import asyncio
import hashlib
from types import SimpleNamespace
from unittest.mock import patch

import pytest

import queue_control_timing_adapter_v1 as adapter


SOURCE = '''from __future__ import annotations
import time
def atomic_payload_v1(path, payload):
    work.append('atomic')
class Queue:
    def __init__(self):
        self.full_loop_state = {'completed_cycles': 0}
        self.next_sequence = 4
    def guard(self):
        work.append('guard')
    def check_after(self, *args):
        work.append('classifier')
    def persist_loop_state(self):
        work.append('persist')
    async def call(self, session, request, path):
        self.guard()
        sequence = request['sequence']
        started, mono = 'fixture-UTC', time.monotonic()
        try:
            result = await session.call_tool('original', {})
            row, payload = _owner_response_success_row_once_v1(started, mono, result)
        except Exception:
            raise
        atomic_payload_v1(path, payload)
        relay_compact(path, result)
        self.check_after(result)
        return row
    async def generated(self, session):
        pending_request_paths(None, None, self.next_sequence)
        request = {'sequence': self.next_sequence}
        self.next_sequence += 1
        return await self.call(session, request, None)
    async def full_loop(self, session, request, path):
        maximum = request['arguments']['max_turns']
        settled = 0
        while settled < maximum:
            await self.generated(session)
            self.full_loop_state['completed_cycles'] += 1
            self.persist_loop_state()
            settled += 1
        return result_identity
'''
RELAY = '''"""Keep this relay docstring."""
def relay_compact(source, compact):
    return api.wait_text_published(source, compact, timeout_seconds=5)
'''


def digest(source):
    return hashlib.sha256(source.encode()).hexdigest()


class Strip(ast.NodeTransformer):
    def visit_ImportFrom(self, node):
        return None if node.module == 'queue_control_timing_adapter_v1' else node

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == '_control_rpc_boundary_v1':
            return None
        return self.generic_visit(node)

    def visit_Call(self, node):
        node = self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id == '_control_call_v1':
            return ast.Call(func=node.args[1], args=node.args[2:], keywords=node.keywords)
        return node

    def visit_With(self, node):
        node = self.generic_visit(node)
        if all(isinstance(x.context_expr, ast.Call) and isinstance(x.context_expr.func, ast.Name)
               and x.context_expr.func.id in {'_control_span_v1', '_control_call_scope_v1'} for x in node.items):
            return node.body
        return node


def test_source_transform_preserves_every_original_statement_and_argument():
    for source, transform in [(SOURCE, adapter.transform_queue_source_v1), (RELAY, adapter.transform_relay_source_v1)]:
        changed = transform(source, expected_sha256=digest(source))['source']
        assert ast.dump(Strip().visit(ast.parse(changed))) == ast.dump(ast.parse(source))
        with pytest.raises(ValueError):
            transform(source, expected_sha256='0' * 64)


@pytest.mark.parametrize('mode', ['off', 'on', 'writer_error', 'business_error'])
def test_one_shot_getter_binding_preserves_original_result_and_failure(mode, capsys):
    work, snapshots = [], []
    original, identity = RuntimeError('original business failure'), object()
    relay = adapter.transform_relay_source_v1(RELAY, expected_sha256=digest(RELAY))['source']
    namespace = {'work': work, 'result_identity': identity,
        'api': SimpleNamespace(wait_text_published=lambda *a, **k: work.append('ACK')),
        'pending_request_paths': lambda *a: work.append('pending'),
        '_owner_response_success_row_once_v1': lambda started, mono, result: (
            {'ended_at_utc': started, 'elapsed_seconds': 0.0}, b'{}')}
    exec(relay, namespace)
    exec(adapter.transform_queue_source_v1(SOURCE, expected_sha256=digest(SOURCE))['source'], namespace)
    Base = namespace['Queue']
    assert adapter.bind_queue_control_timing_v1(Base, {}, admission=None) is Base
    def writer(path, snapshot, **kwargs):
        snapshots.append(snapshot)
        if mode in {'writer_error', 'business_error'}:
            raise OSError('timing-only write failed')
    admission = {'schema': adapter.ADMISSION_SCHEMA, 'enabled': mode != 'off',
                 'machine_id': 'fixture-machine', 'control_sequence': 3, 'cycle_budget': 2}
    Bound = adapter.bind_queue_control_timing_v1(Base, {'Q': 'owned-fixture', 'atomic': writer},
        admission_getter=lambda queue: queue._normal_cold['admission']['control_timing'])
    queue = Bound()
    queue._normal_cold = {'admission': {'control_timing': admission}}
    async def call(*args):
        work.append('RPC')
        if mode == 'business_error':
            raise original
        return {'ok': True}
    request = {'sequence': 3, 'arguments': {'max_turns': 2}}
    with patch('builtins.open', side_effect=AssertionError('unexpected file I/O')):
        if mode == 'business_error':
            with pytest.raises(RuntimeError) as caught:
                asyncio.run(queue.full_loop(SimpleNamespace(call_tool=call), request, None))
            assert caught.value is original
        else:
            assert asyncio.run(queue.full_loop(SimpleNamespace(call_tool=call), request, None)) is identity
    if mode == 'off':
        assert snapshots == []
    else:
        assert len(snapshots) == 1
        sample = snapshots[0]
        assert sample['open_spans'] == sample['dropped_open_spans'] == 0
        if mode != 'business_error':
            for phase in ['call_total', 'pending_paths', 'consume_guard', 'atomic_write', 'relay_total', 'relay_ack_wait', 'loop_state_persist', 'loop_step']:
                assert sample['phase_totals'][phase]['count'] == 2
            assert sample['observed_settled_cycles'] == 2
        assert getattr(queue, '_control_timing_used_v1') is True
    if mode in {'writer_error', 'business_error'}:
        assert queue.timing_write_diagnostic.startswith('OSError:')
        assert capsys.readouterr().err.count('CONTROL_TIMING_SNAPSHOT_UNAVAILABLE') == 1
    if mode == 'on':
        later = {'sequence': 9, 'arguments': {'max_turns': 1}}
        assert asyncio.run(queue.full_loop(SimpleNamespace(call_tool=call), later, None)) is identity
        assert len(snapshots) == 1
    assert work.count('RPC') == (1 if mode == 'business_error' else 3 if mode == 'on' else 2)
