"""Source fixtures only. No installed game, native watcher, SDK or real Q."""
from __future__ import annotations
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import check_owner
from ck3_mod_acceptance_cases import r08_parent_pointer_read_controller as controller
from ck3_mod_acceptance_cases import pointer_read_public_models as model
from ck3_mod_acceptance_cases import r08_writer_common_adapter as common
from pointer_read_models import Expected
from pointer_read_wire import wire_json

A = Path(__file__).resolve().parent
FILES = A/'tools/ck3_mod_acceptance_cases'
PROD = Path('C:/ck3-e04-resume-20261020-a01/r08-production-runtime-source-2130-a01/source-candidate-a01')
D = Path('D:/workspace/ck3_eternal_recurrence')
BIRTH = 134369989956828136


def expected() -> Expected:
    return Expected(machine_id='fixture-machine',synthetic=True,pid=77,created=BIRTH,
        entry=0x14028f7840,post_pc=0x14028f785a,watch_address=0x1001c0,character=0x100000,
        full_id=33388,context=0,local_player_id=1,game_state=0x200000,date_raw=1000,absolute_day=40,
        foreign_limit=4096,capture_ms=30000,admission_id='fixture-not-admission',owner_binding=None)


def binding() -> model.Binding:
    return model.Binding.parse({'schema':'xar.maintenance.parent_pointer_read.binding.v2','machine_id':'fixture-machine',
        'prepared_only':True,'expected':wire_json(expected()),'root_scope_sha256':'0'*64})


def rows() -> list[dict[str,object]]:
    start: dict[str,object] = dict(expected())
    start.update(kind='start',schema=model.SCHEMA,mode=model.MODE,entryExact=False,
        observation_kind='post_parent_pointer_read',target_record_limit=1,
        prefix_sha256='1df1ff739200e1970c772c4fa83df59ff36219925f0c1d2c3d9897bfaca8c19a')
    return [start,{'kind':'arm','thread_id':81,'thread_generation':1,'thread_created':BIRTH,
        'success':True,'readback':True,'saved_debug':[0,0,0,0,0x4000,0x400],
        'armed_debug':[0x1001c0,0,0,0,0xffff0ff0,0xb0401]}, {'kind':'ready','census_complete':True}]


def save_rows(path: Path, values: list[dict[str,object]]) -> None:
    data = b''.join((json.dumps(wire_json(row))+'\n').encode() for row in values)
    path.write_bytes(data)


def ready() -> model.Ready:
    return model.Ready.parse({'ready':True,'mode':model.MODE,'armed_thread_count':1,'census_complete':True})


class CommonFixture:
    def __init__(self, output: Path) -> None:
        self.output = output
        self._process = {'pid':77}

    def guard(self) -> None:
        pass

    def retain_process(self) -> None:
        pass

    def validate_frame(self, body: object, *, require_event_free: bool) -> None:
        pass

    def execute_plan(self, steps: list[dict[str,object]], name: str, *, timeout: float) -> list[dict[str,object]]:
        if steps[0]['tool'] == 'ck3_take_snapshot':
            body: dict[str,object] = {'played_character':{'character_id':33388},'episode_projection':'native_campaign',
                'episode_run_id':None,'local_player_id':1,'revision':5,'native_revision':6,'date_raw':1000,
                'diagnostics':{'bridge_pid':77,'connection_generation':2,
                    'last_heartbeat':{'main_thread_query_mailbox_v1':{'game_state':0x200000}}}}
        else:
            body = {'war_payment_observations_v1':{'current_session':{'controlled_window_id':7},
                'sampling':{'epoch':8,'capture_enabled':True},'controlled_window_admitted':True}}
        result: list[dict[str,object]] = [{'id':name,'ok':True,'error':None,'result':body}]
        (self.output/(name+'.actual-results.json')).write_text(json.dumps({'rows':result}),encoding='utf-8')
        return result


class PublicPointerTests(unittest.TestCase):
    def test_real_common_producer_integer_to_new_wire(self) -> None:
        with tempfile.TemporaryDirectory(dir=A,prefix='common-') as temp:
            root = Path(temp)
            client = CommonFixture(root)
            raw = common.collect_current_context({'output':str(root)},client,machine='fixture-machine',prefix='owner',
                packet_root=root/'packets',owner_binding_mode='native_campaign_owned_no_load_v2',
                _created_reader=lambda retained:BIRTH)
            collected = model.Collected.parse(raw,'fixture-machine')
            self.assertEqual(collected.created,BIRTH)
            projected = json.loads(model.output_json({'created':collected.created}))
            self.assertEqual(projected['created'],str(BIRTH))
            self.assertIs(type(raw['expected']['created']),int)
            for bad in (True,float(BIRTH),str(BIRTH)):
                changed = dict(raw)
                changed['expected'] = dict(raw['expected'],created=bad)
                with self.assertRaises(ValueError):
                    model.Collected.parse(changed,'fixture-machine')

    def test_raw_v2_full_six_and_retired_generation(self) -> None:
        with tempfile.TemporaryDirectory(dir=A,prefix='ready-') as temp:
            path = Path(temp)/'raw.ndjson'
            values = rows()
            exited = {'kind':'thread_exited','thread_id':81,'thread_generation':1}
            rearm = dict(values[1],thread_generation=2,thread_created=BIRTH+1)
            values[2:2] = [exited,rearm]
            save_rows(path,values)
            proof = controller.bind_ready(path,binding(),ready())
            self.assertIsNotNone(proof)
            self.assertEqual(proof['active_thread_count'],1)
            self.assertTrue(proof['all_six_debug_registers_validated'])

    def test_wire_schema_identity_vectors_and_nullable_presence_refuse(self) -> None:
        with tempfile.TemporaryDirectory(dir=A,prefix='mutation-') as temp:
            path = Path(temp)/'raw.ndjson'
            for label in ('v1','missing-owner','wrong-machine','dr1','dr7','birth-number','birth-padded','dr-bool'):
                values = rows()
                wire = json.loads(json.dumps(wire_json(values)))
                if label == 'v1':wire[0]['schema']='xar.maintenance.parent_pointer_read.raw.v1'
                elif label == 'missing-owner':del wire[0]['owner_binding']
                elif label == 'wrong-machine':wire[0]['machine_id']='other'
                elif label == 'dr1':wire[1]['armed_debug'][1]='1'
                elif label == 'dr7':wire[1]['armed_debug'][5]=str(0xb0401|0x200)
                elif label == 'birth-number':wire[1]['thread_created']=BIRTH
                elif label == 'birth-padded':wire[1]['thread_created']='0'+str(BIRTH)
                else:wire[1]['armed_debug'][0]=True
                path.write_bytes(b''.join((json.dumps(row)+'\n').encode() for row in wire))
                with self.subTest(label=label),self.assertRaises(ValueError):
                    controller.bind_ready(path,binding(),ready())

    def test_sidecar_before_raw_ready_waits_same_owner(self) -> None:
        with tempfile.TemporaryDirectory(dir=A,prefix='gap-') as temp:
            root = Path(temp)
            (root/'parent.ready.json').write_text(json.dumps(ready().raw),encoding='utf-8')
            save_rows(root/'parent.raw.ndjson',rows()[:2])
            stdout = (root/'child.stdout').open('wb')
            stderr = (root/'child.stderr').open('wb')
            process: subprocess.Popen[bytes] = subprocess.Popen([sys.executable,'-B','-c','import time;time.sleep(0.1)'],
                stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
            ticks = [0.0]

            def monotonic() -> float:
                return ticks[0]

            def sleep(seconds: float) -> None:
                ticks[0] += seconds
                save_rows(root/'parent.raw.ndjson',rows())

            session = controller.Session(process,root,0.0,stdout,stderr,0,'fixture-machine')
            try:
                proof = controller.await_ready(session,binding(),monotonic=monotonic,sleep=sleep)
                self.assertTrue(proof['binding']['actual_raw_ready'])
            finally:
                code = controller.wait_original(process,threshold=time.monotonic()+1,warning=lambda:None)
                stdout.close();stderr.close()
            self.assertEqual(code,0)

    def test_original_wait_survives_reporting_error(self) -> None:
        process: subprocess.Popen[bytes] = subprocess.Popen([sys.executable,'-B','-c','import time;time.sleep(0.35)'],
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
        birth = controller.process_birth(process)
        warnings = [0]

        def warning() -> None:
            warnings[0] += 1
            raise ValueError('fixture receipt failure must not release owner')

        code = controller.wait_original(process,threshold=time.monotonic()-1,warning=warning)
        self.assertEqual(code,0)
        self.assertEqual(process.wait(),0)
        self.assertEqual(warnings[0],1)
        print(json.dumps({'kind':'harmless_original_owner','pid':process.pid,'created':birth,
            'actual_original_popen_wait':True,'returncode':code,'warning_receipt_error_injected':True}))

    def test_settings_budget_and_owner_freshness_refuse(self) -> None:
        with tempfile.TemporaryDirectory(dir=A,prefix='settings-') as temp:
            root = Path(temp)
            file = root/'fixture.json';file.write_bytes(b'{}')
            ref = model.pin(file)
            settings = model.Settings(ref,ref,ref,root/'scope',33388,1000,A/'parent-tools','r08-pointer-test',
                datetime.now(timezone.utc)+timedelta(seconds=2000),False,False)
            settings.budget()
            with self.assertRaises(ValueError):
                replace(settings,deadline=datetime.now(timezone.utc)+timedelta(seconds=1049)).budget()
            scope: dict[str,object] = {'schema':'xar.maintenance.parent_pointer_read.root-scope.v1',
                'mode':model.MODE,'machine_id':'fixture-machine','readwatch_authorized':True,
                'observed_at_utc':datetime.now(timezone.utc).isoformat(),
                'expires_at_utc':(datetime.now(timezone.utc)+timedelta(seconds=60)).isoformat()}
            with self.assertRaises(ValueError):
                controller.fresh(scope,machine='fixture-machine',collected_at=0,monotonic=lambda:30.01)

    def test_real_controller_readonly_child_receipt_error_retains_wait(self) -> None:
        with tempfile.TemporaryDirectory(dir=A,prefix='command-owner-') as temp:
            root = Path(temp)
            original_write = controller.write

            def fail_created(path: Path, value: model.Object) -> model.FilePin:
                if path.name.endswith('.CREATED.actual.json'):
                    raise OSError('injected source-fixture CREATED receipt error')
                return original_write(path,value)

            with patch.object(controller,'write',side_effect=fail_created),self.assertRaises(ValueError):
                controller.run_owned([sys.executable,'-B','-c','print("harmless readonly child")'],root,'fixture-command',1)
            receipt = json.loads((root/'fixture-command.ORIGINAL-WAIT.actual.json').read_bytes())
            self.assertTrue(receipt['actual_original_popen_wait'])
            self.assertEqual(receipt['returncode'],0)
            self.assertTrue(receipt['errors'])
            self.assertFalse(controller.COMMANDS)
            print(json.dumps({'kind':'real_controller_harmless_child_owner','receipt':receipt}))

    def test_actual_cleanup_predicate_rejects_exit_sources_and_missing_null(self) -> None:
        with tempfile.TemporaryDirectory(dir=A,prefix='cleanup-contract-') as temp:
            root = Path(temp)
            raw = root/'raw';raw.write_bytes(b'fixture-only\n')
            binding_path = root/'binding.json'
            admitted = dict(expected(),synthetic=False)
            binding_path.write_text(json.dumps({'schema':'xar.maintenance.parent_pointer_read.binding.v2',
                'machine_id':'fixture-machine','prepared_only':True,'expected':wire_json(admitted),'root_scope_sha256':'0'*64}),encoding='utf-8')
            actual: model.Object = {'schema':'xar.maintenance.parent_pointer_read.result.v1',
                'machine_id':'fixture-machine','synthetic':False,'cleanup_complete':True,'full_R08':False,
                'entryExact':False,'observation_kind':'post_parent_pointer_read','target_post_read_qualified':True,
                'raw_pin':model.pin(raw),'binding_pin':model.pin(binding_path),'paid_maintenance_raw':None,'payer':None,'cadence':None}
            controller.validate_cleanup(actual,0,raw,binding_path)
            for label in ('exit','raw-pin','missing-null','synthetic','machine'):
                changed = dict(actual)
                code = 0
                if label == 'exit':code=1
                elif label == 'raw-pin':changed['raw_pin']=model.pin(binding_path)
                elif label == 'missing-null':del changed['payer']
                elif label == 'synthetic':changed['synthetic']=True
                else:changed['machine_id']='other'
                with self.subTest(label=label),self.assertRaises(ValueError):
                    controller.validate_cleanup(changed,code,raw,binding_path)

    def test_real_public_selection_external_route_rejects_before_sdk(self) -> None:
        with tempfile.TemporaryDirectory(dir=A,prefix='public-route-') as temp:
            root = Path(temp)
            paths = [*(A/'parent-tools'/name for name in model.CORE_NAMES),*FILES.glob('*.py'),
                D/'tools/ck3_live_run_id.py',D/'ck3_autonomous_player/src/xar_autoplayer/bridge/war_payment_observations_v1.py',
                D/'ck3_autonomous_player/src/xar_autoplayer/bridge/exact_one_day_postcondition.py',PROD/'tools/ck3_live_run_id.py']
            module_names = ('pointer_read_wire','pointer_read_models','pointer_read_owner_binding','pointer_read_admission_models','parent_pointer_read_contract')
            public_names = ('r04_county_entry_window','r04_county_entry','r08_writer_common_adapter','ordinary_save_contract',
                'r08_writer_one_day','pointer_read_public_models','r08_parent_pointer_read_controller','r08_parent_pointer_read_one_day',
                'r10_prepare_adapter','pointer_read_bundle_loader')
            modules = {name:str(A/'parent-tools'/(name+'.py')) for name in module_names}
            modules.update({name:str(FILES/(name+'.py')) for name in public_names})
            index = root/'index.json'
            index.write_text(json.dumps({'schema':model.INDEX_SCHEMA,'files':[model.pin(path) for path in paths],
                'modules':modules}),encoding='utf-8')
            q = root/'pending-q.json'
            q.write_text(json.dumps({'schema':'pending-not-qualified','status':'PENDING','mode':model.MODE}),encoding='utf-8')
            cfg = {'bundle_index_pin':model.pin(index),'qualification_pin':model.pin(q),'observer_pin':model.pin(q),
                'root_scope_path':str(root/'not-issued'),'actor_id':33388,'expected_start_date_raw':1000,
                'parent_tools':str(A/'parent-tools'),'prefix':'r08-pointer-test',
                'deadline_utc':(datetime.now(timezone.utc)+timedelta(seconds=2000)).isoformat(),
                'payment_enable_once_authorized':False,'natural_phase_enable_once_authorized':False}
            context = root/'context.json'
            context.write_text(json.dumps({'case_contract':{'schema':'xar.e04.r10-common-preparation.v1'},
                'case_inputs':{'r08_parent_pointer_read_one_day':cfg}}),encoding='utf-8')
            script = """import importlib.util,json,sys
from pathlib import Path
entry,adapter,context,expected_error=sys.argv[1:]
spec=importlib.util.spec_from_file_location('actual_public_entry_for_source_fixture',entry)
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
s=m.Selection.__new__(m.Selection);s.locations={'repo_root':Path(r'D:/workspace/ck3_eternal_recurrence')};s.adapter_path=Path(adapter)
loaded=s.load_adapter()
try:loaded.validate_contract(json.loads(Path(context).read_bytes()))
except ValueError as e:
 if not expected_error or expected_error not in str(e):raise
 rejected=True
else:
 if expected_error:raise RuntimeError('expected refusal absent')
 rejected=False
print(json.dumps({'actual_selection_method':'Selection.load_adapter','adapter':loaded.__file__,
 'loader':sys.modules['ck3_mod_acceptance_cases.pointer_read_bundle_loader'].__file__,
 'new_save':sys.modules['ck3_mod_acceptance_cases.ordinary_save_contract'].__file__,
 'SDK_requests':0,'qualification_refused':rejected,'source_preflight_only':True,'preloaded_candidate_modules':False}))
"""
            environment = os.environ.copy()
            environment['PYTHONPATH'] = os.pathsep.join((str(PROD/'tools'),str(D/'tools'),str(D/'ck3_autonomous_player/src')))
            real_q = A.parent/'Root/cold-adjudication-a01/POINTER-READ-QUALIFICATION.actual-a01.json'
            real_q_value = json.loads(real_q.read_bytes())
            cases = [('pending-Q',dict(cfg),'New independent pointer qualification required')]
            admitted_cfg = dict(cfg,qualification_pin=model.pin(real_q),observer_pin=real_q_value['observer_pin'])
            cases.append(('actual-new-Q',admitted_cfg,''))
            cases.append(('wrong-tools',dict(admitted_cfg,parent_tools=str(root/'wrong-parent-tools')),'Executed tool not bound'))
            old_q = root/'old-execution-q-fixture.json'
            old_q.write_text(json.dumps({'schema':'xar.maintenance.parent_entry.execution-qualification.v1',
                'status':'SELECTED_EXECUTION_COLD_PASS','mode':'parent-entry-execution-once-v1'}),encoding='utf-8')
            cases.append(('old-execution-Q-fixture',dict(cfg,qualification_pin=model.pin(old_q)),
                'New independent pointer qualification required'))
            missing_index = root/'missing-runtime-index.json'
            missing_value = json.loads(index.read_bytes())
            missing_value['files'] = [ref for ref in missing_value['files'] if Path(ref['path']).name != 'ck3_live_run_id.py']
            missing_index.write_text(json.dumps(missing_value),encoding='utf-8')
            cases.append(('missing-runtime-peer',dict(admitted_cfg,bundle_index_pin=model.pin(missing_index)),
                'Actual runtime dependency lacks an explicit source pin'))
            for label,settings,error in cases:
                case_path = root/('case-inputs-'+label+'.json')
                case_path.write_text(json.dumps({'case_contract':{'schema':'xar.e04.r10-common-preparation.v1'},
                    'case_inputs':{'r08_parent_pointer_read_one_day':settings}}),encoding='utf-8')
                argv = [sys.executable,'-B','-c',script,str(PROD/'tools/ck3_mod_acceptance.py'),str(FILES/'r10_prepare_adapter.py'),str(case_path),error]
                process: subprocess.Popen[bytes] = subprocess.Popen(argv,cwd=root,env=environment,stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
                outcome = check_owner.own_wait(process,None,check_owner.creation_filetime,lambda birth:None)
                self.assertEqual(outcome.code,0,outcome.stderr.decode(errors='replace'))
                report = json.loads(outcome.stdout)
                self.assertEqual(Path(report['adapter']).resolve(),(FILES/'r10_prepare_adapter.py').resolve())
                self.assertEqual(Path(report['new_save']).resolve(),(FILES/'ordinary_save_contract.py').resolve())
                self.assertEqual(report['SDK_requests'],0)
                print(json.dumps({'kind':'real_public_entry_source_route','case':label,'original_pid':outcome.pid,'created':outcome.created,
                    'actual_original_popen_wait':True,'returncode':outcome.code,'report':report}))


if __name__ == '__main__':
    unittest.main(verbosity=2)
