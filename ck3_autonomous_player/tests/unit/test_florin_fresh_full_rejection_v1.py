"""Actual R0004 rejection through the existing strict read consumer and MCP."""
from __future__ import annotations
import asyncio
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

REPO=Path(os.environ.get('CK3_FRESH_ERROR_REPO',Path(__file__).resolve().parents[3]))
CANDIDATE=os.environ.get('CK3_FRESH_ERROR_CANDIDATE')
sys.path[:0]=[str(REPO/'ck3_autonomous_player/src'),str(REPO/'ck3_autonomous_player/tests/unit')]
import xar_autoplayer.bridge
if CANDIDATE:
    name='xar_autoplayer.bridge.native_driver'
    path=Path(CANDIDATE)/'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py'
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
from xar_autoplayer.bridge import native_driver
from xar_autoplayer.bridge.native_driver import _NativeCommandRejectedError
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.mcp_server import create_server
from mcp.server.mcpserver.exceptions import ToolError
from test_florin_fresh_full_public_v1 import SoftwareCase

fixture_root=Path(CANDIDATE) if CANDIDATE else REPO
ACTUAL=json.loads((fixture_root/'ck3_autonomous_player/tests/fixtures/fresh_full1210/rejected-r0004.json').read_text())
ID='fresh-full-3-1b4152dad875'
# Declared candidate serializer contract stimulus, not an observed Native trace.
DIAGNOSTIC={'schema':'xar.native.fresh-full-state-diagnostic/v1','stage':'wait_terminal',
    'submit_result':0,'wait_result':2,'reclaim_result':None,'wait_running_timeouts':0,
    'query_sequence':'9007199254740999','elapsed_ms':'8000','owner_thread_id':22040,
    'pump_epoch_at_start':'18968','pump_epoch_at_end':'18968','wake_attempts':32,
    'wake_succeeded':31,'wake_failed':1,'last_wake_error':5,'fresh_available':False,'queued_wake_interval_ms':250}

class OriginalRejectionMixin(SoftwareCase):
    def original_rejection(self,diagnostic=None):
        driver,endpoint=self.make_driver();driver._request_sequence=2
        def send(request):
            self.assertEqual(request,ACTUAL['request'])
            endpoint.requests.append(deepcopy(request))
            ack=deepcopy(ACTUAL['ack'])
            if diagnostic is not None:ack['fresh_full_state_diagnostic']=deepcopy(diagnostic)
            driver.state.ingest(ack)
        endpoint.send=send
        return driver,endpoint

    def fixed_id(self):
        return patch.object(native_driver.uuid,'uuid4',return_value=SimpleNamespace(hex='1b4152dad87500000000000000000000'))

class ExactNativeRejectionTests(OriginalRejectionMixin,unittest.TestCase):
    def test_actual_native_rejection_preserves_error_id_and_unmodified_envelopes(self):
        driver,endpoint=self.original_rejection()
        with self.fixed_id(),self.assertRaises(_NativeCommandRejectedError) as caught:
            driver.take_fresh_full_snapshot_v1()
        error=caught.exception
        self.assertEqual(error.native_error,'fresh_full_state_read_failed')
        self.assertEqual(error.native_request_id,ID)
        self.assertEqual(error.native_request_frame,ACTUAL['request'])
        self.assertEqual(error.native_command_result_frame,ACTUAL['ack'])
        self.assertIn(ID,str(error));self.assertIn('fresh_full_state_read_failed',str(error))
        self.assertEqual(driver._florin_fresh_full_read_pending_v1,ID)
        with self.assertRaisesRegex(BridgeUnavailableError,'no automatic replay'):
            driver.take_fresh_full_snapshot_v1()
        self.assertEqual(len(endpoint.requests),1)

    def test_malformed_or_nonmatching_negative_ack_does_not_claim_exact_rejection(self):
        changes=[lambda a:a.update(protocol_version=True),lambda a:a.update(error=True),
            lambda a:a.update(error=''),lambda a:a.update(extra='unexpected'),
            lambda a:a.update(request_id='another-read')]
        for change in changes:
            with self.subTest(change=change):
                driver,endpoint=self.make_driver()
                def send(request):
                    endpoint.requests.append(deepcopy(request))
                    ack=deepcopy(ACTUAL['ack']);ack['request_id']=request['request_id'];change(ack)
                    driver.state.ingest(ack)
                endpoint.send=send
                with self.assertRaises(BridgeUnavailableError) as caught:
                    driver.take_fresh_full_snapshot_v1()
                self.assertNotIsInstance(caught.exception,_NativeCommandRejectedError)
                self.assertNotIn('fresh-full-state-read-rejection/v1',str(caught.exception))
                with self.assertRaisesRegex(BridgeUnavailableError,'no automatic replay'):
                    driver.take_fresh_full_snapshot_v1()
                self.assertEqual(len(endpoint.requests),1)

    def test_strict_correlated_success_remains_available(self):
        driver,endpoint=self.make_driver()
        result=driver.take_fresh_full_snapshot_v1()
        self.assertEqual(result['snapshot_id'],'native:11')
        self.assertIsNone(driver._florin_fresh_full_read_pending_v1)
        self.assertEqual(len(endpoint.requests),1)

    def test_optional_declared_diagnostic_preserves_exact_types_and_original_error(self):
        for nullable in (True,False):
            diagnostic=deepcopy(DIAGNOSTIC)
            if nullable:diagnostic.update(submit_result=None,wait_result=None,reclaim_result=None)
            else:diagnostic.update(submit_result=7,wait_result=6,reclaim_result=2)
            driver,endpoint=self.original_rejection(diagnostic)
            with self.fixed_id(),self.assertRaises(_NativeCommandRejectedError) as caught:
                driver.take_fresh_full_snapshot_v1()
            error=caught.exception
            self.assertEqual(error.native_error,'fresh_full_state_read_failed')
            self.assertEqual(error.native_command_result_frame['fresh_full_state_diagnostic'],diagnostic)
            self.assertEqual(error.native_raw_return_receipt['fresh_full_state_diagnostic'],diagnostic)
            self.assertIn('9007199254740999',str(error))
            self.assertEqual(len(endpoint.requests),1)

    def test_malformed_optional_diagnostic_does_not_claim_exact_rejection(self):
        changes=[lambda d:d.update(stage='invented'),lambda d:d.update(extra=0),lambda d:d.pop('wait_result'),
            lambda d:d.update(submit_result=True),lambda d:d.update(wait_result=7),lambda d:d.update(reclaim_result=3),
            lambda d:d.update(query_sequence=9007199254740999),lambda d:d.update(query_sequence='01'),
            lambda d:d.update(elapsed_ms=str(2**64)),lambda d:d.update(pump_epoch_at_start='-1'),
            lambda d:d.update(owner_thread_id=2**32),lambda d:d.update(wake_attempts=True),
            lambda d:d.update(fresh_available=0),lambda d:d.update(queued_wake_interval_ms='250')]
        for change in changes:
            with self.subTest(change=change):
                diagnostic=deepcopy(DIAGNOSTIC);change(diagnostic)
                driver,endpoint=self.original_rejection(diagnostic)
                with self.fixed_id(),self.assertRaises(BridgeUnavailableError) as caught:
                    driver.take_fresh_full_snapshot_v1()
                self.assertNotIsInstance(caught.exception,_NativeCommandRejectedError)
                self.assertEqual(len(endpoint.requests),1)

class PublicOriginalRejectionTests(OriginalRejectionMixin,unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):asyncio.get_running_loop().set_debug(False)

    async def test_actual_rejection_error_and_request_id_survive_registered_public_tool(self):
        driver,endpoint=self.original_rejection();server=create_server(driver)
        with self.fixed_id(),self.assertRaises(ToolError) as caught:
            await server.call_tool('ck3_take_fresh_full_snapshot_v1',{})
        self.assertIn('fresh_full_state_read_failed',str(caught.exception))
        self.assertIn(ID,str(caught.exception))
        self.assertNotIn('exact successful ACK',str(caught.exception))
        with self.assertRaisesRegex(ToolError,'no automatic replay'):
            await server.call_tool('ck3_take_fresh_full_snapshot_v1',{})
        self.assertEqual(len(endpoint.requests),1)

    async def test_optional_declared_diagnostic_survives_public_error_without_read_credit(self):
        driver,endpoint=self.original_rejection(DIAGNOSTIC);server=create_server(driver)
        with self.fixed_id(),self.assertRaises(ToolError) as caught:
            await server.call_tool('ck3_take_fresh_full_snapshot_v1',{})
        for value in (ID,'fresh_full_state_read_failed','xar.native.fresh-full-state-diagnostic/v1','9007199254740999'):
            self.assertIn(value,str(caught.exception))
        self.assertEqual(driver._florin_fresh_full_read_pending_v1,ID)
        self.assertEqual(len(endpoint.requests),1)

if __name__=='__main__':unittest.main()
