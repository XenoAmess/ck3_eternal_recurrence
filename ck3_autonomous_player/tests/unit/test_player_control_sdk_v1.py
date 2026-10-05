"""Actual official MCP client checks; no game, pipe, desktop or native credit."""
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest

TOOLS=Path(__file__).resolve().parents[3]/'tools'
if str(TOOLS) not in sys.path: sys.path.insert(0,str(TOOLS))
from mcp import Client
from ck3_native_profile_mcp import create_server


class SchemaService:
    def __init__(self, expanded=False):
        self.profile={'player_control_source_inventory':{'path':'fixture','sha256':'b'*64}} if expanded else {}
        self.calls=[]
    def query_player_control_context(self, revision):
        self.calls.append(('query',revision))
        return {'status':'OFFLINE_SDK_FIXTURE_ONLY','native_gameplay_credit':False}
    def request_player_control(self, action, revision, signature, candidate):
        self.calls.append((action,revision,signature,candidate))
        return {'status':'OFFLINE_SDK_FIXTURE_ONLY','candidate_character_id':candidate,'native_gameplay_credit':False}
    def player_control_tools_admission_v1(self):
        return {'status':'OFFLINE_SDK_FIXTURE_ONLY','actual_native_acceptance':False}
    def __getattr__(self,name): raise AttributeError(name)


def preserve(name,payload):
    folder=os.environ.get('LYD_PLAYER_CONTROL_TEST_ARTIFACTS')
    if folder:
        path=Path(folder)/name; path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('x',encoding='utf-8') as stream:
            json.dump(payload,stream,ensure_ascii=False,indent=2); stream.write('\n')


class ActualSdkTests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_client_21_compatibility_and_opt_in_23_closed_metadata(self):
        async with Client(create_server(SchemaService()),cache=None) as client:
            legacy=(await client.list_tools()).model_dump(mode='json',by_alias=True,exclude_none=False)
        async with Client(create_server(SchemaService(True),player_control_tools=True),cache=None) as client:
            expanded=(await client.list_tools()).model_dump(mode='json',by_alias=True,exclude_none=False)
        old={row['name']:row for row in legacy['tools']}; new={row['name']:row for row in expanded['tools']}
        self.assertEqual(len(old),21); self.assertEqual(len(new),23)
        self.assertEqual({key:new[key] for key in old},old)
        baseline_file=os.environ.get('LYD_PLAYER_CONTROL_BASELINE_METADATA')
        if baseline_file:
            baseline=json.loads(Path(baseline_file).read_bytes())
            self.assertEqual(legacy,baseline)
        for name in ('ck3_query_profile_player_control_context_v1','ck3_request_profile_player_control_v1'):
            self.assertFalse(new[name]['inputSchema']['additionalProperties'])
        query=new['ck3_query_profile_player_control_context_v1']
        action=new['ck3_request_profile_player_control_v1']
        self.assertTrue(query['annotations']['readOnlyHint']); self.assertFalse(action['annotations']['readOnlyHint'])
        self.assertFalse(action['annotations']['idempotentHint'])
        self.assertEqual(action['inputSchema']['properties']['action']['enum'],
                         ['open_pause_menu','open_switch','choose_character','confirm_control'])
        self.assertEqual(set(action['inputSchema']['required']),{'action','expected_revision',
            'expected_control_context_signature','candidate_character_id'})
        preserve('actual-sdk-legacy-21-tools.json',legacy); preserve('actual-sdk-expanded-23-tools.json',expanded)
    async def test_actual_sdk_rejects_unknown_fields_coercion_missing_candidate_and_eval_before_service(self):
        service=SchemaService(True); results=[]
        query='ck3_query_profile_player_control_context_v1'; action='ck3_request_profile_player_control_v1'
        valid={'action':'choose_character','expected_revision':72,
               'expected_control_context_signature':'c'*64,'candidate_character_id':0x234567800000002}
        async with Client(create_server(service,player_control_tools=True),cache=None) as client:
            for name,args in [(query,{'expected_revision':True}),(query,{'expected_revision':'72'}),
                    (query,{'expected_revision':2**64}),(query,{'expected_revision':72,'rva':123}),
                    (action,{**valid,'action':'eval'}),(action,{**valid,'candidate_character_id':True}),
                    (action,{**valid,'candidate_character_id':2**64}),(action,{**valid,'path':'x'}),
                    (action,{k:v for k,v in valid.items() if k!='candidate_character_id'})]:
                result=await client.call_tool(name,args)
                self.assertTrue(result.is_error,repr(args)); results.append(result.model_dump(mode='json',by_alias=True,exclude_none=False))
        self.assertEqual(service.calls,[])
        preserve('actual-sdk-invalid-inputs-rejected.json',{'service_calls':0,'results':results})
    async def test_actual_sdk_preserves_complete_u64_candidate_and_explicit_null(self):
        service=SchemaService(True)
        async with Client(create_server(service,player_control_tools=True),cache=None) as client:
            for action,candidate in [('open_pause_menu',None),('open_switch',None),
                                     ('choose_character',0x234567800000002),('confirm_control',0x234567800000002)]:
                result=await client.call_tool('ck3_request_profile_player_control_v1',{'action':action,'expected_revision':72,
                    'expected_control_context_signature':'c'*64,'candidate_character_id':candidate})
                self.assertFalse(result.is_error); self.assertEqual(result.structured_content['candidate_character_id'],candidate)
        self.assertEqual([row[3] for row in service.calls],[None,None,0x234567800000002,0x234567800000002])
        preserve('actual-sdk-complete-id-fixture.json',{'service_calls':service.calls,'actual_native_acceptance':False})


if __name__=='__main__': unittest.main()
