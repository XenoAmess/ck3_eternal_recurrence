"""No game: real native-driver FakeEndpoint file + shared cleanup regressions."""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from collections.abc import Mapping

from ck3_mod_acceptance_cases import r08_writer_one_day as actor
from ck3_mod_acceptance_cases.ordinary_save_contract import (
    SaveUnconfirmed, begin_save, verify_save, retained_client, obj)

ROOT=Path(__file__).resolve().parents[1]

def fixture_root(script: Path) -> Path:
    explicit=os.environ.get('XAR_ORDINARY_SAVE_TEST_ROOT')
    return Path(explicit).resolve() if explicit else script.resolve().parents[1]/'tmp'
DATE=53149080

class Client:
    def __init__(self) -> None:
        self._handle=object();self._process={'pid':4242};self.closed:list[str]=[]
    def normal_close(self, disposition: str) -> str:
        self.closed.append(disposition);return disposition

def frame(state: Path, revision: int=6) -> dict[str,object]:
    return dict(backend_id='native-headless',source='injected-dll-named-pipe',
        episode_projection='native_campaign',episode_run_id=None,episode_character_id=None,
        map_ready=True,paused=True,date_raw=DATE,local_player_id=1,
        played_character=dict(character_id=33388,alive=True,source='native'),
        diagnostics=dict(connected=True,bridge_pid=4242,connection_generation=1,pipe_name='fixture-pipe'),
        revision=revision+1,native_revision=revision,snapshot_id='native:'+str(revision),
        managed_campaign_run_binding=dict(run_id='synthetic-run',state_dir=str(state),bridge_pipe='fixture-pipe',
            host_path='synthetic-managed-host.py',frozen_argv_sha256='a'*64))

def result(state: Path) -> dict[str,object]:
    return dict(step='save-checkpoint',accepted=True,backend_id='native-headless',
        checkpoint=dict(status='saved',path=str(state/'profile'/'save games'/'xar_checkpoint.ck3'),
            name='xar_checkpoint.ck3',size=23,sha256='b'*64,date_raw=DATE,
            episode_projection='native_campaign',succession_lifecycle=None,episode_run_id=None,
            episode_character_id=None,strategy='native-autosave-command-v1'),
        submission=dict(sequence=1,date_raw=DATE),
        materialization=dict(available=True,save_dir=str(state/'profile'/'save games'),mtime_ns=123),
        driver_state_replace_receipt=dict(status='unconfirmed',reason='save_binding_mismatch'))

def change(row: dict[str,object], section: str, key: str, value: object) -> None:
    updated=dict(obj(row[section],section));updated[key]=value;row[section]=updated

class Endpoint:
    def __init__(self, state: Path) -> None:
        self.state=state;self.client=Client();self.calls:list[str]=[]
        self.before=frame(state);self.after=frame(state,7);self.saved=result(state)
        self.raise_after=False;self.raise_save=False
    def snapshot(self, label: str) -> Mapping[str,object]:
        self.calls.append(label)
        if label=='Save-independent-after' and self.raise_after:raise RuntimeError('independent after unavailable')
        return self.before if label=='Save-before' else self.after
    def call(self, label: str, tool: str, args: dict[str,object]) -> Mapping[str,object]:
        self.calls.append(label)
        if label=='Save-once':
            if self.raise_save:raise TimeoutError('submission unknown')
            return self.saved
        return {}
    def payment(self, label: str, mode: str) -> Mapping[str,object]:
        self.calls.append(label)
        return {'sampling':dict(available=True,capture_enabled=False,busy=False,clear_completed=True,
            active_captures=0,retained_records=0)}
    def cleanup(self, *, clock_error: bool=False) -> tuple[dict[str,object],list[str],int|None,actor.CloseGate]:
        gate=actor.CloseGate(self.client)
        def clock(*args: object, **kwargs: object) -> dict[str,object]:
            if clock_error:raise ValueError('clock unknown')
            return {'state':'idle'}
        def sampling(*args: object, **kwargs: object) -> dict[str,object]:
            return {str(i):dict(installed=True,available=True,capture_enabled=False,busy=False,
                clear_completed=True,active_captures=0,retained_records=0) for i in range(9)}
        with patch.object(actor,'cleanup_clock',clock),patch.object(actor,'sampling_control',sampling):
            out,errors,days=actor.cleanup_writer_window(self.call,self.snapshot,self.payment,gate,
                observer_claimed=False,expected_start_date_raw=DATE-24)
        return dict(out),errors,days,gate

class OrdinarySaveTests(unittest.TestCase):
    def setUp(self) -> None:
        root=fixture_root(Path(__file__));root.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=root);self.state=Path(self.temp.name)
    def tearDown(self) -> None:self.temp.cleanup()
    def test_success_opens_shared_close_and_preserves_one_life_diagnostic(self) -> None:
        e=Endpoint(self.state);raw=copy.deepcopy(e.saved)
        out,errors,days,gate=e.cleanup()
        self.assertEqual(errors,[]);self.assertEqual(days,1);self.assertTrue(out['Save']);self.assertTrue(gate.save_verified)
        self.assertEqual(e.saved,raw);self.assertEqual(out['Save_result'],raw)
        proof=obj(out['ordinary_save_proof'],'proof');self.assertFalse(proof['one_life_identity_proven'])
        self.assertFalse(proof['consumer_rehashed_file']);self.assertTrue(proof['native_frame_advanced'])
        self.assertEqual(e.client.normal_close('normal'),'normal')
        self.assertEqual(e.calls.count('Save-once'),1)
    def test_independent_after_failure_preserves_received_save_before_error(self) -> None:
        e=Endpoint(self.state);e.raise_after=True
        out,errors,days,gate=e.cleanup()
        self.assertEqual(out['Save_result'],e.saved);self.assertFalse(out['Save']);self.assertFalse(gate.save_verified)
        self.assertTrue(errors);self.assertIsNone(days);self.assertEqual(e.calls.count('Save-once'),1)
        with self.assertRaises(Exception):e.client.normal_close('normal')
    def test_unknown_save_not_replayed_and_after_not_requested(self) -> None:
        e=Endpoint(self.state);e.raise_save=True
        out,errors,_,gate=e.cleanup()
        self.assertFalse(out['Save']);self.assertFalse(gate.save_verified);self.assertTrue(errors)
        self.assertNotIn('Save_result',out);self.assertNotIn('Save-independent-after',e.calls)
        self.assertEqual(e.calls.count('Save-once'),1)
    def test_before_native_missing_prevents_save_despite_managed_mapping(self) -> None:
        e=Endpoint(self.state);e.before.pop('diagnostics')
        out,errors,_,gate=e.cleanup()
        self.assertFalse(out['Save']);self.assertFalse(gate.save_verified);self.assertTrue(errors)
        self.assertNotIn('Save-once',e.calls)
    def test_independent_owner_drift_blocks_close(self) -> None:
        variants=[('actor',lambda x:change(x,'played_character','character_id',33389)),
            ('pid',lambda x:change(x,'diagnostics','bridge_pid',4243)),
            ('generation',lambda x:change(x,'diagnostics','connection_generation',2)),
            ('pipe',lambda x:change(x,'diagnostics','pipe_name','other')),
            ('date',lambda x:x.update(date_raw=DATE+24)),('paused',lambda x:x.update(paused=False)),
            ('run',lambda x:change(x,'managed_campaign_run_binding','run_id','other'))]
        for label,mutate in variants:
            with self.subTest(label=label):
                e=Endpoint(self.state);mutate(e.after);out,errors,_,gate=e.cleanup()
                self.assertFalse(out['Save']);self.assertFalse(gate.save_verified);self.assertTrue(errors)
                self.assertEqual(e.calls.count('Save-once'),1)
    def test_strict_native_fields_reject_bool_float_and_missing(self) -> None:
        for key,value in [('local_player_id',True),('native_revision',6.0),('date_raw',False)]:
            with self.subTest(key=key):
                before=frame(self.state);before[key]=value
                with self.assertRaises(SaveUnconfirmed):begin_save(before,retained_client(Client()))
    def test_materialization_failures_never_verify(self) -> None:
        for key,value in [('status','submitted'),('size',0),('size',True),('sha256','bad'),
                ('date_raw',DATE+24),('path',str(self.state/'outside.ck3')),('episode_run_id','fake')]:
            with self.subTest(key=key,value=value):
                e=Endpoint(self.state);checkpoint=dict(obj(e.saved['checkpoint'],'c'));checkpoint[key]=value;e.saved['checkpoint']=checkpoint
                out,errors,_,gate=e.cleanup();self.assertFalse(out['Save']);self.assertFalse(gate.save_verified);self.assertTrue(errors)
    def test_same_native_sample_allowed_without_claiming_new_frame(self) -> None:
        e=Endpoint(self.state);e.after=copy.deepcopy(e.before)
        out,errors,_,_=e.cleanup();self.assertEqual(errors,[])
        proof=obj(out['ordinary_save_proof'],'proof');self.assertFalse(proof['native_frame_advanced'])
        self.assertTrue(proof['independent_after_request'])
    def test_retained_client_or_handle_change_rejected(self) -> None:
        c=Client();start=begin_save(frame(self.state),retained_client(c));c._handle=object()
        with self.assertRaises(SaveUnconfirmed):verify_save(start,result(self.state),frame(self.state,7),retained_client(c))
        with self.assertRaises(SaveUnconfirmed):verify_save(start,result(self.state),frame(self.state,7),retained_client(Client()))
    def test_clock_failure_keeps_independent_off_but_no_save(self) -> None:
        e=Endpoint(self.state);out,errors,_,gate=e.cleanup(clock_error=True)
        self.assertTrue(out['OFFclear']);self.assertTrue(errors);self.assertFalse(gate.off_clear)
        self.assertIn('payment-independent-off',e.calls);self.assertNotIn('Save-once',e.calls)
    def test_canonical_fixture_root_and_explicit_external_root(self) -> None:
        with patch.dict(os.environ,{},clear=True):
            self.assertEqual(fixture_root(Path('C:/checkout/tools/test_ck3_ordinary_save_contract.py')),
                Path('C:/checkout/tmp'))
        with patch.dict(os.environ,{'XAR_ORDINARY_SAVE_TEST_ROOT':str(self.state)},clear=True):
            self.assertEqual(fixture_root(Path('C:/checkout/tools/test_ck3_ordinary_save_contract.py')),self.state.resolve())
    def test_checkpoint_nullable_fields_missing_rejected(self) -> None:
        for key in ('succession_lifecycle','episode_run_id','episode_character_id'):
            with self.subTest(key=key):
                e=Endpoint(self.state);checkpoint=dict(obj(e.saved['checkpoint'],'checkpoint'))
                checkpoint.pop(key);e.saved['checkpoint']=checkpoint
                out,errors,_,gate=e.cleanup()
                self.assertFalse(out['Save']);self.assertFalse(gate.save_verified);self.assertTrue(errors)
                self.assertEqual(obj(out['ordinary_save_proof'],'proof')['reason_code'],'projection_fields_missing')
                self.assertEqual(e.calls.count('Save-once'),1)
    def test_snapshot_missing_and_null_distinguished_without_new_producer_fields(self) -> None:
        e=Endpoint(self.state);e.before.pop('episode_character_id');e.after.pop('episode_run_id')
        out,errors,_,gate=e.cleanup();self.assertEqual(errors,[]);self.assertTrue(gate.save_verified)
        proof=obj(out['ordinary_save_proof'],'proof')
        self.assertEqual(proof['before_episode_identity_representation'],
            {'episode_run_id':'explicit_null','episode_character_id':'missing'})
        self.assertEqual(proof['after_episode_identity_representation'],
            {'episode_run_id':'missing','episode_character_id':'explicit_null'})
        for key in ('episode_run_id','episode_character_id'):
            for value in (False,0,'one-life'):
                with self.subTest(key=key,value=value):
                    bad=frame(self.state);bad[key]=value
                    with self.assertRaises(SaveUnconfirmed):begin_save(bad,retained_client(Client()))
    def test_new_proof_numbers_reject_unsafe_integer_and_u32_overflow(self) -> None:
        unsafe=1<<53
        for key in ('date_raw','revision','native_revision'):
            with self.subTest(key=key):
                bad=frame(self.state);bad[key]=unsafe
                with self.assertRaises(SaveUnconfirmed):begin_save(bad,retained_client(Client()))
        for key,value in [('bridge_pid',1<<32),('connection_generation',unsafe)]:
            with self.subTest(key=key):
                bad=frame(self.state);change(bad,'diagnostics',key,value)
                with self.assertRaises(SaveUnconfirmed):begin_save(bad,retained_client(Client()))
        for section,key in [('checkpoint','size'),('checkpoint','date_raw'),('submission','sequence')]:
            with self.subTest(section=section,key=key):
                e=Endpoint(self.state);change(e.saved,section,key,unsafe)
                out,errors,_,gate=e.cleanup();self.assertFalse(out['Save']);self.assertFalse(gate.save_verified);self.assertTrue(errors)
        good=frame(self.state);good['revision']=(1<<53)-1
        begin_save(good,retained_client(Client()))
    def test_legacy_large_mtime_not_migrated_into_new_proof(self) -> None:
        e=Endpoint(self.state);legacy=(1<<63)-1;change(e.saved,'materialization','mtime_ns',legacy)
        out,errors,_,gate=e.cleanup();self.assertEqual(errors,[]);self.assertTrue(gate.save_verified)
        self.assertEqual(obj(obj(out['Save_result'],'raw')['materialization'],'mat')['mtime_ns'],legacy)
        self.assertNotIn('mtime_ns',json.dumps(out['ordinary_save_proof']))
    def test_real_existing_driver_materializes_small_file_and_brackets(self) -> None:
        # Import actual frozen driver/test transport; no monkeypatch of Save logic.
        from test_native_bridge_driver import FakeEndpoint,_hello,_snapshot
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        save_dir=self.state/'profile'/'save games';save_dir.mkdir(parents=True)
        file=save_dir/'xar_checkpoint.ck3';payload=b'ordinary synthetic checkpoint\n'
        endpoint=FakeEndpoint();driver=NativeHeadlessGameplayDriver(endpoint.pipe_name,endpoint=endpoint,
            episode_projection='native_campaign',state_dir=self.state,save_dir=save_dir,
            checkpoint_timeout_seconds=1.0,checkpoint_poll_interval_seconds=.005)
        endpoint.publish(_hello('game.state.snapshot','game.command.save-checkpoint'))
        def publish(revision: int) -> None:
            native=_snapshot(revision,date_raw=DATE,played_character={'character_id':33388,'alive':True})
            native['state']['local_player_id']=1
            endpoint.publish(native)
        publish(6)
        requests:list[str]=[]
        def answer(request: dict[str,object]) -> None:
            if request.get('type')!='execute_step':return
            requests.append(str(request.get('step')));file.write_bytes(payload)
            endpoint.publish(dict(type='command_result',protocol_version=1,request_id=request['request_id'],ok=True,
                result=dict(step='save-checkpoint',accepted=True,status='submitted',submission=dict(
                    sequence=1,requested_save_name='xar_checkpoint',date_raw=DATE))))
        endpoint.send_hook=answer
        def managed_snapshot() -> dict[str,object]:
            snap=driver.take_snapshot()
            # The existing managed host adds this static mapping, not native owner.
            snap['managed_campaign_run_binding']=dict(run_id='synthetic-run',state_dir=str(self.state),
                bridge_pipe=endpoint.pipe_name,host_path='synthetic-managed-host.py',frozen_argv_sha256='a'*64)
            return snap
        try:
            class ActualEndpoint(Endpoint):
                def snapshot(self, label: str) -> Mapping[str,object]:
                    if label=='Save-independent-after':publish(7)
                    return managed_snapshot()
                def call(self, label: str, tool: str, args: dict[str,object]) -> Mapping[str,object]:
                    self.calls.append(label)
                    if label=='Save-once':return driver.execute_step('save-checkpoint',expected_revision=args['expected_revision'])
                    return {}
            e=ActualEndpoint(self.state)
            cleanup,errors,days,gate=e.cleanup()
            self.assertEqual(errors,[]);self.assertTrue(cleanup['Save']);self.assertTrue(gate.save_verified)
            self.assertEqual(e.client.normal_close('normal'),'normal')
            proof=obj(cleanup['ordinary_save_proof'],'proof');saved=obj(cleanup['Save_result'],'Save result')
            before_repr=obj(proof['before_episode_identity_representation'],'before representation')
            self.assertEqual(before_repr['episode_character_id'],'missing')
            self.assertEqual(requests,['save-checkpoint']);self.assertEqual(file.read_bytes(),payload)
            facts=obj(proof['file'],'file');self.assertEqual(facts['bytes'],len(payload));self.assertEqual(facts['sha256'],hashlib.sha256(payload).hexdigest())
            self.assertEqual(obj(saved['driver_state_replace_receipt'],'receipt')['status'],'unconfirmed')
            self.assertIsNone(obj(saved['checkpoint'],'checkpoint')['episode_run_id']);self.assertIsNone(obj(saved['checkpoint'],'checkpoint')['episode_character_id'])
            print('ACTUAL_FAKE_ENDPOINT_FILE',json.dumps(dict(proof=proof,driver_state_replace_receipt=saved['driver_state_replace_receipt']),sort_keys=True))
        finally:driver.close()

if __name__=='__main__':unittest.main(verbosity=2)
