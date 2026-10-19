"""Closed F91 inputs plus detached, all-in-memory read-only reconciliation tests."""
from __future__ import annotations
import argparse
import asyncio
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import types

import c16_war_results8495_reconcile_v1 as h


class Queue:
    def __init__(self):
        self.next_sequence = 8496
        self.launch = {'pid': 30852, 'creation_filetime': 134368995759027619}
        self.job = {'game_creation_filetime': 134368995759027619}
        self.full_loop_state = h.pinned('state.json')
        row = h.pinned('auto8495.json')
        self.halted = {'request': row['request'], 'row': row,
            'response': str(h.T / 'p37-responses/8495-1-result.json')}
        self.current_attempt = copy.deepcopy(self.halted)
        self.held_control = None
        self.expected_lifecycle_binding = {'fixture': 'same retained ordinary lifecycle'}
        self.checkpoint_bootstrap_verified = True
        self.persisted = 0

    def guard(self):
        pass  # Detached fixture: never observes a real process or desktop.

    def consume_sequence(self, request):
        h.require(request['sequence'] == self.next_sequence, 'fixture sequence differs')
        self.next_sequence += 1
        return request['sequence']

    def call_budget(self, tool):
        return 1

    def persist_loop_state(self):
        self.persisted += 1


def semantic(queue, pending):
    return {'map_ready': True, 'paused': True, 'one_life_terminal': False,
        'played_character': {'alive': True, 'character_id': 40526},
        'snapshot_id': 'native:1200', 'revision': 1201, 'native_revision': 1200,
        'date_raw': 53217072, 'episode_run_id': 'native-40526-1bec95182886',
        'diagnostics': {'bridge_pid': 30852, 'connection_generation': 1,
            'hello': {'pid': 30852, 'connection_generation': 1}},
        'succession_lifecycle': queue.expected_lifecycle_binding,
        'war_results_window_v1_close_pending': ({'native_request_id': h.OLD_ID,
            'step': 'close-war-results-window-v1', 'status': 'verification_pending'} if pending else None)}


def query_fixture(queue, visible):
    frame = h.checked_frame(semantic(queue, True), queue)
    dto = copy.deepcopy(h.pinned('auto8495.json')['result']['structured_content']['result'])
    request_id = 'war-overview-query-' + 'a' * 32
    receipt = {**h.OLD_OWNER, 'request_id': request_id, 'ticket_sequence': 2300,
        'executor_started_sequence': 2300, 'completed_sequence': 2300,
        'pump_epoch': 190000, 'date_raw': frame['date_raw']}
    dto.update(operation='query', step='query-war-results-window-v1', available=True,
        accepted=True, status='visible' if visible else 'absent', scope_unchanged=True,
        dispatch_attempted=False, dispatch_invoked=False, native_handled=False,
        closure_verified=False, request_id=request_id, native_request_id=request_id,
        ticket_sequence=2300, pump_epoch=190000, date_raw=frame['date_raw'],
        native_revision=frame['native_revision'], post_window_present=visible,
        post_effective_visible=visible,
        native_command_result={'type': 'command_result', 'protocol_version': 1,
            'request_id': request_id, 'ok': True, 'war_results_window_owner_receipt': receipt},
        prior_close_execution_observation={'native_request_id': h.OLD_ID,
            'status': 'callback_completed_closure_unverified', 'original_owner_receipt': h.OLD_OWNER,
            'followup_query_request_id': request_id, 'fresh_window_visible': visible,
            'original_action_replayed': False, 'close_action_credit': False})
    for key, value in {'queried_snapshot_id': 'snapshot_id', 'queried_revision': 'revision',
        'queried_native_revision': 'native_revision', 'queried_date_raw': 'date_raw',
        'queried_actor_character_id': 'actor_character_id',
        'queried_episode_run_id': 'episode_run_id',
        'queried_connection_generation': 'connection_generation'}.items():
        dto[key] = frame[value]
    return dto


async def exercise(*, visible=False, foreign_first=False, missing_final_latch=False):
    queue = Queue(); original = copy.deepcopy(queue.full_loop_state)
    persisted = {}
    inbox, outbox, q = h.T / 'p37-requests', h.T / 'p37-responses', h.T / 'p37-queue'
    sources = {
        q / 'ROOT-CUMULATIVE-LOOP-STATE.json': h.pinned('state.json'),
        q / 'ROOT-GOVERNANCE-RESULT-STATE.json': h.pinned('governance-exact.json'),
        outbox / '8495-1-result.json': h.pinned('auto8495.json'),
        outbox / '8495-0-plan.json': h.pinned('plan8495.json')}

    def atomic(path, value, **kwargs):
        persisted[path] = copy.deepcopy(value)

    calls, relays = [], []
    first = semantic(queue, True); final = semantic(queue, False)
    if foreign_first:
        first['played_character']['character_id'] += 1
    if missing_final_latch:
        del final['war_results_window_v1_close_pending']
    returns = [first, query_fixture(queue, visible), final]

    class Session:
        async def call_tool(self, tool, arguments, **kwargs):
            calls.append((tool, copy.deepcopy(arguments)))
            body = returns[len(calls) - 1]
            return types.SimpleNamespace(model_dump=lambda **kw: {'is_error': False,
                'result_type': 'complete', 'structured_content': body})

    def decoded(row):
        h.require(row['result']['is_error'] is False, 'fixture errored')
        return row['result']['structured_content']

    env = {'INBOX': inbox, 'OUTBOX': outbox, 'Q': q, 'REPLY_RESERVE': 262144,
        'read': lambda path, *args: sources[path], 'atomic': atomic,
        'now': lambda: datetime.now(timezone.utc), 'decoded': decoded,
        'sha256': lambda path: hashlib.sha256(json.dumps(persisted[path], sort_keys=True).encode()).hexdigest()}
    fake = types.ModuleType('root_p37c16_overlay_relay')
    fake.relay_compact = lambda source, projection: relays.append((source, projection))
    fake.error_projection = lambda row: row
    previous = sys.modules.get(fake.__name__)
    sys.modules[fake.__name__] = fake
    request = {'sequence': 8496, 'command': 'recover_partial_life_advance',
        'arguments': {'recovery_kind': h.KIND}}
    error = None
    try:
        try:
            await h.recover(queue, Session(), request, inbox / '8496-1-result.json', env,
                birth_reader=lambda pid: 134368995759027619)
        except ValueError as caught:
            error = str(caught)
    finally:
        if previous is None:
            del sys.modules[fake.__name__]
        else:
            sys.modules[fake.__name__] = previous
    if foreign_first or missing_final_latch:
        h.require(error is not None and queue.full_loop_state == original and queue.halted is not None,
            'foreign/incomplete proof cleared the original')
    elif visible:
        h.require(error is None and queue.full_loop_state == original and queue.halted is not None
            and queue.persisted == 0, 'visible window did not retain Queue pending')
    else:
        h.require(error is None and queue.full_loop_state['pending_cycle'] is None
            and queue.halted is None and queue.full_loop_state['completed_cycles'] == 3828
            and queue.full_loop_state['counts'] == original['counts']
            and queue.full_loop_state['actual_saved_checkpoint'] == original['actual_saved_checkpoint']
            and queue.full_loop_state['before']['date_raw'] == 53217072,
            'proved clear did not preserve original counts/SAVE')
    h.require([c[0] for c in calls] == ([h.SEM] if foreign_first else [h.SEM, h.QUERY, h.SEM]),
        'unexpected recovery tool or replay')
    h.require(len(relays) == len(calls) and all(persisted[h.T / 'CURRENT-REQUEST-P37.json']['sequence'] >= 8497
        for _ in (0,)), 'unique current request or relay path not preserved')
    return {'case': 'foreign_first' if foreign_first else 'missing_latch' if missing_final_latch
            else 'visible_hold' if visible else 'clear_observation', 'PASS': True,
        'calls': [c[0] for c in calls], 'actual_Game_RPC': 0, 'fixture_only': True}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    original = (h.T / 'root_p37_known_pause_recovery_control.py').read_bytes()
    outputs = h.build_sources(original)
    for raw in outputs.values():
        compile(raw, '<finite candidate>', 'exec')
    results = [asyncio.run(exercise()), asyncio.run(exercise(visible=True)),
        asyncio.run(exercise(foreign_first=True)), asyncio.run(exercise(missing_final_latch=True))]
    queue = Queue(); bad = query_fixture(queue, False)
    bad['prior_close_execution_observation']['original_owner_receipt'] = {**h.OLD_OWNER, 'thread_id': 1}
    rejected = False
    try:
        h.checked_query(bad, h.checked_frame(semantic(queue, True), queue))
    except ValueError:
        rejected = True
    h.require(rejected, 'wrong original ACK owner accepted')
    results.append({'case': 'wrong_original_owner_receipt', 'PASS': True, 'actual_Game_RPC': 0})
    payload = {'schema': 'xar.c16.war-results8495-source-qualification/v1',
        'machine_id': h.MACHINE, 'utc': datetime.now(timezone.utc).isoformat(),
        'source_only': True, 'actual_Game_RPC': 0, 'D_writes': 0,
        'actual_input_pins': {name: {'bytes': pin[0], 'sha256': pin[1]} for name, pin in h.PINS.items()},
        'outputs': {name: {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
            for name, raw in outputs.items()}, 'results': results,
        'dispatcher_change': 'one exact-kind lazy branch; inverse byte-identical to bfc3de2c original',
        'actual_MRO_fact': 'Fresh cold ready -> Clean.check_before3730 rejects halted; local3430 bypasses tool check',
        'current_context': 'unique child CURRENT written before each original session.call_tool; correct C16 relay',
        'limits': 'all child replies are synthetic; actual query/SEM adoption belongs solely to runtime'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'output': str(args.output), 'bytes': args.output.stat().st_size,
        'sha256': hashlib.sha256(args.output.read_bytes()).hexdigest(), 'cases': len(results),
        'outputs': payload['outputs']}))


if __name__ == '__main__':
    main()
