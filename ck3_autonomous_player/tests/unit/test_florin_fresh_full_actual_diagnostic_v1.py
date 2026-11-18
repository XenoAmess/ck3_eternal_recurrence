"""Actual Q09 C++ diagnostic operands through the strict shared SDK and MCP.

Fixture bytes are the untouched handler stdout packets. Only outer request_id
is rebound in the software endpoint to the SDK-generated readonly request.
"""
from __future__ import annotations
import asyncio
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest

REPO=Path(os.environ.get('CK3_DIAGNOSTIC_CI_REPO',Path(__file__).resolve().parents[3]))
sys.path[:0]=[str(REPO/'ck3_autonomous_player/src'),str(REPO/'ck3_autonomous_player/tests/unit')]
from xar_autoplayer.bridge.native_driver import _NativeCommandRejectedError
from xar_autoplayer.bridge.mcp_server import create_server
from mcp.server.mcpserver.exceptions import ToolError
from test_florin_fresh_full_public_v1 import SoftwareCase

FIXTURES=Path(os.environ.get('CK3_DIAGNOSTIC_CI_FIXTURES',REPO/'ck3_autonomous_player/tests/fixtures/fresh_full1210/diagnostic-q09'))

def actual_packets():
    provenance=json.loads((FIXTURES/'producer.json').read_bytes())
    if provenance['native_diagnostic_operands_modified'] is not False:
        raise AssertionError('Require untouched actual Native producer diagnostic operands')
    values=[]
    for row in provenance['packets']:
        raw=(FIXTURES/row['file']).read_bytes()
        if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:
            raise AssertionError('Actual C++ producer packet bytes changed')
        frame=json.loads(raw)
        if (frame.get('type')!='command_result' or frame.get('ok') is not False
                or frame.get('error')!='fresh_full_state_read_failed'):
            raise AssertionError('Expected the actual Native rejection')
        values.append(frame)
    if {frame['fresh_full_state_diagnostic']['stage'] for frame in values}!={'raw_read_unavailable','submit_rejected'}:
        raise AssertionError('Require both actual Native failure stages')
    return values

def install_actual_reply(case,driver,endpoint,frame):
    def send(request):
        endpoint.requests.append(deepcopy(request))
        correlated=deepcopy(frame);correlated['request_id']=request['request_id']
        case.assertEqual({k:v for k,v in correlated.items() if k!='request_id'},
                         {k:v for k,v in frame.items() if k!='request_id'})
        driver.state.ingest(correlated)
    endpoint.send=send

class ActualDiagnosticDriver(SoftwareCase,unittest.TestCase):
    def test_actual_cpp_operands_survive_strict_driver(self):
        for frame in actual_packets():
            with self.subTest(stage=frame['fresh_full_state_diagnostic']['stage']):
                driver,endpoint=self.make_driver();install_actual_reply(self,driver,endpoint,frame)
                with self.assertRaises(_NativeCommandRejectedError) as caught:driver.take_fresh_full_snapshot_v1()
                diagnostic=frame['fresh_full_state_diagnostic']
                self.assertEqual(caught.exception.native_error,frame['error'])
                self.assertEqual(caught.exception.native_command_result_frame['fresh_full_state_diagnostic'],diagnostic)
                self.assertEqual(caught.exception.native_raw_return_receipt['fresh_full_state_diagnostic'],diagnostic)
                self.assertEqual(len(endpoint.requests),1)
                self.assertEqual(driver._florin_fresh_full_read_pending_v1,endpoint.requests[0]['request_id'])
                self.assertIs(type(diagnostic['query_sequence']),str)
                if diagnostic['stage']=='submit_rejected':self.assertIsNone(diagnostic['wait_result'])
                else:self.assertEqual(diagnostic['wait_result'],0)

class ActualDiagnosticPublicMcp(SoftwareCase,unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):asyncio.get_running_loop().set_debug(False)
    async def test_actual_cpp_operands_survive_service_and_registered_mcp(self):
        for frame in actual_packets():
            with self.subTest(stage=frame['fresh_full_state_diagnostic']['stage']):
                driver,endpoint=self.make_driver();install_actual_reply(self,driver,endpoint,frame)
                with self.assertRaises(ToolError) as caught:
                    await create_server(driver).call_tool('ck3_take_fresh_full_snapshot_v1',{})
                self.assertIn(frame['error'],str(caught.exception))
                self.assertIn(frame['fresh_full_state_diagnostic']['stage'],str(caught.exception))
                self.assertIn(endpoint.requests[0]['request_id'],str(caught.exception))
                self.assertEqual(len(endpoint.requests),1)

if __name__=='__main__':unittest.main()
