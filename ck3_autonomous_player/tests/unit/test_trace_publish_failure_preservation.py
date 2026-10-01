"""Offline parser-return preservation; no endpoint/game/desktop is opened."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'src'))
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, _NativeCommandRejectedError

BEGIN='experimental-combat-phase-event-trace-begin-v1'
FINISH='experimental-combat-phase-event-trace-finish-v1'

class Fixture(NativeHeadlessGameplayDriver):
    def __init__(self, folder, frame):
        self.state_dir=folder;self.frame=frame;self.sent=[];self._request_sequence=0
        self.command_timeout_seconds=1
        self.endpoint=SimpleNamespace(send=self.sent.append)
        self.state=SimpleNamespace(wait_for_command_result=self.return_frame,capabilities=self.capabilities)
    def capabilities(self):
        return {'action_steps':[BEGIN,FINISH,'offline-unrelated-step'],'bridge_capabilities':[]}
    def take_snapshot(self):
        return {'revision':4,'native_revision':3,'date_raw':53146872,'paused':True}
    def take_internal_semantic_snapshot(self):
        return self.take_snapshot()
    def return_frame(self, request_id, timeout):
        return {**copy.deepcopy(self.frame),'request_id':request_id}

class TraceFailurePreservationTests(unittest.TestCase):
    def test_begin_finish_original_red_preserved_before_exception(self):
        for step in (BEGIN,FINISH):
            with self.subTest(step=step),tempfile.TemporaryDirectory() as temp:
                raw={'type':'command_result','ok':False,'error':'experimental trace managed DTO unavailable',
                     'trace_publish_diagnostic':{'failure_gate':'managed_wire_cap','assembled_output_bytes':1234567,
                        'managed_cap_bytes':921600,'drain_failure_flags':1040,'scoped_failure_flags':32}}
                driver=Fixture(Path(temp),raw)
                with self.assertRaises(_NativeCommandRejectedError) as captured:
                    driver._execute_primitive_step(step,expected_revision=4,request_fields={'combat_id':16777218})
                error=captured.exception;receipt=error.native_raw_return_receipt
                data=Path(receipt['path']).read_bytes();saved=json.loads(data)
                self.assertFalse(saved['original_parsed_command_result']['ok'])
                self.assertEqual(saved['original_parsed_command_result']['error'],raw['error'])
                self.assertEqual(saved['original_parsed_command_result']['trace_publish_diagnostic'],raw['trace_publish_diagnostic'])
                self.assertEqual(saved['request'],driver.sent[0])
                self.assertEqual(saved['actual_pre_submission_snapshot'],driver.take_snapshot())
                self.assertFalse(saved['wire_bytes_preserved'])
                self.assertEqual(receipt['bytes'],len(data))
                self.assertEqual(receipt['sha256'],hashlib.sha256(data).hexdigest())
                self.assertEqual(error.native_error,raw['error'])
                encoded_receipt=str(error).split('; original parsed return receipt=',1)[1]
                self.assertEqual(json.loads(encoded_receipt),receipt)
    def test_create_only_collision_never_changes_original(self):
        with tempfile.TemporaryDirectory() as temp:
            driver=Fixture(Path(temp),{});request={'step':FINISH};raw={'ok':False,'error':'original'}
            with patch('xar_autoplayer.bridge.native_driver.uuid.uuid4',return_value=SimpleNamespace(hex='fixed-offline')):
                receipt=driver._preserve_private_trace_native_frame(request,raw,driver.take_snapshot())
                data=Path(receipt['path']).read_bytes()
                with self.assertRaises(FileExistsError):
                    driver._preserve_private_trace_native_frame(request,{'ok':True},driver.take_snapshot())
                self.assertEqual(data,Path(receipt['path']).read_bytes())
    def test_evidence_directory_required_before_dispatch(self):
        with tempfile.TemporaryDirectory() as temp:
            driver=Fixture(Path(temp),{'ok':False,'error':'original'})
            evidence_folder=driver._native_driver_state_path().parent
            evidence_folder.mkdir(parents=True,exist_ok=True)
            (evidence_folder/'combat-trace-native-results').write_text('existing-file')
            with self.assertRaises(FileExistsError):driver._execute_primitive_step(FINISH,expected_revision=4)
            self.assertEqual(driver.sent,[])
    def test_unrelated_step_retains_original_error_without_trace_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            driver=Fixture(Path(temp),{'ok':False,'error':'unrelated native refusal'})
            with self.assertRaises(_NativeCommandRejectedError) as captured:
                driver._execute_primitive_step('offline-unrelated-step',expected_revision=4)
            self.assertIsNone(captured.exception.native_raw_return_receipt)
            self.assertEqual(str(captured.exception),'native gameplay step failed: unrelated native refusal')
            self.assertFalse((Path(temp)/'combat-trace-native-results').exists())
    def test_success_stays_original_status_with_additive_unvalidated_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            raw={'ok':True,'result':{'status':'trace_unavailable','failure_flags':1040}}
            driver=Fixture(Path(temp),raw)
            value=driver._execute_primitive_step(FINISH,expected_revision=4,internal_semantic_snapshot=True)
            self.assertEqual(value['status'],'trace_unavailable');self.assertEqual(value['failure_flags'],1040)
            receipt=value['native_trace_raw_return_receipt']
            saved=json.loads(Path(receipt['path']).read_bytes())
            self.assertTrue(saved['original_parsed_command_result']['ok'])
            self.assertEqual(saved['validation_state'],'unvalidated')

if __name__=='__main__':unittest.main()
