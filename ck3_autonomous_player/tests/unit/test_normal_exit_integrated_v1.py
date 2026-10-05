from pathlib import Path
import copy
import hashlib
import json
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(tempfile.gettempdir())

# This repository test resolves only its own checked-in tools dependency.
# The xar_autoplayer package follows the standard test environment; no external
# candidate checkout or archived dedicated module is put on sys.path.
_REPOSITORY_TOOLS = Path(__file__).resolve().parents[3] / 'tools'
if str(_REPOSITORY_TOOLS) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_TOOLS))
from ck3_native_profile_mcp import NativeProfileService
from xar_autoplayer.bridge.normal_exit_contract_v1 import (
    ExitWireBinding, classify_terminal_exit_receipt, encode_normal_exit_map_request,
    encode_normal_exit_map_packet, NATIVE_PROOF_KEYS, normalize_public_exit_result,
)
from xar_autoplayer.bridge.normal_exit_process_observer_v1 import RetainedProcessIdentity
from xar_autoplayer.bridge.normal_exit_source_inventory_v1 import (
    verify_source_inventory_v1, canonical_profile_projection, STOCK_GUI_PATHS,
)
from xar_autoplayer.bridge import normal_exit_map_driver_v1 as driver_module
from xar_autoplayer.bridge import normal_exit_pending_observer_v1 as pending_module
from xar_autoplayer.bridge.native_driver import NativeNamedPipeServer, NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from build_normal_exit_source_inventory_v1 import build_inventory
from test_normal_exit_process_observer_v1 import FakeApi

EXE_SHA = '94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6'


def native_observation(request, *, modal=False):
    action = request['action']
    observation = {
        'schema': 'ck3-normal-exit-map-v1', 'step': 'normal-exit-map-v1', 'action': action,
        'status': 'context_observed' if action == 'query_context' else
                  'confirmation_observed' if action == 'prepare_confirmation' else 'dispatch_pending',
        'native_revision': request['expected_revision'],
        'connection_generation': request['expected_connection_generation'],
        'game_pid': request['expected_game_pid'], 'played_character_id': request['expected_player_character_id'],
        'process_creation_filetime_100ns': request['expected_process_creation_filetime_100ns'],
        'pump_epoch': 11, **{key: True for key in NATIVE_PROOF_KEYS},
        'context_signature_verified': action != 'query_context',
        'confirmation_visible': modal or action == 'prepare_confirmation',
        'stage_consumed': [True, True, action == 'confirm_desktop'] if modal or action != 'query_context' else [False, False, False],
        'orderly_exit_verified': False, 'autosave_verified': False,
        'exit_context_signature': 'c' * 64, 'reason': '',
        'targets': [{key: True for key in ['read_complete', 'root_exists', 'root_visible', 'target_exists',
                                            'target_visible', 'target_enabled', 'unique_target', 'dispatch_admitted']}
                    | {'target_vtable_rva': 123} for _ in range(3)],
        'dispatches': [{key: False for key in ['claim_latched', 'dispatch_invoked', 'native_handled',
                                              'post_read_complete', 'postcondition_observed']} for _ in range(3)],
    }
    if action == 'prepare_confirmation':
        observation['dispatches'][0] = {key: True for key in observation['dispatches'][0]}
        observation['dispatches'][1] = {key: True for key in observation['dispatches'][1]}
    if action == 'confirm_desktop':
        observation['dispatches'][2] = {key: True for key in observation['dispatches'][2]}
    return observation


class FakeExitDriver:
    query_normal_exit_context_v1 = NativeHeadlessGameplayDriver.query_normal_exit_context_v1
    request_normal_exit_v1 = NativeHeadlessGameplayDriver.request_normal_exit_v1
    observe_normal_exit_v1 = NativeHeadlessGameplayDriver.observe_normal_exit_v1
    def __init__(self, path):
        self.path = path
        self.sent = []; self.modal = False; self.dead = False; self.fail_after_confirm = False
        self.remain_pending = False
        self.api = FakeApi(); self.normal_exit_process_api_factory = lambda: self.api
        self.normal_exit_managed_profile = {'normal_exit_source_inventory': {'path': 'fixture', 'sha256': 'b'*64}}
        self.endpoint = self; self.state = self; self.command_timeout_seconds = 0.01
        self.snapshot_calls = 0; self.capability_enabled = True
    def _native_driver_state_path(self): return self.path / 'driver-state.json'
    def capabilities(self): return {'bridge_capabilities': ['normal-exit-map-v1'] if self.capability_enabled else []}
    def take_snapshot(self):
        self.snapshot_calls += 1
        if self.dead: raise AssertionError('terminal flow tried to snapshot the dead process')
        return {'revision': 72, 'native_revision': 72, 'paused': True, 'map_ready': True,
                'date_raw': 123456, 'episode_run_id': 'run',
                'played_character': {'character_id': 9301, 'alive': True},
                'diagnostics': {'connection_generation': 8, 'bridge_pid': 43,
                    'hello': {'pid': 43, 'ck3_build_match': True, 'game_adapter_id': 'ck3-1.20.0.3-msvc-x64',
                              'expected_ck3_version': '1.20.0.3', 'expected_ck3_sha256': EXE_SHA}}}
    def send(self, request):
        self.sent.append(copy.deepcopy(request))
        if request['action'] == 'prepare_confirmation': self.modal = True
        if request['action'] == 'confirm_desktop':
            if not self.remain_pending: self.api.wait_result, self.api.code = 0, 0
            self.dead = True
            if self.fail_after_confirm: raise OSError('injected pipe closure after submission')
    def wait_for_command_result(self, request_id, timeout):
        return {'ok': True, 'request_id': request_id, 'result': native_observation(self.sent[-1], modal=self.modal)}


class DriverTests(unittest.TestCase):
    def sources(self): return patch.object(driver_module, 'verify_source_inventory_v1', return_value={'source_inventory_sha256': 'b'*64})
    def prepare_confirm_context(self, driver):
        first = driver.query_normal_exit_context_v1(expected_revision=72)
        prepared = driver.request_normal_exit_v1('prepare_confirmation', expected_revision=72,
                                                expected_exit_context_signature=first['exit_context_signature'])
        self.assertTrue(prepared['confirmation_observed'])
        return driver.query_normal_exit_context_v1(expected_revision=72)
    def test_actual_driver_service_preserves_terminal_exit_without_dead_snapshot(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary, self.sources():
            driver = FakeExitDriver(Path(temporary)); context = self.prepare_confirm_context(driver)
            service = GameplayBridgeService(driver)
            before = driver.snapshot_calls
            result = service.request_normal_exit_v1('confirm_desktop', expected_revision=72,
                expected_exit_context_signature=context['exit_context_signature'])
            self.assertTrue(result['process_exit_observed']); self.assertTrue(result['typed_normal_exit_observed'])
            self.assertFalse(result['autosave_verified'])
            self.assertEqual(driver.snapshot_calls, before + 1)  # submission frame only
            self.assertFalse(result['retry_authorized'])
            self.assertEqual(sum(call[0] == 'open' for call in driver.api.calls), 3) # two queries + preconfirm original pin
    def test_pipe_unknown_remains_consumed_and_only_independent_process_fact(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary, self.sources():
            driver = FakeExitDriver(Path(temporary)); context = self.prepare_confirm_context(driver)
            driver.fail_after_confirm = True
            result = driver.request_normal_exit_v1('confirm_desktop', expected_revision=72,
                expected_exit_context_signature=context['exit_context_signature'])
            self.assertTrue(result['process_exit_observed']); self.assertFalse(result['typed_normal_exit_observed'])
            self.assertIsNone(result['native_observation']); self.assertIsNone(result['driver_dispatch_receipt_observed_monotonic_ns'])
            self.assertTrue(result['claim_consumed']); self.assertFalse(result['retry_authorized'])
            driver.dead = False
            calls = len(driver.sent)
            with self.assertRaises(BridgeUnavailableError): driver.request_normal_exit_v1(
                'confirm_desktop', expected_revision=72, expected_exit_context_signature=context['exit_context_signature'])
            self.assertEqual(len(driver.sent), calls)
    def test_default_off_rejects_before_process_or_source_call(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            driver = FakeExitDriver(Path(temporary)); driver.capability_enabled = False
            with patch.object(driver_module, 'verify_source_inventory_v1', side_effect=AssertionError('forbidden')):
                with self.assertRaises(UnsupportedStepError): driver.query_normal_exit_context_v1(expected_revision=72)
            self.assertEqual(driver.api.calls, []); self.assertEqual(driver.sent, [])
    def test_missing_inventory_rejects_before_process_call(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            driver = FakeExitDriver(Path(temporary)); driver.normal_exit_managed_profile = {}
            with self.assertRaises(UnsupportedStepError): driver.query_normal_exit_context_v1(expected_revision=72)
            self.assertEqual(driver.api.calls, []); self.assertEqual(driver.sent, [])
    def test_confirm_requires_actual_modal_query_and_preconfirm_exact_identity(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary, self.sources():
            driver = FakeExitDriver(Path(temporary)); first = driver.query_normal_exit_context_v1(expected_revision=72)
            with self.assertRaises(BridgeUnavailableError): driver.request_normal_exit_v1(
                'confirm_desktop', expected_revision=72, expected_exit_context_signature=first['exit_context_signature'])
            context = self.prepare_confirm_context(driver); driver.api.creation += 1
            count = len(driver.sent)
            with self.assertRaises(ValueError): driver.request_normal_exit_v1(
                'confirm_desktop', expected_revision=72, expected_exit_context_signature=context['exit_context_signature'])
            self.assertEqual(len(driver.sent), count)

    def test_actual_profile_terminal_method_preserves_receipt_without_after_guard(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary, self.sources():
            directory=Path(temporary)
            driver=FakeExitDriver(directory)
            context=self.prepare_confirm_context(driver)
            class Backend:
                def poll(self, profile): return {'ack':True}
            class BoundProfile(NativeProfileService):
                def _bound_frame(self, revision, *, paused): return self.driver.take_snapshot()
                def _gameplay_service(self): return GameplayBridgeService(self.driver)
                def guard(self): raise AssertionError('terminal profile tried to guard after process exit')
            profile={'evidence_directory':str(directory/'profile-evidence'),'profile_sha256':'d'*64,
                     'normal_exit_source_inventory':{'path':'fixture','sha256':'b'*64}}
            service=BoundProfile(profile, backend=Backend()); service.driver=driver
            before=driver.snapshot_calls
            receipt=service.request_normal_exit('confirm_desktop',72,context['exit_context_signature'])
            self.assertTrue(receipt['result']['typed_normal_exit_observed'])
            self.assertFalse(receipt['snapshot_after_required'])
            self.assertEqual(driver.snapshot_calls,before+3) # two profile prechecks, one driver frame
            self.assertTrue(Path(receipt['receipt_path']).is_file())

    def test_service_rejects_untyped_backend_success_without_reading_a_final_snapshot(self):
        class BadBackend:
            def request_normal_exit_v1(self, *args, **kwargs): return {'status':'success'}
            def take_snapshot(self): raise AssertionError('service tried a live snapshot')
        service=GameplayBridgeService(BadBackend())
        with self.assertRaises(ValueError): service.request_normal_exit_v1('confirm_desktop',expected_revision=72,
            expected_exit_context_signature='c'*64)

    def test_pending_retains_original_handle_and_readonly_observer_eventually_completes(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary, self.sources():
            driver=FakeExitDriver(Path(temporary)); context=self.prepare_confirm_context(driver)
            driver.remain_pending=True
            result=driver.request_normal_exit_v1('confirm_desktop',expected_revision=72,
                expected_exit_context_signature=context['exit_context_signature'])
            self.assertTrue(result['observer_retained']); self.assertFalse(result['process_exit_observed'])
            opens=sum(c[0]=='open' for c in driver.api.calls); sends=len(driver.sent)
            service=GameplayBridgeService(driver)
            pending=service.observe_normal_exit_v1()
            self.assertTrue(pending['observer_retained']); self.assertEqual(pending['native_submission_count'],0)
            driver.api.wait_result,driver.api.code=0,0
            done=service.observe_normal_exit_v1()
            self.assertTrue(done['typed_normal_exit_observed']); self.assertFalse(done['observer_retained'])
            self.assertIsNone(driver._normal_exit_owned_observer_v1)
            self.assertEqual(sum(c[0]=='open' for c in driver.api.calls),opens)
            self.assertEqual(len(driver.sent),sends)
            self.assertTrue(Path(done['receipt_path']).is_file())
            self.assertTrue(Path(done['observer_close_receipt_path']).is_file())

    def test_pending_unknown_pipe_later_death_has_only_process_fact(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary, self.sources():
            driver=FakeExitDriver(Path(temporary)); context=self.prepare_confirm_context(driver)
            driver.remain_pending=True; driver.fail_after_confirm=True
            result=driver.request_normal_exit_v1('confirm_desktop',expected_revision=72,
                expected_exit_context_signature=context['exit_context_signature'])
            self.assertTrue(result['observer_retained']); self.assertIsNone(result['native_observation'])
            driver.api.wait_result,driver.api.code=0,0
            done=GameplayBridgeService(driver).observe_normal_exit_v1()
            self.assertTrue(done['process_exit_observed']); self.assertFalse(done['typed_normal_exit_observed'])
            self.assertIsNone(done['driver_dispatch_receipt_observed_monotonic_ns'])

    def test_public_confirm_recomputes_facts_and_rejects_forged_backend_summaries(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary, self.sources():
            driver=FakeExitDriver(Path(temporary)); context=self.prepare_confirm_context(driver)
            driver.remain_pending=True
            result=driver.request_normal_exit_v1('confirm_desktop',expected_revision=72,
                expected_exit_context_signature=context['exit_context_signature'])
            normalize_public_exit_result(result,action='confirm_desktop',expected_revision=72)
            for changes in [{'process_exit_observed':True}, {'typed_normal_exit_observed':True},
                            {'exit_code':0}, {'status':'process_exit_observed_zero'}]:
                forged=copy.deepcopy(result); forged.update(changes)
                with self.assertRaises(ValueError):
                    normalize_public_exit_result(forged,action='confirm_desktop',expected_revision=72)
            forged=copy.deepcopy(result)
            forged['process_observation']['retained_handle_token']='substituted'
            with self.assertRaises(ValueError):
                normalize_public_exit_result(forged,action='confirm_desktop',expected_revision=72)
            pending_module.dispose_normal_exit_observer_v1(driver)

    def test_failed_wait_retains_owned_observer_for_later_same_handle_observation(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary,self.sources():
            driver=FakeExitDriver(Path(temporary)); context=self.prepare_confirm_context(driver)
            driver.remain_pending=True
            driver.request_normal_exit_v1('confirm_desktop',expected_revision=72,
                expected_exit_context_signature=context['exit_context_signature'])
            owned=driver._normal_exit_owned_observer_v1
            driver.api.wait_error=OSError('injected failed wait')
            result=driver.observe_normal_exit_v1()
            self.assertTrue(result['observer_retained']); self.assertFalse(result['process_exit_observed'])
            self.assertIs(driver._normal_exit_owned_observer_v1,owned)
            driver.api.wait_error=None; driver.api.wait_result,driver.api.code=0,0
            self.assertTrue(driver.observe_normal_exit_v1()['typed_normal_exit_observed'])

    def test_actual_driver_close_disposes_pending_handle_without_fake_exit(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary, self.sources():
            directory=Path(temporary); driver=FakeExitDriver(directory)
            context=self.prepare_confirm_context(driver); driver.remain_pending=True
            driver.request_normal_exit_v1('confirm_desktop',expected_revision=72,
                expected_exit_context_signature=context['exit_context_signature'])
            waits=sum(c[0]=='wait' for c in driver.api.calls)
            closed=[]; driver.endpoint=SimpleNamespace(close=lambda:closed.append(True))
            driver._driver_state_lock=threading.RLock(); driver.state_dir=None
            NativeHeadlessGameplayDriver.close(driver)
            self.assertEqual(closed,[True]); self.assertIsNone(driver._normal_exit_owned_observer_v1)
            self.assertEqual(sum(c[0]=='wait' for c in driver.api.calls),waits)
            receipts=list((directory/'normal-exit-map-requests').glob('*.observer-dispose-*.json'))
            facts=[json.loads(path.read_bytes()) for path in receipts if not path.name.endswith('.close.json')]
            self.assertEqual(len(facts),1); self.assertFalse(facts[0]['process_exit_observed'])

    def test_receipt_write_failure_preserves_pending_ownership_until_new_readonly_attempt(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary, self.sources():
            driver=FakeExitDriver(Path(temporary)); context=self.prepare_confirm_context(driver)
            driver.remain_pending=True
            driver.request_normal_exit_v1('confirm_desktop',expected_revision=72,
                expected_exit_context_signature=context['exit_context_signature'])
            driver.api.wait_result,driver.api.code=0,0
            state=driver._normal_exit_owned_observer_v1
            with patch.object(pending_module,'_preserve',side_effect=OSError('injected receipt failure')):
                with self.assertRaises(OSError): driver.observe_normal_exit_v1()
            self.assertIs(driver._normal_exit_owned_observer_v1,state)
            self.assertTrue(driver.observe_normal_exit_v1()['process_exit_observed'])

    def test_close_receipt_failure_keeps_terminal_fact_and_clears_closed_ownership(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary, self.sources():
            driver=FakeExitDriver(Path(temporary)); context=self.prepare_confirm_context(driver)
            driver.remain_pending=True
            driver.request_normal_exit_v1('confirm_desktop',expected_revision=72,
                expected_exit_context_signature=context['exit_context_signature'])
            driver.api.wait_result,driver.api.code=0,0
            original_preserve=pending_module._preserve
            def fail_only_close_receipt(path,value):
                if value.get('schema')=='ck3-normal-exit-observer-close-v1':
                    raise OSError('injected close receipt failure')
                return original_preserve(path,value)
            with patch.object(pending_module,'_preserve',side_effect=fail_only_close_receipt):
                result=GameplayBridgeService(driver).observe_normal_exit_v1()
            self.assertTrue(result['typed_normal_exit_observed']); self.assertFalse(result['observer_retained'])
            self.assertIn('close receipt failure',result['observer_close_receipt_error'])
            self.assertIsNone(driver._normal_exit_owned_observer_v1)
            self.assertTrue(json.loads(Path(result['receipt_path']).read_bytes())['process_exit_observed'])
            with self.assertRaises(UnsupportedStepError): driver.observe_normal_exit_v1()

    def test_profile_observer_uses_owned_backend_without_dead_guard_snapshot_or_poll(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary,self.sources():
            directory=Path(temporary); driver=FakeExitDriver(directory)
            context=self.prepare_confirm_context(driver); driver.remain_pending=True
            driver.request_normal_exit_v1('confirm_desktop',expected_revision=72,
                expected_exit_context_signature=context['exit_context_signature'])
            profile={'evidence_directory':str(directory/'profile-evidence'),'profile_sha256':'d'*64}
            service=NativeProfileService(profile,backend=SimpleNamespace())
            service.driver=driver; service._gameplay=GameplayBridgeService(driver)
            service.guard=lambda:(_ for _ in ()).throw(AssertionError('no afterguard'))
            calls=driver.snapshot_calls; driver.api.wait_result,driver.api.code=0,0
            receipt=service.observe_normal_exit()
            self.assertTrue(receipt['result']['process_exit_observed'])
            self.assertEqual(driver.snapshot_calls,calls)


class TerminalClassifierTests(unittest.TestCase):
    def classify(self, process, native=None):
        return classify_terminal_exit_receipt(native, process,
            driver_dispatch_receipt_observed_monotonic_ns=100,
            expected_process_identity=RetainedProcessIdentity(43, 133000000000000043, 'original'))
    def process(self): return {'pid': 43, 'creation_filetime_100ns': 133000000000000043,
        'retained_handle_token': 'original', 'wait_state': 'signaled', 'wait_result': 0, 'exit_code': 0,
        'observed_monotonic_ns': 101, 'observation_clock_domain': 'driver_monotonic_v1',
        'process_identity_verified':True}
    def test_timeout_false_summary_and_invalid_dword_never_count_exit(self):
        for changes in [{'wait_state':'timeout', 'wait_result':258, 'process_exit_observed':True},
                        {'exit_code':True}, {'exit_code':-1}, {'exit_code':2**32}, {'wait_result':False}]:
            process = self.process(); process.update(changes)
            self.assertFalse(self.classify(process)['process_exit_observed'])
    def test_replaced_original_handle_token_never_counts_exit(self):
        process = self.process(); process['retained_handle_token'] = 'replacement'
        self.assertEqual(self.classify(process)['status'], 'original_retained_handle_identity_mismatch')
    def test_unknown_native_only_has_process_fact(self):
        facts = self.classify(self.process())
        self.assertTrue(facts['process_exit_observed']); self.assertFalse(facts['typed_normal_exit_observed'])


class PacketTests(unittest.TestCase):
    def test_actual_production_endpoint_encoder_packet_equals_production_contract(self):
        arguments = {'request_id':'req-1', 'action':'query_context', 'request_nonce':'nonce-1',
                     'binding':ExitWireBinding(72,9301,43,8,133000000000000043,'b'*64)}
        payload = encode_normal_exit_map_request(**arguments)
        packet = []
        server = NativeNamedPipeServer(r'\\.\pipe\offline_fixture')
        with patch.object(server, '_current_handle', return_value=999), patch(
                'xar_autoplayer.bridge.native_driver._write_all', side_effect=lambda handle,data: packet.append(data) or True):
            server.send(json.loads(payload))
        self.assertEqual(packet, [encode_normal_exit_map_packet(**arguments)])
        self.assertEqual(packet[0][4:], payload)
    def test_actor_boundary_matches_native_snapshot_signed_int32(self):
        for actor in [1, 2147483647]:
            encode_normal_exit_map_request(request_id='req', action='query_context', request_nonce='nonce',
                binding=ExitWireBinding(1,actor,1,1,1,'b'*64))
        for actor in [0,2147483648,4294967295,2**64-1]:
            with self.assertRaises(ValueError): ExitWireBinding(1,actor,1,1,1,'b'*64)


class InventoryTests(unittest.TestCase):
    def fixture(self, root):
        userdir = root / 'userdir'; userdir.mkdir()
        game = root / 'game'; game.mkdir()
        executable = root / 'ck3.exe'; executable.write_bytes(b'fake exact binary')
        (userdir / 'pdx_settings.txt').write_bytes(b'fixture settings')
        (userdir / 'dlc_load.json').write_text(json.dumps({'enabled_mods':['mod/example.mod']}))
        mod = root / 'mod-root'; mod.mkdir(); (mod / 'descriptor.mod').write_bytes(b'name="fixture"\n')
        (mod / 'content.txt').write_bytes(b'fixture mod content')
        (userdir / 'mod').mkdir(); (userdir / 'mod/example.mod').write_text(f'path="{mod.as_posix()}"\n')
        for relative in STOCK_GUI_PATHS:
            path = game / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(relative.encode())
        profile = {'schema_version':1,'guard_profile':str(root / 'guard.json'),'guard_profile_sha256':'d'*64,
                   'userdir':str(userdir),'evidence_directory':str(root / 'evidence'),'game_version':'1.20.0.3',
                   'state_directory':str(root / 'state'),'dll':{'path':str(root / 'dll'),'sha256':'e'*64},
                   'injector':{'path':str(root / 'injector'),'sha256':'f'*64},
                   'guard':{'target':{'executable':str(executable),'executable_sha256':hashlib.sha256(executable.read_bytes()).hexdigest()}}}
        inventory, projection = build_inventory(profile, game)
        path = userdir / 'normal-exit-source-inventory-v1.json'
        path.write_text(json.dumps(inventory, separators=(',', ':'), ensure_ascii=False))
        reference = {'path':str(path), 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        return profile, reference, inventory, mod, game
    def test_complete_physical_inventory_and_projection_without_reference_cycle(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            profile, reference, _, _, _ = self.fixture(Path(temporary))
            before = canonical_profile_projection(profile)
            profile['normal_exit_source_inventory'] = reference
            self.assertEqual(canonical_profile_projection(profile), before)
            proof = verify_source_inventory_v1(reference, profile)
            self.assertTrue(proof['static_sources_verified']); self.assertEqual(proof['enabled_mod_count'], 1)
    def test_missing_inventory_new_file_and_changed_source_are_rejected(self):
        for mode in ['extra','changed','settings']:
            with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
                profile, reference, _, mod, _ = self.fixture(Path(temporary))
                if mode=='extra': (mod / 'new.txt').write_bytes(b'unrecorded')
                elif mode=='changed': (mod / 'content.txt').write_bytes(b'changed')
                else: (Path(profile['userdir']) / 'pdx_settings.txt').write_bytes(b'changed')
                with self.assertRaises(ValueError): verify_source_inventory_v1(reference, profile)
    def test_strict_zero_gui_scope_rejects_even_inventoried_gui(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            profile, reference, inventory, mod, _ = self.fixture(Path(temporary))
            data = b'types={type unrelated=window{}}'; (mod / 'unrelated.gui').write_bytes(data)
            inventory['enabled_mods'][0]['files'].append({'relative_path':'unrelated.gui','bytes':len(data),
                                                        'sha256':hashlib.sha256(data).hexdigest()})
            path = Path(reference['path']); path.write_text(json.dumps(inventory)); reference['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, 'does not support enabled mod GUI'): verify_source_inventory_v1(reference, profile)


if __name__ == '__main__': unittest.main()
