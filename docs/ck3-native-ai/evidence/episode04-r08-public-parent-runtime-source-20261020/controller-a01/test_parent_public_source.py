"""Offline source/control boundaries. Native/Steam/game qualification is always false."""
from pathlib import Path
import copy
from datetime import datetime, timezone, timedelta
import hashlib
import importlib.util
import json
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
TOOLS = BASE/'public-bundle-a01/tools'
REPO = Path(sys.argv.pop(sys.argv.index('--repo')+1)) if '--repo' in sys.argv else None
if '--repo' in sys.argv:
    sys.argv.remove('--repo')
sys.path[:0] = [str(TOOLS), str(REPO/'tools'), str(REPO/'ck3_autonomous_player/src')]
import ck3_mod_acceptance as entry
import ck3_mod_acceptance_launcher as launcher
import ck3_mod_acceptance_steam_gate as steam
import steam_offline_native_provider_v1 as provider
from steam_offline_state_contract import ProcessIdentity


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


controller = load(HERE/'r08_parent_entry_controller.py', 'parent_controller_test')


class Focused(unittest.TestCase):
    def setUp(self):
        temp_root = HERE/'tests-temp'
        temp_root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=temp_root)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def native_receipt(self):
        now = datetime.now(timezone.utc).isoformat()
        process = dict(pid=1234, birth_filetime='134000000000000000',
            exe=str(self.root/'steam.exe'), file_version=provider.STEAM_VERSION)
        source = dict(path=str(self.root/'steamui.dll'), bytes=provider.IMAGE_BYTES, sha256=provider.IMAGE_SHA256,
                      file_id='12345',mtime_ns='134000000000000000')
        base = 0x180000000
        evidence = dict(machine_id='synthetic-test-machine', observed_at_utc=now, nonce='a'*32,
            module_base=str(base), module_size=provider.IMAGE_SIZE, value_rva=str(provider.VALUE_RVA),
            value_address=str(base+provider.VALUE_RVA), producer_rva=str(provider.PRODUCER_RVA),
            producer_anchor_hex=provider.PRODUCER.hex(),
            producer_anchor_sha256=hashlib.sha256(provider.PRODUCER).hexdigest(), raw_samples=[1,1],
            steam_before=process, steam_after=process, source_before=source, source_after=source,
            tray_manager_pointer_rva=str(provider.TRAY_MANAGER_RVA), tray_manager_address=str(base+0x3000000),
            tray_state_offset=str(provider.TRAY_OFFSET), tray_state_samples=[4,4])
        result = dict(schema='xar.steam-offline-state-probe/v2', machine_id='synthetic-test-machine',
            observed_at_utc=now, nonce='a'*32, status='offline', reason='observed', steam=process,
            source=source, endpoint=None, diagnostics=[], observation_method='native_current_user_byte',
            native_evidence=evidence, offline_mode=True)
        reader = SimpleNamespace(identity=lambda pid: ProcessIdentity(**process))
        return result, reader

    def test_background_profile_machine_birth_and_freshness(self):
        value, reader = self.native_receipt()
        self.assertEqual(steam.validate_observation(value, machine_id='synthetic-test-machine', reader=reader).status, 'offline')
        variants = []
        bad = copy.deepcopy(value); bad['machine_id'] = 'other'; variants.append(bad)
        bad = copy.deepcopy(value); bad['source']['sha256'] = 'b'*64
        bad['native_evidence']['source_before'] = bad['source']; bad['native_evidence']['source_after'] = bad['source']; variants.append(bad)
        for bad in variants:
            with self.assertRaises(ValueError):
                steam.validate_observation(bad, machine_id='synthetic-test-machine', reader=reader)
        with self.assertRaises(ValueError):
            steam.validate_observation(value, machine_id='synthetic-test-machine', reader=reader,
                now=datetime.now(timezone.utc)+timedelta(seconds=31))
        with self.assertRaises(ValueError):
            steam.validate_observation(value, machine_id='synthetic-test-machine',
                reader=SimpleNamespace(identity=lambda pid: ProcessIdentity(pid, '134000000000000001', value['steam']['exe'], provider.STEAM_VERSION)))

    def test_source_hash_crossing_ttl_is_rejected(self):
        value, reader = self.native_receipt()
        path = self.root/'receipt.json'; path.write_text(json.dumps(value))
        with patch.object(steam, '_qualified_source', return_value=steam.parse_result(value).source), \
             patch.object(steam, 'validate_observation', wraps=steam.validate_observation) as observed:
            steam.validate_receipt(path, machine_id='synthetic-test-machine', reader=reader)
            self.assertEqual(observed.call_count, 2)
        # A slow hash crosses the boundary; the second real parser/freshness check rejects.
        stamp = datetime.now(timezone.utc)-timedelta(seconds=29)
        value['observed_at_utc'] = stamp.isoformat(); value['native_evidence']['observed_at_utc'] = stamp.isoformat()
        path.write_text(json.dumps(value))
        real = steam.datetime
        clock = SimpleNamespace(fromisoformat=real.fromisoformat, now=lambda tz: stamp+timedelta(seconds=31))
        with patch.object(steam, '_qualified_source', return_value=steam.parse_result(value).source), \
             patch.object(steam, 'datetime', clock):
            with self.assertRaises(ValueError):
                steam.validate_receipt(path, machine_id='synthetic-test-machine', reader=reader, now=stamp+timedelta(seconds=29))

    def test_actual_selection_external_adapter_explicit_peers_and_no_six_queries(self):
        fixture = load(REPO/'tools/test_ck3_mod_acceptance.py', 'shared_fixture_source')
        fixture.entry = entry
        f = fixture.SharedEntryTests('test_three_products_select_one_host_source_and_native')
        original_temp = tempfile.TemporaryDirectory
        with patch.object(fixture.tempfile, 'TemporaryDirectory', side_effect=lambda: original_temp(dir=HERE/'tests-temp')):
            f.setUp()
        self.addCleanup(f.doCleanups)
        f.products['product_inventory'] = str(REPO/'workshop/products.json')
        case = f.products['products']['xqol']['cases'][0]
        case['adapter'] = dict(path=str(TOOLS/'ck3_mod_acceptance_cases/r10_prepare_adapter.py'),
                               config=str(TOOLS/'ck3_mod_acceptance_cases/r10_prepare.json'))
        f.write(f.products_path, f.products)
        selected = entry.Selection(f.runtime_path, f.products_path, 'xqol', 'core')
        index = controller.pin(HERE/'BUNDLE-SOURCE-INDEX.prepared.json')
        cfg = json.loads((HERE/'CASE-INPUTS.binding-template.json').read_text())['case_inputs']['r08_parent_entry_one_day']
        q = self.root/'q.json'; q.write_text('{}')
        cfg.update(bundle_index_pin=index, qualification_pin=controller.pin(q), expected_start_date_raw=100,
                   deadline_utc=(datetime.now(timezone.utc)+timedelta(hours=2)).isoformat())
        selected.context = {'case_inputs': {'r08_parent_entry_one_day':cfg}}
        adapter = selected.load_adapter()
        context = selected.adapter_context()
        adapter.validate_contract(context)  # Executes actual explicit loader and all exact source pins.
        parent = sys.modules['ck3_mod_acceptance_cases.r08_parent_entry_one_day']
        self.assertEqual(Path(parent.__file__).resolve(), (HERE/'r08_parent_entry_one_day.py').resolve())
        client = object()
        with patch.object(parent, 'run_case', return_value={'source_route_only':True}) as route, \
             patch.object(adapter, 'collect_ready_t0', side_effect=AssertionError('No six-query R10 prelude')):
            self.assertTrue(adapter.run_case(context, client)['source_route_only'])
            route.assert_called_once_with(context, client)
        # Actual public run constructs its real CaseClient. Only SDK/UI methods
        # and the business actor are replaced with explicit source-only boundaries.
        context_path, run, freeze, actual_context = f.context()
        actual_context['steam_offline_receipt'] = str(self.root/'not-probed.json')
        actual_context['case_inputs'] = selected.context['case_inputs']
        f.write(context_path,actual_context)
        running=entry.Selection(f.runtime_path,f.products_path,'xqol','core',context_path)
        from ck3_mod_acceptance_client import CaseClient
        seen=[]
        def source_actor(c,original_client):
            self.assertIsInstance(original_client,CaseClient)
            seen.append(original_client);original_client._handle=object()
            return {'source_route_only':True}
        with patch.object(running,'preflight',return_value={'status':'READY_FOR_EXISTING_REVIEWED_LAUNCH','blockers':[]}), \
             patch.object(CaseClient,'wait_hold'),patch.object(CaseClient,'close_handle'), \
             patch.object(CaseClient,'normal_close',autospec=True,return_value={'source_only':True}) as close, \
             patch.object(parent,'run_case',side_effect=source_actor):
            self.assertTrue(running.run()['case_result']['source_route_only'])
            self.assertIs(close.call_args.args[0],seen[0])
        # The real public script also parses this external product route from an unrelated cwd.
        import subprocess
        result = subprocess.run([sys.executable,'-B',str(TOOLS/'ck3_mod_acceptance.py'),'plan',
            '--runtime',str(f.runtime_path),'--products',str(f.products_path),'--product','xqol','--case','core'],
            cwd=self.root, capture_output=True, timeout=15)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['adapter']['path'], case['adapter']['path'])

    def raw_ready(self, output, expected):
        start = dict(kind='start',schema='xar.maintenance.parent_entry.raw.v1',mode=controller.MODE,**expected)
        arm = dict(kind='arm',thread_id=10,thread_generation=1,thread_created=100,success=True,readback=True,
                   armed_debug=[expected['entry'],0,0,0,0,1])
        raw = output/'parent.raw.ndjson'
        raw.write_text('\n'.join(json.dumps(r) for r in [start,arm,dict(kind='ready',census_complete=True)])+'\n')
        return raw

    def test_actual_ready_prefix_identity_and_census(self):
        expected = {'machine_id':'test','pid':4,'created':10,'entry':100}
        raw = self.raw_ready(self.root,expected)
        ready = dict(ready=True,mode=controller.MODE,census_complete=True,armed_thread_count=1)
        self.assertTrue(controller.bind_ready(raw,{'expected':expected},ready)['actual_raw_ready'])
        with self.assertRaises(ValueError):
            controller.bind_ready(raw,{'expected':{**expected,'pid':5}},ready)
        with self.assertRaises(ValueError):
            controller.bind_ready(raw,{'expected':expected},{**ready,'armed_thread_count':2})

    def test_unknown_day_not_replayed_and_postread_only_after_cleanup(self):
        for cleanup in (True, False):
            with self.subTest(cleanup=cleanup):
                output=self.root/str(cleanup);output.mkdir();prepared=output/'prepared';prepared.mkdir()
                scope=dict(machine_id='test',mode=controller.MODE,execution_authorized=True,cancel_event='synthetic',
                    observed_at_utc=datetime.now(timezone.utc).isoformat(),expires_at_utc=(datetime.now(timezone.utc)+timedelta(seconds=60)).isoformat())
                scope_path=output/'scope.json';scope_path.write_text(json.dumps(scope));scope_pin=controller.pin(scope_path)
                expected={'machine_id':'test','pid':4,'created':10,'entry':100}
                (prepared/'BINDING.prepared.json').write_text(json.dumps(dict(expected=expected,root_scope_sha256=scope_pin['sha256'])))
                exe=output/'synthetic-not-executed.bin';exe.write_bytes(b'source-test-only')
                self.raw_ready(output,expected)
                order=[];process=SimpleNamespace(pid=55,poll=lambda:None)
                def call(label,tool,args):
                    order.append(label)
                    if label=='day-once':raise TimeoutError('original unknown')
                    return dict(date_raw=124,paused=True,played_character={'character_id':1},diagnostics={'bridge_pid':4,'connection_generation':1})
                def finish(session,**kwargs):
                    self.assertIs(session.process,process);order.append('cleanup');return {'cleanup_complete':cleanup}
                before=dict(date_raw=100,played_character={'character_id':1},diagnostics={'bridge_pid':4,'connection_generation':1})
                with patch.object(controller,'create_cancel',return_value=1),patch.object(controller,'process_birth',return_value='134000000000000000'), \
                     patch.object(controller.subprocess,'Popen',return_value=process),patch.object(controller,'finish',side_effect=finish), \
                     patch.object(controller,'await_ready',return_value=dict(ready=True,mode=controller.MODE,census_complete=True,armed_thread_count=1)):
                    result=controller.observe(python=sys.executable,tools=HERE/'parent-tools',observer=controller.pin(exe),
                        prepared=prepared,output=output,machine='test',scope_pin=scope_pin,collected_at=controller.time.monotonic(),before=before,deadline_utc=(datetime.now(timezone.utc)+timedelta(hours=2)).isoformat(),call=call)
                self.assertEqual(order.count('day-once'),1)
                self.assertEqual(order, ['day-once','cleanup','independent-after'] if cleanup else ['day-once','cleanup'])
                self.assertFalse(result['day']['exact_day_verified'])
                self.assertFalse(result['full_R08_qualified'])
                session=controller.SESSIONS.pop(str(output))
                session.stdout.close();session.stderr.close();controller.EVENTS.pop(str(output),None)

    def test_diagnostic_timeout_keeps_same_original_wait_until_exit(self):
        import subprocess
        output=self.root/'hold';output.mkdir();prepared=output/'prepared';prepared.mkdir()
        process=SimpleNamespace(pid=44,wait=unittest.mock.Mock(side_effect=[subprocess.TimeoutExpired('observer',45),0]))
        stdout=(output/'out').open('wb');stderr=(output/'err').open('wb')
        session=controller.Session(process,output,controller.time.monotonic()-46,stdout,stderr,1,'test','134000000000000000')
        def consume(argv,**kwargs):
            Path(argv[argv.index('--output')+1]).write_text(json.dumps({'synthetic':False,'cleanup_complete':True}))
            return SimpleNamespace(returncode=0)
        with patch.object(controller,'close_cancel'),patch.object(controller.time,'sleep'), \
             patch.object(controller.subprocess,'run',side_effect=consume):
            self.assertTrue(controller.finish(session,python=sys.executable,tools=HERE/'parent-tools',prepared=prepared)['cleanup_complete'])
        self.assertEqual(process.wait.call_count,2)
        self.assertTrue((output/'UNRESOLVED-NATIVE-HOLD.actual.json').exists())

    def test_expired_pair_and_rebuilt_observer_are_zero_launch(self):
        output=self.root/'refuse';output.mkdir();prepared=output/'prepared';prepared.mkdir()
        scope=dict(machine_id='test',mode=controller.MODE,execution_authorized=True,
            observed_at_utc=datetime.now(timezone.utc).isoformat(),
            expires_at_utc=(datetime.now(timezone.utc)+timedelta(seconds=60)).isoformat())
        p=output/'scope.json';p.write_text(json.dumps(scope));ref=controller.pin(p)
        (prepared/'BINDING.prepared.json').write_text(json.dumps({'root_scope_sha256':ref['sha256']}))
        exe=output/'not-executed.bin';exe.write_bytes(b'new content')
        original=controller.pin(exe)
        for age,observer,remaining in ((31,original,7200),(0,{**original,'sha256':'0'*64},7200),(0,original,1049)):
            with patch.object(controller.subprocess,'Popen') as launch,patch.object(controller,'create_cancel') as event:
                with self.assertRaises(ValueError):
                    controller.observe(python=sys.executable,tools=HERE/'parent-tools',observer=observer,
                        prepared=prepared,output=output,machine='test',scope_pin=ref,
                        collected_at=controller.time.monotonic()-age,before={},deadline_utc=(datetime.now(timezone.utc)+timedelta(seconds=remaining)).isoformat(),call=lambda *a: {})
                launch.assert_not_called();event.assert_not_called()
        self.assertFalse((output/'day.once.json').exists())

    def test_real_prepare_cli_requires_root_selected_seventeen_cases(self):
        import subprocess
        tools=HERE/'parent-tools'
        exe=self.root/'synthetic-observer-not-executed.bin';exe.write_bytes(b'not native qualification')
        source_pins=[controller.pin(tools/name) for name in ('cold_observer.cpp','parent_entry_execution_once.inc')]
        system=self.root/'system.json'
        system.write_text(json.dumps(dict(status='verified',system_token_sid='S-1-5-18',admin_token=True,
            missing_requested_paths=[],verified_requested_paths=[str(exe)],files=[controller.pin(exe)])))
        fifteen=['foreign257_then_target','created_thread','foreign4096_limit','timeout','cancel_late',
            'restore-fault','readback-fault','continue-fault','default-off','occupied-dr','occupied-tf',
            'context-drift','fullid-drift','magic-drift','session-drift']
        cold=self.root/'cold.json';cold.write_text(json.dumps(dict(schema='xar.maintenance.parent_entry.cold.suite.v1',
            mode=controller.MODE,machine_id='synthetic',selected_cases=fifteen,cases=[])))
        accept=self.root/'accept.json';accept.write_text('{}')
        q=self.root/'q.json';q.write_text(json.dumps(dict(schema='xar.maintenance.parent_entry.execution-qualification.v1',
            status='SELECTED_EXECUTION_COLD_PASS',mode=controller.MODE,machine_id='synthetic',observer_pin=controller.pin(exe),
            source_pins=source_pins,SYSTEM_receipt_pin=controller.pin(system),cold_suite_pin=controller.pin(cold),Root_acceptance_pin=controller.pin(accept))))
        scope=self.root/'scope.json';scope.write_text(json.dumps(dict(schema='xar.maintenance.parent_entry.root-scope.v1',
            mode=controller.MODE,execution_authorized=True,observed_at_utc=datetime.now(timezone.utc).isoformat(),
            expires_at_utc=(datetime.now(timezone.utc)+timedelta(seconds=60)).isoformat(),
            qualification_sha256=controller.pin(q)['sha256'],observer_sha256=controller.pin(exe)['sha256'])))
        argv=[sys.executable,'-B',str(tools/'prepare_parent_entry_admission.py'),'--prepare-parent-entry',
            '--repo',str(REPO),'--snapshot',str(self.root/'absent-before'),'--cash',str(self.root/'absent-cash'),
            '--root-scope',str(scope),'--qualification',str(q),'--observer',str(exe),'--output-root',str(self.root/'must-not-exist')]
        result=subprocess.run(argv,cwd=self.root,capture_output=True,timeout=15)
        self.assertEqual(result.returncode,2)
        self.assertIn(b'actual required cold suite',result.stderr)
        self.assertFalse((self.root/'must-not-exist').exists())

    def test_retained_real_harmless_host_wait_has_background_provenance(self):
        import subprocess
        frozen=dict(argv=[sys.executable,'-c','raise SystemExit(0)'],lease_anchor=str(self.root),run_id='synthetic')
        review={'schema':'synthetic-background-only'}
        with patch('ck3_mod_acceptance_steam_gate.recheck_before_popen') as gate:
            self.assertEqual(launcher.retain_host(self.root,frozen,review,{'lease':{}}),0)
        gate.assert_called_once()
        host=json.loads((self.root/'host-started.json').read_text())
        self.assertEqual(host['background_offline_admission'],review)
        self.assertNotIn('direct_review',host)
        self.assertTrue(json.loads((self.root/'host-original-process-exit.json').read_text())['actual_original_popen_wait'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
