"""Standalone experimental WAL tests; no runtime owner or external evidence path."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
def repo_root():
    override=os.environ.get('XAR_WAL_PUBLIC_REPO')
    if override:
        return Path(override).resolve()
    for parent in HERE.parents:
        if (parent/'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py').is_file():
            return parent
    raise RuntimeError('set XAR_WAL_PUBLIC_REPO to the checkout under test')

REPO=repo_root()
SRC=REPO/'ck3_autonomous_player/src'
sys.path.insert(0,str(SRC))

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    sys.modules[name]=mod
    spec.loader.exec_module(mod)
    return mod

wal=load('xar_autoplayer.bridge.driver_state_wal_v1',HERE/'driver_state_wal_v1.py')
from xar_autoplayer.bridge.driver_state_history_json import DriverStateHistoryJsonCache
from xar_autoplayer.environment import write_bytes_atomic
from xar_autoplayer.bridge.war_contract import parse_advance_route_contact_horizon_step

def patched_modules(root):
    for relative in ('bridge/native_driver.py','native_session.py'):
        target=root/'ck3_autonomous_player/src/xar_autoplayer'/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(SRC/'xar_autoplayer'/relative,target)
    for filename in ('bridge-native_driver.py.patch','native_session.py.patch'):
        try:
            subprocess.run(['git','apply',str(HERE/filename)],cwd=root,check=True,
                           stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        except subprocess.CalledProcessError as error:
            raise RuntimeError(
                f'experimental WAL git apply failed: {filename}\n'
                f'stdout:\n{error.stdout}\nstderr:\n{error.stderr}'
            ) from error
    driver=load('xar_autoplayer.bridge.native_driver_wal_portable',
                root/'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py')
    cold=load('xar_autoplayer.native_session_wal_portable',
              root/'ck3_autonomous_player/src/xar_autoplayer/native_session.py')
    return driver,cold

def synthetic_state():
    return {'format_version':2,'pipe_name':r'\\.\pipe\xar-wal-test',
            'bridge_pid':12345,'episode_character_id':7,
            'episode_run_id':'native-7-wal-test',
            'last_checkpoint':None,'command_history':[],
            'rollback_war_failure':None,'managed_restore_transaction':None,
            'succession_expectation':None,'succession_lifecycle':None,
            'campaign_goal':None,'rollback_war_failures':[]}

def fake_driver(module,state_dir):
    state=synthetic_state()
    obj=module.NativeHeadlessGameplayDriver.__new__(module.NativeHeadlessGameplayDriver)
    obj.state_dir=state_dir
    obj.pipe_name=state['pipe_name']
    obj._driver_state_lock=threading.RLock()
    obj._history_lock=obj._driver_state_lock
    obj._driver_state_write_lock=threading.Lock()
    obj._driver_state_dirty=False
    obj._driver_state_error=None
    obj._driver_state_history_json=DriverStateHistoryJsonCache()
    obj.allow_driver_state_wal_v1=True
    obj._driver_state_wal_document=None
    obj._driver_state_wal_committed_rows=0
    obj._driver_state_wal_replay_status=None
    obj._driver_state_wal_base_stat=None
    obj._driver_state_wal_base_sha256=None
    obj._driver_state_wal_base_version=None
    obj._session_bridge_pid=state['bridge_pid']
    obj._episode_character_id=state['episode_character_id']
    obj._episode_run_id=state['episode_run_id']
    obj._last_checkpoint=None
    obj._command_history=[]
    obj._rollback_war_failures=[]
    obj._rollback_war_failures_migration_required=False
    obj._managed_restore_transaction=None
    obj._succession_expectation=None
    obj._succession_lifecycle=None
    obj._campaign_goal=None
    obj._natural_successor_persistence_unconfirmed=False
    return obj

class PortableWal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.root=Path(cls.temp.name)
        cls.driver_module,cls.cold_module=patched_modules(cls.root)
        cls.fixture=json.loads((HERE/'actual_route_horizon_fixture.json').read_text(encoding='utf-8'))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_default_off_and_route_exact_delta(self):
        with tempfile.TemporaryDirectory() as tmp:
            driver=fake_driver(self.driver_module,Path(tmp))
            driver.allow_driver_state_wal_v1=False
            driver._persist_driver_state()
            step=self.fixture['selected_step']
            result=self.fixture['result']
            self.assertIsNotNone(parse_advance_route_contact_horizon_step(step))
            driver._record_command(step,ok=True,result=result)
            base=driver._native_driver_state_path()
            self.assertEqual(json.loads(base.read_bytes())['format_version'],wal.FULL_VERSION)
            self.assertFalse(base.with_name(wal.FILENAME).exists())
            driver.allow_driver_state_wal_v1=True
            driver._record_command(step,ok=True,result=result)
            self.assertEqual(json.loads(base.read_bytes())['format_version'],wal.SEALED_VERSION)
            replayed,status=wal.load_pair(base)
            self.assertEqual(status,'replayed')
            self.assertEqual(replayed['command_history'][-1]['command'],step)

    def test_strict_route_mutations_fall_back_to_full(self):
        step=self.fixture['selected_step']
        result=self.fixture['result']
        self.assertTrue(wal.eligible_route_horizon_delta(step,result,parsed_step_valid=True))
        for key,value in (('elapsed_days',0),('ending_date_raw',result['ending_date_raw']+24),
                          ('paused',False),('active_event',{'id':1}),('progress_status','interrupted')):
            changed=copy.deepcopy(result);changed[key]=value
            self.assertFalse(wal.eligible_route_horizon_delta(step,changed,parsed_step_valid=True))
        for key,value in (('trigger_reasons',['contact']),('overshoot_days',1),
                          ('completed_daily_ticks',2),('terminal_observed',True)):
            changed=copy.deepcopy(result);changed['exact_day_native_clock']['stopped'][key]=value
            self.assertFalse(wal.eligible_route_horizon_delta(step,changed,parsed_step_valid=True))

    def test_second_append_does_not_read_base_stat_mutation_rejects(self):
        with tempfile.TemporaryDirectory() as tmp:
            driver=fake_driver(self.driver_module,Path(tmp))
            driver._persist_driver_state()
            driver._record_command('life-advance-one-day',ok=True,result={'step':'life-advance-one-day'})
            base=driver._native_driver_state_path()
            journal=base.with_name(wal.FILENAME)
            original=Path.read_bytes
            def guarded(path):
                if path==base: raise AssertionError('re-read sealed base')
                return original(path)
            with patch.object(Path,'read_bytes',guarded):
                driver._record_command('life-advance-one-day',ok=True,result={'step':'life-advance-one-day'})
            before=journal.read_bytes()
            stat=base.stat()
            os.utime(base,ns=(stat.st_atime_ns,stat.st_mtime_ns+1_000_000_000))
            driver._record_command('life-advance-one-day',ok=True,result={'step':'life-advance-one-day'})
            self.assertEqual(journal.read_bytes(),before)
            self.assertIn('base identity changed',driver._driver_state_error)

    def test_reader_rejects_sealed_base_then_full_barrier_and_materializer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            source=root/'source'
            driver=fake_driver(self.driver_module,source)
            driver._persist_driver_state()
            driver._record_command('life-advance-one-day',ok=True,result={'step':'life-advance-one-day'})
            base=driver._native_driver_state_path()
            journal=base.with_name(wal.FILENAME)
            with self.assertRaisesRegex(self.cold_module.AgentError,'committed daily journal'):
                self.cold_module.validate_cold_start_checkpoint_for_pipe(
                    SimpleNamespace(state_dir=source),driver.pipe_name)
            with self.assertRaisesRegex(wal.JournalInvalid,'missing its journal'):
                wal.replay(base.read_bytes(),None)
            with self.assertRaisesRegex(wal.JournalInvalid,'closed SDK owner'):
                wal.materialize_closed_directory(source,root/'materialized',owner_closed=False,
                    expected_base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),
                    expected_journal_sha256=hashlib.sha256(journal.read_bytes()).hexdigest())
            receipt=wal.materialize_closed_directory(source,root/'materialized',owner_closed=True,
                expected_base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),
                expected_journal_sha256=hashlib.sha256(journal.read_bytes()).hexdigest())
            self.assertEqual(receipt['status'],'materialized_v2')
            self.assertEqual(wal.load_pair(root/'materialized/native-session/driver-state.json')[1],'base_only')
            driver._persist_driver_state() # Same full-state barrier as SAVE/normal close.
            self.assertEqual(wal.load_pair(base)[1],'base_only')
            self.assertFalse(journal.exists())

    def test_missing_reordered_truncated_foreign_base_never_replays(self):
        state=synthetic_state()
        base=wal.sealed_base_bytes(wal.full_state_bytes(state))
        header=wal.new_journal(base,json.loads(base))
        fields={k:v for k,v in state.items() if k!='command_history'}
        row={'index':1,'command':'life-advance-one-day','ok':True}
        journal=wal.append_delta(header,[row],fields)
        encoded=json.dumps(journal).encode()
        self.assertEqual(wal.replay(base,encoded)[0]['command_history'],[row])
        cases=[]
        bad=copy.deepcopy(journal);bad['entries'][0]['sequence']=2;cases.append((base,json.dumps(bad).encode()))
        bad=copy.deepcopy(journal);bad['entries'][0]['history_rows'][0]['index']=2;cases.append((base,json.dumps(bad).encode()))
        bad=copy.deepcopy(journal);bad['base_sha256']='0'*64;cases.append((base,json.dumps(bad).encode()))
        cases.extend([(base,encoded[:-1]),(base+b' ',encoded),(base,None)])
        for wrong_base,wrong_journal in cases:
            with self.subTest(wrong_journal=wrong_journal is None):
                with self.assertRaises(wal.JournalInvalid): wal.replay(wrong_base,wrong_journal)

    def test_save_receipt_and_normal_close_are_full_barriers(self):
        with tempfile.TemporaryDirectory() as tmp:
            driver=fake_driver(self.driver_module,Path(tmp))
            driver._persist_driver_state()
            driver._record_command('life-advance-one-day',ok=True,result={'step':'life-advance-one-day'})
            base=driver._native_driver_state_path()
            checkpoint={'history_index':len(driver._command_history)+1,
                        'pipe_name':driver.pipe_name,'bridge_pid':driver._session_bridge_pid,
                        'episode_character_id':driver._episode_character_id,
                        'episode_run_id':driver._episode_run_id}
            driver._last_checkpoint=copy.deepcopy(checkpoint)
            receipt=driver._record_command('save-checkpoint',ok=True,result={'checkpoint':checkpoint})
            self.assertEqual(receipt['status'],'replaced')
            self.assertTrue(receipt['save_binding_verified'])
            self.assertEqual(wal.load_pair(base)[1],'base_only')
            driver._record_command('life-advance-one-day',ok=True,result={'step':'life-advance-one-day'})
            observed=[]
            driver.endpoint=SimpleNamespace(close=lambda:observed.append(
                (base.with_name(wal.FILENAME).exists(),json.loads(base.read_bytes())['format_version'])))
            with patch('xar_autoplayer.bridge.normal_exit_pending_observer_v1.dispose_normal_exit_observer_v1'):
                driver.close()
            self.assertEqual(observed,[(False,wal.FULL_VERSION)])

if __name__=='__main__': unittest.main()
