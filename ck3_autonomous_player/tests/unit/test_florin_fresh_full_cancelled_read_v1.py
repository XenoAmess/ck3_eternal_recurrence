"""NoGame: existing public MCP/service/driver + canonical saved-startup consumer.

Only native transport publications/heartbeats are software-authored inputs.
The original R8 failed receipt is read from its retained wire, never rewritten.
"""
from __future__ import annotations
import asyncio
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import unittest

CANDIDATE = Path(__file__).resolve().parents[3]
REPO = Path(os.environ.get('CK3_FRESH_CANDIDATE_REPO', CANDIDATE))
sys.path.insert(0, str(REPO / 'ck3_autonomous_player/src'))
import xar_autoplayer.bridge
xar_autoplayer.bridge.__path__.insert(0, str(CANDIDATE / 'ck3_autonomous_player/src/xar_autoplayer/bridge'))
driver_path = CANDIDATE / 'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py'
qualified = 'xar_autoplayer.bridge.native_driver'
loaded = sys.modules.get(qualified)
if loaded is None or Path(loaded.__file__).resolve() != driver_path.resolve():
    spec = importlib.util.spec_from_file_location(qualified, driver_path)
    driver_module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = driver_module
    spec.loader.exec_module(driver_module)
os.environ['CK3_FRESH_CANDIDATE_HOST'] = str(CANDIDATE / 'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py')
spec = importlib.util.spec_from_file_location('original_fresh_public_fixture', REPO / 'ck3_autonomous_player/tests/unit/test_florin_fresh_full_public_v1.py')
BASE = importlib.util.module_from_spec(spec); spec.loader.exec_module(BASE)
from xar_autoplayer.bridge.fresh_full_cancelled_read_v1 import CancelledFreshReadV1, FreshOwnerV1, FreshCancelledGateV1, cancelled_receipt_from_mcp_error_v1
from xar_autoplayer.bridge.driver import BridgeUnavailableError

R8_ACK = json.loads((CANDIDATE / 'ck3_autonomous_player/tests/fixtures/fresh_full1210/r0008-cancelled-ack.json').read_text())['actual_wire_entry']['message']
OWNER = BASE.OWNER['main_thread_query_mailbox_v1']['owner_tid']


def heartbeat(sequence=10, pump=40000, completed=100, completed_ms=1000, **changes):
    value = BASE.heartbeat(pump)
    value['sequence'] = sequence
    mailbox = value['main_thread_query_mailbox_v1']
    mailbox.update(active_hook_calls=0, owner_verified_pump_epochs=2)
    hook = {'entered': str(completed), 'completed': str(completed), 'last_entered_ms': str(completed_ms),
            'last_completed_ms': str(completed_ms), 'last_return_rva': 1, 'last_thread_id': OWNER}
    mailbox['owner_hook_entries_v1'] = {'schema': 'xar.native.owner-hook-entries/v1', 'peek': deepcopy(hook), 'poll': deepcopy(hook)}
    mailbox.update(changes)
    return value


class Endpoint(BASE.SoftwareEndpoint):
    def __init__(self):
        super().__init__(); self.failures = 1; self.change_ack = None; self.after_ack_busy = False
    def send(self, request):
        if len(self.requests) < self.failures:
            self.requests.append(deepcopy(request))
            ack = deepcopy(R8_ACK)
            ack['request_id'] = request['request_id']
            diagnostic = ack['fresh_full_state_diagnostic']
            diagnostic.update(owner_thread_id=OWNER, pump_epoch_at_start='40000', pump_epoch_at_end='40000')
            if self.change_ack is not None:
                self.change_ack(ack)
            self.driver.state.ingest(ack)
            if self.after_ack_busy:
                self.driver.state.ingest(heartbeat(11, 40000, 101, 1001, active_hook_calls=1))
        else:
            super().send(request)


class Case(BASE.SoftwareCase):
    def make(self):
        driver, _ = self.make_driver()
        endpoint = Endpoint(); endpoint.driver = driver; driver.endpoint = endpoint
        driver.state.ingest(heartbeat())
        return driver, endpoint
    def anchor(self, driver):
        driver.state.ingest(heartbeat(11, 40000, 101, 1001))
        return driver.diagnostics()
    def progress(self, driver):
        driver.state.ingest(heartbeat(12, 40002, 102, 1002))
        return driver.diagnostics()


class DriverProofTests(Case, unittest.TestCase):
    def test_original_r8_cancellation_is_exact_unexecuted_terminal(self):
        receipt = {'schema': 'xar.native.fresh-full-state-read-rejection/v1', 'request_id': R8_ACK['request_id'],
                   'step': 'query-fresh-full-state-v1', 'fresh_full_state_diagnostic': R8_ACK['fresh_full_state_diagnostic']}
        self.assertEqual(CancelledFreshReadV1.parse(receipt).to_json(), receipt)

    def test_cancel_then_no_progress_anchor_then_new_id_real_publication(self):
        driver, endpoint = self.make()
        cached_before = driver.state.semantic_snapshot()
        with self.assertRaises(BridgeUnavailableError) as failed:
            driver.take_fresh_full_snapshot_v1()
        original = deepcopy(failed.exception.native_raw_return_receipt)
        self.assertEqual(original['fresh_full_state_diagnostic']['wait_result'], 4)
        self.assertIsNone(driver._florin_fresh_full_read_pending_v1)
        with self.assertRaises(BridgeUnavailableError): driver.take_fresh_full_snapshot_v1()
        self.anchor(driver)
        with self.assertRaises(BridgeUnavailableError): driver.take_fresh_full_snapshot_v1()
        self.assertEqual(len(endpoint.requests), 1)
        self.progress(driver)
        self.assertEqual(cached_before['diagnostics']['last_heartbeat']['main_thread_query_mailbox_v1']['pump_epochs'], 40000)
        self.assertEqual(driver.state.semantic_snapshot()['snapshot_id'], cached_before['snapshot_id'])
        self.assertEqual(driver.state.semantic_snapshot()['diagnostics']['last_heartbeat']['main_thread_query_mailbox_v1']['pump_epochs'], 40002)
        result = driver.take_fresh_full_snapshot_v1()
        self.assertEqual(result['snapshot_id'], 'native:12')
        self.assertEqual(len(endpoint.requests), 2)
        self.assertNotEqual(endpoint.requests[0]['request_id'], endpoint.requests[1]['request_id'])
        self.assertEqual(endpoint.requests[0]['expected_revision'], 0)
        self.assertEqual(failed.exception.native_raw_return_receipt, original)

    def test_pump_entry_or_wake_alone_does_not_authorize_new_read(self):
        for change in ('same_completed', 'wrong_thread', 'active_hook', 'observer_busy'):
            with self.subTest(change=change):
                driver, endpoint = self.make()
                with self.assertRaises(BridgeUnavailableError): driver.take_fresh_full_snapshot_v1()
                self.anchor(driver)
                sample = heartbeat(12, 40002, 102, 1002)
                mailbox = sample['main_thread_query_mailbox_v1']
                if change == 'same_completed':
                    for hook in mailbox['owner_hook_entries_v1'].values():
                        if isinstance(hook, dict): hook.update(completed='101', last_completed_ms='1001')
                if change == 'wrong_thread':
                    for hook in mailbox['owner_hook_entries_v1'].values():
                        if isinstance(hook, dict): hook['last_thread_id'] = OWNER + 1
                if change == 'active_hook': mailbox['active_hook_calls'] = 1
                if change == 'observer_busy': sample['snapshot_observer_12002']['read_in_progress'] = True
                driver.state.ingest(sample)
                with self.assertRaises(BridgeUnavailableError): driver.take_fresh_full_snapshot_v1()
                self.assertEqual(len(endpoint.requests), 1)

    def test_unknown_running_reclaim_bad_type_and_bad_packet_keep_original_latch(self):
        changes = [lambda a:a['fresh_full_state_diagnostic'].update(wait_result=5),
            lambda a:a['fresh_full_state_diagnostic'].update(reclaim_result=1),
            lambda a:a['fresh_full_state_diagnostic'].update(wait_running_timeouts=1),
            lambda a:a['fresh_full_state_diagnostic'].update(submit_result=False),
            lambda a:a.update(request_id='not-this-request'), lambda a:a.pop('fresh_full_state_diagnostic')]
        for change in changes:
            with self.subTest(change=changes.index(change)):
                driver, endpoint = self.make(); endpoint.change_ack = change
                with self.assertRaises(BridgeUnavailableError): driver.take_fresh_full_snapshot_v1()
                pending = driver._florin_fresh_full_read_pending_v1
                self.assertIsInstance(pending, str)
                self.anchor(driver); self.progress(driver)
                with self.assertRaises(BridgeUnavailableError): driver.take_fresh_full_snapshot_v1()
                self.assertEqual(len(endpoint.requests), 1)
                self.assertEqual(driver._florin_fresh_full_read_pending_v1, pending)

    def test_owner_date_root_and_connection_drift_cannot_reissue(self):
        for change in ('owner', 'date', 'root', 'generation', 'tls'):
            with self.subTest(change=change):
                driver, endpoint = self.make()
                with self.assertRaises(BridgeUnavailableError): driver.take_fresh_full_snapshot_v1()
                self.anchor(driver)
                sample = heartbeat(12, 40002, 102, 1002)
                if change == 'owner': sample['main_thread_query_mailbox_v1'].update(owner_tid=OWNER+1, current_tid=OWNER+1)
                if change == 'date': sample['main_thread_query_mailbox_v1']['date_raw'] += 1
                if change == 'root': sample['main_thread_query_mailbox_v1']['game_state'] += 8
                if change == 'tls': sample['main_thread_query_mailbox_v1']['tls_context'] += 16
                if change == 'generation':
                    hello = BASE.hello(); hello['connection_generation'] += 1; driver.state.ingest(hello)
                    driver.state.ingest(deepcopy(BASE.ORIGINAL))
                driver.state.ingest(sample)
                with self.assertRaises((BridgeUnavailableError, ValueError)): driver.take_fresh_full_snapshot_v1()
                self.assertEqual(len(endpoint.requests), 1)

    def test_cached_observer_timestamp_and_continuous_count_are_not_total_epoch(self):
        driver, endpoint = self.make()
        with self.assertRaises(BridgeUnavailableError): driver.take_fresh_full_snapshot_v1()
        self.anchor(driver); self.progress(driver)
        self.assertEqual(driver.take_fresh_full_snapshot_v1()['snapshot_id'], 'native:12')
        self.assertEqual(len(endpoint.requests), 2)

    def test_gate_actor_preserves_actual_signed_character_domain(self):
        driver, _ = self.make()
        with self.assertRaises(BridgeUnavailableError): driver.take_fresh_full_snapshot_v1()
        raw = driver.diagnostics()['fresh_full_read_recovery_v1']
        for actor in (0, -2, -(2**31), 2**31-1):
            row = deepcopy(raw); row['actor_id'] = actor
            self.assertEqual(FreshCancelledGateV1.parse(row).actor_id, actor)
        for actor in (-1, True, 2**31, -(2**31)-1):
            row = deepcopy(raw); row['actor_id'] = actor
            with self.assertRaises(ValueError): FreshCancelledGateV1.parse(row)

    def test_tls_flags_require_native_exact_one_in_observe_context_and_parse(self):
        driver, _ = self.make()
        diagnostics = driver.diagnostics()
        valid_owner = FreshOwnerV1.observe(diagnostics)
        for field in ('tls_global', 'tls_marker'):
            with self.subTest(field=field):
                changed = deepcopy(diagnostics)
                changed['last_heartbeat']['main_thread_query_mailbox_v1'][field] = 2
                with self.assertRaises(ValueError): FreshOwnerV1.observe(changed)
                with self.assertRaises(ValueError): FreshOwnerV1.context(changed)
                encoded = valid_owner.to_json(); encoded[field] = 2
                with self.assertRaises(ValueError): FreshOwnerV1.parse(encoded)

    def test_ack_then_busy_keeps_known_terminal_read_recoverable(self):
        driver, endpoint = self.make(); endpoint.after_ack_busy = True
        with self.assertRaises(BridgeUnavailableError): driver.take_fresh_full_snapshot_v1()
        self.assertIsNone(driver._florin_fresh_full_read_pending_v1)
        self.assertIsNotNone(driver.diagnostics()['fresh_full_read_recovery_v1'])
        driver.state.ingest(heartbeat(12, 40000, 102, 1002)); driver.diagnostics()
        driver.state.ingest(heartbeat(13, 40002, 103, 1003)); driver.diagnostics()
        self.assertEqual(driver.take_fresh_full_snapshot_v1()['snapshot_id'], 'native:12')
        self.assertEqual(len(endpoint.requests), 2)

    def test_original_receipt_parser_rejects_ambiguous_and_wrong_tool_text(self):
        driver, _ = self.make()
        with self.assertRaises(BridgeUnavailableError) as failed: driver.take_fresh_full_snapshot_v1()
        prefix = 'MCP tool ck3_take_fresh_full_snapshot_v1 returned an error: Error executing tool ck3_take_fresh_full_snapshot_v1: '
        text = prefix + str(failed.exception)
        self.assertIsNotNone(cancelled_receipt_from_mcp_error_v1(RuntimeError(text)))
        for malformed in (text+' trailing', text.replace('ck3_take_fresh_full_snapshot_v1', 'world-action'),
                          text.replace('"wait_result": 4', '"wait_result": 5'),
                          text.replace('"elapsed_ms": "8000"', '"elapsed_ms": "8000", "elapsed_ms": "8000"')):
            self.assertIsNone(cancelled_receipt_from_mcp_error_v1(RuntimeError(malformed)))


class HostCombinationTests(Case, unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self): asyncio.get_running_loop().set_debug(False)
    def client(self, *, progress=True, spoof=False, drift=False, busy=False, race=False):
        driver, endpoint = self.make(); server = BASE.create_server(driver)
        diagnostic_count = 0
        race_injected = False
        class Client(BASE.HOST.PlanClient):
            async def call(self, name, arguments=None):
                nonlocal diagnostic_count, race_injected
                if name == 'ck3_migration_pipe_diagnostics':
                    diagnostic_count += 1
                    if race_injected and diagnostic_count == 6:
                        driver.state.ingest(heartbeat(14, 40004, 104, 1004))
                    if endpoint.requests and progress:
                        if diagnostic_count == 4:
                            if busy:
                                sample = heartbeat(11, 40000, 101, 1001)
                                if busy == 'ready': sample['main_thread_query_mailbox_v1']['ready'] = False
                                elif busy == 'observer': sample['snapshot_observer_12002']['read_in_progress'] = True
                                else: sample['main_thread_query_mailbox_v1']['active_hook_calls'] = 1
                                driver.state.ingest(sample)
                            else: self_case.anchor(driver)
                        if diagnostic_count == 5 and busy:
                            driver.state.ingest(heartbeat(12, 40001, 102, 1002)); driver.diagnostics()
                        if diagnostic_count == (6 if busy else 5):
                            self_case.progress(driver)
                            if busy: driver.state.ingest(heartbeat(13, 40003, 103, 1003))
                            if drift: driver.state.ingest(heartbeat(13, 40003, 103, 1003, owner_tid=OWNER+1, current_tid=OWNER+1))
                    return {'pipe': BASE.PIPE, 'transport_error': None, 'diagnostics': driver.diagnostics()}
                if race and len(endpoint.requests) == 1 and not race_injected:
                    gate = driver._florin_fresh_full_cancelled_gate_v1
                    if gate is not None and gate.anchor is not None:
                        # Host just admitted S2, but semantic_snapshot at SDK entry
                        # must observe the actual newer S3 busy heartbeat.
                        race_injected = True
                        driver.state.ingest(heartbeat(13, 40003, 103, 1003, active_hook_calls=1))
                try:
                    result = await server.call_tool(name, arguments or {})
                except BASE.ToolError as error:
                    if spoof: driver._florin_fresh_full_cancelled_gate_v1 = None
                    # The actual SDK ClientSession returns this ToolError text in
                    # isError content; canonical PlanClient.call wraps that payload.
                    raise RuntimeError('MCP tool ' + name + ' returned an error: ' + str(error)) from error
                if result.is_error:
                    text = result.content[0].text
                    if spoof:
                        # Error string looks exact; no new driver gate may authorize it.
                        driver._florin_fresh_full_cancelled_gate_v1 = None
                    raise RuntimeError('MCP tool ' + name + ' returned an error: ' + text)
                return result.structured_content
        self_case = self
        client = Client.__new__(Client); client.tools = {'ck3_take_fresh_full_snapshot_v1': {}}; client.snapshot = {}
        report = {'pipe': BASE.PIPE, 'saved_campaign_launch': {'status': 'ACTUAL_SINGLE_CLI_RESTORE_LAUNCHED',
            'argv_admitted': True, 'ck3_pid': BASE.PID}}
        writes = []
        return client, driver, endpoint, report, lambda: writes.append(deepcopy(report)), writes

    async def test_actual_public_failure_wait_progress_new_id_then_two_full_admission(self):
        client, driver, endpoint, report, write, writes = self.client()
        result = await BASE.HOST.wait_for_saved_campaign(client, {'actor_character_id': 1, 'date_raw': 123456},
            report=report, write=write, timeout=3, readiness_deadline=time.monotonic()+2, managed_done=None, poll_interval=.001)
        self.assertEqual(result['status'], 'ACTUAL_SAVED_CAMPAIGN_CURRENT_CONTEXT_BOUND')
        self.assertEqual(len(endpoint.requests), 3)
        self.assertEqual(len({row['request_id'] for row in endpoint.requests}), 3)
        attempts = result['fresh_full_read_attempts']
        self.assertEqual([row['status'] for row in attempts], ['FAILED', 'RETURNED', 'RETURNED'])
        self.assertEqual(attempts[0]['original_parsed_receipt'], attempts[0]['driver_cancelled_read_proof']['receipt'])
        self.assertTrue(any(w['saved_campaign_restore']['fresh_full_read_attempts'][0]['status']=='FAILED' for w in writes if w['saved_campaign_restore'].get('fresh_full_read_attempts')))
        self.assertFalse(result['product_acceptance_proven'])

    async def test_no_progress_preserves_deadline_and_does_not_resubmit(self):
        client, driver, endpoint, report, write, _ = self.client(progress=False)
        started = time.monotonic()
        with self.assertRaises(TimeoutError):
            await BASE.HOST.wait_for_saved_campaign(client, {'actor_character_id': 1, 'date_raw': 123456},
                report=report, write=write, timeout=1800, readiness_deadline=started+.04, managed_done=None, poll_interval=.001)
        self.assertEqual(len(endpoint.requests), 1)
        self.assertLess(time.monotonic()-started, 1)
        self.assertEqual(report['saved_campaign_restore']['fresh_full_read_attempts'][0]['status'], 'FAILED')

    async def test_temporarily_busy_owner_waits_inside_original_deadline(self):
        for busy in ('active', 'ready', 'observer'):
            with self.subTest(busy=busy):
                client, driver, endpoint, report, write, _ = self.client(busy=busy)
                result = await BASE.HOST.wait_for_saved_campaign(client, {'actor_character_id': 1, 'date_raw': 123456},
                    report=report, write=write, timeout=1800, readiness_deadline=time.monotonic()+1, managed_done=None, poll_interval=.001)
                self.assertEqual(result['status'], 'ACTUAL_SAVED_CAMPAIGN_CURRENT_CONTEXT_BOUND')
                self.assertEqual(len(endpoint.requests), 3)

    async def test_host_to_sdk_busy_race_has_new_typed_nosend_proof_then_waits(self):
        client, driver, endpoint, report, write, _ = self.client(race=True)
        result = await BASE.HOST.wait_for_saved_campaign(client, {'actor_character_id': 1, 'date_raw': 123456},
            report=report, write=write, timeout=1800, readiness_deadline=time.monotonic()+1, managed_done=None, poll_interval=.001)
        self.assertEqual(result['status'], 'ACTUAL_SAVED_CAMPAIGN_CURRENT_CONTEXT_BOUND')
        self.assertEqual(len(endpoint.requests), 3)
        attempts = result['fresh_full_read_attempts']
        self.assertEqual([row['status'] for row in attempts], ['FAILED', 'FAILED', 'RETURNED', 'RETURNED'])
        wait = attempts[1]['sdk_presubmission_wait']
        self.assertIs(wait['native_request_created'], False)
        self.assertIs(wait['native_request_sent'], False)
        self.assertEqual(wait['request_sequence_before'], '1')
        self.assertEqual(wait['cancelled_read_gate']['receipt'], attempts[0]['original_parsed_receipt'])
        self.assertTrue(endpoint.requests[1]['request_id'].startswith('fresh-full-2-'))

    async def test_text_only_proof_and_owner_drift_cannot_authorize_retry(self):
        for options in ({'spoof': True}, {'drift': True}):
            with self.subTest(options=options):
                client, driver, endpoint, report, write, _ = self.client(**options)
                with self.assertRaises((RuntimeError, ValueError, TimeoutError)):
                    await BASE.HOST.wait_for_saved_campaign(client, {'actor_character_id': 1, 'date_raw': 123456},
                        report=report, write=write, timeout=1, readiness_deadline=time.monotonic()+.1, managed_done=None, poll_interval=.001)
                self.assertEqual(len(endpoint.requests), 1)


if __name__ == '__main__': unittest.main()
